import React from 'react';
import './CategorySection.css';

const CategorySection = () => {
  const categories = [
    {
      id: 1,
      name: 'Beach Getaways',
      icon: '🏖️',
      description: 'Tropical paradises'
    },
    {
      id: 2,
      name: 'City Breaks',
      icon: '🏙️',
      description: 'Urban adventures'
    },
    {
      id: 3,
      name: 'Mountain Escapes',
      icon: '⛰️',
      description: 'Alpine retreats'
    },
    {
      id: 4,
      name: 'Cultural Tours',
      icon: '🏛️',
      description: 'Historic sites'
    },
    {
      id: 5,
      name: 'Adventure Travel',
      icon: '🎒',
      description: 'Thrilling experiences'
    },
    {
      id: 6,
      name: 'Luxury Stays',
      icon: '✨',
      description: 'Premium accommodations'
    },
  ];

  return (
    <div className="category-section">
      <h2 className="category-title">Explore by Category</h2>
      <div className="category-grid">
        {categories.map((category) => (
          <div key={category.id} className="category-card">
            <div className="category-icon">{category.icon}</div>
            <h3 className="category-name">{category.name}</h3>
            <p className="category-description">{category.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CategorySection;

