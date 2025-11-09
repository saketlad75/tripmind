import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { createTripFromPrompt, saveTripToLocalStorage, extractLocation } from '../utils/tripUtils';
import './SearchBar.css';

const SearchBar = () => {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const textareaRef = useRef(null);
  const wrapperRef = useRef(null);

  // API endpoint - update this with your backend URL
  const API_ENDPOINT = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/trip-planner';

  // Generate a unique tripId with clean URL format
  const generateTripId = (promptText) => {
    // Extract location for better URL
    const location = extractLocation(promptText);
    const locationSlug = location.toLowerCase()
      .replace(/\s+/g, '-')
      .replace(/[^a-z0-9-]/g, '')
      .substring(0, 15);
    
    // Generate short unique ID (8 characters: last 6 digits of timestamp + 2 random chars)
    const timestamp = Date.now();
    const lastDigits = timestamp.toString().slice(-6);
    const randomChars = Math.random().toString(36).substring(2, 4);
    const shortId = `${lastDigits}${randomChars}`;
    
    return `${locationSlug || 'trip'}-${shortId}`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (prompt.trim() && !isGenerating) {
      setIsGenerating(true);
      setError(null);
      setSuccess(false);
      
      const tripId = generateTripId(prompt.trim());
      const promptData = {
        prompt: prompt.trim(),
        userId: 'Kartik7',
        tripId: tripId,
        timestamp: new Date().toISOString()
      };
      
      // Create trip object from the prompt (always create, even if API fails)
      const newTrip = createTripFromPrompt(prompt.trim(), tripId, 'Kartik7');
      
      // Create AbortController for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      // Try to send to API (optional - app works without it)
      try {
        console.log('Attempting to send POST request to:', API_ENDPOINT);
        console.log('Request data:', promptData);
        
        const response = await fetch(API_ENDPOINT, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(promptData),
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);

        console.log('Response status:', response.status);

        if (response.ok) {
          // Try to parse JSON, but handle non-JSON responses
          let data;
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            data = await response.json();
          } else {
            const text = await response.text();
            data = { message: text || 'Request sent successfully', tripId: tripId };
          }
          console.log('API Response:', data);
        } else {
          console.warn('API returned non-OK status:', response.status);
          // Don't throw error, just log it - we'll save locally anyway
        }
      } catch (error) {
        clearTimeout(timeoutId);
        
        // Only log the error, don't block the user
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
          console.warn('Could not connect to backend API. Saving trip locally only.');
        } else if (error.name === 'AbortError') {
          console.warn('API request timed out. Saving trip locally only.');
        } else {
          console.warn('API error (non-critical):', error.message);
        }
        // Continue anyway - we'll save locally
      }
      
      // Always save trip to localStorage (works offline)
      saveTripToLocalStorage(newTrip);
      console.log('Trip saved locally:', newTrip);
      
      // Show success message
      setSuccess(true);
      
      // Reset form after successful submission
      setPrompt('');
      
      // Navigate directly to the trip chat page immediately
      navigate(`/trips/${tripId}/chat`);
      
      setIsGenerating(false);
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
            placeholder={t('searchPlaceholder')}
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
      </form>
    </div>
  );
};

export default SearchBar;