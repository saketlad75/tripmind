import React from 'react';
import './TrustSection.css';

const TrustSection = () => {
  const features = [
    {
      id: 1,
      icon: '✈️',
      title: 'Flight Booking',
      description: 'Best prices on flights worldwide'
    },
    {
      id: 2,
      icon: '🏨',
      title: 'Hotel Reservations',
      description: 'Verified accommodations'
    },
    {
      id: 3,
      icon: '🏥',
      title: 'Health & Safety',
      description: 'Medical requirements & insurance'
    },
    {
      id: 4,
      icon: '🌤️',
      title: 'Weather Updates',
      description: 'Real-time weather forecasts'
    },
    {
      id: 5,
      icon: '🛍️',
      title: 'Shopping Guide',
      description: 'What to buy before & after'
    },
    {
      id: 6,
      icon: '🤖',
      title: 'AI Powered',
      description: 'Smart personalized planning'
    },
  ];

  return (
    <div className="trust-section">
      <h2 className="trust-title">Everything You Need in One Place</h2>
      <div className="trust-grid">
        {features.map((feature) => (
          <div key={feature.id} className="trust-card">
            <div className="trust-icon">{feature.icon}</div>
            <h3 className="trust-feature-title">{feature.title}</h3>
            <p className="trust-feature-description">{feature.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TrustSection;

