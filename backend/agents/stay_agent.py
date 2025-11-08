"""
StayAgent - Finds accommodations using Dedalus Labs
Searches for properties via Airbnb API or embeddings search
Filters by amenities, reviews, photos
"""

from typing import Dict, Any, Optional, List
from dedalus_labs import AsyncDedalus, DedalusRunner
from shared.types import TripRequest, Accommodation
import json
import os
from dotenv import load_dotenv

load_dotenv()


class StayAgent:
    """Agent responsible for finding suitable accommodations"""
    
    def __init__(self, llm=None):
        """
        Initialize StayAgent
        
        Args:
            llm: Not used with Dedalus Labs (kept for compatibility with orchestrator)
        """
        self.client = None
        self.runner = None
        self.mcp_servers = [
            "joerup/exa-mcp",           # For semantic travel research
            "windsor/brave-search-mcp",  # For travel information search
        ]
        # Use GPT-5 or GPT-4.1 for better tool calling (as per Dedalus docs)
        self.model = os.getenv("DEDALUS_MODEL", "openai/gpt-4.1")
    
    async def initialize(self):
        """Initialize Dedalus client and runner"""
        # Check for API key
        api_key = os.getenv("DEDALUS_API_KEY")
        if not api_key or api_key == "your_dedalus_api_key_here":
            raise ValueError(
                "DEDALUS_API_KEY not set. Please set it in your .env file. "
                "Get your API key at https://dedaluslabs.ai"
            )
        
        self.client = AsyncDedalus()
        self.runner = DedalusRunner(self.client)
    
    async def process(self, request: TripRequest) -> Dict[str, Any]:
        """
        Process trip request to find accommodations
        
        Args:
            request: TripRequest with user's trip requirements
            
        Returns:
            Dictionary with accommodations and metadata
        """
        if not self.runner:
            await self.initialize()
        
        # Build the prompt for accommodation search
        prompt = self._build_search_prompt(request)
        
        # Run Dedalus with MCP servers
        try:
            result = await self.runner.run(
                input=prompt,
                model=self.model,
                mcp_servers=self.mcp_servers
            )
        except Exception as e:
            raise RuntimeError(
                f"Error calling Dedalus Labs: {str(e)}. "
                "Make sure DEDALUS_API_KEY is set correctly and you have access to the MCP servers."
            ) from e
        
        # Parse and structure the results
        accommodations = self._parse_results(result.final_output, request)
        
        return {
            "accommodations": accommodations,
            "raw_output": result.final_output,
            "count": len(accommodations)
        }
    
    def _build_search_prompt(self, request: TripRequest) -> str:
        """Build a detailed prompt for accommodation search"""
        prompt_parts = [
            f"I'm planning a trip and need help finding accommodations.",
            f"\nTrip Details:",
            f"- Description: {request.prompt}",
        ]
        
        if request.destination:
            prompt_parts.append(f"- Destination: {request.destination}")
        
        if request.start_date and request.end_date:
            prompt_parts.append(
                f"- Dates: {request.start_date} to {request.end_date}"
            )
        elif request.duration_days:
            prompt_parts.append(f"- Duration: {request.duration_days} days")
        
        if request.budget:
            prompt_parts.append(f"- Budget: ${request.budget:.2f} total")
        
        prompt_parts.append(f"- Number of travelers: {request.travelers}")
        
        if request.preferences:
            prompt_parts.append(f"- Preferences: {json.dumps(request.preferences, indent=2)}")
        
        prompt_parts.extend([
            "\nPlease help me find:",
            "1. Hotel/Airbnb/Accommodation options in the area",
            "2. Prices per night and total cost",
            "3. Amenities (especially Wi-Fi, parking, etc.)",
            "4. Reviews and ratings",
            "5. Photos and property details",
            "6. Booking links or URLs",
            "7. Location details (address, coordinates if possible)",
            "\nFocus on properties that match the trip description and preferences.",
            "Provide specific recommendations with details.",
            "\nIMPORTANT: Please format your response as JSON with the following structure:",
            "```json",
            "{",
            '  "accommodations": [',
            "    {",
            '      "id": "unique_id",',
            '      "title": "Property name",',
            '      "description": "Detailed description",',
            '      "address": "Full address",',
            '      "location": {"lat": 0.0, "lng": 0.0},',
            '      "price_per_night": 0.0,',
            '      "amenities": ["Wi-Fi", "Parking", ...],',
            '      "rating": 4.5,',
            '      "review_count": 100,',
            '      "images": ["url1", "url2"],',
            '      "booking_url": "https://...",',
            '      "source": "airbnb"',
            "    }",
            "  ]",
            "}",
            "```"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_results(self, output: str, request: TripRequest) -> List[Accommodation]:
        """
        Parse Dedalus output into structured Accommodation objects
        
        Args:
            output: Raw output from Dedalus
            request: Original trip request
            
        Returns:
            List of Accommodation objects
        """
        accommodations = []
        
        # Try to extract structured data from the output
        # This is a basic parser - you may need to enhance based on actual output format
        try:
            # Attempt to parse JSON if present
            if "```json" in output:
                json_start = output.find("```json") + 7
                json_end = output.find("```", json_start)
                json_str = output[json_start:json_end].strip()
                data = json.loads(json_str)
                
                if isinstance(data, list):
                    for item in data:
                        acc = self._create_accommodation_from_dict(item, request)
                        if acc:
                            accommodations.append(acc)
                elif isinstance(data, dict) and "accommodations" in data:
                    for item in data["accommodations"]:
                        acc = self._create_accommodation_from_dict(item, request)
                        if acc:
                            accommodations.append(acc)
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
        
        # If no structured data found, create a placeholder from the text
        if not accommodations:
            # Extract basic info from text output
            acc = self._extract_from_text(output, request)
            if acc:
                accommodations.append(acc)
        
        return accommodations
    
    def _create_accommodation_from_dict(self, data: Dict[str, Any], request: TripRequest) -> Optional[Accommodation]:
        """Create Accommodation object from dictionary"""
        try:
            # Calculate total price
            price_per_night = float(data.get("price_per_night", data.get("price", 0)))
            duration = request.duration_days or (
                (request.end_date - request.start_date).days 
                if request.start_date and request.end_date else 1
            )
            total_price = price_per_night * duration
            
            # Extract location
            location = {"lat": 0.0, "lng": 0.0}
            if "location" in data:
                if isinstance(data["location"], dict):
                    location = {
                        "lat": float(data["location"].get("lat", 0.0)),
                        "lng": float(data["location"].get("lng", 0.0))
                    }
            
            return Accommodation(
                id=data.get("id", f"acc_{len(data)}"),
                title=data.get("title", data.get("name", "Unknown Property")),
                description=data.get("description", ""),
                location=location,
                address=data.get("address", ""),
                price_per_night=price_per_night,
                total_price=total_price,
                amenities=data.get("amenities", []),
                rating=data.get("rating"),
                review_count=data.get("review_count"),
                images=data.get("images", []),
                booking_url=data.get("booking_url", data.get("url")),
                source=data.get("source", "airbnb")
            )
        except (KeyError, ValueError, TypeError) as e:
            print(f"Error creating accommodation: {e}")
            return None
    
    def _extract_from_text(self, text: str, request: TripRequest) -> Optional[Accommodation]:
        """Extract accommodation info from unstructured text (fallback)"""
        # This is a basic fallback - in production, you'd want more sophisticated parsing
        # or ask Dedalus to return structured JSON
        lines = text.split("\n")
        title = "Accommodation Recommendation"
        description = text[:500]  # First 500 chars
        
        # Try to find price mentions
        price_per_night = 0.0
        for line in lines:
            if "$" in line or "USD" in line or "price" in line.lower():
                # Simple price extraction (can be enhanced)
                import re
                prices = re.findall(r'\$?(\d+(?:\.\d{2})?)', line)
                if prices:
                    try:
                        price_per_night = float(prices[0])
                        break
                    except ValueError:
                        pass
        
        duration = request.duration_days or 1
        total_price = price_per_night * duration
        
        return Accommodation(
            id="acc_text_1",
            title=title,
            description=description,
            location={"lat": 0.0, "lng": 0.0},
            address="",
            price_per_night=price_per_night,
            total_price=total_price,
            amenities=[],
            rating=None,
            review_count=None,
            images=[],
            booking_url=None,
            source="unknown"
        )

