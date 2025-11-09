"""
Itinerary Service - Handles itinerary generation from prompts and follow-ups
"""

from typing import Dict, Any, Optional
from datetime import date, timedelta, datetime
import re
import json
from shared.types import TripRequest, TripPlan, UserProfile
from agents.stay_agent import StayAgent
from agents.restaurant_agent import RestaurantAgent
from agents.travel_agent import TravelAgent
from agents.experience_agent import ExperienceAgent
from agents.budget_agent import BudgetAgent
from agents.planner_agent import PlannerAgent
from follow_up_handler import FollowUpHandler
from database.db import get_db_connection
from services.user_service import UserService


class ItineraryService:
    """Service for generating and managing itineraries"""
    
    def __init__(self):
        self.stay_agent = None
        self.restaurant_agent = None
        self.travel_agent = None
        self.experience_agent = None
        self.budget_agent = None
        self.planner_agent = None
        self.follow_up_handler = None
        self.user_service = UserService()
    
    async def initialize(self):
        """Initialize all agents"""
        self.stay_agent = StayAgent()
        await self.stay_agent.initialize()
        
        self.restaurant_agent = RestaurantAgent()
        await self.restaurant_agent.initialize()
        
        self.travel_agent = TravelAgent()
        await self.travel_agent.initialize()
        
        self.experience_agent = ExperienceAgent()
        await self.experience_agent.initialize()
        
        self.budget_agent = BudgetAgent()
        await self.budget_agent.initialize()
        
        self.planner_agent = PlannerAgent()
        await self.planner_agent.initialize()
        
        self.follow_up_handler = FollowUpHandler()
        await self.follow_up_handler.initialize()
    
    def extract_trip_details(self, prompt: str) -> Dict[str, Any]:
        """Extract trip details from natural language prompt"""
        details = {
            "destination": None,
            "origin": None,
            "duration": None,
            "start_date": None,
            "travelers": 1,
            "budget": None
        }
        
        prompt_lower = prompt.lower()
        
        # Extract duration
        if 'weekend' in prompt_lower:
            details["duration"] = 2
        else:
            duration_patterns = [
                r'(\d+)\s*[-]?\s*day',
                r'(\d+)\s*[-]?\s*night',
                r'\bweek\b'
            ]
            for pattern in duration_patterns:
                match = re.search(pattern, prompt_lower)
                if match:
                    if 'week' in match.group(0):
                        details["duration"] = 7
                    else:
                        details["duration"] = int(match.group(1))
                    break
        
        # Extract travelers
        travelers_patterns = [
            r'(\d+)\s*(?:people|persons|travelers|guests|adults)',
            r'(\d+)\s*(?:person|traveler|guest|adult)',
            r'solo',
            r'couple',
            r'family'
        ]
        for pattern in travelers_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                if 'solo' in match.group(0):
                    details["travelers"] = 1
                elif 'couple' in match.group(0):
                    details["travelers"] = 2
                elif 'family' in match.group(0):
                    details["travelers"] = 4
                else:
                    details["travelers"] = int(match.group(1))
                break
        
        # Extract budget
        budget_patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*)\s*dollars?',
            r'budget\s*(?:of|is)?\s*\$?(\d+(?:,\d{3})*)',
        ]
        for pattern in budget_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                budget_str = match.group(1).replace(',', '')
                details["budget"] = float(budget_str)
                break
        
        # Extract origin and destination
        from_to_pattern = r'from\s+([A-Z][a-zA-Z\s,]+?)(?:\s+to|\s*,|\s+for|\s+with|$)'
        to_pattern = r'to\s+([A-Z][a-zA-Z\s,]+?)(?:\s+for|\s+with|\s*,|$)'
        
        from_match = re.search(from_to_pattern, prompt, re.IGNORECASE)
        to_match = re.search(to_pattern, prompt, re.IGNORECASE)
        
        if from_match:
            details["origin"] = from_match.group(1).strip().rstrip(',')
        
        if to_match:
            details["destination"] = to_match.group(1).strip().rstrip(',')
        
        # If no "from/to" pattern, extract capitalized location names
        if not details["destination"]:
            words = prompt.split()
            destination_candidates = []
            for i, word in enumerate(words):
                if word[0].isupper() and len(word) > 2:
                    if word.lower() in ['weekend', 'getaway', 'trip', 'vacation', 'holiday']:
                        continue
                    candidate = word
                    if i + 1 < len(words) and words[i + 1][0].isupper() and words[i + 1].lower() not in ['to', 'from', 'for', 'with']:
                        candidate += " " + words[i + 1]
                    destination_candidates.append(candidate)
            
            for candidate in reversed(destination_candidates):
                if candidate != details.get("origin"):
                    details["destination"] = candidate
                    break
        
        return details
    
    async def generate_from_prompt(
        self,
        prompt: str,
        user_id: str,
        user_profile: Optional[UserProfile] = None,
        trip_id: Optional[str] = None
    ) -> TripPlan:
        """Generate itinerary from natural language prompt"""
        # Fetch user data from database if not provided
        if user_profile is None:
            user_profile = self.user_service.to_user_profile(user_id)
            if not user_profile:
                raise ValueError(f"User {user_id} not found in database")
        
        # Get additional user context for agents
        user_context = self.user_service.get_user_context_for_agents(user_id)
        
        # Extract details from prompt
        details = self.extract_trip_details(prompt)
        
        # Check for dietary preferences in prompt (prompt has priority)
        prompt_lower = prompt.lower()
        dietary_prefs = list(user_profile.dietary_preferences) if user_profile.dietary_preferences else []
        
        # Prompt overrides database preferences
        if any(word in prompt_lower for word in ['vegetarian', 'vegan']):
            # Clear existing and use prompt preference
            dietary_prefs = []
            if 'vegan' in prompt_lower:
                dietary_prefs.append('vegan')
            elif 'vegetarian' in prompt_lower:
                dietary_prefs.append('vegetarian')
        elif 'gluten' in prompt_lower and 'gluten-free' not in dietary_prefs:
            dietary_prefs.append('gluten-free')
        
        # Update user profile with dietary preferences (prompt takes priority)
        user_profile.dietary_preferences = dietary_prefs
        
        # Create trip request
        start_date = details.get("start_date") or (date.today() + timedelta(days=30))
        enhanced_prompt = prompt
        if details.get("origin"):
            enhanced_prompt = f"{prompt} (traveling from {details['origin']})"
        
        request = TripRequest(
            prompt=enhanced_prompt,
            user_id=user_id,
            destination=details.get("destination"),
            start_date=start_date,
            duration_days=details.get("duration") or 3,
            travelers=details.get("travelers") or 1,
            budget=details.get("budget") or user_profile.budget
        )
        
        # Store origin for TravelAgent
        request._origin = details.get("origin")
        
        # Run all agents with user data
        # StayAgent: Uses user_profile (disability_needs, budget) + user_context (home_city, etc.)
        stay_results = await self.stay_agent.process(request, user_profile, user_context)
        
        # RestaurantAgent: Uses user_profile (dietary_preferences, disability_needs) + user_context
        restaurant_results = await self.restaurant_agent.process(request, stay_results, user_profile, user_context)
        
        # TravelAgent: Does NOT use user profile (only origin/destination)
        travel_results = await self.travel_agent.process(request, stay_results)
        
        # ExperienceAgent: Uses user_context (occupation, interests) + prompt
        experience_results = await self.experience_agent.process(request, stay_results, user_context)
        
        budget_results = await self.budget_agent.process(request, stay_results, travel_results, experience_results)
        
        # Generate final itinerary
        final_plan = await self.planner_agent.process(
            request, stay_results, restaurant_results, travel_results,
            experience_results, budget_results
        )
        
        # trip_id is required from frontend
        if not trip_id:
            raise ValueError("trip_id is required from frontend")
        
        # Store itinerary in database (creates version 1)
        # itinerary = the generated TripPlan JSON text
        self._save_itinerary(user_id, trip_id, request, final_plan)
        
        # Set trip_id in response
        final_plan.trip_id = trip_id
        
        return final_plan
    
    def _save_itinerary(
        self, 
        user_id: str,
        trip_id: str,
        request: TripRequest, 
        plan: TripPlan
    ):
        """
        Save itinerary to database (creates new version)
        
        Args:
            user_id: User ID (who is creating/modifying)
            trip_id: Trip ID (from frontend)
            request: TripRequest
            plan: TripPlan to save (the generated itinerary text)
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # itinerary = the generated TripPlan JSON text
            itinerary_json = json.dumps(plan.model_dump(), default=str)
            now = datetime.now().isoformat()
            
            # Check if trip exists to determine version number
            cursor.execute(
                "SELECT trip_id FROM itineraries WHERE user_id = ? AND trip_id = ?",
                (user_id, trip_id)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Trip exists - create new version (track who modified)
                cursor.execute(
                    """
                    SELECT MAX(version_number) as max_version 
                    FROM itinerary_versions 
                    WHERE user_id = ? AND trip_id = ?
                    """,
                    (user_id, trip_id)
                )
                result = cursor.fetchone()
                new_version = (result["max_version"] or 0) + 1
                
                # Update main itinerary record with latest version
                cursor.execute(
                    "UPDATE itineraries SET itinerary = ? WHERE user_id = ? AND trip_id = ?",
                    (itinerary_json, user_id, trip_id)
                )
            else:
                # New trip, create initial record
                new_version = 1
                cursor.execute(
                    "INSERT INTO itineraries (user_id, trip_id, itinerary) VALUES (?, ?, ?)",
                    (user_id, trip_id, itinerary_json)
                )
            
            # Save version with modifier tracking
            # modified_by tracks who made this specific modification (can be different from owner)
            modifying_user = user_id  # Default to owner, can be updated if different user modifies
            cursor.execute(
                """
                INSERT INTO itinerary_versions 
                (user_id, trip_id, version_number, modified_by, itinerary, created_at) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, trip_id, new_version, modifying_user, itinerary_json, now)
            )
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _load_itinerary(self, user_id: str, trip_id: str, version: Optional[int] = None) -> Optional[TripPlan]:
        """
        Load itinerary from database
        
        Args:
            user_id: User ID
            trip_id: Trip ID (from frontend)
            version: Version number (if None, loads latest version from itineraries table)
            
        Returns:
            TripPlan or None if not found
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if version is None:
                # Load latest version from itineraries table
                cursor.execute(
                    "SELECT itinerary FROM itineraries WHERE user_id = ? AND trip_id = ?",
                    (user_id, trip_id)
                )
            else:
                # Load specific version from itinerary_versions table
                cursor.execute(
                    """
                    SELECT itinerary 
                    FROM itinerary_versions 
                    WHERE user_id = ? AND trip_id = ? AND version_number = ?
                    """,
                    (user_id, trip_id, version)
                )
            
            row = cursor.fetchone()
            
            if row:
                itinerary_data = json.loads(row["itinerary"])
                plan = TripPlan(**itinerary_data)
                plan.trip_id = trip_id
                return plan
            return None
        finally:
            conn.close()
    
    def _update_itinerary(
        self, 
        user_id: str,
        trip_id: str,
        plan: TripPlan
    ):
        """
        Update itinerary by creating a new version
        
        Args:
            user_id: User ID
            trip_id: Trip ID (from frontend)
            plan: Updated TripPlan (the generated itinerary text)
        """
        # Verify itinerary exists
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT user_id FROM itineraries WHERE user_id = ? AND trip_id = ?",
                (user_id, trip_id)
            )
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"Itinerary not found for user_id={user_id}, trip_id={trip_id}")
            
            # Create a dummy TripRequest (not stored in new schema)
            destination = plan.request.destination if plan.request else None
            request = TripRequest(
                prompt="",
                user_id=user_id,
                destination=destination
            )
            
            # Save as new version
            self._save_itinerary(
                user_id=user_id,
                trip_id=trip_id,
                request=request,
                plan=plan
            )
        finally:
            conn.close()
    
    async def handle_follow_up(
        self,
        user_id: str,
        trip_id: str,
        prompt: str,
        modifying_user_id: Optional[str] = None,
        user_profile: Optional[UserProfile] = None
    ) -> Dict[str, Any]:
        """
        Handle follow-up prompt for an existing itinerary
        
        Args:
            user_id: User ID who owns the itinerary
            trip_id: Trip ID (from frontend)
            prompt: User's follow-up prompt
            modifying_user_id: User ID who is making the modification (can be different from owner)
            user_profile: Optional user profile
        """
        itinerary = self._load_itinerary(user_id, trip_id)
        if not itinerary:
            raise ValueError(f"Itinerary not found for user_id={user_id}, trip_id={trip_id}")
        
        # Use modifying_user_id if provided, otherwise use user_id
        modifier = modifying_user_id if modifying_user_id else user_id
        
        # Fetch user profile from database if not provided
        if user_profile is None and modifier:
            user_profile = self.user_service.to_user_profile(modifier)
        
        result = await self.follow_up_handler.handle_follow_up(prompt, itinerary, user_profile)
        
        # Update stored itinerary if modified (creates new version)
        if result["type"] == "modification" and result.get("itinerary"):
            # Save new version with correct modifier
            updated_plan = result["itinerary"]
            destination = updated_plan.request.destination if updated_plan.request else None
            self._save_itinerary_with_modifier(
                user_id=user_id,
                trip_id=trip_id,
                request=TripRequest(prompt="", user_id=user_id, destination=destination),
                plan=updated_plan,
                modified_by=modifier
            )
        
        return result
    
    def _save_itinerary_with_modifier(
        self, 
        user_id: str,
        trip_id: str,
        request: TripRequest, 
        plan: TripPlan,
        modified_by: str
    ):
        """
        Save itinerary with specific modifier (for collaborative edits)
        
        Args:
            user_id: User ID who owns the itinerary
            trip_id: Trip ID (from frontend)
            request: TripRequest
            plan: TripPlan to save
            modified_by: User ID who made this modification
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            itinerary_json = json.dumps(plan.model_dump(), default=str)
            now = datetime.now().isoformat()
            
            # Get next version number
            cursor.execute(
                """
                SELECT MAX(version_number) as max_version 
                FROM itinerary_versions 
                WHERE user_id = ? AND trip_id = ?
                """,
                (user_id, trip_id)
            )
            result = cursor.fetchone()
            new_version = (result["max_version"] or 0) + 1
            
            # Update main itinerary record with latest version
            cursor.execute(
                "UPDATE itineraries SET itinerary = ? WHERE user_id = ? AND trip_id = ?",
                (itinerary_json, user_id, trip_id)
            )
            
            # Save version with specific modifier
            cursor.execute(
                """
                INSERT INTO itinerary_versions 
                (user_id, trip_id, version_number, modified_by, itinerary, created_at) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, trip_id, new_version, modified_by, itinerary_json, now)
            )
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_itinerary(self, user_id: str, trip_id: str, version: Optional[int] = None) -> Optional[TripPlan]:
        """
        Get stored itinerary by user_id and trip_id
        
        Args:
            user_id: User ID
            trip_id: Trip ID (from frontend)
            version: Version number (if None, returns latest version)
            
        Returns:
            TripPlan or None if not found
        """
        return self._load_itinerary(user_id, trip_id, version)
    
    def get_itinerary_versions(self, user_id: str, trip_id: str) -> list:
        """
        Get all versions of an itinerary with modification history
        
        Args:
            user_id: User ID
            trip_id: Trip ID (from frontend)
            
        Returns:
            List of version info including who made each modification
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                SELECT version_number, modified_by, created_at 
                FROM itinerary_versions 
                WHERE user_id = ? AND trip_id = ?
                ORDER BY version_number ASC
                """,
                (user_id, trip_id)
            )
            rows = cursor.fetchall()
            
            return [
                {
                    "version": row["version_number"],
                    "modified_by": row["modified_by"],
                    "created_at": row["created_at"]
                }
                for row in rows
            ]
        finally:
            conn.close()
    
    def list_itineraries(self, user_id: str) -> list:
        """List all itineraries for a user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT trip_id, itinerary FROM itineraries WHERE user_id = ?",
                (user_id,)
            )
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                # Parse itinerary to get basic info
                try:
                    itinerary_data = json.loads(row["itinerary"])
                    result.append({
                        "trip_id": row["trip_id"],
                        "destination": itinerary_data.get("destination"),
                        "status": itinerary_data.get("status", "draft")
                    })
                except:
                    result.append({
                        "trip_id": row["trip_id"],
                        "destination": None,
                        "status": "unknown"
                    })
            
            return result
        finally:
            conn.close()

