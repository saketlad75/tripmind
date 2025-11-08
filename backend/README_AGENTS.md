# TripMind Agents Documentation

## StayAgent

The StayAgent uses **Google Gemini API** to find accommodations for trips. It uses AI reasoning to search for properties, filtering by amenities, reviews, and photos.

### Features

- Uses Google Gemini API for AI-powered search
- Parses results into structured Accommodation objects
- Filters by user preferences (amenities, budget, location)
- Handles rate limits with automatic retry logic

### Usage

```python
from agents.stay_agent import StayAgent
from shared.types import TripRequest

agent = StayAgent()
await agent.initialize()

request = TripRequest(
    prompt="I want a 5-day quiet nature escape with good Wi-Fi near Zurich",
    destination="Zurich, Switzerland",
    duration_days=5,
    budget=2000.0,
    travelers=2
)

results = await agent.process(request)
# Returns: {"accommodations": [...], "raw_output": "...", "count": N}
```

### Configuration

Set in `.env`:
- `GOOGLE_API_KEY`: Your Google Gemini API key (required)
  - Get your API key at [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Sign in with Google account → Create API key
- `GEMINI_MODEL`: Model to use (default: "gemini-1.5-pro")
  - Options: `gemini-1.5-pro` (recommended), `gemini-1.5-flash` (faster), `gemini-pro`

### Testing

1. **Set up your API key** in `.env`:
   ```bash
   GOOGLE_API_KEY=your_actual_api_key_here
   GEMINI_MODEL=gemini-1.5-pro
   ```

2. **Run the test script**:
   ```bash
   cd backend
   python test_stay_agent.py
   ```

### Error Handling

The StayAgent includes:
- API key validation on initialization
- Clear error messages if the API key is missing
- Error handling for Dedalus API calls
- Fallback parsing if structured JSON isn't returned

## Other Agents

- **TravelAgent**: Finds transportation options (to be implemented)
- **ExperienceAgent**: Finds local activities (to be implemented)
- **BudgetAgent**: Plans and optimizes budget (to be implemented)
- **PlannerAgent**: Creates final itinerary (to be implemented)

