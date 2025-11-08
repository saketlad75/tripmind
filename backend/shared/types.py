"""
Shared types and data models for TripMind
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date
from enum import Enum


class TripRequest(BaseModel):
    """User's trip request"""
    prompt: str = Field(..., description="Natural language description of the dream trip")
    destination: Optional[str] = Field(None, description="Destination city/region")
    start_date: Optional[date] = Field(None, description="Trip start date")
    end_date: Optional[date] = Field(None, description="Trip end date")
    duration_days: Optional[int] = Field(None, description="Trip duration in days")
    budget: Optional[float] = Field(None, description="Total budget in USD")
    travelers: int = Field(1, description="Number of travelers")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Additional preferences")


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
    transportation: List[Transportation]
    experiences: List[Experience]
    itinerary: List[DayItinerary]
    budget: BudgetBreakdown
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "draft"  # draft, approved, booked


class AgentState(BaseModel):
    """State passed between agents in the workflow"""
    request: TripRequest
    stay_results: Optional[Dict[str, Any]] = None
    travel_results: Optional[Dict[str, Any]] = None
    experience_results: Optional[Dict[str, Any]] = None
    budget_results: Optional[Dict[str, Any]] = None
    final_plan: Optional[TripPlan] = None

