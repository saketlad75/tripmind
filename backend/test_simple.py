"""
Simple test script for RestaurantAgent
Runs automatically without user input
"""

import asyncio
from agents.restaurant_agent import RestaurantAgent
from agents.stay_agent import StayAgent
from shared.types import TripRequest, UserProfile, Accommodation
from datetime import date
from dotenv import load_dotenv

load_dotenv()


async def main():
    """Run the test"""
    
    print("=" * 80)
    print("Testing RestaurantAgent with User Profile")
    print("=" * 80)
    
    # Create user profile
    print("\n1. Creating User Profile...")
    user_profile = UserProfile(
        user_id="test_user_123",
        name="John Doe",
        email="john.doe@example.com",
        budget=2000.0,
        dietary_preferences=["vegetarian", "gluten-free"],
        disability_needs=["wheelchair accessible"]
    )
    print(f"   ✓ Created profile for {user_profile.name}")
    print(f"     Budget: ${user_profile.budget}, Dietary: {', '.join(user_profile.dietary_preferences)}")
    
    # Create trip request
    print("\n2. Creating Trip Request...")
    request = TripRequest(
        prompt="I want a 5-day quiet nature escape with good Wi-Fi near Zurich.",
        user_id="test_user_123",
        duration_days=5,
        travelers=2
    )
    print(f"   ✓ Trip request: {request.prompt[:50]}...")
    
    # Test StayAgent
    print("\n3. Testing StayAgent...")
    stay_agent = StayAgent()
    await stay_agent.initialize()
    
    try:
        stay_results = await stay_agent.process(request, user_profile)
        print(f"   ✓ StayAgent completed: {stay_results['count']} accommodations found")
        
        if stay_results['accommodations']:
            selected_acc = stay_results['accommodations'][0]
            print(f"\n   Selected: {selected_acc.title}")
            print(f"   Address: {selected_acc.address}")
            
            # Test RestaurantAgent
            print("\n4. Testing RestaurantAgent...")
            restaurant_agent = RestaurantAgent()
            await restaurant_agent.initialize()
            
            request.selected_accommodation_id = selected_acc.id
            
            restaurant_results = await restaurant_agent.process(
                request, stay_results, user_profile
            )
            
            print(f"   ✓ RestaurantAgent completed: {restaurant_results['count']} restaurants found")
            
            if restaurant_results['restaurants']:
                print(f"\n   Restaurants:")
                for i, r in enumerate(restaurant_results['restaurants'][:3], 1):
                    print(f"   {i}. {r.name} - {r.cuisine_type} ({r.price_range})")
                    if r.dietary_options:
                        print(f"      Dietary: {', '.join(r.dietary_options)}")
            else:
                print(f"\n   ⚠ No restaurants parsed from output")
                print(f"   Raw output preview: {restaurant_results['raw_output'][:200]}...")
        else:
            print(f"\n   ⚠ No accommodations found")
            print(f"   Raw output: {stay_results['raw_output'][:200]}...")
            
    except Exception as e:
        print(f"\n   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

