"""
API routes for TripMind
"""

from fastapi import APIRouter, HTTPException
from shared.types import TripRequest, TripPlan, UserProfile
from services.orchestrator import TripOrchestrator

trip_router = APIRouter()

# Global orchestrator instance (will be set by main.py)
orchestrator: TripOrchestrator = None


@trip_router.post("/users/{user_id}/profile", response_model=UserProfile)
async def create_or_update_profile(user_id: str, profile: UserProfile):
    """
    Create or update user profile
    
    Args:
        user_id: User ID (must match profile.user_id)
        profile: User profile data
        
    Returns:
        Created/updated user profile
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    if profile.user_id != user_id:
        raise HTTPException(
            status_code=400,
            detail="User ID in path must match user_id in profile"
        )
    
    try:
        orchestrator.register_user_profile(profile)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving profile: {str(e)}")


@trip_router.get("/users/{user_id}/profile", response_model=UserProfile)
async def get_profile(user_id: str):
    """
    Get user profile by ID
    
    Args:
        user_id: User ID
        
    Returns:
        User profile
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    profile = orchestrator.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    return profile


@trip_router.post("/plan", response_model=TripPlan)
async def plan_trip(request: TripRequest):
    """
    Plan a trip based on user request
    
    Args:
        request: TripRequest with user's trip description and user_id
        
    Returns:
        Complete TripPlan with accommodations, restaurants, transportation, experiences, and itinerary
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        # Get user profile
        user_profile = orchestrator.get_user_profile(request.user_id)
        if not user_profile:
            raise HTTPException(
                status_code=404,
                detail=f"User profile not found for user_id: {request.user_id}. Please create a profile first."
            )
        
        plan = await orchestrator.plan_trip(request, user_profile)
        return plan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error planning trip: {str(e)}")


@trip_router.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return {"status": "ok", "message": "TripMind API is running"}

