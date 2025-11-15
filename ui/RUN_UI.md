# How to Run the UI

## Step-by-Step Instructions

### 1. Open a Terminal

Open a new terminal window (keep it open to see the output).

### 2. Navigate to UI Directory

```bash
cd /Volumes/Seagate/Masters/Projects/Airbnb/ui
```

### 3. Start the React App

```bash
npm start
```

### 4. Wait for Compilation

You should see:
```
Compiling...
Compiled successfully!

You can now view trip-booking-platform in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

### 5. Browser Opens Automatically

The app should open in your default browser at **http://localhost:3000**

## If It Doesn't Start

### Check Node.js Version
```bash
node --version  # Should be v14+ or v16+
npm --version   # Should be v6+
```

### Reinstall Dependencies
```bash
cd /Volumes/Seagate/Masters/Projects/Airbnb/ui
rm -rf node_modules package-lock.json
npm install
npm start
```

### Check for Port Conflicts
```bash
# If port 3000 is in use:
lsof -ti:3000 | xargs kill

# Or use a different port:
PORT=3001 npm start
```

### Check for Errors
Look for error messages in the terminal output. Common issues:
- Missing dependencies
- Syntax errors in code
- Port already in use

## Important: Backend Must Be Running

Before the UI can work, start the backend in **another terminal**:

```bash
cd /Volumes/Seagate/Masters/Projects/Airbnb/backend
source venv/bin/activate
uvicorn main:app --reload
```

Backend runs on: **http://localhost:8000**

## Quick Test

Once both are running:
1. Open browser: http://localhost:3000
2. You should see the TripMind UI
3. Try entering a prompt in the search bar

## Troubleshooting

**"npm: command not found"**
- Install Node.js from https://nodejs.org/

**"EADDRINUSE: address already in use"**
- Kill the process using port 3000
- Or use: `PORT=3001 npm start`

**"Module not found" errors**
- Run: `npm install` again

**UI loads but shows errors**
- Check browser console (F12)
- Make sure backend is running
- Check API endpoint in SearchBar.js

