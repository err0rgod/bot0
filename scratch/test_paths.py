import requests

base_url = "https://cybernews.com"
paths = ["/feed/", "/rss/", "/news/feed/", "/editorial/feed/"]
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

for path in paths:
    url = base_url + path
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"URL: {url} | Status: {response.status_code}")
        if response.status_code == 200:
            if "xml" in response.headers.get("Content-Type", "") or "<rss" in response.text[:100]:
                print(f"  SUCCESS! Found RSS feed at {url}")
    except Exception as e:
        print(f"URL: {url} | Error: {e}")
