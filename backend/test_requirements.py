"""
Test script to verify minimum requirements:
- StayAgent finds minimum 3 accommodations
- RestaurantAgent finds minimum 3-4 restaurants/cafes
- Location extracted from prompt only
- Budget from user profile
"""

import asyncio
from agents.restaurant_agent import RestaurantAgent
from agents.stay_agent import StayAgent
from shared.types import TripRequest, UserProfile
from datetime import date
from dotenv import load_dotenv

load_dotenv()


async def test_minimum_requirements():
    """Test that agents meet minimum requirements"""
    
    print("=" * 80)
    print("Testing Minimum Requirements")
    print("=" * 80)
    
    # Create user profile with budget
    print("\n1. Creating User Profile...")
    user_profile = UserProfile(
        user_id="test_user_001",
        name="Test User",
        email="test@example.com",
        budget=2500.0,  # Budget from profile
        dietary_preferences=["vegetarian"],
        disability_needs=[]
    )
    print(f"   ✓ Profile created with budget: ${user_profile.budget}")
    
    # Create trip request with ONLY prompt (no explicit location or budget)
    print("\n2. Creating Trip Request (prompt only)...")
    request = TripRequest(
        prompt="I want a 4-day relaxing beach vacation in Bali with good restaurants nearby",
        user_id="test_user_001",
        duration_days=4,
        travelers=2
        # No destination, no budget - should be extracted/used from profile
    )
    print(f"   ✓ Request created with prompt only:")
    print(f"     '{request.prompt}'")
    print(f"     (No explicit location or budget provided)")
    
    # Test StayAgent
    print("\n3. Testing StayAgent...")
    print("   Requirements: Extract location from prompt, find minimum 3 accommodations")
    stay_agent = StayAgent()
    await stay_agent.initialize()
    
    try:
        stay_results = await stay_agent.process(request, user_profile)
        count = stay_results['count']
        meets_min = stay_results.get('meets_minimum', False)
        
        print(f"\n   Results:")
        print(f"   - Accommodations found: {count}")
        print(f"   - Meets minimum (3+): {'✓ YES' if meets_min else '✗ NO'}")
        
        if stay_results['accommodations']:
            print(f"\n   Accommodations:")
            for i, acc in enumerate(stay_results['accommodations'][:5], 1):
                print(f"   {i}. {acc.title}")
                print(f"      Location: {acc.address}")
                print(f"      Price: ${acc.price_per_night}/night")
        else:
            print(f"\n   ⚠ No accommodations parsed")
            print(f"   Raw output preview: {stay_results['raw_output'][:300]}...")
        
        # Test RestaurantAgent if we have accommodations
        if stay_results['accommodations']:
            print("\n4. Testing RestaurantAgent...")
            print("   Requirements: Find minimum 3-4 restaurants/cafes near selected accommodation")
            
            restaurant_agent = RestaurantAgent()
            await restaurant_agent.initialize()
            
            # Select first accommodation
            selected_acc = stay_results['accommodations'][0]
            request.selected_accommodation_id = selected_acc.id
            
            restaurant_results = await restaurant_agent.process(
                request, stay_results, user_profile
            )
            
            rest_count = restaurant_results['count']
            rest_meets_min = restaurant_results.get('meets_minimum', False)
            
            print(f"\n   Results:")
            print(f"   - Restaurants/Cafes found: {rest_count}")
            print(f"   - Meets minimum (3+): {'✓ YES' if rest_meets_min else '✗ NO'}")
            print(f"   - Near accommodation: {selected_acc.title}")
            
            if restaurant_results['restaurants']:
                print(f"\n   Restaurants/Cafes:")
                for i, r in enumerate(restaurant_results['restaurants'][:5], 1):
                    print(f"   {i}. {r.name}")
                    print(f"      Type: {r.cuisine_type}")
                    print(f"      Price: {r.price_range}")
                    if r.dietary_options:
                        print(f"      Dietary: {', '.join(r.dietary_options)}")
            else:
                print(f"\n   ⚠ No restaurants parsed")
                print(f"   Raw output preview: {restaurant_results['raw_output'][:300]}...")
        
    except Exception as e:
        print(f"\n   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_minimum_requirements())

