import React, { useState, useRef, useEffect } from 'react';
import './SearchBar.css';

const SearchBar = () => {
  const [prompt, setPrompt] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const textareaRef = useRef(null);
  const wrapperRef = useRef(null);

  // API endpoint - update this with your backend URL
  const API_ENDPOINT = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/trip-planner';

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (prompt.trim() && !isGenerating) {
      setIsGenerating(true);
      setError(null);
      setSuccess(false);
      
      const promptData = {
        prompt: prompt.trim(),
        timestamp: new Date().toISOString()
      };
      
      try {
        const response = await fetch(API_ENDPOINT, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(promptData)
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Handle successful response
        console.log('API Response:', data);
        setSuccess(true);
        
        // Reset form after successful submission
        setPrompt('');
        
        // Reset success message after 3 seconds
        setTimeout(() => {
          setSuccess(false);
        }, 3000);
        
      } catch (error) {
        console.error('Error sending prompt to backend:', error);
        setError(error.message || 'Failed to send request. Please try again.');
        
        // Clear error message after 5 seconds
        setTimeout(() => {
          setError(null);
        }, 5000);
      } finally {
        setIsGenerating(false);
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current;
    const wrapper = wrapperRef.current;
    
    if (textarea) {
      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto';
      
      // Get min/max heights based on screen size
      const isMobile = window.innerWidth <= 768;
      const minHeight = isMobile ? 70 : 70; // Minimum height in pixels
      const maxHeight = isMobile ? 200 : 250; // Maximum height in pixels
      
      // Calculate new height based on content
      const scrollHeight = textarea.scrollHeight;
      
      // If prompt is empty, force minimum height
      const newHeight = prompt.trim() === '' 
        ? minHeight 
        : Math.min(Math.max(scrollHeight, minHeight), maxHeight);
      
      textarea.style.height = `${newHeight}px`;
      
      // Adjust wrapper min-height to accommodate textarea + actions + padding
      if (wrapper) {
        const actionsHeight = isMobile ? 36 : 40; // Button height
        const padding = isMobile ? 20 : 24; // Top + bottom padding
        const margin = isMobile ? 10 : 10; // Margin bottom of textarea
        
        // Base min-height for empty state
        const baseMinHeight = isMobile ? 110 : 120;
        
        // If prompt is empty, use base min-height, otherwise calculate
        const calculatedMinHeight = prompt.trim() === ''
          ? baseMinHeight
          : newHeight + actionsHeight + padding + margin;
        
        wrapper.style.minHeight = `${Math.max(calculatedMinHeight, baseMinHeight)}px`;
      }
    }
  }, [prompt, isFocused]);

  // Initial resize on mount
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const scrollHeight = textarea.scrollHeight;
      const isMobile = window.innerWidth <= 768;
      const minHeight = isMobile ? 70 : 70;
      textarea.style.height = `${Math.max(scrollHeight, minHeight)}px`;
    }
  }, []);

  return (
    <div id="search-bar" className="search-container">
      <div className="search-header">
        <h2 className="ai-planner-title">Your Smart Trip Planner ✈️</h2>
        <p className="ai-planner-subtitle">
          Travel smarter with AI that plans it all — flights, hotels, health, and weather, personalized just for you. One platform, every detail, zero hassle.
        </p>
      </div>
      
      <form className="search-form" onSubmit={handleSubmit}>
        <div 
          ref={wrapperRef}
          className={`search-wrapper ${isFocused ? 'focused' : ''} ${isGenerating ? 'generating' : ''}`}
          onClick={(e) => {
            // If clicking on the wrapper (not on textarea or button), focus the textarea
            if (e.target === e.currentTarget || e.target.classList.contains('search-wrapper')) {
              textareaRef.current?.focus();
            }
          }}
        >
          <textarea
            ref={textareaRef}
            className="search-input"
            placeholder="Describe your travel plans in detail... For example: I'm planning a 10-day trip to Japan in March 2024. I have diabetes and need to ensure medical facilities are accessible. I prefer budget-friendly hotels near public transportation. Please include weather-based backup plans for outdoor activities, recommendations for what to pack, and shopping suggestions for items to buy before and after the trip. Also, I'd like information about cultural etiquette and any health requirements or vaccinations needed."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onKeyDown={handleKeyDown}
            disabled={isGenerating}
            style={{ width: '100%', overflowY: 'auto' }}
          />
          <div className="search-actions">
            <div className="char-count">
              {prompt.length > 0 && (
                <span className={prompt.length > 2000 ? 'char-count-warning' : ''}>
                  {prompt.length} characters
                </span>
              )}
            </div>
            <button 
              type="submit" 
              className="search-button"
              disabled={!prompt.trim() || isGenerating}
              title="Generate itinerary (Enter)"
            >
              {isGenerating ? (
                <div className="spinner"></div>
              ) : (
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              )}
            </button>
          </div>
        </div>
        {error && (
          <div className="search-message search-error">
            <p>❌ <strong>Error:</strong> {error}</p>
          </div>
        )}
        {success && (
          <div className="search-message search-success">
            <p>✅ <strong>Success:</strong> Your travel plan request has been sent successfully!</p>
          </div>
        )}
        <div className="search-hint">
          <p>💡 <strong>Tip:</strong> The more details you provide, the better your personalized itinerary will be. Include dates, preferences, medical needs, budget, and any special requirements.</p>
        </div>
      </form>
    </div>
  );
};

export default SearchBar;