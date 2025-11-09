"""
API routes for TripMind
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from shared.types import TripRequest, TripPlan
from services.orchestrator import TripOrchestrator
import os
import json

trip_router = APIRouter()

# Global orchestrator instance (will be set by main.py)
orchestrator: TripOrchestrator = None

# In-memory storage for trips and messages (in production, use a database)
trips_storage: Dict[str, Dict] = {}
messages_storage: Dict[str, List[Dict]] = {}
shared_users_storage: Dict[str, List[Dict]] = {}


# Pydantic models for chat
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str


class ChatRequest(BaseModel):
    userId: str
    tripId: str
    message: str
    systemPrompt: Optional[str] = None
    conversationHistory: Optional[List[Dict]] = None
    timestamp: Optional[str] = None
    isInitialPlan: Optional[bool] = False


class MessageRequest(BaseModel):
    userId: str
    tripId: str
    message: Dict[str, Any]
    timestamp: str


class InviteRequest(BaseModel):
    userId: str
    tripId: str
    inviteEmail: str


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


# Chat endpoints for trip-planner API
chat_router = APIRouter()


@chat_router.post("/trips/{tripId}/chat")
async def chat_with_trip(tripId: str, request: ChatRequest):
    """
    Chat with AI about a trip using Google Gemini
    """
    try:
        import google.generativeai as genai
        
        # Get Gemini API key
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY or GOOGLE_API_KEY not configured. Get your key from: https://makersuite.google.com/app/apikey")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Initialize the model
        model = genai.GenerativeModel('gemini-pro')
        
        # Build the full prompt with system prompt and conversation history
        full_prompt_parts = []
        
        # Add system prompt if provided
        if request.systemPrompt:
            full_prompt_parts.append(request.systemPrompt)
        
        # Add conversation history if provided
        if request.conversationHistory and len(request.conversationHistory) > 0:
            conversation_text = "\n\n".join([
                f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}"
                for msg in request.conversationHistory
                if msg.get('role') in ['user', 'assistant']
            ])
            full_prompt_parts.append(conversation_text)
        
        # Add the current user message
        full_prompt_parts.append(f"User: {request.message}\n\nAssistant:")
        
        # Combine all parts
        full_prompt = "\n\n".join(full_prompt_parts)
        
        # Call Gemini API
        generation_config = {
            "temperature": 0.7,
            "max_output_tokens": 2000,
        }
        response = model.generate_content(
            full_prompt,
            generation_config=generation_config
        )
        
        ai_response = response.text
        
        return {
            "response": ai_response,
            "message": ai_response,
            "plan": ai_response if request.isInitialPlan else None
        }
        
    except ImportError:
        raise HTTPException(status_code=500, detail="Google Generative AI library not installed. Run: pip install google-generativeai")
    except Exception as e:
        error_msg = str(e)
        if "API_KEY" in error_msg or "api key" in error_msg.lower():
            error_msg = "GEMINI_API_KEY not configured. Get your key from: https://makersuite.google.com/app/apikey"
        raise HTTPException(status_code=500, detail=f"Error calling Gemini AI: {error_msg}")


@chat_router.post("/trips/{tripId}/messages")
async def save_message(tripId: str, request: MessageRequest):
    """Save a message to the trip chat"""
    if tripId not in messages_storage:
        messages_storage[tripId] = []
    
    messages_storage[tripId].append(request.message)
    return {"status": "saved", "message": "Message saved successfully"}


@chat_router.get("/trips/{tripId}/messages")
async def get_messages(tripId: str, userId: str = Query(...)):
    """Get all messages for a trip"""
    messages = messages_storage.get(tripId, [])
    return {"messages": messages}


@chat_router.get("/trips/{tripId}")
async def get_trip(tripId: str, userId: str = Query(...)):
    """Get trip information"""
    trip = trips_storage.get(tripId, {})
    return trip if trip else {"id": tripId, "title": f"Trip {tripId}", "destination": "Unknown"}


@chat_router.get("/trips")
async def list_trips(userId: str = Query(...)):
    """List all trips for a user"""
    user_trips = [trip for trip in trips_storage.values() if trip.get("userId") == userId]
    return {"trips": user_trips}


@chat_router.post("/trips/{tripId}/invite")
async def invite_user(tripId: str, request: InviteRequest):
    """Invite a user to view a trip chat"""
    if tripId not in shared_users_storage:
        shared_users_storage[tripId] = []
    
    shared_users_storage[tripId].append({
        "email": request.inviteEmail,
        "status": "invited",
        "invitedBy": request.userId
    })
    
    return {"status": "invited", "message": f"User {request.inviteEmail} has been invited"}


@chat_router.get("/trips/{tripId}/shared-users")
async def get_shared_users(tripId: str, userId: str = Query(...)):
    """Get list of users who can view this trip"""
    shared_users = shared_users_storage.get(tripId, [])
    return {"sharedUsers": shared_users}


@chat_router.post("")
async def create_trip(request: Dict[str, Any] = Body(...)):
    """Create a new trip (from SearchBar)"""
    trip_id = request.get("tripId")
    if trip_id:
        trips_storage[trip_id] = {
            "id": trip_id,
            "userId": request.get("userId", "Kartik7"),
            "prompt": request.get("prompt", ""),
            "timestamp": request.get("timestamp", ""),
            "title": request.get("title", f"Trip {trip_id}"),
            "destination": request.get("destination", "Unknown")
        }
        return {"status": "created", "tripId": trip_id, "message": "Trip created successfully"}
    return {"status": "error", "message": "tripId is required"}

