import React from 'react';
import './FeaturedExperiences.css';

const FeaturedExperiences = () => {
  const experiences = [
    {
      id: 1,
      title: 'Weekend Getaways',
      image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop',
      description: 'Perfect short trips'
    },
    {
      id: 2,
      title: 'Family Friendly',
      image: 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=400&h=300&fit=crop',
      description: 'Safe for all ages'
    },
    {
      id: 3,
      title: 'Romantic Escapes',
      image: 'https://images.unsplash.com/photo-1613395877344-13d4a8e0d49e?w=400&h=300&fit=crop',
      description: 'Couples retreats'
    },
    {
      id: 4,
      title: 'Solo Adventures',
      image: 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=400&h=300&fit=crop',
      description: 'Travel alone safely'
    },
  ];

  return (
    <div className="featured-experiences">
      <h2 className="experiences-title">Travel Your Way</h2>
      <div className="experiences-grid">
        {experiences.map((experience) => (
          <div key={experience.id} className="experience-card">
            <div className="experience-image-wrapper">
              <img 
                src={experience.image} 
                alt={experience.title}
                className="experience-image"
                loading="lazy"
              />
              <div className="experience-overlay">
                <h3 className="experience-title">{experience.title}</h3>
                <p className="experience-description">{experience.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FeaturedExperiences;

