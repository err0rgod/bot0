import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.db import DynamoDBClient, get_db_client

class TestDynamoDBClient(unittest.TestCase):
    @patch('lib.db.boto3.resource')
    def setUp(self, mock_boto_resource):
        # Setup mock Table
        self.mock_table = MagicMock()
        
        # Setup mock DynamoDB resource
        self.mock_dynamodb = MagicMock()
        self.mock_dynamodb.Table.return_value = self.mock_table
        mock_boto_resource.return_value = self.mock_dynamodb
        
        # Instantiate client (this will call _get_table)
        self.client = DynamoDBClient()

    def test_check_email_already_sent_true(self):
        # Mock get_item returning a sent status
        self.mock_table.get_item.return_value = {
            'Item': {
                'PK': 'EMAIL#user@example.com',
                'SK': 'LOG#2026-06-26',
                'status': 'sent'
            }
        }
        
        result = self.client.check_email_already_sent("user@example.com", "2026-06-26")
        self.assertTrue(result)
        self.mock_table.get_item.assert_called_once_with(
            Key={
                'PK': 'EMAIL#user@example.com',
                'SK': 'LOG#2026-06-26'
            }
        )

    def test_check_email_already_sent_false(self):
        # Mock get_item returning None
        self.mock_table.get_item.return_value = {}
        
        result = self.client.check_email_already_sent("user@example.com", "2026-06-26")
        self.assertFalse(result)

    def test_log_email_sent(self):
        self.client.log_email_sent("user@example.com", "2026-06-26", "track123")
        
        self.mock_table.put_item.assert_called_once()
        called_item = self.mock_table.put_item.call_args[1]['Item']
        self.assertEqual(called_item['PK'], 'EMAIL#user@example.com')
        self.assertEqual(called_item['SK'], 'LOG#2026-06-26')
        self.assertEqual(called_item['track_token'], 'track123')
        self.assertEqual(called_item['status'], 'sent')

    def test_get_active_subscribers(self):
        self.mock_table.scan.return_value = {
            'Items': [
                {
                    'PK': 'EMAIL#active1@example.com',
                    'SK': 'PROFILE',
                    'is_active': True,
                    'verified_email': True
                },
                {
                    'PK': 'EMAIL#active2@example.com',
                    'SK': 'PROFILE',
                    'email': 'active2@example.com',
                    'is_active': True,
                    'verified_email': True
                }
            ]
        }
        
        subscribers = self.client.get_active_subscribers()
        self.assertEqual(len(subscribers), 2)
        
        # Verify fallback email extraction from PK
        self.assertEqual(subscribers[0]['email'], 'active1@example.com')
        self.assertEqual(subscribers[1]['email'], 'active2@example.com')

if __name__ == "__main__":
    unittest.main()
