import config from '../config';
import apiClient from './apiClient';

/**
 * Authentication API service
 */
const authApi = {
  /**
   * Login a user
   * @param {string} username - The username
   * @param {string} password - The password
   * @returns {Promise} - The authentication response
   */
  login: async (username, password) => {
    try {
      // Don't use apiClient for login since we don't have a token yet
      const response = await fetch(`${config.apiBaseUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Login failed');
      }

      // Store the token in localStorage
      localStorage.setItem('auth_token', data.token);
      localStorage.setItem('username', data.username);

      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  /**
   * Get the current user's information
   * @returns {Promise} - The user information
   */
  getCurrentUser: async () => {
    try {
      return await apiClient.get('/auth/me');
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  },

  /**
   * List all users (admin only)
   * @returns {Promise} - The list of users
   */
  listUsers: async () => {
    try {
      return await apiClient.get('/auth/users');
    } catch (error) {
      console.error('List users error:', error);
      throw error;
    }
  },

  /**
   * Create a new user (admin only)
   * @param {string} username - The username
   * @param {string} password - The password
   * @param {boolean} isAdmin - Whether the user is an admin
   * @returns {Promise} - The creation response
   */
  createUser: async (username, password, isAdmin = false) => {
    try {
      return await apiClient.post('/auth/users', { 
        username, 
        password, 
        is_admin: isAdmin 
      });
    } catch (error) {
      console.error('Create user error:', error);
      throw error;
    }
  },

  /**
   * Delete a user (admin only)
   * @param {string} username - The username to delete
   * @returns {Promise} - The deletion response
   */
  deleteUser: async (username) => {
    try {
      return await apiClient.delete(`/auth/users/${username}`);
    } catch (error) {
      console.error('Delete user error:', error);
      throw error;
    }
  },

  /**
   * Change a user's password
   * @param {string} username - The username
   * @param {string} newPassword - The new password
   * @returns {Promise} - The password change response
   */
  changePassword: async (username, newPassword) => {
    try {
      return await apiClient.post(`/auth/users/${username}/change-password`, {
        new_password: newPassword
      });
    } catch (error) {
      console.error('Change password error:', error);
      throw error;
    }
  },

  /**
   * Logout the current user
   */
  logout: () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('username');
    // Redirect to login page or refresh the app
    window.location.href = '/login';
  },

  /**
   * Check if the user is authenticated
   * @returns {boolean} - Whether the user is authenticated
   */
  isAuthenticated: () => {
    return !!localStorage.getItem('auth_token');
  },

  /**
   * Get the authentication token
   * @returns {string|null} - The authentication token
   */
  getToken: () => {
    return localStorage.getItem('auth_token');
  },
};

export default authApi; 