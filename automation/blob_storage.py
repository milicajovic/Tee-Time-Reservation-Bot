from azure.storage.blob import BlobServiceClient
import os
import uuid
import logging
from datetime import datetime

class BlobStorageService:
    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = os.getenv("AZURE_STORAGE_BLOB_CONTAINER_NAME")
        self.session_id = str(uuid.uuid4())
        self.screenshot_urls = []
        self.success_screenshot_url = None
        
        if not self.connection_string or not self.container_name:
            raise ValueError("Missing blob storage configuration in environment variables")
            
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.container_name)
        
    def start_new_session(self):
        """Start a new session with a fresh session_id"""
        self.session_id = str(uuid.uuid4())
        self.screenshot_urls = []
        self.success_screenshot_url = None
        logging.info(f"Started new session with ID: {self.session_id}")
        
    def upload_screenshot(self, local_file_path, method_name):
        """Upload a screenshot to blob storage and return its URL"""
        try:
            # Generate blob name with session_id/method_timestamp.png format
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            blob_name = f"{self.session_id}/{method_name}_{timestamp}.png"
            
            # Upload the file
            blob_client = self.container_client.get_blob_client(blob_name)
            with open(local_file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            
            # Get the public URL
            url = blob_client.url
            self.screenshot_urls.append(url)
            logging.info(f"Uploaded screenshot {blob_name} to blob storage")
            return url
            
        except Exception as e:
            logging.error(f"Failed to upload screenshot: {str(e)}")
            return None
            
    def get_screenshot_urls(self):
        """Return all screenshot URLs from the current session"""
        return self.screenshot_urls
        
    def set_success_screenshot(self, url):
        """Set the success screenshot URL for the current session"""
        self.success_screenshot_url = url
        logging.info(f"Set success screenshot URL: {url}")
        
    def get_success_screenshot_url(self):
        """Get the success screenshot URL for the current session"""
        return self.success_screenshot_url 