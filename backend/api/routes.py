"""
API routes for TripMind

NOTE: This API is designed for UI integration.
All user registration and profile data comes from the frontend UI.
No hardcoded user data - everything is received via API endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from shared.types import TripRequest, TripPlan, UserProfile
from services.orchestrator import TripOrchestrator
from services.itinerary_service import ItineraryService

trip_router = APIRouter()

# Global orchestrator instance (will be set by main.py)
orchestrator: TripOrchestrator = None

# Global itinerary service instance (will be set by main.py)
itinerary_service: ItineraryService = None


# Request/Response models
class GenerateItineraryRequest(BaseModel):
    """Request model for generating itinerary from prompt"""
    prompt: str
    user_id: str
    trip_id: str  # Required from frontend


class FollowUpRequest(BaseModel):
    """Request model for follow-up queries/modifications"""
    prompt: str
    user_id: Optional[str] = None


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


@trip_router.post("/generate", response_model=TripPlan)
async def generate_itinerary(request: GenerateItineraryRequest):
    """
    Generate itinerary from natural language prompt
    
    Args:
        request: GenerateItineraryRequest with prompt and user_id
        
    Returns:
        Complete TripPlan with accommodations, restaurants, transportation, experiences, and itinerary
    """
    if itinerary_service is None:
        raise HTTPException(status_code=503, detail="Itinerary service not initialized")
    
    try:
        # Generate itinerary from prompt
        # User profile will be fetched from database automatically
        # trip_id is optional - frontend can provide it
        plan = await itinerary_service.generate_from_prompt(
            request.prompt,
            request.user_id,
            user_profile=None,  # Will fetch from database
            trip_id=request.trip_id  # Frontend provides trip_id
        )
        
        return plan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating itinerary: {str(e)}")


@trip_router.post("/{user_id}/{trip_id}/follow-up")
async def handle_follow_up(user_id: str, trip_id: str, request: FollowUpRequest):
    """
    Handle follow-up queries or modifications for an existing itinerary
    
    Args:
        user_id: User ID who owns the itinerary
        trip_id: Trip ID (from frontend)
        request: FollowUpRequest with prompt and optional user_id (modifier)
        
    Returns:
        Either an answer (for queries) or updated itinerary (for modifications)
    """
    if itinerary_service is None:
        raise HTTPException(status_code=503, detail="Itinerary service not initialized")
    
    try:
        # Handle follow-up
        # request.user_id is the modifying user (can be different from owner)
        result = await itinerary_service.handle_follow_up(
            user_id=user_id,
            trip_id=trip_id,
            prompt=request.prompt,
            modifying_user_id=request.user_id,  # Who is making the modification
            user_profile=None  # Will fetch from database
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error handling follow-up: {str(e)}")


@trip_router.get("/{user_id}/{trip_id}", response_model=TripPlan)
async def get_itinerary(user_id: str, trip_id: str, version: Optional[int] = None):
    """
    Get itinerary by user_id and trip_id
    
    Args:
        user_id: User ID
        trip_id: Trip ID (from frontend)
        version: Optional version number (if not provided, returns latest version)
        
    Returns:
        TripPlan (the generated itinerary text)
    """
    if itinerary_service is None:
        raise HTTPException(status_code=503, detail="Itinerary service not initialized")
    
    itinerary = itinerary_service.get_itinerary(user_id, trip_id, version)
    if not itinerary:
        raise HTTPException(status_code=404, detail=f"Itinerary not found for user_id={user_id}, trip_id={trip_id}")
    
    return itinerary


@trip_router.get("/{user_id}/{trip_id}/versions")
async def get_itinerary_versions(user_id: str, trip_id: str):
    """
    Get all versions of an itinerary
    
    Args:
        user_id: User ID
        trip_id: Trip ID (from frontend)
        
    Returns:
        List of version summaries
    """
    if itinerary_service is None:
        raise HTTPException(status_code=503, detail="Itinerary service not initialized")
    
    try:
        versions = itinerary_service.get_itinerary_versions(user_id, trip_id)
        return {"user_id": user_id, "trip_id": trip_id, "versions": versions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching versions: {str(e)}")


@trip_router.get("/users/{user_id}/itineraries")
async def list_user_itineraries(user_id: str):
    """
    List all itineraries for a user
    
    Args:
        user_id: User ID
        
    Returns:
        List of itinerary summaries
    """
    if itinerary_service is None:
        raise HTTPException(status_code=503, detail="Itinerary service not initialized")
    
    try:
        itineraries = itinerary_service.list_itineraries(user_id)
        return {"user_id": user_id, "itineraries": itineraries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing itineraries: {str(e)}")
