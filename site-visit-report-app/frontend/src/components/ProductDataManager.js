import React, { useState, useEffect } from 'react';
import config from '../config';

const ProductDataManager = () => {
  const [productFiles, setProductFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState({ text: '', type: '' });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    fetchProductData();
  }, []);

  const fetchProductData = async () => {
    try {
      const response = await fetch(`${config.apiBaseUrl}/list-product-data`);
      
      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      
      const data = await response.json();
      setProductFiles(data.files);
    } catch (error) {
      console.error('Error fetching product data:', error);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    
    if (!selectedFile) {
      alert('Please select a file first');
      return;
    }
    
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
      const response = await fetch(`${config.apiBaseUrl}/upload-product-data`, {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        setMessage({ text: 'Failed to upload file', type: 'error' });
        throw new Error(`Error: ${response.status}`);
      } else {
        await response.json();
        setMessage({ text: 'File uploaded successfully', type: 'success' });
        setSelectedFile(null);
        fetchProductData(); // Refresh the list
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      setMessage({ text: 'Error uploading file: ' + error.message, type: 'error' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileDelete = async (filename) => {
    if (window.confirm(`Are you sure you want to delete ${filename}?`)) {
      try {
        const response = await fetch(`${config.apiBaseUrl}/delete-product-data/${filename}`, {
          method: 'DELETE'
        });
        
        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }
        
        fetchProductData(); // Refresh the list
      } catch (error) {
        console.error('Error deleting file:', error);
      }
    }
  };

  const searchProductData = async () => {
    if (!searchQuery.trim()) {
      setMessage({ text: 'Please enter a search query', type: 'error' });
      return;
    }

    setIsSearching(true);
    setSearchResults([]);
    setMessage({ text: '', type: '' });

    try {
      const response = await fetch(`${config.apiBaseUrl}/query-product-data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: searchQuery, k: 5 }),
      });

      const data = await response.json();
      
      if (response.ok) {
        setSearchResults(data.results || []);
        if (data.results.length === 0) {
          setMessage({ text: 'No matching results found', type: 'info' });
        }
      } else {
        setMessage({ text: data.error || 'Failed to search', type: 'error' });
      }
    } catch (error) {
      console.error('Error searching:', error);
      setMessage({ text: 'Failed to connect to server', type: 'error' });
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold mb-4 text-gray-800">Product Data Management</h1>
        <p className="text-gray-600 mb-6">
          Upload product data sheets to enhance the AI's understanding of building materials and components.
          When hashtags in photos match these product names, the AI will include relevant information in its analysis.
        </p>
      </div>

      {message.text && (
        <div className={`p-3 rounded ${
          message.type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' :
          message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' :
          'bg-blue-50 text-blue-700 border border-blue-200'
        }`}>
          {message.text}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-800">Upload Product Data</h2>
          
          <div className="border border-gray-200 rounded-lg p-4 bg-white">
            <div className="space-y-4">
              <label className="block font-medium text-gray-700">
                Select File (PDF or TXT)
                <input
                  type="file"
                  onChange={handleFileSelect}
                  accept=".pdf,.txt"
                  className="mt-2 block w-full text-sm text-gray-600 
                            file:mr-4 file:py-2 file:px-4
                            file:rounded file:border-0
                            file:text-sm file:font-semibold
                            file:bg-orange-500 file:text-white
                            hover:file:bg-orange-600 cursor-pointer"
                  disabled={isUploading}
                />
              </label>
              
              <button
                onClick={handleFileUpload}
                disabled={isUploading || !selectedFile}
                className="bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? 'Uploading...' : 'Upload File'}
              </button>
              
              {isUploading && (
                <div className="flex items-center text-gray-600">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-orange-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Uploading...
                </div>
              )}
            </div>
          </div>

          <h2 className="text-xl font-semibold mt-6 text-gray-800">Uploaded Product Data</h2>
          <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
            {productFiles.length > 0 ? (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Filename</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {productFiles.map((file, index) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-700">{file}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm">
                        <button
                          onClick={() => handleFileDelete(file)}
                          className="text-red-600 hover:text-red-800"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-4 text-center text-gray-500">
                No product data sheets uploaded yet.
              </div>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-800">Search Product Data</h2>
          
          <div className="border border-gray-200 rounded-lg p-4 bg-white">
            <div className="space-y-4">
              <label className="block font-medium text-gray-700">
                Search Query
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="e.g., window sealant, flashing membrane"
                  className="mt-2 block w-full rounded-md border-gray-300 bg-white text-gray-700 px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500/50 transition-colors"
                />
              </label>
              
              <button
                onClick={searchProductData}
                disabled={isSearching || !searchQuery.trim()}
                className="bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSearching ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>

          <h2 className="text-xl font-semibold mt-6 text-gray-800">Search Results</h2>
          <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
            {searchResults.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {searchResults.map((result, index) => (
                  <div key={index} className="p-4">
                    <div className="flex justify-between mb-2">
                      <div className="font-medium text-orange-700">
                        Source: {result.source ? result.source.split('/').pop() : 'Unknown'}
                        {result.page !== undefined && ` (Page ${result.page})`}
                      </div>
                      <div className="text-gray-500 text-sm">
                        Score: {Math.round((1 - result.relevance_score) * 100)}%
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{result.content}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 text-center text-gray-500">
                {isSearching ? 'Searching...' : searchQuery ? 'No results found. Try a different query.' : 'Enter a search term to find relevant product information.'}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDataManager; 