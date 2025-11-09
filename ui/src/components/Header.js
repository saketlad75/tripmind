import React from 'react';
import './Header.css';

const Header = () => {
  const handleExperiencesClick = (e) => {
    e.preventDefault();
    const testimonials = document.getElementById('testimonials');
    if (testimonials) {
      const header = document.querySelector('.header');
      const headerHeight = header ? header.offsetHeight : 80;
      const elementPosition = testimonials.getBoundingClientRect().top + window.pageYOffset;
      const offsetPosition = elementPosition - headerHeight - 20;
      
      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      });
    }
  };

  return (
    <header className="header">
      <div className="header-container">
        {/* Left Side - Logo */}
        <div className="logo-container">
          <div className="logo">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M16 2L4 10V28L16 20L28 28V10L16 2Z" fill="#FF385C"/>
              <path d="M16 2L4 10V28L16 20L28 28V10L16 2Z" stroke="#FF385C" strokeWidth="1.5" strokeLinejoin="round"/>
            </svg>
          </div>
          <span className="logo-text">Phoenix Travel</span>
        </div>

        {/* Center Navigation */}
        <nav className="header-nav">
          <a 
            href="#testimonials" 
            className="nav-link"
            onClick={handleExperiencesClick}
          >
            <span className="nav-icon">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M10 2C8 2 6 3 6 5C6 7 8 8 10 8C12 8 14 7 14 5C14 3 12 2 10 2Z" fill="#FF385C"/>
                <path d="M10 2C8 2 6 3 6 5C6 7 8 8 10 8C12 8 14 7 14 5C14 3 12 2 10 2Z" stroke="#FF385C" strokeWidth="1.5"/>
                <ellipse cx="10" cy="12" rx="6" ry="6" fill="#FF6B35" opacity="0.8"/>
                <path d="M4 12C4 8 6.5 5 10 5C13.5 5 16 8 16 12" stroke="#FF6B35" strokeWidth="1.5" strokeLinecap="round"/>
                <path d="M10 2L10 8" stroke="#FF385C" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </span>
            <span className="nav-text">Experiences</span>
            <span className="nav-badge">NEW</span>
          </a>
        </nav>

        {/* Right Side */}
        <div className="header-right">
          <a href="#host" className="become-host-link">Become a host</a>
          
          <button className="icon-button" title="Language & Currency">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M9 2C10 4 11 6 11 9C11 12 10 14 9 16M9 2C8 4 7 6 7 9C7 12 8 14 9 16" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M2 9H16" stroke="currentColor" strokeWidth="1.5"/>
            </svg>
          </button>

          <button className="icon-button user-menu" title="User Menu">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" className="menu-icon">
              <rect x="1" y="3.5" width="14" height="1.5" rx="0.75" fill="currentColor"/>
              <rect x="1" y="7.25" width="14" height="1.5" rx="0.75" fill="currentColor"/>
              <rect x="1" y="11" width="14" height="1.5" rx="0.75" fill="currentColor"/>
            </svg>
            <svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg" className="user-avatar">
              <circle cx="15" cy="15" r="14" fill="#717171" stroke="white" strokeWidth="2"/>
              <circle cx="15" cy="12" r="3.5" fill="white"/>
              <path d="M7 24C7 20 10.5 17 15 17C19.5 17 23 20 23 24" stroke="white" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;