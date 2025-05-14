import os
import boto3
from datetime import datetime
import logging
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from io import BytesIO
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class S3Storage:
    """
    Storage implementation using AWS S3 for site visit photos and product data files
    """
    
    def __init__(self):
        """Initialize S3 client using environment variables"""
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region_name = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = os.getenv('S3_BUCKET')
        
        if not self.aws_access_key or not self.aws_secret_key or not self.bucket_name:
            logger.warning("AWS credentials or bucket name not provided. S3 storage will not work.")
            self.is_configured = False
        else:
            self.is_configured = True
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region_name
            )
    
    def upload_file(self, file_data, file_name, directory='general'):
        """
        Upload a file to S3
        
        Args:
            file_data: File data as bytes or file-like object
            file_name: Name of the file
            directory: Subdirectory in the bucket (e.g., 'photos', 'product-data')
            
        Returns:
            URL of the uploaded file or None if upload fails
        """
        if not self.is_configured:
            logger.error("S3 storage not configured. Cannot upload file.")
            return None
        
        # Generate a unique file name to avoid overwrites
        file_extension = file_name.split('.')[-1] if '.' in file_name else ''
        unique_file_name = f"{uuid.uuid4().hex}"
        if file_extension:
            unique_file_name = f"{unique_file_name}.{file_extension}"
            
        # Generate a path with date organization
        date_prefix = datetime.now().strftime('%Y/%m/%d')
        key = f"{directory}/{date_prefix}/{unique_file_name}"
        
        try:
            # Upload the file
            self.s3_client.upload_fileobj(
                file_data,
                self.bucket_name,
                key
            )
            
            # Generate the URL for the file
            url = f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{key}"
            logger.info(f"Successfully uploaded file to {url}")
            return {
                'url': url,
                'key': key,
                'bucket': self.bucket_name,
                'original_filename': file_name
            }
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            return None
    
    def upload_base64_image(self, base64_data, original_filename=None, directory='photos'):
        """
        Upload a base64 encoded image to S3
        
        Args:
            base64_data: Base64 encoded image data (without 'data:image/...' prefix)
            original_filename: Original filename (optional)
            directory: Subdirectory in the bucket
            
        Returns:
            URL of the uploaded image or None if upload fails
        """
        if not self.is_configured:
            logger.error("S3 storage not configured. Cannot upload image.")
            return None
        
        try:
            # Convert base64 to binary
            import base64
            
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
            logger.error(f"Error uploading base64 image: {e}")
            return None
    
    def get_file(self, key):
        """
        Get a file from S3 by key
        
        Args:
            key: S3 key for the file
            
        Returns:
            File data as bytes or None if retrieval fails
        """
        if not self.is_configured:
            logger.error("S3 storage not configured. Cannot retrieve file.")
            return None
        
        try:
            # Get the file from S3
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            # Return the file data
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Error retrieving file from S3: {e}")
            return None
    
    def delete_file(self, key):
        """
        Delete a file from S3 by key
        
        Args:
            key: S3 key for the file
            
        Returns:
            True if deletion succeeds, False otherwise
        """
        if not self.is_configured:
            logger.error("S3 storage not configured. Cannot delete file.")
            return False
        
        try:
            # Delete the file from S3
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            logger.info(f"Successfully deleted file {key}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False

# Singleton instance
_s3_storage = None

def get_s3_storage():
    """Get or create the S3 storage singleton."""
    global _s3_storage
    if _s3_storage is None:
        _s3_storage = S3Storage()
    return _s3_storage 