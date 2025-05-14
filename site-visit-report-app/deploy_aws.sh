#!/bin/bash

# Exit on error
set -e

# Output colorization
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting AWS deployment for Site Visit Report App...${NC}"

# Create necessary directories if they don't exist
mkdir -p backend/feedback
mkdir -p logs

# 1. Backend Preparation
echo -e "${GREEN}1. Preparing backend for AWS deployment...${NC}"

# Create production .env file
echo -e "${YELLOW}Creating .env.production file template...${NC}"
cat > backend/.env.production << EOF
# Production Environment Variables
FLASK_ENV=production
DEBUG=False
PORT=5001
HOST=0.0.0.0

# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=your_aws_region
S3_BUCKET=your_s3_bucket_name

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=your_pinecone_index_name

# Security Settings
ALLOWED_ORIGINS=https://your-frontend-url.com
API_KEY=your_internal_api_key_here
LOG_LEVEL=WARNING

# Database Settings (optional - for storing feedback)
# MONGO_URI=mongodb://your-mongodb-uri
EOF

echo -e "${YELLOW}Please edit backend/.env.production with your actual values${NC}"

# 2. Create AWS Elastic Beanstalk configuration
echo -e "${GREEN}2. Creating AWS Elastic Beanstalk configuration...${NC}"

# Create Procfile for Elastic Beanstalk
cat > Procfile << EOF
web: cd backend && gunicorn --workers=3 --threads=3 -b 0.0.0.0:\$PORT app:app
EOF

# Create requirements.txt at the root
cp backend/requirements.txt ./requirements.txt
echo "gunicorn==20.1.0" >> requirements.txt
echo "awsebcli==3.20.3" >> requirements.txt

# Create .ebignore to exclude unnecessary files
cat > .ebignore << EOF
frontend/
frontend/node_modules/
frontend/build/
.git/
.github/
.vscode/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
ENV/
.env
.env.*
!backend/.env.production
*.log
*.zip
*.pkl
EOF

# Create EB config file
mkdir -p .elasticbeanstalk
cat > .elasticbeanstalk/config.yml << EOF
branch-defaults:
  main:
    environment: site-visit-report-env
global:
  application_name: site-visit-report
  default_platform: Python 3.9
  default_region: us-west-2
  profile: eb-cli
  sc: git
EOF

echo -e "${YELLOW}Update .elasticbeanstalk/config.yml with your preferred region${NC}"

# 3. Frontend Preparation
echo -e "${GREEN}3. Preparing frontend for deployment...${NC}"

# Create frontend configuration with API endpoint
cat > frontend/.env.production << EOF
REACT_APP_BACKEND_URL=https://your-elastic-beanstalk-url.elasticbeanstalk.com
EOF

echo -e "${YELLOW}Please edit frontend/.env.production with your actual backend URL${NC}"

# Install dependencies
echo -e "${GREEN}Installing frontend dependencies...${NC}"
cd frontend
npm install

# Build frontend
echo -e "${GREEN}Building frontend for production...${NC}"
npm run build

cd ..

# 4. Create Amazon S3 configuration for frontend
echo -e "${GREEN}4. Creating S3 configuration for frontend hosting...${NC}"

# Create S3 bucket policy
cat > s3_policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    }
  ]
}
EOF

echo -e "${YELLOW}Please edit s3_policy.json with your actual S3 bucket name for frontend hosting${NC}"

# 5. Create deployment instructions
echo -e "${GREEN}5. Creating deployment instructions...${NC}"

cat > DEPLOYMENT.md << EOF
# Deployment Instructions

## Backend Deployment (AWS Elastic Beanstalk)

1. Install EB CLI:
   \`\`\`
   pip install awsebcli
   \`\`\`

2. Initialize EB application (if you haven't already):
   \`\`\`
   eb init
   \`\`\`
   - Choose your region
   - Enter your application name
   - Choose Python platform
   - Set up CodeCommit (optional)

3. Create a new environment:
   \`\`\`
   eb create site-visit-report-env
   \`\`\`

4. Deploy your application:
   \`\`\`
   eb deploy
   \`\`\`

5. Set environment variables:
   \`\`\`
   eb setenv $(cat backend/.env.production)
   \`\`\`

6. Get the URL of your application:
   \`\`\`
   eb status
   \`\`\`

## Frontend Deployment (AWS S3 + CloudFront)

1. Create an S3 bucket:
   \`\`\`
   aws s3 mb s3://your-site-visit-report-app
   \`\`\`

2. Configure bucket for static website hosting:
   \`\`\`
   aws s3 website s3://your-site-visit-report-app --index-document index.html --error-document index.html
   \`\`\`

3. Apply bucket policy for public read:
   \`\`\`
   aws s3api put-bucket-policy --bucket your-site-visit-report-app --policy file://s3_policy.json
   \`\`\`

4. Upload frontend build files:
   \`\`\`
   aws s3 sync frontend/build/ s3://your-site-visit-report-app --acl public-read
   \`\`\`

5. (Optional) Set up CloudFront for CDN and HTTPS:
   - Create a CloudFront distribution
   - Set origin to your S3 website endpoint
   - Configure HTTPS
   - Create a more user-friendly domain with Route 53

## Update Frontend with Backend URL

After deploying the backend, update the frontend .env.production with the Elastic Beanstalk URL,
rebuild the frontend, and redeploy to S3:

1. Edit frontend/.env.production with your EB URL
2. Rebuild: \`cd frontend && npm run build\`
3. Redeploy: \`aws s3 sync frontend/build/ s3://your-site-visit-report-app --acl public-read\`

## Monitoring and Maintenance

- Monitor your application with AWS CloudWatch
- Set up alarms for errors and high CPU usage
- Regularly check logs in Elastic Beanstalk console
- Consider implementing AWS Lambda for automated backups

EOF

echo -e "${GREEN}Deployment preparation completed!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review and update all configuration files with your actual values"
echo "2. Follow instructions in DEPLOYMENT.md to deploy your application"
echo "3. Set up monitoring and maintenance as needed"
echo ""
echo -e "${GREEN}Happy deploying!${NC}" 