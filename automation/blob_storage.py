from azure.storage.blob import BlobServiceClient
import os
import logging
from datetime import datetime

class BlobStorageService:
    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = os.getenv("AZURE_STORAGE_BLOB_CONTAINER_NAME")
        self.current_reservation_folder = None
        self.current_attempt = None
        
        if not self.connection_string or not self.container_name:
            raise ValueError("Missing blob storage configuration in environment variables")
            
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.container_name)
        
    def set_reservation_context(self, row_key, retry_count):
        """Set the current reservation context for uploading screenshots"""
        self.current_reservation_folder = row_key
        self.current_attempt = retry_count
        logging.info(f"Set reservation context: folder={row_key}, attempt={retry_count}")
        
    def upload_screenshot(self, local_file_path, method_name):
        """Upload a screenshot to blob storage in the correct attempt folder"""
        try:
            if not self.current_reservation_folder or self.current_attempt is None:
                raise ValueError("No active reservation context")
                
            # Generate blob name with folder structure
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            blob_name = f"{self.current_reservation_folder}/Attempt_{self.current_attempt}/{method_name}_{timestamp}.png"
            
            # Upload the file
            blob_client = self.container_client.get_blob_client(blob_name)
            with open(local_file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            
            logging.info(f"Uploaded screenshot {blob_name} to blob storage")
            
        except Exception as e:
            logging.error(f"Failed to upload screenshot: {str(e)}")
            
    def get_reservation_folder_url(self):
        """Get the URL for the current reservation folder"""
        if self.current_reservation_folder:
            # Get the storage account name from environment variable
            account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
            if not account_name:
                raise ValueError("AZURE_STORAGE_ACCOUNT_NAME environment variable is not set")
            
            # Construct the Azure Storage URL
            container_url = f"https://{account_name}.blob.core.windows.net/{self.container_name}"
            folder_url = f"{container_url}/{self.current_reservation_folder}"
            return folder_url
        return None 