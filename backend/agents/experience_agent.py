"""
ExperienceAgent - Finds local experiences and activities using Google Gemini
Uses user context (occupation, interests) to personalize recommendations
"""

from typing import Dict, Any, Optional, List
from agents.gemini_search_agent import GeminiSearchAgent
from shared.types import TripRequest, Experience
import json
import os
from dotenv import load_dotenv

load_dotenv()


class ExperienceAgent:
    """Agent responsible for finding local experiences and activities"""
    
    def __init__(self, llm=None):
        """
        Initialize ExperienceAgent
        
        Args:
            llm: Not used (kept for compatibility with orchestrator)
        """
        self.gemini_agent = GeminiSearchAgent()
    
    async def initialize(self):
        """Initialize Gemini search agent"""
        await self.gemini_agent.initialize()
    
    async def process(
        self, 
        request: TripRequest, 
        stay_results: Optional[Dict[str, Any]] = None,
        user_context: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        Process experience request
        
        Args:
            request: TripRequest with user's trip requirements
            stay_results: Results from StayAgent (for location context)
            user_context: Additional user context (occupation, interests, etc.)
            
        Returns:
            Dictionary with experiences and metadata
        """
        if not self.gemini_agent.model:
            await self.initialize()
        
        # Build the prompt for experience search
        prompt = self._build_search_prompt(request, stay_results, user_context)
        
        # Search using Gemini
        try:
            result = await self.gemini_agent.search(prompt, format_json=True)
            output = result.get("results", result.get("raw_output", ""))
        except Exception as e:
            raise RuntimeError(
                f"Error calling Gemini: {str(e)}. "
                "Make sure GEMINI_API_KEY is set correctly."
            ) from e
        
        # Parse and structure the results
        experiences = self._parse_results(output, request)
        
        # Validate minimum requirements
        min_required = 3
        if len(experiences) < min_required:
            print(f"Warning: Only found {len(experiences)} experiences, minimum {min_required} required")
        
        return {
            "experiences": experiences,
            "raw_output": output,
            "count": len(experiences),
            "meets_minimum": len(experiences) >= min_required
        }
    
    def _build_search_prompt(
        self,
        request: TripRequest,
        stay_results: Optional[Dict[str, Any]] = None,
        user_context: Optional[dict] = None
    ) -> str:
        """Build a detailed prompt for experience search"""
        prompt_parts = [
            f"I need help finding local experiences and activities for a trip.",
            f"\nUser's Trip Description:",
            f'"{request.prompt}"',
            f"\nIMPORTANT: Extract the destination/location and activity preferences from the trip description above.",
            f"\nNOTE: The trip description above has PRIORITY. If it conflicts with user profile data, use the trip description.",
        ]
        
        # Add destination from request or stay results
        if request.destination:
            prompt_parts.append(f"\nDestination: {request.destination}")
        elif stay_results and stay_results.get("accommodations"):
            acc = stay_results["accommodations"][0]
            if hasattr(acc, 'address') and acc.address:
                prompt_parts.append(f"\nLocation: {acc.address}")
        
        # Add duration
        if request.duration_days:
            prompt_parts.append(f"Trip Duration: {request.duration_days} days")
        
        # Add user context for personalization
        if user_context:
            context_parts = []
            if user_context.get('occupation'):
                context_parts.append(f"User's occupation: {user_context['occupation']}")
            if user_context.get('home_city'):
                context_parts.append(f"User's home city: {user_context['home_city']}")
            if context_parts:
                prompt_parts.append(f"\nUser Context: {', '.join(context_parts)}")
        
        prompt_parts.extend([
            "\nPlease help me find experiences and activities by:",
            "1. Finding activities that match the trip description (HIGHEST PRIORITY)",
            "2. Considering user's occupation and interests for personalization",
            "3. Including a mix of:",
            "   - Cultural experiences (museums, galleries, historical sites, monuments)",
            "   - Outdoor activities (hiking, parks, nature tours, beaches)",
            "   - Entertainment (shows, concerts, nightlife, events)",
            "   - Local experiences (food tours, cooking classes, workshops, local markets)",
            "   - Adventure activities (if mentioned in trip description)",
            "4. Ensuring activities are suitable for the trip duration",
            "5. Finding activities near the destination/accommodation location",
            "",
            "For each experience, provide:",
            "- Activity/experience name",
            "- Description and what makes it special",
            "- Category (hiking, food, culture, entertainment, outdoor, adventure, etc.)",
            "- Exact location and address with coordinates (lat, lng)",
            "- Duration/time required (in hours)",
            "- Price range or cost (per person if applicable)",
            "- Ratings and review counts",
            "- Best time to visit (time of day, season, etc.)",
            "- Booking information (URL if available)",
            "- Images/photos if available",
            "- Source (TripAdvisor, Viator, GetYourGuide, etc.)",
            "",
            "IMPORTANT REQUIREMENTS:",
            "- Find MINIMUM 3-5 experiences/activities",
            "- Focus on activities mentioned in the trip description first",
            "- All activities must be in or near the destination location",
            "- Provide real, bookable experiences with actual information",
            "- Include a variety of categories (not all the same type)",
            "- Consider the trip duration when selecting activities",
            "",
            "Please format your response as JSON with the following structure:",
            "```json",
            "{",
            '  "experiences": [',
            "    {",
            '      "id": "unique_id",',
            '      "name": "Experience/Activity name",',
            '      "description": "Detailed description and what makes it special",',
            '      "category": "hiking/food/culture/entertainment/outdoor/adventure/etc",',
            '      "address": "Full address with city and country",',
            '      "location": {"lat": 0.0, "lng": 0.0},',
            '      "duration_hours": 2.5,',
            '      "price": 50.0,',
            '      "rating": 4.5,',
            '      "review_count": 100,',
            '      "best_time_to_visit": "Morning, 9am-12pm",',
            '      "booking_url": "https://...",',
            '      "images": ["url1", "url2"],',
            '      "source": "tripadvisor"',
            "    }",
            "    // ... at least 2-4 more experiences",
            "  ]",
            "}",
            "```"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_results(self, output: str, request: TripRequest) -> List[Experience]:
        """
        Parse Gemini output into structured Experience objects
        
        Args:
            output: Raw output from Gemini
            request: Original trip request
            
        Returns:
            List of Experience objects
        """
        experiences = []
        
        # Try to extract structured data from the output
        try:
            # Attempt to parse JSON if present
            if "```json" in output:
                json_start = output.find("```json") + 7
                json_end = output.find("```", json_start)
                json_str = output[json_start:json_end].strip()
                data = json.loads(json_str)
                
                if isinstance(data, list):
                    for item in data:
                        exp = self._create_experience_from_dict(item)
                        if exp:
                            experiences.append(exp)
                elif isinstance(data, dict) and "experiences" in data:
                    for item in data["experiences"]:
                        exp = self._create_experience_from_dict(item)
                        if exp:
                            experiences.append(exp)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing experiences JSON: {e}")
            pass
        
        # If no structured data found, try to extract from text
        if not experiences:
            # Try to find JSON without code blocks
            try:
                # Look for JSON object directly
                json_start = output.find("{")
                if json_start != -1:
                    json_end = output.rfind("}") + 1
                    if json_end > json_start:
                        json_str = output[json_start:json_end]
                        data = json.loads(json_str)
                        
                        if isinstance(data, list):
                            for item in data:
                                exp = self._create_experience_from_dict(item)
                                if exp:
                                    experiences.append(exp)
                        elif isinstance(data, dict) and "experiences" in data:
                            for item in data["experiences"]:
                                exp = self._create_experience_from_dict(item)
                                if exp:
                                    experiences.append(exp)
            except (json.JSONDecodeError, ValueError):
                pass
        
        # If still no experiences, create a placeholder from text
        if not experiences:
            exp = self._extract_from_text(output, request)
            if exp:
                experiences.append(exp)
        
        return experiences
    
    def _create_experience_from_dict(self, data: Dict[str, Any]) -> Optional[Experience]:
        """Create Experience object from dictionary"""
        try:
            # Extract location
            location = {"lat": 0.0, "lng": 0.0}
            if "location" in data:
                if isinstance(data["location"], dict):
                    location = {
                        "lat": float(data["location"].get("lat", 0.0)),
                        "lng": float(data["location"].get("lng", 0.0))
                    }
            
            # Extract price
            price = None
            if "price" in data:
                try:
                    price = float(data["price"])
                except (ValueError, TypeError):
                    pass
            
            # Extract duration
            duration_hours = None
            if "duration_hours" in data:
                try:
                    duration_hours = float(data["duration_hours"])
                except (ValueError, TypeError):
                    pass
            
            return Experience(
                id=data.get("id", f"exp_{hash(data.get('name', ''))}"),
                name=data.get("name", "Unknown Experience"),
                description=data.get("description", ""),
                category=data.get("category", "general"),
                location=location,
                address=data.get("address", ""),
                price=price,
                duration_hours=duration_hours,
                rating=data.get("rating"),
                review_count=data.get("review_count"),
                images=data.get("images", []),
                booking_url=data.get("booking_url", data.get("url")),
                source=data.get("source", "tripadvisor")
            )
        except (KeyError, ValueError, TypeError) as e:
            print(f"Error creating experience: {e}")
            return None
    
    def _extract_from_text(self, text: str, request: TripRequest) -> Optional[Experience]:
        """Extract experience info from unstructured text (fallback)"""
        # This is a basic fallback - in production, you'd want more sophisticated parsing
        lines = text.split("\n")
        name = "Experience Recommendation"
        description = text[:500]  # First 500 chars
        
        # Try to find name in first few lines
        for line in lines[:5]:
            if line.strip() and len(line.strip()) < 100:
                name = line.strip()
                break
        
        # Try to find price mentions
        price = None
        for line in lines:
            if "$" in line or "USD" in line or "price" in line.lower():
                import re
                prices = re.findall(r'\$?(\d+(?:\.\d{2})?)', line)
                if prices:
                    try:
                        price = float(prices[0])
                        break
                    except ValueError:
                        pass
        
        return Experience(
            id="exp_text_1",
            name=name,
            description=description,
            category="general",
            location={"lat": 0.0, "lng": 0.0},
            address="",
            price=price,
            duration_hours=None,
            rating=None,
            review_count=None,
            images=[],
            booking_url=None,
            source="unknown"
        )
