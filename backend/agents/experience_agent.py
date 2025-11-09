"""
ExperienceAgent - Finds local experiences and activities
Uses user context (occupation, interests) to personalize recommendations
"""

from typing import Dict, Any, Optional
from shared.types import TripRequest


class ExperienceAgent:
    """Agent responsible for finding local experiences"""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    async def initialize(self):
        """Initialize the agent"""
        pass
    
    async def process(
        self, 
        request: TripRequest, 
        stay_results: Optional[Dict[str, Any]] = None,
        user_context: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        Process experience request
        
        Args:
            request: TripRequest with user's trip requirements
            stay_results: Results from StayAgent (for location context)
            user_context: Additional user context (occupation, interests, etc.)
            
        Returns:
            Dictionary with experiences and metadata
        """
        # Build prompt with user context
        prompt_parts = [
            f"I need to find local experiences and activities for a trip.",
            f"\nUser's Trip Description:",
            f'"{request.prompt}"',
            f"\nNOTE: The trip description above has PRIORITY. If it conflicts with user profile data, use the trip description.",
        ]
        
        # Add destination from request or stay results
        if request.destination:
            prompt_parts.append(f"\nDestination: {request.destination}")
        elif stay_results and stay_results.get("accommodations"):
            acc = stay_results["accommodations"][0]
            if hasattr(acc, 'address') and acc.address:
                prompt_parts.append(f"\nLocation: {acc.address}")
        
        # Add duration
        if request.duration_days:
            prompt_parts.append(f"Trip Duration: {request.duration_days} days")
        
        # Add user context for personalization
        if user_context:
            context_parts = []
            if user_context.get('occupation'):
                context_parts.append(f"User's occupation: {user_context['occupation']}")
            if user_context.get('home_city'):
                context_parts.append(f"User's home city: {user_context['home_city']}")
            if context_parts:
                prompt_parts.append(f"\nUser Context: {', '.join(context_parts)}")
        
        prompt_parts.extend([
            "\nPlease help me find experiences and activities by:",
            "1. Finding activities that match the trip description",
            "2. Considering user's occupation and interests for personalization",
            "3. Including a mix of cultural, outdoor, entertainment, and local experiences",
            "4. Ensuring activities are suitable for the trip duration",
            "",
            "For each experience, provide:",
            "- Activity/experience name",
            "- Description and what makes it special",
            "- Location and address",
            "- Duration/time required",
            "- Price range or cost",
            "- Best time to visit",
            "- Booking information if needed",
            "",
            "IMPORTANT: Focus on activities mentioned in the trip description first.",
        ])
        
        # For now, return placeholder (will be implemented with actual search later)
        return {
            "experiences": [],
            "raw_output": "\n".join(prompt_parts),
            "count": 0,
            "message": "ExperienceAgent: Using user context for personalization. Full implementation pending."
        }

