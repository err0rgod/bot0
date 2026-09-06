import requests
import feedparser
import time
import random
import json
import logging
from newspaper import Article



logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# sources to fetch the content 
NEWS_FEEDS = [
    "https://feeds.feedburner.com/TheHackers",
    "https://feeds.feedburner.com/TheHackersNews", # The Hacker News
    "https://www.bleepingcomputer.com/feed/",
    "https://krebsonsecurity.com/feed/",
    "https://www.darkreading.com/rss.xml",  
    "https://www.securityweek.com/rss",
    "https://blog.cloudflare.com/rss/", # Cloudflare Blog
    "https://googleprojectzero.blogspot.com/feeds/posts/default?alt=rss", # Google Project Zero
    "https://techcrunch.com/category/artificial-intelligence/feed/", # TechCrunch AI
    "https://www.theverge.com/rss/index.xml", # The Verge Tech
    "https://feeds.arstechnica.com/arstechnica/technology-lab" # Ars Technica IT/Tech
]

# NVD api for cves
NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"


# Multiple user agents to avoid getting blocked
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
]

# random delays to avoid blocking 
def random_delay():
    time.sleep(random.uniform(1, 3))

# picking random user agent and headers
def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }


# extract article content using newspaper3k
def extract_article(url):
    try:
        random_delay()
        
        headers = get_headers()
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html = response.text

        from newspaper import Config
        config = Config()
        config.browser_user_agent = headers["User-Agent"]
        config.request_timeout = 10

        article = Article(url, config=config)
        article.set_html(html)
        article.parse()

        return article.text

    except Exception as e:
        logging.warning(f"Failed to parse article: {url} | Error: {e}")
        return ""


# scrape news from RSS feeds
def scrape_news(max_items=5):

    news_data = []
    seen_links = set()
# loop through the news feeds
    for feed_url in NEWS_FEEDS:

        logging.info(f"Reading RSS: {feed_url}")

        feed = feedparser.parse(feed_url)

        count = 0

        for entry in feed.entries:

            if count >= max_items:
 
                break

            link = entry.link

            if link in seen_links:
                continue

            seen_links.add(link)

            title = entry.title
            date = entry.get("published", "")
            summary = entry.get("summary", "")

            logging.info(f"Scraping article: {title}")

            content = extract_article(link)
            if not content:
                continue

            news_data.append({
                "id":link,
                "title": title,
                "link": link,
                "date": date,
                "summary": summary,
                "content": content
            })

            count += 1

    return news_data

# scraping cves from NVD API
def scrape_cves(max_items=10):

    logging.info("Fetching latest CVEs")

    params = {
        "resultsPerPage": max_items
    }

    # retry mechanism
    for attempt in range(3):
        try:
            response = requests.get(NVD_API, headers=get_headers(), params=params, timeout=20)
            response.raise_for_status()
            data = response.json()

            cves = []
            for vuln in data.get("vulnerabilities", []):
                cve = vuln["cve"]
                cve_id = cve["id"]
                
                descriptions = cve.get("descriptions", [])
                description = ""
                for d in descriptions:
                    if d["lang"] == "en":
                        description = d["value"]
                        break

                severity = "Unknown"
                metrics = cve.get("metrics", {})
                if "cvssMetricV31" in metrics:
                    cvss = metrics["cvssMetricV31"][0]["cvssData"]
                    severity = f'{cvss["baseScore"]} ({cvss["baseSeverity"]})'

                cves.append({
                    "cve_id": cve_id,
                    "description": description,
                    "severity": severity,
                    "published_date": cve.get("published", "")
                })

            return cves
            
        except requests.exceptions.HTTPError as http_err:
            logging.warning(f"CVE scraping HTTP error on attempt {attempt + 1}: {http_err}")
            time.sleep(5)
        except Exception as e:
            logging.warning(f"CVE scraping general error on attempt {attempt + 1}: {e}")
            time.sleep(5)
            
    logging.error("All CVE scraping attempts failed after 3 retries.")
    return []


