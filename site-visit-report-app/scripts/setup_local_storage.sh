#!/bin/bash

# Script to set up local storage configuration for the Site Visit Report App

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  Site Visit Report App - Local Storage  ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}Error: Please run this script from the root directory of the project (site-visit-report-app)${NC}"
    exit 1
fi

# Create .env file
ENV_FILE="backend/.env"

echo -e "${YELLOW}Setting up local storage configuration...${NC}"

# Check if .env already exists
if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Warning: $ENV_FILE already exists.${NC}"
    read -p "Do you want to overwrite it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Setup aborted. Existing .env file was not modified.${NC}"
        exit 0
    fi
fi

# Ask for Anthropic API key
echo -e "${YELLOW}Please enter your Anthropic API key (required for image analysis):${NC}"
read -p "Anthropic API Key: " anthropic_key

# Create the .env file
cat > "$ENV_FILE" << EOL
# Storage configuration
STORAGE_TYPE=local

# Anthropic API configuration (required for image analysis)
ANTHROPIC_API_KEY=$anthropic_key

# Vector storage configuration (using local FAISS by default)
# PINECONE_API_KEY=your_pinecone_api_key
# PINECONE_ENVIRONMENT=your_pinecone_environment
# PINECONE_INDEX_NAME=svr-product-data
EOL

# Create necessary directories
mkdir -p backend/local_storage/photos
mkdir -p backend/local_storage/product_data
mkdir -p backend/local_storage/reports
mkdir -p backend/product_data

# Set permissions
chmod 755 backend/local_storage
chmod 755 backend/local_storage/photos
chmod 755 backend/local_storage/product_data
chmod 755 backend/local_storage/reports
chmod 755 backend/product_data

echo -e "${GREEN}Local storage configuration complete!${NC}"
echo -e "${GREEN}Created directories:${NC}"
echo "  - backend/local_storage/photos"
echo "  - backend/local_storage/product_data"
echo "  - backend/local_storage/reports"
echo "  - backend/product_data"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Start the backend server: cd backend && python app.py"
echo "2. Start the frontend: cd frontend && npm start"
echo ""
echo -e "${GREEN}Happy testing!${NC}" 