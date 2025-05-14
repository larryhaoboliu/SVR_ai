import os
import uuid
import base64
import logging
from datetime import datetime
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base directory for local storage
STORAGE_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "local_storage")

class LocalStorage:
    """
    Storage implementation using local filesystem for site visit photos and product data files
    """
    
    def __init__(self):
        """Initialize local storage"""
        # Ensure base storage directory exists
        os.makedirs(STORAGE_BASE_DIR, exist_ok=True)
        
        # Create subdirectories
        self.photos_dir = os.path.join(STORAGE_BASE_DIR, "photos")
        self.product_data_dir = os.path.join(STORAGE_BASE_DIR, "product_data")
        self.reports_dir = os.path.join(STORAGE_BASE_DIR, "reports")
        
        os.makedirs(self.photos_dir, exist_ok=True)
        os.makedirs(self.product_data_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        logger.info(f"Local storage initialized at {STORAGE_BASE_DIR}")
    
    def upload_file(self, file_data, file_name, directory='general'):
        """
        Upload a file to local storage
        
        Args:
            file_data: File data as bytes or file-like object
            file_name: Name of the file
            directory: Subdirectory in the storage (e.g., 'photos', 'product_data')
            
        Returns:
            Path of the stored file or None if upload fails
        """
        try:
            # Determine the target directory
            if directory == 'photos':
                target_dir = self.photos_dir
            elif directory == 'product-data':
                target_dir = self.product_data_dir
            else:
                target_dir = os.path.join(STORAGE_BASE_DIR, directory)
                os.makedirs(target_dir, exist_ok=True)
            
            # Generate a unique file name to avoid overwrites
            file_extension = file_name.split('.')[-1] if '.' in file_name else ''
            unique_file_name = f"{uuid.uuid4().hex}"
            if file_extension:
                unique_file_name = f"{unique_file_name}.{file_extension}"
                
            # Generate a path with date organization
            date_prefix = datetime.now().strftime('%Y/%m/%d')
            date_dir = os.path.join(target_dir, *date_prefix.split('/'))
            os.makedirs(date_dir, exist_ok=True)
            
            file_path = os.path.join(date_dir, unique_file_name)
            
            # Write the file data to disk
            if hasattr(file_data, 'read'):
                # If it's a file-like object
                with open(file_path, 'wb') as f:
                    f.write(file_data.read())
            else:
                # If it's bytes
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                    
            logger.info(f"Successfully saved file to {file_path}")
            
            # Return file details
            relative_path = os.path.relpath(file_path, STORAGE_BASE_DIR)
            return {
                'path': file_path,
                'relative_path': relative_path,
                'original_filename': file_name
            }
        
        except Exception as e:
            logger.error(f"Error saving file locally: {e}")
            return None
    
    def upload_base64_image(self, base64_data, original_filename=None, directory='photos'):
        """
        Upload a base64 encoded image to local storage
        
        Args:
            base64_data: Base64 encoded image data (without 'data:image/...' prefix)
            original_filename: Original filename (optional)
            directory: Subdirectory in the storage
            
        Returns:
            Path of the stored file or None if upload fails
        """
        try:
            # Convert base64 to binary
            # If the data includes the prefix (data:image/...), remove it
            if base64_data.startswith('data:'):
                base64_data = base64_data.split(',')[1]
            
            file_data = BytesIO(base64.b64decode(base64_data))
            
            # Default filename if none provided
            if not original_filename:
                original_filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            
            # Upload using the standard method
            return self.upload_file(file_data, original_filename, directory)
            
        except Exception as e:
            logger.error(f"Error saving base64 image locally: {e}")
            return None
    
    def get_file(self, path):
        """
        Get a file from local storage by path
        
        Args:
            path: Path to the file, either absolute or relative to STORAGE_BASE_DIR
            
        Returns:
            File data as bytes or None if retrieval fails
        """
        try:
            # If path is relative, make it absolute
            if not os.path.isabs(path):
                path = os.path.join(STORAGE_BASE_DIR, path)
                
            # Check if file exists
            if not os.path.exists(path):
                logger.error(f"File not found: {path}")
                return None
                
            # Read and return the file data
            with open(path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error retrieving file: {e}")
            return None
    
    def delete_file(self, path):
        """
        Delete a file from local storage by path
        
        Args:
            path: Path to the file, either absolute or relative to STORAGE_BASE_DIR
            
        Returns:
            True if deletion succeeds, False otherwise
        """
        try:
            # If path is relative, make it absolute
            if not os.path.isabs(path):
                path = os.path.join(STORAGE_BASE_DIR, path)
                
            # Check if file exists
            if not os.path.exists(path):
                logger.error(f"File not found: {path}")
                return False
                
            # Delete the file
            os.remove(path)
            logger.info(f"Successfully deleted file {path}")
            
            return True
                
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

# Singleton instance
_local_storage = None

def get_local_storage():
    """Get or create the local storage singleton."""
    global _local_storage
    if _local_storage is None:
        _local_storage = LocalStorage()
    return _local_storage 