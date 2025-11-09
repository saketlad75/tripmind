// Utility functions for trip management

// Common location keywords to extract from prompts
const locationKeywords = [
  'tokyo', 'japan', 'paris', 'france', 'london', 'uk', 'england', 'new york', 'nyc',
  'bali', 'indonesia', 'sydney', 'australia', 'dubai', 'uae', 'singapore', 'bangkok',
  'thailand', 'seoul', 'korea', 'hong kong', 'beijing', 'china', 'rome', 'italy',
  'barcelona', 'spain', 'amsterdam', 'netherlands', 'berlin', 'germany', 'vienna',
  'austria', 'prague', 'czech', 'istanbul', 'turkey', 'cairo', 'egypt', 'mumbai',
  'india', 'rio', 'brazil', 'cape town', 'south africa', 'maldives', 'hawaii',
  'santorini', 'greece', 'iceland', 'switzerland', 'norway', 'morocco', 'phuket',
  'lisbon', 'portugal', 'kyoto', 'budapest', 'hungary', 'edinburgh', 'scotland',
  'stockholm', 'sweden', 'copenhagen', 'denmark', 'new zealand', 'machu picchu',
  'peru', 'mexico', 'canada', 'vancouver', 'toronto', 'montreal'
];

// Extract location from prompt text
export const extractLocation = (prompt) => {
  if (!prompt) return 'Unknown Destination';
  
  const lowerPrompt = prompt.toLowerCase();
  
  // Try to find location keywords
  for (const keyword of locationKeywords) {
    if (lowerPrompt.includes(keyword)) {
      // Capitalize first letter of each word
      return keyword.split(' ').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ');
    }
  }
  
  // Try to extract location from common patterns
  const patterns = [
    /(?:to|in|visit|travel to|going to|planning.*?to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/gi,
    /([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+(?:Japan|France|USA|UK|Italy|Spain|Germany|etc\.?)/gi,
  ];
  
  for (const pattern of patterns) {
    const matches = prompt.match(pattern);
    if (matches && matches.length > 0) {
      const location = matches[0].replace(/(?:to|in|visit|travel to|going to|planning.*?to)\s+/gi, '').trim();
      if (location.length > 2 && location.length < 50) {
        return location;
      }
    }
  }
  
  // Fallback: use first few words if no location found
  const words = prompt.trim().split(/\s+/).slice(0, 3);
  return words.join(' ') || 'New Trip';
};

// Generate a destination image URL based on location
export const getDestinationImage = (location) => {
  // Map common locations to Unsplash image URLs
  const imageMap = {
    'tokyo': 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800&h=400&fit=crop',
    'japan': 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800&h=400&fit=crop',
    'paris': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&h=400&fit=crop',
    'france': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&h=400&fit=crop',
    'london': 'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&h=400&fit=crop',
    'new york': 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800&h=400&fit=crop',
    'bali': 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800&h=400&fit=crop',
    'dubai': 'https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=800&h=400&fit=crop',
    'sydney': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=400&fit=crop',
  };
  
  const locationLower = location.toLowerCase();
  for (const [key, imageUrl] of Object.entries(imageMap)) {
    if (locationLower.includes(key)) {
      return imageUrl;
    }
  }
  
  // Default travel image
  return 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&h=400&fit=crop';
};

// Save trip to localStorage
export const saveTripToLocalStorage = (trip) => {
  try {
    const trips = getTripsFromLocalStorage();
    // Check if trip with same ID already exists
    const existingIndex = trips.findIndex(t => t.id === trip.id);
    if (existingIndex >= 0) {
      trips[existingIndex] = trip; // Update existing
    } else {
      trips.unshift(trip); // Add new trip at the beginning
    }
    localStorage.setItem('userTrips', JSON.stringify(trips));
    return true;
  } catch (error) {
    console.error('Error saving trip to localStorage:', error);
    return false;
  }
};

// Get trips from localStorage
export const getTripsFromLocalStorage = () => {
  try {
    const tripsJson = localStorage.getItem('userTrips');
    return tripsJson ? JSON.parse(tripsJson) : [];
  } catch (error) {
    console.error('Error reading trips from localStorage:', error);
    return [];
  }
};

// Delete trip from localStorage
export const deleteTripFromLocalStorage = (tripId) => {
  try {
    const trips = getTripsFromLocalStorage();
    const filteredTrips = trips.filter(trip => trip.id !== tripId);
    localStorage.setItem('userTrips', JSON.stringify(filteredTrips));
    return true;
  } catch (error) {
    console.error('Error deleting trip from localStorage:', error);
    return false;
  }
};

// Create a trip object from prompt and tripId
export const createTripFromPrompt = (prompt, tripId, userId = 'Kartik7') => {
  const location = extractLocation(prompt);
  const title = `${location} Trip`;
  
  return {
    id: tripId,
    title: title,
    destination: location,
    prompt: prompt,
    userId: userId,
    image: getDestinationImage(location),
    date: new Date().toISOString().split('T')[0], // Today's date in YYYY-MM-DD format
    status: 'Planning',
    createdAt: new Date().toISOString()
  };
};

