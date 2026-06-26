import os
import sys
import logging

logging.basicConfig(level=logging.INFO)

# Make sure we can import local modules
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from scraper.pipeline import process_scraped_json
from automation.send_newsletter import send_newsletters

def main():
    raw_file = os.path.join(PROJECT_ROOT, "data", "output", "2026-04-17", "scraped_data.json")
    processed_file = os.path.join(PROJECT_ROOT, "data", "output", "2026-04-17", "newsletter_prepared_data.json")
    
    logging.info("Running AI Pipeline...")
    if os.path.exists(raw_file):
        process_scraped_json(raw_file, processed_file)
    else:
        logging.warning(f"Raw data file not found at {raw_file}. Cannot run local pipeline integration check.")
        return
    
    logging.info("Dispatching Newsletters...")
    # Because of our manual override in send_newsletter.py, 
    # it will ONLY go to nirbhayerror@gmail.com
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        loop.run_until_complete(send_newsletters())
    else:
        loop.run_until_complete(send_newsletters())
    logging.info("Done.")

if __name__ == "__main__":
    main()
