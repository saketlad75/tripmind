import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTripsFromLocalStorage, deleteTripFromLocalStorage } from '../utils/tripUtils';
import './MyTripsListing.css';

const MyTripsListing = () => {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  // Fetch trips from backend API and localStorage
  useEffect(() => {
    const fetchTrips = async () => {
      try {
        // First, get trips from localStorage (always available)
        const localTrips = getTripsFromLocalStorage();
        
        // Try to fetch from backend API
        try {
          const API_ENDPOINT = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/trip-planner';
          const response = await fetch(`${API_ENDPOINT}/trips?userId=Kartik7`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
            },
          });

          if (response.ok) {
            const data = await response.json();
            const backendTrips = data.trips || [];
            
            // Merge backend trips with local trips, prioritizing backend data
            // Create a map to avoid duplicates
            const tripMap = new Map();
            
            // Add local trips first
            localTrips.forEach(trip => {
              tripMap.set(trip.id, trip);
            });
            
            // Override with backend trips if they exist
            backendTrips.forEach(trip => {
              tripMap.set(trip.id, trip);
            });
            
            // Convert map to array and sort by date (newest first)
            const mergedTrips = Array.from(tripMap.values()).sort((a, b) => {
              return new Date(b.date || b.createdAt) - new Date(a.date || a.createdAt);
            });
            
            setTrips(mergedTrips);
          } else {
            // If backend fails, use local trips
            setTrips(localTrips.sort((a, b) => {
              return new Date(b.date || b.createdAt) - new Date(a.date || a.createdAt);
            }));
          }
        } catch (error) {
          console.error('Error fetching trips from backend:', error);
          // If backend fails, use local trips
          setTrips(localTrips.sort((a, b) => {
            return new Date(b.date || b.createdAt) - new Date(a.date || a.createdAt);
          }));
        }
      } catch (error) {
        console.error('Error fetching trips:', error);
        setTrips([]);
      } finally {
        setLoading(false);
      }
    };

    fetchTrips();
  }, []);

  // Sample trips for demonstration
  const sampleTrips = [
    {
      id: 'trip-1',
      title: 'Japan Adventure',
      destination: 'Tokyo, Japan',
      image: 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800&h=400&fit=crop',
      date: '2024-03-15',
      status: 'Planning',
      prompt: 'Plan a 10-day trip to Japan in March 2024. I have diabetes and prefer budget hotels. Include weather-based backup plans.'
    },
    {
      id: 'trip-2',
      title: 'European Tour',
      destination: 'Paris, France',
      image: 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&h=400&fit=crop',
      date: '2024-05-20',
      status: 'Upcoming',
      prompt: '7-day European tour with medical insurance, visiting Paris and Rome.'
    },
    {
      id: 'trip-3',
      title: 'Bali Family Trip',
      destination: 'Bali, Indonesia',
      image: 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800&h=400&fit=crop',
      date: '2024-07-10',
      status: 'Planning',
      prompt: 'Family trip to Bali with weather backup plans and kid-friendly activities.'
    },
    {
      id: 'trip-4',
      title: 'New York City',
      destination: 'New York, USA',
      image: 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800&h=400&fit=crop',
      date: '2024-09-05',
      status: 'Upcoming',
      prompt: 'Weekend trip to New York with Broadway shows and shopping recommendations.'
    },
  ];

  // Use trips from state (which includes both backend and local storage)
  // Only show sample trips if no trips exist at all
  const displayTrips = trips.length > 0 ? trips : sampleTrips;

  // Filter trips based on search query
  const filteredTrips = displayTrips.filter(trip => 
    trip.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    trip.destination.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (trip.prompt && trip.prompt.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleTripClick = (tripId, e) => {
    // Don't navigate if clicking on delete button
    if (e && (e.target.closest('.delete-trip-button') || e.target.closest('.delete-trip-icon'))) {
      return;
    }
    navigate(`/trips/${tripId}/chat`);
  };

  const handleDeleteTrip = async (tripId, e) => {
    e.stopPropagation(); // Prevent triggering trip click
    
    // Confirm deletion
    if (!window.confirm('Are you sure you want to delete this trip? This action cannot be undone.')) {
      return;
    }

    try {
      // Delete from localStorage
      deleteTripFromLocalStorage(tripId);
      
      // Try to delete from backend (optional, non-blocking)
      try {
        const API_ENDPOINT = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/trip-planner';
        await fetch(`${API_ENDPOINT}/trips/${tripId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          },
        }).catch(err => {
          console.log('Could not delete trip from backend:', err);
        });
      } catch (err) {
        console.log('Error deleting trip from backend:', err);
      }
      
      // Update trips list
      const updatedTrips = trips.filter(trip => trip.id !== tripId);
      setTrips(updatedTrips);
      
    } catch (error) {
      console.error('Error deleting trip:', error);
      alert('Failed to delete trip. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="my-trips-listing">
        <h2 className="listing-title">My Trips</h2>
        <div className="listing-loading">
          <p>Loading your trips...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="my-trips-listing">
      <h2 className="listing-title">My Trips</h2>
      
      {/* Search Bar */}
      <div className="trips-search-container">
        <input
          type="text"
          className="trips-search-input"
          placeholder="Search trips by destination, title, or description..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <svg className="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2"/>
          <path d="m21 21-4.35-4.35" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      </div>

      {filteredTrips.length === 0 ? (
        <div className="listing-empty">
          <p>{searchQuery ? 'No trips found matching your search.' : "You don't have any trips yet. Start planning your first adventure!"}</p>
        </div>
      ) : (
        <div className="trips-grid">
          {filteredTrips.map((trip) => (
            <div 
              key={trip.id} 
              className="trip-banner-card"
              onClick={(e) => handleTripClick(trip.id, e)}
            >
              <div className="trip-banner-image-wrapper">
                <img 
                  src={trip.image} 
                  alt={trip.destination}
                  className="trip-banner-image"
                  loading="lazy"
                />
                <div className="trip-banner-overlay">
                  <button
                    className="delete-trip-button"
                    onClick={(e) => handleDeleteTrip(trip.id, e)}
                    title="Delete trip"
                    aria-label="Delete trip"
                  >
                    <svg className="delete-trip-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3 6H5H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6H19Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M10 11V17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M14 11V17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </button>
                  <div className="trip-banner-content">
                    <h3 className="trip-banner-title">{trip.title}</h3>
                    <p className="trip-banner-destination">{trip.destination}</p>
                    <div className="trip-banner-meta">
                      <span className="trip-banner-date">{new Date(trip.date).toLocaleDateString()}</span>
                      <span className={`trip-banner-status ${trip.status.toLowerCase()}`}>{trip.status}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyTripsListing;

