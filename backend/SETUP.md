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
- `GOOGLE_API_KEY` - For Google Gemini API (required for StayAgent, RestaurantAgent, PlannerAgent)
  - Get your API key at [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Sign in with Google account → Create API key
- `GEMINI_MODEL` - Optional, defaults to "gemini-1.5-pro"
  - Options: "gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` - For LLM (for other agents)

4. **Test StayAgent**

```bash
python test_stay_agent.py
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
│   ├── stay_agent.py      # StayAgent (using Google Gemini API)
│   ├── travel_agent.py    # TravelAgent (placeholder)
│   ├── experience_agent.py # ExperienceAgent (placeholder)
│   ├── budget_agent.py    # BudgetAgent (placeholder)
│   └── planner_agent.py   # PlannerAgent (placeholder)
├── api/              # API routes
│   └── routes.py
├── services/         # Core services
│   └── orchestrator.py   # Main orchestration service
├── shared/           # Shared types (symlink or copy)
│   └── types.py
├── main.py           # FastAPI application entry point
├── requirements.txt  # Python dependencies
└── test_stay_agent.py # Test script for StayAgent
```

## Troubleshooting

### Import errors

Make sure you're in the backend directory and the virtual environment is activated.

### Google Gemini API errors

- Verify your `GOOGLE_API_KEY` is set correctly
- Check that the API key has proper permissions
- Ensure you have the latest version of `google-generativeai`
- Check rate limits: Free tier has 15 requests per minute

### LangGraph errors

- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.11+)

