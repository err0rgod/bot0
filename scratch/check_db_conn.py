import os
import sys
import boto3
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from lib.db import get_db_client

def test_connection():
    region = os.getenv("AWS_REGION")
    table_name = os.getenv("DYNAMODB_TABLE_NAME")
    print(f"Testing connection to {table_name} in {region}...")
    
    try:
        client = get_db_client()
        # Ping the table using describe-table-like behavior (checking if it exists)
        table = client.table
        status = table.table_status
        print(f"Success! Table status: {status}")
        
        # Try a sample scan
        items = client.get_active_subscribers()
        print(f"Subscribers found: {len(items)}")
        
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_connection()
