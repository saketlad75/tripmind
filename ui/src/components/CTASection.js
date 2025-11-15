import React from 'react';
import './CTASection.css';

const CTASection = () => {
  const handleScrollToSearch = () => {
    const searchBar = document.getElementById('search-bar');
    if (searchBar) {
      // Get header height to account for sticky positioning
      const header = document.querySelector('.header');
      const headerHeight = header ? header.offsetHeight : 80;
      
      // Calculate position with offset for sticky header
      const elementPosition = searchBar.getBoundingClientRect().top + window.pageYOffset;
      const offsetPosition = elementPosition - headerHeight - 20; // 20px extra padding
      
      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      });
      
      // Small delay to ensure smooth scroll, then focus the textarea
      setTimeout(() => {
        const textarea = searchBar.querySelector('textarea');
        if (textarea) {
          textarea.focus();
        }
      }, 600);
    }
  };

  return (
    <div className="cta-section">
      <div className="cta-content">
        <h2 className="cta-title">Ready to Plan Your Next Adventure?</h2>
        <p className="cta-description">
          Let our AI-powered platform handle all the details. From booking flights to finding the perfect accommodations, we've got you covered.
        </p>
        <button className="cta-button" onClick={handleScrollToSearch}>Start Planning Now</button>
      </div>
    </div>
  );
};

export default CTASection;

