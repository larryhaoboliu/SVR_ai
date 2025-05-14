#!/bin/bash

# Site Visit Report App Deployment Script
# This script prepares both backend and frontend for deployment

# Exit on error
set -e

# Output colorization
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting deployment preparation for Site Visit Report App...${NC}"

# Create necessary directories if they don't exist
mkdir -p scripts/logs

# Backend preparation
echo -e "${GREEN}Preparing backend for deployment...${NC}"
cd backend

# Check for virtual environment
if [ ! -d "../venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python -m venv ../venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source ../venv/bin/activate

# Install production dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt

# Create production .env if it doesn't exist
if [ ! -f ".env.production" ]; then
    echo -e "${YELLOW}Creating production .env file template...${NC}"
    cat > .env.production << EOF
# Production Environment Variables
FLASK_ENV=production
DEBUG=False
PORT=5001
HOST=0.0.0.0
ALLOWED_ORIGINS=https://your-frontend-url.com
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_key_here
AWS_REGION=your-region
S3_BUCKET=your-s3-bucket
MONGO_URI=mongodb://your-mongodb-uri
LOG_LEVEL=WARNING
API_KEY=your_internal_api_key_here
EOF
    echo -e "${YELLOW}Please edit .env.production with your actual values${NC}"
fi

# Run tests
echo "Running backend tests..."
python -m pytest test_security.py -v || { echo -e "${RED}Backend tests failed. Please fix any issues before deploying.${NC}"; exit 1; }

# Check for vector store
if [ ! -f "vector_store.pkl" ]; then
    echo -e "${RED}Warning: vector_store.pkl not found. The RAG service may not work properly.${NC}"
fi

echo -e "${GREEN}Backend preparation complete.${NC}"

# Go back to project root
cd ..

# Frontend preparation
echo -e "${GREEN}Preparing frontend for deployment...${NC}"
cd frontend

# Install dependencies
echo "Installing frontend dependencies..."
npm install

# Create production build
echo "Creating optimized production build..."
npm run build

echo -e "${GREEN}Frontend preparation complete.${NC}"

# Go back to project root
cd ..

# Create deployment archive
echo "Creating deployment archive..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ZIP_NAME="site-visit-report-app_${TIMESTAMP}.zip"

# Exclude unnecessary files
echo "Creating .deployignore file..."
cat > .deployignore << EOF
node_modules/
venv/
__pycache__/
*.pyc
.git/
.github/
.vscode/
.idea/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.DS_Store
frontend/node_modules/
frontend/.pnp
frontend/.pnp.js
frontend/coverage
frontend/build
frontend/.DS_Store
frontend/.env.local
frontend/.env.development.local
frontend/.env.test.local
frontend/.env.production.local
*.pkl
EOF

# Create deployment zip
echo "Zipping deployment package..."
zip -r "$ZIP_NAME" . -x@.deployignore

echo -e "${GREEN}Deployment preparation complete. Archive created: ${ZIP_NAME}${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review and update the .env.production file with actual values"
echo "2. If deploying to Heroku, run: heroku create your-app-name"
echo "3. Set environment variables on your hosting platform"
echo "4. Deploy the application using the platform-specific instructions"
echo ""
echo -e "${GREEN}For Heroku deployment:${NC}"
echo "git push heroku main"
echo ""
echo -e "${GREEN}For AWS Elastic Beanstalk:${NC}"
echo "eb deploy"
echo ""
echo -e "${GREEN}For frontend deployment to Netlify/Vercel:${NC}"
echo "Follow the specific platform instructions in the README"

# Cleanup
rm .deployignore

echo -e "${GREEN}Deployment preparation script completed successfully.${NC}" 