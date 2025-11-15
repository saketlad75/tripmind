# Chat API Documentation

## Overview

The Chat API endpoint (`/api/trips/chat`) is designed for UI chat interfaces. It accepts natural language prompts from users, runs all AI agents to generate a complete trip plan, and returns the results in a chat-friendly format.

## Endpoints

### 1. Create/Update Trip Plan via Chat

**Endpoint:** `POST /api/trips/chat`

**Description:** 
- Accepts a natural language prompt from the user
- Runs all AI agents (StayAgent, RestaurantAgent, TravelAgent, ExperienceAgent, BudgetAgent, PlannerAgent)
- Generates a complete trip plan
- Stores the plan in the database
- Returns the plan in a chat-friendly format

**Request Body:**
```json
{
  "prompt": "I want a 5-day quiet nature escape with good Wi-Fi, hiking trails, and local food near San Francisco, California. I'll be traveling from New York.",
  "user_id": "user_123",
  "trip_id": "optional-trip-id",  // If provided, updates existing trip plan
  "selected_accommodation_id": "optional-acc-id"  // If user selected an accommodation
}
```

**Response:**
```json
{
  "trip_id": "uuid-generated-or-provided",
  "message": "🎉 Your trip plan is ready! ...",
  "trip_plan": {
    "request": {...},
    "accommodations": [...],
    "selected_accommodation": {...},
    "restaurants": [...],
    "transportation": [...],
    "experiences": [...],
    "itinerary": [...],
    "budget": {...},
    "map_data": {...},
    "trip_id": "uuid",
    "status": "draft"
  },
  "status": "new"  // or "updated" if trip_id was provided
}
```

**Usage:**
- **New Trip:** Don't provide `trip_id` - a new UUID will be generated
- **Update Trip:** Provide `trip_id` - the existing trip plan will be updated

### 2. Get Trip Plan

**Endpoint:** `GET /api/trips/chat/{user_id}/{trip_id}`

**Description:** Retrieves a trip plan by user_id and trip_id

**Response:** Complete TripPlan object

### 3. User Profile Management

**Create/Update Profile:** `POST /api/trips/users/{user_id}/profile`

**Get Profile:** `GET /api/trips/users/{user_id}/profile`

## Complete Flow Example

### Step 1: User Registration
```javascript
// UI sends user registration
const profile = {
  user_id: "user_123",
  name: "John Doe",
  email: "john@example.com",
  phone_number: "+1234567890",
  budget: 3500.0,
  dietary_preferences: ["vegetarian"],
  disability_needs: []
};

await fetch('/api/trips/users/user_123/profile', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(profile)
});
```

### Step 2: User Sends First Prompt (Create New Trip)
```javascript
// UI chat interface - user enters prompt
const chatRequest = {
  prompt: "I want a 5-day quiet nature escape with good Wi-Fi, hiking trails, and local food near San Francisco, California. I'll be traveling from New York.",
  user_id: "user_123"
  // No trip_id - creates new trip
};

const response = await fetch('/api/trips/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(chatRequest)
});

const result = await response.json();
// result.trip_id - save this for future updates
// result.trip_plan - display in chat interface
// result.message - show to user
```

### Step 3: User Updates Trip Plan
```javascript
// User enters new prompt to update the trip
const updateRequest = {
  prompt: "Actually, I want to add more hiking activities and prefer budget-friendly restaurants.",
  user_id: "user_123",
  trip_id: result.trip_id  // Use trip_id from previous response
};

const updateResponse = await fetch('/api/trips/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(updateRequest)
});

const updatedResult = await updateResponse.json();
// updatedResult.trip_plan - updated plan
// updatedResult.status - "updated"
```

### Step 4: Retrieve Trip Plan Later
```javascript
// Get trip plan by trip_id
const planResponse = await fetch(`/api/trips/chat/${user_id}/${trip_id}`);
const tripPlan = await planResponse.json();
```

## Chat Interface Integration

### Displaying Results

The `trip_plan` object contains all the information needed for the UI:

1. **Accommodations:** `trip_plan.accommodations` - List of available accommodations
2. **Selected Accommodation:** `trip_plan.selected_accommodation` - Currently selected accommodation
3. **Restaurants:** `trip_plan.restaurants` - Recommended restaurants/cafes
4. **Transportation:** `trip_plan.transportation` - Flight/train/bus options
5. **Experiences:** `trip_plan.experiences` - Activities and experiences
6. **Itinerary:** `trip_plan.itinerary` - Day-by-day itinerary
7. **Budget:** `trip_plan.budget` - Budget breakdown

### Chat Message Format

The `message` field provides a summary that can be displayed in the chat:

```
🎉 Your trip plan is ready! 

🏨 **Accommodation:** Farmhouse Inn
🍽️ **Restaurants:** 4 recommendations
✈️ **Transportation:** 5 options
🎯 **Experiences:** 5 activities
💰 **Total Budget:** $6586.25
📅 **Itinerary:** 5 days planned
```

## Error Handling

- **404:** User profile not found - user must register first
- **503:** Orchestrator not initialized - backend not ready
- **500:** Server error during trip planning

## Notes

1. **Processing Time:** The chat endpoint may take 2-5 minutes to process as it runs all AI agents sequentially
2. **Trip ID:** Always save the `trip_id` from the first response to enable updates
3. **User Profile:** User must be registered before planning trips
4. **Updates:** When updating a trip, the system creates a new version in the database

## Testing

Run the test script to verify the chat API:

```bash
cd backend
python test_chat_api.py
```

Make sure the backend server is running:
```bash
cd backend
uvicorn main:app --reload
```

