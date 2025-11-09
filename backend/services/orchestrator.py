"""
Trip Orchestrator - Main orchestration service using LangGraph
Coordinates all agents to plan and book trips
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import os
from dotenv import load_dotenv

from agents.stay_agent import StayAgent
from agents.travel_agent import TravelAgent
from agents.experience_agent import ExperienceAgent
from agents.budget_agent import BudgetAgent
from agents.planner_agent import PlannerAgent
from shared.types import TripRequest, TripPlan

load_dotenv()


class TripOrchestrator:
    """Main orchestrator that coordinates all agents"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        # StayAgent uses Dedalus Labs, doesn't need LLM
        self.stay_agent = StayAgent()
        # Other agents can use LLM if needed
        self.travel_agent = TravelAgent(self.llm)
        self.experience_agent = ExperienceAgent(self.llm)
        self.budget_agent = BudgetAgent(self.llm)
        self.planner_agent = PlannerAgent(self.llm)
        self.workflow = self._build_workflow()
    
    def _initialize_llm(self):
        """Initialize LLM based on environment configuration"""
        if os.getenv("ANTHROPIC_API_KEY"):
            return ChatAnthropic(
                model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-3-5-20241022"),
                temperature=0.7
            )
        else:
            return ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0.7
            )
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        # Use dict-based state for LangGraph compatibility
        from typing import TypedDict
        
        class AgentStateDict(TypedDict):
            request: TripRequest
            stay_results: Optional[Dict[str, Any]]
            travel_results: Optional[Dict[str, Any]]
            experience_results: Optional[Dict[str, Any]]
            budget_results: Optional[Dict[str, Any]]
            final_plan: Optional[TripPlan]
        
        workflow = StateGraph(AgentStateDict)
        
        # Add nodes for each agent
        workflow.add_node("stay_agent", self._stay_agent_node)
        workflow.add_node("travel_agent", self._travel_agent_node)
        workflow.add_node("experience_agent", self._experience_agent_node)
        workflow.add_node("budget_agent", self._budget_agent_node)
        workflow.add_node("planner_agent", self._planner_agent_node)
        
        # Define the flow
        workflow.set_entry_point("stay_agent")
        workflow.add_edge("stay_agent", "travel_agent")
        workflow.add_edge("travel_agent", "experience_agent")
        workflow.add_edge("experience_agent", "budget_agent")
        workflow.add_edge("budget_agent", "planner_agent")
        workflow.add_edge("planner_agent", END)
        
        return workflow.compile()
    
    async def _stay_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Stay agent processing node"""
        request = state["request"]
        result = await self.stay_agent.process(request)
        return {"stay_results": result}
    
    async def _travel_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Travel agent processing node"""
        request = state["request"]
        stay_results = state.get("stay_results")
        result = await self.travel_agent.process(request, stay_results)
        return {"travel_results": result}
    
    async def _experience_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Experience agent processing node"""
        request = state["request"]
        stay_results = state.get("stay_results")
        result = await self.experience_agent.process(request, stay_results)
        return {"experience_results": result}
    
    async def _budget_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Budget agent processing node"""
        request = state["request"]
        stay_results = state.get("stay_results")
        travel_results = state.get("travel_results")
        experience_results = state.get("experience_results")
        restaurant_results = state.get("restaurant_results")
        result = await self.budget_agent.process(
            request, stay_results, travel_results, experience_results, restaurant_results
        )
        return {"budget_results": result}
    
    async def _planner_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Planner agent processing node"""
        request = state["request"]
        stay_results = state.get("stay_results")
        travel_results = state.get("travel_results")
        experience_results = state.get("experience_results")
        budget_results = state.get("budget_results")
        result = await self.planner_agent.process(
            request, stay_results, travel_results, experience_results, budget_results
        )
        return {"final_plan": result}
    
    async def plan_trip(self, request: TripRequest) -> TripPlan:
        """Main method to plan a trip"""
        # Convert Pydantic model to dict for LangGraph
        initial_state = {
            "request": request,
            "stay_results": None,
            "travel_results": None,
            "experience_results": None,
            "budget_results": None,
            "final_plan": None
        }
        
        # Execute workflow
        final_state = await self.workflow.ainvoke(initial_state)
        
        # Extract final plan
        final_plan = final_state.get("final_plan")
        if isinstance(final_plan, TripPlan):
            return final_plan
        elif isinstance(final_plan, dict):
            return TripPlan(**final_plan)
        else:
            raise ValueError("Invalid final_plan format")
    
    async def initialize(self):
        """Initialize all agents"""
        await self.stay_agent.initialize()
        await self.travel_agent.initialize()
        await self.experience_agent.initialize()
        await self.budget_agent.initialize()
        await self.planner_agent.initialize()
    
    async def cleanup(self):
        """Cleanup resources"""
        pass

