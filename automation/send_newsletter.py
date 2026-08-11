import os
import sys
import time
import json
import logging
from html import escape

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
from lib.db import get_db_client

# Configure logging
logger = logging.getLogger(__name__)

resend.api_key = os.getenv("RESEND_API_KEY", "")
# Assume DB is handled externally or ready





import asyncio


def _build_roast_email(roasts: list, issue_url: str) -> tuple[str, str]:
    """Build the plain-text and HTML versions of the roast-only newsletter."""
    clean_roasts = [str(roast).strip() for roast in roasts if str(roast).strip()]

    text_parts = clean_roasts + [
        f"Read the full issue: {issue_url}",
        "ZeroDay Daily • Cybersecurity intelligence.",
    ]
    text_body = "\n\n".join(text_parts)

    roast_html = "".join(
        f'<p style="margin:0 0 24px;font-size:17px;line-height:1.7;color:#111111;">'
        f'{escape(roast).replace(chr(10), "<br>")}</p>'
        for roast in clean_roasts
    )
    escaped_issue_url = escape(issue_url, quote=True)
    html_body = f"""<!DOCTYPE html>
<html lang="en">
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background-color:#ffffff;color:#111111;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#ffffff;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;margin:0 auto;text-align:left;">
          <tr>
            <td style="padding:20px;">
              {roast_html}
              <table cellpadding="0" cellspacing="0" style="margin-top:32px;">
                <tr>
                  <td style="border-radius:8px;background:#111827;">
                    <a href="{escaped_issue_url}" style="display:inline-block;padding:14px 24px;color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;border-radius:8px;">Read the full issue</a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:20px;border-top:1px solid #eeeeee;font-size:13px;color:#666666;">
              <p style="margin:0;">ZeroDay Daily &bull; Cybersecurity intelligence.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    return text_body, html_body

async def send_newsletters():
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

    # 2. Fetch subscribers
    sub_start = time.time()
    db = get_db_client()
    subscribers = db.get_active_subscribers()
    status["total_target"] = len(subscribers)

    if not subscribers:
        logger.warning("[WARN][EMAIL] no active subscribers found.")
        status["email"] = "skipped (no recipients)"
        _print_summary(status, start_time)
        return status

    # 3. Send a roast-only teaser with a unique tracked issue link.
    success_count = 0
    for sub in subscribers:
        try:
            email = sub.get("email")
            
            # Idempotency Check: Skip if already sent today
            if db.check_email_already_sent(email, date_str):
                logger.info(f"[EMAIL] idempotency check passed: skipping {email}, already sent for issue {date_str}.")
                continue
                
            # Use unique track token
            track_token = secrets.token_urlsafe(16)
            track_url = f"{BASE_URL}/daily?track={track_token}"
            roasts = latest_issue.get("roast_summary", [])
            text_body, html_body = _build_roast_email(roasts, track_url)

            params: resend.Emails.SendParams = {
                "from": FROM_EMAIL,
                "to": [email],
                "subject": f"notes on {date_str} for you",
                "text": text_body,
                "html": html_body,
            }
            resend.Emails.send(params)
            
            # Log event to DynamoDB
            db.log_email_sent(email, date_str, track_token, "sent")

            logger.debug(f"[EMAIL] successfully sent to {email}")
            success_count += 1
        except Exception as e:
            logger.error(f"[ERROR][EMAIL] failed to send to {sub.get('email', '?')}: {e}")

    status["total_sent"] = success_count
    
    if success_count > 0:
        status["email"] = "success"
    else:
        if len(subscribers) > 0 and success_count == 0:
            status["email"] = "skipped (already sent today)"
        else:
            status["email"] = "failed"
    
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
    print(f"total_time: {duration} seconds")
    print("="*30 + "\n")

def lambda_handler(event, context):
    """
    AWS Lambda Entry Point for Dispatcher.
    Triggered manually or via S3 Upload EventBridge rule.
    """
    logger.info("Lambda invocation Triggered - starting Email Dispatch cycle.")
    return asyncio.run(send_newsletters())

if __name__ == "__main__":
    asyncio.run(send_newsletters())
