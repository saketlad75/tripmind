"""
PlannerAgent - Creates comprehensive trip plans with day-by-day itineraries
Uses Google Gemini API to generate detailed itineraries
"""

from typing import Dict, Any, Optional, List
import google.generativeai as genai
from shared.types import (
    TripRequest, TripPlan, DayItinerary, BudgetBreakdown,
    Accommodation, Restaurant, Experience, UserProfile
)
from datetime import date, timedelta
import json
import os
import asyncio
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_message,
    retry_if_exception_type
)

load_dotenv()


class PlannerAgent:
    """Agent responsible for creating final itinerary"""
    
    def __init__(self, llm=None):
        self.llm = llm
        self.model = None
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    async def initialize(self):
        """Initialize the Gemini model"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your_google_api_key_here":
            raise ValueError(
                "GOOGLE_API_KEY not set. Please set it in your .env file. "
                "Get your API key at https://makersuite.google.com/app/apikey"
            )
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    async def process(
        self,
        request: TripRequest,
        stay_results: Optional[Dict[str, Any]] = None,
        restaurant_results: Optional[Dict[str, Any]] = None,
        travel_results: Optional[Dict[str, Any]] = None,
        experience_results: Optional[Dict[str, Any]] = None,
        budget_results: Optional[Dict[str, Any]] = None,
        user_profile: Optional[UserProfile] = None
    ) -> TripPlan:
        """
        Create comprehensive trip plan with day-by-day itinerary
        
        Args:
            request: TripRequest with user's trip description
            stay_results: Results from StayAgent
            restaurant_results: Results from RestaurantAgent
            travel_results: Results from TravelAgent
            experience_results: Results from ExperienceAgent
            budget_results: Results from BudgetAgent
            user_profile: User profile with preferences
            
        Returns:
            Complete TripPlan with detailed itinerary
        """
        if not self.model:
            await self.initialize()
        
        # Get selected accommodation
        selected_accommodation = self._get_selected_accommodation(
            request, stay_results
        )
        
        # Get restaurants
        restaurants = restaurant_results.get("restaurants", []) if restaurant_results else []
        
        # Get experiences
        experiences = experience_results.get("experiences", []) if experience_results else []
        
        # Calculate trip dates
        start_date = request.start_date or date.today() + timedelta(days=7)
        duration = request.duration_days or 5
        end_date = request.end_date or (start_date + timedelta(days=duration - 1))
        
        # Build prompt for itinerary generation
        prompt = self._build_itinerary_prompt(
            request, selected_accommodation, restaurants, experiences,
            start_date, duration, user_profile
        )
        
        # Generate itinerary using Gemini API (with rate limit handling)
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
        
        # Parse and create itinerary
        itinerary = self._parse_itinerary(
            result.final_output, start_date, duration
        )
        
        # Calculate budget breakdown
        budget = self._calculate_budget(
            selected_accommodation, restaurants, duration, request, user_profile, budget_results
        )
        
        # Create final trip plan
        return TripPlan(
            request=request,
            accommodations=stay_results.get("accommodations", []) if stay_results else [],
            selected_accommodation=selected_accommodation,
            restaurants=restaurants,
            transportation=travel_results.get("transportation", []) if travel_results else [],
            experiences=experiences,
            itinerary=itinerary,
            budget=budget,
            map_data=self._generate_map_data(selected_accommodation, restaurants, experiences),
            status="draft"
        )
    
    def _get_selected_accommodation(
        self,
        request: TripRequest,
        stay_results: Optional[Dict[str, Any]]
    ) -> Optional[Accommodation]:
        """Get the selected accommodation"""
        if not stay_results or not request.selected_accommodation_id:
            accommodations = stay_results.get("accommodations", []) if stay_results else []
            return accommodations[0] if accommodations else None
        
        accommodations = stay_results.get("accommodations", [])
        for acc in accommodations:
            if acc.id == request.selected_accommodation_id:
                return acc
        return accommodations[0] if accommodations else None
    
    def _build_itinerary_prompt(
        self,
        request: TripRequest,
        accommodation: Optional[Accommodation],
        restaurants: List[Restaurant],
        experiences: List[Experience],
        start_date: date,
        duration: int,
        user_profile: Optional[UserProfile]
    ) -> str:
        """Build detailed prompt for itinerary generation"""
        prompt_parts = [
            f"I need to create a detailed day-by-day itinerary for a trip.",
            f"\nUser's Trip Request:",
            f'"{request.prompt}"',
            f"\nTrip Duration: {duration} days",
            f"Start Date: {start_date}",
            f"Number of Travelers: {request.travelers}",
        ]
        
        # Add accommodation details
        if accommodation:
            prompt_parts.extend([
                f"\nSelected Accommodation:",
                f"- Name: {accommodation.title}",
                f"- Address: {accommodation.address}",
                f"- Location: {accommodation.location.get('lat', 0)}, {accommodation.location.get('lng', 0)}",
            ])
        
        # Add restaurants
        if restaurants:
            prompt_parts.append(f"\nRecommended Restaurants/Cafes ({len(restaurants)} options):")
            for i, r in enumerate(restaurants[:5], 1):  # Show first 5
                prompt_parts.append(
                    f"{i}. {r.name} - {r.cuisine_type} ({r.price_range}) - {r.address}"
                )
        
        # Add experiences
        if experiences:
            prompt_parts.append(f"\nAvailable Activities/Experiences ({len(experiences)} options):")
            # Group by category
            by_category = {}
            for exp in experiences:
                cat = exp.category if hasattr(exp, 'category') else "General"
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(exp)
            
            for category, exps in list(by_category.items())[:5]:  # Top 5 categories
                prompt_parts.append(f"\n{category.title()}:")
                for exp in exps[:3]:  # Top 3 per category
                    price_str = f"${exp.price:.2f}" if hasattr(exp, 'price') and exp.price else "Free"
                    prompt_parts.append(
                        f"  - {exp.name} ({price_str}) - {exp.address if hasattr(exp, 'address') else 'Location TBD'}"
                    )
        
        # Add user preferences
        if user_profile:
            if user_profile.dietary_preferences:
                prompt_parts.append(
                    f"\nDietary Preferences: {', '.join(user_profile.dietary_preferences)}"
                )
            if user_profile.disability_needs:
                prompt_parts.append(
                    f"Accessibility Needs: {', '.join(user_profile.disability_needs)}"
                )
        
        prompt_parts.extend([
            f"\nPlease create a detailed {duration}-day itinerary that:",
            "1. Matches the user's trip request and theme",
            "2. Includes activities relevant to the location and user's interests",
            "3. Suggests meals at the recommended restaurants",
            "4. Includes specific times for activities and meals",
            "5. Provides realistic travel times between locations",
            "6. Balances activities with rest time",
            "",
            "For each day, include:",
            "- Morning activities (with times, e.g., '9:00 AM - 12:00 PM')",
            "- Lunch suggestions (restaurant name and time)",
            "- Afternoon activities (with times)",
            "- Dinner suggestions (restaurant name and time)",
            "- Evening activities (if applicable)",
            "- Notes or tips for the day",
            "",
            "IMPORTANT: Base activities on the user's prompt theme:",
            "- If they want 'nature escape' → include hiking, nature walks, parks",
            "- If they want 'hiking trails' → include specific trail recommendations",
            "- If they want 'local food' → include food tours, local markets",
            "- If they want 'quiet' → avoid crowded tourist spots",
            "",
            "Please format your response as JSON with the following structure:",
            "```json",
            "{",
            '  "itinerary": [',
            "    {",
            '      "day": 1,',
            '      "date": "2025-01-15",',
            '      "activities": [',
            '        {',
            '          "time": "9:00 AM - 12:00 PM",',
            '          "title": "Activity name",',
            '          "description": "Detailed description",',
            '          "location": "Location name or address",',
            '          "type": "hiking/nature/food/culture/etc"',
            '        }',
            '      ],',
            '      "meals": [',
            '        {',
            '          "time": "1:00 PM",',
            '          "type": "lunch",',
            '          "restaurant": "Restaurant name from recommendations",',
            '          "description": "What to try"',
            '        }',
            '      ],',
            '      "notes": "Tips or important notes for the day"',
            '    }',
            '    // ... repeat for all days',
            "  ]",
            "}",
            "```"
        ])
        
        return "\n".join(prompt_parts)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_message(match=r".*(rate limit|429|quota|too many requests|resource exhausted).*"),
        reraise=True
    )
    async def _run_with_retry(self, prompt: str):
        """Run Gemini API call with retry logic"""
        response = await asyncio.to_thread(
            self.model.generate_content,
            prompt
        )
        class Result:
            def __init__(self, text):
                self.final_output = text
        return Result(response.text)
    
    def _parse_itinerary(
        self,
        output: str,
        start_date: date,
        duration: int
    ) -> List[DayItinerary]:
        """Parse Gemini output into DayItinerary objects"""
        itinerary = []
        
        try:
            # Try to extract JSON
            if "```json" in output:
                json_start = output.find("```json") + 7
                json_end = output.find("```", json_start)
                json_str = output[json_start:json_end].strip()
                data = json.loads(json_str)
            elif "```" in output:
                # Try to find JSON between any code blocks
                json_start = output.find("```") + 3
                json_end = output.find("```", json_start)
                if json_end > json_start:
                    json_str = output[json_start:json_end].strip()
                    # Remove language identifier if present
                    if json_str.startswith("json"):
                        json_str = json_str[4:].strip()
                    data = json.loads(json_str)
                else:
                    # Try to parse the whole output as JSON
                    data = json.loads(output.strip())
            else:
                # Try to parse the whole output as JSON
                data = json.loads(output.strip())
                
            if isinstance(data, dict) and "itinerary" in data:
                for day_data in data["itinerary"]:
                    day_itinerary = self._create_day_itinerary(
                        day_data, start_date, duration
                    )
                    if day_itinerary:
                        itinerary.append(day_itinerary)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"⚠️  Error parsing itinerary JSON: {e}")
            print(f"Raw output preview: {output[:200]}...")
            # Fallback: create basic itinerary
            itinerary = self._create_fallback_itinerary(start_date, duration)
        
        # Ensure we have entries for all days
        while len(itinerary) < duration:
            day_num = len(itinerary) + 1
            day_date = start_date + timedelta(days=day_num - 1)
            itinerary.append(DayItinerary(
                day=day_num,
                date=day_date,
                activities=[],
                meals=[],
                notes="Activities to be planned"
            ))
        
        return itinerary[:duration]  # Ensure we don't exceed duration
    
    def _create_day_itinerary(
        self,
        day_data: Dict[str, Any],
        start_date: date,
        duration: int
    ) -> Optional[DayItinerary]:
        """Create DayItinerary from parsed data"""
        try:
            day_num = int(day_data.get("day", 1))
            if day_num < 1 or day_num > duration:
                return None
            
            # Parse date
            day_date = start_date + timedelta(days=day_num - 1)
            if "date" in day_data:
                try:
                    day_date = date.fromisoformat(day_data["date"])
                except (ValueError, TypeError):
                    pass
            
            activities = day_data.get("activities", [])
            meals = day_data.get("meals", [])
            notes = day_data.get("notes", "")
            
            return DayItinerary(
                day=day_num,
                date=day_date,
                activities=activities if isinstance(activities, list) else [],
                meals=meals if isinstance(meals, list) else [],
                notes=notes
            )
        except (KeyError, ValueError, TypeError) as e:
            print(f"⚠️  Error creating day itinerary: {e}")
            return None
    
    def _create_fallback_itinerary(
        self,
        start_date: date,
        duration: int
    ) -> List[DayItinerary]:
        """Create a basic fallback itinerary"""
        itinerary = []
        for day_num in range(1, duration + 1):
            day_date = start_date + timedelta(days=day_num - 1)
            itinerary.append(DayItinerary(
                day=day_num,
                date=day_date,
                activities=[],
                meals=[],
                notes="Itinerary details to be generated"
            ))
        return itinerary
    
    def _calculate_budget(
        self,
        accommodation: Optional[Accommodation],
        restaurants: List[Restaurant],
        duration: int,
        request: TripRequest,
        user_profile: Optional[UserProfile],
        budget_results: Optional[Dict[str, Any]]
    ) -> BudgetBreakdown:
        """Calculate budget breakdown"""
        # Use budget from BudgetAgent if available
        if budget_results and "budget" in budget_results:
            budget = budget_results["budget"]
            if isinstance(budget, BudgetBreakdown):
                return budget
            elif isinstance(budget, dict):
                return BudgetBreakdown(**budget)
        
        # Fallback: calculate approximate budget
        accommodation_cost = 0.0
        if accommodation:
            accommodation_cost = accommodation.total_price or (accommodation.price_per_night or 0) * duration
        
        # Estimate meal costs
        meal_cost_per_day = 50.0  # Default estimate
        if restaurants:
            # Average price from restaurants
            total_price = sum(
                r.average_price_per_person or 30.0
                for r in restaurants[:5]
            )
            meal_cost_per_day = (total_price / len(restaurants[:5])) * 2  # 2 meals per day
        
        meals_cost = meal_cost_per_day * duration * request.travelers
        
        # Miscellaneous (10% of total)
        subtotal = accommodation_cost + meals_cost
        miscellaneous = subtotal * 0.1
        
        return BudgetBreakdown(
            accommodation=accommodation_cost,
            transportation=0.0,  # Will be filled by BudgetAgent
            experiences=0.0,  # Will be filled by BudgetAgent
            meals=meals_cost,
            miscellaneous=miscellaneous,
            total=accommodation_cost + meals_cost + miscellaneous,
            currency="USD"
        )
    
    def _generate_map_data(
        self,
        accommodation: Optional[Accommodation],
        restaurants: List[Restaurant],
        experiences: List[Experience]
    ) -> Dict[str, Any]:
        """Generate map data for visualization"""
        locations = []
        
        # Add accommodation
        if accommodation and accommodation.location:
            locations.append({
                "type": "accommodation",
                "name": accommodation.title,
                "lat": accommodation.location.get("lat"),
                "lng": accommodation.location.get("lng"),
                "address": accommodation.address
            })
        
        # Add restaurants
        for restaurant in restaurants[:10]:  # Limit to 10
            if restaurant.location:
                locations.append({
                    "type": "restaurant",
                    "name": restaurant.name,
                    "lat": restaurant.location.get("lat"),
                    "lng": restaurant.location.get("lng"),
                    "address": restaurant.address
                })
        
        # Add experiences
        for experience in experiences[:10]:  # Limit to 10
            if hasattr(experience, 'location') and experience.location:
                locations.append({
                    "type": "experience",
                    "name": experience.name,
                    "lat": experience.location.get("lat"),
                    "lng": experience.location.get("lng"),
                    "address": getattr(experience, 'address', 'Location TBD')
                })
        
        return {
            "center": locations[0] if locations else {"lat": 0, "lng": 0},
            "locations": locations,
            "zoom": 12
        }
