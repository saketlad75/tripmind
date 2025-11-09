"""
BusSearchAgent - Specialized agent for finding bus options
Uses web search to find bus/coach options
"""

from typing import Dict, Any, Optional, List
from shared.types import Transportation
from agents.gemini_search_agent import GeminiSearchAgent
import json
import re
from datetime import datetime


class BusSearchAgent:
    """Agent specialized in finding bus/coach options"""
    
    def __init__(self):
        self.web_search = GeminiSearchAgent()
        self.max_options = 5
    
    async def initialize(self):
        """Initialize the agent"""
        await self.web_search.initialize()
    
    async def search_buses(
        self,
        origin: str,
        destination: str,
        departure_date: Optional[str] = None,
        travelers: int = 1,
        budget: Optional[float] = None
    ) -> List[Transportation]:
        """
        Search for bus options
        
        Args:
            origin: Origin location (city/bus station)
            destination: Destination location (city/bus station)
            departure_date: Departure date (YYYY-MM-DD)
            travelers: Number of travelers
            budget: Budget constraint
            
        Returns:
            List of Transportation objects
        """
        # Build custom prompt targeting specific bus booking sites
        date_str = f" on {departure_date}" if departure_date else ""
        budget_str = f" under ${budget}" if budget else ""
        
        custom_prompt = f"""Search for bus/coach ticket prices and options from {origin} to {destination}{date_str} for {travelers} traveler(s){budget_str}.

Please search on these specific bus booking websites:
1. Greyhound (https://www.greyhound.com) - for US buses
2. FlixBus (https://www.flixbus.com) - for US and European buses
3. Megabus (https://us.megabus.com) - for US buses
4. BoltBus (if available) - for US buses
5. National Express (https://www.nationalexpress.com) - for UK buses
6. Eurolines (https://www.eurolines.com) - for European buses
7. Busbud (https://www.busbud.com) - for bus comparison

For each bus option found, extract and return:
- Bus operator name (e.g., Greyhound, FlixBus, Megabus)
- Exact price in USD (total price for all travelers)
- Price per person
- Bus duration (in hours and minutes)
- Departure and arrival times (if available)
- Number of transfers/stops
- Direct booking URL or link to the booking site
- Departure station/bus stop name
- Arrival station/bus stop name
- Amenities (Wi-Fi, power outlets, restroom, etc.)

Return bus options with real, current prices from these booking sites.
Focus on finding the most affordable and convenient options."""

        # Perform web search with custom prompt
        search_results = await self.web_search.search(
            custom_prompt=custom_prompt,
            format_json=True
        )
        
        # Parse results
        buses = self._parse_bus_results(
            search_results["results"],
            origin,
            destination,
            travelers
        )
        
        # Limit and sort by price
        buses = sorted(buses, key=lambda x: x.price)[:self.max_options]
        
        return buses
    
    def _parse_bus_results(
        self,
        output: str,
        origin: str,
        destination: str,
        travelers: int
    ) -> List[Transportation]:
        """Parse bus search results into Transportation objects"""
        buses = []
        
        # Check if output indicates no direct bus route
        if any(phrase in output.lower() for phrase in [
            "no direct bus", "no bus route", "not available"
        ]):
            return buses
        
        # Try to extract JSON
        try:
            if "```json" in output:
                json_start = output.find("```json") + 7
                json_end = output.find("```", json_start)
                json_str = output[json_start:json_end].strip()
                data = json.loads(json_str)
                
                if isinstance(data, list):
                    bus_list = data
                elif isinstance(data, dict):
                    bus_list = data.get("buses", data.get("results", data.get("options", [])))
                    if not isinstance(bus_list, list) and isinstance(bus_list, dict):
                        bus_list = [bus_list]
                else:
                    bus_list = []
                
                for idx, bus_data in enumerate(bus_list[:self.max_options]):
                    if isinstance(bus_data, dict):
                        bus = self._create_bus_from_dict(
                            bus_data, origin, destination, travelers, idx
                        )
                        if bus and bus.price > 0:
                            buses.append(bus)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing bus JSON: {e}")
        
        # If no JSON found, try text extraction
        if not buses:
            buses = self._extract_buses_from_text(output, origin, destination, travelers)
        
        return buses
    
    def _parse_amenities(self, amenities_input) -> List[str]:
        """Parse amenities from various formats"""
        if isinstance(amenities_input, list):
            return amenities_input
        elif isinstance(amenities_input, str):
            # Split by comma and clean up
            return [a.strip() for a in amenities_input.split(',') if a.strip()]
        else:
            return ["Wi-Fi", "Power Outlets", "Restroom"]
    
    def _create_bus_from_dict(
        self,
        data: Dict[str, Any],
        origin: str,
        destination: str,
        travelers: int,
        idx: int
    ) -> Optional[Transportation]:
        """Create Transportation object from bus data"""
        try:
            # Parse price
            price = 0.0
            price_str = str(data.get("price", data.get("total_price", data.get("cost", "0"))))
            price_match = re.search(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', price_str)
            if price_match:
                price = float(price_match.group(1).replace(',', ''))
            else:
                try:
                    price = float(price_str)
                except (ValueError, TypeError):
                    price = 0.0
            
            price_per_person = data.get("price_per_person")
            if price_per_person is None and price > 0:
                price_per_person = price / travelers
            elif price_per_person is not None:
                price_per_person_str = str(price_per_person)
                price_match = re.search(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', price_per_person_str)
                if price_match:
                    price_per_person = float(price_match.group(1).replace(',', ''))
                else:
                    try:
                        price_per_person = float(price_per_person)
                    except (ValueError, TypeError):
                        price_per_person = price / travelers if price > 0 else None
            
            # Parse duration
            duration_minutes = None
            if "duration_minutes" in data:
                duration_minutes = int(data["duration_minutes"])
            elif "duration_hours" in data:
                duration_minutes = int(float(data["duration_hours"]) * 60)
            elif "duration" in data:
                duration_str = str(data["duration"])
                hours_match = re.search(r'(\d+)h', duration_str)
                mins_match = re.search(r'(\d+)m', duration_str)
                hours = int(hours_match.group(1)) if hours_match else 0
                mins = int(mins_match.group(1)) if mins_match else 0
                duration_minutes = hours * 60 + mins
            
            # Get operator
            provider = data.get("operator", data.get("provider", data.get("company", "")))
            if not provider or provider == "":
                desc = str(data.get("description", data.get("details", "")))
                bus_match = re.search(r'(Greyhound|FlixBus|Megabus|BoltBus|National Express|Eurolines)', desc, re.IGNORECASE)
                if bus_match:
                    provider = bus_match.group(1)
            if not provider or provider == "":
                provider = "Unknown Bus Operator"
            provider = str(provider).strip()
            
            # Calculate carbon emissions (rough estimate: ~0.05 kg CO2 per km per passenger)
            # Estimate distance from duration (average bus speed ~80 km/h)
            carbon_emissions_kg = None
            if duration_minutes:
                distance_km = (80 * duration_minutes) / 60
                carbon_emissions_kg = round(distance_km * 0.05 * travelers, 2)
            
            return Transportation(
                id=f"bus_{idx}_{abs(hash(str(data)) % 10000)}",
                type="bus",
                origin=data.get("origin", origin),
                destination=data.get("destination", destination),
                duration_minutes=duration_minutes,
                price=price,
                price_per_person=price_per_person,
                provider=provider,
                booking_url=data.get("booking_url", data.get("url", data.get("link"))),
                carbon_emissions_kg=carbon_emissions_kg,
                carbon_score="low" if carbon_emissions_kg and carbon_emissions_kg < 20 else "medium",
                transfers=data.get("transfers", data.get("stops", 0)),
                comfort_level="economy",
                amenities=self._parse_amenities(data.get("amenities", ["Wi-Fi", "Power Outlets", "Restroom"])),
                details=data.get("details", {})
            )
        except (KeyError, ValueError, TypeError) as e:
            print(f"Error creating bus: {e}")
            return None
    
    def _extract_buses_from_text(
        self,
        text: str,
        origin: str,
        destination: str,
        travelers: int
    ) -> List[Transportation]:
        """Extract bus info from unstructured text (fallback)"""
        buses = []
        bus_operators = ["Greyhound", "FlixBus", "Megabus", "BoltBus", "National Express"]
        
        paragraphs = re.split(r'\n\n|\n(?=[A-Z])', text)
        
        for idx, para in enumerate(paragraphs[:self.max_options]):
            para_lower = para.lower()
            if any(word in para_lower for word in ["bus", "coach", "greyhound", "flixbus", "megabus"]):
                # Extract price
                price_matches = re.findall(r'\$(\d+(?:\.\d{2})?)', para)
                price = float(price_matches[0]) if price_matches else 0.0
                
                # Extract operator
                operator_match = re.search(r'(' + '|'.join([re.escape(op) for op in bus_operators]) + r')', para, re.IGNORECASE)
                provider = operator_match.group(1) if operator_match else "Unknown Bus Operator"
                
                # Extract duration
                duration_minutes = None
                duration_match = re.search(r'(\d+)\s*(?:hours?|hrs?|h)\s*(?:(\d+)\s*(?:minutes?|mins?|m))?', para_lower)
                if duration_match:
                    hours = int(duration_match.group(1))
                    mins = int(duration_match.group(2)) if duration_match.group(2) else 0
                    duration_minutes = hours * 60 + mins
                
                if price > 0:
                    bus = Transportation(
                        id=f"bus_text_{idx}",
                        type="bus",
                        origin=origin,
                        destination=destination,
                        price=price,
                        price_per_person=price / travelers if price > 0 else None,
                        provider=provider,
                        duration_minutes=duration_minutes,
                        carbon_emissions_kg=10.0,  # Default estimate
                        carbon_score="low",
                        details={"extracted_from": "text"}
                    )
                    buses.append(bus)
        
        return buses

