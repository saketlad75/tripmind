import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { useLanguage, languages } from '../contexts/LanguageContext';
import './Header.css';

const Header = () => {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  const [isLanguageDropdownOpen, setIsLanguageDropdownOpen] = useState(false);
  const languageDropdownRef = useRef(null);

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

  const handleMyTripClick = (e) => {
    e.preventDefault();
    navigate('/trips');
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (languageDropdownRef.current && !languageDropdownRef.current.contains(event.target)) {
        setIsLanguageDropdownOpen(false);
      }
    };

    if (isLanguageDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isLanguageDropdownOpen]);

  const handleLanguageSelect = (langCode) => {
    setLanguage(langCode);
    setIsLanguageDropdownOpen(false);
  };

  return (
    <header className="header">
      <div className="header-container">
        {/* Left Side - Logo */}
        <div 
          className="logo-container"
          onClick={() => navigate('/')}
          style={{ cursor: 'pointer' }}
        >
          <div className="logo">
            <div className="logo-image">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z" fill="#FF385C"/>
              </svg>
            </div>
          </div>
          <span className="logo-text">TripMIND</span>
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
            <span className="nav-text">{t('experiences')}</span>
            <span className="nav-badge">NEW</span>
          </a>
          <a 
            href="/trips" 
            className="nav-link"
            onClick={handleMyTripClick}
          >
            <span className="nav-icon">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M2 4H18V16H2V4Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M14 4V2M6 4V2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                <path d="M2 8H18" stroke="currentColor" strokeWidth="1.5"/>
                <circle cx="6" cy="12" r="1" fill="currentColor"/>
                <circle cx="10" cy="12" r="1" fill="currentColor"/>
                <circle cx="14" cy="12" r="1" fill="currentColor"/>
              </svg>
            </span>
            <span className="nav-text">{t('myItineraries')}</span>
          </a>
        </nav>

        {/* Right Side */}
        <div className="header-right">
          <a href="#host" className="become-host-link">{t('becomeHost')}</a>
          
          <button 
            className="icon-button theme-toggle" 
            title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
            onClick={toggleTheme}
          >
            {theme === 'light' ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            )}
          </button>

          <div className="language-dropdown-container" ref={languageDropdownRef}>
            <button 
              className="icon-button language-button" 
              title="Language"
              onClick={() => setIsLanguageDropdownOpen(!isLanguageDropdownOpen)}
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.5"/>
                <path d="M9 2C10 4 11 6 11 9C11 12 10 14 9 16M9 2C8 4 7 6 7 9C7 12 8 14 9 16" stroke="currentColor" strokeWidth="1.5"/>
                <path d="M2 9H16" stroke="currentColor" strokeWidth="1.5"/>
              </svg>
            </button>
            {isLanguageDropdownOpen && (
              <div className="language-dropdown">
                {Object.values(languages).map((lang) => (
                  <button
                    key={lang.code}
                    className={`language-option ${language === lang.code ? 'active' : ''}`}
                    onClick={() => handleLanguageSelect(lang.code)}
                  >
                    <span className="language-flag">{lang.flag}</span>
                    <span className="language-name">{lang.name}</span>
                    {language === lang.code && (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="check-icon">
                        <path d="M20 6L9 17L4 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          <button className="icon-button user-menu" title="User Menu">
            <span className="user-greeting">{t('hiKartik')}</span>
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