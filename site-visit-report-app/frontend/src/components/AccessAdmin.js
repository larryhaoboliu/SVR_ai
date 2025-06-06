import React, { useState, useEffect } from 'react';
import axios from 'axios';

const AccessAdmin = () => {
  const [accessCodes, setAccessCodes] = useState([]);
  const [stats, setStats] = useState({});
  const [accessLogs, setAccessLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [adminVerified, setAdminVerified] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(null);
  const [lastRefreshed, setLastRefreshed] = useState(null);
  
  // New code form
  const [newCodeForm, setNewCodeForm] = useState({
    assigned_to: '',
    email: '',
    expiry_days: 30,
    uses: 100,
    notes: '',
    access_level: 'standard'
  });
  
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5001';
  
  // Verify admin password
  const verifyAdminPassword = async () => {
    if (!adminPassword.trim()) {
      setError('Please enter admin password');
      return;
    }
    
    console.log("Attempting to verify admin password:", adminPassword);
    
    try {
      const response = await axios.get(`${backendUrl}/api/admin/access/list`, {
        headers: {
          'X-API-Key': adminPassword
        }
      });
      
      console.log("Verification response:", response.data);
      
      if (response.data.status === 'success') {
        console.log("Admin verified successfully");
        setAdminVerified(true);
        localStorage.setItem('admin_password', adminPassword);
        await loadData();
        startAutoRefresh();
      }
    } catch (error) {
      console.error('Admin password verification failed:', error);
      setError('Invalid admin password');
    }
  };
  
  // Start auto-refresh of data
  const startAutoRefresh = () => {
    // Set up an interval to refresh data every 30 seconds
    const interval = setInterval(() => {
      loadData();
    }, 30000); // 30 seconds
    
    setRefreshInterval(interval);
  };
  
  // Load access codes and stats
  const loadData = async () => {
    setLoading(true);
    setError('');
    
    try {
      console.log("Fetching data with admin password:", adminPassword);
      
      const codesResponse = await axios.get(`${backendUrl}/api/admin/access/list`, {
        headers: {
          'X-API-Key': adminPassword
        }
      });
      
      const statsResponse = await axios.get(`${backendUrl}/api/admin/access/stats`, {
        headers: {
          'X-API-Key': adminPassword
        }
      });
      
      const logsResponse = await axios.get(`${backendUrl}/api/admin/access/logs`, {
        headers: {
          'X-API-Key': adminPassword
        }
      });
      
      console.log("API Responses:", {
        codes: codesResponse.data,
        stats: statsResponse.data,
        logs: logsResponse.data
      });
      
      if (codesResponse.data.status === 'success') {
        setAccessCodes(codesResponse.data.access_codes || []);
        console.log("Access codes updated:", codesResponse.data.access_codes);
      }
      
      if (statsResponse.data.status === 'success') {
        setStats(statsResponse.data.stats || {});
        console.log("Stats updated:", statsResponse.data.stats);
      }
      
      if (logsResponse.data.status === 'success') {
        setAccessLogs(logsResponse.data.logs || []);
        console.log("Logs updated:", logsResponse.data.logs);
      }
      
      // Update the last refreshed timestamp
      setLastRefreshed(new Date());
    } catch (error) {
      console.error('Error loading data:', error);
      setError('Failed to load data');
      setAdminVerified(false);
    } finally {
      setLoading(false);
    }
  };
  
  // Manual refresh button handler
  const handleManualRefresh = () => {
    loadData();
  };
  
  // Create a new access code
  const createAccessCode = async (e) => {
    e.preventDefault();
    
    if (!newCodeForm.assigned_to || !newCodeForm.email) {
      setError('Name and email are required');
      return;
    }
    
    try {
      const response = await axios.post(
        `${backendUrl}/api/admin/access/create`,
        newCodeForm,
        {
          headers: {
            'X-API-Key': adminPassword
          }
        }
      );
      
      if (response.data.status === 'success') {
        alert(`New access code created: ${response.data.access_code}`);
        
        // Reset form
        setNewCodeForm({
          assigned_to: '',
          email: '',
          expiry_days: 30,
          uses: 100,
          notes: '',
          access_level: 'standard'
        });
        
        // Reload data
        loadData();
      }
    } catch (error) {
      console.error('Error creating access code:', error);
      setError('Failed to create access code');
    }
  };
  
  // Disable an access code
  const disableAccessCode = async (code) => {
    if (!window.confirm(`Disable access code ${code}?`)) {
      return;
    }
    
    try {
      const response = await axios.post(
        `${backendUrl}/api/admin/access/disable/${code}`,
        {},
        {
          headers: {
            'X-API-Key': adminPassword
          }
        }
      );
      
      if (response.data.status === 'success') {
        alert('Access code disabled successfully');
        loadData();
      }
    } catch (error) {
      console.error('Error disabling access code:', error);
      setError('Failed to disable access code');
    }
  };
  
  // Handle form input changes
  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setNewCodeForm(prev => ({
      ...prev,
      [name]: name === 'expiry_days' || name === 'uses' ? parseInt(value, 10) : value
    }));
  };
  
  // Check for stored admin password on component mount
  useEffect(() => {
    const storedPassword = localStorage.getItem('admin_password');
    if (storedPassword) {
      setAdminPassword(storedPassword);
      setAdminVerified(true);
    } else {
      // Set a default admin password for development/testing
      const defaultPassword = 'admin123';
      setAdminPassword(defaultPassword);
      
      // Auto-verify with default password
      const autoVerify = async () => {
        console.log("Auto-verifying with default admin password");
        try {
          const response = await axios.get(`${backendUrl}/api/admin/access/list`, {
            headers: {
              'X-API-Key': defaultPassword
            }
          });
          
          if (response.data.status === 'success') {
            console.log("Auto-verification successful");
            setAdminVerified(true);
            localStorage.setItem('admin_password', defaultPassword);
          }
        } catch (error) {
          console.error("Auto-verification failed:", error);
          // Just keep the login form displayed if auto-verification fails
        }
      };
      
      autoVerify();
    }
  }, [backendUrl]);
  
  // Load data and set up auto-refresh when admin is verified
  useEffect(() => {
    if (adminVerified) {
      loadData();
      startAutoRefresh();
    }
    
    // Cleanup function to clear the interval when component unmounts
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [adminVerified]);
  
  // Format the last refreshed time
  const formatLastRefreshed = () => {
    if (!lastRefreshed) return 'Never';
    
    return lastRefreshed.toLocaleTimeString();
  };
  
  // Format timestamp for display
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    
    const date = new Date(timestamp);
    return date.toLocaleString();
  };
  
  // If admin not verified, show password form
  if (!adminVerified) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">Access Code Admin</h1>
        
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Admin Authentication</h2>
          
          <div className="mb-4">
            <label className="block text-gray-700 mb-2">Admin Password</label>
            <input
              type="password"
              value={adminPassword}
              onChange={(e) => setAdminPassword(e.target.value)}
              className="w-full p-2 border rounded"
              placeholder="Enter admin password"
            />
          </div>
          
          {error && (
            <div className="mb-4 text-red-600 text-sm">
              {error}
            </div>
          )}
          
          <button
            onClick={verifyAdminPassword}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Verify Password
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Access Code Admin</h1>
        
        <div className="flex items-center">
          <span className="text-sm text-gray-500 mr-3">
            Last refreshed: {formatLastRefreshed()}
          </span>
          <button 
            onClick={handleManualRefresh} 
            className="flex items-center text-sm bg-gray-100 hover:bg-gray-200 py-1 px-3 rounded"
            disabled={loading}
          >
            {loading ? (
              <span>Refreshing...</span>
            ) : (
              <span>Refresh Data</span>
            )}
          </button>
        </div>
      </div>
      
      {/* Stats */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Stats</h2>
        
        {loading ? (
          <p>Loading...</p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded">
              <p className="text-sm text-gray-500">Total Codes</p>
              <p className="text-2xl font-bold">{stats.total_codes || 0}</p>
            </div>
            <div className="bg-green-50 p-4 rounded">
              <p className="text-sm text-gray-500">Active</p>
              <p className="text-2xl font-bold text-green-600">{stats.active_codes || 0}</p>
            </div>
            <div className="bg-red-50 p-4 rounded">
              <p className="text-sm text-gray-500">Expired/Disabled</p>
              <p className="text-2xl font-bold text-red-600">
                {(stats.expired_codes || 0) + (stats.disabled_codes || 0)}
              </p>
            </div>
            <div className="bg-blue-50 p-4 rounded">
              <p className="text-sm text-gray-500">Recent Logins (24h)</p>
              <p className="text-2xl font-bold text-blue-600">{stats.recent_logins || 0}</p>
            </div>
          </div>
        )}
      </div>
      
      {/* Recent Access Logs */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
        
        {loading ? (
          <p>Loading...</p>
        ) : accessLogs.length === 0 ? (
          <p>No recent activity found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Access Code
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {accessLogs.slice(0, 10).map((log) => (
                  <tr key={log.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatTimestamp(log.timestamp)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap font-mono text-sm">
                      {log.access_code}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {log.user}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        log.action === 'login' ? 'bg-green-100 text-green-800' : 
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {log.action}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      
      {/* Create Form */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Create New Access Code</h2>
        
        <form onSubmit={createAccessCode}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-gray-700 mb-2">Name</label>
              <input
                type="text"
                name="assigned_to"
                value={newCodeForm.assigned_to}
                onChange={handleFormChange}
                className="w-full p-2 border rounded"
                placeholder="Tester's name"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2">Email</label>
              <input
                type="email"
                name="email"
                value={newCodeForm.email}
                onChange={handleFormChange}
                className="w-full p-2 border rounded"
                placeholder="Tester's email"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2">Expires After (days)</label>
              <input
                type="number"
                name="expiry_days"
                value={newCodeForm.expiry_days}
                onChange={handleFormChange}
                className="w-full p-2 border rounded"
                min="1"
                max="365"
              />
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2">Number of Uses</label>
              <input
                type="number"
                name="uses"
                value={newCodeForm.uses}
                onChange={handleFormChange}
                className="w-full p-2 border rounded"
                min="1"
                max="1000"
              />
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2">Access Level</label>
              <select
                name="access_level"
                value={newCodeForm.access_level}
                onChange={handleFormChange}
                className="w-full p-2 border rounded"
              >
                <option value="standard">Standard</option>
                <option value="admin">Admin</option>
                <option value="read_only">Read Only</option>
              </select>
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2">Notes</label>
              <input
                type="text"
                name="notes"
                value={newCodeForm.notes}
                onChange={handleFormChange}
                className="w-full p-2 border rounded"
                placeholder="Optional notes"
              />
            </div>
          </div>
          
          {error && (
            <div className="mb-4 text-red-600 text-sm">
              {error}
            </div>
          )}
          
          <button
            type="submit"
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          >
            Create Access Code
          </button>
        </form>
      </div>
      
      {/* Codes List */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Access Codes</h2>
        
        {loading ? (
          <p>Loading...</p>
        ) : accessCodes.length === 0 ? (
          <p>No access codes found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Code
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Assigned To
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uses Remaining
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Used
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {accessCodes.map((code) => (
                  <tr key={code.code}>
                    <td className="px-6 py-4 whitespace-nowrap font-mono text-sm">
                      {code.code}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{code.assigned_to}</div>
                      <div className="text-sm text-gray-500">{code.email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        code.status === 'active' ? 'bg-green-100 text-green-800' :
                        code.status === 'expired' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {code.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {code.uses_remaining}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {code.last_used ? new Date(code.last_used).toLocaleString() : 'Never'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {code.status === 'active' && (
                        <button
                          onClick={() => disableAccessCode(code.code)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Disable
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AccessAdmin; 