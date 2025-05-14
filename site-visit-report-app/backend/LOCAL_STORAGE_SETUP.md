# Local Storage Setup Guide

This guide explains how to configure the Site Visit Report App to use local storage for all data inputs during testing.

## Overview

The application can be configured to store files in two ways:
1. **Local Storage**: Files are stored on the local filesystem
2. **S3 Storage**: Files are stored in AWS S3 buckets

For testing purposes, local storage is recommended as it doesn't require AWS credentials or incur any costs.

## Configuration Steps

### 1. Create a .env file

Create a file named `.env` in the `backend` directory with the following content:

```
# Storage configuration
STORAGE_TYPE=local

# Anthropic API configuration (required for image analysis)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Vector storage configuration (using local FAISS by default)
# Leave the following commented out to use local FAISS
# PINECONE_API_KEY=your_pinecone_api_key
# PINECONE_ENVIRONMENT=your_pinecone_environment
# PINECONE_INDEX_NAME=svr-product-data
```

Make sure to replace `your_anthropic_api_key_here` with your actual Anthropic API key.

### 2. Directory Structure

When using local storage, the application will automatically create the following directory structure:

```
backend/
├── local_storage/
│   ├── photos/           # Uploaded images
│   │   └── YYYY/MM/DD/   # Date-organized folders
│   ├── product_data/     # Product data sheets
│   │   └── YYYY/MM/DD/   # Date-organized folders
│   └── reports/          # Generated PDF reports
│       └── YYYY/MM/DD/   # Date-organized folders
├── product_data/         # Product data for RAG indexing
└── ...
```

### 3. Start the Application

Start the application normally. The first time you upload files, the necessary directories will be created automatically.

## File Storage Details

- **Images**: When you upload images through the analyze-image endpoint, they will be saved in `backend/local_storage/photos/YYYY/MM/DD/` with unique filenames.
- **Product Data Sheets**: Product data sheets will be saved in both:
  - `backend/local_storage/product_data/YYYY/MM/DD/` for storage
  - `backend/product_data/` for RAG indexing
- **PDF Reports**: Generated PDF reports will be saved in `backend/local_storage/reports/YYYY/MM/DD/` with unique filenames.

## Switching to S3 Storage

If you later decide to use S3 storage, update your `.env` file with:

```
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET=your_bucket_name
``` 