"""
CarSearchAgent - Specialized agent for finding cab/car options
Uses web search to find cab, rideshare, and car rental options
Limited to 3 practical options based on destination
"""

from typing import Dict, Any, Optional, List
from shared.types import Transportation
from agents.gemini_search_agent import GeminiSearchAgent
import json
import re
from datetime import datetime


class CarSearchAgent:
    """Agent specialized in finding cab/car/rideshare options"""
    
    def __init__(self):
        self.web_search = GeminiSearchAgent()
        self.max_options = 3  # Limit to 3 practical cab options
    
    async def initialize(self):
        """Initialize the agent"""
        await self.web_search.initialize()
    
    async def search_cabs(
        self,
        origin: str,
        destination: str,
        travelers: int = 1,
        budget: Optional[float] = None
    ) -> List[Transportation]:
        """
        Search for cab/rideshare options using specific ride-hailing and taxi services
        
        Args:
            origin: Origin location (address or landmark)
            destination: Destination location (address or landmark)
            travelers: Number of travelers
            budget: Budget constraint
            
        Returns:
            List of Transportation objects (max 3)
        """
        # Build custom prompt targeting specific cab/rideshare services
        budget_str = f" under ${budget}" if budget else ""
        
        custom_prompt = f"""Search for taxi cab or rideshare prices and options from {origin} to {destination} for {travelers} traveler(s){budget_str}.

Please search on these specific ride-hailing and taxi services:
1. Uber (https://www.uber.com) - check fare estimates
2. Lyft (https://www.lyft.com) - check fare estimates
3. Local taxi services in the destination area
4. Airport taxi services if traveling to/from airports
5. Ride-hailing apps available in the destination country

For each cab/rideshare option found, extract and return:
- Service provider name (e.g., Uber, Lyft, Local Taxi, Airport Taxi)
- Estimated fare or price in USD
- Estimated travel time (in minutes)
- Distance (if available)
- Service type (UberX, Uber Comfort, Lyft Standard, etc.)
- Booking method or app link
- Pickup location details
- Drop-off location details

Return up to {self.max_options} practical cab/rideshare options with real fare estimates.
Focus on services that are actually available in the destination area.
For airport transfers, prioritize airport taxi services."""
        
        # Perform web search with custom prompt
        search_results = await self.web_search.search(
            custom_prompt=custom_prompt,
            format_json=True
        )
        
        # Parse results
        cabs = self._parse_cab_results(
            search_results["results"],
            origin,
            destination,
            travelers
        )
        
        # Limit to max options and sort by price
        cabs = sorted(cabs, key=lambda x: x.price)[:self.max_options]
        
        return cabs
    
    def _parse_cab_results(
        self,
        output: str,
        origin: str,
        destination: str,
        travelers: int
    ) -> List[Transportation]:
        """Parse cab search results into Transportation objects"""
        cabs = []
        
        # Try to extract JSON
        try:
            if "```json" in output:
                json_start = output.find("```json") + 7
                json_end = output.find("```", json_start)
                json_str = output[json_start:json_end].strip()
                data = json.loads(json_str)
                
                if isinstance(data, list):
                    cab_list = data
                elif isinstance(data, dict):
                    cab_list = data.get("cabs", data.get("rides", data.get("results", [])))
                else:
                    cab_list = []
                
                for idx, cab_data in enumerate(cab_list[:self.max_options]):
                    cab = self._create_cab_from_dict(
                        cab_data, origin, destination, travelers, idx
                    )
                    if cab:
                        cabs.append(cab)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing cab JSON: {e}")
        
        # If no JSON found, try text extraction
        if not cabs:
            cabs = self._extract_cabs_from_text(output, origin, destination, travelers)
        
        return cabs
    
    def _create_cab_from_dict(
        self,
        data: Dict[str, Any],
        origin: str,
        destination: str,
        travelers: int,
        idx: int
    ) -> Optional[Transportation]:
        """Create Transportation object from cab data"""
        try:
            # Determine type (cab, rideshare, or rental)
            trans_type = data.get("type", "cab")
            if trans_type not in ["cab", "taxi", "rideshare", "uber", "lyft", "rental"]:
                trans_type = "cab"
            
            # Parse price
            price = float(data.get("price", data.get("fare", data.get("cost", data.get("total_price", 0)))))
            price_per_person = data.get("price_per_person")
            if price_per_person is None and price > 0:
                price_per_person = price / travelers
            elif price_per_person is not None:
                price_per_person = float(price_per_person)
            
            # Parse duration (estimate if not provided)
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
            elif "distance_km" in data:
                # Estimate duration from distance (average city speed ~50 km/h)
                distance = float(data["distance_km"])
                duration_minutes = int((distance / 50) * 60)
            
            # Get provider
            provider = data.get("provider", data.get("company", data.get("service", "Unknown")))
            if isinstance(provider, list):
                provider = ", ".join(provider)
            
            # Calculate carbon emissions (rough estimate: ~0.12 kg CO2 per km per passenger)
            carbon_emissions_kg = None
            if duration_minutes:
                # Estimate distance from duration (average city speed ~50 km/h)
                distance_km = (50 * duration_minutes) / 60
                carbon_emissions_kg = round(distance_km * 0.12 * travelers, 2)
            elif "distance_km" in data:
                distance_km = float(data["distance_km"])
                carbon_emissions_kg = round(distance_km * 0.12 * travelers, 2)
            
            return Transportation(
                id=f"{trans_type}_{idx}_{abs(hash(str(data)) % 10000)}",
                type=trans_type,
                origin=data.get("origin", origin),
                destination=data.get("destination", destination),
                duration_minutes=duration_minutes,
                price=price,
                price_per_person=price_per_person,
                provider=str(provider),
                booking_url=data.get("booking_url", data.get("url", data.get("link"))),
                carbon_emissions_kg=carbon_emissions_kg,
                carbon_score="low" if carbon_emissions_kg and carbon_emissions_kg < 10 else "medium",
                transfers=0,  # Cabs are typically direct
                comfort_level="economy",
                amenities=data.get("amenities", []),
                details=data.get("details", {})
            )
        except (KeyError, ValueError, TypeError) as e:
            print(f"Error creating cab: {e}")
            return None
    
    def _extract_cabs_from_text(
        self,
        text: str,
        origin: str,
        destination: str,
        travelers: int
    ) -> List[Transportation]:
        """Extract cab info from unstructured text (fallback)"""
        cabs = []
        lines = text.split("\n")
        
        cab_types = ["uber", "lyft", "taxi", "cab"]
        for idx, line in enumerate(lines[:self.max_options]):
            line_lower = line.lower()
            if any(cab_type in line_lower for cab_type in cab_types):
                # Determine type
                trans_type = "rideshare"
                if "uber" in line_lower:
                    provider = "Uber"
                elif "lyft" in line_lower:
                    provider = "Lyft"
                elif "taxi" in line_lower or "cab" in line_lower:
                    trans_type = "cab"
                    provider = "Local Taxi"
                else:
                    provider = "Unknown"
                
                # Try to extract price
                price_match = re.search(r'\$?(\d+(?:\.\d{2})?)', line)
                price = float(price_match.group(1)) if price_match else 0.0
                
                cab = Transportation(
                    id=f"{trans_type}_text_{idx}",
                    type=trans_type,
                    origin=origin,
                    destination=destination,
                    price=price,
                    price_per_person=price / travelers if price > 0 else None,
                    provider=provider,
                    carbon_emissions_kg=2.4,  # Default estimate for short trips
                    carbon_score="low",
                    details={"extracted_from": "text"}
                )
                cabs.append(cab)
        
        return cabs

