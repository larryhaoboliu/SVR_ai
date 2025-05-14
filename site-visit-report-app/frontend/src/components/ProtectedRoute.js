import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

/**
 * Protected route component
 * Redirects to login if not authenticated
 * 
 * @param {object} props - Component props
 * @param {boolean} props.requireAdmin - Whether the route requires admin privileges
 * @param {React.ReactNode} props.children - Child components
 * @returns {JSX.Element} - Protected route component
 */
const ProtectedRoute = ({ requireAdmin = false, children }) => {
  const { isAuthenticated, isAdmin, loading } = useAuth();
  const location = useLocation();

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // If not authenticated, redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If admin required but user is not admin, redirect to home
  if (requireAdmin && !isAdmin) {
    return <Navigate to="/" replace />;
  }

  // If authenticated and meets admin requirements, render children
  return children;
};

export default ProtectedRoute; 