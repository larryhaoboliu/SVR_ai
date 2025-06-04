import os
import logging
from dotenv import load_dotenv

# Import local storage (always available)
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
        try:
            # Import S3 storage only when needed
            from .s3_storage import get_s3_storage
            logger.info("Using S3 storage")
            return get_s3_storage()
        except ImportError as e:
            logger.error(f"S3 storage requested but dependencies not available: {e}")
            logger.info("Falling back to local storage")
            return get_local_storage()
    else:
        logger.info("Using local file storage")
        return get_local_storage() 