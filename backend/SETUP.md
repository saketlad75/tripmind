# TripMind Backend Setup Guide

## Prerequisites

- Python 3.11 or higher
- pip
- Virtual environment (recommended)

## Installation Steps

1. **Create and activate virtual environment**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required API keys:
- `DEDALUS_API_KEY` - For Dedalus Labs (required for StayAgent)
  - Get your API key at [dedaluslabs.ai](https://dedaluslabs.ai)
  - Create an account → Dashboard → Settings → Generate API key
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` - For LLM (for other agents)

4. **Test the API**

```bash
python main.py
# Then test with: curl http://localhost:8000/api/trips/test
```

5. **Run the API server**

```bash
python main.py
# Or
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health check
- `GET /api/trips/test` - Test endpoint
- `POST /api/trips/plan` - Plan a trip

## Example API Request

```bash
curl -X POST "http://localhost:8000/api/trips/plan" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "I want a 5-day quiet nature escape with good Wi-Fi near Zurich",
    "destination": "Zurich, Switzerland",
    "duration_days": 5,
    "budget": 2000.0,
    "travelers": 2
  }'
```

## Project Structure

```
backend/
├── agents/           # Agent implementations
│   ├── stay_agent.py           # StayAgent (using Dedalus Labs)
│   ├── travel_agent.py         # TravelAgent (multi-agent orchestration)
│   ├── flight_search_agent.py  # Flight search agent
│   ├── train_search_agent.py   # Train search agent
│   ├── bus_search_agent.py     # Bus search agent
│   ├── car_search_agent.py     # Car/cab search agent
│   ├── route_analyzer_agent.py # Route analysis agent
│   ├── gemini_search_agent.py  # Gemini web search agent
│   ├── experience_agent.py      # ExperienceAgent
│   ├── budget_agent.py         # BudgetAgent
│   └── planner_agent.py        # PlannerAgent
├── api/              # API routes
│   └── routes.py
├── services/         # Core services
│   └── orchestrator.py   # Main orchestration service
├── shared/           # Shared types
│   └── types.py
├── main.py           # FastAPI application entry point
└── requirements.txt  # Python dependencies
```

## Troubleshooting

### Import errors

Make sure you're in the backend directory and the virtual environment is activated.

### Dedalus Labs errors

- Verify your `DEDALUS_API_KEY` is set correctly
- Check that MCP servers are accessible
- Ensure you have the latest version of `dedalus-labs`

### LangGraph errors

- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.11+)

