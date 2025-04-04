import os
import logging
import tempfile

# Bot token from environment variable
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# User agent for requests
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Maximum file size for Telegram (50 MB in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Directory for temporary file downloads
DOWNLOAD_DIR = os.path.join(tempfile.gettempdir(), 'telegram_downloads')

# Make sure the download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)