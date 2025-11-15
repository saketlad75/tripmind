import React, { useState, useEffect } from 'react';
import SearchBar from './SearchBar';
import './HeroBanner.css';

const HeroBanner = () => {
  // Group destinations by similarity for better rotation
  // Each set contains 10 destinations (2 rows × 5 columns)
  const destinationSets = [
    // Set 1: Tropical & Beach Destinations
    [
      { id: 1, name: 'Bali, Indonesia', image: 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=600&h=400&fit=crop', description: 'Tropical paradise with stunning beaches' },
      { id: 5, name: 'Maldives', image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&h=400&fit=crop', description: 'Crystal clear waters and overwater bungalows' },
      { id: 12, name: 'Hawaii, USA', image: 'https://images.unsplash.com/photo-1531168556467-80aace0d0144?w=600&h=400&fit=crop', description: 'Volcanic islands with pristine beaches' },
      { id: 2, name: 'Santorini, Greece', image: 'https://images.unsplash.com/photo-1613395877344-13d4a8e0d49e?w=600&h=400&fit=crop', description: 'Breathtaking sunsets and white-washed buildings' },
      { id: 26, name: 'Rio de Janeiro, Brazil', image: 'https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=600&h=400&fit=crop', description: 'Vibrant beaches and carnival spirit' },
      { id: 25, name: 'Cape Town, South Africa', image: 'https://images.unsplash.com/photo-1505142468610-359e7d316be0?w=600&h=400&fit=crop', description: 'Stunning coastline and Table Mountain' },
      { id: 10, name: 'Sydney, Australia', image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&h=400&fit=crop', description: 'Harbor city with iconic landmarks' },
      { id: 28, name: 'Seychelles', image: 'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=600&h=400&fit=crop', description: 'Pristine beaches and crystal-clear waters' },
      { id: 29, name: 'Mumbai, India', image: 'https://images.unsplash.com/photo-1529253355930-ddbe423a2ac7?w=600&h=400&fit=crop', description: 'Bollywood city with diverse culture' },
      { id: 37, name: 'Phuket, Thailand', image: 'https://images.unsplash.com/photo-1552465011-b4e21bf6e79a?w=600&h=400&fit=crop', description: 'Tropical paradise with vibrant nightlife' },
    ],
    // Set 2: European Cities
    [
      { id: 4, name: 'Paris, France', image: 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=600&h=400&fit=crop', description: 'The City of Light and romance' },
      { id: 8, name: 'Rome, Italy', image: 'https://images.unsplash.com/photo-1529260830199-42c24126f198?w=600&h=400&fit=crop', description: 'Eternal city with rich history' },
      { id: 9, name: 'Barcelona, Spain', image: 'https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=600&h=400&fit=crop', description: 'Vibrant culture and stunning architecture' },
      { id: 16, name: 'London, UK', image: 'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=600&h=400&fit=crop', description: 'Historic capital with royal heritage' },
      { id: 17, name: 'Amsterdam, Netherlands', image: 'https://images.unsplash.com/photo-1534351590666-13e3e96b5017?w=600&h=400&fit=crop', description: 'Canals, art, and cycling culture' },
      { id: 18, name: 'Prague, Czech Republic', image: 'https://images.unsplash.com/photo-1541849546-216549ae216d?w=600&h=400&fit=crop', description: 'Medieval charm and Gothic architecture' },
      { id: 19, name: 'Vienna, Austria', image: 'https://images.unsplash.com/photo-1516550893923-42d28e5677af?w=600&h=400&fit=crop', description: 'Imperial elegance and classical music' },
      { id: 20, name: 'Venice, Italy', image: 'https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?w=600&h=400&fit=crop', description: 'Romantic canals and Renaissance art' },
      { id: 31, name: 'Lisbon, Portugal', image: 'https://images.unsplash.com/photo-1513622470522-26c3c8a854bc?w=600&h=400&fit=crop', description: 'Historic hills and colorful tiles' },
      { id: 38, name: 'Berlin, Germany', image: 'https://images.unsplash.com/photo-1587330979470-3595ac045ab0?w=600&h=400&fit=crop', description: 'Historic city with vibrant art scene' },
    ],
    // Set 3: Asian Metropolises
    [
      { id: 3, name: 'Tokyo, Japan', image: 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=600&h=400&fit=crop', description: 'Modern metropolis meets ancient tradition' },
      { id: 21, name: 'Seoul, South Korea', image: 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=600&h=400&fit=crop', description: 'Modern tech hub with ancient palaces' },
      { id: 22, name: 'Singapore', image: 'https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=600&h=400&fit=crop', description: 'Garden city with futuristic skyline' },
      { id: 23, name: 'Hong Kong', image: 'https://images.unsplash.com/photo-1536599018102-9f803c140fc1?w=600&h=400&fit=crop', description: 'Vibrant cityscape and culinary paradise' },
      { id: 30, name: 'Kyoto, Japan', image: 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=600&h=400&fit=crop', description: 'Traditional temples and cherry blossoms' },
      { id: 7, name: 'New York, USA', image: 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=600&h=400&fit=crop', description: 'The city that never sleeps' },
      { id: 6, name: 'Dubai, UAE', image: 'https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=600&h=400&fit=crop', description: 'Luxury and modern architecture' },
      { id: 32, name: 'Istanbul, Turkey', image: 'https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?w=600&h=400&fit=crop', description: 'Where East meets West' },
      { id: 24, name: 'Cairo, Egypt', image: 'https://images.unsplash.com/photo-1526392060635-9d6019884377?w=600&h=400&fit=crop', description: 'Ancient pyramids and rich history' },
      { id: 39, name: 'Bangkok, Thailand', image: 'https://images.unsplash.com/photo-1552465011-b4e21bf6e79a?w=600&h=400&fit=crop', description: 'Temples, street food, and vibrant culture' },
    ],
    // Set 4: Natural Wonders & Adventure
    [
      { id: 11, name: 'Iceland', image: 'https://images.unsplash.com/photo-1531168556467-80aace0d0144?w=600&h=400&fit=crop', description: 'Land of fire and ice' },
      { id: 13, name: 'Switzerland', image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&h=400&fit=crop', description: 'Alpine beauty and pristine lakes' },
      { id: 15, name: 'Norway', image: 'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=600&h=400&fit=crop', description: 'Fjords and Northern Lights' },
      { id: 27, name: 'Machu Picchu, Peru', image: 'https://images.unsplash.com/photo-1526392060635-9d6019884377?w=600&h=400&fit=crop', description: 'Ancient Incan citadel in the clouds' },
      { id: 14, name: 'Morocco', image: 'https://images.unsplash.com/photo-1539020140153-e479b8c22e70?w=600&h=400&fit=crop', description: 'Exotic markets and desert landscapes' },
      { id: 33, name: 'Budapest, Hungary', image: 'https://images.unsplash.com/photo-1541849546-216549ae216d?w=600&h=400&fit=crop', description: 'The Pearl of the Danube' },
      { id: 34, name: 'Edinburgh, Scotland', image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&h=400&fit=crop', description: 'Medieval charm and festivals' },
      { id: 35, name: 'Stockholm, Sweden', image: 'https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=600&h=400&fit=crop', description: 'Scandinavian beauty and design' },
      { id: 36, name: 'Copenhagen, Denmark', image: 'https://images.unsplash.com/photo-1513622470522-26c3c8a854bc?w=600&h=400&fit=crop', description: 'Hygge capital of the world' },
      { id: 40, name: 'New Zealand', image: 'https://images.unsplash.com/photo-1507692049790-de58290a4334?w=600&h=400&fit=crop', description: 'Stunning landscapes and adventure sports' },
    ],
  ];

  const [currentSetIndex, setCurrentSetIndex] = useState(0);
  const [direction, setDirection] = useState(1); // 1 for forward, -1 for backward

  // Rotate through different sets of 10 destinations
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSetIndex((prevIndex) => (prevIndex + 1) % destinationSets.length);
    }, 8000); // Rotate every 8 seconds (slower, less distracting)

    return () => clearInterval(interval);
  }, [destinationSets.length]);

  // Get current set of 10 destinations
  const currentDestinations = destinationSets[currentSetIndex];

  // Split to have 5 above and 5 below search bar
  // Layout: Top 5, Middle: SearchBar, Bottom: 5
  const topRow = currentDestinations.slice(0, 5);
  const bottomRow = currentDestinations.slice(5, 10);

  return (
    <div className="hero-banner">
      <div className="destinations-grid-container">
        {/* Top Row - 5 columns */}
        <div className="destination-row-top" key={`top-${currentSetIndex}`}>
          {topRow.map((destination, index) => (
            <div key={`${currentSetIndex}-${destination.id}`} className="destination-card carousel-item">
              <div className="card-image-wrapper">
                <img 
                  src={destination.image} 
                  alt={destination.name}
                  className="card-image"
                  loading="lazy"
                />
                <div className="card-overlay">
                  <h3 className="card-name">{destination.name}</h3>
                  <p className="card-description">{destination.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* SearchBar in center */}
        <div className="search-bar-wrapper">
          <SearchBar />
        </div>

        {/* Bottom Row - 5 columns */}
        <div className="destination-row-bottom" key={`bottom-${currentSetIndex}`}>
          {bottomRow.map((destination, index) => (
            <div key={`${currentSetIndex}-${destination.id}`} className="destination-card carousel-item">
              <div className="card-image-wrapper">
                <img 
                  src={destination.image} 
                  alt={destination.name}
                  className="card-image"
                  loading="lazy"
                />
                <div className="card-overlay">
                  <h3 className="card-name">{destination.name}</h3>
                  <p className="card-description">{destination.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default HeroBanner;