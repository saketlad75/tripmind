"""
BudgetAgent - Calculates approximate budget based on accommodations, 
transportation, experiences, and meals
"""

from typing import Dict, Any, Optional, List
from shared.types import (
    TripRequest, BudgetBreakdown, Accommodation, 
    Transportation, Experience, Restaurant, UserProfile
)
from datetime import date, timedelta


class BudgetAgent:
    """Agent responsible for budget planning"""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    async def initialize(self):
        """Initialize the agent"""
        pass
    
    async def process(
        self,
        request: TripRequest,
        stay_results: Optional[Dict[str, Any]] = None,
        travel_results: Optional[Dict[str, Any]] = None,
        experience_results: Optional[Dict[str, Any]] = None,
        restaurant_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate budget breakdown from all trip components
        
        Args:
            request: Trip request with duration, travelers, etc.
            stay_results: Results from StayAgent with accommodations
            travel_results: Results from TravelAgent with transportation options
            experience_results: Results from ExperienceAgent with activities
            restaurant_results: Results from RestaurantAgent with restaurants (optional)
        
        Returns:
            Dict with 'budget' (BudgetBreakdown) and 'message'
        """
        # Get trip duration
        duration = request.duration_days or 5
        travelers = request.travelers or 1
        
        # Calculate accommodation cost
        accommodation_cost = self._calculate_accommodation_cost(
            stay_results, request, duration
        )
        
        # Calculate transportation cost
        transportation_cost = self._calculate_transportation_cost(
            travel_results, travelers
        )
        
        # Calculate meal costs
        meals_cost = self._calculate_meals_cost(
            restaurant_results, duration, travelers
        )
        
        # Calculate experience costs
        experiences_cost = self._calculate_experiences_cost(
            experience_results, travelers
        )
        
        # Calculate miscellaneous costs (10-15% buffer for unexpected expenses)
        subtotal = accommodation_cost + transportation_cost + meals_cost + experiences_cost
        miscellaneous_cost = subtotal * 0.12  # 12% buffer
        
        # Calculate total
        total = subtotal + miscellaneous_cost
        
        # Create budget breakdown
        budget = BudgetBreakdown(
            accommodation=round(accommodation_cost, 2),
            transportation=round(transportation_cost, 2),
            experiences=round(experiences_cost, 2),
            meals=round(meals_cost, 2),
            miscellaneous=round(miscellaneous_cost, 2),
            total=round(total, 2),
            currency="USD"
        )
        
        return {
            "budget": budget,
            "message": f"Budget calculated for {duration}-day trip for {travelers} traveler(s)"
        }
    
    def _calculate_accommodation_cost(
        self,
        stay_results: Optional[Dict[str, Any]],
        request: TripRequest,
        duration: int
    ) -> float:
        """Calculate accommodation cost from stay results"""
        if not stay_results:
            return 0.0
        
        accommodations: List[Accommodation] = stay_results.get("accommodations", [])
        if not accommodations:
            return 0.0
        
        # If user selected an accommodation, use that
        if request.selected_accommodation_id:
            for acc in accommodations:
                if acc.id == request.selected_accommodation_id:
                    # Use total_price if available, otherwise calculate from price_per_night
                    if acc.total_price > 0:
                        return acc.total_price
                    return acc.price_per_night * duration
        
        # Otherwise, use average price of all accommodations
        total = 0.0
        count = 0
        for acc in accommodations:
            if acc.total_price > 0:
                total += acc.total_price
            else:
                total += acc.price_per_night * duration
            count += 1
        
        return total / count if count > 0 else 0.0
    
    def _calculate_transportation_cost(
        self,
        travel_results: Optional[Dict[str, Any]],
        travelers: int
    ) -> float:
        """Calculate transportation cost (round trip)"""
        if not travel_results:
            return 0.0
        
        transportation: List[Transportation] = travel_results.get("transportation", [])
        if not transportation:
            return 0.0
        
        # Find the recommended option or cheapest flight
        recommended = None
        cheapest = None
        cheapest_price = float('inf')
        
        for trans in transportation:
            # Prefer recommended option
            if trans.recommended:
                recommended = trans
                break
            
            # Track cheapest option
            price = trans.price_per_person if trans.price_per_person else trans.price
            if price < cheapest_price:
                cheapest_price = price
                cheapest = trans
        
        # Use recommended or cheapest
        selected = recommended or cheapest
        if not selected:
            return 0.0
        
        # Calculate cost: price_per_person * travelers, or total price
        if selected.price_per_person:
            # Round trip: multiply by 2
            return selected.price_per_person * travelers * 2
        else:
            # Assume price is per person for round trip, multiply by travelers
            return selected.price * travelers * 2
    
    def _calculate_meals_cost(
        self,
        restaurant_results: Optional[Dict[str, Any]],
        duration: int,
        travelers: int
    ) -> float:
        """Calculate meal costs based on restaurants"""
        if not restaurant_results:
            # Estimate: $50 per person per day if no restaurants provided
            return 50.0 * duration * travelers
        
        restaurants: List[Restaurant] = restaurant_results.get("restaurants", [])
        if not restaurants:
            # Estimate: $50 per person per day
            return 50.0 * duration * travelers
        
        # Calculate average price per person from restaurants
        total_price = 0.0
        count = 0
        
        for restaurant in restaurants:
            if restaurant.average_price_per_person:
                total_price += restaurant.average_price_per_person
                count += 1
            else:
                # Estimate from price_range
                price = self._estimate_price_from_range(restaurant.price_range)
                total_price += price
                count += 1
        
        if count == 0:
            # Fallback estimate
            avg_price_per_meal = 50.0
        else:
            avg_price_per_meal = total_price / count
        
        # Calculate: 3 meals per day (breakfast, lunch, dinner)
        # Use average restaurant price for lunch and dinner, estimate breakfast at 60% of average
        breakfast_cost = avg_price_per_meal * 0.6
        lunch_dinner_cost = avg_price_per_meal * 2  # lunch + dinner
        
        daily_meal_cost = (breakfast_cost + lunch_dinner_cost) * travelers
        return daily_meal_cost * duration
    
    def _estimate_price_from_range(self, price_range: str) -> float:
        """Estimate price from price range string ($, $$, $$$, $$$$)"""
        price_range = price_range.strip().upper()
        if price_range == "$":
            return 15.0  # Budget
        elif price_range == "$$":
            return 35.0  # Moderate
        elif price_range == "$$$":
            return 65.0  # Expensive
        elif price_range == "$$$$":
            return 100.0  # Very expensive
        else:
            return 50.0  # Default moderate
    
    def _calculate_experiences_cost(
        self,
        experience_results: Optional[Dict[str, Any]],
        travelers: int
    ) -> float:
        """Calculate total cost of experiences/activities"""
        if not experience_results:
            return 0.0
        
        experiences: List[Experience] = experience_results.get("experiences", [])
        if not experiences:
            return 0.0
        
        # Sum up all experience prices
        total = 0.0
        for exp in experiences:
            if exp.price:
                # Assume price is per person, multiply by travelers
                total += exp.price * travelers
            # If no price, assume free (skip)
        
        return total
