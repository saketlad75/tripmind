"""
API routes for TripMind
"""

from fastapi import APIRouter, HTTPException
from shared.types import TripRequest, TripPlan
from services.orchestrator import TripOrchestrator

trip_router = APIRouter()

# Global orchestrator instance (will be set by main.py)
orchestrator: TripOrchestrator = None


@trip_router.post("/plan", response_model=TripPlan)
async def plan_trip(request: TripRequest):
    """
    Plan a trip based on user request
    
    Args:
        request: TripRequest with user's trip description
        
    Returns:
        Complete TripPlan with accommodations, transportation, experiences, and itinerary
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        plan = await orchestrator.plan_trip(request)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error planning trip: {str(e)}")


@trip_router.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return {"status": "ok", "message": "TripMind API is running"}
