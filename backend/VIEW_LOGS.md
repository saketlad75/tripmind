# Viewing Backend Logs

To see all backend output and logs in your terminal, run the backend server in the foreground.

## Option 1: Using the Script (Recommended)

```bash
cd backend
./start_with_logs.sh
```

## Option 2: Manual Command

```bash
cd backend
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info --access-log
```

## What You'll See

When a request comes in, you'll see:

```
================================================================================
📨 NEW CHAT REQUEST RECEIVED
================================================================================
👤 User ID: Kartik7
🆔 Trip ID: NEW TRIP
💬 Prompt: I want a 5-day quiet nature escape with good Wi-Fi, hiking trails...
================================================================================
🔍 Fetching user profile for: Kartik7
✅ User profile found: John Doe (Budget: $3500.0)
🆔 Using Trip ID: abc123-def456 (NEW)

🤖 Starting AI Agent Workflow...
   Running: StayAgent → RestaurantAgent → TravelAgent → ExperienceAgent → BudgetAgent → PlannerAgent
   This may take 2-5 minutes...

   🏨 [1/6] StayAgent: Finding accommodations...
      ✅ Found 3 accommodations
   🍽️  [2/6] RestaurantAgent: Finding restaurants...
      ✅ Found 4 restaurants
   ✈️  [3/6] TravelAgent: Finding transportation options...
      ✅ Found 5 transportation options
   🎯 [4/6] ExperienceAgent: Finding local activities...
      ✅ Found 5 experiences
   💰 [5/6] BudgetAgent: Calculating budget...
      ✅ Budget calculated: $6586.25
   📅 [6/6] PlannerAgent: Creating itinerary...
      ✅ Created 5-day itinerary

✅ All agents completed successfully!
   🏨 Accommodations: 3
   🍽️  Restaurants: 4
   ✈️  Transportation: 5
   🎯 Experiences: 5
   📅 Itinerary Days: 5
   💰 Total Budget: $6586.25 USD

💾 Saving trip plan to database...
✅ Trip plan saved successfully!

📤 Sending response to client...
================================================================================
✅ REQUEST COMPLETED SUCCESSFULLY
```

## Stop the Server

Press `Ctrl+C` in the terminal where the server is running.

