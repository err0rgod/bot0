import os
import resend
from dotenv import load_dotenv

load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY", "")

email = "nirbhayerror@gmail.com"
BASE_URL = os.getenv("BASE_URL", "https://zerodaily.in").rstrip("/")
FROM_EMAIL = "ZeroDay Daily <news@zerodaily.in>"

# Simulating human_text from the newsletter logic
test_human_text = """hey nirbhayerror,

here are your notes on 2026-04-14 for you.

it seems a new CVE just dropped regarding a critical vulnerability.
Read more about it below.

https://zerodaily.in/daily?track=test1234
"""

html_text = test_human_text.replace('\n', '<br>')
import re
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

params = {
    "from": FROM_EMAIL,
    "to": [email],
    "subject": f"notes on 2026-04-14 for you",
    "text": test_human_text,
    "html": attractive_html,
}

try:
    response = resend.Emails.send(params)
    print(f"Mail sent! Response: {response}")
except Exception as e:
    print(f"Error sending mail: {e}")
