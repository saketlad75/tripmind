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

  const API_ENDPOINT = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/trip-planner';

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

        // Try to fetch from backend API
        try {
          const tripResponse = await fetch(`${API_ENDPOINT}/trips/${tripId}?userId=Kartik7`);
          if (tripResponse.ok && isMounted) {
            const tripData = await tripResponse.json();
            setTripInfo(prev => prev || tripData);
          }
        } catch (err) {
          console.log('Could not fetch from backend, using local data');
        }

        // Fetch existing messages
        let hasExistingMessages = false;
        try {
          const messagesResponse = await fetch(`${API_ENDPOINT}/trips/${tripId}/messages?userId=Kartik7`);
          if (messagesResponse.ok) {
            const messagesData = await messagesResponse.json();
            if (messagesData.messages && messagesData.messages.length > 0 && isMounted) {
              setMessages(messagesData.messages);
              hasExistingMessages = true;
            }
          }
        } catch (err) {
          console.log('Could not fetch messages from backend');
          // Try to load from localStorage as backup
          try {
            const key = `trip_chat_${tripId}`;
            const localMessages = JSON.parse(localStorage.getItem(key) || '[]');
            if (localMessages.length > 0 && isMounted) {
              setMessages(localMessages);
              hasExistingMessages = true;
            }
          } catch (localErr) {
            console.log('Could not load messages from localStorage');
          }
        }

            // If no messages exist and we have a prompt, save it as the first message
            if (!hasExistingMessages) {
              const tripPrompt = localTrip?.prompt;
              if (tripPrompt && isMounted) {
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
      await fetch(`${API_ENDPOINT}/trips/${tripId}/messages`, {
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
    } catch (error) {
      console.error('Error saving message to backend:', error);
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
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString()
    };

    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');

    // Save user message to backend
    await saveMessageToBackend(userMessage);
    saveMessageToLocalStorage(userMessage);
  };

  // Invite user to view chat
  const handleInviteUser = async (e) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;

    try {
      const response = await fetch(`${API_ENDPOINT}/trips/${tripId}/invite`, {
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
        const response = await fetch(`${API_ENDPOINT}/trips/${tripId}/shared-users?userId=Kartik7`);
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
              <div key={message.id} className="message user-message">
                <div className="message-content">
                  {message.content}
                </div>
                <div className="message-timestamp">
                  {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            ))
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
              disabled={!inputMessage.trim()}
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

