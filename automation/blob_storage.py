from azure.storage.blob import BlobServiceClient
import os
import logging
from datetime import datetime
from azure.core.exceptions import ResourceNotFoundError, ServiceRequestError
import time

class BlobStorageService:
    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = os.getenv("AZURE_STORAGE_BLOB_CONTAINER_NAME")
        self.current_reservation_folder = None
        self.current_attempt = None
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        if not self.connection_string or not self.container_name:
            raise ValueError("Missing blob storage configuration in environment variables")
            
        # Log which environment is being used
        if "devstoreaccount1" in self.connection_string:
            logging.info("Using Azurite (local) storage emulator")
        else:
            logging.info("Using Azure Portal storage")
            
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.container_name)
        
    def _retry_operation(self, operation, *args, **kwargs):
        """Helper method to retry operations with exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except (ServiceRequestError, ResourceNotFoundError) as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay * (2 ** attempt))
        
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
            
            # Upload the file with retry logic
            def upload_operation():
                blob_client = self.container_client.get_blob_client(blob_name)
                with open(local_file_path, "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)
                return blob_name
            
            blob_name = self._retry_operation(upload_operation)
            logging.info(f"Uploaded screenshot {blob_name} to blob storage")
            
        except Exception as e:
            logging.error(f"Failed to upload screenshot: {str(e)}")
            raise
            
    def upload_log_file(self, local_file_path, log_name):
        """Upload a log file to blob storage in the correct attempt folder"""
        try:
            if not self.current_reservation_folder or self.current_attempt is None:
                raise ValueError("No active reservation context")

            # Generate blob name with folder structure
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            blob_name = f"{self.current_reservation_folder}/Attempt_{self.current_attempt}/{log_name}_{timestamp}.log"

            # Upload the file with retry logic
            def upload_operation():
                blob_client = self.container_client.get_blob_client(blob_name)
                with open(local_file_path, "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)
                return blob_name

            blob_name = self._retry_operation(upload_operation)
            logging.info(f"Uploaded log file {blob_name} to blob storage")

        except Exception as e:
            logging.error(f"Failed to upload log file: {str(e)}")
            raise
            
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

    def get_screenshots(self, date, time):
        """Get screenshots for a specific date and time"""
        try:
            # Format the folder path
            folder_path = f"{date}_{time}"
            
            # List all blobs in the folder with retry logic
            def list_blobs_operation():
                return list(self.container_client.list_blobs(name_starts_with=folder_path))
            
            blobs = self._retry_operation(list_blobs_operation)
            
            # Group screenshots by attempt number
            screenshots = {}
            
            def get_screenshot_sort_key(screenshot_name):
                # Extract the filename from the full path
                filename = screenshot_name.split('/')[-1]
                # Try to extract the leading number
                try:
                    number = float(filename.split('.')[0])
                    return (0, number)  # Numbered screenshots come first
                except (ValueError, IndexError):
                    return (1, filename)  # Non-numbered screenshots come last
            
            for blob in blobs:
                # Extract attempt number from blob name
                parts = blob.name.split('/')
                if len(parts) >= 3:  # Ensure we have the correct path structure
                    attempt = parts[1]  # e.g., "Attempt_1"
                    if attempt not in screenshots:
                        screenshots[attempt] = []
                    
                    # Create a proxy URL instead of using direct blob URL
                    proxy_url = f"/blob-image/{blob.name}"
                    screenshots[attempt].append({
                        'url': proxy_url,
                        'name': blob.name
                    })
            
            # Sort screenshots in each attempt
            for attempt in screenshots:
                screenshots[attempt].sort(key=lambda x: get_screenshot_sort_key(x['name']))
            
            return screenshots
            
        except Exception as e:
            logging.error(f"Failed to get screenshots: {str(e)}")
            return {}
            
    def get_blob_with_cache_headers(self, blob_path):
        """Get blob data with cache headers"""
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            blob_properties = self._retry_operation(blob_client.get_blob_properties)
            
            # Get blob data with retry logic
            def download_blob_operation():
                return blob_client.download_blob().readall()
            
            blob_data = self._retry_operation(download_blob_operation)
            
            # Set cache headers
            headers = {
                'Content-Type': 'image/png',
                'Cache-Control': 'public, max-age=31536000',  # Cache for 1 year
                'ETag': blob_properties.etag,
                'Last-Modified': blob_properties.last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')
            }
            
            return blob_data, headers
            
        except Exception as e:
            logging.error(f"Failed to get blob with cache headers: {str(e)}")
            raise 