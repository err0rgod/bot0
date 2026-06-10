import requests

url = "https://cybernews.com/feed/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

response = requests.get(url, headers=headers)
print(f"Status Code: {response.status_code}")
print(f"Headers: {response.headers}")
print(f"Content Preview: {response.text[:500]}")
