import sys
import os
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

load_dotenv()

from scraper.v2 import extract_article

url = "https://www.darkreading.com/cybersecurity-operations/rsac-2026-how-ai-is-reshaping-cybersecurity-faster-than-ever"
print(f"Testing extraction for: {url}")
content = extract_article(url)

if content:
    print("Success! Content length:", len(content))
    print("Content preview:", content[:200])
else:
    print("Failed to extract content.")
