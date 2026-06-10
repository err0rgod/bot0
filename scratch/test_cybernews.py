import feedparser
import requests

url = "https://cybernews.com/feed/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
print(f"Status Code: {response.status_code}")

feed = feedparser.parse(response.content)

print(f"Feed Title: {feed.feed.get('title', 'N/A')}")
print(f"Number of entries: {len(feed.entries)}")

for entry in feed.entries[:3]:
    print(f"- {entry.title} ({entry.link})")
