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

### Run Tests

Once the virtual environment is activated, you can run the test script:

```bash
python test_stay_agent.py
```

### Run the API Server

```bash
python main.py
# Or
uvicorn main:app --reload
```

### Deactivate the Virtual Environment

When you're done:
```bash
deactivate
```

## Important Notes

1. **Always activate the virtual environment** before running Python scripts
2. Make sure your `.env` file has `DEDALUS_API_KEY` set
3. The virtual environment is located at `backend/venv/`

## Alternative: Use venv Python Directly

If you prefer not to activate the virtual environment, you can use:

```bash
cd backend
./venv/bin/python test_stay_agent.py
```

Or on Windows:
```bash
cd backend
venv\Scripts\python.exe test_stay_agent.py
```

