"""
FlightSearchAgent - Specialized agent for finding flight options
Uses web search to find real flight data
"""

from typing import Dict, Any, Optional, List
from shared.types import TripRequest, Transportation
from agents.gemini_search_agent import GeminiSearchAgent
import json
import re
from datetime import datetime


class FlightSearchAgent:
    """Agent specialized in finding flight options"""
    
    def __init__(self):
        self.web_search = GeminiSearchAgent()
        self.max_flights = 5
    
    async def initialize(self):
        """Initialize the agent"""
        await self.web_search.initialize()
    
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: Optional[str] = None,
        travelers: int = 1,
        budget: Optional[float] = None
    ) -> List[Transportation]:
        """
        Search for flight options using specific flight booking sites
        
        Args:
            origin: Origin location (city/airport code)
            destination: Destination location (city/airport code)
            departure_date: Departure date (YYYY-MM-DD)
            travelers: Number of travelers
            budget: Budget constraint
            
        Returns:
            List of Transportation objects (max 5)
        """
        # Build custom prompt targeting specific flight booking sites
        date_str = f" on {departure_date}" if departure_date else ""
        budget_str = f" under ${budget}" if budget else ""
        
        custom_prompt = f"""Search for flight prices and options from {origin} to {destination}{date_str} for {travelers} traveler(s){budget_str}.

Please search on these specific flight booking websites:
1. Google Flights (https://www.google.com/travel/flights)
2. Skyscanner (https://www.skyscanner.com)
3. Kayak (https://www.kayak.com/flights)
4. Expedia (https://www.expedia.com/Flights)
5. Momondo (https://www.momondo.com/flights)

For each flight option found, extract and return:
- Airline name (e.g., United Airlines, Delta, Lufthansa, SWISS)
- Exact price in USD (total price for all travelers)
- Price per person
- Flight duration (in hours and minutes)
- Departure and arrival times (if available)
- Number of stops/transfers
- Direct booking URL or link to the booking site
- Departure airport code (e.g., JFK, EWR, LAX)
- Arrival airport code (e.g., ZRH, CDG, NRT)

Return up to {self.max_flights} flight options with the best prices and most convenient schedules.
Focus on finding real, current prices from these booking sites."""
        
        # Perform web search with custom prompt
        search_results = await self.web_search.search(
            custom_prompt=custom_prompt,
            format_json=True
        )
        
        # Parse results
        flights = self._parse_flight_results(
            search_results["results"],
            origin,
            destination,
            travelers
        )
        
        # Limit to max flights and sort by price
        flights = sorted(flights, key=lambda x: x.price)[:self.max_flights]
        
        return flights
    
    def _parse_flight_results(
        self,
        output: str,
        origin: str,
        destination: str,
        travelers: int
    ) -> List[Transportation]:
        """Parse flight search results into Transportation objects"""
        flights = []
        
        # Try multiple JSON extraction methods
        json_data = None
        
        # Method 1: Look for ```json blocks
        if "```json" in output:
            try:
                json_start = output.find("```json") + 7
                json_end = output.find("```", json_start)
                if json_end > json_start:
                    json_str = output[json_start:json_end].strip()
                    json_data = json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Method 2: Look for JSON objects in the text
        if json_data is None:
            try:
                # Try to find JSON array or object
                json_match = re.search(r'\{[^{}]*"flights"[^{}]*\[.*?\]', output, re.DOTALL)
                if json_match:
                    json_data = json.loads(json_match.group(0))
            except (json.JSONDecodeError, ValueError, AttributeError):
                pass
        
        # Method 3: Try to parse entire output as JSON
        if json_data is None:
            try:
                json_data = json.loads(output)
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Extract flight list from JSON
        if json_data:
            try:
                if isinstance(json_data, list):
                    flight_list = json_data
                elif isinstance(json_data, dict):
                    flight_list = json_data.get("flights", json_data.get("results", json_data.get("options", [])))
                    if not isinstance(flight_list, list) and isinstance(flight_list, dict):
                        flight_list = [flight_list]
                else:
                    flight_list = []
                
                for idx, flight_data in enumerate(flight_list[:self.max_flights]):
                    if isinstance(flight_data, dict):
                        flight = self._create_flight_from_dict(
                            flight_data, origin, destination, travelers, idx
                        )
                        if flight and flight.price > 0:  # Only add flights with valid prices
                            flights.append(flight)
            except (KeyError, ValueError, TypeError) as e:
                print(f"Error processing flight JSON: {e}")
        
        # If no valid flights from JSON, try text extraction
        if not flights:
            flights = self._extract_flights_from_text(output, origin, destination, travelers)
        
        # Also try extracting from raw output even if we got some from JSON
        # This helps catch flights that weren't in JSON format
        if len(flights) < self.max_flights:
            additional_flights = self._extract_flights_from_text(output, origin, destination, travelers)
            # Add flights that aren't duplicates
            existing_prices = {f.price for f in flights if f.price > 0}
            for flight in additional_flights:
                if flight.price > 0 and flight.price not in existing_prices:
                    flights.append(flight)
                    existing_prices.add(flight.price)
                    if len(flights) >= self.max_flights:
                        break
        
        return flights[:self.max_flights]
    
    def _create_flight_from_dict(
        self,
        data: Dict[str, Any],
        origin: str,
        destination: str,
        travelers: int,
        idx: int
    ) -> Optional[Transportation]:
        """Create Transportation object from flight data"""
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
                # Try to parse "8h 30m" format
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
            
            # Get airline/provider - try multiple fields and extract from text if needed
            provider = data.get("airline", data.get("provider", data.get("carrier", data.get("airline_name", ""))))
            if not provider or provider == "":
                # Try to extract from description or other fields
                desc = str(data.get("description", data.get("details", "")))
                airline_match = re.search(r'(United|Delta|American|Lufthansa|SWISS|British Airways|Air France|KLM|Emirates|Qatar|Singapore Airlines|Japan Airlines|ANA|Alaska|JetBlue|Southwest)', desc, re.IGNORECASE)
                if airline_match:
                    provider = airline_match.group(1)
            if not provider or provider == "":
                provider = "Unknown Airline"
            if isinstance(provider, list):
                provider = ", ".join([str(p) for p in provider if p])
            provider = str(provider).strip()
            
            # Calculate carbon emissions (rough estimate: ~0.25 kg CO2 per km per passenger)
            # Estimate distance from duration (average flight speed ~800 km/h)
            carbon_emissions_kg = None
            if duration_minutes:
                distance_km = (800 * duration_minutes) / 60
                carbon_emissions_kg = round(distance_km * 0.25 * travelers, 2)
            
            return Transportation(
                id=f"flight_{idx}_{hash(str(data)) % 10000}",
                type="flight",
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
                carbon_score="high" if carbon_emissions_kg and carbon_emissions_kg > 200 else "medium",
                transfers=data.get("stops", data.get("transfers", 0)),
                comfort_level=data.get("class", data.get("comfort_level", "economy")),
                amenities=data.get("amenities", ["Meals", "Entertainment"]),
                details=data.get("details", {})
            )
        except (KeyError, ValueError, TypeError) as e:
            print(f"Error creating flight: {e}")
            return None
    
    def _extract_flights_from_text(
        self,
        text: str,
        origin: str,
        destination: str,
        travelers: int
    ) -> List[Transportation]:
        """Extract flight info from unstructured text (fallback)"""
        flights = []
        
        # Common airline names to look for
        airlines = [
            "United Airlines", "Delta", "American Airlines", "Lufthansa", "SWISS",
            "British Airways", "Air France", "KLM", "Emirates", "Qatar Airways",
            "Singapore Airlines", "Japan Airlines", "ANA", "Alaska Airlines",
            "JetBlue", "Southwest", "Virgin Atlantic", "Turkish Airlines"
        ]
        
        # Look for price patterns with airline mentions
        price_pattern = r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        airline_pattern = r'(' + '|'.join([re.escape(a) for a in airlines]) + r')'
        
        # Split into sentences/paragraphs
        paragraphs = re.split(r'\n\n|\n(?=[A-Z])', text)
        
        for idx, para in enumerate(paragraphs[:self.max_flights]):
            para_lower = para.lower()
            if any(word in para_lower for word in ["flight", "airline", "fly", "airport"]):
                # Extract price
                price_matches = re.findall(price_pattern, para)
                price = 0.0
                if price_matches:
                    try:
                        price = float(price_matches[0].replace(',', ''))
                    except (ValueError, IndexError):
                        pass
                
                # Extract airline
                airline_match = re.search(airline_pattern, para, re.IGNORECASE)
                provider = airline_match.group(1) if airline_match else "Unknown Airline"
                
                # Extract duration if mentioned
                duration_minutes = None
                duration_match = re.search(r'(\d+)\s*(?:hours?|hrs?|h)\s*(?:(\d+)\s*(?:minutes?|mins?|m))?', para_lower)
                if duration_match:
                    hours = int(duration_match.group(1))
                    mins = int(duration_match.group(2)) if duration_match.group(2) else 0
                    duration_minutes = hours * 60 + mins
                
                # Only add if we found a price
                if price > 0:
                    flight = Transportation(
                        id=f"flight_text_{idx}",
                        type="flight",
                        origin=origin,
                        destination=destination,
                        price=price,
                        price_per_person=price / travelers if price > 0 else None,
                        provider=provider,
                        duration_minutes=duration_minutes,
                        carbon_emissions_kg=250.0,  # Default estimate
                        carbon_score="high",
                        details={"extracted_from": "text"}
                    )
                    flights.append(flight)
        
        return flights

