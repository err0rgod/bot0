import unittest
from unittest.mock import AsyncMock, patch
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.humanizer import safety_filter, humanize_email, _fallback_humanize

class TestHumanizer(unittest.TestCase):
    def test_safety_filter_valid(self):
        valid_text = "Hey Nirbhay,\n\nI found some interesting threat intelligence today.\nHere is the link: [ISSUE_LINK]\n\nHope this helps, let me know if this helps!"
        self.assertTrue(safety_filter(valid_text))

    def test_safety_filter_forbidden_words(self):
        # Contains forbidden marketing words
        invalid_words = [
            "Hey Nirbhay,\n\nThis exciting new update is here!\n[ISSUE_LINK]",
            "Hey Nirbhay,\n\nIntroducing our latest launch!\n[ISSUE_LINK]",
            "Hey Nirbhay,\n\nCheck out the new features!\n[ISSUE_LINK]"
        ]
        for text in invalid_words:
            self.assertFalse(safety_filter(text))

    def test_safety_filter_html(self):
        # Contains HTML
        html_text = "Hey Nirbhay,\n\nI saw this <b>CVE-2026-1234</b>.\n[ISSUE_LINK]"
        self.assertFalse(safety_filter(html_text))

    def test_safety_filter_length(self):
        # Too short (less than 3 lines)
        short_text = "Hey Nirbhay, check this: [ISSUE_LINK]"
        self.assertFalse(safety_filter(short_text))
        
        # Too long (more than 10 lines)
        long_text = "\n".join([f"Line {i} [ISSUE_LINK]" for i in range(12)])
        self.assertFalse(safety_filter(long_text))

    def test_fallback_humanize(self):
        fallback = _fallback_humanize("Nirbhay", "cybersecurity news")
        self.assertIn("Nirbhay", fallback)
        self.assertIn("cybersecurity news", fallback)
        self.assertTrue(safety_filter(fallback))

    @patch('lib.humanizer.LLMClient')
    def test_humanize_email_success(self, mock_llm_client_cls):
        # Setup mock client
        mock_client = AsyncMock()
        mock_llm_client_cls.return_value = mock_client
        
        # LLM returns a safe humanized email
        safe_response = "Hey Nirbhay,\n\nI saw a critical vulnerability in standard router OS.\nHere is the link: [ISSUE_LINK]\n\nlet me know if this helps!"
        mock_client.generate.return_value = safe_response
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        result = loop.run_until_complete(humanize_email("<h1>Sample</h1>", "Nirbhay", "updates"))
        
        self.assertEqual(result, safe_response)
        mock_client.generate.assert_called_once()

    @patch('lib.humanizer.LLMClient')
    def test_humanize_email_fails_safety_falls_back(self, mock_llm_client_cls):
        mock_client = AsyncMock()
        mock_llm_client_cls.return_value = mock_client
        
        # LLM returns something that fails safety (e.g. contains forbidden marketing words)
        unsafe_response = "Hey Nirbhay,\n\nThis is an exciting new launch with amazing features!\n[ISSUE_LINK]"
        mock_client.generate.return_value = unsafe_response
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        result = loop.run_until_complete(humanize_email("<h1>Sample</h1>", "Nirbhay", "updates"))
        
        # Should fallback to fallback text
        self.assertEqual(result, _fallback_humanize("Nirbhay", "updates"))

if __name__ == "__main__":
    unittest.main()
