import os
import datetime
import logging
import boto3
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger(__name__)

_DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "ZeroDaily-DB")

def _get_table():
    region = os.getenv("AWS_REGION", "us-east-1")
    dynamodb = boto3.resource('dynamodb', region_name=region)
    return dynamodb.Table(_DYNAMODB_TABLE_NAME)

def init_db():
    """
    In AWS Serverless architecture, table provisioning should be handled 
    by Infrastructure as Code (Terraform/CloudFormation) or the AWS Console.
    This function is a no-op to prevent breaking legacy initialization chains.
    """
    logger.info(f"[DB] Initialized DynamoDB connection to table: {_DYNAMODB_TABLE_NAME}")

class DynamoDBClient:
    """Serverless client wrapper for DynamoDB operations."""
    
    def __init__(self):
        self.table = _get_table()
        
    def check_email_already_sent(self, email: str, issue_date: str) -> bool:
        """
        Idempotency check: Queries DynamoDB to verify if a newsletter was 
        already sent to the specific user for the specific date.
        
        Expected Schema:
        PK: EMAIL#<user_email>
        SK: LOG#<issue_date>
        """
        try:
            response = self.table.get_item(
                Key={
                    'PK': f'EMAIL#{email}',
                    'SK': f'LOG#{issue_date}'
                }
            )
            item = response.get('Item')
            return bool(item and item.get('status') == 'sent')
        except Exception as e:
            logger.error(f"[DB ERROR] Failed to check email log in DynamoDB: {e}")
            # Fail safe: return False to allow sending, or True to block? 
            # We return False to prioritize delivery, but log the error.
            return False

    def log_email_sent(self, email: str, issue_date: str, track_token: str, status: str = "sent"):
        """
        Records the successful dispatch of an email to DynamoDB.
        """
        try:
            self.table.put_item(
                Item={
                    'PK': f'EMAIL#{email}',
                    'SK': f'LOG#{issue_date}',
                    'type': 'EmailLog',
                    'track_token': track_token,
                    'status': status,
                    'sent_at': datetime.datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"[DB ERROR] Failed to add email log to DynamoDB: {e}")
            raise e

    def get_active_subscribers(self) -> list:
        """
        Scans DynamoDB for all active subscribers.
        
        Note: For very large datasets, a Global Secondary Index (GSI) on 
        `is_active` combined with a query is heavily recommended over `scan()`.
        """
        try:
            response = self.table.scan(
                FilterExpression=Attr('type').eq('Subscriber') & Attr('is_active').eq(True)
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"[DB ERROR] Failed fetching subscribers from DynamoDB: {e}")
            return []

def get_db_client() -> DynamoDBClient:
    """Dependency injection friendly client generator."""
    return DynamoDBClient()
