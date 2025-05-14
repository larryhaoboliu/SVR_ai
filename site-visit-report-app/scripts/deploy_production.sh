#!/bin/bash

# Site Visit Report App Production Deployment Script
# This script prepares the application for production deployment

# Exit on error
set -e

# Output colorization
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Set deployment environment
DEPLOY_ENV="production"

echo -e "${YELLOW}Starting production deployment for Site Visit Report App...${NC}"

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
pip install gunicorn  # Make sure gunicorn is installed

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

# Create production environment file
cat > .env.production << EOF
REACT_APP_BACKEND_URL=https://your-backend-url.com
EOF
echo -e "${YELLOW}Please edit frontend/.env.production with your actual backend URL${NC}"

# Create optimized production build
echo "Creating optimized production build..."
npm run build

echo -e "${GREEN}Frontend preparation complete.${NC}"

# Go back to project root
cd ..

# Create deployment archive
echo "Creating deployment package..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ZIP_NAME="site-visit-report-app_${TIMESTAMP}.zip"

# Create .deployignore file
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
frontend/.DS_Store
frontend/.env.local
frontend/.env.development.local
frontend/.env.test.local
frontend/.env.production.local
*.pkl
backend/feedback/
EOF

# Create deployment zip
echo "Zipping deployment package..."
zip -r "$ZIP_NAME" . -x@.deployignore

echo -e "${GREEN}Deployment preparation complete. Archive created: ${ZIP_NAME}${NC}"

# Deployment instructions
echo ""
echo -e "${YELLOW}Next steps for deployment:${NC}"
echo "1. Review and update the backend/.env.production file with actual values"
echo "2. Review and update the frontend/.env.production file with your backend URL"
echo "3. Deploy the backend to your chosen platform (Heroku, AWS, etc.)"
echo "4. Deploy the frontend build directory to a static hosting service (Netlify, Vercel, etc.)"
echo ""
echo -e "${GREEN}For Heroku backend deployment:${NC}"
echo "git push heroku main"
echo ""
echo -e "${GREEN}For AWS Elastic Beanstalk backend deployment:${NC}"
echo "eb deploy"
echo ""
echo -e "${GREEN}For Netlify frontend deployment:${NC}"
echo "netlify deploy --prod -d frontend/build"
echo ""
echo -e "${GREEN}For Vercel frontend deployment:${NC}"
echo "vercel --prod frontend"

# Cleanup
rm .deployignore

echo -e "${GREEN}Production deployment preparation script completed successfully.${NC}" 