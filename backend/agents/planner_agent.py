"""
PlannerAgent - Creates final itinerary from all agent results
Combines accommodations, restaurants, transportation, and experiences into a day-by-day plan
"""

from typing import Dict, Any, Optional, List
from shared.types import TripRequest, TripPlan, DayItinerary, BudgetBreakdown, Transportation, Experience
from datetime import date, timedelta, datetime, time


class PlannerAgent:
    """Agent responsible for creating final itinerary"""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    async def initialize(self):
        """Initialize the agent"""
        pass
    
    async def process(
        self,
        request: TripRequest,
        stay_results: Optional[Dict[str, Any]] = None,
        restaurant_results: Optional[Dict[str, Any]] = None,
        travel_results: Optional[Dict[str, Any]] = None,
        experience_results: Optional[Dict[str, Any]] = None,
        budget_results: Optional[Dict[str, Any]] = None
    ) -> TripPlan:
        """Process planning request and create complete itinerary"""
        from shared.types import BudgetBreakdown
        
        # Get selected accommodation (use first one if none selected)
        selected_accommodation = None
        accommodations = stay_results.get("accommodations", []) if stay_results else []
        if request.selected_accommodation_id:
            for acc in accommodations:
                if acc.id == request.selected_accommodation_id:
                    selected_accommodation = acc
                    break
        if not selected_accommodation and accommodations:
            selected_accommodation = accommodations[0]
        
        # Get transportation options
        transportation = []
        if travel_results:
            # Get all transportation options
            all_transport = travel_results.get("transportation", [])
            if all_transport:
                transportation = all_transport[:5]  # Top 5 options
        
        # Get experiences
        experiences = experience_results.get("experiences", []) if experience_results else []
        
        # Get restaurants
        restaurants = restaurant_results.get("restaurants", []) if restaurant_results else []
        
        # Get budget
        budget = budget_results.get("budget") if budget_results else None
        if not budget:
            # Calculate basic budget
            budget = self._calculate_budget(
                accommodations, transportation, experiences, restaurants, request
            )
        
        # Create day-by-day itinerary
        itinerary = self._create_itinerary(
            request, selected_accommodation, restaurants, experiences, transportation
        )
        
        return TripPlan(
            request=request,
            accommodations=accommodations,
            selected_accommodation=selected_accommodation,
            restaurants=restaurants,
            transportation=transportation,
            experiences=experiences,
            itinerary=itinerary,
            budget=budget
        )
    
    def _calculate_budget(
        self,
        accommodations: List,
        transportation: List,
        experiences: List,
        restaurants: List,
        request: TripRequest
    ) -> BudgetBreakdown:
        """Calculate budget breakdown"""
        # Accommodation
        acc_total = 0.0
        if accommodations:
            # Use first accommodation total price
            acc_total = accommodations[0].total_price if hasattr(accommodations[0], 'total_price') else 0.0
        
        # Transportation
        trans_total = 0.0
        if transportation:
            # Use first transportation option price
            trans_total = transportation[0].price if hasattr(transportation[0], 'price') else 0.0
            # Multiply by travelers if per person
            if hasattr(transportation[0], 'price_per_person') and transportation[0].price_per_person:
                trans_total = transportation[0].price_per_person * request.travelers
        
        # Experiences
        exp_total = 0.0
        for exp in experiences[:3]:  # Top 3 experiences
            if hasattr(exp, 'price') and exp.price:
                exp_total += exp.price * request.travelers
        
        # Meals (estimate based on restaurants)
        meal_total = 0.0
        if restaurants:
            # Estimate $30-50 per person per meal
            avg_meal_price = 40.0
            # 2-3 meals per day
            meals_per_day = 2.5
            meal_total = avg_meal_price * meals_per_day * request.duration_days * request.travelers
        
        # Miscellaneous (10% of total)
        subtotal = acc_total + trans_total + exp_total + meal_total
        misc_total = subtotal * 0.1
        
        total = subtotal + misc_total
        
        return BudgetBreakdown(
            accommodation=acc_total,
            transportation=trans_total,
            experiences=exp_total,
            meals=meal_total,
            miscellaneous=misc_total,
            total=total
        )
    
    def _create_itinerary(
        self,
        request: TripRequest,
        accommodation,
        restaurants: List,
        experiences: List,
        transportation: List
    ) -> List[DayItinerary]:
        """Create day-by-day itinerary"""
        itinerary = []
        
        if not request.start_date:
            # Use today as start date if not provided
            start_date = date.today() + timedelta(days=7)
        else:
            start_date = request.start_date
        
        duration = request.duration_days or 3
        
        # Day 1: Arrival
        day1_activities = []
        day1_meals = []
        
        # Add transportation as first activity
        if transportation:
            top_transport = transportation[0]
            day1_activities.append({
                "time": "09:00",
                "type": "transportation",
                "title": f"Travel: {top_transport.origin} → {top_transport.destination}",
                "description": f"{top_transport.type.upper()} via {top_transport.provider}",
                "duration": f"{top_transport.duration_minutes // 60}h {top_transport.duration_minutes % 60}m" if top_transport.duration_minutes else "N/A",
                "location": top_transport.destination,
                "price": f"${top_transport.price:.2f}"
            })
        
        # Add check-in
        if accommodation:
            day1_activities.append({
                "time": "15:00",
                "type": "accommodation",
                "title": f"Check-in: {accommodation.title}",
                "description": accommodation.description[:100] + "..." if len(accommodation.description) > 100 else accommodation.description,
                "location": accommodation.address,
                "price": f"${accommodation.price_per_night:.2f}/night"
            })
        
        # Add first restaurant for dinner
        if restaurants:
            day1_meals.append({
                "time": "19:00",
                "type": "dinner",
                "restaurant": restaurants[0].name,
                "cuisine": restaurants[0].cuisine_type,
                "location": restaurants[0].address,
                "price_range": restaurants[0].price_range,
                "description": restaurants[0].description[:100] + "..." if len(restaurants[0].description) > 100 else restaurants[0].description
            })
        
        day1_notes = "Arrival day - settle in and explore the area around your accommodation"
        itinerary.append(DayItinerary(
            day=1,
            date=start_date,
            activities=day1_activities,
            meals=day1_meals,
            notes=day1_notes
        ))
        
        # Middle days: Activities and meals
        for day_num in range(2, duration):
            current_date = start_date + timedelta(days=day_num - 1)
            day_activities = []
            day_meals = []
            
            # Add breakfast
            if restaurants and len(restaurants) > 1:
                day_meals.append({
                    "time": "09:00",
                    "type": "breakfast",
                    "restaurant": restaurants[1].name if len(restaurants) > 1 else restaurants[0].name,
                    "cuisine": restaurants[1].cuisine_type if len(restaurants) > 1 else restaurants[0].cuisine_type,
                    "location": restaurants[1].address if len(restaurants) > 1 else restaurants[0].address,
                    "price_range": restaurants[1].price_range if len(restaurants) > 1 else restaurants[0].price_range
                })
            
            # Add experiences/activities
            exp_index = day_num - 2
            if experiences and exp_index < len(experiences):
                exp = experiences[exp_index]
                day_activities.append({
                    "time": "10:30",
                    "type": "experience",
                    "title": exp.name,
                    "description": exp.description[:150] + "..." if len(exp.description) > 150 else exp.description,
                    "category": exp.category,
                    "location": exp.address,
                    "duration": f"{exp.duration_hours}h" if exp.duration_hours else "Half day",
                    "price": f"${exp.price:.2f}" if exp.price else "Free"
                })
            else:
                # Generic activity
                day_activities.append({
                    "time": "10:30",
                    "type": "activity",
                    "title": "Explore Local Area",
                    "description": "Discover the city's attractions, culture, and hidden gems",
                    "location": accommodation.address if accommodation else "City Center",
                    "duration": "3-4 hours",
                    "price": "Free"
                })
            
            # Add lunch
            if restaurants and len(restaurants) > 2:
                day_meals.append({
                    "time": "13:00",
                    "type": "lunch",
                    "restaurant": restaurants[2].name if len(restaurants) > 2 else restaurants[0].name,
                    "cuisine": restaurants[2].cuisine_type if len(restaurants) > 2 else restaurants[0].cuisine_type,
                    "location": restaurants[2].address if len(restaurants) > 2 else restaurants[0].address,
                    "price_range": restaurants[2].price_range if len(restaurants) > 2 else restaurants[0].price_range
                })
            
            # Add afternoon activity
            day_activities.append({
                "time": "15:00",
                "type": "activity",
                "title": "Free Time / Optional Activities",
                "description": "Relax, shop, or explore at your own pace",
                "location": "Various",
                "duration": "Flexible",
                "price": "Varies"
            })
            
            # Add dinner
            if restaurants:
                # Rotate through restaurants
                dinner_index = (day_num - 1) % len(restaurants)
                day_meals.append({
                    "time": "19:00",
                    "type": "dinner",
                    "restaurant": restaurants[dinner_index].name,
                    "cuisine": restaurants[dinner_index].cuisine_type,
                    "location": restaurants[dinner_index].address,
                    "price_range": restaurants[dinner_index].price_range
                })
            
            day_notes = f"Day {day_num} - Enjoy local experiences and cuisine"
            itinerary.append(DayItinerary(
                day=day_num,
                date=current_date,
                activities=day_activities,
                meals=day_meals,
                notes=day_notes
            ))
        
        # Last day: Departure
        last_day = duration
        last_date = start_date + timedelta(days=duration - 1)
        last_day_activities = []
        last_day_meals = []
        
        # Add breakfast
        if restaurants:
            last_day_meals.append({
                "time": "09:00",
                "type": "breakfast",
                "restaurant": restaurants[0].name,
                "cuisine": restaurants[0].cuisine_type,
                "location": restaurants[0].address,
                "price_range": restaurants[0].price_range
            })
        
        # Add check-out
        if accommodation:
            last_day_activities.append({
                "time": "11:00",
                "type": "accommodation",
                "title": f"Check-out: {accommodation.title}",
                "description": "Departure",
                "location": accommodation.address
            })
        
        # Add departure transportation
        if transportation:
            top_transport = transportation[0]
            last_day_activities.append({
                "time": "12:00",
                "type": "transportation",
                "title": f"Return Travel: {top_transport.destination} → {top_transport.origin}",
                "description": f"{top_transport.type.upper()} via {top_transport.provider}",
                "duration": f"{top_transport.duration_minutes // 60}h {top_transport.duration_minutes % 60}m" if top_transport.duration_minutes else "N/A",
                "location": top_transport.origin,
                "price": f"${top_transport.price:.2f}"
            })
        
        last_day_notes = "Departure day - safe travels!"
        itinerary.append(DayItinerary(
            day=last_day,
            date=last_date,
            activities=last_day_activities,
            meals=last_day_meals,
            notes=last_day_notes
        ))
        
        return itinerary

