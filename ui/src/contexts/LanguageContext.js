import React, { createContext, useContext, useState, useEffect } from 'react';

const LanguageContext = createContext();

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

export const languages = {
  'en-US': { code: 'en-US', name: 'English (US)', flag: '🇺🇸' },
  'es-ES': { code: 'es-ES', name: 'Español', flag: '🇪🇸' },
  'fr-FR': { code: 'fr-FR', name: 'Français', flag: '🇫🇷' },
};

export const translations = {
  'en-US': {
    experiences: 'Experiences',
    myItineraries: 'My Itineraries',
    becomeHost: 'Become a host',
    hiKartik: 'Hi Kartik',
    hiName: 'Hi {name}',
    signIn: 'Sign in',
    aiPlannerTitle: 'Your Smart Trip Planner ✈️',
    aiPlannerSubtitle: 'Travel smarter with AI that plans it all — flights, hotels, health, and weather, personalized just for you. One platform, every detail, zero hassle.',
    searchPlaceholder: 'Describe your travel plans in detail...',
    searchHint: '💡 Tip: The more details you provide, the better your personalized itinerary will be. Include dates, preferences, medical needs, budget, and any special requirements.',
  },
  'es-ES': {
    experiences: 'Experiencias',
    myItineraries: 'Mis Itinerarios',
    becomeHost: 'Ser anfitrión',
    hiKartik: 'Hola Kartik',
    hiName: 'Hola {name}',
    signIn: 'Iniciar sesión',
    aiPlannerTitle: 'Tu Planificador de Viajes Inteligente ✈️',
    aiPlannerSubtitle: 'Viaja más inteligente con IA que planifica todo: vuelos, hoteles, salud y clima, personalizado solo para ti. Una plataforma, cada detalle, cero complicaciones.',
    searchPlaceholder: 'Describe tus planes de viaje en detalle...',
    searchHint: '💡 Consejo: Cuantos más detalles proporciones, mejor será tu itinerario personalizado. Incluye fechas, preferencias, necesidades médicas, presupuesto y cualquier requisito especial.',
  },
  'fr-FR': {
    experiences: 'Expériences',
    myItineraries: 'Mes Itinéraires',
    becomeHost: 'Devenir hôte',
    hiKartik: 'Salut Kartik',
    hiName: 'Salut {name}',
    signIn: 'Connexion',
    aiPlannerTitle: 'Votre Planificateur de Voyage Intelligent ✈️',
    aiPlannerSubtitle: 'Voyagez plus intelligemment avec une IA qui planifie tout — vols, hôtels, santé et météo, personnalisé juste pour vous. Une plateforme, chaque détail, zéro tracas.',
    searchPlaceholder: 'Décrivez vos projets de voyage en détail...',
    searchHint: '💡 Astuce: Plus vous fournissez de détails, meilleur sera votre itinéraire personnalisé. Incluez les dates, préférences, besoins médicaux, budget et toute exigence spéciale.',
  },
};

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    const savedLanguage = localStorage.getItem('language');
    return savedLanguage || 'en-US';
  });

  useEffect(() => {
    localStorage.setItem('language', language);
  }, [language]);

  const t = (key) => {
    return translations[language]?.[key] || translations['en-US'][key] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, languages }}>
      {children}
    </LanguageContext.Provider>
  );
};

