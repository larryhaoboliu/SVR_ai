# Site Visit Report Application

A web application for creating and managing site visit reports with AI-powered image analysis and report generation.

## Environment Setup

This project uses a virtual environment to manage dependencies and avoid conflicts with other projects.

### Setting Up the Virtual Environment

1. Navigate to the project directory:
   ```bash
   cd /path/to/site-visit-report-app
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. Make sure your virtual environment is activated

2. Start the backend server:
   ```bash
   cd backend
   python app.py
   ```
   The backend will run on http://localhost:5001

3. In a separate terminal, activate the virtual environment again and start the frontend:
   ```bash
   cd frontend
   npm install    # Only needed first time
   npm start
   ```
   The frontend will run on http://localhost:3000

### Deactivating the Virtual Environment

When you're done working on the project, you can deactivate the virtual environment:
```bash
deactivate
```

## Application Structure

- `backend/`: Flask server with API endpoints for image analysis and report generation
- `frontend/`: React application for the user interface
- `venv/`: Virtual environment (not included in version control)
- `requirements.txt`: Python dependencies

## Dependencies

The main dependencies are:
- Flask: Web server
- FastAPI: API framework
- LangChain: Framework for AI applications
- sentence-transformers: For embedding and similarity search
- FAISS: Vector database for fast similarity search
- Reportlab: PDF generation
- PyPDF2: PDF processing
- React: Frontend framework

Check `requirements.txt` for the full list of Python dependencies. 

## Environment Variables

The application requires certain environment variables to be set in order to function properly. Create a `.env` file in the backend directory with the following variables:

### Required Variables
- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude models
- `STORAGE_TYPE`: Storage type to use - 'local' or 's3' (default: 'local')

### AWS S3 Variables (Only required if STORAGE_TYPE=s3)
- `AWS_ACCESS_KEY_ID`: AWS access key for S3 storage
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for S3 storage
- `AWS_REGION`: AWS region (e.g., us-east-1)
- `S3_BUCKET`: S3 bucket name for storing reports and images

### Optional Variables
- `PORT`: Port to run the backend server (default: 5001)
- `HOST`: Host to run the backend server (default: 0.0.0.0)
- `FLASK_ENV`: Flask environment (development/production)
- `DEBUG`: Enable/disable debug mode (True/False)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins for CORS
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `MAX_CONTENT_LENGTH`: Maximum allowed upload size in bytes
- `ADMIN_PASSWORD`: Password for accessing admin features and API endpoints

### Vector Storage Variables (Optional)
- `PINECONE_API_KEY`: Pinecone API key for vector storage
- `PINECONE_ENVIRONMENT`: Pinecone environment
- `PINECONE_INDEX_NAME`: Pinecone index name (default: svr-product-data)

### Storage Configuration

The application supports two storage modes:

#### Local Storage (Default)

For testing and development, the application can store all files locally. This is the default mode and requires no additional configuration.

When using local storage:
- Images are stored in `backend/local_storage/photos/`
- Product data sheets are stored in `backend/local_storage/product_data/`
- Generated PDF reports are stored in `backend/local_storage/reports/`

All files are organized in date-based subdirectories (YYYY/MM/DD) with unique filenames.

To use local storage, set in your `.env` file:
```
STORAGE_TYPE=local
```

For detailed instructions on local storage setup, see `backend/LOCAL_STORAGE_SETUP.md`.

#### S3 Storage (Production)

For production use, the application can store files in Amazon S3 buckets.

To use S3 storage, set in your `.env` file:
```
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET=your_bucket_name
```

## Deployment Instructions

### Testing Deployment with ngrok

For quick testing with real users before a full production deployment:

1. Install ngrok:
   ```bash
   npm install -g ngrok
   # or with Homebrew
   brew install ngrok
   ```

2. Start both backend and frontend servers:
   ```bash
   # Terminal 1: Start backend
   cd backend
   python app.py
   
   # Terminal 2: Start frontend
   cd frontend
   npm start
   ```

3. Run the test deployment script:
   ```bash
   cd site-visit-report-app
   bash scripts/deploy_test.sh
   ```
   
4. Share the ngrok URL with your testers. The script will display a public URL that forwards to your local development server.

5. User feedback will be collected in two ways:
   - Through the in-app feedback button
   - Saved to `backend/feedback/*.json` files

### Backend Deployment

#### Option 1: Heroku Deployment
1. Install Heroku CLI and log in:
   ```bash
   npm install -g heroku
   heroku login
   ```

2. Create a Heroku app:
   ```bash
   heroku create your-app-name
   ```

3. Add a Procfile to the root directory:
   ```
   web: cd backend && gunicorn app:app
   ```

4. Configure environment variables on Heroku:
   ```bash
   heroku config:set OPENAI_API_KEY=your_key_here
   # Add all other required variables
   ```

5. Deploy the application:
   ```bash
   git push heroku main
   ```

#### Option 2: AWS Elastic Beanstalk
1. Install EB CLI:
   ```bash
   pip install awsebcli
   ```

2. Initialize EB application:
   ```bash
   cd backend
   eb init
   ```

3. Create an environment:
   ```bash
   eb create your-environment-name
   ```

4. Configure environment variables in the EB environment

5. Deploy:
   ```bash
   eb deploy
   ```

### Frontend Deployment

#### Option 1: Netlify
1. Install Netlify CLI:
   ```bash
   npm install -g netlify-cli
   netlify login
   ```

2. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```

3. Deploy to Netlify:
   ```bash
   netlify deploy --prod
   ```

#### Option 2: Vercel
1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   vercel login
   ```

2. Deploy to Vercel:
   ```bash
   cd frontend
   vercel --prod
   ```

## API Documentation

The backend provides the following API endpoints:

### Image Analysis
- `POST /analyze-image`: Analyze an image and provide insights
  - Request: `multipart/form-data` with `image` field
  - Response: JSON with analysis results

### Report Generation
- `POST /generate-report`: Generate a PDF report
  - Request: JSON with report data
  - Response: URL to generated PDF

### Product Information
- `GET /list-product-data`: List available product information
  - Response: JSON list of available products

For a complete API reference, refer to the API documentation in the `/docs` endpoint (e.g., http://localhost:5001/docs) when running the application. 

## Production Deployment Checklist

Before deploying to production, ensure the following:

1. **Environment Variables**:
   - Update all environment variables in `.env.production`
   - Ensure API keys have appropriate rate limiting
   - Set `FLASK_ENV=production` and `DEBUG=False`

2. **CORS Configuration**:
   - Update the `ALLOWED_ORIGINS` to include only your production domains

3. **Security**:
   - Enable HTTPS for all communications
   - Set proper Content Security Policy headers
   - Configure proper rate limiting
   - Use a strong API key for internal authentication

4. **Database**:
   - Set up a proper database for feedback storage (MongoDB or SQL)
   - Configure backup procedures

5. **Monitoring**:
   - Set up application monitoring (e.g., Prometheus, Grafana)
   - Configure error alerting (e.g., Sentry)

6. **Scaling**:
   - Consider using PM2 or Gunicorn for the backend
   - Configure auto-scaling if needed

7. **CI/CD**:
   - Set up CI/CD pipelines for automatic testing and deployment
   - Configure staging environment for pre-production testing

8. **Analytics**:
   - Set up usage analytics to track feature usage
   - Configure feedback monitoring dashboard

9. **Documentation**:
   - Update API documentation
   - Create user guide for testers

## Access Code Management System

The Site Visit Report application includes a comprehensive access code management system for controlling tester access to the application during development and testing phases.

### Features

- **Invitation-based Access**: Testers need a valid access code to use the application
- **Time-limited Access**: Codes automatically expire after a configurable period
- **Usage Limits**: Each code has a limited number of uses
- **User Tracking**: Track which testers are using the system and how frequently
- **Access Levels**: Different permission levels for different types of testers
- **Admin Interface**: Easy management of access codes through a web interface

### How It Works

1. Administrators generate access codes through the admin interface
2. These codes are distributed to testers via email or other communication channels
3. Testers enter their access code on the application's welcome page
4. The system validates the code and grants appropriate access permissions
5. Usage is tracked for analytics and security purposes

### User Experience

Testers will:
1. Visit the application's URL
2. Be redirected to the welcome page if they don't have valid access
3. Enter their unique access code
4. Gain access to the application based on their permission level
5. Maintain access until their code expires or reaches its usage limit

### Administration

Administrators can:
1. Create new access codes with customizable parameters
2. Monitor active codes and their usage
3. Disable codes when needed
4. View comprehensive usage statistics
5. Track detailed access logs for auditing

### Technical Implementation

- Backend: Python Flask API with JSON storage
- Frontend: React with protected routes
- Security: JWT tokens and role-based permissions
- Tracking: Detailed logging of all access events

### API Endpoints

#### Public Endpoints

- `POST /api/access/validate` - Validate an access code and get permissions

#### Admin Endpoints (Require Admin Password)

- `POST /api/admin/access/create` - Create a new access code
- `GET /api/admin/access/list` - List all access codes
- `POST /api/admin/access/disable/:code` - Disable an access code
- `POST /api/admin/access/update/:code` - Update an access code
- `GET /api/admin/access/logs` - Get access logs
- `GET /api/admin/access/stats` - Get usage statistics

### Environment Variables

- `ADMIN_PASSWORD` - The password used to authenticate admin requests
- `FLASK_ENV` - Set to 'development' to bypass authentication in development
- `DEBUG` - Set to 'True' to enable debug features