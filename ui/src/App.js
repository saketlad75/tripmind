import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { LanguageProvider } from './contexts/LanguageContext';
import Header from './components/Header';
import Footer from './components/Footer';
import HeroBanner from './components/HeroBanner';
import CategorySection from './components/CategorySection';
import TrustSection from './components/TrustSection';
import FeaturedExperiences from './components/FeaturedExperiences';
import Testimonials from './components/Testimonials';
import CTASection from './components/CTASection';
import MyTripsListing from './pages/MyTripsListing';
import TripChat from './pages/TripChat';
import './App.css';

function HomePage() {
  return (
    <>
      <section id="destinations">
        <HeroBanner />
      </section>
      <TrustSection />
      <CategorySection />
      <section id="experiences">
        <FeaturedExperiences />
      </section>
      <Testimonials />
      <CTASection />
    </>
  );
}

function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <Router>
          <div className="App">
            <Header />
            <main className="main-content">
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/trips" element={<MyTripsListing />} />
                <Route path="/trips/:tripId/chat" element={<TripChat />} />
              </Routes>
            </main>
            <Footer />
          </div>
        </Router>
      </LanguageProvider>
    </ThemeProvider>
  );
}

export default App;