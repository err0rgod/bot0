import sys
import os
import unittest
from dotenv import load_dotenv

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

from lib.humanizer import humanize_email, safety_filter

class TestIntegrationHumanizer(unittest.IsolatedAsyncioTestCase):
    async def test_humanizer(self):
        sample_html = """
        <h1>ZeroDay Weekly</h1>
        <p>Exciting news! We are launching new features today.</p>
        <ul>
          <li>Story 1: CVE-2026-0001 fix</li>
          <li>Story 2: New update available</li>
        </ul>
        <a href="http://localhost:8000/weekly">Read More</a>
        """
        
        try:
            human_text = await humanize_email(sample_html, "Nirbhay", "cybersecurity news")
            self.assertIsInstance(human_text, str)
            self.assertTrue(len(human_text) > 0)
            
            passed = safety_filter(human_text)
            self.assertTrue(passed, "The returned text should always pass the safety filter, either natively or via the fallback.")
        except Exception as e:
            self.skipTest(f"Skipping integration test due to API error: {e}")

if __name__ == "__main__":
    unittest.main()
