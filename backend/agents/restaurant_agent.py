"""
RestaurantAgent - Finds restaurants using Google Gemini API
Suggests restaurants near the selected accommodation
Considers user's budget and dietary preferences
"""

from typing import Dict, Any, Optional, List
import google.generativeai as genai
from shared.types import TripRequest, Restaurant, Accommodation, UserProfile
import json
import os
import asyncio
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_message
)

load_dotenv()


class RestaurantAgent:
    """Agent responsible for finding suitable restaurants near accommodation"""
    
    def __init__(self, llm=None):
        """
        Initialize RestaurantAgent
        
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
    
    async def process(
        self,
        request: TripRequest,
        stay_results: Optional[Dict[str, Any]] = None,
        user_profile: Optional[UserProfile] = None
    ) -> Dict[str, Any]:
        """
        Process restaurant search request
        
        Args:
            request: TripRequest with selected accommodation
            stay_results: Results from StayAgent
            user_profile: User profile with dietary preferences and budget
            
        Returns:
            Dictionary with restaurants and metadata
        """
        if not self.model:
            await self.initialize()
        
        # Get selected accommodation
        selected_accommodation = self._get_selected_accommodation(
            request, stay_results
        )
        
        if not selected_accommodation:
            return {
                "restaurants": [],
                "raw_output": "No accommodation selected",
                "count": 0,
                "error": "No accommodation selected. Please select an accommodation first."
            }
        
        # Build the prompt for restaurant search
        prompt = self._build_search_prompt(
            request, selected_accommodation, user_profile
        )
        
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
        restaurants = self._parse_results(
            result.final_output, request, selected_accommodation, user_profile
        )
        
        # Validate minimum requirements
        min_required = 3
        if len(restaurants) < min_required:
            print(f"Warning: Only found {len(restaurants)} restaurants/cafes, minimum {min_required} required")
        
        return {
            "restaurants": restaurants,
            "raw_output": result.final_output,
            "count": len(restaurants),
            "meets_minimum": len(restaurants) >= min_required,
            "selected_accommodation": selected_accommodation
        }
    
    def _get_selected_accommodation(
        self,
        request: TripRequest,
        stay_results: Optional[Dict[str, Any]]
    ) -> Optional[Accommodation]:
        """Get the selected accommodation from stay results"""
        if not stay_results or not stay_results.get("accommodations"):
            return None
        
        accommodations = stay_results["accommodations"]
        
        # If user specified an accommodation ID, find it
        if request.selected_accommodation_id:
            for acc in accommodations:
                if acc.id == request.selected_accommodation_id:
                    return acc
        
        # Otherwise, return the first one (or could be smart and pick best match)
        if accommodations:
            return accommodations[0]
        
        return None
    
    def _build_search_prompt(
        self,
        request: TripRequest,
        accommodation: Accommodation,
        user_profile: Optional[UserProfile]
    ) -> str:
        """Build a detailed prompt for restaurant search"""
        prompt_parts = [
            f"I need to find restaurants near a selected accommodation.",
            f"\nAccommodation Details:",
            f"- Name: {accommodation.title}",
            f"- Address: {accommodation.address}",
            f"- Location: {accommodation.location.get('lat', 0)}, {accommodation.location.get('lng', 0)}",
        ]
        
        # Add user preferences
        if user_profile:
            prompt_parts.append(f"\nUser Preferences:")
            
            if user_profile.dietary_preferences:
                prompt_parts.append(
                    f"- Dietary preferences: {', '.join(user_profile.dietary_preferences)}"
                )
            
            if user_profile.disability_needs:
                prompt_parts.append(
                    f"- Accessibility needs: {', '.join(user_profile.disability_needs)}"
                )
            
            # Budget consideration
            budget = request.budget or user_profile.budget
            if budget:
                # Allocate portion of budget for meals (e.g., 20-30%)
                meal_budget = budget * 0.25  # 25% of total budget for meals
                days = request.duration_days or 1
                daily_meal_budget = meal_budget / days
                prompt_parts.append(
                    f"- Budget: ${daily_meal_budget:.2f} per day for meals (out of ${budget:.2f} total budget)"
                )
        
        prompt_parts.extend([
            "\nPlease help me find restaurants and cafes by:",
            "1. Finding restaurants within walking distance or short drive from the accommodation",
            "2. Including BOTH restaurants AND cafes",
            "3. Ensuring they match dietary preferences and accessibility needs",
            "4. Ensuring prices fit within the budget constraints",
            "",
            "For each restaurant/cafe, provide:",
            "- Restaurant or cafe name",
            "- Cuisine type and specialties",
            "- Exact address and location coordinates (lat, lng)",
            "- Price range ($, $$, $$$, $$$$) and average cost per person",
            "- Ratings and reviews",
            "- Opening hours",
            "- Contact information (phone) and booking options",
            "- Available dietary options (vegetarian, vegan, gluten-free, etc.)",
            "- Accessibility features (wheelchair accessible, etc.)",
            "- Photos if available",
            "",
            "IMPORTANT REQUIREMENTS:",
            "- Find MINIMUM 3-4 restaurants and cafes (mix of both)",
            "- All must be near the accommodation location",
            "- Prices should fit within the daily meal budget",
            "- Must match dietary preferences if specified",
            "- Must have accessibility features if required",
            "- Provide real restaurants with actual information",
            "",
            "Please format your response as JSON with the following structure:",
            "```json",
            "{",
            '  "restaurants": [',
            "    {",
            '      "id": "unique_id",',
            '      "name": "Restaurant/Cafe name",',
            '      "description": "Description and specialties",',
            '      "cuisine_type": "Italian/Asian/Cafe/etc",',
            '      "address": "Full address",',
            '      "location": {"lat": 0.0, "lng": 0.0},',
            '      "price_range": "$$",',
            '      "average_price_per_person": 25.0,',
            '      "rating": 4.5,',
            '      "review_count": 100,',
            '      "dietary_options": ["vegetarian", "vegan", "gluten-free"],',
            '      "accessibility_features": ["wheelchair accessible"],',
            '      "images": ["url1", "url2"],',
            '      "booking_url": "https://...",',
            '      "phone": "+1234567890",',
            '      "opening_hours": "Mon-Sun: 11am-10pm",',
            '      "source": "tripadvisor"',
            "    }",
            "    // ... at least 2-3 more restaurants/cafes",
            "  ]",
            "}",
            "```"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_results(
        self,
        output: str,
        request: TripRequest,
        accommodation: Accommodation,
        user_profile: Optional[UserProfile]
    ) -> List[Restaurant]:
        """
        Parse Dedalus output into structured Restaurant objects
        
        Args:
            output: Raw output from Dedalus
            request: Original trip request
            accommodation: Selected accommodation
            user_profile: User profile
            
        Returns:
            List of Restaurant objects
        """
        restaurants = []
        
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
                        restaurant = self._create_restaurant_from_dict(item)
                        if restaurant:
                            restaurants.append(restaurant)
                elif isinstance(data, dict) and "restaurants" in data:
                    for item in data["restaurants"]:
                        restaurant = self._create_restaurant_from_dict(item)
                        if restaurant:
                            restaurants.append(restaurant)
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
        
        # If no structured data found, create a placeholder from the text
        if not restaurants:
            # Extract basic info from text output
            restaurant = self._extract_from_text(output)
            if restaurant:
                restaurants.append(restaurant)
        
        return restaurants
    
    def _create_restaurant_from_dict(self, data: Dict[str, Any]) -> Optional[Restaurant]:
        """Create Restaurant object from dictionary"""
        try:
            # Extract location
            location = {"lat": 0.0, "lng": 0.0}
            if "location" in data:
                if isinstance(data["location"], dict):
                    location = {
                        "lat": float(data["location"].get("lat", 0.0)),
                        "lng": float(data["location"].get("lng", 0.0))
                    }
            
            return Restaurant(
                id=data.get("id", f"rest_{len(data)}"),
                name=data.get("name", "Unknown Restaurant"),
                description=data.get("description", ""),
                cuisine_type=data.get("cuisine_type", "Unknown"),
                location=location,
                address=data.get("address", ""),
                price_range=data.get("price_range", "$$"),
                average_price_per_person=data.get("average_price_per_person"),
                rating=data.get("rating"),
                review_count=data.get("review_count"),
                dietary_options=data.get("dietary_options", []),
                accessibility_features=data.get("accessibility_features", []),
                images=data.get("images", []),
                booking_url=data.get("booking_url", data.get("url")),
                phone=data.get("phone"),
                opening_hours=data.get("opening_hours"),
                source=data.get("source", "unknown")
            )
        except (KeyError, ValueError, TypeError) as e:
            print(f"Error creating restaurant: {e}")
            return None
    
    def _extract_from_text(self, text: str) -> Optional[Restaurant]:
        """Extract restaurant info from unstructured text (fallback)"""
        lines = text.split("\n")
        name = "Restaurant Recommendation"
        description = text[:500]  # First 500 chars
        
        # Try to find price mentions
        price_range = "$$"
        for line in lines:
            if "$" in line:
                price_range = "$$"
                break
        
        return Restaurant(
            id="rest_text_1",
            name=name,
            description=description,
            cuisine_type="Unknown",
            location={"lat": 0.0, "lng": 0.0},
            address="",
            price_range=price_range,
            average_price_per_person=None,
            rating=None,
            review_count=None,
            dietary_options=[],
            accessibility_features=[],
            images=[],
            booking_url=None,
            phone=None,
            opening_hours=None,
            source="unknown"
        )

