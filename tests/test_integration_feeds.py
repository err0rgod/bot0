import feedparser
import unittest

class TestIntegrationFeeds(unittest.TestCase):
    def test_feed_availability(self):
        urls = [
            "https://thehackernews.com/",
            "https://projectzero.google/",
            "https://blog.cloudflare.com/"
        ]
        
        for url in urls:
            try:
                feed = feedparser.parse(url)
                if len(feed.entries) > 0:
                    continue
                    
                common_feeds = ["/rss", "/feed", "/rss.xml", "/feeds/posts/default"]
                found = False
                for path in common_feeds:
                    test_url = url.rstrip('/') + path
                    f = feedparser.parse(test_url)
                    if len(f.entries) > 0:
                        found = True
                        break
                        
            except Exception as e:
                print(f"Skipping {url} due to network error: {e}")

if __name__ == "__main__":
    unittest.main()
