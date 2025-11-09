import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTripsFromLocalStorage } from '../utils/tripUtils';
import './TripChat.css';

const TripChat = () => {
  const { tripId } = useParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [tripInfo, setTripInfo] = useState(null);
  const [sharedUsers, setSharedUsers] = useState([]);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const API_ENDPOINT = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/trips';
  const CHAT_API_ENDPOINT = process.env.REACT_APP_CHAT_API_URL || 'http://localhost:8000/api/trip-planner';
  const [isLoading, setIsLoading] = useState(false);
  const [currentTripId, setCurrentTripId] = useState(tripId);

  // Fetch trip info and generate initial plan
  useEffect(() => {
    let isMounted = true;
    
    const fetchTripDataAndGeneratePlan = async () => {
      try {
        // First, try to get trip from localStorage
        const localTrips = getTripsFromLocalStorage();
        const localTrip = localTrips.find(trip => trip.id === tripId);
        
        if (localTrip && isMounted) {
          setTripInfo({
            id: localTrip.id,
            title: localTrip.title,
            destination: localTrip.destination,
            image: localTrip.image,
            prompt: localTrip.prompt
          });
        }
        
        // Try to fetch from backend API for trip info
        try {
          const tripResponse = await fetch(`${API_ENDPOINT}/trips/${tripId}?userId=Kartik7`);
          if (tripResponse.ok && isMounted) {
            const tripData = await tripResponse.json();
            setTripInfo(prev => prev || tripData);
          }
        } catch (err) {
          console.log('Could not fetch trip info from backend, using local data');
        }

        // Fetch existing messages FIRST (before checking for stored prompts)
        let hasExistingMessages = false;
        try {
          const messagesResponse = await fetch(`${CHAT_API_ENDPOINT}/trips/${tripId}/messages?userId=Kartik7`);
          if (messagesResponse.ok) {
            const messagesData = await messagesResponse.json();
            if (messagesData.messages && messagesData.messages.length > 0 && isMounted) {
              setMessages(messagesData.messages);
              hasExistingMessages = true;
              console.log(`✅ Loaded ${messagesData.messages.length} messages from database`);
              // If we loaded messages, don't auto-send stored prompt
              return; // Exit early - messages loaded successfully
            }
          } else {
            console.log('⚠️ Could not fetch messages from backend:', messagesResponse.status);
            // Try to get error details
            try {
              const errorData = await messagesResponse.json();
              console.log('Error details:', errorData);
            } catch (e) {
              // Ignore JSON parse errors
            }
          }
        } catch (err) {
          console.log('❌ Error fetching messages from backend:', err);
          // Try to load from localStorage as backup
          try {
            const key = `trip_chat_${tripId}`;
            const localMessages = JSON.parse(localStorage.getItem(key) || '[]');
            if (localMessages.length > 0 && isMounted) {
              setMessages(localMessages);
              hasExistingMessages = true;
              console.log(`📦 Loaded ${localMessages.length} messages from localStorage`);
              return; // Exit early - messages loaded from localStorage
            }
          } catch (localErr) {
            console.log('❌ Could not load messages from localStorage:', localErr);
          }
        }
        
        // Only check for stored prompt if no messages were found
        // Check if there's a prompt stored for this trip (from SearchBar)
        const promptKey = `trip_prompt_${tripId}`;
        const storedPrompt = localStorage.getItem(promptKey);
        
        // If we have a prompt and no messages, automatically send it
        if (storedPrompt && !hasExistingMessages && isMounted) {
          // Remove the stored prompt
          localStorage.removeItem(promptKey);
          
          // Automatically send the prompt
          const autoSendPrompt = async () => {
            const userPrompt = storedPrompt;
            const userMessage = {
              id: Date.now(),
              role: 'user',
              content: userPrompt,
              timestamp: new Date().toISOString()
            };

            // Add user message immediately
            setMessages([userMessage]);
            setIsLoading(true);

            try {
              const response = await fetch(`${API_ENDPOINT}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  prompt: userPrompt,
                  user_id: 'Kartik7',
                  trip_id: tripId || undefined,
                }),
              });

              if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(errorData.detail || `Server error: ${response.status}`);
              }

              const data = await response.json();
              
              if (data.trip_id) {
                setCurrentTripId(data.trip_id);
                if (tripId !== data.trip_id) {
                  window.history.replaceState(null, '', `/trips/${data.trip_id}/chat`);
                }
              }

              const aiMessage = {
                id: Date.now() + 1,
                role: 'assistant',
                content: data.message || 'Trip plan generated successfully!',
                timestamp: new Date().toISOString(),
                trip_plan: data.trip_plan,
              };

              setMessages(prev => [...prev, aiMessage]);
              saveMessageToLocalStorage(userMessage);
              saveMessageToLocalStorage(aiMessage);

              if (data.trip_plan?.request?.destination) {
                setTripInfo(prev => ({
                  ...prev,
                  destination: data.trip_plan.request.destination,
                  title: data.trip_plan.request.destination || prev?.title || `Trip ${data.trip_id}`,
                }));
              }
            } catch (error) {
              console.error('Error auto-sending prompt:', error);
              const errorMessage = {
                id: Date.now() + 1,
                role: 'assistant',
                content: `❌ Error: ${error.message}. Please try again.`,
                timestamp: new Date().toISOString(),
                isError: true,
              };
              setMessages(prev => [...prev, errorMessage]);
            } finally {
              setIsLoading(false);
            }
          };
          
          // Wait a bit for component to be ready
          setTimeout(() => {
            if (isMounted) {
              autoSendPrompt();
            }
          }, 500);
          return; // Exit early - auto-sent prompt
        }

        // If no messages exist and we have a trip prompt, save it as the first message
        if (!hasExistingMessages && localTrip?.prompt && isMounted) {
          const tripPrompt = localTrip.prompt;
          const initialMessage = {
            id: Date.now(),
            role: 'user',
            content: tripPrompt,
            timestamp: new Date().toISOString()
          };
          await saveMessageToBackend(initialMessage).catch(() => {});
          saveMessageToLocalStorage(initialMessage);
          setMessages([initialMessage]);
        }
      } catch (error) {
        console.error('Error fetching trip data:', error);
        if (!isMounted) return;
        
        // Use fallback data
        const localTrips = getTripsFromLocalStorage();
        const localTrip = localTrips.find(trip => trip.id === tripId);
        if (localTrip && isMounted) {
          setTripInfo({
            id: localTrip.id,
            title: localTrip.title,
            destination: localTrip.destination,
            image: localTrip.image,
            prompt: localTrip.prompt
          });
               // Save local trip prompt as first message
               if (localTrip.prompt) {
                 const initialMessage = {
                   id: Date.now(),
                   role: 'user',
                   content: localTrip.prompt,
                   timestamp: new Date().toISOString()
                 };
                 await saveMessageToBackend(initialMessage).catch(() => {});
                 saveMessageToLocalStorage(initialMessage);
                 setMessages([initialMessage]);
               }
        } else if (isMounted) {
          setTripInfo({
            id: tripId,
            title: `Trip ${tripId}`,
            destination: 'Unknown',
            image: 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&h=400&fit=crop'
          });
        }
      }
    };

    fetchTripDataAndGeneratePlan();
    
    return () => {
      isMounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tripId]);


  // Save message to backend
  const saveMessageToBackend = async (message) => {
    try {
      const response = await fetch(`${CHAT_API_ENDPOINT}/trips/${tripId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: 'Kartik7',
          tripId: tripId,
          message: message,
          timestamp: message.timestamp
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('✅ Message saved to backend:', result);
    } catch (error) {
      console.error('❌ Error saving message to backend:', error);
      // Also save to localStorage as backup
      saveMessageToLocalStorage(message);
    }
  };

  // Save message to localStorage as backup
  const saveMessageToLocalStorage = (message) => {
    try {
      const key = `trip_chat_${tripId}`;
      const existingMessages = JSON.parse(localStorage.getItem(key) || '[]');
      existingMessages.push(message);
      localStorage.setItem(key, JSON.stringify(existingMessages));
    } catch (error) {
      console.error('Error saving message to localStorage:', error);
    }
  };


  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userPrompt = inputMessage.trim();
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: userPrompt,
      timestamp: new Date().toISOString()
    };

    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Call the chat API endpoint that runs all agents
      const response = await fetch(`${API_ENDPOINT}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: userPrompt,
          user_id: 'Kartik7', // TODO: Get from auth context
          trip_id: currentTripId || undefined, // Use current trip_id if exists
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }

      const data = await response.json();
      
      // Update trip_id if this is a new trip
      if (data.trip_id && !currentTripId) {
        setCurrentTripId(data.trip_id);
        // Update URL if needed
        if (tripId !== data.trip_id) {
          window.history.replaceState(null, '', `/trips/${data.trip_id}/chat`);
        }
      }

      // Add AI response message
      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.message || 'Trip plan generated successfully!',
        timestamp: new Date().toISOString(),
        trip_plan: data.trip_plan, // Store full trip plan for display
      };

      setMessages(prev => [...prev, aiMessage]);
      
      // Save messages to backend and localStorage
      await saveMessageToBackend(userMessage);
      await saveMessageToBackend(aiMessage);
      saveMessageToLocalStorage(userMessage);
      saveMessageToLocalStorage(aiMessage);

      // Update trip info if available
      if (data.trip_plan) {
        const plan = data.trip_plan;
        if (plan.request && plan.request.destination) {
          setTripInfo(prev => ({
            ...prev,
            destination: plan.request.destination,
            title: plan.request.destination || prev?.title || `Trip ${data.trip_id}`,
          }));
        }
      }

    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `❌ Error: ${error.message}. Please try again.`,
        timestamp: new Date().toISOString(),
        isError: true,
      };
      
      setMessages(prev => [...prev, errorMessage]);
      saveMessageToLocalStorage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // Invite user to view chat
  const handleInviteUser = async (e) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;

    try {
      const response = await fetch(`${CHAT_API_ENDPOINT}/trips/${tripId}/invite`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: 'Kartik7',
          tripId: tripId,
          inviteEmail: inviteEmail.trim()
        })
      });

      if (response.ok) {
        await response.json(); // Response handled, but data not needed
        setSharedUsers(prev => [...prev, { email: inviteEmail.trim(), status: 'invited' }]);
        setInviteEmail('');
        setShowInviteModal(false);
        alert(`Invitation sent to ${inviteEmail.trim()}`);
      } else {
        alert('Failed to send invitation. Please try again.');
      }
    } catch (error) {
      console.error('Error inviting user:', error);
      alert('Failed to send invitation. Please try again.');
    }
  };

  // Fetch shared users
  useEffect(() => {
    const fetchSharedUsers = async () => {
      try {
        const response = await fetch(`${CHAT_API_ENDPOINT}/trips/${tripId}/shared-users?userId=Kartik7`);
      if (response.ok) {
        const responseData = await response.json();
        setSharedUsers(responseData.sharedUsers || []);
      }
      } catch (error) {
        console.error('Error fetching shared users:', error);
      }
    };
    fetchSharedUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tripId]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };


  return (
    <div className="trip-chat-page">
      <button className="back-button" onClick={() => navigate('/trips')}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M19 12H5M5 12L12 19M5 12L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        Back to My Trips
      </button>

      {tripInfo && (
        <div className="trip-chat-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flex: 1 }}>
            <div className="trip-chat-header-image">
              <img src={tripInfo.image} alt={tripInfo.destination} />
            </div>
            <div className="trip-chat-header-info">
              <h2>{tripInfo.title || `Trip ${tripId}`}</h2>
              <p>{tripInfo.destination || 'Unknown Destination'}</p>
            </div>
          </div>
          <div className="trip-chat-header-actions">
            <button 
              className="invite-button"
              onClick={() => setShowInviteModal(true)}
              title="Invite user to view chat"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <circle cx="8.5" cy="7" r="4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M20 8v6M23 11h-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Invite
            </button>
            {sharedUsers.length > 0 && (
              <div className="shared-users">
                <span className="shared-users-label">Shared with:</span>
                {sharedUsers.map((user, idx) => (
                  <span key={idx} className="shared-user-badge">{user.email}</span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {showInviteModal && (
        <div className="invite-modal-overlay" onClick={() => setShowInviteModal(false)}>
          <div className="invite-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Invite User to View Chat</h3>
            <form onSubmit={handleInviteUser}>
              <input
                type="email"
                className="invite-email-input"
                placeholder="Enter email address"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                required
              />
              <div className="invite-modal-actions">
                <button type="button" onClick={() => setShowInviteModal(false)}>Cancel</button>
                <button type="submit">Send Invitation</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="chat-container">
        <div className="chat-messages" ref={messagesEndRef}>
          {messages.length === 0 ? (
            <div className="chat-empty-state">
              <div className="empty-state-icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3>Start a conversation</h3>
              <p>Add notes, questions, or details about your trip.</p>
            </div>
          ) : (
            messages.map((message) => (
              <div 
                key={message.id} 
                className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'} ${message.isError ? 'error-message' : ''}`}
              >
                <div className="message-content">
                  {message.role === 'assistant' && message.trip_plan ? (
                    <div className="trip-plan-summary">
                      {/* Display the formatted message content */}
                      <div className="trip-plan-text" style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.9em' }}>
                        {message.content}
                      </div>
                      
                      {/* Also display structured data for better visualization */}
                      {message.trip_plan && (
                        <div className="trip-plan-details">
                          {/* ACCOMMODATIONS - Show ALL */}
                          {message.trip_plan.accommodations && message.trip_plan.accommodations.length > 0 && (
                            <div className="plan-section">
                              <h4>🏨 All Accommodations ({message.trip_plan.accommodations.length})</h4>
                              {message.trip_plan.accommodations.map((acc, idx) => (
                                <div key={idx} className="plan-item">
                                  <strong>{acc.title}</strong>
                                  {acc.description && <p className="item-description">{acc.description}</p>}
                                  {acc.address && <p className="item-location">📍 {acc.address}</p>}
                                  <div className="item-details">
                                    {acc.price_per_night && <span>💰 ${acc.price_per_night.toFixed(2)}/night</span>}
                                    {acc.rating && <span>⭐ {acc.rating}/5.0 ({acc.review_count || 0} reviews)</span>}
                                    {acc.amenities && acc.amenities.length > 0 && (
                                      <span>✨ {acc.amenities.slice(0, 3).join(', ')}</span>
                                    )}
                                  </div>
                                  {acc.booking_url && (
                                    <a href={acc.booking_url} target="_blank" rel="noopener noreferrer" className="booking-link">
                                      🔗 Book Now
                                    </a>
                                  )}
                                </div>
                              ))}
                              {message.trip_plan.selected_accommodation && (
                                <div className="selected-item">
                                  ✅ <strong>SELECTED:</strong> {message.trip_plan.selected_accommodation.title}
                                </div>
                              )}
                            </div>
                          )}
                          
                          {/* RESTAURANTS - Show ALL */}
                          {message.trip_plan.restaurants && message.trip_plan.restaurants.length > 0 && (
                            <div className="plan-section">
                              <h4>🍽️ All Restaurants & Cafes ({message.trip_plan.restaurants.length})</h4>
                              {message.trip_plan.restaurants.map((rest, idx) => (
                                <div key={idx} className="plan-item">
                                  <strong>{rest.name}</strong>
                                  {rest.description && <p className="item-description">{rest.description}</p>}
                                  {rest.address && <p className="item-location">📍 {rest.address}</p>}
                                  <div className="item-details">
                                    {rest.cuisine_type && <span>🍴 {rest.cuisine_type}</span>}
                                    {rest.price_range && <span>💰 {rest.price_range}</span>}
                                    {rest.average_price_per_person && <span>💵 ${rest.average_price_per_person.toFixed(2)}/person</span>}
                                    {rest.rating && <span>⭐ {rest.rating}/5.0 ({rest.review_count || 0} reviews)</span>}
                                  </div>
                                  {rest.dietary_options && rest.dietary_options.length > 0 && (
                                    <p className="item-tags">🌱 {rest.dietary_options.join(', ')}</p>
                                  )}
                                  {rest.accessibility_features && rest.accessibility_features.length > 0 && (
                                    <p className="item-tags">♿ {rest.accessibility_features.join(', ')}</p>
                                  )}
                                  {rest.booking_url && (
                                    <a href={rest.booking_url} target="_blank" rel="noopener noreferrer" className="booking-link">
                                      🔗 Reserve
                                    </a>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                          
                          {/* TRANSPORTATION - Show ALL */}
                          {message.trip_plan.transportation && message.trip_plan.transportation.length > 0 && (
                            <div className="plan-section">
                              <h4>✈️ All Transportation Options ({message.trip_plan.transportation.length})</h4>
                              {message.trip_plan.transportation.map((trans, idx) => (
                                <div key={idx} className="plan-item">
                                  <strong>{trans.type?.toUpperCase()} - {trans.provider || 'N/A'}</strong>
                                  {trans.origin && trans.destination && (
                                    <p className="item-location">🗺️ {trans.origin} → {trans.destination}</p>
                                  )}
                                  <div className="item-details">
                                    {trans.price && <span>💰 ${trans.price.toFixed(2)}</span>}
                                    {trans.price_per_person && <span>💵 ${trans.price_per_person.toFixed(2)}/person</span>}
                                    {trans.duration_minutes && (
                                      <span>⏱️ {Math.floor(trans.duration_minutes / 60)}h {trans.duration_minutes % 60}m</span>
                                    )}
                                    {trans.transfers !== null && trans.transfers !== undefined && (
                                      <span>🔄 {trans.transfers} transfer(s)</span>
                                    )}
                                  </div>
                                  {trans.recommended && <span className="recommended-badge">✅ RECOMMENDED</span>}
                                  {trans.booking_url && (
                                    <a href={trans.booking_url} target="_blank" rel="noopener noreferrer" className="booking-link">
                                      🔗 Book Now
                                    </a>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                          
                          {/* EXPERIENCES - Show ALL */}
                          {message.trip_plan.experiences && message.trip_plan.experiences.length > 0 && (
                            <div className="plan-section">
                              <h4>🎯 All Experiences & Activities ({message.trip_plan.experiences.length})</h4>
                              {message.trip_plan.experiences.map((exp, idx) => (
                                <div key={idx} className="plan-item">
                                  <strong>{exp.name}</strong>
                                  {exp.description && <p className="item-description">{exp.description}</p>}
                                  {exp.address && <p className="item-location">📍 {exp.address}</p>}
                                  <div className="item-details">
                                    {exp.category && <span>🏷️ {exp.category}</span>}
                                    {exp.price !== null && exp.price !== undefined && (
                                      <span>💰 {exp.price === 0 ? 'Free' : `$${exp.price.toFixed(2)}`}</span>
                                    )}
                                    {exp.duration_hours && <span>⏱️ {exp.duration_hours} hours</span>}
                                    {exp.rating && <span>⭐ {exp.rating}/5.0 ({exp.review_count || 0} reviews)</span>}
                                  </div>
                                  {exp.booking_url && exp.booking_url !== 'N/A' && (
                                    <a href={exp.booking_url} target="_blank" rel="noopener noreferrer" className="booking-link">
                                      🔗 Book Now
                                    </a>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                          
                          {/* BUDGET - Full Breakdown */}
                          {message.trip_plan.budget && (
                            <div className="plan-section">
                              <h4>💰 Complete Budget Breakdown</h4>
                              <div className="budget-breakdown">
                                {message.trip_plan.budget.accommodation && (
                                  <div className="budget-item">
                                    <span>🏨 Accommodation:</span>
                                    <span>${message.trip_plan.budget.accommodation.toFixed(2)}</span>
                                  </div>
                                )}
                                {message.trip_plan.budget.transportation && (
                                  <div className="budget-item">
                                    <span>✈️ Transportation:</span>
                                    <span>${message.trip_plan.budget.transportation.toFixed(2)}</span>
                                  </div>
                                )}
                                {message.trip_plan.budget.experiences && (
                                  <div className="budget-item">
                                    <span>🎯 Experiences:</span>
                                    <span>${message.trip_plan.budget.experiences.toFixed(2)}</span>
                                  </div>
                                )}
                                {message.trip_plan.budget.meals && (
                                  <div className="budget-item">
                                    <span>🍽️ Meals:</span>
                                    <span>${message.trip_plan.budget.meals.toFixed(2)}</span>
                                  </div>
                                )}
                                {message.trip_plan.budget.miscellaneous && (
                                  <div className="budget-item">
                                    <span>🛍️ Miscellaneous:</span>
                                    <span>${message.trip_plan.budget.miscellaneous.toFixed(2)}</span>
                                  </div>
                                )}
                                {message.trip_plan.budget.total && (
                                  <div className="budget-total">
                                    <span><strong>💵 TOTAL:</strong></span>
                                    <span><strong>${message.trip_plan.budget.total.toFixed(2)} {message.trip_plan.budget.currency || 'USD'}</strong></span>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                          
                          {/* ITINERARY - Show ALL Days */}
                          {message.trip_plan.itinerary && message.trip_plan.itinerary.length > 0 && (
                            <div className="plan-section">
                              <h4>📅 Complete Day-by-Day Itinerary ({message.trip_plan.itinerary.length} days)</h4>
                              {message.trip_plan.itinerary.map((day, idx) => (
                                <div key={idx} className="itinerary-day-full">
                                  <h5>Day {day.day || idx + 1} ({day.date || 'TBD'})</h5>
                                  
                                  {day.activities && day.activities.length > 0 && (
                                    <div className="day-activities">
                                      <strong>🎯 Activities:</strong>
                                      {day.activities.map((activity, actIdx) => {
                                        const act = typeof activity === 'object' ? activity : { title: activity };
                                        return (
                                          <div key={actIdx} className="activity-item">
                                            <span className="activity-time">{act.time || 'TBD'}:</span>
                                            <span className="activity-title"><strong>{act.title || 'Activity'}</strong></span>
                                            {act.description && <p className="activity-desc">{act.description}</p>}
                                            {act.location && <p className="activity-location">📍 {act.location}</p>}
                                          </div>
                                        );
                                      })}
                                    </div>
                                  )}
                                  
                                  {day.meals && day.meals.length > 0 && (
                                    <div className="day-meals">
                                      <strong>🍽️ Meals:</strong>
                                      {day.meals.map((meal, mealIdx) => {
                                        const m = typeof meal === 'object' ? meal : { type: 'meal', restaurant: meal };
                                        return (
                                          <div key={mealIdx} className="meal-item">
                                            <span className="meal-time">{m.time || 'TBD'}</span>
                                            <span className="meal-type">({m.type || 'meal'})</span>
                                            <span className="meal-restaurant"><strong>{m.restaurant || 'TBD'}</strong></span>
                                            {m.description && <p className="meal-desc">{m.description}</p>}
                                          </div>
                                        );
                                      })}
                                    </div>
                                  )}
                                  
                                  {day.notes && (
                                    <div className="day-notes">
                                      <strong>💡 Notes:</strong> {day.notes}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
                  )}
                </div>
                <div className="message-timestamp">
                  {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div className="message assistant-message">
              <div className="message-content">
                <div className="loading-indicator">
                  <div className="spinner"></div>
                  <span>Planning your trip... This may take a few minutes.</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="chat-input-form" onSubmit={handleSendMessage}>
          <div className="chat-input-wrapper">
            <textarea
              ref={inputRef}
              className="chat-input"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Add a note or message about your trip..."
              rows="1"
            />
            <button 
              type="submit" 
              className="chat-send-button"
              disabled={!inputMessage.trim() || isLoading}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TripChat;

