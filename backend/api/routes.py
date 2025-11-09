"""
API routes for TripMind
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime
import json
import re
from shared.types import TripRequest, TripPlan, UserProfile
from services.orchestrator import TripOrchestrator
from services.itinerary_service import ItineraryService
from database.db import get_db_connection

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


class ChatRequest(BaseModel):
    """Request model for chat-style trip planning"""
    prompt: str
    user_id: str
    trip_id: Optional[str] = None  # If provided, updates existing trip plan
    selected_accommodation_id: Optional[str] = None  # If user selected an accommodation


class ChatResponse(BaseModel):
    """Response model for chat-style trip planning"""
    trip_id: str
    message: str
    trip_plan: TripPlan
    status: str  # "new", "updated", "in_progress"


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

>>>>>>> Stashed changes

@trip_router.post("/chat", response_model=ChatResponse)
async def chat_plan_trip(request: ChatRequest):
    """
    Chat-style trip planning endpoint for UI chat interface
    
    This endpoint:
    1. Accepts a natural language prompt from the user
    2. Runs all AI agents (StayAgent, RestaurantAgent, TravelAgent, ExperienceAgent, BudgetAgent, PlannerAgent)
    3. Generates a complete trip plan
    4. Stores the plan in the database
    5. Returns the plan in a chat-friendly format
    
    If trip_id is provided, it updates an existing trip plan.
    If not provided, it creates a new trip plan.
    
    Args:
        request: ChatRequest with prompt, user_id, and optional trip_id
        
    Returns:
        ChatResponse with trip_id, message, and complete TripPlan
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
        
        # Generate or get trip_id
        trip_id = request.trip_id or str(uuid.uuid4())
        is_update = request.trip_id is not None
        
        # If updating, load existing trip plan to preserve destination and other details
        existing_plan = None
        if is_update:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT itinerary FROM itineraries 
                    WHERE user_id = ? AND trip_id = ?
                    """,
                    (request.user_id, trip_id)
                )
                result = cursor.fetchone()
                if result:
                    plan_dict = json.loads(result['itinerary'])
                    existing_plan = TripPlan(**plan_dict)
                conn.close()
            except Exception as e:
                print(f"⚠️  Warning: Could not load existing trip plan: {e}")
                # Continue without existing plan
        
        # Create TripRequest from chat prompt
        # If updating, preserve destination and other details from existing plan
        trip_request = TripRequest(
            prompt=request.prompt,
            user_id=request.user_id,
            selected_accommodation_id=request.selected_accommodation_id
        )
        
        # Preserve destination and other details from existing plan if updating
        if existing_plan:
            # Get destination from existing plan's request or prompt
            if existing_plan.request:
                if existing_plan.request.destination:
                    trip_request.destination = existing_plan.request.destination
                elif existing_plan.request.prompt:
                    # Try to extract destination from original prompt
                    # Look for location mentions in the original prompt
                    original_prompt = existing_plan.request.prompt
                    # Common patterns: "near [Location]", "in [Location]", "[Location], [State]"
                    location_patterns = [
                        r'near\s+([A-Z][a-zA-Z\s,]+?)(?:\s|,|$)',
                        r'in\s+([A-Z][a-zA-Z\s,]+?)(?:\s|,|$)',
                        r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?),\s*([A-Z]{2}|[A-Z][a-zA-Z]+)'
                    ]
                    for pattern in location_patterns:
                        match = re.search(pattern, original_prompt, re.IGNORECASE)
                        if match:
                            if len(match.groups()) == 2:
                                trip_request.destination = f"{match.group(1)}, {match.group(2)}"
                            else:
                                trip_request.destination = match.group(1).strip().rstrip(',')
                            break
                
                # Preserve other details
                if existing_plan.request.start_date:
                    trip_request.start_date = existing_plan.request.start_date
                if existing_plan.request.duration_days:
                    trip_request.duration_days = existing_plan.request.duration_days
                if existing_plan.request.travelers:
                    trip_request.travelers = existing_plan.request.travelers
            
            # If still no destination, try to get it from selected accommodation
            if not trip_request.destination and existing_plan.selected_accommodation:
                acc = existing_plan.selected_accommodation
                if acc.address:
                    # Extract city/state from address
                    address_parts = acc.address.split(',')
                    if len(address_parts) >= 2:
                        city = address_parts[-2].strip()
                        state = address_parts[-1].strip()
                        trip_request.destination = f"{city}, {state}"
                    else:
                        trip_request.destination = acc.address
        
        # Run all agents through orchestrator (same as test_all_agents_flow.py)
        plan = await orchestrator.plan_trip(trip_request, user_profile)
        
        # Set trip_id in the plan
        plan.trip_id = trip_id
        
        # Store trip plan in database
        _save_trip_plan_to_db(request.user_id, trip_id, plan, is_update)
        
        # Generate chat-friendly message
        message = _generate_chat_message(plan, is_update)
        
        return ChatResponse(
            trip_id=trip_id,
            message=message,
            trip_plan=plan,
            status="updated" if is_update else "new"
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Error in chat_plan_trip: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error planning trip: {str(e)}")


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


@trip_router.get("/chat/{user_id}/{trip_id}", response_model=TripPlan)
async def get_chat_trip_plan(user_id: str, trip_id: str):
    """
    Get trip plan by trip_id for chat interface
    
    Args:
        user_id: User ID
        trip_id: Trip ID
        
    Returns:
        TripPlan with complete trip details
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT itinerary FROM itineraries 
            WHERE trip_id = ?
            """,
            (trip_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Trip plan not found for user_id={user_id}, trip_id={trip_id}"
            )
        
        # Parse JSON and return TripPlan
        plan_dict = json.loads(result['itinerary'])
        return TripPlan(**plan_dict)
    finally:
        conn.close()


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


# Helper functions for chat endpoint
def _save_trip_plan_to_db(user_id: str, trip_id: str, plan: TripPlan, is_update: bool):
    """Save trip plan to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Convert TripPlan to JSON
        plan_json = json.dumps(plan.model_dump(), default=str)
        
        # Check if itinerary exists
        cursor.execute(
            """
            SELECT itinerary FROM itineraries 
            WHERE user_id = ? AND trip_id = ?
            """,
            (user_id, trip_id)
        )
        exists = cursor.fetchone()
        
        if exists:
            # Update existing itinerary
            cursor.execute(
                """
                UPDATE itineraries 
                SET itinerary = ? 
                WHERE user_id = ? AND trip_id = ?
                """,
                (plan_json, user_id, trip_id)
            )
            
            # Get current version number
            cursor.execute(
                """
                SELECT MAX(version_number) as max_version 
                FROM itinerary_versions 
                WHERE user_id = ? AND trip_id = ?
                """,
                (user_id, trip_id)
            )
            result = cursor.fetchone()
            if result and result['max_version'] is not None:
                next_version = result['max_version'] + 1
            else:
                # No versions yet, start with version 2 (version 1 should exist from initial creation)
                next_version = 2
            
            # Insert new version
            cursor.execute(
                """
                INSERT INTO itinerary_versions (user_id, trip_id, version_number, modified_by, itinerary, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, trip_id, next_version, user_id, plan_json, datetime.now().isoformat())
            )
        else:
            # Insert new itinerary
            cursor.execute(
                """
                INSERT INTO itineraries (user_id, trip_id, itinerary)
                VALUES (?, ?, ?)
                """,
                (user_id, trip_id, plan_json)
            )
            
            # Insert version 1
            cursor.execute(
                """
                INSERT INTO itinerary_versions (user_id, trip_id, version_number, modified_by, itinerary, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, trip_id, 1, user_id, plan_json, datetime.now().isoformat())
            )
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Database error in _save_trip_plan_to_db: {error_trace}")
        raise RuntimeError(f"Database error saving trip plan: {str(e)}") from e
    finally:
        conn.close()


def _generate_chat_message(plan: TripPlan, is_update: bool) -> str:
    """Generate a chat-friendly message summarizing the trip plan"""
    if is_update:
        message = "✅ Trip plan updated! "
    else:
        message = "🎉 Your trip plan is ready! "
    
    # Add summary
    if plan.selected_accommodation:
        message += f"\n\n🏨 **Accommodation:** {plan.selected_accommodation.title}"
    
    if plan.restaurants:
        message += f"\n🍽️ **Restaurants:** {len(plan.restaurants)} recommendations"
    
    if plan.transportation:
        message += f"\n✈️ **Transportation:** {len(plan.transportation)} options"
    
    if plan.experiences:
        message += f"\n🎯 **Experiences:** {len(plan.experiences)} activities"
    
    if plan.budget:
        message += f"\n💰 **Total Budget:** ${plan.budget.total:.2f}"
    
    if plan.itinerary:
        message += f"\n📅 **Itinerary:** {len(plan.itinerary)} days planned"
    
    return message
>>>>>>> Stashed changes
