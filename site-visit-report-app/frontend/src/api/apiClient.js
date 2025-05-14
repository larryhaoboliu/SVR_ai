import config from '../config';

/**
 * API client with authentication interceptor
 */
const apiClient = {
  /**
   * Make a GET request
   * @param {string} endpoint - API endpoint
   * @param {object} options - Additional fetch options
   * @returns {Promise} - The API response
   */
  get: async (endpoint, options = {}) => {
    return apiClient.request('GET', endpoint, null, options);
  },

  /**
   * Make a POST request
   * @param {string} endpoint - API endpoint
   * @param {object} data - Request body data
   * @param {object} options - Additional fetch options
   * @returns {Promise} - The API response
   */
  post: async (endpoint, data, options = {}) => {
    return apiClient.request('POST', endpoint, data, options);
  },

  /**
   * Make a PUT request
   * @param {string} endpoint - API endpoint
   * @param {object} data - Request body data
   * @param {object} options - Additional fetch options
   * @returns {Promise} - The API response
   */
  put: async (endpoint, data, options = {}) => {
    return apiClient.request('PUT', endpoint, data, options);
  },

  /**
   * Make a DELETE request
   * @param {string} endpoint - API endpoint
   * @param {object} options - Additional fetch options
   * @returns {Promise} - The API response
   */
  delete: async (endpoint, options = {}) => {
    return apiClient.request('DELETE', endpoint, null, options);
  },

  /**
   * Make an API request
   * @param {string} method - HTTP method
   * @param {string} endpoint - API endpoint
   * @param {object} data - Request body data
   * @param {object} options - Additional fetch options
   * @returns {Promise} - The API response
   */
  request: async (method, endpoint, data = null, options = {}) => {
    const url = `${config.apiBaseUrl}${endpoint}`;
    
    // Prepare headers with authentication
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    // Add authentication token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Prepare request options
    const requestOptions = {
      method,
      headers,
      ...options,
    };
    
    // Add body for non-GET requests with data
    if (data && method !== 'GET') {
      requestOptions.body = JSON.stringify(data);
    }
    
    try {
      const response = await fetch(url, requestOptions);
      
      // Parse JSON response if available
      let responseData;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        responseData = await response.json();
      } else {
        responseData = await response.text();
      }
      
      // Handle error responses
      if (!response.ok) {
        throw new Error(
          responseData.error || responseData.message || `API error: ${response.status}`
        );
      }
      
      return responseData;
    } catch (error) {
      console.error(`API request failed: ${error.message}`);
      throw error;
    }
  },
};

export default apiClient; 