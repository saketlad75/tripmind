"""
Follow-up Handler - Handles user follow-up prompts after itinerary generation
Routes to appropriate agents based on intent
"""

from typing import Dict, Any, Optional
from agents.intent_classifier import IntentClassifier
from agents.qa_agent import QAAgent
from agents.stay_agent import StayAgent
from agents.restaurant_agent import RestaurantAgent
from agents.travel_agent import TravelAgent
from agents.experience_agent import ExperienceAgent
from agents.planner_agent import PlannerAgent
from shared.types import TripPlan, TripRequest, UserProfile


class FollowUpHandler:
    """Handles follow-up prompts and modifies itinerary or answers questions"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.qa_agent = QAAgent()
        self.stay_agent = None
        self.restaurant_agent = None
        self.travel_agent = None
        self.experience_agent = None
        self.planner_agent = None
    
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
        
        self.planner_agent = PlannerAgent()
        await self.planner_agent.initialize()
        
        await self.qa_agent.initialize()
    
    async def handle_follow_up(
        self,
        prompt: str,
        current_itinerary: TripPlan,
        user_profile: Optional[UserProfile] = None
    ) -> Dict[str, Any]:
        """
        Handle follow-up prompt
        
        Args:
            prompt: User's follow-up prompt
            current_itinerary: Current trip plan
            user_profile: User profile (optional)
            
        Returns:
            {
                "type": "modification" | "answer" | "chat",
                "itinerary": TripPlan (if modified),
                "answer": str (if query/chat),
                "message": str
            }
        """
        # Classify intent
        intent = self.intent_classifier.classify(prompt)
        
        print(f"\n🔍 Intent: {intent['intent']} | Category: {intent['category']} | Action: {intent['action']}")
        
        if intent["intent"] == "modify":
            # Modification requests return UPDATED ITINERARY
            return await self._handle_modification(prompt, intent, current_itinerary, user_profile)
        elif intent["intent"] == "query":
            # Query requests return ANSWER ONLY (no itinerary update)
            answer = await self.qa_agent.answer_question(prompt, current_itinerary)
            return {
                "type": "query",  # Changed from "answer" to "query" for consistency
                "answer": answer,
                "message": "Here's the information you requested:",
                "itinerary": None  # Explicitly no itinerary update for queries
            }
        else:  # chat
            # Chat requests return RESPONSE ONLY (no itinerary update)
            return {
                "type": "chat",
                "answer": self._handle_chat(prompt),
                "message": "",
                "itinerary": None  # Explicitly no itinerary update for chat
            }
    
    async def _handle_modification(
        self,
        prompt: str,
        intent: Dict[str, Any],
        itinerary: TripPlan,
        user_profile: Optional[UserProfile]
    ) -> Dict[str, Any]:
        """Handle modification requests"""
        category = intent["category"]
        action = intent["action"]
        
        request = itinerary.request
        stay_results = {"accommodations": itinerary.accommodations}
        restaurant_results = {"restaurants": itinerary.restaurants}
        travel_results = {"transportation": itinerary.transportation}
        experience_results = {"experiences": itinerary.experiences}
        
        modified = False
        
        # Handle accommodation modifications
        if category == "accommodation":
            if action in ["add", "change", "find"]:
                print("🏨 Searching for new accommodations...")
                new_stay_results = await self.stay_agent.process(request, user_profile)
                if new_stay_results.get("accommodations"):
                    stay_results = new_stay_results
                    modified = True
        
        # Handle restaurant modifications
        elif category == "restaurant":
            if action in ["add", "change", "find"]:
                print("🍽️  Searching for new restaurants...")
                new_restaurant_results = await self.restaurant_agent.process(
                    request, stay_results, user_profile
                )
                if new_restaurant_results.get("restaurants"):
                    restaurant_results = new_restaurant_results
                    modified = True
        
        # Handle transportation modifications
        elif category == "transportation":
            if action in ["add", "change", "find"]:
                print("🚗 Searching for new transportation options...")
                new_travel_results = await self.travel_agent.process(request, stay_results)
                if new_travel_results.get("transportation"):
                    travel_results = new_travel_results
                    modified = True
        
        # Handle experience modifications
        elif category == "experience":
            if action in ["add", "change", "find"]:
                print("🎯 Searching for new experiences...")
                new_experience_results = await self.experience_agent.process(request, stay_results)
                if new_experience_results.get("experiences"):
                    experience_results = new_experience_results
                    modified = True
        
        # Re-generate itinerary if modified
        if modified:
            print("📅 Updating itinerary...")
            budget_results = {"budget": itinerary.budget}  # Keep existing budget
            
            updated_itinerary = await self.planner_agent.process(
                request, stay_results, restaurant_results, travel_results,
                experience_results, budget_results
            )
            
            return {
                "type": "modification",
                "itinerary": updated_itinerary,
                "message": f"✅ I've updated your itinerary based on your request: {prompt}"
            }
        else:
            return {
                "type": "modification",
                "itinerary": itinerary,
                "message": f"⚠️  I couldn't make that change. Could you be more specific? (e.g., 'add more restaurants' or 'find cheaper flights')"
            }
    
    def _handle_chat(self, prompt: str) -> str:
        """Handle general chat"""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ["thanks", "thank you", "thank"]):
            return "You're welcome! Happy to help with your trip planning. Is there anything else you'd like to know or change?"
        elif any(word in prompt_lower for word in ["hello", "hi", "hey"]):
            return "Hello! I'm here to help you with your trip. You can ask me questions about your itinerary or request changes."
        elif any(word in prompt_lower for word in ["yes", "ok", "okay", "sure"]):
            return "Great! What would you like to do? You can ask questions about your itinerary or request modifications."
        else:
            return "I'm here to help with your trip! You can ask me questions about your itinerary or request changes. What would you like to know or modify?"

