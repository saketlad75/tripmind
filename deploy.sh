#!/bin/bash

# TripMind Deployment Script
# This script helps deploy the application using Docker Compose

set -e

echo "🚀 TripMind Deployment Script"
echo "=============================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check for .env file
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Warning: backend/.env file not found"
    echo "   Creating template .env file..."
    cat > backend/.env << EOF
# Google Gemini API (Required)
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Optional: Other LLM providers
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Environment
ENVIRONMENT=production

# CORS (comma-separated, use * for all)
CORS_ORIGINS=*
EOF
    echo "   ✅ Created backend/.env template"
    echo "   ⚠️  Please edit backend/.env and add your API keys before deploying!"
    read -p "   Press Enter to continue after adding your API keys, or Ctrl+C to exit..."
fi

# Build and start services
echo ""
echo "📦 Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo ""
echo "🏥 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Backend is healthy"
else
    echo "   ⚠️  Backend health check failed (may still be starting)"
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "   ✅ Frontend is healthy"
else
    echo "   ⚠️  Frontend health check failed (may still be starting)"
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📍 Access your application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   Health:   http://localhost:8000/health"
echo ""
echo "📋 Useful commands:"
echo "   View logs:    docker-compose logs -f"
echo "   Stop:         docker-compose down"
echo "   Restart:      docker-compose restart"
echo "   Rebuild:      docker-compose up -d --build"
echo ""

