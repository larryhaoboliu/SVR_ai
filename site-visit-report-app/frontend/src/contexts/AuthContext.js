import React, { createContext, useState, useEffect, useContext } from 'react';
import authApi from '../api/auth';

// Create the authentication context
const AuthContext = createContext();

/**
 * Authentication provider component
 * @param {object} props - Component props
 * @returns {JSX.Element} - Authentication provider component
 */
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if the user is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        if (authApi.isAuthenticated()) {
          const userData = await authApi.getCurrentUser();
          setUser(userData);
        }
      } catch (err) {
        console.error('Authentication error:', err);
        // Clear invalid auth data
        authApi.logout();
        setError('Authentication failed. Please log in again.');
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  /**
   * Login a user
   * @param {string} username - The username
   * @param {string} password - The password
   * @returns {Promise} - The login result
   */
  const login = async (username, password) => {
    setLoading(true);
    setError(null);

    try {
      const result = await authApi.login(username, password);
      const userData = await authApi.getCurrentUser();
      setUser(userData);
      return result;
    } catch (err) {
      setError(err.message || 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Logout the current user
   */
  const logout = () => {
    authApi.logout();
    setUser(null);
  };

  /**
   * Create a new user (admin only)
   * @param {string} username - The username
   * @param {string} password - The password
   * @param {boolean} isAdmin - Whether the user is an admin
   * @returns {Promise} - The creation result
   */
  const createUser = async (username, password, isAdmin = false) => {
    setLoading(true);
    setError(null);

    try {
      return await authApi.createUser(username, password, isAdmin);
    } catch (err) {
      setError(err.message || 'Failed to create user');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Delete a user (admin only)
   * @param {string} username - The username to delete
   * @returns {Promise} - The deletion result
   */
  const deleteUser = async (username) => {
    setLoading(true);
    setError(null);

    try {
      return await authApi.deleteUser(username);
    } catch (err) {
      setError(err.message || 'Failed to delete user');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Change a user's password
   * @param {string} username - The username
   * @param {string} newPassword - The new password
   * @returns {Promise} - The password change result
   */
  const changePassword = async (username, newPassword) => {
    setLoading(true);
    setError(null);

    try {
      return await authApi.changePassword(username, newPassword);
    } catch (err) {
      setError(err.message || 'Failed to change password');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  /**
   * List all users (admin only)
   * @returns {Promise} - The list of users
   */
  const listUsers = async () => {
    setLoading(true);
    setError(null);

    try {
      return await authApi.listUsers();
    } catch (err) {
      setError(err.message || 'Failed to list users');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Authentication context value
  const value = {
    user,
    loading,
    error,
    isAuthenticated: !!user,
    isAdmin: user?.is_admin || false,
    login,
    logout,
    createUser,
    deleteUser,
    changePassword,
    listUsers,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Hook to use the authentication context
 * @returns {object} - The authentication context
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext; 