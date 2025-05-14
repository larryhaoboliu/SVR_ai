import React, { useState } from 'react';
import FeedbackForm from './FeedbackForm';
import './Feedback.css';

const FeedbackButton = () => {
  const [isOpen, setIsOpen] = useState(false);
  
  const toggleFeedback = () => {
    setIsOpen(!isOpen);
  };
  
  const closeFeedback = () => {
    setIsOpen(false);
  };
  
  return (
    <div className="feedback-container">
      {isOpen && (
        <div className="feedback-modal">
          <div className="feedback-modal-content">
            <button 
              className="feedback-close-button" 
              onClick={closeFeedback}
            >
              ×
            </button>
            <FeedbackForm onClose={closeFeedback} />
          </div>
        </div>
      )}
      
      <button 
        className="feedback-button"
        onClick={toggleFeedback}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          backgroundColor: '#4CAF50',
          color: 'white',
          border: 'none',
          borderRadius: '50%',
          width: '60px',
          height: '60px',
          fontSize: '16px',
          cursor: 'pointer',
          boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}
      >
        Feedback
      </button>
    </div>
  );
};

export default FeedbackButton; 