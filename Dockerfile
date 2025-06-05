# Multi-stage build for optimized deployment
FROM node:18-alpine as frontend-build
WORKDIR /app

# Copy package files first for better caching
COPY site-visit-report-app/frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy all frontend source files
COPY site-visit-report-app/frontend/ ./

# Set environment variables
ENV REACT_APP_API_URL=/api
ENV GENERATE_SOURCEMAP=false
ENV CI=false

# Build the application
RUN npm run build

# Python backend
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY site-visit-report-app/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY site-visit-report-app/backend/ ./

# Copy built frontend
COPY --from=frontend-build /app/build ./static

# Create directories
RUN mkdir -p local_storage/photos local_storage/product_data local_storage/reports feedback

# Set environment variables
ENV PORT=8080
ENV STORAGE_TYPE=local

EXPOSE 8080

# Start the application
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app 