# TripMind — AI Trip Orchestrator

"Describe your dream trip, and TripMind books the stay, itinerary, and experiences for you."

## Overview

TripMind is an AI-powered trip planning system that uses a multi-agent architecture to orchestrate complete trip planning and booking. Simply describe your dream trip, and TripMind handles everything from finding accommodations to creating detailed itineraries.

## Features

- 🏡 **StayAgent** - Finds properties via Airbnb API or embeddings search
- ✈️ **TravelAgent** - Finds nearest airport/train and optimized schedule
- 🗺️ **ExperienceAgent** - Fetches local activities from TripAdvisor/Viator APIs
- 💰 **BudgetAgent** - Plans total cost and adjusts parameters
- 🧭 **PlannerAgent** - Composes complete itinerary with map visualization

## Tech Stack

- **Frontend**: Next.js 14 with TypeScript
- **Backend**: Python FastAPI
- **Orchestration**: LangGraph
- **LLM**: OpenAI GPT-4o-mini / Claude Sonnet
- **Embeddings**: OpenAI / AWS Bedrock Titan
- **APIs**: Airbnb, Skyscanner, TripAdvisor/Viator

## Project Structure

```
├── frontend/          # Next.js application
├── backend/           # Python FastAPI backend
│   ├── agents/        # Multi-agent system
│   ├── api/           # API integrations
│   └── services/      # Core services
├── shared/            # Shared types and utilities
└── docs/              # Documentation
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- API keys for:
  - OpenAI (or Anthropic)
  - Airbnb API
  - Skyscanner API
  - TripAdvisor/Viator API

### Installation

1. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Frontend Setup**
```bash
cd frontend
npm install
```

3. **Environment Variables**
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
# Edit with your API keys
```

### Running the Application

1. **Start Backend**
```bash
cd backend
uvicorn main:app --reload
```

2. **Start Frontend**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000` to use TripMind.

## Usage

1. Enter your dream trip description in natural language
2. TripMind's agents work together to:
   - Find suitable accommodations
   - Plan transportation
   - Discover local experiences
   - Optimize budget
   - Create detailed itinerary
3. Review and approve the generated plan
4. Optionally book automatically via API

## Metrics

- Conversion rate ↑
- Planning time ↓ 90%
- Average trip value ↑

## License

MIT

