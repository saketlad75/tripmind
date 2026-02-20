import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useUser } from '../contexts/UserContext';
import './Register.css';

const DIET_OPTIONS = ['vegetarian', 'vegan', 'gluten-free', 'halal', 'kosher', 'none'];
const ACCESSIBILITY_OPTIONS = ['wheelchair accessible', 'hearing impaired', 'visual assistance', 'none'];

const Register = () => {
  const navigate = useNavigate();
  const { register, user } = useUser();
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone_number: '',
    date_of_birth: '',
    budget: '',
    dietary_preferences: [],
    disability_needs: [],
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleDietChange = (option) => {
    setForm((prev) => {
      const next = option === 'none' ? [] : prev.dietary_preferences.filter((d) => d !== 'none');
      if (option === 'none') return { ...prev, dietary_preferences: [] };
      const has = next.includes(option);
      return {
        ...prev,
        dietary_preferences: has ? next.filter((d) => d !== option) : [...next, option],
      };
    });
  };

  const handleAccessibilityChange = (option) => {
    setForm((prev) => {
      const next = option === 'none' ? [] : prev.disability_needs.filter((d) => d !== 'none');
      if (option === 'none') return { ...prev, disability_needs: [] };
      const has = next.includes(option);
      return {
        ...prev,
        disability_needs: has ? next.filter((d) => d !== option) : [...next, option],
      };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!form.name.trim() || !form.email.trim()) {
      setError('Name and email are required.');
      return;
    }
    setSubmitting(true);
    try {
      await register({
        name: form.name.trim(),
        email: form.email.trim(),
        phone_number: form.phone_number.trim() || null,
        date_of_birth: form.date_of_birth || null,
        budget: form.budget ? parseFloat(form.budget) : null,
        dietary_preferences: form.dietary_preferences.length ? form.dietary_preferences : [],
        disability_needs: form.disability_needs.length ? form.disability_needs : [],
      });
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (user) {
    navigate('/', { replace: true });
    return null;
  }

  return (
    <div className="register-page">
      <div className="register-card">
        <h1>Create your profile</h1>
        <p className="register-subtitle">
          Set up your preferences so we can plan better trips for you.
        </p>
        <form onSubmit={handleSubmit} className="register-form">
          {error && <div className="register-error">{error}</div>}
          <label>
            Name <span className="required">*</span>
          </label>
          <input
            type="text"
            name="name"
            value={form.name}
            onChange={handleChange}
            placeholder="Your name"
            required
          />
          <label>
            Email <span className="required">*</span>
          </label>
          <input
            type="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            placeholder="you@example.com"
            required
          />
          <label>Phone</label>
          <input
            type="tel"
            name="phone_number"
            value={form.phone_number}
            onChange={handleChange}
            placeholder="+1 234 567 8900"
          />
          <label>Date of birth</label>
          <input
            type="date"
            name="date_of_birth"
            value={form.date_of_birth}
            onChange={handleChange}
          />
          <label>Default trip budget (USD)</label>
          <input
            type="number"
            name="budget"
            value={form.budget}
            onChange={handleChange}
            placeholder="e.g. 2500"
            min="0"
            step="100"
          />
          <label>Dietary preferences</label>
          <div className="register-chips">
            {DIET_OPTIONS.map((opt) => (
              <button
                key={opt}
                type="button"
                className={`chip ${form.dietary_preferences.includes(opt) ? 'active' : ''}`}
                onClick={() => handleDietChange(opt)}
              >
                {opt}
              </button>
            ))}
          </div>
          <label>Accessibility needs</label>
          <div className="register-chips">
            {ACCESSIBILITY_OPTIONS.map((opt) => (
              <button
                key={opt}
                type="button"
                className={`chip ${form.disability_needs.includes(opt) ? 'active' : ''}`}
                onClick={() => handleAccessibilityChange(opt)}
              >
                {opt}
              </button>
            ))}
          </div>
          <button type="submit" className="register-submit" disabled={submitting}>
            {submitting ? 'Saving…' : 'Save profile & continue'}
          </button>
        </form>
        <p className="register-login">
          Already have a profile? <Link to="/">Go home</Link> and we’ll load it from this device.
        </p>
      </div>
    </div>
  );
};

export default Register;
