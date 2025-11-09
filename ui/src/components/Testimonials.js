import React from 'react';
import './Testimonials.css';

const Testimonials = () => {
  const testimonials = [
    {
      id: 1,
      name: 'Sarah Johnson',
      location: 'New York, USA',
      rating: 5,
      text: 'Phoenix Travel made planning my European tour effortless. Everything from flights to shopping recommendations was spot on!',
      avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop'
    },
    {
      id: 2,
      name: 'Michael Chen',
      location: 'Singapore',
      rating: 5,
      text: 'The AI planner understood my medical needs and created a perfect itinerary. Highly recommend!',
      avatar: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=100&h=100&fit=crop&crop=faces'
    },
    {
      id: 3,
      name: 'Emma Williams',
      location: 'London, UK',
      rating: 5,
      text: 'Best travel planning platform I\'ve used. The personalized recommendations were exactly what I needed.',
      avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop'
    },
  ];

  return (
    <div id="testimonials" className="testimonials-section">
      <h2 className="testimonials-title">What Travelers Say</h2>
      <div className="testimonials-grid">
        {testimonials.map((testimonial) => (
          <div key={testimonial.id} className="testimonial-card">
            <div className="testimonial-header">
              <img 
                src={testimonial.avatar} 
                alt={testimonial.name}
                className="testimonial-avatar"
              />
              <div className="testimonial-info">
                <h3 className="testimonial-name">{testimonial.name}</h3>
                <p className="testimonial-location">{testimonial.location}</p>
              </div>
            </div>
            <div className="testimonial-rating">
              {'★'.repeat(testimonial.rating)}
            </div>
            <p className="testimonial-text">"{testimonial.text}"</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Testimonials;

