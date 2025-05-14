import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
  const location = useLocation();
  
  return (
    <nav className="bg-orange-300">
      <div className="container mx-auto px-4">
        <div className="flex flex-col">
          <div className="text-2xl font-bold py-3 px-2 text-black">Site Visit Report App</div>
          <div className="flex">
            <Link 
              to="/" 
              className={`px-6 py-2 text-base font-medium transition-colors border-t border-r border-l rounded-t-lg ${
                location.pathname === '/' 
                  ? 'bg-white text-orange-700 border-white' 
                  : 'bg-orange-500 text-white hover:bg-orange-400 border-orange-400'
              }`}
            >
              Report Writer
            </Link>
            <Link 
              to="/product-data" 
              className={`px-6 py-2 text-base font-medium transition-colors border-t border-r border-l rounded-t-lg ${
                location.pathname === '/product-data' 
                  ? 'bg-white text-orange-700 border-white' 
                  : 'bg-orange-500 text-white hover:bg-orange-400 border-orange-400'
              }`}
            >
              Product Data
            </Link>
            <div className="flex-grow border-b border-white"></div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 