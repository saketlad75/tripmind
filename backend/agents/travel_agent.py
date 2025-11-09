"""
TravelAgent - Multi-agent orchestration for transportation planning
Uses specialized agents to find flights, trains, and cabs asynchronously
Plans multi-modal routes combining different transportation modes
"""

from typing import Dict, Any, Optional, List
import asyncio
from shared.types import TripRequest, Transportation, Route
from agents.flight_search_agent import FlightSearchAgent
from agents.train_search_agent import TrainSearchAgent
from agents.car_search_agent import CarSearchAgent
from agents.bus_search_agent import BusSearchAgent
from agents.route_analyzer_agent import RouteAnalyzerAgent


class TravelAgent:
    """Main agent that orchestrates specialized transportation search agents"""
    
    def __init__(self, llm=None):
        """
        Initialize TravelAgent
        
        Args:
            llm: Not used (kept for compatibility with orchestrator)
        """
        self.flight_agent = FlightSearchAgent()
        self.train_agent = TrainSearchAgent()
        self.car_agent = CarSearchAgent()
        self.bus_agent = BusSearchAgent()
        self.route_analyzer = RouteAnalyzerAgent()
        self.initialized = False
    
    async def initialize(self):
        """Initialize all sub-agents"""
        if self.initialized:
            return
        
        # Initialize all agents in parallel
        await asyncio.gather(
            self.flight_agent.initialize(),
            self.train_agent.initialize(),
            self.car_agent.initialize(),
            self.bus_agent.initialize(),
            self.route_analyzer.initialize()
        )
        self.initialized = True
    
    async def process(
        self,
        request: TripRequest,
        stay_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process trip request to find transportation options using multi-agent approach
        
        Args:
            request: TripRequest with user's trip requirements
            stay_results: Results from StayAgent (can help determine final destination)
            
        Returns:
            Dictionary with transportation options, routes, and metadata
        """
        if not self.initialized:
            await self.initialize()
        
        # Extract origin and destination
        origin = self._extract_origin(request)
        destination = request.destination or self._extract_destination_from_stay(stay_results)
        
        if not destination:
            raise ValueError("Destination is required for transportation planning")
        
        # Extract final destination (e.g., hotel address) from stay results
        final_destination = None
        if stay_results and "accommodations" in stay_results:
            accommodations = stay_results["accommodations"]
            if accommodations and len(accommodations) > 0:
                first_acc = accommodations[0]
                if hasattr(first_acc, 'address') and first_acc.address:
                    final_destination = first_acc.address
        
        # Format dates
        departure_date = None
        if request.start_date:
            departure_date = request.start_date.isoformat()
        
        # Step 1: Check user preferences first, then analyze route
        user_preferred_mode = None
        # Check if request has preferences (for backward compatibility)
        if hasattr(request, 'preferences') and request.preferences and "mode_preferences" in request.preferences:
            mode_prefs = request.preferences["mode_preferences"]
            if isinstance(mode_prefs, list) and len(mode_prefs) > 0:
                # If user explicitly requests a specific mode, prioritize it
                if len(mode_prefs) == 1:
                    user_preferred_mode = mode_prefs[0]
                # Check if user mentions mode in prompt
                prompt_lower = request.prompt.lower()
                if "by bus" in prompt_lower or ("bus" in prompt_lower and "bus" in mode_prefs):
                    user_preferred_mode = "bus"
                elif "by train" in prompt_lower or ("train" in prompt_lower and "train" in mode_prefs):
                    user_preferred_mode = "train"
                elif "by cab" in prompt_lower or "cab" in prompt_lower or "taxi" in prompt_lower or "airport" in prompt_lower:
                    user_preferred_mode = "car"
        else:
            # Check prompt for mode preferences
            prompt_lower = request.prompt.lower()
            if "by bus" in prompt_lower or "bus" in prompt_lower:
                user_preferred_mode = "bus"
            elif "by train" in prompt_lower or "train" in prompt_lower:
                user_preferred_mode = "train"
            elif "by cab" in prompt_lower or "cab" in prompt_lower or "taxi" in prompt_lower or "airport" in prompt_lower:
                user_preferred_mode = "car"
        
        # Step 2: Analyze route to determine best transportation mode
        route_analysis = await self.route_analyzer.analyze_route(origin, destination)
        recommended_mode = route_analysis.get("recommended_mode", "flight")
        
        # Override with user preference if explicitly requested
        if user_preferred_mode:
            recommended_mode = user_preferred_mode
            reasoning = f"User explicitly requested {user_preferred_mode}"
        else:
            reasoning = route_analysis.get("reasoning", "Based on route analysis")
        
        print(f"Route Analysis: {origin} → {destination}")
        print(f"Recommended Mode: {recommended_mode.upper()} - {reasoning}")
        
        # Step 2: Search only for the recommended mode
        flights = []
        trains = []
        cars = []
        buses = []
        
        if recommended_mode == "flight":
            flights = await self.flight_agent.search_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                travelers=request.travelers,
                budget=request.budget
            )
            # Limit to 5 best options
            flights = flights[:5]
            
            # Check if we need additional transportation from airport to final destination
            airport_to_destination = await self._get_airport_to_destination_transport(
                flights, destination, request
            )
            if airport_to_destination:
                # Add airport-to-destination options to cars list
                cars.extend(airport_to_destination)
        elif recommended_mode == "train":
            trains = await self.train_agent.search_trains(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                travelers=request.travelers,
                budget=request.budget
            )
            # Limit to 5 best options
            trains = trains[:5]
        elif recommended_mode == "bus":
            buses = await self.bus_agent.search_buses(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                travelers=request.travelers,
                budget=request.budget
            )
            # Limit to 5 best options
            buses = buses[:5]
        elif recommended_mode in ["car", "cab"]:
            # For car/cab, use car search agent
            cars = await self.car_agent.search_cabs(
                origin=origin,
                destination=destination,
                travelers=request.travelers,
                budget=request.budget
            )
            # Limit to 3-5 options
            cars = cars[:5]
        else:
            # Fallback: try flights
            flights = await self.flight_agent.search_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                travelers=request.travelers,
                budget=request.budget
            )
            flights = flights[:5]
        
        # Mark recommendations
        all_transportation = flights + trains + cars + buses
        self._mark_recommendations(flights, trains, [], request)
        
        # Separate airport-to-destination options
        airport_transport = [t for t in cars if t.details.get("is_airport_transfer", False)]
        regular_cars = [t for t in cars if not t.details.get("is_airport_transfer", False)]
        
        return {
            "transportation": all_transportation,
            "flights": flights,
            "trains": trains,
            "cars": regular_cars,
            "buses": buses,
            "airport_to_destination": airport_transport,  # Additional transport from airport
            "count": len(all_transportation),
            "origin": origin,
            "destination": destination,
            "recommended_mode": recommended_mode,
            "route_analysis": route_analysis
        }
    
    def _extract_origin(self, request: TripRequest) -> str:
        """Extract origin location from request"""
        # Check if origin was stored directly (from generate_itinerary script)
        if hasattr(request, '_origin') and request._origin:
            return request._origin
        
        # Check if request has preferences attribute (from old structure)
        # New TripRequest doesn't have preferences, so we'll infer from prompt
        if hasattr(request, 'preferences') and request.preferences:
            if "origin" in request.preferences:
                origin = request.preferences["origin"]
                if isinstance(origin, dict) and "text" in origin:
                    return origin["text"]
                elif isinstance(origin, str):
                    return origin
            
            # Check for common origin fields
            for key in ["from", "from_location", "departure_location", "starting_location"]:
                if key in request.preferences:
                    origin = request.preferences[key]
                    if isinstance(origin, str):
                        return origin
        
        # Try to infer from prompt
        prompt_lower = request.prompt.lower()
        import re
        patterns = [
            r"from\s+([A-Z][a-zA-Z\s,]+?)(?:\s+to|\s+for|\s+with|$)",
            r"traveling\s+from\s+([A-Z][a-zA-Z\s,]+?)(?:\s+to|\s+for|$)",
            r"departing\s+from\s+([A-Z][a-zA-Z\s,]+?)(?:\s+to|\s+for|$)",
            r"\(traveling\s+from\s+([A-Z][a-zA-Z\s,]+?)\)",  # From enhanced prompt
        ]
        
        for pattern in patterns:
            match = re.search(pattern, request.prompt, re.IGNORECASE)
            if match:
                origin = match.group(1).strip().rstrip(',').title()
                # Clean up common suffixes
                origin = re.sub(r'\s*\(.*?\)\s*$', '', origin)
                return origin
        
        return "User Location"
    
    def _extract_destination_from_stay(self, stay_results: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract destination from stay results if available"""
        if stay_results and "accommodations" in stay_results:
            accommodations = stay_results["accommodations"]
            if accommodations and len(accommodations) > 0:
                first_acc = accommodations[0]
                if hasattr(first_acc, 'address') and first_acc.address:
                    # Extract city from address
                    parts = first_acc.address.split(',')
                    if len(parts) > 0:
                        return parts[-1].strip()
        return None
    
    def _mark_recommendations(
        self,
        flights: List[Transportation],
        trains: List[Transportation],
        routes: List[Route],
        request: TripRequest
    ):
        """Mark recommended options based on user preferences"""
        # Check if request has preferences (for backward compatibility)
        if hasattr(request, 'preferences') and request.preferences:
            preferences = request.preferences
        else:
            preferences = {}
        priority = preferences.get("priority", "balanced")
        
        all_options = flights + trains
        
        if not all_options and not routes:
            return
        
        # Score and recommend individual options
        scored_options = []
        for option in all_options:
            score = self._calculate_score(option, priority)
            scored_options.append((score, option))
        
        # Score routes
        scored_routes = []
        for route in routes:
            score = self._calculate_route_score(route, priority)
            scored_routes.append((score, route))
        
        # Mark top individual option
        if scored_options:
            scored_options.sort(key=lambda x: x[0], reverse=True)
            top_option = scored_options[0][1]
            top_option.recommended = True
            top_option.recommendation_reason = f"Best {top_option.type} option based on {priority} priority"
        
        # Mark top route
        if scored_routes:
            scored_routes.sort(key=lambda x: x[0], reverse=True)
            top_route = scored_routes[0][1]
            top_route.recommended = True
            top_route.recommendation_reason = f"Best multi-modal route based on {priority} priority"
    
    def _calculate_score(self, option: Transportation, priority: str) -> float:
        """Calculate score for an option based on priority"""
        score = 0
        
        if priority == "cheapest":
            if option.price > 0:
                score = 1000 / option.price
        elif priority == "fastest":
            if option.duration_minutes:
                score = 1000 / option.duration_minutes
        elif priority == "greenest":
            if option.carbon_emissions_kg:
                score = 1000 / (option.carbon_emissions_kg + 1)
        else:  # balanced
            price_score = (1000 / (option.price + 1)) if option.price > 0 else 0
            time_score = (1000 / (option.duration_minutes + 1)) if option.duration_minutes else 0
            green_score = (1000 / (option.carbon_emissions_kg + 1)) if option.carbon_emissions_kg else 0
            score = (price_score * 0.3) + (time_score * 0.3) + (green_score * 0.4)
        
        return score
    
    def _calculate_route_score(self, route: Route, priority: str) -> float:
        """Calculate score for a route based on priority"""
        score = 0
        
        if priority == "cheapest":
            if route.total_price > 0:
                score = 1000 / route.total_price
        elif priority == "fastest":
            if route.total_duration_minutes:
                score = 1000 / route.total_duration_minutes
        elif priority == "greenest":
            if route.total_carbon_emissions_kg:
                score = 1000 / (route.total_carbon_emissions_kg + 1)
        else:  # balanced
            price_score = (1000 / (route.total_price + 1)) if route.total_price > 0 else 0
            time_score = (1000 / (route.total_duration_minutes + 1)) if route.total_duration_minutes else 0
            green_score = (1000 / (route.total_carbon_emissions_kg + 1)) if route.total_carbon_emissions_kg else 0
            score = (price_score * 0.3) + (time_score * 0.3) + (green_score * 0.4)
        
        return score
    
    async def _get_airport_to_destination_transport(
        self,
        flights: List[Transportation],
        final_destination: str,
        request: TripRequest
    ) -> List[Transportation]:
        """
        Get transportation options from airport to final destination
        This is needed when flights land at an airport but the destination is a specific location
        (e.g., university, hotel) that's far from the airport
        """
        if not flights:
            return []
        
        # Check if destination is a specific location (not an airport)
        destination_lower = final_destination.lower()
        is_specific_location = any(keyword in destination_lower for keyword in [
            "university", "college", "hotel", "hospital", "address", "street", "avenue", "road"
        ])
        
        if not is_specific_location:
            return []
        
        # Extract airport codes from flight destinations
        airports = set()
        for flight in flights:
            # Flight destination might be airport code (e.g., JFK, LGA, EWR) or airport name
            flight_dest = flight.destination or ""
            
            # Common airport patterns
            import re
            airport_code_match = re.search(r'\b([A-Z]{3})\b', flight_dest)
            if airport_code_match:
                airports.add(airport_code_match.group(1))
            elif any(airport_name in flight_dest.lower() for airport_name in [
                "jfk", "kennedy", "laguardia", "lga", "newark", "ewr", "airport"
            ]):
                # Try to extract or infer airport
                if "jfk" in flight_dest.lower() or "kennedy" in flight_dest.lower():
                    airports.add("JFK")
                elif "lga" in flight_dest.lower() or "laguardia" in flight_dest.lower():
                    airports.add("LGA")
                elif "ewr" in flight_dest.lower() or "newark" in flight_dest.lower():
                    airports.add("EWR")
                else:
                    # Generic airport - use the flight destination as-is
                    airports.add(flight_dest)
        
        if not airports:
            return []
        
        # Get transportation from each airport to final destination
        all_options = []
        for airport in airports:
            airport_name = f"{airport} Airport" if len(airport) == 3 else airport
            
            print(f"\n🔍 Searching transportation from {airport_name} to {final_destination}")
            
            # Try train first (more eco-friendly and often available from airports)
            train_options = await self.train_agent.search_trains(
                origin=airport_name,
                destination=final_destination,
                departure_date=None,  # No specific date for airport transfer
                travelers=request.travelers,
                budget=request.budget
            )
            
            # Try bus
            bus_options = await self.bus_agent.search_buses(
                origin=airport_name,
                destination=final_destination,
                departure_date=None,
                travelers=request.travelers,
                budget=request.budget
            )
            
            # Try cab/rideshare (most common for airport transfers)
            cab_options = await self.car_agent.search_cabs(
                origin=airport_name,
                destination=final_destination,
                travelers=request.travelers,
                budget=request.budget
            )
            
            # Mark all as airport transfers
            for option in train_options + bus_options + cab_options:
                option.details["is_airport_transfer"] = True
                option.details["airport"] = airport
                option.details["transfer_type"] = "airport_to_destination"
            
            all_options.extend(train_options[:2])  # Top 2 train options
            all_options.extend(bus_options[:2])    # Top 2 bus options
            all_options.extend(cab_options[:3])    # Top 3 cab options
        
        # Remove duplicates and limit
        seen = set()
        unique_options = []
        for option in all_options:
            option_key = (option.provider, option.origin, option.destination, option.price)
            if option_key not in seen:
                seen.add(option_key)
                unique_options.append(option)
        
        return unique_options[:10]  # Return top 10 options

