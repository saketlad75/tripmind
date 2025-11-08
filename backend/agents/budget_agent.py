"""
BudgetAgent - Placeholder for budget agent
Will be implemented later
"""

from typing import Dict, Any, Optional
from shared.types import TripRequest


class BudgetAgent:
    """Agent responsible for budget planning"""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    async def initialize(self):
        """Initialize the agent"""
        pass
    
    async def process(
        self,
        request: TripRequest,
        stay_results: Optional[Dict[str, Any]] = None,
        travel_results: Optional[Dict[str, Any]] = None,
        experience_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process budget request"""
        return {
            "budget": {},
            "message": "BudgetAgent not yet implemented"
        }

