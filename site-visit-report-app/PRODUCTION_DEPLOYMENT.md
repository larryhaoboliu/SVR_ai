# Complete Production Deployment Guide

This guide outlines the step-by-step process to deploy your Site Visit Report app to AWS, leveraging your existing AWS and Pinecone setup.

## Prerequisites

- AWS account with appropriate permissions
- Anthropic API key for Claude
- Existing AWS S3 bucket (or permission to create one)
- Existing Pinecone setup
- AWS CLI installed and configured
- Elastic Beanstalk CLI installed

## Deployment Steps

### 1. Prepare for Deployment

Run the deployment preparation script:

```bash
cd site-visit-report-app
./deploy_aws.sh
```

This script will:
- Create necessary configuration files
- Set up environment templates
- Build the frontend
- Prepare AWS configuration templates

### 2. Update Configuration Values

After running the script, you need to update several files with your actual values:

1. **Backend Environment Variables** (`backend/.env.production`):
   - Update your Anthropic API key
   - Add your AWS credentials and S3 bucket information
   - Configure your Pinecone settings
   - Set allowed origins for CORS
   - Set a secure internal API key

2. **Frontend Environment** (`frontend/.env.production`):
   - After deploying the backend, update with your Elastic Beanstalk URL

3. **S3 Bucket Policy** (`s3_policy.json`):
   - Replace `YOUR-BUCKET-NAME` with your actual S3 bucket name for frontend hosting

4. **Elastic Beanstalk Config** (`.elasticbeanstalk/config.yml`):
   - Update the region and other settings as needed

### 3. Deploy the Backend (AWS Elastic Beanstalk)

```bash
# Initialize EB application (if first time)
eb init

# Create a new environment
eb create site-visit-report-env

# Deploy your application
eb deploy

# Set environment variables from your .env.production file
eb setenv $(cat backend/.env.production)
```

### 4. Get the Backend URL

```bash
eb status
```

Note the environment URL (e.g., `http://site-visit-report-env.eba-xyz123.us-west-2.elasticbeanstalk.com`)

### 5. Update Frontend Configuration

Edit `frontend/.env.production` with your backend URL:

```
REACT_APP_BACKEND_URL=https://your-elastic-beanstalk-url.elasticbeanstalk.com
```

Rebuild the frontend:

```bash
cd frontend
npm run build
cd ..
```

### 6. Deploy the Frontend (AWS S3)

```bash
# Create S3 bucket (if needed)
aws s3 mb s3://your-site-visit-report-app

# Configure for static website hosting
aws s3 website s3://your-site-visit-report-app --index-document index.html --error-document index.html

# Apply bucket policy for public access
aws s3api put-bucket-policy --bucket your-site-visit-report-app --policy file://s3_policy.json

# Upload the frontend files
aws s3 sync frontend/build/ s3://your-site-visit-report-app --acl public-read
```

### 7. Set Up CloudFront (Optional but Recommended)

1. Create a CloudFront distribution in the AWS Console
2. Set the origin to your S3 website endpoint
3. Configure HTTPS
4. Set appropriate cache behaviors
5. Create a distribution

### 8. Configure Storage for Uploaded Data

By default, data will be stored as follows:

- **Uploaded Images**: Will be stored in your S3 bucket
- **Generated Reports**: Will be stored in your S3 bucket
- **Feedback Data**: Will be stored in the database or in JSON files on the Elastic Beanstalk instance
- **Vector Database**: Pinecone will store your vector embeddings

Make sure your S3 bucket has appropriate lifecycle policies and permissions.

### 9. Set Up Monitoring and Alerts

1. Configure CloudWatch monitoring for your Elastic Beanstalk environment
2. Set up alerts for:
   - High CPU usage
   - Memory issues
   - Error rates
   - Response times

### 10. Regular Maintenance

1. Set up automated backups for your data
2. Regularly check logs for errors
3. Monitor usage and scale resources as needed
4. Update dependencies as needed

## Useful Commands

```bash
# View Elastic Beanstalk logs
eb logs

# SSH into your EB instance
eb ssh

# Terminate an environment (caution!)
eb terminate environment-name

# List S3 buckets
aws s3 ls

# Remove files from S3
aws s3 rm s3://your-bucket/path/to/file

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id DISTRIBUTION_ID --paths "/*"
```

## Troubleshooting

1. **CORS Issues**:
   - Check that `ALLOWED_ORIGINS` in your backend environment variables includes your frontend URL

2. **Permission Problems**:
   - Verify IAM roles for Elastic Beanstalk have permission to access S3 and other services

3. **Deployment Failures**:
   - Check EB logs with `eb logs`
   - Ensure your application works locally before deploying

4. **Frontend Not Loading**:
   - Verify S3 bucket policy allows public access
   - Check CloudFront distribution settings

## Additional Resources

- [AWS Elastic Beanstalk Documentation](https://docs.aws.amazon.com/elasticbeanstalk/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/)
- [AWS CloudFront Documentation](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/)
- [Pinecone Documentation](https://docs.pinecone.io/) 