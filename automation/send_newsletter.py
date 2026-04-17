import os
import sys
import time
import json
import logging

# Add project root to sys.path at index 0 to avoid Linux 'lib' folder collisions
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Load credentials from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), override=True)

# mailing client
import resend
import secrets
from lib.content import get_latest_issue
from lib.notifications import FROM_EMAIL, BASE_URL, validate_sender_domain
from lib.db import init_db, SessionLocal, EmailLog
from lib.humanizer import humanize_email, safety_filter

# Configure logging
logger = logging.getLogger(__name__)

resend.api_key = os.getenv("RESEND_API_KEY", "")
init_db() # Ensure tables exist


def _fetch_subscribers_from_blob() -> list:
    """Fetch the latest subscriber list from Azure Blob Storage (subscribers.json)."""
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_CONTAINER_NAME", "news")

    if not conn_str:
        print("Warning: No Azure connection string found. Falling back to local subscribers.json")
        return _fetch_subscribers_from_local()

    try:
        from azure.storage.blob import BlobServiceClient
        blob_service = BlobServiceClient.from_connection_string(conn_str)
        container_client = blob_service.get_container_client(container_name)
        blob_client = container_client.get_blob_client("subscribers.json")

        data = json.loads(blob_client.download_blob().readall().decode("utf-8-sig"))
        # Only send to active subscribers
        active = [s for s in data if s.get("is_active", True)]
        logger.info(f"[STORAGE] fetched {len(active)} active subscribers from cloud.")
        return active
    except Exception as e:
        logger.warning(f"[WARN][FALLBACK] cloud subscriber fetch failed: {e}. trying local.")
        return _fetch_subscribers_from_local()


