import os
import logging
from dotenv import load_dotenv

# Import storage implementations
from .s3_storage import get_s3_storage
from .local_storage import get_local_storage

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get storage type from environment variable
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local").lower()

def get_storage():
    """
    Factory function to get the appropriate storage implementation
    based on the STORAGE_TYPE environment variable.
    
    Returns:
        Storage implementation instance
    """
    if STORAGE_TYPE == "s3":
        logger.info("Using S3 storage")
        return get_s3_storage()
    else:
        logger.info("Using local file storage")
        return get_local_storage() 