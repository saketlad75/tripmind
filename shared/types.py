"""
Shared types and data models for TripMind
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, date
from enum import Enum


class UserProfile(BaseModel):
    """User profile with preferences and personal information"""
    user_id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    date_of_birth: Optional[date] = Field(None, description="User's date of birth")
    budget: Optional[float] = Field(None, description="Default budget in USD")
    dietary_preferences: List[str] = Field(default_factory=list, description="Dietary restrictions/preferences (e.g., vegetarian, vegan, gluten-free, halal)")
    disability_needs: List[str] = Field(default_factory=list, description="Accessibility requirements (e.g., wheelchair accessible, hearing impaired)")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TripRequest(BaseModel):
    """User's trip request - only prompt is required, rest comes from user profile"""
    prompt: str = Field(..., description="Natural language description of the dream trip")
    user_id: str = Field(..., description="User ID to fetch profile data")
    # Optional overrides (will use profile defaults if not provided)
    destination: Optional[str] = Field(None, description="Destination city/region (extracted from prompt)")
    start_date: Optional[date] = Field(None, description="Trip start date (extracted from prompt)")
    end_date: Optional[date] = Field(None, description="Trip end date (extracted from prompt)")
    duration_days: Optional[int] = Field(None, description="Trip duration in days (extracted from prompt)")
    budget: Optional[float] = Field(None, description="Trip budget override (uses profile budget if not provided)")
    travelers: int = Field(1, description="Number of travelers")
    selected_accommodation_id: Optional[str] = Field(None, description="Selected accommodation ID from StayAgent results")


class Accommodation(BaseModel):
    """Accommodation listing"""
    id: str
    title: str
    description: str
    location: Dict[str, float]  # lat, lng
    address: str
    price_per_night: float
    total_price: float
    amenities: List[str]
    rating: Optional[float] = None
    review_count: Optional[int] = None
    images: List[str]
    booking_url: Optional[str] = None
    source: str = "airbnb"  # airbnb, booking, etc.


class Transportation(BaseModel):
    """Transportation option"""
    id: str
    type: str  # flight, train, car, bus, rideshare, rental, etc.
    origin: str
    destination: str
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None  # Total travel time in minutes
    price: float
    price_per_person: Optional[float] = None  # Price per person if applicable
    provider: str
    booking_url: Optional[str] = None
    carbon_emissions_kg: Optional[float] = None  # CO2 emissions in kg
    carbon_score: Optional[str] = None  # "low", "medium", "high" or rating 1-10
    transfers: Optional[int] = None  # Number of transfers/connections
    comfort_level: Optional[str] = None  # "economy", "business", "first", etc.
    amenities: List[str] = Field(default_factory=list)  # Wi-Fi, meals, etc.
    recommended: bool = False  # Whether this is the recommended option
    recommendation_reason: Optional[str] = None  # Why it's recommended
    details: Dict[str, Any] = Field(default_factory=dict)


class Route(BaseModel):
    """Multi-modal route combining multiple transportation segments"""
    id: str
    segments: List[Transportation]  # Ordered list of transportation segments
    total_price: float
    total_duration_minutes: Optional[int] = None
    total_carbon_emissions_kg: Optional[float] = None
    total_carbon_score: Optional[str] = None
    route_summary: str  # e.g., "NYC -> Zurich (flight) -> Interlaken (train) -> Hotel (cab)"
    recommended: bool = False
    recommendation_reason: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class Restaurant(BaseModel):
    """Restaurant listing"""
    id: str
    name: str
    description: str
    cuisine_type: str  # Italian, Asian, etc.
    location: Dict[str, float]  # lat, lng
    address: str
    price_range: str  # $, $$, $$$, $$$$
    average_price_per_person: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    dietary_options: List[str] = Field(default_factory=list, description="Available dietary options (vegetarian, vegan, gluten-free, etc.)")
    accessibility_features: List[str] = Field(default_factory=list, description="Accessibility features (wheelchair accessible, etc.)")
    images: List[str]
    booking_url: Optional[str] = None
    phone: Optional[str] = None
    opening_hours: Optional[str] = None
    source: str = "unknown"  # tripadvisor, yelp, google, etc.


class Experience(BaseModel):
    """Local experience/activity"""
    id: str
    name: str
    description: str
    category: str  # hiking, food, culture, etc.
    location: Dict[str, float]
    address: str
    price: Optional[float] = None
    duration_hours: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    images: List[str]
    booking_url: Optional[str] = None
    source: str  # tripadvisor, viator, etc.


class DayItinerary(BaseModel):
    """Single day itinerary"""
    day: int
    date: date
    activities: List[Dict[str, Any]]  # List of activities with time, location, etc.
    meals: List[Dict[str, Any]]
    notes: Optional[str] = None


class BudgetBreakdown(BaseModel):
    """Budget breakdown"""
    accommodation: float
    transportation: float
    experiences: float
    meals: float
    miscellaneous: float
    total: float
    currency: str = "USD"


class TripPlan(BaseModel):
    """Complete trip plan"""
    request: TripRequest
    accommodations: List[Accommodation]
    selected_accommodation: Optional[Accommodation] = None
    restaurants: List[Restaurant] = Field(default_factory=list)
    transportation: List[Transportation]
    experiences: List[Experience]
    itinerary: List[DayItinerary]
    budget: BudgetBreakdown
    map_data: Optional[Dict[str, Any]] = None
    trip_id: Optional[str] = None  # Trip ID for API responses
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "draft"  # draft, approved, booked


class AgentState(BaseModel):
    """State passed between agents in the workflow"""
    request: TripRequest
    user_profile: Optional[UserProfile] = None
    stay_results: Optional[Dict[str, Any]] = None
    restaurant_results: Optional[Dict[str, Any]] = None
    travel_results: Optional[Dict[str, Any]] = None
    experience_results: Optional[Dict[str, Any]] = None
    budget_results: Optional[Dict[str, Any]] = None
    final_plan: Optional[TripPlan] = None