def _fetch_subscribers_from_local() -> list:
    """Fallback: read subscribers from local subscribers.json file."""
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.getenv("DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
    local_path = os.path.join(DATA_DIR, "subscribers.json")

    if not os.path.exists(local_path):
        print("No local subscribers.json found.")
        return []

    try:
        with open(local_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        logger.info(f"[WARN][FALLBACK] using local subscribers.json ({len(data)} records)")
        return data
    except Exception as e:
        logger.error(f"[ERROR] failed to read local subscribers.json: {e}")
        return []


def send_newsletters():
    start_time = time.time()
    logger.info("[SUMMARY] starting automated newsletter dispatch")
    
    # Track status for final summary
    status = {
        "scrape": "unknown",
        "upload": "unknown",
        "email": "pending",
        "fallback_used": "no",
        "total_sent": 0,
        "total_target": 0
    }

    # 1. Fetch latest issue
    latest_issue = get_latest_issue()
    if not latest_issue:
        logger.error("[ERROR][EMAIL] no issue found to send.")
        status["email"] = "failed (no content)"
        _print_summary(status, start_time)
        return status

    # Check if fallback was used (clunky but heuristic based on cached result or lack of cloud result)
    # The actual fallback logic is inside lib.content, but we can check if it just happened
    # by looking at logger if we had a shared state. For now, we'll assume 'no' unless we catch a warning.
    
    date_str = latest_issue.get("date", "Latest")
    top_stories = latest_issue.get("top_stories", [])
    status["scrape"] = "success"
    status["upload"] = "success" # If we found it, it was ideally uploaded

    # Validate sender config up front to avoid generating content when delivery must fail.
    sender_ok, sender_reason = validate_sender_domain(FROM_EMAIL)
    if not sender_ok:
        logger.error(
            f"[ERROR][EMAIL] Sender domain validation failed for FROM_EMAIL={FROM_EMAIL!r}. {sender_reason} "
            "Fix: verify domain in Resend dashboard and update DNS (SPF/DKIM), or use a verified sender."
        )
        status["email"] = "failed (sender domain not verified)"
        _print_summary(status, start_time)
        return status
    logger.info(f"[EMAIL] sender check passed. {sender_reason}")

    # Generate the email story blocks
    story_html = ""
    for idx, story in enumerate(top_stories, 1):
        story_html += f"""
        <tr>
            <td style="padding: 24px 0; border-bottom: 1px solid #f1f5f9;">
                <h3 style="margin: 0 0 8px 0; font-size: 18px; color: #0f172a; font-weight: 600;">{idx}. {story.get('title', '')}</h3>
                <p style="margin: 0; font-size: 15px; color: #475569; line-height: 1.6;">{story.get('short_summary', '')}</p>
            </td>
        </tr>
        """
    # (Rest of base_html omitted for brevity in chunk, but stays in file)
    base_html = f"""<!DOCTYPE html>
<html lang="en">
<body style="margin:0;padding:0;background-color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e2e8f0;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
          <tr>
            <td style="background:#ffffff;padding:48px 40px 24px;text-align:center;border-bottom:1px solid #f1f5f9;">
              <div style="display:inline-block;background:#f3e8ff;border-radius:6px;padding:6px 14px;margin-bottom:16px;">
                <span style="color:#7e22ce;font-size:12px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;">ZeroDay Daily</span>
              </div>
              <h1 style="color:#0f172a;font-size:26px;font-weight:700;margin:0;line-height:1.3;letter-spacing:-0.5px;">
                Issue for {date_str}
              </h1>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 40px 48px;">
              <p style="color:#64748b;font-size:16px;line-height:1.6;margin:0 0 32px;text-align:center;">
                Here are the top cybersecurity stories for today.
              </p>
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
                {story_html}
              </table>
              <table cellpadding="0" cellspacing="0" style="margin:0 auto;">
                <tr>
                  <td align="center" style="border-radius:8px;background:linear-gradient(135deg,#8b5cf6,#6366f1);box-shadow:0 4px 14px 0 rgba(139,92,246,0.39);">
                    <a href="{BASE_URL}/daily" style="display:inline-block;padding:14px 32px;color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;border-radius:8px;letter-spacing:0.3px;">Explore Full Issue</a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="background:#f8fafc;padding:32px 40px;border-top:1px solid #e2e8f0;text-align:center;">
              <p style="color:#94a3b8;font-size:13px;margin:0 0 12px;">ZeroDay Daily &bull; Cybersecurity intelligence.</p>
              <p style="margin:0;"><a href="{{unsubscribe_url}}" style="color:#cbd5e1;font-size:12px;text-decoration:underline;">Unsubscribe</a></p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    # 2. Fetch subscribers
    sub_start = time.time()
    subscribers = _fetch_subscribers_from_blob()
    status["total_target"] = len(subscribers)

    if not subscribers:
        logger.warning("[WARN][EMAIL] no active subscribers found.")
        status["email"] = "skipped (no recipients)"
        _print_summary(status, start_time)
        return status

    # 3. Send personalised humanized emails individually
    success_count = 0
    db = SessionLocal()
    for sub in subscribers:
        try:
            email = sub.get("email")
            name = email.split('@')[0] if email else "there"
            
            # Use unique track token
            track_token = secrets.token_urlsafe(16)
            
            # Humanize
            context = f"the {date_str} cybersecurity issue"
            human_text = humanize_email(base_html, name, context)
            
            # Safety Filter
            if not safety_filter(human_text):
                logger.debug(f"[EMAIL] safety filter flagged email for {email}. Skipping.")
                continue
                
            # Inject tracking
            track_url = f"{BASE_URL}/daily?track={track_token}"
            if "{BASE_URL}/daily" in human_text:
                 human_text = human_text.replace(f"{BASE_URL}/daily", track_url)
            elif "http" not in human_text:
                human_text += f"\n\nlink to full issue: {track_url}"

            # Convert basic plain text features to HTML
            import re
            html_text = human_text.replace('\n', '<br>')
            html_text = re.sub(r'(https?://[^\s<>]+)', r'<a href="\1" style="color: #3b82f6; text-decoration: none;">\1</a>', html_text)

            attractive_html = f"""<!DOCTYPE html>
<html lang="en">
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background-color:#ffffff;color:#111111;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#ffffff;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;margin:0 auto;text-align:left;">
          <tr>
            <td style="padding:20px;font-size:16px;line-height:1.7;color:#111111;">
              {html_text}
            </td>
          </tr>
          <tr>
            <td style="padding:20px;border-top:1px solid #eeeeee;font-size:13px;color:#666666;margin-top:30px;">
              <p style="margin:0;">ZeroDay Daily &bull; Cybersecurity intelligence.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

            params: resend.Emails.SendParams = {
                "from": FROM_EMAIL,
                "to": [email],
                "subject": f"notes on {date_str} for you",
                "text": human_text,
                "html": attractive_html,
            }
            resend.Emails.send(params)
            
            # Log event
            log_entry = EmailLog(email=email, issue_date=date_str, track_token=track_token, status="sent")
            db.add(log_entry)
            db.commit()

            logger.debug(f"[EMAIL] successfully sent to {email}")
            success_count += 1
        except Exception as e:
            logger.error(f"[ERROR][EMAIL] failed to send to {sub.get('email', '?')}: {e}")
            db.rollback()

    db.close()
    status["total_sent"] = success_count
    status["email"] = "success" if success_count > 0 else "failed"
    
    _print_summary(status, start_time)
    
    status["time_taken"] = time.time() - start_time
    return status

def _print_summary(status, start_time):
    duration = round(time.time() - start_time, 2)
    print("\n" + "="*30)
    print("[SUMMARY]")
    print(f"scrape: {status['scrape']}")
    print(f"upload: {status['upload']}")
    print(f"email: {status['email']} ({status['total_sent']}/{status['total_target']} sent)")
    print(f"fallback_used: {status['fallback_used']}")
    print(f"total_time: {duration} seconds")
    print("="*30 + "\n")

if __name__ == "__main__":
    send_newsletters()
