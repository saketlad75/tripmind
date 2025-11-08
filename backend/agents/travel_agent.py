"""
TravelAgent - Placeholder for travel agent
Will be implemented later
"""

from typing import Dict, Any, Optional
from shared.types import TripRequest


class TravelAgent:
    """Agent responsible for finding transportation options"""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    async def initialize(self):
        """Initialize the agent"""
        pass
    
    async def process(self, request: TripRequest, stay_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process travel request"""
        return {
            "transportation": [],
            "message": "TravelAgent not yet implemented"
        }

