import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const Welcome = () => {
  const [accessCode, setAccessCode] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [storedAccess, setStoredAccess] = useState(null);
  const navigate = useNavigate();

  // Check if user already has access
  useEffect(() => {
    const storedAccessData = localStorage.getItem('svr_access');
    if (storedAccessData) {
      try {
        const accessData = JSON.parse(storedAccessData);
        // Check if access data is still valid (not expired)
        const expiresAt = new Date(accessData.expires_at);
        const now = new Date();
        
        if (expiresAt > now && accessData.uses_remaining > 0) {
          setStoredAccess(accessData);
        } else {
          // Clear invalid access data
          localStorage.removeItem('svr_access');
        }
      } catch (error) {
        // Invalid stored data, clear it
        localStorage.removeItem('svr_access');
      }
    }
  }, []);

  const handleAccessSubmit = async (e) => {
    e.preventDefault();
    
    if (!accessCode.trim()) {
      setErrorMessage('Please enter an access code');
      return;
    }
    
    setLoading(true);
    setErrorMessage('');
    
    try {
      // Get backend URL from environment or use default
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5001';
      
      // Validate access code
      const response = await axios.post(`${backendUrl}/api/access/validate`, {
        access_code: accessCode
      });
      
      if (response.data.status === 'success') {
        // Store access data in local storage
        const accessData = {
          user_name: response.data.user_name,
          access_level: response.data.access_level,
          permissions: response.data.permissions,
          expires_at: response.data.expires_at,
          uses_remaining: response.data.uses_remaining,
          timestamp: new Date().toISOString()
        };
        
        localStorage.setItem('svr_access', JSON.stringify(accessData));
        
        // Redirect to main app
        navigate('/');
      }
    } catch (error) {
      console.error('Error validating access code:', error);
      let message = 'Failed to validate access code';
      
      if (error.response && error.response.data && error.response.data.message) {
        message = error.response.data.message;
      }
      
      setErrorMessage(message);
    } finally {
      setLoading(false);
    }
  };

  const continueAccess = () => {
    navigate('/');
  };

  const startFresh = () => {
    localStorage.removeItem('svr_access');
    setStoredAccess(null);
  };

  // If user already has valid access, show continue screen
  if (storedAccess) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[80vh] py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg shadow-md">
          <div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              Welcome Back, {storedAccess.user_name}!
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              You have an active testing session
            </p>
          </div>
          
          <div className="mt-6">
            <div className="rounded-md shadow-sm bg-gray-50 p-4 text-sm">
              <p><span className="font-medium">Access Level:</span> {storedAccess.access_level}</p>
              <p><span className="font-medium">Uses Remaining:</span> {storedAccess.uses_remaining}</p>
              <p><span className="font-medium">Expires:</span> {new Date(storedAccess.expires_at).toLocaleString()}</p>
            </div>
          </div>
          
          <div className="flex flex-col space-y-4 mt-6">
            <button
              onClick={continueAccess}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Continue to Application
            </button>
            
            <button
              onClick={startFresh}
              className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Use Different Access Code
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg shadow-md">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Welcome to the Building Envelope Report System
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Please enter your access code to begin
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleAccessSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="access-code" className="sr-only">Access Code</label>
              <input
                id="access-code"
                name="access-code"
                type="text"
                required
                className="appearance-none rounded relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Enter your access code"
                value={accessCode}
                onChange={(e) => setAccessCode(e.target.value.toUpperCase())}
              />
            </div>
          </div>

          {errorMessage && (
            <div className="text-red-600 text-sm mt-2">
              {errorMessage}
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
            >
              {loading ? 'Verifying...' : 'Access Application'}
            </button>
          </div>
        </form>
        
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Need an access code? Contact your administrator or project manager.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Welcome; 