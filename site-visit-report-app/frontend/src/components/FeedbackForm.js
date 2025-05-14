import React, { useState } from 'react';
import axios from 'axios';

const FeedbackForm = ({ onClose }) => {
  const [feedback, setFeedback] = useState({
    rating: 5,
    usability: '',
    features: '',
    issues: '',
    suggestions: '',
    email: ''
  });
  const [status, setStatus] = useState({ loading: false, success: false, error: null });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFeedback(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus({ loading: true, success: false, error: null });
    
    try {
      // Get backend URL from environment or use default
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5001';
      
      // Backend endpoint for feedback
      await axios.post(`${backendUrl}/api/feedback`, feedback);
      setStatus({ loading: false, success: true, error: null });
      // Reset form after successful submission
      setTimeout(() => {
        if (onClose) onClose();
      }, 3000);
    } catch (err) {
      setStatus({ 
        loading: false, 
        success: false, 
        error: err.response?.data?.message || 'Failed to submit feedback' 
      });
    }
  };

  if (status.success) {
    return (
      <div className="feedback-form success">
        <h3>Thank you for your feedback!</h3>
        <p>Your input is valuable and will help us improve the application.</p>
      </div>
    );
  }

  return (
    <div className="feedback-form">
      <h3>Share Your Feedback</h3>
      <p>Help us improve the Site Visit Report Application by sharing your experience.</p>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Overall Rating</label>
          <select 
            name="rating" 
            value={feedback.rating} 
            onChange={handleChange}
            required
          >
            <option value="5">Excellent (5)</option>
            <option value="4">Good (4)</option>
            <option value="3">Average (3)</option>
            <option value="2">Below Average (2)</option>
            <option value="1">Poor (1)</option>
          </select>
        </div>
        
        <div className="form-group">
          <label>How was the usability?</label>
          <textarea 
            name="usability"
            value={feedback.usability}
            onChange={handleChange}
            placeholder="Was the application easy to use? Any challenges?"
            rows="3"
          />
        </div>
        
        <div className="form-group">
          <label>Features Feedback</label>
          <textarea 
            name="features"
            value={feedback.features}
            onChange={handleChange}
            placeholder="What features did you like? What needs improvement?"
            rows="3"
          />
        </div>
        
        <div className="form-group">
          <label>Issues Encountered</label>
          <textarea 
            name="issues"
            value={feedback.issues}
            onChange={handleChange}
            placeholder="Please describe any bugs or issues you found"
            rows="3"
          />
        </div>
        
        <div className="form-group">
          <label>Suggestions</label>
          <textarea 
            name="suggestions"
            value={feedback.suggestions}
            onChange={handleChange}
            placeholder="What would make this application better?"
            rows="3"
          />
        </div>
        
        <div className="form-group">
          <label>Email (Optional)</label>
          <input 
            type="email"
            name="email"
            value={feedback.email}
            onChange={handleChange}
            placeholder="Your email if you'd like us to contact you"
          />
        </div>
        
        <div className="form-actions">
          {onClose && (
            <button type="button" className="cancel-button" onClick={onClose}>
              Cancel
            </button>
          )}
          <button 
            type="submit" 
            className="submit-button"
            disabled={status.loading}
          >
            {status.loading ? 'Submitting...' : 'Submit Feedback'}
          </button>
        </div>
        
        {status.error && (
          <div className="error-message">
            {status.error}
          </div>
        )}
      </form>
    </div>
  );
};

export default FeedbackForm; 