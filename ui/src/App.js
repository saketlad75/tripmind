import React from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import HeroBanner from './components/HeroBanner';
import CategorySection from './components/CategorySection';
import TrustSection from './components/TrustSection';
import FeaturedExperiences from './components/FeaturedExperiences';
import Testimonials from './components/Testimonials';
import CTASection from './components/CTASection';
import './App.css';

function App() {
  return (
    <div className="App">
      <Header />
      <main className="main-content">
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
      </main>
      <Footer />
    </div>
  );
}

export default App;