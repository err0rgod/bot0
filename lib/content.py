import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

# Configure logging with structured format
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
OUTPUT_DIR = os.path.join(DATA_DIR, "output")

# Simple in-memory cache with 10-minute TTL
_blob_cache = {
    "dates": None,
    "issues": {},
    "last_checked": 0
}

# cache time set to 1 minute
import time
CACHE_TTL = 60 # 1 minute

def _get_blob_service():
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not conn_str: 
        logger.debug("[STORAGE] No Azure connection string found.")
        return None, None
    try:
        from azure.storage.blob import BlobServiceClient
        service = BlobServiceClient.from_connection_string(conn_str)
        container = os.getenv("AZURE_CONTAINER_NAME", "news")
        return service, container
    except Exception as e:
        logger.debug(f"[STORAGE] Failed to initialize BlobServiceClient: {e}")
        return None, None

def _retry_azure_call(func, *args, **kwargs):
    """Internal helper for exponential backoff retries on Azure calls."""
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_attempts:
                logger.error(f"[ERROR][STORAGE] cloud operation failed permanently after {max_attempts} attempts: {e}")
                raise e
            delay = 2 ** attempt
            logger.error(f"[ERROR][STORAGE] operation failed (attempt {attempt}/{max_attempts})")
            logger.info(f"[RETRY] retrying in {delay}s...")
            time.sleep(delay)

def get_issue_dates() -> List[str]:
    """Returns a sorted list of all available issue dates (YYYY-MM-DD), newest first."""
    service, container = _get_blob_service()
    
    if service:
        current_time = time.time()
        # If cache is valid, return it
        if _blob_cache["dates"] is not None and (current_time - _blob_cache["last_checked"] < CACHE_TTL):
            return _blob_cache["dates"]
            
        try:
            container_client = service.get_container_client(container)
            
            def _list_blobs():
                return list(container_client.list_blobs(name_starts_with="issue_"))
            
            blobs = _retry_azure_call(_list_blobs)
            dates = []
            for blob in blobs:
                try:
                    date_str = blob.name.replace("issue_", "").replace(".json", "")
                    datetime.strptime(date_str, "%Y-%m-%d")
                    dates.append(date_str)
                except ValueError:
                    continue
            
            dates.sort(reverse=True)
            _blob_cache["dates"] = dates
            _blob_cache["last_checked"] = time.time()
            logger.info(f"[STORAGE] fetched list of {len(dates)} available issues from cloud.")
            return dates
        except Exception:
            logger.warning("[WARN][FALLBACK] cloud fetch failed for issue dates, falling back to local storage.")
    
    # Fallback to local
    if not os.path.exists(OUTPUT_DIR):
        return []
    
    dates = []
    for d in os.listdir(OUTPUT_DIR):
        path = os.path.join(OUTPUT_DIR, d)
        if os.path.isdir(path):
            try:
                datetime.strptime(d, "%Y-%m-%d")
                dates.append(d)
            except ValueError:
                pass # not a date folder
                
    dates.sort(reverse=True)
    return dates

def get_issue_data(date_str: str) -> Optional[Dict]:
    """Reads and returns the JSON data for a specific issue date."""
    if date_str in _blob_cache["issues"]:
        return _blob_cache["issues"][date_str]

    service, container = _get_blob_service()
    if service:
        try:
            container_client = service.get_container_client(container)
            blob_client = container_client.get_blob_client(f"issue_{date_str}.json")
            
            def _download():
                return json.loads(blob_client.download_blob().readall())
            
            data = _retry_azure_call(_download)
            _blob_cache["issues"][date_str] = data
            logger.debug(f"[STORAGE] downloaded issue for {date_str} from cloud.")
            return data
        except Exception:
            logger.warning(f"[WARN][FALLBACK] cloud download failed for {date_str}, check local cache.")
            
    # Priority 1: Check standard local output path for the date
    json_path = os.path.join(OUTPUT_DIR, date_str, "newsletter_prepared_data.json")
    # Priority 2: Simple fallback to data dir as requested by user
    fallback_path = os.path.join(DATA_DIR, "newsletter_prepared_data.json")
    
    for path in [json_path, fallback_path]:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    _blob_cache["issues"][date_str] = data
                    logger.info(f"[WARN][FALLBACK] using local cached newsletter data for {date_str}")
                    return data
            except Exception as e:
                logger.error(f"[ERROR] failed to read local fallback for {date_str}: {e}")
                
    return None

def get_latest_issue() -> Optional[Dict]:
    """Returns the latest issue data, if any."""
    dates = get_issue_dates()
    if not dates:
        return None
    return get_issue_data(dates[0])

def get_all_articles() -> List[Dict]:
    """Returns a flat list of all articles across all issues (useful for search)."""
    dates = get_issue_dates()
    all_articles = []
    
    for d in dates:
        issue = get_issue_data(d)
        if issue and "top_stories" in issue:
            for story in issue["top_stories"]:
                story["issue_date"] = issue.get("date", d)
                all_articles.append(story)
                
    return all_articles

def search_articles(query: str) -> List[Dict]:
    """Simple text search on article titles and summaries."""
    if not query:
        return []
        
    query = query.lower()
    results = []
    for article in get_all_articles():
        title = article.get("title", "").lower()
        summary = article.get("short_summary", "").lower()
        
        if query in title or query in summary:
            results.append(article)
            
    return results
