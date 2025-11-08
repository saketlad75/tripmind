"""
Test script for StayAgent using Google Gemini API
Run this to test the StayAgent independently
"""

import asyncio
from agents.stay_agent import StayAgent
from shared.types import TripRequest, UserProfile
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()


async def test_stay_agent():
    """Test the StayAgent with a sample request"""
    
    # Create a test user profile
    user_profile = UserProfile(
        user_id="test_user_001",
        name="Test User",
        email="test@example.com",
        budget=2000.0,
        dietary_preferences=[],
        disability_needs=[]
    )
    
    # Create a test trip request
    request = TripRequest(
        prompt="I want a 5-day quiet nature escape with good Wi-Fi, hiking trails, and local food near Zurich.",
        user_id="test_user_001",
        destination="Zurich, Switzerland",
        start_date=date.today() + timedelta(days=30),
        end_date=date.today() + timedelta(days=35),
        duration_days=5,
        budget=2000.0,
        travelers=2
    )
    
    # Initialize and run StayAgent
    agent = StayAgent()
    await agent.initialize()
    
    print("=" * 80)
    print("Testing StayAgent with Google Gemini API")
    print("=" * 80)
    print(f"\nRequest: {request.prompt}")
    print(f"Destination: {request.destination}")
    print(f"Budget: ${request.budget}")
    print("\nProcessing...\n")
    
    try:
        results = await agent.process(request, user_profile)
        
        print("=" * 80)
        print("Results:")
        print("=" * 80)
        print(f"\nFound {results['count']} accommodations\n")
        
        for i, acc in enumerate(results['accommodations'], 1):
            print(f"\n{i}. {acc.title}")
            print(f"   Description: {acc.description[:100]}...")
            print(f"   Price per night: ${acc.price_per_night:.2f}")
            print(f"   Total price: ${acc.total_price:.2f}")
            print(f"   Rating: {acc.rating or 'N/A'}")
            print(f"   Address: {acc.address}")
            if acc.booking_url:
                print(f"   Booking URL: {acc.booking_url}")
        
        print("\n" + "=" * 80)
        print("Raw Output (first 500 chars):")
        print("=" * 80)
        print(results['raw_output'][:500] + "...")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_stay_agent())

