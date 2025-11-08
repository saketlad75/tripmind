"""
StayAgent - Finds accommodations using Google Gemini API
Searches for properties via web search and AI reasoning
Filters by amenities, reviews, photos
"""

from typing import Dict, Any, Optional, List
import google.generativeai as genai
from shared.types import TripRequest, Accommodation, UserProfile
import json
import os
import asyncio
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_exception_message
)

load_dotenv()


class StayAgent:
    """Agent responsible for finding suitable accommodations"""
    
    def __init__(self, llm=None):
        """
        Initialize StayAgent
        
        Args:
            llm: Not used (kept for compatibility with orchestrator)
        """
        self.model = None
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    async def initialize(self):
        """Initialize Gemini client"""
        # Check for API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your_google_api_key_here":
            raise ValueError(
                "GOOGLE_API_KEY not set. Please set it in your .env file. "
                "Get your API key at https://makersuite.google.com/app/apikey"
            )
        
        genai.configure(api_key=api_key)
        # Use the specified model name (will be validated by the API)
        self.model = genai.GenerativeModel(self.model_name)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_message(match=r".*(rate limit|429|quota|too many requests|resource exhausted).*"),
        reraise=True
    )
    async def _run_with_retry(self, prompt: str):
        """Run Gemini with retry logic for rate limits"""
        response = await asyncio.to_thread(
            self.model.generate_content,
            prompt
        )
        # Create a simple result object similar to Dedalus format
        class Result:
            def __init__(self, text):
                self.final_output = text
        return Result(response.text)
    
    async def process(self, request: TripRequest, user_profile: Optional[UserProfile] = None) -> Dict[str, Any]:
        """
        Process trip request to find accommodations
        
        Args:
            request: TripRequest with user's trip requirements
            
        Returns:
            Dictionary with accommodations and metadata
        """
        if not self.model:
            await self.initialize()
        
        # Build the prompt for accommodation search
        prompt = self._build_search_prompt(request, user_profile)
        
        # Run Gemini API (with rate limit handling)
        try:
            result = await self._run_with_retry(prompt)
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg or "quota" in error_msg or "resource exhausted" in error_msg:
                raise RuntimeError(
                    "API rate limit exceeded. Please wait a few minutes and try again. "
                    "The Google Gemini API has usage limits. Consider upgrading your plan or waiting before retrying."
                ) from e
            raise RuntimeError(
                f"Error calling Google Gemini API: {str(e)}. "
                "Make sure GOOGLE_API_KEY is set correctly."
            ) from e
        
        # Parse and structure the results
        accommodations = self._parse_results(result.final_output, request)
        
        # Handle cases where fewer accommodations are found
        count = len(accommodations)
        min_preferred = 3
        
        if count == 0:
            print("Warning: No accommodations found in the specified area")
        elif count == 1:
            print(f"Note: Only 1 accommodation found in this area. Suggesting this option.")
        elif count < min_preferred:
            print(f"Note: Found {count} accommodations (preferred: {min_preferred}). All available options are shown.")
        
        return {
            "accommodations": accommodations,
            "raw_output": result.final_output,
            "count": count,
            "meets_minimum": count >= min_preferred,
            "message": self._get_accommodation_message(count)
        }
    
    def _build_search_prompt(self, request: TripRequest, user_profile: Optional[UserProfile] = None) -> str:
        """Build a detailed prompt for accommodation search"""
        prompt_parts = [
            f"I need help finding accommodations for a trip.",
            f"\nUser's Trip Description:",
            f'"{request.prompt}"',
            f"\nIMPORTANT: Extract the destination/location from the trip description above.",
        ]
        
        # Add duration if available
        if request.start_date and request.end_date:
            prompt_parts.append(f"\nTrip Dates: {request.start_date} to {request.end_date}")
        elif request.duration_days:
            prompt_parts.append(f"\nTrip Duration: {request.duration_days} days")
        
        prompt_parts.append(f"Number of travelers: {request.travelers}")
        
        # Budget from user profile or request
        budget = request.budget
        if not budget and user_profile and user_profile.budget:
            budget = user_profile.budget
        
        if budget:
            prompt_parts.append(f"Total Budget: ${budget:.2f} USD")
            # Calculate approximate budget per night
            duration = request.duration_days or (
                (request.end_date - request.start_date).days 
                if request.start_date and request.end_date else 1
            )
            budget_per_night = budget / duration if duration > 0 else budget
            prompt_parts.append(f"Approximate budget per night: ${budget_per_night:.2f}")
        
        # Add user profile preferences if available
        if user_profile:
            if user_profile.disability_needs:
                prompt_parts.append(f"\nAccessibility Requirements: {', '.join(user_profile.disability_needs)}")
        
        prompt_parts.extend([
            "\nPlease help me find accommodations by:",
            "1. EXTRACTING the destination/location from the trip description",
            "2. Finding available hotel/accommodation options in that location (preferably 3+, but include all available options)",
            "3. Ensuring prices fit within the budget range",
            "4. Including properties that match any accessibility requirements",
            "",
            "For each accommodation, provide:",
            "- Property name and description",
            "- Exact address and location coordinates (lat, lng)",
            "- Price per night and total cost for the trip duration",
            "- Amenities (especially Wi-Fi, parking, etc.)",
            "- Reviews and ratings",
            "- Photos and property details",
            "- Booking links or URLs",
            "",
            "IMPORTANT REQUIREMENTS:",
            "- Find ALL available accommodation options in the location (aim for 3+, but include all you find)",
            "- If only 1-2 options are available in the area, include those",
            "- All accommodations must be in the location extracted from the trip description",
            "- Prices should be within the specified budget range",
            "- Provide real, bookable properties with actual prices",
            "- If very few options exist, mention this in your response",
            "",
            "Please format your response as JSON with the following structure:",
            "```json",
            "{",
            '  "accommodations": [',
            "    {",
            '      "id": "unique_id",',
            '      "title": "Property name",',
            '      "description": "Detailed description",',
            '      "address": "Full address with city and country",',
            '      "location": {"lat": 0.0, "lng": 0.0},',
            '      "price_per_night": 0.0,',
            '      "amenities": ["Wi-Fi", "Parking", ...],',
            '      "rating": 4.5,',
            '      "review_count": 100,',
            '      "images": ["url1", "url2"],',
            '      "booking_url": "https://...",',
            '      "source": "airbnb"',
            "    }",
            "    // ... include all available accommodations (preferably 3+, but include all found)",
            "  ]",
            "}",
            "```"
        ])
        
        return "\n".join(prompt_parts)
    
    def _get_accommodation_message(self, count: int) -> str:
        """Get appropriate message based on accommodation count"""
        if count == 0:
            return "No accommodations found in the specified area. Please try a different location or adjust your search criteria."
        elif count == 1:
            return "Only 1 accommodation found in this area. This is the available option."
        elif count == 2:
            return f"Found {count} accommodations in this area. Both options are shown."
        elif count >= 3:
            return f"Found {count} accommodations in this area. Here are the available options."
        else:
            return f"Found {count} accommodation(s) in this area."
    
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

