# Deploy TripMind frontend on Vercel

Only the **React frontend** (`ui/`) is deployed on Vercel. The **Python FastAPI backend** must be hosted elsewhere (e.g. Railway, Render, Fly.io) because Vercel serverless is not suitable for long-running agent workflows and SQLite.

---

## 1. Deploy the backend first

Deploy your FastAPI backend to a provider that supports long-running requests and persistent storage, for example:

- **Railway**: Connect repo, set root to `backend`, add env vars, deploy.
- **Render**: New Web Service, root `backend`, build `pip install -r requirements.txt`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- **Fly.io**: Use a Dockerfile or `fly launch` and point to the backend.

Set **CORS** so your Vercel domain can call the API, e.g. in `backend/main.py` or env:

```bash
CORS_ORIGINS=https://your-app.vercel.app,https://your-app-*.vercel.app
```

Note the **backend URL** (e.g. `https://your-backend.railway.app`).

---

## 2. Deploy the frontend to Vercel

### Option A: Vercel dashboard (recommended)

1. Go to [vercel.com](https://vercel.com) and sign in (GitHub).
2. **Add New** → **Project** and import your TripMind.AI repo.
3. **Configure:**
   - **Root Directory:** leave as `.` (repo root).  
     Vercel will use the repo’s `vercel.json` (build/output in `ui/`).
   - **Framework Preset:** Other (or leave as detected).
   - **Build Command:** (from `vercel.json`) `cd ui && npm ci && npm run build`.
   - **Output Directory:** `ui/build`.
   - **Install Command:** `cd ui && npm ci`.
4. **Environment variables:**
   - `REACT_APP_API_URL` = your backend URL (origin only), e.g. `https://your-backend.railway.app`  
     No trailing slash. The app will call `REACT_APP_API_URL/api/trips`, `REACT_APP_API_URL/api/trip-planner`, etc.
5. Click **Deploy**. Your app will be at `https://your-project.vercel.app`.

### Option B: Vercel CLI

1. Install CLI: `npm i -g vercel`.
2. From the **repo root**:
   ```bash
   cd /path/to/TripMind.AI
   vercel
   ```
3. Follow prompts (link to existing project or create new one).
4. Add env var:
   ```bash
   vercel env add REACT_APP_API_URL
   ```
   Enter your backend origin (e.g. `https://your-backend.railway.app`) when prompted. Choose **Production** (and Preview if you want).
5. Redeploy so the env is used:
   ```bash
   vercel --prod
   ```

---

## 3. Optional: use “ui” as root in Vercel

If you prefer the project root to be `ui/` in Vercel:

1. In the project **Settings** → **General** → **Root Directory** set to `ui`.
2. Remove or override the repo’s `vercel.json` so that:
   - **Build Command:** `npm run build`
   - **Output Directory:** `build`
   - **Install Command:** (leave default or `npm ci`)
3. Add **Environment Variable** `REACT_APP_API_URL` = backend origin (same as above).

---

## 4. Checklist

- [ ] Backend deployed and reachable (e.g. `https://your-backend.railway.app/health`).
- [ ] Backend CORS includes your Vercel URL(s).
- [ ] `REACT_APP_API_URL` set on Vercel to backend **origin** (no trailing slash, no `/api/...`).
- [ ] Redeploy after changing env vars.

---

## 5. Troubleshooting

| Issue | Fix |
|-------|-----|
| CORS errors in browser | Add your Vercel URL to `CORS_ORIGINS` on the backend and redeploy backend. |
| 404 on refresh (e.g. `/trips`) | Repo’s `vercel.json` rewrites `/*` to `/index.html` for SPA routing; ensure it’s applied. |
| “Network error” or API not called | Confirm `REACT_APP_API_URL` is set and has no trailing slash; rebuild/redeploy frontend. |
| Build fails | Ensure **Root Directory** and build/output in `vercel.json` match (repo root + `ui` subfolder, or root = `ui`). |
