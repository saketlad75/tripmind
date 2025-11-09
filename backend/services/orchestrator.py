"""
Trip Orchestrator - Main orchestration service using LangGraph
Coordinates all agents to plan and book trips
Optimized for parallel execution where possible
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import os
import asyncio
from dotenv import load_dotenv

from agents.stay_agent import StayAgent
from agents.restaurant_agent import RestaurantAgent
from agents.travel_agent import TravelAgent
from agents.experience_agent import ExperienceAgent
from agents.budget_agent import BudgetAgent
from agents.planner_agent import PlannerAgent
from shared.types import TripRequest, TripPlan, UserProfile

load_dotenv()


class TripOrchestrator:
    """Main orchestrator that coordinates all agents"""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        # Agents using Dedalus Labs, don't need LLM
        self.stay_agent = StayAgent()
        self.restaurant_agent = RestaurantAgent()
        # Other agents can use LLM if needed
        self.travel_agent = TravelAgent(self.llm)
        self.experience_agent = ExperienceAgent(self.llm)
        self.budget_agent = BudgetAgent(self.llm)
        self.planner_agent = PlannerAgent(self.llm)
        self.workflow = self._build_workflow()
        # User profile storage (in production, use a database)
        # Profiles are registered via API from UI registration
        self._user_profiles: Dict[str, UserProfile] = {}
    
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
        """Build the LangGraph workflow with parallel execution where possible"""
        # Use dict-based state for LangGraph compatibility
        from typing import TypedDict
        
        class AgentStateDict(TypedDict):
            request: TripRequest
            user_profile: Optional[UserProfile]
            stay_results: Optional[Dict[str, Any]]
            restaurant_results: Optional[Dict[str, Any]]
            travel_results: Optional[Dict[str, Any]]
            experience_results: Optional[Dict[str, Any]]
            budget_results: Optional[Dict[str, Any]]
            final_plan: Optional[TripPlan]
        
        workflow = StateGraph(AgentStateDict)
        
        # Add nodes for each agent
        workflow.add_node("stay_agent", self._stay_agent_node)
        workflow.add_node("parallel_agents", self._parallel_agents_node)  # Parallel execution node
        workflow.add_node("budget_agent", self._budget_agent_node)
        workflow.add_node("planner_agent", self._planner_agent_node)
        
        # Optimized flow:
        # 1. StayAgent (must run first)
        # 2. Parallel: RestaurantAgent, TravelAgent, ExperienceAgent (all only need stay_results)
        # 3. BudgetAgent (needs all previous results)
        # 4. PlannerAgent (needs all results)
        workflow.set_entry_point("stay_agent")
        workflow.add_edge("stay_agent", "parallel_agents")
        workflow.add_edge("parallel_agents", "budget_agent")
        workflow.add_edge("budget_agent", "planner_agent")
        workflow.add_edge("planner_agent", END)
        
        return workflow.compile()
    
    async def _stay_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Stay agent processing node"""
        print("   🏨 [1/6] StayAgent: Finding accommodations...")
        request = state["request"]
        user_profile = state.get("user_profile")
        result = await self.stay_agent.process(request, user_profile)
        acc_count = len(result.get("accommodations", [])) if result else 0
        print(f"      ✅ Found {acc_count} accommodations")
        return {"stay_results": result}
    
    async def _parallel_agents_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parallel execution node - runs RestaurantAgent, TravelAgent, and ExperienceAgent concurrently
        All three agents only depend on stay_results, so they can run in parallel
        """
        print("   ⚡ [2-4/6] Running agents in parallel: RestaurantAgent, TravelAgent, ExperienceAgent...")
        request = state["request"]
        stay_results = state.get("stay_results")
        user_profile = state.get("user_profile")
        
        # Run all three agents in parallel using asyncio.gather
        async def run_restaurant():
            print("      🍽️  RestaurantAgent: Finding restaurants...")
            result = await self.restaurant_agent.process(request, stay_results, user_profile)
            rest_count = len(result.get("restaurants", [])) if result else 0
            print(f"         ✅ RestaurantAgent: Found {rest_count} restaurants")
            return ("restaurant", result)
        
        async def run_travel():
            print("      ✈️  TravelAgent: Finding transportation options...")
            result = await self.travel_agent.process(request, stay_results)
            trans_count = len(result.get("transportation", [])) if result else 0
            print(f"         ✅ TravelAgent: Found {trans_count} transportation options")
            return ("travel", result)
        
        async def run_experience():
            print("      🎯 ExperienceAgent: Finding local activities...")
            result = await self.experience_agent.process(request, stay_results)
            exp_count = len(result.get("experiences", [])) if result else 0
            print(f"         ✅ ExperienceAgent: Found {exp_count} experiences")
            return ("experience", result)
        
        # Execute all three agents concurrently
        results = await asyncio.gather(
            run_restaurant(),
            run_travel(),
            run_experience(),
            return_exceptions=True
        )
        
        # Process results and handle any exceptions
        output = {}
        for result_tuple in results:
            if isinstance(result_tuple, Exception):
                print(f"         ❌ Agent failed: {result_tuple}")
                continue
            
            agent_name, result = result_tuple
            if isinstance(result, Exception):
                print(f"         ❌ {agent_name.capitalize()}Agent failed: {result}")
                # Return empty result for failed agent
                if agent_name == "restaurant":
                    output["restaurant_results"] = {"restaurants": []}
                elif agent_name == "travel":
                    output["travel_results"] = {"transportation": []}
                elif agent_name == "experience":
                    output["experience_results"] = {"experiences": []}
            else:
                if agent_name == "restaurant":
                    output["restaurant_results"] = result
                elif agent_name == "travel":
                    output["travel_results"] = result
                elif agent_name == "experience":
                    output["experience_results"] = result
        
        print("   ✅ All parallel agents completed!")
        return output
    
    async def _budget_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Budget agent processing node"""
        print("   💰 [5/6] BudgetAgent: Calculating budget...")
        request = state["request"]
        stay_results = state.get("stay_results")
        travel_results = state.get("travel_results")
        experience_results = state.get("experience_results")
        restaurant_results = state.get("restaurant_results")
        result = await self.budget_agent.process(
            request, stay_results, travel_results, experience_results, restaurant_results
        )
        # result is a dict with "budget" key containing BudgetBreakdown object
        budget_obj = result.get("budget") if result else None
        budget_total = budget_obj.total if budget_obj and hasattr(budget_obj, 'total') else 0
        print(f"      ✅ Budget calculated: ${budget_total:.2f}")
        return {"budget_results": result}
    
    async def _planner_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Planner agent processing node"""
        print("   📅 [6/6] PlannerAgent: Creating itinerary...")
        request = state["request"]
        stay_results = state.get("stay_results")
        restaurant_results = state.get("restaurant_results")
        travel_results = state.get("travel_results")
        experience_results = state.get("experience_results")
        budget_results = state.get("budget_results")
        result = await self.planner_agent.process(
            request, stay_results, restaurant_results, travel_results, experience_results, budget_results
        )
        if isinstance(result, dict):
            itinerary_days = len(result.get("itinerary", [])) if result else 0
        else:
            itinerary_days = len(result.itinerary) if hasattr(result, 'itinerary') and result.itinerary else 0
        print(f"      ✅ Created {itinerary_days}-day itinerary")
        return {"final_plan": result}
    
    async def plan_trip(self, request: TripRequest, user_profile: Optional[UserProfile] = None) -> TripPlan:
        """
        Main method to plan a trip
        
        Args:
            request: TripRequest with user's trip description
            user_profile: Optional user profile (will be fetched if not provided)
        """
        # Fetch user profile if not provided
        if not user_profile:
            user_profile = self._user_profiles.get(request.user_id)
        
        # Convert Pydantic model to dict for LangGraph
        initial_state = {
            "request": request,
            "user_profile": user_profile,
            "stay_results": None,
            "restaurant_results": None,
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
    
    def register_user_profile(self, profile: UserProfile):
        """Register or update a user profile"""
        self._user_profiles[profile.user_id] = profile
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID - loads from database if not in memory"""
        # First check in-memory cache
        if user_id in self._user_profiles:
            return self._user_profiles[user_id]
        
        # Load from database
        try:
            from services.user_service import UserService
            user_service = UserService()
            profile = user_service.to_user_profile(user_id)
            if profile:
                # Cache it for future use
                self._user_profiles[user_id] = profile
                return profile
        except Exception as e:
            print(f"⚠️  Error loading user profile from database: {e}")
        
        return None
    
    async def initialize(self):
        """Initialize all agents"""
        await self.stay_agent.initialize()
        await self.restaurant_agent.initialize()
        await self.travel_agent.initialize()
        await self.experience_agent.initialize()
        await self.budget_agent.initialize()
        await self.planner_agent.initialize()
    
    async def cleanup(self):
        """Cleanup resources"""
        pass

