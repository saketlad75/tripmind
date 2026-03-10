/**
 * Backend API base URL (origin only).
 * Set REACT_APP_API_URL in Vercel (or .env) to your deployed backend, e.g. https://your-backend.railway.app
 */
export const API_ORIGIN = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const API_TRIPS = `${API_ORIGIN}/api/trips`;
export const API_TRIP_PLANNER = `${API_ORIGIN}/api/trip-planner`;
