#!/bin/bash

# Site Visit Report App Testing Deployment Script
# This script helps deploy the app for testing with ngrok

# Exit on error
set -e

# Output colorization
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting test deployment for Site Visit Report App...${NC}"

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}ngrok is not installed. Please install it first:${NC}"
    echo "npm install -g ngrok"
    echo "or"
    echo "brew install ngrok"
    exit 1
fi

# Create deployment directories if they don't exist
mkdir -p scripts/logs

# Function to check if a port is in use
is_port_in_use() {
    if lsof -Pi :"$1" -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Check if frontend port is in use
if is_port_in_use 3000; then
    echo -e "${YELLOW}Port 3000 is already in use. Frontend may be running.${NC}"
else
    echo -e "${RED}Frontend is not running. Please start it in another terminal:${NC}"
    echo "cd frontend && npm start"
    exit 1
fi

# Check if backend port is in use
if is_port_in_use 5001; then
    echo -e "${YELLOW}Port 5001 is already in use. Backend may be running.${NC}"
else
    echo -e "${RED}Backend is not running. Please start it in another terminal:${NC}"
    echo "cd backend && python app.py"
    exit 1
fi

# Create a browser-based feedback link to add to the app
echo -e "${GREEN}Creating feedback URL...${NC}"
FEEDBACK_URL="https://forms.gle/YOUR_GOOGLE_FORM_ID"
echo "Feedback URL: $FEEDBACK_URL"
echo "You can create a Google Form for feedback and update this URL in the script."

# Expose the frontend with ngrok
echo -e "${GREEN}Exposing frontend on port 3000 with ngrok...${NC}"
echo "This terminal will be used by ngrok. Press Ctrl+C to stop exposure when done testing."
echo "The ngrok URL will be displayed below. Share this URL with your testers."

# Run ngrok in the foreground
ngrok http 3000

echo -e "${GREEN}Test deployment ended.${NC}" 