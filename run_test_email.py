import os
import sys
import logging

logging.basicConfig(level=logging.INFO)

# Make sure we can import local modules
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from scraper.pipeline import process_scraped_json
from automation.send_newsletter import send_newsletters

def main():
    raw_file = r"d:\bot0\data\output\2026-04-17\scraped_data.json"
    processed_file = r"d:\bot0\data\output\2026-04-17\newsletter_prepared_data.json"
    
    logging.info("Running AI Pipeline...")
    process_scraped_json(raw_file, processed_file)
    
    logging.info("Dispatching Newsletters...")
    # Because of our manual override in send_newsletter.py, 
    # it will ONLY go to nirbhayerror@gmail.com
    send_newsletters()
    logging.info("Done.")

if __name__ == "__main__":
    main()
