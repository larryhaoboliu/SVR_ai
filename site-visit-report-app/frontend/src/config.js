/**
 * Configuration file for the frontend application
 * Manages environment-specific settings like API endpoints
 */

// Determine the current environment
const environment = process.env.NODE_ENV || 'development';

// Base configuration with environment-specific overrides
const config = {
  // Common configuration for all environments
  app: {
    name: 'Site Visit Report Application',
    version: '1.0.0',
  },
  
  // Environment-specific configuration
  development: {
    apiBaseUrl: 'http://localhost:5001',
    debug: true,
    logLevel: 'debug',
  },
  
  production: {
    // In production, you would use the deployed backend URL
    // apiBaseUrl: 'https://your-production-backend.herokuapp.com',
    apiBaseUrl: process.env.REACT_APP_API_URL || 'https://your-production-backend.herokuapp.com',
    debug: false,
    logLevel: 'error',
  },
  
  test: {
    apiBaseUrl: 'http://localhost:5001',
    debug: true,
    logLevel: 'debug',
  }
};

// Export the configuration for the current environment
const currentConfig = {
  ...config.app,
  ...config[environment],
  environment,
};

export default currentConfig; 