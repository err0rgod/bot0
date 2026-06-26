import json
import os
import sys
from datetime import datetime

# Setup paths to ensure we can import pipeline from scraper
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import process_scraped_json

def test_production_pipeline():
    """Test the upgraded production pipeline against scraped data."""
    print("--- Running Pipeline Test ---")
    
    DATA_DIR = os.getenv("DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
    output_dir = os.path.join(DATA_DIR, "output", datetime.today().strftime("%Y-%m-%d"))
    os.makedirs(output_dir, exist_ok=True)
    
    real_scraper_file = os.path.join(output_dir, "scraped_data.json")
    if not os.path.exists(real_scraper_file):
        print(f"[INFO] Could not find '{real_scraper_file}'. Generating mock scraped data for testing...")
        mock_data = {
            "news": [
                {
                    "title": "Critical RCE Vulnerability in Popular Router Firmware",
                    "link": "https://example.com/rce-router-firmware",
                    "date": "2026-06-26",
                    "summary": "A critical remote code execution vulnerability was found in major home router OS.",
                    "content": "Researchers have discovered a remote code execution vulnerability affecting millions of home router devices globally. The bug allows unauthenticated attackers to execute arbitrary code via a specially crafted HTTP request to the administration interface. A patch has been released, and users are urged to update their firmware immediately to mitigate the threat of botnets enrolling their devices. The vulnerability is tracked as CVE-2026-9999 and has a CVSS score of 9.8."
                },
                {
                    "title": "New Ransomware Group 'CyberAlpha' Targets Healthcare Sector",
                    "link": "https://example.com/cyberalpha-ransomware",
                    "date": "2026-06-26",
                    "summary": "A new ransomware variant is actively targeting clinics and hospitals.",
                    "content": "The ZeroDay threat intelligence team has identified a new ransomware-as-a-service group named CyberAlpha. The group utilizes advanced phishing campaigns to compromise corporate credentials, followed by lateral movement using dual-use administrative tools. Thus far, five hospitals have reported encrypted systems, and the group is demanding ransoms starting at 2 BTC. No decryption tool is currently available, and organizations are advised to restore from offline backups."
                }
            ],
            "cves": [
                {
                    "cve_id": "CVE-2026-1234",
                    "description": "SQL injection vulnerability in ZeroDay portal before version 3.2.1 allows remote attackers to execute arbitrary database commands.",
                    "severity": "8.8 High",
                    "published_date": "2026-06-25T12:00:00Z"
                }
            ]
        }
        with open(real_scraper_file, "w", encoding="utf-8") as f:
            json.dump(mock_data, f, indent=2)
        print(f"[SUCCESS] Generated mock data at '{real_scraper_file}'.")
        
    print(f"Loading data from {real_scraper_file}...")
    
    # Process it via new pipeline logic into output dir
    test_json_out = os.path.join(output_dir, "test_newsletter.json")
    newsletter_json = process_scraped_json(real_scraper_file, test_json_out)
    
    if not newsletter_json:
        print("[ERROR] Pipeline failed or returned empty data.")
        sys.exit(1)
        
    print("\n--- FINAL JSON OUTPUT GENERATED SUCCESSFULLY ---")
    print("Top stories found:", len(newsletter_json.get("top_stories", [])))
    print("CVEs found:", len(newsletter_json.get("cves", [])))
    
    # Text generation should also implicitly run and be stored in output/test_newsletter.txt
    test_txt_out = test_json_out.replace(".json", ".txt")
    print(f"\n--- READING GENERATED TEXT NEWSLETTER ({test_txt_out}) PREVIEW ---")
    if os.path.exists(test_txt_out):
        with open(test_txt_out, "r", encoding="utf-8") as f:
            content = f.read()
            # Print just the first 1000 chars as a rough preview
            print(content[:1000] + "\n\n... (preview truncated) ...")

if __name__ == "__main__":
    test_production_pipeline()

