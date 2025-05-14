import os
from functools import wraps
from flask import request, jsonify, current_app
import time
from datetime import datetime, timedelta
from flask_cors import CORS
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Rate limiting configuration
RATE_LIMIT = {
    'default': {'requests': 100, 'window': 60},  # 100 requests per 60 seconds by default
    '/analyze-image': {'requests': 20, 'window': 60},  # 20 requests per 60 seconds
    '/generate-report': {'requests': 10, 'window': 60},  # 10 requests per 60 seconds
}

# Dictionary to store request records for rate limiting
request_records = {}

def setup_security(app):
    """Configure all security settings for the application"""
    # Setup CORS
    allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000')
    origins = [origin.strip() for origin in allowed_origins.split(',')]
    
    CORS(app, resources={r"/*": {"origins": origins}})
    
    # Setup security headers
    @app.after_request
    def add_security_headers(response):
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline';"
        
        return response
    
    # Log all requests in development mode
    if os.getenv('FLASK_ENV') == 'development':
        @app.before_request
        def log_request_info():
            logger.debug(f"Request: {request.method} {request.path}")
            logger.debug(f"Headers: {request.headers}")
            if request.is_json:
                logger.debug(f"Body: {request.get_json()}")
    
    return app

def rate_limit(func):
    """Rate limiting decorator for API endpoints"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        client_ip = request.remote_addr
        endpoint = request.path
        
        # Determine which rate limit applies
        limit_key = endpoint if endpoint in RATE_LIMIT else 'default'
        limit_config = RATE_LIMIT[limit_key]
        
        # Create key for this IP and endpoint
        key = f"{client_ip}:{endpoint}"
        
        current_time = time.time()
        if key not in request_records:
            request_records[key] = []
        
        # Clean expired records
        window_start = current_time - limit_config['window']
        request_records[key] = [t for t in request_records[key] if t > window_start]
        
        # Check if rate limit exceeded
        if len(request_records[key]) >= limit_config['requests']:
            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
            reset_time = min(request_records[key]) + limit_config['window']
            reset_seconds = int(reset_time - current_time)
            
            response = jsonify({
                'error': 'Rate limit exceeded',
                'retry_after': reset_seconds
            })
            response.status_code = 429
            response.headers['Retry-After'] = str(reset_seconds)
            return response
        
        # Add current request to records
        request_records[key].append(current_time)
        
        # Execute the original function
        return func(*args, **kwargs)
    
    return wrapper

def require_api_key(func):
    """Decorator to require API key for certain endpoints"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        # Skip API key check in development for real application routes, but not for test routes
        if (os.getenv('FLASK_ENV') == 'development' and os.getenv('DEBUG') == 'True' 
            and not request.path.startswith('/test-')):
            return func(*args, **kwargs)
        
        # Check if API key is valid
        if not api_key or api_key != os.getenv('ADMIN_PASSWORD'):
            logger.warning(f"Invalid API key attempt from {request.remote_addr}")
            response = jsonify({'error': 'Invalid or missing API key'})
            response.status_code = 401
            return response
        
        return func(*args, **kwargs)
    
    return wrapper

def sanitize_input(func):
    """Decorator to sanitize user input"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # For form data
        sanitized_form = {}
        if request.form:
            for key, value in request.form.items():
                if isinstance(value, str):
                    # Sanitize by replacing dangerous characters
                    cleaned = value.replace('<', '&lt;').replace('>', '&gt;')
                    sanitized_form[key] = cleaned
                    if cleaned != value:
                        logger.warning(f"Potentially malicious input sanitized in form data for {key}")
        
        # For JSON data
        if request.is_json:
            try:
                json_data = request.get_json()
                if isinstance(json_data, dict):
                    sanitized_json = {}
                    for key, value in json_data.items():
                        if isinstance(value, str):
                            cleaned = value.replace('<', '&lt;').replace('>', '&gt;')
                            sanitized_json[key] = cleaned
                            if cleaned != value:
                                logger.warning(f"Potentially malicious input sanitized in JSON for {key}")
                        else:
                            sanitized_json[key] = value
                    
                    # Replace the request's JSON data with the sanitized version
                    # We can't modify request.json directly, so we'll use a monkey patch
                    # Store the original get_json method
                    original_get_json = request.get_json
                    
                    # Define a new get_json method that returns our sanitized data
                    def sanitized_get_json(*args, **kwargs):
                        return sanitized_json
                    
                    # Replace the method temporarily
                    request.get_json = sanitized_get_json
                    
                    # Call the original function
                    result = func(*args, **kwargs)
                    
                    # Restore the original method
                    request.get_json = original_get_json
                    
                    return result
            except Exception as e:
                logger.error(f"Error processing JSON: {str(e)}")
        
        # If we didn't return from the JSON branch, just call the original function
        return func(*args, **kwargs)
    
    return wrapper 