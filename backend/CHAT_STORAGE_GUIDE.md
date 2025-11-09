# Chat Storage and Sharing Guide

## Overview

TripMind now saves all chat conversations to the database, allowing you to:
1. **Save entire chat history** - All messages are permanently stored
2. **Invite friends** - Share trips with friends who can view and edit
3. **Collaborative planning** - Multiple users can contribute to the same trip

## How It Works

### Database Tables

1. **`chat_messages`** - Stores all chat messages for each trip
   - Includes user prompts and AI responses
   - Stores trip plans with assistant messages
   - Preserves full conversation history

2. **`shared_trips`** - Tracks which users have access to which trips
   - Owner automatically has access
   - Invited users can view and edit
   - Tracks invitation status

### Features

#### 1. Automatic Chat Saving

When you send a prompt to plan a trip:
- Your prompt is saved as a user message
- The AI's response (with trip plan) is saved as an assistant message
- All messages are stored in chronological order

#### 2. Inviting Friends

**To invite a friend:**

1. Open the trip chat
2. Click the "Invite" button (if available in UI)
3. Enter your friend's email address
4. They will be added to the shared users list

**Requirements:**
- You must be the trip owner
- Your friend must have a TripMind account (their email must exist in the database)

**API Endpoint:**
```bash
POST /api/trip-planner/trips/{tripId}/invite
{
  "userId": "Kartik7",
  "tripId": "trip-123",
  "inviteEmail": "friend@example.com"
}
```

#### 3. Viewing Shared Trips

**To see who has access:**
```bash
GET /api/trip-planner/trips/{tripId}/shared-users?userId=Kartik7
```

**Response:**
```json
{
  "sharedUsers": [
    {
      "user_id": "Kartik7",
      "email": "kartik@example.com",
      "name": "Kartik Sharma",
      "permission": "view_edit",
      "status": "accepted",
      "invited_at": "2024-01-15T10:30:00"
    },
    {
      "user_id": "friend_user",
      "email": "friend@example.com",
      "name": "Friend Name",
      "permission": "view_edit",
      "status": "invited",
      "invited_at": "2024-01-15T11:00:00"
    }
  ]
}
```

#### 4. Accessing Chat History

**All users with access can:**
- View the complete chat history
- See all previous prompts and responses
- Continue the conversation
- Make changes to the trip plan

**API Endpoint:**
```bash
GET /api/trip-planner/trips/{tripId}/messages?userId=Kartik7
```

**Response:**
```json
{
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "I want a 5-day trip to Zurich",
      "timestamp": "2024-01-15T10:00:00"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "🎉 Your trip plan is ready!...",
      "trip_plan": { ... },
      "timestamp": "2024-01-15T10:01:30"
    }
  ]
}
```

## Database Schema

### chat_messages Table

```sql
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id TEXT NOT NULL,
    user_id TEXT NOT NULL,          -- User who sent the message
    role TEXT NOT NULL,              -- 'user' or 'assistant'
    content TEXT NOT NULL,            -- Message content
    trip_plan TEXT,                  -- JSON string of TripPlan (for assistant messages)
    timestamp TEXT NOT NULL,         -- ISO format timestamp
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### shared_trips Table

```sql
CREATE TABLE shared_trips (
    trip_id TEXT NOT NULL,
    owner_user_id TEXT NOT NULL,     -- Original trip creator
    shared_user_id TEXT NOT NULL,    -- User who has been invited
    shared_user_email TEXT,           -- Email of shared user
    permission TEXT DEFAULT 'view_edit',  -- 'view_only' or 'view_edit'
    invited_at TEXT NOT NULL DEFAULT (datetime('now')),
    accepted_at TEXT,                 -- When user accepted the invitation
    PRIMARY KEY (trip_id, shared_user_id)
);
```

## Security

- **Access Control**: Only users with access (owner or invited) can view messages
- **Invitation**: Only the trip owner can invite other users
- **Message Ownership**: Messages are tagged with the user_id who sent them

## Usage Examples

### Example 1: Creating a Trip and Inviting a Friend

```python
# 1. Create a trip (owner: Kartik7)
POST /api/trips/chat
{
  "prompt": "I want a 5-day trip to Zurich",
  "user_id": "Kartik7"
}
# Response includes trip_id: "abc-123"

# 2. Invite a friend
POST /api/trip-planner/trips/abc-123/invite
{
  "userId": "Kartik7",
  "tripId": "abc-123",
  "inviteEmail": "friend@example.com"
}

# 3. Friend can now view and edit
GET /api/trip-planner/trips/abc-123/messages?userId=friend_user
```

### Example 2: Collaborative Planning

```python
# Friend adds a request
POST /api/trips/chat
{
  "prompt": "Can we add more hiking trails?",
  "user_id": "friend_user",
  "trip_id": "abc-123"
}

# Both users see the updated conversation
GET /api/trip-planner/trips/abc-123/messages?userId=Kartik7
GET /api/trip-planner/trips/abc-123/messages?userId=friend_user
```

## Frontend Integration

The UI should:
1. **Load chat history** when opening a trip
2. **Display shared users** in the trip info
3. **Show invite button** for trip owners
4. **Auto-save messages** as they're sent
5. **Sync messages** when multiple users are viewing

## Troubleshooting

### "You don't have access to this trip"
- Make sure you're the trip owner, or
- Ask the trip owner to invite you

### "User with email X not found"
- The user needs to create a TripMind account first
- Their email must exist in the `users` table

### Messages not appearing
- Check that messages are being saved (check database)
- Verify user has access to the trip
- Check API response for errors

## Future Enhancements

- [ ] Real-time message updates (WebSocket)
- [ ] Message notifications
- [ ] Read receipts
- [ ] Permission levels (view-only vs edit)
- [ ] Trip finalization status
- [ ] Export chat history

