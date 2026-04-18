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

def _get_s3_client():
    region = os.getenv("AWS_REGION", "us-east-1")
    bucket = os.getenv("S3_BUCKET_NAME")
    if not bucket:
        logger.debug("[STORAGE] No S3_BUCKET_NAME found.")
        return None, None
    try:
        import boto3
        s3 = boto3.client('s3', region_name=region)
        return s3, bucket
    except Exception as e:
        logger.debug(f"[STORAGE] Failed to initialize S3 Client: {e}")
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
    s3, bucket = _get_s3_client()
    
    if s3:
        current_time = time.time()
        # If cache is valid, return it
        if _blob_cache["dates"] is not None and (current_time - _blob_cache["last_checked"] < CACHE_TTL):
            return _blob_cache["dates"]
            
        try:
            def _list_blobs():
                # We fetch keys that look like 'issue_YYYY-MM-DD.json'
                response = s3.list_objects_v2(Bucket=bucket, Prefix="issue_")
                return response.get('Contents', [])
            
            objects = _retry_azure_call(_list_blobs)
            dates = []
            for obj in objects:
                try:
                    key = obj['Key']
                    if not key.endswith(".json"):
                        continue
                    date_str = key.replace("issue_", "").replace(".json", "")
                    datetime.strptime(date_str, "%Y-%m-%d")
                    dates.append(date_str)
                except ValueError:
                    continue
            
            dates = list(set(dates)) # deduplicate
            dates.sort(reverse=True)
            _blob_cache["dates"] = dates
            _blob_cache["last_checked"] = time.time()
            logger.info(f"[STORAGE] fetched list of {len(dates)} available issues from S3 cloud.")
            return dates
        except Exception as e:
            logger.warning(f"[WARN] S3 fetch failed for issue dates: {e}")
    
    return []

def get_issue_data(date_str: str) -> Optional[Dict]:
    """Reads and returns the JSON data for a specific issue date."""
    if date_str in _blob_cache["issues"]:
        return _blob_cache["issues"][date_str]

    s3, bucket = _get_s3_client()
    if s3:
        try:
            def _download():
                response = s3.get_object(Bucket=bucket, Key=f"issue_{date_str}.json")
                return json.loads(response['Body'].read().decode('utf-8'))
            
            data = _retry_azure_call(_download)
            _blob_cache["issues"][date_str] = data
            logger.debug(f"[STORAGE] downloaded issue for {date_str} from S3.")
            return data
        except Exception as e:
            logger.warning(f"[WARN] S3 download failed for {date_str}: {e}")
                
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
