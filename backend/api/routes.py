"""
API routes for TripMind
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from shared.types import TripRequest, TripPlan
from services.orchestrator import TripOrchestrator
from database.db import get_db_connection
from datetime import datetime
import os
import json
import uuid
import re

trip_router = APIRouter()

# Global orchestrator instance (will be set by main.py)
orchestrator: TripOrchestrator = None

# In-memory storage for trips (legacy, will migrate to database)
trips_storage: Dict[str, Dict] = {}


# Pydantic models for chat
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str


class ChatRequest(BaseModel):
    """Request model for chat_plan_trip endpoint (runs all agents)"""
    prompt: str
    user_id: str
    trip_id: Optional[str] = None
    selected_accommodation_id: Optional[str] = None


class ChatRequestSimple(BaseModel):
    """Request model for simple chat endpoint (just Gemini conversation)"""
    userId: str
    tripId: str
    message: str
    systemPrompt: Optional[str] = None
    conversationHistory: Optional[List[Dict]] = None
    timestamp: Optional[str] = None
    isInitialPlan: Optional[bool] = False


class ChatResponse(BaseModel):
    """Response model for chat_plan_trip endpoint"""
    trip_id: str
    message: str
    trip_plan: TripPlan
    status: str  # "new" or "updated"


class MessageRequest(BaseModel):
    userId: str
    tripId: str
    message: Dict[str, Any]
    timestamp: str


class InviteRequest(BaseModel):
    userId: str
    tripId: str
    inviteEmail: str


def _user_has_access_to_trip(cursor, user_id: str, trip_id: str) -> bool:
    """
    Check if a user has access to a trip
    Users have access if:
    1. They are the owner (trip exists in itineraries with their user_id)
    2. They have been invited (entry exists in shared_trips)
    """
    # Check if user is the owner
    cursor.execute(
        """
        SELECT user_id FROM itineraries 
        WHERE trip_id = ? AND user_id = ?
        """,
        (trip_id, user_id)
    )
    if cursor.fetchone():
        return True
    
    # Check if user has been invited
    cursor.execute(
        """
        SELECT shared_user_id FROM shared_trips 
        WHERE trip_id = ? AND shared_user_id = ?
        """,
        (trip_id, user_id)
    )
    if cursor.fetchone():
        return True
    
    return False


def _ensure_trip_owner_access(cursor, user_id: str, trip_id: str):
    """
    Ensure the trip owner has access in shared_trips table
    This is called when a trip is created
    """
    # Check if owner entry already exists
    cursor.execute(
        """
        SELECT owner_user_id FROM shared_trips 
        WHERE trip_id = ? AND owner_user_id = ? AND shared_user_id = ?
        """,
        (trip_id, user_id, user_id)
    )
    if not cursor.fetchone():
        # Add owner as having access to their own trip
        cursor.execute(
            """
            INSERT OR IGNORE INTO shared_trips 
            (trip_id, owner_user_id, shared_user_id, permission, invited_at, accepted_at)
            VALUES (?, ?, ?, 'view_edit', datetime('now'), datetime('now'))
            """,
            (trip_id, user_id, user_id)
        )


def _save_trip_plan_to_db(user_id: str, trip_id: str, plan: TripPlan, is_update: bool):
    """Save trip plan to database and ensure owner has access"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the latest version number
        cursor.execute(
            """
            SELECT MAX(version_number) as max_version 
            FROM itinerary_versions 
            WHERE user_id = ? AND trip_id = ?
            """,
            (user_id, trip_id)
        )
        result = cursor.fetchone()
        version_number = (result['max_version'] or 0) + 1 if result else 1
        
        # Save to itineraries table (latest version)
        plan_json = json.dumps(plan.model_dump(), default=str)
        cursor.execute(
            """
            INSERT OR REPLACE INTO itineraries (user_id, trip_id, itinerary, created_at, updated_at)
            VALUES (?, ?, ?, datetime('now'), datetime('now'))
            """,
            (user_id, trip_id, plan_json)
        )
        
        # Save to itinerary_versions table
        cursor.execute(
            """
            INSERT INTO itinerary_versions (user_id, trip_id, version_number, modified_by, itinerary, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (user_id, trip_id, version_number, user_id, plan_json)
        )
        
        # Ensure owner has access to their trip
        _ensure_trip_owner_access(cursor, user_id, trip_id)
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️  Error saving trip plan to database: {e}")
        import traceback
        traceback.print_exc()
        # Don't raise - allow the API to continue even if DB save fails


def _generate_chat_message(plan: TripPlan, is_update: bool) -> str:
    """Generate a detailed chat-friendly message from the trip plan showing all model outputs"""
    message_parts = []
    
    if is_update:
        message_parts.append("✅ Your trip plan has been updated!")
    else:
        message_parts.append("🎉 Your trip plan is ready!")
    
    message_parts.append("")  # Empty line
    message_parts.append("=" * 60)
    message_parts.append("📋 COMPLETE TRIP PLAN DETAILS")
    message_parts.append("=" * 60)
    message_parts.append("")
    
    # ========== ACCOMMODATIONS ==========
    message_parts.append("🏨 **ACCOMMODATIONS**")
    message_parts.append("-" * 60)
    if plan.accommodations and len(plan.accommodations) > 0:
        for i, acc in enumerate(plan.accommodations, 1):
            message_parts.append(f"\n{i}. **{acc.title}**")
            if acc.description:
                message_parts.append(f"   📝 {acc.description}")
            if acc.address:
                message_parts.append(f"   📍 {acc.address}")
            if acc.price_per_night:
                message_parts.append(f"   💰 ${acc.price_per_night:.2f}/night")
            if acc.total_price:
                message_parts.append(f"   💵 Total: ${acc.total_price:.2f}")
            if acc.rating:
                message_parts.append(f"   ⭐ Rating: {acc.rating}/5.0 ({acc.review_count or 0} reviews)")
            if acc.amenities:
                message_parts.append(f"   ✨ Amenities: {', '.join(acc.amenities[:5])}")
            if acc.booking_url:
                message_parts.append(f"   🔗 Book: {acc.booking_url}")
    else:
        message_parts.append("   No accommodations found")
    
    # Selected Accommodation
    if plan.selected_accommodation:
        message_parts.append(f"\n✅ **SELECTED:** {plan.selected_accommodation.title}")
    
    message_parts.append("")
    
    # ========== RESTAURANTS ==========
    message_parts.append("🍽️ **RESTAURANTS & CAFES**")
    message_parts.append("-" * 60)
    if plan.restaurants and len(plan.restaurants) > 0:
        for i, rest in enumerate(plan.restaurants, 1):
            message_parts.append(f"\n{i}. **{rest.name}**")
            if rest.description:
                message_parts.append(f"   📝 {rest.description}")
            if rest.cuisine_type:
                message_parts.append(f"   🍴 Cuisine: {rest.cuisine_type}")
            if rest.address:
                message_parts.append(f"   📍 {rest.address}")
            if rest.price_range:
                message_parts.append(f"   💰 Price: {rest.price_range}")
            if rest.average_price_per_person:
                message_parts.append(f"   💵 Avg per person: ${rest.average_price_per_person:.2f}")
            if rest.rating:
                message_parts.append(f"   ⭐ Rating: {rest.rating}/5.0 ({rest.review_count or 0} reviews)")
            if rest.dietary_options:
                message_parts.append(f"   🌱 Dietary: {', '.join(rest.dietary_options)}")
            if rest.accessibility_features:
                message_parts.append(f"   ♿ Accessibility: {', '.join(rest.accessibility_features)}")
            if rest.booking_url:
                message_parts.append(f"   🔗 Reserve: {rest.booking_url}")
    else:
        message_parts.append("   No restaurants found")
    
    message_parts.append("")
    
    # ========== TRANSPORTATION ==========
    message_parts.append("✈️ **TRANSPORTATION OPTIONS**")
    message_parts.append("-" * 60)
    if plan.transportation and len(plan.transportation) > 0:
        for i, trans in enumerate(plan.transportation, 1):
            message_parts.append(f"\n{i}. **{trans.type.upper()}** - {trans.provider or 'N/A'}")
            if trans.origin and trans.destination:
                message_parts.append(f"   🗺️  Route: {trans.origin} → {trans.destination}")
            if trans.price:
                message_parts.append(f"   💰 Price: ${trans.price:.2f}")
            if trans.price_per_person:
                message_parts.append(f"   💵 Per person: ${trans.price_per_person:.2f}")
            if trans.duration_minutes:
                hours = trans.duration_minutes // 60
                mins = trans.duration_minutes % 60
                message_parts.append(f"   ⏱️  Duration: {hours}h {mins}m")
            if trans.transfers is not None:
                message_parts.append(f"   🔄 Transfers: {trans.transfers}")
            if trans.recommended:
                message_parts.append(f"   ✅ **RECOMMENDED**")
            if trans.booking_url:
                message_parts.append(f"   🔗 Book: {trans.booking_url}")
    else:
        message_parts.append("   No transportation options found")
    
    message_parts.append("")
    
    # ========== EXPERIENCES ==========
    message_parts.append("🎯 **EXPERIENCES & ACTIVITIES**")
    message_parts.append("-" * 60)
    if plan.experiences and len(plan.experiences) > 0:
        for i, exp in enumerate(plan.experiences, 1):
            message_parts.append(f"\n{i}. **{exp.name}**")
            if exp.description:
                message_parts.append(f"   📝 {exp.description}")
            if exp.category:
                message_parts.append(f"   🏷️  Category: {exp.category}")
            if exp.address:
                message_parts.append(f"   📍 {exp.address}")
            if exp.price is not None:
                if exp.price == 0:
                    message_parts.append(f"   💰 Free")
                else:
                    message_parts.append(f"   💰 Price: ${exp.price:.2f}")
            if exp.duration_hours:
                message_parts.append(f"   ⏱️  Duration: {exp.duration_hours} hours")
            if exp.rating:
                message_parts.append(f"   ⭐ Rating: {exp.rating}/5.0 ({exp.review_count or 0} reviews)")
            if exp.booking_url and exp.booking_url != "N/A":
                message_parts.append(f"   🔗 Book: {exp.booking_url}")
    else:
        message_parts.append("   No experiences found")
    
    message_parts.append("")
    
    # ========== BUDGET ==========
    message_parts.append("💰 **BUDGET BREAKDOWN**")
    message_parts.append("-" * 60)
    if plan.budget:
        budget = plan.budget
        if budget.accommodation:
            message_parts.append(f"   🏨 Accommodation: ${budget.accommodation:.2f}")
        if budget.transportation:
            message_parts.append(f"   ✈️  Transportation: ${budget.transportation:.2f}")
        if budget.experiences:
            message_parts.append(f"   🎯 Experiences: ${budget.experiences:.2f}")
        if budget.meals:
            message_parts.append(f"   🍽️  Meals: ${budget.meals:.2f}")
        if budget.miscellaneous:
            message_parts.append(f"   🛍️  Miscellaneous: ${budget.miscellaneous:.2f}")
        if budget.total:
            message_parts.append(f"\n   💵 **TOTAL: ${budget.total:.2f} {budget.currency}**")
    else:
        message_parts.append("   Budget not calculated")
    
    message_parts.append("")
    
    # ========== ITINERARY ==========
    message_parts.append("📅 **DAY-BY-DAY ITINERARY**")
    message_parts.append("-" * 60)
    if plan.itinerary and len(plan.itinerary) > 0:
        for day_plan in plan.itinerary:
            message_parts.append(f"\n**Day {day_plan.day}** ({day_plan.date})")
            
            # Activities
            if day_plan.activities and len(day_plan.activities) > 0:
                message_parts.append("   🎯 Activities:")
                for activity in day_plan.activities:
                    time_str = activity.get('time', 'TBD') if isinstance(activity, dict) else getattr(activity, 'time', 'TBD')
                    title = activity.get('title', 'Activity') if isinstance(activity, dict) else getattr(activity, 'title', 'Activity')
                    desc = activity.get('description', '') if isinstance(activity, dict) else getattr(activity, 'description', '')
                    location = activity.get('location', '') if isinstance(activity, dict) else getattr(activity, 'location', '')
                    message_parts.append(f"      ⏰ {time_str}: {title}")
                    if desc:
                        message_parts.append(f"         {desc}")
                    if location:
                        message_parts.append(f"         📍 {location}")
            
            # Meals
            if day_plan.meals and len(day_plan.meals) > 0:
                message_parts.append("   🍽️  Meals:")
                for meal in day_plan.meals:
                    time_str = meal.get('time', 'TBD') if isinstance(meal, dict) else getattr(meal, 'time', 'TBD')
                    meal_type = meal.get('type', 'meal') if isinstance(meal, dict) else getattr(meal, 'type', 'meal')
                    restaurant = meal.get('restaurant', '') if isinstance(meal, dict) else getattr(meal, 'restaurant', '')
                    desc = meal.get('description', '') if isinstance(meal, dict) else getattr(meal, 'description', '')
                    message_parts.append(f"      ⏰ {time_str} ({meal_type}): {restaurant}")
                    if desc:
                        message_parts.append(f"         {desc}")
            
            # Notes
            if day_plan.notes:
                notes = day_plan.notes if isinstance(day_plan.notes, str) else str(day_plan.notes)
                if notes and notes.strip():
                    message_parts.append(f"   💡 Notes: {notes}")
    else:
        message_parts.append("   Itinerary not generated")
    
    message_parts.append("")
    message_parts.append("=" * 60)
    message_parts.append("✅ All model outputs displayed above")
    message_parts.append("=" * 60)
    
    return "\n".join(message_parts)


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
    print("\n" + "="*80)
    print("📨 NEW CHAT REQUEST RECEIVED")
    print("="*80)
    print(f"👤 User ID: {request.user_id}")
    print(f"🆔 Trip ID: {request.trip_id or 'NEW TRIP'}")
    print(f"💬 Prompt: {request.prompt[:100]}{'...' if len(request.prompt) > 100 else ''}")
    print("="*80)
    
    if orchestrator is None:
        print("❌ ERROR: Orchestrator not initialized")
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        # Get user profile
        print(f"🔍 Fetching user profile for: {request.user_id}")
        user_profile = orchestrator.get_user_profile(request.user_id)
        if not user_profile:
            print(f"❌ ERROR: User profile not found for: {request.user_id}")
            raise HTTPException(
                status_code=404,
                detail=f"User profile not found for user_id: {request.user_id}. Please create a profile first."
            )
        print(f"✅ User profile found: {user_profile.name} (Budget: ${user_profile.budget or 'N/A'})")
        
        # Generate or get trip_id
        trip_id = request.trip_id or str(uuid.uuid4())
        is_update = request.trip_id is not None
        print(f"🆔 Using Trip ID: {trip_id} ({'UPDATE' if is_update else 'NEW'})")
        
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
        
        # Run all agents through orchestrator (optimized with parallel execution)
        print(f"\n🤖 Starting AI Agent Workflow (Optimized)...")
        print(f"   Flow: StayAgent → [RestaurantAgent, TravelAgent, ExperienceAgent in parallel] → BudgetAgent → PlannerAgent")
        print(f"   ⚡ Parallel execution enabled for faster results!")
        print(f"   This may take 1-3 minutes...\n")
        
        plan = await orchestrator.plan_trip(trip_request, user_profile)
        
        # Set trip_id in the plan
        plan.trip_id = trip_id
        
        print(f"\n✅ All agents completed successfully!")
        print(f"   🏨 Accommodations: {len(plan.accommodations) if plan.accommodations else 0}")
        print(f"   🍽️  Restaurants: {len(plan.restaurants) if plan.restaurants else 0}")
        print(f"   ✈️  Transportation: {len(plan.transportation) if plan.transportation else 0}")
        print(f"   🎯 Experiences: {len(plan.experiences) if plan.experiences else 0}")
        print(f"   📅 Itinerary Days: {len(plan.itinerary) if plan.itinerary else 0}")
        if plan.budget and plan.budget.total:
            print(f"   💰 Total Budget: ${plan.budget.total:.2f} {plan.budget.currency}")
        
        # Store trip plan in database (this also ensures owner has access)
        print(f"\n💾 Saving trip plan to database...")
        _save_trip_plan_to_db(request.user_id, trip_id, plan, is_update)
        print(f"✅ Trip plan saved successfully!")
        
        # Generate chat-friendly message
        message = _generate_chat_message(plan, is_update)
        
        # Save user's prompt and AI response to chat history
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Save user message
            user_message_timestamp = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT INTO chat_messages (trip_id, user_id, role, content, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    trip_id,
                    request.user_id,
                    "user",
                    request.prompt,
                    user_message_timestamp
                )
            )
            
            # Save assistant message with trip plan
            assistant_message_timestamp = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT INTO chat_messages (trip_id, user_id, role, content, trip_plan, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    trip_id,
                    request.user_id,
                    "assistant",
                    message,
                    json.dumps(plan.model_dump(), default=str),
                    assistant_message_timestamp
                )
            )
            
            conn.commit()
            conn.close()
            print(f"💾 Saved chat messages to database (user prompt + AI response)")
        except Exception as e:
            print(f"⚠️  Warning: Could not save chat messages: {e}")
            import traceback
            traceback.print_exc()
            # Don't fail the request if chat save fails
        
        print(f"\n📤 Sending response to client...")
        print("="*80)
        print("✅ REQUEST COMPLETED SUCCESSFULLY\n")
        
        return ChatResponse(
            trip_id=trip_id,
            message=message,
            trip_plan=plan,
            status="updated" if is_update else "new"
        )
    except HTTPException:
        print("="*80)
        print("❌ REQUEST FAILED (HTTPException)\n")
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print("\n" + "="*80)
        print("❌ ERROR IN CHAT_PLAN_TRIP")
        print("="*80)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("\nFull Traceback:")
        print(error_details)
        print("="*80 + "\n")
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


# Chat endpoints for trip-planner API
chat_router = APIRouter()


@chat_router.post("/trips/{tripId}/chat")
async def chat_with_trip(tripId: str, request: ChatRequestSimple):
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
    """
    Save a message to the trip chat in the database
    Messages are saved permanently so all shared users can view the full conversation
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user has access to this trip
        if not _user_has_access_to_trip(cursor, request.userId, tripId):
            conn.close()
            raise HTTPException(
                status_code=403,
                detail="You don't have access to this trip. Please request access from the trip owner."
            )
        
        # Prepare message data
        message = request.message
        trip_plan_json = None
        if message.get("trip_plan"):
            trip_plan_json = json.dumps(message.get("trip_plan"), default=str)
        
        # Save message to database
        cursor.execute(
            """
            INSERT INTO chat_messages (trip_id, user_id, role, content, trip_plan, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                tripId,
                request.userId,
                message.get("role", "user"),
                message.get("content", ""),
                trip_plan_json,
                message.get("timestamp", datetime.now().isoformat())
            )
        )
        
        conn.commit()
        conn.close()
        
        print(f"💾 Saved message to database: trip_id={tripId}, user_id={request.userId}, role={message.get('role')}")
        
        return {"status": "saved", "message": "Message saved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error saving message: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error saving message: {str(e)}")


@chat_router.get("/trips/{tripId}/messages")
async def get_messages(tripId: str, userId: str = Query(...)):
    """
    Get all messages for a trip from the database
    Only users with access to the trip can view messages
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user has access to this trip
        # First, check if trip exists (might be a new trip)
        cursor.execute(
            """
            SELECT user_id FROM itineraries WHERE trip_id = ?
            """,
            (tripId,)
        )
        trip_exists = cursor.fetchone()
        
        # If trip doesn't exist yet, allow access (for new trips)
        if not trip_exists:
            conn.close()
            print(f"⚠️  Trip {tripId} doesn't exist yet, returning empty messages")
            return {"messages": []}
        
        # If trip exists, check access
        if not _user_has_access_to_trip(cursor, userId, tripId):
            conn.close()
            raise HTTPException(
                status_code=403,
                detail="You don't have access to this trip. Please request access from the trip owner."
            )
        
        # Fetch all messages for this trip, ordered by timestamp
        cursor.execute(
            """
            SELECT id, user_id, role, content, trip_plan, timestamp, created_at
            FROM chat_messages
            WHERE trip_id = ?
            ORDER BY timestamp ASC
            """,
            (tripId,)
        )
        
        rows = cursor.fetchall()
        messages = []
        
        for row in rows:
            message = {
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "timestamp": row["timestamp"],
            }
            
            # Parse trip_plan if present
            if row["trip_plan"]:
                try:
                    message["trip_plan"] = json.loads(row["trip_plan"])
                except:
                    pass
            
            messages.append(message)
        
        conn.close()
        
        print(f"📤 Retrieved {len(messages)} messages for trip_id={tripId}, user_id={userId}")
        
        return {"messages": messages}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error retrieving messages: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")


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
    """
    Invite a user to view and edit a trip chat
    The invited user will be able to see all chat history and make changes
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify that the requesting user is the owner
        # First check in shared_trips
        cursor.execute(
            """
            SELECT owner_user_id FROM shared_trips 
            WHERE trip_id = ? AND owner_user_id = ? AND shared_user_id = ?
            """,
            (tripId, request.userId, request.userId)
        )
        owner_row = cursor.fetchone()
        
        # If not found, check in itineraries table
        if not owner_row:
            cursor.execute(
                """
                SELECT user_id FROM itineraries WHERE trip_id = ? AND user_id = ?
                """,
                (tripId, request.userId)
            )
            owner_row = cursor.fetchone()
        
        if not owner_row:
            conn.close()
            raise HTTPException(
                status_code=403,
                detail="Only the trip owner can invite users"
            )
        
        # Find user by email to get their user_id
        cursor.execute(
            """
            SELECT user_id, email FROM users WHERE email = ?
            """,
            (request.inviteEmail,)
        )
        user_row = cursor.fetchone()
        
        if not user_row:
            conn.close()
            raise HTTPException(
                status_code=404,
                detail=f"User with email {request.inviteEmail} not found. They need to create an account first."
            )
        
        shared_user_id = user_row["user_id"]
        
        # Check if user is already invited
        cursor.execute(
            """
            SELECT shared_user_id FROM shared_trips 
            WHERE trip_id = ? AND shared_user_id = ?
            """,
            (tripId, shared_user_id)
        )
        if cursor.fetchone():
            conn.close()
            return {
                "status": "already_invited",
                "message": f"User {request.inviteEmail} already has access to this trip"
            }
        
        # Add user to shared_trips
        cursor.execute(
            """
            INSERT INTO shared_trips 
            (trip_id, owner_user_id, shared_user_id, shared_user_email, permission, invited_at)
            VALUES (?, ?, ?, ?, 'view_edit', datetime('now'))
            """,
            (tripId, request.userId, shared_user_id, request.inviteEmail)
        )
        
        conn.commit()
        conn.close()
        
        print(f"✅ Invited user {request.inviteEmail} (user_id: {shared_user_id}) to trip {tripId}")
        
        return {
            "status": "invited",
            "message": f"User {request.inviteEmail} has been invited and can now view and edit the trip"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error inviting user: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error inviting user: {str(e)}")


@chat_router.get("/trips/{tripId}/shared-users")
async def get_shared_users(tripId: str, userId: str = Query(...)):
    """
    Get list of users who can view and edit this trip
    Only users with access can see the shared users list
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if requesting user has access
        if not _user_has_access_to_trip(cursor, userId, tripId):
            conn.close()
            raise HTTPException(
                status_code=403,
                detail="You don't have access to this trip"
            )
        
        # Get all shared users for this trip
        cursor.execute(
            """
            SELECT st.shared_user_id, st.shared_user_email, st.permission, st.invited_at, st.accepted_at,
                   u.name, u.email
            FROM shared_trips st
            LEFT JOIN users u ON st.shared_user_id = u.user_id
            WHERE st.trip_id = ?
            ORDER BY st.invited_at ASC
            """,
            (tripId,)
        )
        
        rows = cursor.fetchall()
        shared_users = []
        
        for row in rows:
            shared_users.append({
                "user_id": row["shared_user_id"],
                "email": row["shared_user_email"] or row["email"],
                "name": row["name"],
                "permission": row["permission"],
                "status": "accepted" if row["accepted_at"] else "invited",
                "invited_at": row["invited_at"]
            })
        
        conn.close()
        
        return {"sharedUsers": shared_users}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error retrieving shared users: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving shared users: {str(e)}")


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
