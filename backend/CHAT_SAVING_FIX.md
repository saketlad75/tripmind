# Chat History Saving - Fix Summary

## Issue
Chat history was not being saved because the frontend was calling the wrong API endpoint.

## Root Cause
The frontend was using:
- `API_ENDPOINT = 'http://localhost:8000/api/trips'`
- Then calling: `${API_ENDPOINT}/trips/${tripId}/messages`
- This resulted in: `http://localhost:8000/api/trips/trips/${tripId}/messages` ❌ (double "trips")

But the backend endpoint is at:
- `/api/trip-planner/trips/{tripId}/messages` ✅

## Fix Applied

### 1. Frontend Changes (`ui/src/pages/TripChat.js`)

Added a separate endpoint constant for chat API:
```javascript
const CHAT_API_ENDPOINT = process.env.REACT_APP_CHAT_API_URL || 'http://localhost:8000/api/trip-planner';
```

Updated all chat-related API calls to use `CHAT_API_ENDPOINT`:
- ✅ `saveMessageToBackend()` - Now uses `${CHAT_API_ENDPOINT}/trips/${tripId}/messages`
- ✅ `get_messages()` - Now uses `${CHAT_API_ENDPOINT}/trips/${tripId}/messages`
- ✅ `handleInviteUser()` - Now uses `${CHAT_API_ENDPOINT}/trips/${tripId}/invite`
- ✅ `fetchSharedUsers()` - Now uses `${CHAT_API_ENDPOINT}/trips/${tripId}/shared-users`

### 2. Backend Verification

The backend was already correctly saving messages:
- ✅ `/api/trips/chat` endpoint saves user prompt + AI response to database
- ✅ `/api/trip-planner/trips/{tripId}/messages` endpoint saves individual messages
- ✅ Database table `chat_messages` exists and is working

## How It Works Now

### Automatic Saving (via `/api/trips/chat`)
When you send a prompt to plan a trip:
1. User prompt is saved to `chat_messages` table
2. AI response (with trip plan) is saved to `chat_messages` table
3. Both messages are linked to the `trip_id`

### Manual Saving (via `/api/trip-planner/trips/{tripId}/messages`)
When the frontend calls `saveMessageToBackend()`:
1. Message is sent to the correct endpoint
2. Backend verifies user has access to the trip
3. Message is saved to `chat_messages` table
4. Success response is returned

### Loading Chat History
When opening a trip:
1. Frontend calls `${CHAT_API_ENDPOINT}/trips/${tripId}/messages?userId=Kartik7`
2. Backend checks user access
3. Returns all messages for that trip, ordered by timestamp
4. Frontend displays the full conversation history

## Testing

To verify chat history is being saved:

1. **Check database directly:**
```bash
cd backend
source venv/bin/activate
python -c "
from database.db import get_db_connection
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) as count FROM chat_messages')
print('Total messages:', cursor.fetchone()['count'])
cursor.execute('SELECT trip_id, user_id, role, substr(content, 1, 50) as preview FROM chat_messages ORDER BY timestamp DESC LIMIT 5')
for row in cursor.fetchall():
    print(f\"{row['trip_id']} | {row['user_id']} | {row['role']} | {row['preview']}...\")
conn.close()
"
```

2. **Check browser console:**
   - Open browser DevTools (F12)
   - Look for: `✅ Message saved to backend:` messages
   - Look for: `✅ Loaded X messages from database` when opening a trip

3. **Test the API directly:**
```bash
# Save a message
curl -X POST "http://localhost:8000/api/trip-planner/trips/YOUR_TRIP_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "Kartik7",
    "tripId": "YOUR_TRIP_ID",
    "message": {
      "id": 123,
      "role": "user",
      "content": "Test message",
      "timestamp": "2024-01-15T10:00:00"
    },
    "timestamp": "2024-01-15T10:00:00"
  }'

# Get messages
curl "http://localhost:8000/api/trip-planner/trips/YOUR_TRIP_ID/messages?userId=Kartik7"
```

## Status

✅ **FIXED** - Chat history is now being saved correctly!

- Messages are saved when you send prompts via `/api/trips/chat`
- Messages are saved when frontend calls `saveMessageToBackend()`
- Chat history loads correctly when opening a trip
- All shared users can view the full conversation

