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

load_dotenv()

# Global orchestrator instance
orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global orchestrator
    # Startup
    orchestrator = TripOrchestrator()
    await orchestrator.initialize()
    # Set orchestrator in routes module
    routes.orchestrator = orchestrator
    yield
    # Shutdown
    await orchestrator.cleanup()
    routes.orchestrator = None


app = FastAPI(
    title="TripMind API",
    description="AI Trip Orchestrator - Multi-agent trip planning system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.trip_router, prefix="/api/trips", tags=["trips"])


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

