import json
import os
import time
import logging
from dotenv import load_dotenv

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, ".env"), override=True)

from summarizer import summarize_article, generate_two_level_summary
from categorizer import categorize_article
from utils import is_duplicate_title, rank_article

# Setup pipeline logging with structured format
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def _retry_storage(func, *args, **kwargs):
    """Internal helper for exponential backoff retries on cloud uploads."""
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_attempts:
                logger.error(f"[ERROR][STORAGE] cloud upload failed permanently after {max_attempts} attempts: {e}")
                return False
            delay = 2 ** attempt
            logger.error(f"[ERROR][STORAGE] upload failed (attempt {attempt}/{max_attempts})")
            logger.info(f"[RETRY] retrying in {delay}s...")
            time.sleep(delay)
    return False

def generate_newsletter(json_data: dict, output_file: str = None):
    """
    Generates a human-readable text newsletter from the structured JSON data.
    """
    if not output_file:
        from datetime import datetime
        PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        DATA_DIR = os.getenv("DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
        output_file = os.path.join(DATA_DIR, "output", datetime.today().strftime("%Y-%m-%d"), "newsletter.txt")
        
    # Ensure output directory exists before writing
    out_dir = os.path.dirname(output_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Cybersecurity Weekly Brief\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("Top 5 Security Stories\n")
        f.write("-" * 50 + "\n\n")
        
        # Write top stories
        for i, story in enumerate(json_data.get("top_stories", []), 1):
            f.write(f"{i}. {story['title']}\n\n")
            f.write(f"{story['short_summary']}\n\n")
            f.write(f"{story['deep_summary']}\n")
            f.write("\n" + "-" * 30 + "\n\n")
            
        # Optional: Add CVE section
        cves = json_data.get("cves", [])
        if cves:
            f.write("Important Vulnerabilities (CVEs)\n")
            f.write("-" * 50 + "\n\n")
            for cve in cves:
                f.write(f"- {cve['title']}: {cve['summary']}\n")
                if cve.get('cve_ids'):
                    ids_str = ', '.join(cve['cve_ids'])
                    f.write(f"  Vulnerabilities: {ids_str}\n")

    logger.info(f"Generated human readable newsletter text at {output_file}")


import asyncio

async def process_scraped_json(file_path: str, output_path: str = None):
    """
    Reads JSON from v2.py, applies filtering, deduplication, ranking, and AI summarization rules.
    Outputs the final segregated structure into output/newsletter.json. Operations are processed concurrently.
    """
    if not os.path.exists(file_path):
        logger.error(f"[ERROR] file {file_path} not found.")
        return {"scrape": "failed", "upload": "skipped"}

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    logger.info(f"[SCRAPER] processing raw data from {os.path.basename(file_path)}")
        
    if not output_path:
        from datetime import datetime
        PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        DATA_DIR = os.getenv("DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
        output_path = os.path.join(DATA_DIR, "output", datetime.today().strftime("%Y-%m-%d"), "newsletter.json")
        
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    
    seen_urls = set()
    seen_titles = []
    
    # --- DEDUPLICATE AGAINST YESTERDAY'S NEWS ---
    from datetime import datetime, timedelta
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _DATA_DIR = os.getenv("DATA_DIR", os.path.join(_PROJECT_ROOT, "data"))
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")    
    yesterday_file = os.path.join(_DATA_DIR, "output", yesterday, "newsletter.json")
    yesterday_data = None
    
    if os.path.exists(yesterday_file):
        try:
            with open(yesterday_file, "r", encoding="utf-8") as yf:
                yesterday_data = json.load(yf)
        except Exception as e:
            logger.error(f"Failed to load yesterday's local data: {e}")
    else:
        azure_conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("AZURE_CONTAINER_NAME", "news")
        if azure_conn_str:
            try:
                from azure.storage.blob import BlobServiceClient
                blob_service = BlobServiceClient.from_connection_string(azure_conn_str)
                container_client = blob_service.get_container_client(container_name)
                blob_name = f"issue_{yesterday}.json"
                blob_client = container_client.get_blob_client(blob_name)
                if blob_client.exists():
                    logger.info(f"Downloading yesterday's issue from Azure: {blob_name}")
                    download_stream = blob_client.download_blob()
                    yesterday_data = json.loads(download_stream.readall())
            except Exception as e:
                logger.error(f"Failed to download yesterday's news from Azure: {e}")

    if yesterday_data:
        for item in yesterday_data.get("top_stories", []):
            if item.get("url"):
                seen_urls.add(item["url"])
            if item.get("title"):
                seen_titles.append(item["title"])
        for cve in yesterday_data.get("cves", []):
            if cve.get("title"):
                seen_titles.append(cve["title"])
        logger.info(f"Loaded {len(yesterday_data.get('top_stories', []))} stories and {len(yesterday_data.get('cves', []))} CVEs from yesterday for deduplication.")
    
    processed_news = []
    processed_cves = []
    
    # --- PROCESS NEWS ---
    logger.info("Scheduling News Articles for Async Processing...")
    news_tasks = []
    
    async def process_single_news(item):
        title = item.get("title", "")
        content = item.get("content", "")
        url = item.get("link", "")
        score = rank_article(content)
        
        try:
            category = await categorize_article(title, content[:1500])
            if category == "CVE":
                summary = await summarize_article(title, content)
                import re as _re
                extracted_ids = list(dict.fromkeys(_re.findall(r'CVE-\d{4}-\d{4,7}', content, _re.IGNORECASE)))
                return {"type": "cve", "data": {
                    "title": title, "summary": summary, 
                    "cve_ids": [c.upper() for c in extracted_ids], "score": score
                }}
                
            summaries = await generate_two_level_summary(title, content)
            return {"type": "news", "data": {
                "title": title, "category": category,
                "short_summary": summaries["short_summary"],
                "deep_summary": summaries["deep_summary"],
                "score": score, "source": "RSS Scraping", "url": url
            }}
        except Exception as e:
            logger.error(f"[ERROR] AI processing failed for article '{title}': {e}")
            return None

    # Filter items before scheduling to prevent duplicates within the batch
    for item in data.get("news", []):
        if len(news_tasks) >= 15:
            logger.info("Reached maximum of 15 processed articles. Skipping the rest.")
            break
            
        title = item.get("title", "")
        content = item.get("content", "")
        url = item.get("link", "")
        
        if len(content) < 200: continue
        if url and url in seen_urls: continue
        
        is_dup = False
        for seen_t in seen_titles:
            if is_duplicate_title(title, seen_t, threshold=0.8):
                is_dup = True
                break
        if is_dup: continue
        
        # Add to seen to prevent internal duplicates in the same batch
        seen_urls.add(url)
        seen_titles.append(title)
        
        news_tasks.append(process_single_news(item))

    # Await all valid news items
    if news_tasks:
        results = await asyncio.gather(*news_tasks)
        for res in results:
            if not res: continue
            if res["type"] == "cve":
                processed_cves.append(res["data"])
            elif res["type"] == "news":
                processed_news.append(res["data"])


    # --- PROCESS CVES ---
    # Scraper explicit CVEs
    logger.info("Scheduling Explicit API CVEs for Async Processing...")
    cve_tasks = []
    
    async def process_single_cve(cve_id, desc):
        title = f"Vulnerability {cve_id}"
        try:
            summary = await summarize_article(title, desc)
            return {
                "title": title,
                "summary": summary,
                "cve_ids": [cve_id]
            }
        except Exception as e:
            logger.error(f"Error processing CVE {cve_id}: {e}")
            return None

    for cve in data.get("cves", []):
        cve_id = cve.get("cve_id", "")
        desc = cve.get("description", "")
        if cve_id and desc:
            cve_tasks.append(process_single_cve(cve_id, desc))
            
    if cve_tasks:
        cve_results = await asyncio.gather(*cve_tasks)
        for res in cve_results:
            if res: processed_cves.append(res)

    # --- RANK & SELECT TOP STORIES ---
    # Sort news descending by score
    processed_news.sort(key=lambda x: x["score"], reverse=True)
    top_stories = processed_news[:10]
    
    logger.info(f"Selected {len(top_stories)} Top stories for the final newsletter.")

    # --- BUILD FINAL JSON ---
    from datetime import datetime
    final_output = {
        "date": datetime.today().strftime("%Y-%m-%d"),
        "top_stories": top_stories,
        "cves": processed_cves
    }

    # Save to disk
    with open(output_path, "w", encoding="utf-8") as out:
        json.dump(final_output, out, indent=4)
        
    logger.info(f"[FILTER] selected {len(top_stories)} high-priority items.")
    logger.info(f"[STORAGE] saved local issue data ({(os.path.getsize(output_path)//1024)}KB)")

    # Cloud Storage Upload (Azure Blob Storage)
    upload_status = "skipped"
    azure_conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_CONTAINER_NAME", "news")
    if azure_conn_str:
        try:
            from azure.storage.blob import BlobServiceClient
            blob_service = BlobServiceClient.from_connection_string(azure_conn_str)
            container_client = blob_service.get_container_client(container_name)
            
            if not container_client.exists():
                container_client.create_container()
            
            # Upload dated file
            blob_name = f"issue_{final_output['date']}.json"
            def _upload_all():
                # Upload dated file
                container_client.get_blob_client(blob_name).upload_blob(json.dumps(final_output), overwrite=True)
                # Upload latest alias
                container_client.get_blob_client("latest.json").upload_blob(json.dumps(final_output), overwrite=True)
                return True

            if _retry_storage(_upload_all):
                logger.info(f"[STORAGE] uploaded {blob_name} and latest.json (Azure)")
                upload_status = "success"
            else:
                upload_status = "failed"
                
        except Exception as e:
            logger.error(f"[ERROR][STORAGE] cloud upload initialization failed: {e}")
            upload_status = "failed"

    
    # Also generate text version
    text_out_path = output_path.replace(".json", ".txt")
    generate_newsletter(final_output, text_out_path)

    return {
        "scrape": "success",
        "upload": upload_status,
        "issue_date": final_output['date'],
        "stories": len(top_stories)
    }
