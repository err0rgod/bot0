import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Clear environment variables or set dummy ones to trigger S3 client path
os.environ["S3_BUCKET_NAME"] = "test-bucket"

from lib.content import get_issue_dates, get_issue_data, get_latest_issue, _blob_cache

class TestContent(unittest.TestCase):
    def setUp(self):
        # Set dummy bucket in environment for tests
        os.environ["S3_BUCKET_NAME"] = "test-bucket"
        # Reset simple cache before each test
        _blob_cache["dates"] = None
        _blob_cache["issues"] = {}
        _blob_cache["last_checked"] = 0

    @patch('boto3.client')
    def test_get_issue_dates(self, mock_s3_client_cls):
        # Setup mock S3 response
        mock_s3 = MagicMock()
        mock_s3_client_cls.return_value = mock_s3
        
        mock_s3.list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'issue_2026-06-25.json'},
                {'Key': 'issue_2026-06-26.json'},
                {'Key': 'issue_invalid-date.json'}, # should be skipped
                {'Key': 'some_other_file.txt'} # should be skipped
            ]
        }
        
        dates = get_issue_dates()
        self.assertEqual(dates, ["2026-06-26", "2026-06-25"])
        mock_s3.list_objects_v2.assert_called_once_with(Bucket="test-bucket", Prefix="issue_")

    @patch('boto3.client')
    def test_get_issue_data(self, mock_s3_client_cls):
        mock_s3 = MagicMock()
        mock_s3_client_cls.return_value = mock_s3
        
        issue_content = {
            "date": "2026-06-26",
            "top_stories": [{"title": "Story 1"}],
            "cves": []
        }
        
        # Mock body read
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps(issue_content).encode('utf-8')
        mock_s3.get_object.return_value = {'Body': mock_body}
        
        data = get_issue_data("2026-06-26")
        self.assertEqual(data, issue_content)
        mock_s3.get_object.assert_called_once_with(Bucket="test-bucket", Key="issue_2026-06-26.json")

    @patch('lib.content.get_issue_dates')
    @patch('lib.content.get_issue_data')
    def test_get_latest_issue(self, mock_get_issue_data, mock_get_issue_dates):
        mock_get_issue_dates.return_value = ["2026-06-26", "2026-06-25"]
        mock_get_issue_data.return_value = {"date": "2026-06-26"}
        
        latest = get_latest_issue()
        self.assertEqual(latest, {"date": "2026-06-26"})
        mock_get_issue_data.assert_called_once_with("2026-06-26")

if __name__ == "__main__":
    unittest.main()
