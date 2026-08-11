import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.send_newsletter import _build_roast_email


class TestNewsletterEmail(unittest.TestCase):
    def test_builds_roast_only_email_with_issue_link(self):
        issue_url = "https://zerodaily.in/daily?track=test-token"
        roasts = [
            "A firewall rule this open is basically a welcome mat.",
            "They rotated passwords right after the attackers rotated the data.",
        ]

        text_body, html_body = _build_roast_email(roasts, issue_url)

        for roast in roasts:
            self.assertIn(roast, text_body)
            self.assertIn(roast, html_body)
        self.assertIn(f"Read the full issue: {issue_url}", text_body)
        self.assertIn(f'href="{issue_url}"', html_body)
        self.assertNotIn("Top stories", text_body)
        self.assertNotIn("story_html", html_body)

    def test_escapes_roast_html(self):
        _, html_body = _build_roast_email(
            ["<script>alert('nope')</script>"],
            "https://zerodaily.in/daily?track=test-token",
        )

        self.assertNotIn("<script>", html_body)
        self.assertIn("&lt;script&gt;", html_body)


if __name__ == "__main__":
    unittest.main()
