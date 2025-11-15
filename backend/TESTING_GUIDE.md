# Testing Guide - Chat API

## Quick Start Testing

### Step 1: Start the Backend Server

Open a terminal and navigate to the backend directory:

```bash
cd /Volumes/Seagate/Masters/Projects/Airbnb/backend
source venv/bin/activate  # Activate virtual environment
uvicorn main:app --reload
```

The server will start on `http://localhost:8000`

### Step 2: Run the Test Script

Open a **new terminal** (keep the server running) and run:

```bash
cd /Volumes/Seagate/Masters/Projects/Airbnb/backend
source venv/bin/activate
python test_chat_api.py
```

This will:
1. Create a user profile
2. Send a chat message to create a new trip
3. Retrieve the trip plan
4. Update the trip plan with a new prompt

## Manual Testing with curl

### 1. Create User Profile

```bash
curl -X POST "http://localhost:8000/api/trips/users/test_user_001/profile" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "name": "Test User",
    "email": "test@example.com",
    "phone_number": "+1234567890",
    "budget": 3500.0,
    "dietary_preferences": ["vegetarian"],
    "disability_needs": []
  }'
```

### 2. Send Chat Message (Create New Trip)

```bash
curl -X POST "http://localhost:8000/api/trips/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "I want a 5-day quiet nature escape with good Wi-Fi, hiking trails, and local food near San Francisco, California. I will be traveling from New York.",
    "user_id": "test_user_001"
  }'
```

**Note:** This will take 2-5 minutes as it runs all AI agents.

### 3. Get Trip Plan

Replace `TRIP_ID` with the trip_id from step 2:

```bash
curl "http://localhost:8000/api/trips/chat/test_user_001/TRIP_ID"
```

### 4. Update Trip Plan

Replace `TRIP_ID` with the trip_id from step 2:

```bash
curl -X POST "http://localhost:8000/api/trips/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Actually, I want to add more hiking activities and prefer budget-friendly restaurants.",
    "user_id": "test_user_001",
    "trip_id": "TRIP_ID"
  }'
```

## Testing with Python Script

The `test_chat_api.py` script automates all the above steps:

```bash
cd backend
source venv/bin/activate
python test_chat_api.py
```

## Testing with Postman/Thunder Client

### 1. Create User Profile
- **Method:** POST
- **URL:** `http://localhost:8000/api/trips/users/test_user_001/profile`
- **Body (JSON):**
```json
{
  "user_id": "test_user_001",
  "name": "Test User",
  "email": "test@example.com",
  "phone_number": "+1234567890",
  "budget": 3500.0,
  "dietary_preferences": ["vegetarian"],
  "disability_needs": []
}
```

### 2. Send Chat Message
- **Method:** POST
- **URL:** `http://localhost:8000/api/trips/chat`
- **Body (JSON):**
```json
{
  "prompt": "I want a 5-day quiet nature escape with good Wi-Fi, hiking trails, and local food near San Francisco, California. I will be traveling from New York.",
  "user_id": "test_user_001"
}
```

### 3. Get Trip Plan
- **Method:** GET
- **URL:** `http://localhost:8000/api/trips/chat/test_user_001/{trip_id}`

## Expected Response Format

### Chat Response:
```json
{
  "trip_id": "uuid-here",
  "message": "🎉 Your trip plan is ready! ...",
  "trip_plan": {
    "accommodations": [...],
    "selected_accommodation": {...},
    "restaurants": [...],
    "transportation": [...],
    "experiences": [...],
    "itinerary": [...],
    "budget": {...}
  },
  "status": "new"
}
```

## Troubleshooting

### Server not starting?
- Make sure you're in the backend directory
- Activate virtual environment: `source venv/bin/activate`
- Check if port 8000 is available
- Check `.env` file has `GOOGLE_API_KEY` set

### API returns 404?
- Make sure user profile is created first
- Check user_id matches in all requests

### API returns 503?
- Orchestrator not initialized - check API keys in `.env`
- Make sure `GOOGLE_API_KEY` is set

### API takes too long?
- Normal! The chat endpoint runs all 6 agents sequentially
- Expect 2-5 minutes for complete trip planning
- This is expected behavior

## Quick Test Command

Run this one-liner to test everything:

```bash
cd backend && source venv/bin/activate && python test_chat_api.py
```

Make sure the server is running in another terminal first!

