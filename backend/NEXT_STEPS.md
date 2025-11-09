# Next Steps - UI Integration Guide

## ✅ Completed

1. ✅ All AI agents working (StayAgent, RestaurantAgent, TravelAgent, ExperienceAgent, BudgetAgent, PlannerAgent)
2. ✅ Chat API endpoint created (`POST /api/trips/chat`)
3. ✅ Database storage for trip plans
4. ✅ Update functionality (preserves destination and trip details)
5. ✅ Test script verified end-to-end

## 🎯 Next Steps

### 1. Review UI Branch Structure

```bash
# Checkout UI branch to see frontend structure
git fetch origin
git checkout UI_Kartik
# Or view files without switching:
git ls-tree -r --name-only origin/UI_Kartik | grep -E "\.(js|jsx|ts|tsx|html)$"
```

### 2. Backend Setup (Keep Running)

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Important:** The backend must be running for the UI to work.

### 3. UI Integration Points

The UI needs to integrate with these endpoints:

#### A. User Registration
```javascript
POST /api/trips/users/{user_id}/profile
Body: {
  user_id: "user_123",
  name: "John Doe",
  email: "john@example.com",
  phone_number: "+1234567890",
  budget: 3500.0,
  dietary_preferences: ["vegetarian"],
  disability_needs: []
}
```

#### B. Chat Interface - Send Prompt
```javascript
POST /api/trips/chat
Body: {
  prompt: "I want a 5-day nature escape near San Francisco",
  user_id: "user_123"
  // trip_id: optional - only if updating existing trip
}
```

**Response:**
```javascript
{
  trip_id: "uuid-here",
  message: "🎉 Your trip plan is ready! ...",
  trip_plan: {
    accommodations: [...],
    selected_accommodation: {...},
    restaurants: [...],
    transportation: [...],
    experiences: [...],
    itinerary: [...],
    budget: {...}
  },
  status: "new" // or "updated"
}
```

#### C. Retrieve Trip Plan
```javascript
GET /api/trips/chat/{user_id}/{trip_id}
```

### 4. UI Implementation Checklist

- [ ] **User Registration Flow**
  - [ ] Create user profile form
  - [ ] Send profile to `POST /api/trips/users/{user_id}/profile`
  - [ ] Store `user_id` in session/localStorage

- [ ] **Chat Interface**
  - [ ] Text input for user prompts
  - [ ] Send prompt to `POST /api/trips/chat`
  - [ ] Show loading state (takes 2-5 minutes)
  - [ ] Display response message
  - [ ] Display trip plan details

- [ ] **Trip Plan Display**
  - [ ] Show accommodations (with selection option)
  - [ ] Show restaurants
  - [ ] Show transportation options
  - [ ] Show experiences/activities
  - [ ] Show day-by-day itinerary
  - [ ] Show budget breakdown

- [ ] **Update Functionality**
  - [ ] Store `trip_id` from first response
  - [ ] When user sends new prompt, include `trip_id` in request
  - [ ] Update displayed trip plan

- [ ] **Error Handling**
  - [ ] Handle 404 (user not registered)
  - [ ] Handle 500 (server errors)
  - [ ] Show user-friendly error messages

### 5. CORS Configuration

The backend already has CORS enabled for all origins. If you need to restrict it:

```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Your UI ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6. Testing Integration

1. **Start Backend:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn main:app --reload
   ```

2. **Start UI:**
   ```bash
   cd ui  # or wherever your UI code is
   npm start  # or your UI start command
   ```

3. **Test Flow:**
   - Register a user
   - Send a trip planning prompt
   - Wait for response (2-5 minutes)
   - View trip plan
   - Send update prompt
   - Verify trip plan updates

### 7. Environment Variables

Make sure `.env` file has:
```bash
GOOGLE_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### 8. API Base URL

In your UI code, set the API base URL:

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
// or
const API_BASE_URL = 'http://localhost:8000';
```

### 9. Example UI Integration Code

```javascript
// Example: Send chat message
async function sendChatMessage(prompt, userId, tripId = null) {
  const response = await fetch(`${API_BASE_URL}/api/trips/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt: prompt,
      user_id: userId,
      trip_id: tripId  // null for new trip, existing trip_id for updates
    })
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }
  
  return await response.json();
}

// Example: Display trip plan
function displayTripPlan(tripPlan) {
  // Show accommodations
  tripPlan.accommodations.forEach(acc => {
    console.log(`${acc.title} - $${acc.price_per_night}/night`);
  });
  
  // Show restaurants
  tripPlan.restaurants.forEach(rest => {
    console.log(`${rest.name} - ${rest.cuisine_type}`);
  });
  
  // Show itinerary
  tripPlan.itinerary.forEach(day => {
    console.log(`Day ${day.day}: ${day.activities.length} activities`);
  });
  
  // Show budget
  console.log(`Total Budget: $${tripPlan.budget.total}`);
}
```

### 10. Performance Considerations

- **Response Time:** Chat endpoint takes 2-5 minutes (all agents run sequentially)
- **Loading States:** Show progress indicator
- **Timeout:** Set HTTP client timeout to 5-10 minutes
- **Error Handling:** Handle timeout errors gracefully

### 11. Optional Enhancements

- [ ] **Accommodation Selection:** Allow user to select accommodation before restaurants
- [ ] **Streaming Responses:** Show progress as agents complete (advanced)
- [ ] **Trip History:** List all user trips
- [ ] **Export Trip Plan:** PDF/JSON export
- [ ] **Share Trip:** Share trip plan with others

## 📚 Documentation Files

- `CHAT_API_DOCUMENTATION.md` - Complete API documentation
- `TESTING_GUIDE.md` - How to test the API
- `API_DOCUMENTATION.md` - General API docs

## 🐛 Troubleshooting

### Backend not responding?
- Check if server is running: `curl http://localhost:8000/health`
- Check logs for errors
- Verify `.env` file has correct API keys

### CORS errors?
- Backend already allows all origins
- Check browser console for specific error
- Verify API base URL is correct

### 404 errors?
- Make sure user profile is created first
- Check `user_id` matches in all requests

### Timeout errors?
- Increase HTTP client timeout (5-10 minutes)
- Chat endpoint takes time - this is normal

## 🚀 Ready to Integrate!

The backend is fully functional and ready for UI integration. All endpoints are tested and working.

**Key Endpoint:** `POST /api/trips/chat` - This is the main endpoint your UI should use.

