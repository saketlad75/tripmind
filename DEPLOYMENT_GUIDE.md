# TripMind Deployment Guide

This guide covers multiple deployment options for the TripMind application.

## Table of Contents

1. [Quick Start with Docker](#quick-start-with-docker)
2. [Cloud Platform Deployments](#cloud-platform-deployments)
3. [Traditional VPS Deployment](#traditional-vps-deployment)
4. [Environment Variables](#environment-variables)
5. [Database Setup](#database-setup)
6. [Production Considerations](#production-considerations)

---

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- API keys (Google Gemini API key)

### Step 1: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Google Gemini API (Required)
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Optional: Other LLM providers
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

### Step 2: Build and Run

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Step 3: Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

---

## Cloud Platform Deployments

### Option 1: Railway

#### Backend Deployment

1. **Create Railway Account**: https://railway.app

2. **Create New Project**:
   ```bash
   # Install Railway CLI
   npm i -g @railway/cli
   
   # Login
   railway login
   
   # Initialize project
   cd backend
   railway init
   ```

3. **Set Environment Variables** in Railway dashboard:
   - `GOOGLE_API_KEY`
   - `GEMINI_MODEL=gemini-2.5-flash`
   - `PORT=8000` (Railway sets this automatically)

4. **Deploy**:
   ```bash
   railway up
   ```

5. **Add Railway Configuration** (`railway.json`):
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "DOCKERFILE",
       "dockerfilePath": "Dockerfile"
     },
     "deploy": {
       "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

#### Frontend Deployment

1. **Build React App**:
   ```bash
   cd ui
   npm run build
   ```

2. **Deploy to Railway** or use **Vercel/Netlify**:
   - Connect your GitHub repo
   - Set build command: `npm run build`
   - Set output directory: `build`
   - Add environment variable: `REACT_APP_API_URL=https://your-backend-url.railway.app/api/trips`

### Option 2: Render

#### Backend Deployment

1. **Create Render Account**: https://render.com

2. **Create New Web Service**:
   - Connect GitHub repository
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables**:
   - `GOOGLE_API_KEY`
   - `GEMINI_MODEL=gemini-2.5-flash`
   - `PORT=8000`

4. **Deploy**: Render will automatically deploy on git push

#### Frontend Deployment

1. **Create Static Site**:
   - Connect GitHub repository
   - Root Directory: `ui`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `build`

2. **Set Environment Variable**:
   - `REACT_APP_API_URL=https://your-backend.onrender.com/api/trips`

### Option 3: Heroku

#### Backend Deployment

1. **Install Heroku CLI**: https://devcenter.heroku.com/articles/heroku-cli

2. **Create Heroku App**:
   ```bash
   cd backend
   heroku create tripmind-backend
   ```

3. **Set Environment Variables**:
   ```bash
   heroku config:set GOOGLE_API_KEY=your_key_here
   heroku config:set GEMINI_MODEL=gemini-2.5-flash
   ```

4. **Create `Procfile`** in `backend/`:
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

5. **Deploy**:
   ```bash
   git push heroku main
   ```

#### Frontend Deployment

1. **Build and Deploy**:
   ```bash
   cd ui
   npm run build
   # Use Heroku static buildpack or deploy to Vercel/Netlify
   ```

### Option 4: AWS (EC2 + ECS)

#### Using Docker on EC2

1. **Launch EC2 Instance** (Ubuntu 22.04)

2. **Install Docker**:
   ```bash
   sudo apt update
   sudo apt install docker.io docker-compose -y
   sudo usermod -aG docker $USER
   ```

3. **Clone Repository**:
   ```bash
   git clone <your-repo-url>
   cd Airbnb
   ```

4. **Set Environment Variables**:
   ```bash
   # Create .env file
   nano backend/.env
   # Add your API keys
   ```

5. **Start Services**:
   ```bash
   docker-compose up -d
   ```

6. **Configure Security Group**:
   - Allow inbound: Port 80 (HTTP), Port 443 (HTTPS), Port 8000 (Backend)

7. **Set Up Nginx Reverse Proxy** (optional):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:3000;
       }
       
       location /api {
           proxy_pass http://localhost:8000;
       }
   }
   ```

---

## Traditional VPS Deployment

### Backend Setup

1. **SSH into VPS**:
   ```bash
   ssh user@your-server-ip
   ```

2. **Install Python and Dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3.10 python3-pip python3-venv nginx -y
   ```

3. **Clone Repository**:
   ```bash
   git clone <your-repo-url>
   cd Airbnb/backend
   ```

4. **Create Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Set Environment Variables**:
   ```bash
   nano .env
   # Add: GOOGLE_API_KEY=your_key_here
   ```

6. **Create Systemd Service** (`/etc/systemd/system/tripmind-backend.service`):
   ```ini
   [Unit]
   Description=TripMind Backend API
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/path/to/Airbnb/backend
   Environment="PATH=/path/to/Airbnb/backend/venv/bin"
   ExecStart=/path/to/Airbnb/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

7. **Start Service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tripmind-backend
   sudo systemctl start tripmind-backend
   sudo systemctl status tripmind-backend
   ```

### Frontend Setup

1. **Install Node.js**:
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt install -y nodejs
   ```

2. **Build React App**:
   ```bash
   cd ui
   npm install
   npm run build
   ```

3. **Configure Nginx**:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       root /path/to/Airbnb/ui/build;
       index index.html;

       location / {
           try_files $uri $uri/ /index.html;
       }

       location /api {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **Restart Nginx**:
   ```bash
   sudo nginx -t
   sudo systemctl restart nginx
   ```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API key | `AIzaSy...` |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.5-flash` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (for LLM) | - |
| `ANTHROPIC_API_KEY` | Anthropic API key (for LLM) | - |
| `ENVIRONMENT` | Environment (production/development) | `development` |
| `PORT` | Backend port | `8000` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

### Setting Variables

**Docker Compose**:
```yaml
environment:
  - GOOGLE_API_KEY=${GOOGLE_API_KEY}
```

**Railway/Render/Heroku**:
- Set in dashboard under "Environment Variables"

**VPS**:
```bash
export GOOGLE_API_KEY=your_key_here
# Or add to .env file
```

---

## Database Setup

### SQLite (Default - Development)

The application uses SQLite by default. The database file is created automatically at:
```
backend/database/tripmind.db
```

### PostgreSQL (Production Recommended)

1. **Install PostgreSQL**:
   ```bash
   sudo apt install postgresql postgresql-contrib
   ```

2. **Create Database**:
   ```sql
   CREATE DATABASE tripmind;
   CREATE USER tripmind_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE tripmind TO tripmind_user;
   ```

3. **Update `backend/database/db.py`** to use PostgreSQL:
   ```python
   import psycopg2
   # Update connection string
   DATABASE_URL = "postgresql://tripmind_user:password@localhost/tripmind"
   ```

4. **Install PostgreSQL adapter**:
   ```bash
   pip install psycopg2-binary
   ```

---

## Production Considerations

### Security

1. **Use HTTPS**: Set up SSL certificates (Let's Encrypt)
2. **Environment Variables**: Never commit `.env` files
3. **API Rate Limiting**: Implement rate limiting for API endpoints
4. **CORS**: Restrict CORS origins to your frontend domain
5. **Database**: Use PostgreSQL in production, not SQLite

### Performance

1. **Gunicorn Workers**: Use Gunicorn with multiple workers:
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

2. **Caching**: Implement Redis for caching API responses

3. **CDN**: Use CDN for static assets (Vercel/Netlify provide this)

4. **Database Indexing**: Ensure database indexes are created

### Monitoring

1. **Health Checks**: Use `/health` endpoint for monitoring
2. **Logging**: Set up centralized logging (e.g., Logtail, Datadog)
3. **Error Tracking**: Use Sentry for error tracking
4. **Uptime Monitoring**: Use UptimeRobot or Pingdom

### Scaling

1. **Horizontal Scaling**: Deploy multiple backend instances behind a load balancer
2. **Database**: Use managed database service (AWS RDS, Railway Postgres)
3. **Queue**: Use Redis/RabbitMQ for background job processing

---

## Quick Deployment Checklist

- [ ] Set up environment variables
- [ ] Configure database (SQLite for dev, PostgreSQL for prod)
- [ ] Set up SSL/HTTPS
- [ ] Configure CORS for frontend domain
- [ ] Set up monitoring and logging
- [ ] Test health check endpoint
- [ ] Test API endpoints
- [ ] Set up automated backups
- [ ] Configure firewall rules
- [ ] Set up CI/CD pipeline (optional)

---

## Troubleshooting

### Backend won't start
- Check environment variables are set
- Verify API keys are valid
- Check logs: `docker-compose logs backend`

### Frontend can't connect to backend
- Verify backend is running
- Check CORS configuration
- Verify API URL in frontend environment variables

### Database errors
- Ensure database file/directory has write permissions
- Check database connection string
- Verify database is initialized

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Review error messages in terminal
3. Verify all environment variables are set correctly