def main():
    import time
    overall_start = time.time()
    
    logging.info("Starting Cyber News Scraper")

    scrape_start = time.time()
    news = scrape_news()
    cves = scrape_cves()
    
    scrape_time = time.time() - scrape_start

    output = {
        "news": news,
        "cves": cves
    }

    import os
    from datetime import datetime

    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # In AWS Lambda, we write pure raw dicts to S3 immediately
    s3_bucket = os.getenv("S3_BUCKET_NAME")
    if s3_bucket:
        try:
            import boto3
            s3_client = boto3.client('s3', region_name=os.getenv("AWS_REGION", "ap-south-2"))
            raw_blob_name = f"raw_data_{datetime.today().strftime('%Y-%m-%d')}.json"
            s3_client.put_object(Bucket=s3_bucket, Key=raw_blob_name, Body=json.dumps(output))
            logging.info(f"Raw data saved to S3 Key: {raw_blob_name}")
        except Exception as e:
            logging.warning(f"Failed to upload raw data to S3: {e}")
    
    pipeline_status = None
    email_status = None
    pipeline_time = 0
    email_time = 0

    # Sequential Async execution in a single loop
    async def run_async_phases():
        from scraper.pipeline import process_scraped_data
        from automation.send_newsletter import send_newsletters
        
        logging.info("Starting AI Processing Pipeline...")
        p_start = time.time()
        p_status = await process_scraped_data(output)
        p_time = time.time() - p_start
        
        logging.info("Dispatching email newsletters...")
        e_start = time.time()
        e_status = await send_newsletters()
        e_time = time.time() - e_start
        
        return p_status, p_time, e_status, e_time

    # Run the consolidated async phases
    try:
        import asyncio
        pipeline_status, pipeline_time, email_status, email_time = asyncio.run(run_async_phases())
        logging.info("AI Pipeline and Email Dispatch completed successfully.")
    except Exception as e:
        logging.error(f"Error during async phase execution: {e}")

    total_time = time.time() - overall_start

    # Dispatch Analytics Email
    try:
        import sys
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)
        from lib.notifications import send_custom_email
        
        s3_ok = (pipeline_status and pipeline_status.get("upload") == "success")
        
        # Placeholder for website health check
        website_status = "Pending Integration" 
        
        html_report = f"""
        <html><body>
        <h2>AWS Bot Execution Analytics</h2>
        <table border="1" cellpadding="8" style="border-collapse: collapse;">
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Execution Time</td><td>{total_time:.2f} s</td></tr>
            <tr><td>Scraping Time</td><td>{scrape_time:.2f} s</td></tr>
            <tr><td>AI Pipeline Time</td><td>{pipeline_time:.2f} s</td></tr>
            <tr><td>Email Dispatch Time</td><td>{email_time:.2f} s</td></tr>
            <tr><td>Stories Scraped</td><td>{len(news)}</td></tr>
            <tr><td>CVEs Fetched</td><td>{len(cves)}</td></tr>
            <tr><td>AWS S3 Status</td><td>{'OK' if s3_ok else 'FAILED'}</td></tr>
            <tr><td>Website Status</td><td>{website_status}</td></tr>
        </table>
        """
        
        if email_status:
            html_report += f"""
            <br>
            <h3>Email Serverless Stats</h3>
            <table border="1" cellpadding="8" style="border-collapse: collapse;">
                <tr><th>Status</th><td>{email_status.get('email', 'unknown')}</td></tr>
                <tr><th>Total Target Subscribers</th><td>{email_status.get('total_target', 0)}</td></tr>
                <tr><th>Total Successfully Sent</th><td>{email_status.get('total_sent', 0)}</td></tr>
            </table>
            """
        else:
            html_report += "<p><b>Email Delivery:</b> FAILED or DID NOT RUN.</p>"
            
        html_report += "</body></html>"
        
        logging.info("Sending Analytics Email to nirbhayerror@gmail.com")
        send_custom_email(["nirbhayerror@gmail.com"], f"Analytics Report [{datetime.today().strftime('%Y-%m-%d')}]", html_report)
    except Exception as e:
        logging.error(f"Failed to send analytics report: {e}")

    return {
        "statusCode": 200,
        "body": "Daily intelligence cycle completed successfully."
    }

def lambda_handler(event, context):
    """
    AWS Lambda Entry Point.
    Triggered by EventBridge (e.g. 8:00 AM Cron).
    """
    print("Lambda invocation Triggered - starting intelligence cycle.")
    return main()

if __name__ == "__main__":
    main()