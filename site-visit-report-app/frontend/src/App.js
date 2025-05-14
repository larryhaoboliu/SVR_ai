import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import ReportForm from './components/ReportForm';
import Navbar from './components/Navbar';
import ProductDataManager from './components/ProductDataManager';
import FeedbackButton from './components/FeedbackButton';
import Welcome from './components/Welcome';
import AccessAdmin from './components/AccessAdmin';
import './components/Feedback.css';

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const [hasAccess, setHasAccess] = useState(false);
  const [loading, setLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    // Check if user has access
    const storedAccessData = localStorage.getItem('svr_access');
    
    if (storedAccessData) {
      try {
        const accessData = JSON.parse(storedAccessData);
        // Check if access data is still valid (not expired)
        const expiresAt = new Date(accessData.expires_at);
        const now = new Date();
        
        if (expiresAt > now && accessData.uses_remaining > 0) {
          setHasAccess(true);
        }
      } catch (error) {
        // Invalid stored data
        console.error('Invalid access data:', error);
      }
    }
    
    setLoading(false);
  }, [location]);

  if (loading) {
    // You could show a loading spinner here
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  return hasAccess ? children : <Navigate to="/welcome" />;
};

// Admin route protection
const AdminRoute = ({ children }) => {
  const [hasAdminAccess, setHasAdminAccess] = useState(false);
  const [loading, setLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    // Check if user has admin access
    const storedAccessData = localStorage.getItem('svr_access');
    
    if (storedAccessData) {
      try {
        const accessData = JSON.parse(storedAccessData);
        // Check if admin level access
        if (accessData.access_level === 'admin') {
          setHasAdminAccess(true);
        }
      } catch (error) {
        console.error('Invalid access data:', error);
      }
    }
    
    setLoading(false);
  }, [location]);

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  return hasAdminAccess ? children : <Navigate to="/" />;
};

function App() {
  const [images, setImages] = useState([]); // State for uploaded photos

  return (
    <Router>
      <div className="min-h-screen bg-gray-50 text-gray-800 flex flex-col">
        <Navbar />
        <main className="flex-1 container mx-auto px-4 py-8">
          <Routes>
            {/* Public route */}
            <Route path="/welcome" element={<Welcome />} />
            
            {/* Protected routes */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <ReportForm images={images} setImages={setImages} />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/product-data" 
              element={
                <ProtectedRoute>
                  <ProductDataManager />
                </ProtectedRoute>
              } 
            />
            
            {/* Admin route */}
            <Route 
              path="/admin/access" 
              element={
                <AccessAdmin />
              } 
            />
            
            {/* Redirect any other route to welcome */}
            <Route path="*" element={<Navigate to="/welcome" />} />
          </Routes>
        </main>
        <footer className="py-4 border-t border-gray-200 text-center text-sm text-gray-500">
          © {new Date().getFullYear()} Building Envelope Reporting System
        </footer>
        <FeedbackButton />
      </div>
    </Router>
  );
}

export default App;

