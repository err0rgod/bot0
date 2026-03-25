import os
import sys
from dotenv import load_dotenv

# Try loading .env from right next to this script, and then falling back to parent folder
load_dotenv(override=True)
parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(parent_env, override=True)

conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = os.getenv("AZURE_CONTAINER_NAME", "news")

print("=== Azure Blob Storage Connection Test ===")
if not conn_str:
    print("❌ ERROR: AZURE_STORAGE_CONNECTION_STRING is not found in the environment variables.")
    sys.exit(1)

print(f"✅ Found AZURE_STORAGE_CONNECTION_STRING")
print(f"ℹ️ Configured Container Name: {container_name}")

try:
    print("\nAttempting to connect to Azure and initialize BlobServiceClient...")
    from azure.storage.blob import BlobServiceClient
    blob_service = BlobServiceClient.from_connection_string(conn_str)
    
    print(f"✅ Successfully authenticated with Azure Storage Account!")
    
    print("\nGetting container client...")
    container_client = blob_service.get_container_client(container_name)
    
    if not container_client.exists():
        print(f"ℹ️ Container '{container_name}' does not exist. Creating it now...")
        container_client.create_container()
        print(f"✅ Container '{container_name}' created.")
    else:
        print(f"✅ Container '{container_name}' already exists.")
        
    print("\nAttempting to upload a test blob ('connection_test.txt')...")
    blob_client = container_client.get_blob_client("connection_test.txt")
    blob_client.upload_blob("Testing Azure Blob Storage connection...", overwrite=True)
    print(f"✅ Test blob uploaded successfully.")
    
    print("\nAttempting to read the test blob back...")
    downloaded_blob = blob_client.download_blob().readall()
    print(f"✅ Content read: '{downloaded_blob.decode('utf-8')}'")
    
    print("\n🎉 Connection test passed completely!")
    
except ImportError:
    print("❌ ERROR: The 'azure-storage-blob' package is not installed.")
    print("Please install it using: pip install azure-storage-blob")
except Exception as e:
    print(f"❌ ERROR: An exception occurred during the test:")
    print(e)
    sys.exit(1)
