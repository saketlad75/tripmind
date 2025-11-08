# TripMind Agents Documentation

## StayAgent

The StayAgent uses **Dedalus Labs** to find accommodations for trips. It searches for properties via Airbnb API or embeddings search, filtering by amenities, reviews, and photos.

### Features

- Uses Dedalus Labs with MCP servers for semantic search
- Integrates with Exa MCP for travel research
- Uses Brave Search MCP for accommodation information
- Parses results into structured Accommodation objects
- Filters by user preferences (amenities, budget, location)

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
- `DEDALUS_MODEL`: Model to use (default: "openai/gpt-4.1")
  - Recommended: `openai/gpt-5` or `openai/gpt-4.1` for better tool calling
  - Alternative: `openai/gpt-5-mini` for faster responses
- `DEDALUS_API_KEY`: Your Dedalus Labs API key
  - Get your API key at [dedaluslabs.ai](https://dedaluslabs.ai)
  - Create an account → Dashboard → Settings → Generate API key

### MCP Servers Used

1. **joerup/exa-mcp**: Semantic travel research
2. **windsor/brave-search-mcp**: Travel information search

### Testing

1. **Set up your API key** in `.env`:
   ```bash
   DEDALUS_API_KEY=your_actual_api_key_here
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

