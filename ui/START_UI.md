# Starting the UI

## Quick Start

```bash
cd ui
npm start
```

The UI will start on **http://localhost:3000**

## Important Notes

1. **Backend must be running first:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn main:app --reload
   ```
   Backend runs on: **http://localhost:8000**

2. **UI Configuration:**
   - The SearchBar component currently points to: `http://localhost:8000/api/trip-planner`
   - This needs to be updated to: `http://localhost:8000/api/trips/chat`
   - See `INTEGRATION_GUIDE.md` for details

3. **User Registration:**
   - Users must register before planning trips
   - Registration endpoint: `POST /api/trips/users/{user_id}/profile`

## Troubleshooting

- **Port 3000 already in use?**
  - Kill the process: `lsof -ti:3000 | xargs kill`
  - Or use a different port: `PORT=3001 npm start`

- **npm install issues?**
  - Delete `node_modules` and `package-lock.json`
  - Run `npm install` again

- **Backend not responding?**
  - Make sure backend is running on port 8000
  - Check: `curl http://localhost:8000/health`

