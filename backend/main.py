"""
TripMind Backend - FastAPI Application
Main entry point for the TripMind API server
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv

from api import routes
from services.orchestrator import TripOrchestrator
from services.itinerary_service import ItineraryService
from database.db import init_db

load_dotenv()

# Global orchestrator instance
orchestrator = None
itinerary_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global orchestrator, itinerary_service
    
    # Initialize database
    init_db()
    
    # Startup
    # Initialize orchestrator only if API keys are available
    # (needed for legacy /plan endpoint)
    import os
    if os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        try:
            orchestrator = TripOrchestrator()
            await orchestrator.initialize()
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize orchestrator: {e}")
            print("   Legacy /plan endpoint will not be available")
            orchestrator = None
    else:
        print("⚠️  Warning: No LLM API key found (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
        print("   Orchestrator not initialized. Legacy /plan endpoint will not be available.")
        print("   New /generate endpoint uses ItineraryService (doesn't need orchestrator)")
        orchestrator = None
    
    # Initialize itinerary service (uses its own agents, doesn't need orchestrator)
    itinerary_service = ItineraryService()
    await itinerary_service.initialize()
    
    # Set in routes module
    routes.orchestrator = orchestrator
    routes.itinerary_service = itinerary_service
    yield
    # Shutdown
    if orchestrator:
        await orchestrator.cleanup()
    routes.orchestrator = None
    routes.itinerary_service = None


app = FastAPI(
    title="TripMind API",
    description="AI Trip Orchestrator - Multi-agent trip planning system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
import os
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
if cors_origins == ["*"]:
    # Development: allow all origins
    cors_origins = ["*"]
else:
    # Production: specific origins
    cors_origins = [origin.strip() for origin in cors_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.trip_router, prefix="/api/trips", tags=["trips"])
# Include chat router for trip-planner API (matches frontend expectations)
app.include_router(routes.chat_router, prefix="/api/trip-planner", tags=["chat"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "TripMind API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "orchestrator": "initialized" if orchestrator else "not initialized"
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

