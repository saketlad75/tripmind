# TripMind API Documentation

## Overview

TripMind API is designed to work with a UI frontend. All user registration and profile data comes from the UI through API endpoints.

## User Registration Flow

1. **User registers via UI** → UI calls `POST /api/trips/users/{user_id}/profile`
2. **User plans trip via UI** → UI calls `POST /api/trips/plan` with `user_id` and `prompt`
3. **System fetches user profile** → Automatically retrieved using `user_id`

## API Endpoints

### User Profile Management

#### Create/Update User Profile
```http
POST /api/trips/users/{user_id}/profile
Content-Type: application/json

{
  "user_id": "user_123",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone_number": "+1234567890",
  "date_of_birth": "1990-01-01",
  "budget": 2500.0,
  "dietary_preferences": ["vegetarian", "gluten-free"],
  "disability_needs": ["wheelchair accessible"]
}
```

**Response:**
```json
{
  "user_id": "user_123",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "budget": 2500.0,
  "dietary_preferences": ["vegetarian", "gluten-free"],
  "disability_needs": ["wheelchair accessible"],
  "created_at": "2025-01-08T10:00:00",
  "updated_at": "2025-01-08T10:00:00"
}
```

#### Get User Profile
```http
GET /api/trips/users/{user_id}/profile
```

**Response:** UserProfile object

### Trip Planning

#### Plan a Trip
```http
POST /api/trips/plan
Content-Type: application/json

{
  "prompt": "I want a 4-day relaxing beach vacation in Bali with good restaurants nearby",
  "user_id": "user_123",
  "duration_days": 4,
  "travelers": 2,
  "selected_accommodation_id": "acc_123"  // Optional, for restaurant search
}
```

**Note:** 
- Only `prompt` and `user_id` are required
- Location is extracted from the prompt automatically
- Budget comes from user profile
- `selected_accommodation_id` is used for restaurant recommendations

**Response:** TripPlan object with:
- `accommodations`: List of at least 3 accommodations
- `restaurants`: List of at least 3-4 restaurants/cafes (if accommodation selected)
- `selected_accommodation`: Selected accommodation
- `transportation`: Transportation options
- `experiences`: Local experiences
- `itinerary`: Day-by-day itinerary
- `budget`: Budget breakdown

## Data Flow

```
UI Registration
    ↓
POST /api/trips/users/{user_id}/profile
    ↓
User Profile Stored
    ↓
UI Trip Planning
    ↓
POST /api/trips/plan (with prompt + user_id)
    ↓
System fetches user profile automatically
    ↓
StayAgent extracts location from prompt
    ↓
StayAgent uses budget from user profile
    ↓
Returns trip plan
```

## Important Notes

1. **No Hardcoded Data**: All user data comes from UI registration
2. **Profile Required**: User must register before planning trips
3. **Location Extraction**: Location is automatically extracted from the prompt
4. **Budget from Profile**: Budget comes from user profile, not request
5. **Minimum Requirements**:
   - StayAgent: Minimum 3 accommodations
   - RestaurantAgent: Minimum 3-4 restaurants/cafes

## Example UI Integration

### Step 1: User Registration
```javascript
// UI sends registration data
const profile = {
  user_id: "user_123",
  name: "John Doe",
  email: "john@example.com",
  budget: 2500.0,
  dietary_preferences: ["vegetarian"],
  disability_needs: []
};

await fetch('/api/trips/users/user_123/profile', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(profile)
});
```

### Step 2: Trip Planning
```javascript
// UI sends trip request
const tripRequest = {
  prompt: "I want a beach vacation in Bali",
  user_id: "user_123",
  duration_days: 4,
  travelers: 2
};

const plan = await fetch('/api/trips/plan', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(tripRequest)
}).then(r => r.json());
```

## Error Handling

- **404**: User profile not found - user must register first
- **400**: Invalid request data
- **500**: Server error during trip planning

