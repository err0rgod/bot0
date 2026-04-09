import json
import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

# Load .env before importing modules that read env at import time.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), override=True)

# Add project root to import local modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.notifications import FROM_EMAIL, send_custom_email, validate_sender_domain

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BLOG_URL = "https://zerodaily.in"
DEFAULT_BLOG_TITLE = os.getenv("BLOG_ALERT_TITLE", "A new blog has dropped on ZeroDaily")
DEFAULT_SUBJECT = os.getenv("BLOG_ALERT_SUBJECT", "New blog dropped on ZeroDaily")


def _fetch_subscribers_from_local() -> list[dict]:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.getenv("DATA_DIR", os.path.join(project_root, "data"))
    subscribers_path = os.path.join(data_dir, "subscribers.json")

    if not os.path.exists(subscribers_path):
        logger.warning("No local subscribers.json found at %s", subscribers_path)
        return []

    try:
        with open(subscribers_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return [s for s in data if s.get("is_active", True) and s.get("email")]
    except Exception as exc:
        logger.error("Failed to read local subscribers.json: %s", exc)
        return []


def _fetch_subscribers_from_blob() -> list[dict]:
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_CONTAINER_NAME", "news")

    if not conn_str:
        logger.warning("No Azure connection string found. Falling back to local subscribers.json")
        return _fetch_subscribers_from_local()

    try:
        from azure.storage.blob import BlobServiceClient

        blob_service = BlobServiceClient.from_connection_string(conn_str)
        container_client = blob_service.get_container_client(container_name)
        blob_client = container_client.get_blob_client("subscribers.json")
        data = json.loads(blob_client.download_blob().readall().decode("utf-8-sig"))
        return [s for s in data if s.get("is_active", True) and s.get("email")]
    except Exception as exc:
        logger.warning("Cloud subscriber fetch failed (%s). Falling back to local file.", exc)
        return _fetch_subscribers_from_local()


def _build_blog_email_html(blog_title: str, blog_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<body style="margin:0;padding:0;background-color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e2e8f0;">
          <tr>
            <td style="padding:36px 40px;text-align:center;">
              <div style="display:inline-block;background:#f3e8ff;border-radius:6px;padding:6px 14px;margin-bottom:16px;">
                <span style="color:#7e22ce;font-size:12px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;">ZeroDay Weekly</span>
              </div>
              <h1 style="margin:0;color:#0f172a;font-size:24px;">New blog just dropped</h1>
              <p style="margin:16px 0 0;color:#475569;font-size:16px;line-height:1.6;">
                {blog_title}
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 40px 40px;text-align:center;">
              <a href="{blog_url}" style="display:inline-block;padding:12px 28px;background:#7c3aed;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;">
                Read the latest blog
              </a>
              <p style="margin:14px 0 0;color:#64748b;font-size:13px;word-break:break-all;">
                Or open this link: <a href="{blog_url}" style="color:#7c3aed;">{blog_url}</a>
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:18px 40px;background:#f8fafc;border-top:1px solid #e2e8f0;text-align:center;">
              <p style="margin:0;color:#94a3b8;font-size:12px;">
                Sent on {datetime.utcnow().strftime("%Y-%m-%d")} by ZeroDay Weekly
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_blog_alert(blog_url: str = BLOG_URL, blog_title: str = DEFAULT_BLOG_TITLE, subject: str = DEFAULT_SUBJECT) -> bool:
    sender_ok, sender_reason = validate_sender_domain(FROM_EMAIL)
    if not sender_ok:
        logger.error("Sender validation failed for %r. %s", FROM_EMAIL, sender_reason)
        return False

    subscribers = _fetch_subscribers_from_blob()
    recipients = [s["email"] for s in subscribers if s.get("email")]
    if not recipients:
        logger.warning("No active subscribers found.")
        return False

    final_subject = subject
    html_body = _build_blog_email_html(blog_title, blog_url)

    logger.info("Sending blog alert to %d subscribers", len(recipients))
    ok = send_custom_email(recipients, final_subject, html_body)
    if ok:
        logger.info("Blog alert sent successfully.")
    else:
        logger.error("Blog alert sending failed.")
    return ok


def main() -> int:
    success = send_blog_alert()
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
