"""
ExperienceAgent - Placeholder for experience agent
Will be implemented later
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
    
    async def process(self, request: TripRequest, stay_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process experience request"""
        return {
            "experiences": [],
            "message": "ExperienceAgent not yet implemented"
        }

