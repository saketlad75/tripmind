"""
TrainSearchAgent - Specialized agent for finding train options
Uses web search to find real train data
"""

from typing import Dict, Any, Optional, List
from shared.types import Transportation
from agents.gemini_search_agent import GeminiSearchAgent
import json
import re
from datetime import datetime


class TrainSearchAgent:
    """Agent specialized in finding train options"""
    
    def __init__(self):
        self.web_search = GeminiSearchAgent()
    
    async def initialize(self):
        """Initialize the agent"""
        await self.web_search.initialize()
    
    async def search_trains(
        self,
        origin: str,
        destination: str,
        departure_date: Optional[str] = None,
        travelers: int = 1,
        budget: Optional[float] = None
    ) -> List[Transportation]:
        """
        Search for train options using specific train booking sites
        
        Args:
            origin: Origin location (city/station)
            destination: Destination location (city/station)
            departure_date: Departure date (YYYY-MM-DD)
            travelers: Number of travelers
            budget: Budget constraint
            
        Returns:
            List of Transportation objects
        """
        # Build custom prompt targeting specific train booking sites
        date_str = f" on {departure_date}" if departure_date else ""
        budget_str = f" under ${budget}" if budget else ""
        
        custom_prompt = f"""Search for train ticket prices and options from {origin} to {destination}{date_str} for {travelers} traveler(s){budget_str}.

Please search on these specific train booking websites:
1. Trainline (https://www.thetrainline.com) - for Europe
2. Rail Europe (https://www.raileurope.com) - for European trains
3. Eurail (https://www.eurail.com) - for European rail passes
4. Amtrak (https://www.amtrak.com) - for US trains
5. SNCF (https://www.sncf-connect.com) - for French trains
6. Deutsche Bahn (https://www.bahn.com) - for German trains
7. Omio (https://www.omio.com) - for trains across Europe

For each train option found, extract and return:
- Railway operator name (e.g., SNCF, Deutsche Bahn, Eurostar, Amtrak)
- Exact price in USD (total price for all travelers)
- Price per person
- Train duration (in hours and minutes)
- Departure and arrival times (if available)
- Number of transfers/changes
- Direct booking URL or link to the booking site
- Departure station name
- Arrival station name
- Train class (economy, first class, etc.)

Return train options with real, current prices from these booking sites.
Focus on finding the most convenient and affordable options."""
        
        # Perform web search with custom prompt
        search_results = await self.web_search.search(
            custom_prompt=custom_prompt,
            format_json=True
        )
        
        # Parse results
        trains = self._parse_train_results(
            search_results["results"],
            origin,
            destination,
            travelers
        )
        
        return trains
    
    def _parse_train_results(
        self,
        output: str,
        origin: str,
        destination: str,
        travelers: int
    ) -> List[Transportation]:
        """Parse train search results into Transportation objects"""
        trains = []
        
        # Check if output indicates no direct train route
        if any(phrase in output.lower() for phrase in [
            "no direct train", "no train route", "not possible", 
            "across the atlantic", "no rail connection", "cannot travel by train"
        ]):
            return trains  # Return empty list if no direct route
        
        # Try to extract JSON
        try:
            if "```json" in output:
                json_start = output.find("```json") + 7
                json_end = output.find("```", json_start)
                json_str = output[json_start:json_end].strip()
                data = json.loads(json_str)
                
                if isinstance(data, list):
                    train_list = data
                elif isinstance(data, dict):
                    train_list = data.get("trains", data.get("results", []))
                else:
                    train_list = []
                
                for idx, train_data in enumerate(train_list):
                    train = self._create_train_from_dict(
                        train_data, origin, destination, travelers, idx
                    )
                    if train:
                        trains.append(train)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing train JSON: {e}")
        
        # If no JSON found, try text extraction
        if not trains:
            trains = self._extract_trains_from_text(output, origin, destination, travelers)
        
        return trains
    
    def _create_train_from_dict(
        self,
        data: Dict[str, Any],
        origin: str,
        destination: str,
        travelers: int,
        idx: int
    ) -> Optional[Transportation]:
        """Create Transportation object from train data"""
        try:
            # Parse price - handle various formats
            price = 0.0
            price_str = str(data.get("price", data.get("total_price", data.get("cost", "0"))))
            
            # Try to extract numeric value from strings like "From $192" or "$500-$800"
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
            
            # Parse times
            departure_time = None
            arrival_time = None
            if "departure_time" in data and data["departure_time"]:
                try:
                    departure_time = datetime.fromisoformat(str(data["departure_time"]).replace('Z', '+00:00'))
                except:
                    pass
            if "arrival_time" in data and data["arrival_time"]:
                try:
                    arrival_time = datetime.fromisoformat(str(data["arrival_time"]).replace('Z', '+00:00'))
                except:
                    pass
            
            # Get operator - try multiple fields
            provider = data.get("operator", data.get("provider", data.get("railway", data.get("railway_operator", ""))))
            if not provider or provider == "":
                desc = str(data.get("description", data.get("details", "")))
                railway_match = re.search(r'(SNCF|Deutsche Bahn|Eurostar|Amtrak|TGV|ICE|Thalys|Renfe|Trenitalia|Rail Europe)', desc, re.IGNORECASE)
                if railway_match:
                    provider = railway_match.group(1)
            if not provider or provider == "":
                provider = "Unknown Railway"
            if isinstance(provider, list):
                provider = ", ".join([str(p) for p in provider if p])
            provider = str(provider).strip()
            
            # Filter out invalid providers (airlines mixed with trains)
            airline_keywords = ["united airlines", "lufthansa", "delta", "air france", "british airways", "american airlines"]
            if any(airline in provider.lower() for airline in airline_keywords):
                # Skip this train - it's mixing airline and train
                return None
            
            # Calculate carbon emissions (rough estimate: ~0.04 kg CO2 per km per passenger)
            # Estimate distance from duration (average train speed ~150 km/h)
            carbon_emissions_kg = None
            if duration_minutes:
                distance_km = (150 * duration_minutes) / 60
                carbon_emissions_kg = round(distance_km * 0.04 * travelers, 2)
            
            return Transportation(
                id=f"train_{idx}_{abs(hash(str(data)) % 10000)}",
                type="train",
                origin=data.get("origin", origin),
                destination=data.get("destination", destination),
                departure_time=departure_time,
                arrival_time=arrival_time,
                duration_minutes=duration_minutes,
                price=price,
                price_per_person=price_per_person,
                provider=str(provider),
                booking_url=data.get("booking_url", data.get("url", data.get("link"))),
                carbon_emissions_kg=carbon_emissions_kg,
                carbon_score="low" if carbon_emissions_kg and carbon_emissions_kg < 50 else "medium",
                transfers=data.get("transfers", data.get("changes", 0)),
                comfort_level=data.get("class", data.get("comfort_level", "economy")),
                amenities=data.get("amenities", ["Wi-Fi", "Power Outlets"]),
                details=data.get("details", {})
            )
        except (KeyError, ValueError, TypeError) as e:
            print(f"Error creating train: {e}")
            return None
    
    def _extract_trains_from_text(
        self,
        text: str,
        origin: str,
        destination: str,
        travelers: int
    ) -> List[Transportation]:
        """Extract train info from unstructured text (fallback)"""
        trains = []
        lines = text.split("\n")
        
        for idx, line in enumerate(lines[:5]):
            if any(word in line.lower() for word in ["train", "railway", "rail"]):
                price_match = re.search(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', line)
                price = float(price_match.group(1).replace(',', '')) if price_match else 0.0
                
                train = Transportation(
                    id=f"train_text_{idx}",
                    type="train",
                    origin=origin,
                    destination=destination,
                    price=price,
                    price_per_person=price / travelers if price > 0 else None,
                    provider="Unknown Railway",
                    carbon_emissions_kg=20.0,  # Default estimate
                    carbon_score="low",
                    details={"extracted_from": "text"}
                )
                trains.append(train)
        
        return trains

