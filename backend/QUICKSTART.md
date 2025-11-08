# Quick Start Guide

## Using the Virtual Environment

The project uses a virtual environment to manage dependencies. Here's how to use it:

### Activate the Virtual Environment

**On macOS/Linux:**
```bash
cd backend
source venv/bin/activate
```

**On Windows:**
```bash
cd backend
venv\Scripts\activate
```

### Run the API Server

Once the virtual environment is activated, you can run the API server:

```bash
python main.py
# Or
uvicorn main:app --reload
```

### Test the API

```bash
# Health check
curl http://localhost:8000/api/trips/test

# Plan a trip
curl -X POST http://localhost:8000/api/trips/plan \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "I want a 5-day trip to Zurich",
    "destination": "Zurich, Switzerland",
    "duration_days": 5,
    "budget": 2000.0,
    "travelers": 2
  }'
```

### Deactivate the Virtual Environment

When you're done:
```bash
deactivate
```

## Important Notes

1. **Always activate the virtual environment** before running Python scripts
2. Make sure your `.env` file has required API keys set:
   - `DEDALUS_API_KEY` - For StayAgent
   - `GEMINI_API_KEY` - For TravelAgent
3. The virtual environment is located at `backend/venv/`

## Alternative: Use venv Python Directly

If you prefer not to activate the virtual environment, you can use:

```bash
cd backend
./venv/bin/python main.py
```

Or on Windows:
```bash
cd backend
venv\Scripts\python.exe main.py
```
