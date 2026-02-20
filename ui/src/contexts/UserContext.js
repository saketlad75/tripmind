import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'tripmind_user';
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const PROFILE_ENDPOINT = `${API_BASE}/api/trips/users`;

const UserContext = createContext(null);

export function UserProvider({ children }) {
  const [user, setUserState] = useState(null);
  const [loading, setLoading] = useState(true);

  const setUser = useCallback((userData) => {
    setUserState(userData);
    if (userData) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({
          user_id: userData.user_id,
          name: userData.name,
          email: userData.email,
        }));
      } catch (e) {
        console.warn('localStorage set failed', e);
      }
    } else {
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch (e) {}
    }
  }, []);

  const loadStoredUser = useCallback(async () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        setLoading(false);
        return;
      }
      const stored = JSON.parse(raw);
      const userId = stored.user_id;
      if (!userId) {
        setLoading(false);
        return;
      }
      const res = await fetch(`${PROFILE_ENDPOINT}/${encodeURIComponent(userId)}/profile`);
      if (res.ok) {
        const profile = await res.json();
        setUserState(profile);
      } else {
        setUserState(null);
        try {
          localStorage.removeItem(STORAGE_KEY);
        } catch (e) {}
      }
    } catch (e) {
      console.warn('Load stored user failed', e);
      setUserState(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStoredUser();
  }, [loadStoredUser]);

  const register = useCallback(async (profilePayload) => {
    const user_id = profilePayload.user_id || generateUserId();
    const body = {
      user_id,
      name: profilePayload.name,
      email: profilePayload.email,
      phone_number: profilePayload.phone_number || null,
      date_of_birth: profilePayload.date_of_birth || null,
      budget: profilePayload.budget != null && profilePayload.budget !== '' ? Number(profilePayload.budget) : null,
      dietary_preferences: Array.isArray(profilePayload.dietary_preferences)
        ? profilePayload.dietary_preferences
        : (profilePayload.dietary_preferences || '').split(',').map((s) => s.trim()).filter(Boolean),
      disability_needs: Array.isArray(profilePayload.disability_needs)
        ? profilePayload.disability_needs
        : (profilePayload.disability_needs || '').split(',').map((s) => s.trim()).filter(Boolean),
    };
    const res = await fetch(`${PROFILE_ENDPOINT}/${encodeURIComponent(user_id)}/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Registration failed');
    }
    const profile = await res.json();
    setUser(profile);
    return profile;
  }, [setUser]);

  const logout = useCallback(() => {
    setUserState(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {}
  }, []);

  const value = {
    user,
    loading,
    setUser,
    register,
    logout,
    loadStoredUser,
    user_id: user ? user.user_id : null,
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

function generateUserId() {
  return 'user_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8);
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) {
    throw new Error('useUser must be used within UserProvider');
  }
  return ctx;
}
