import os
import tempfile
import logging
import requests
from typing import Tuple, Optional
import random
import string
import time

from config import USER_AGENT, MAX_FILE_SIZE, DOWNLOAD_DIR

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        
        # Create download directory if it doesn't exist
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)
    
    def download_file(self, url: str, filename: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Download a file from a given URL
        
        Args:
            url: URL of the file to download
            filename: Optional filename to use
            
        Returns:
            Tuple of (success: bool, file_path: Optional[str], error_message: Optional[str])
        """
        if not url:
            return False, None, "URL is empty"
        
        try:
            # Generate a random filename if not provided
            if not filename:
                # Generate a random string for the filename
                random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                
                # Use .torrent extension for torrent files
                if url.endswith('.torrent'):
                    filename = f"movie_{random_string}.torrent"
                else:
                    filename = f"file_{random_string}"
            
            # Create a full path to save the file
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            
            # Download the file
            logger.info(f"Downloading file from {url}")
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Check file size before downloading
            content_length = int(response.headers.get('Content-Length', 0))
            if content_length > MAX_FILE_SIZE:
                return False, None, f"File too large ({content_length / (1024*1024):.2f} MB)"
            
            # Save the file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"File downloaded successfully to {file_path}")
            return True, file_path, None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading file: {str(e)}")
            return False, None, f"Download error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False, None, f"Unexpected error: {str(e)}"
    
    def cleanup_file(self, file_path: str) -> None:
        """
        Remove a temporary file
        
        Args:
            file_path: Path to the file to remove
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {str(e)}")