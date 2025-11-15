# How to Start the Backend Server

## Quick Start (Windows)

1. Open a new terminal/command prompt
2. Navigate to the backend directory:
   ```bash
   cd tripmind\backend
   ```
3. Run the startup script:
   ```bash
   start_server.bat
   ```

## Quick Start (Mac/Linux)

1. Open a new terminal
2. Navigate to the backend directory:
   ```bash
   cd tripmind/backend
   ```
3. Make the script executable and run it:
   ```bash
   chmod +x start_server.sh
   ./start_server.sh
   ```

## Manual Start

1. **Navigate to backend directory:**
   ```bash
   cd tripmind\backend
   ```

2. **Activate virtual environment:**
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

3. **Install dependencies (if not already installed):**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Create a `.env` file in the `tripmind/backend` directory
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY=your_gemini_api_key_here
     ```
   - Get your API key from: https://makersuite.google.com/app/apikey
   - (Optional) You can also use `GOOGLE_API_KEY` instead of `GEMINI_API_KEY`

5. **Start the server:**
   ```bash
   python main.py
   ```
   Or:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

## Verify Server is Running

1. Open your browser and go to: http://localhost:8000/health
2. You should see: `{"status":"healthy","orchestrator":"initialized"}`

## Troubleshooting

- **Port 8000 already in use**: Change the port in `main.py` or use: `uvicorn main:app --reload --port 8001`
- **Module not found**: Make sure you're in the `tripmind/backend` directory and virtual environment is activated
- **Gemini API key error**: Make sure you've set `GEMINI_API_KEY` in your `.env` file

## API Endpoints

Once running, the following endpoints will be available:
- `GET /health` - Health check
- `POST /api/trip-planner/trips/{tripId}/chat` - Chat with AI
- `POST /api/trip-planner/trips/{tripId}/messages` - Save message
- `GET /api/trip-planner/trips/{tripId}/messages` - Get messages
- `GET /api/trip-planner/trips` - List trips
- `POST /api/trip-planner` - Create trip

