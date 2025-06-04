const config = {
  development: {
    // In development, the backend runs on a different port
    apiBaseUrl: 'http://localhost:5001',
    debug: true,
    logLevel: 'debug',
  },
  
  production: {
    // In production, both frontend and backend are served from the same domain
    // API requests go to /api/* which nginx proxies to the Flask backend
    apiBaseUrl: '/api',
    debug: false,
    logLevel: 'error',
  },
  
  test: {
    apiBaseUrl: 'http://localhost:5001',
    debug: false,
    logLevel: 'warn',
  },
};

// Determine the current environment
const environment = process.env.NODE_ENV || 'development';

// Export the configuration for the current environment
export default config[environment]; 