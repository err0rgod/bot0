import feedparser

urls = [
    "https://thehackernews.com/",
    "https://projectzero.google/",
    "https://blog.cloudflare.com/"
]

for url in urls:
    print(f"Testing {url}...")
    feed = feedparser.parse(url)
    print(f"  Entries: {len(feed.entries)}")
    if len(feed.entries) > 0:
        print(f"  Title: {feed.feed.get('title', 'No Title')}")
    else:
        print("  Failed to find entries directly. Checking common feed paths...")
        common_feeds = ["/rss", "/feed", "/rss.xml", "/feeds/posts/default"]
        for path in common_feeds:
            test_url = url.rstrip('/') + path
            print(f"    Testing {test_url}...")
            f = feedparser.parse(test_url)
            if len(f.entries) > 0:
                print(f"      SUCCESS: {len(f.entries)} entries found at {test_url}")
                break
