# UI Integration Guide - Connecting to Backend Chat API

## Current Status

✅ **Backend Ready:**
- Chat API endpoint: `POST /api/trips/chat`
- All agents working
- Database storage functional
- Tested end-to-end

✅ **UI Structure:**
- React app with SearchBar component
- Already has API integration code
- Needs to be updated to use new chat endpoint

## Required Changes

### 1. Update SearchBar.js

**Current API endpoint:** `http://localhost:8000/api/trip-planner`  
**New endpoint:** `http://localhost:8000/api/trips/chat`

**Required changes:**
1. Update API endpoint URL
2. Add `user_id` to request (get from localStorage or user registration)
3. Handle new response format (trip_plan object)
4. Display trip plan results
5. Store `trip_id` for updates
6. Add user registration flow

### 2. Create User Registration Component

Users must register before planning trips. Create a registration form that calls:
```
POST /api/trips/users/{user_id}/profile
```

### 3. Create Trip Plan Display Component

Display the trip plan results:
- Accommodations (with selection)
- Restaurants
- Transportation
- Experiences
- Day-by-day itinerary
- Budget breakdown

## Implementation Steps

### Step 1: Update SearchBar.js

Replace the API endpoint and request format:

```javascript
// Update API endpoint
const API_ENDPOINT = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/trips/chat';

// Get user_id from localStorage (set after registration)
const userId = localStorage.getItem('userId') || 'default_user';

// Update request format
const requestData = {
  prompt: prompt.trim(),
  user_id: userId,
  trip_id: localStorage.getItem('currentTripId') || null  // For updates
};

// Update response handling
const data = await response.json();
// data.trip_id - save this
// data.trip_plan - display this
// data.message - show to user
```

### Step 2: Add User Registration

Create a registration component or modal that collects:
- Name
- Email
- Phone number
- Budget
- Dietary preferences
- Disability needs

Then call:
```javascript
POST /api/trips/users/{user_id}/profile
```

### Step 3: Display Trip Plan

Create a component to display:
- `trip_plan.accommodations` - List with selection
- `trip_plan.restaurants` - List of restaurants
- `trip_plan.transportation` - Flight/train options
- `trip_plan.experiences` - Activities
- `trip_plan.itinerary` - Day-by-day plan
- `trip_plan.budget` - Budget breakdown

## Example Updated SearchBar.js

See the updated file in the next step.

## Testing

1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start UI: `cd ui && npm start`
3. Register a user first
4. Send a trip planning prompt
5. View trip plan results
6. Send update prompt

