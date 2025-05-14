#!/usr/bin/env python3
"""
This script modifies the Flask app for AWS deployment by making
necessary changes to support S3 storage and configuring Pinecone.
"""

import os
import sys
import re

# Define the app.py file path
APP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')

# Backup the original file
BACKUP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py.bak')

def backup_original():
    """Create a backup of the original app.py file"""
    if os.path.exists(APP_FILE) and not os.path.exists(BACKUP_FILE):
        with open(APP_FILE, 'r') as src:
            with open(BACKUP_FILE, 'w') as dest:
                dest.write(src.read())
        print(f"Backed up original app.py to {BACKUP_FILE}")

def modify_app_for_aws():
    """Modify the app.py file for AWS deployment"""
    if not os.path.exists(APP_FILE):
        print(f"Error: {APP_FILE} not found")
        return False

    # Read the contents of the app.py file
    with open(APP_FILE, 'r') as f:
        content = f.read()

    # Modifications to make

    # 1. Add S3 imports and configuration
    s3_imports = """import boto3
from botocore.exceptions import ClientError
"""
    
    s3_config = """
# Configure S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)
S3_BUCKET = os.getenv('S3_BUCKET')
"""

    # Check if imports are already added
    if 'import boto3' not in content:
        # Add imports after other imports
        import_section_end = content.find('# Configure logging')
        if import_section_end != -1:
            content = content[:import_section_end] + s3_imports + content[import_section_end:]
            print("Added S3 imports")
        
        # Add S3 configuration after environment variables
        env_section_end = content.find('# Anthropic API Key')
        if env_section_end != -1:
            content = content[:env_section_end] + s3_config + content[env_section_end:]
            print("Added S3 configuration")

    # 2. Modify image and PDF storage to use S3
    
    # Replace local storage with S3 for generated reports
    if 'def _generate_pdf_using_reportlab' in content:
        # Update the PDF generation to save to S3
        local_pdf_save = "doc.build(content)"
        s3_pdf_save = """doc.build(content)
        
        # If S3 bucket is configured, upload the PDF to S3
        if S3_BUCKET:
            try:
                s3_key = f"reports/Site_Visit_Report_{report_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                s3_client.upload_file(
                    pdf_filename, 
                    S3_BUCKET, 
                    s3_key,
                    ExtraArgs={'ContentType': 'application/pdf'}
                )
                logger.info(f"Uploaded PDF to S3: {s3_key}")
                
                # Generate a pre-signed URL for the file
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': S3_BUCKET, 'Key': s3_key},
                    ExpiresIn=3600 * 24 * 7  # URL valid for 7 days
                )
                
                # Set metadata to include S3 info
                @response.call_on_close
                def update_metadata():
                    if hasattr(response, '_headers'):
                        response._headers.add('X-S3-Location', s3_key)
                        response._headers.add('X-S3-Presigned-URL', presigned_url)
            except Exception as s3_error:
                logger.error(f"Failed to upload PDF to S3: {str(s3_error)}")
        """
        content = content.replace(local_pdf_save, s3_pdf_save)
        print("Updated PDF generation to use S3")

    # 3. Update CORS configuration for production
    cors_config = "CORS(app, resources={r\"/*\": {\"origins\": allowed_origins}})"
    if cors_config in content:
        updated_cors = """# Setup CORS with configured origins
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
logger.info(f"Allowing CORS for origins: {allowed_origins}")
CORS(app, resources={r"/*": {"origins": allowed_origins}})"""
        content = content.replace(cors_config, updated_cors)
        print("Updated CORS configuration")

    # 4. Add AWS environment detection
    if "if __name__ == \"__main__\":" in content:
        local_run = "app.run(debug=True, port=5001)"
        aws_run = """# Get port from environment variable (for AWS Elastic Beanstalk)
    port = int(os.getenv('PORT', 5001))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)"""
        content = content.replace(local_run, aws_run)
        print("Updated app.run for AWS environment")

    # Write the modified content back to the file
    with open(APP_FILE, 'w') as f:
        f.write(content)

    print(f"Successfully modified {APP_FILE} for AWS deployment")
    return True

if __name__ == "__main__":
    backup_original()
    if modify_app_for_aws():
        print("Modifications completed successfully")
    else:
        print("Modifications failed") 