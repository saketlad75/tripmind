"""
Test script for RestaurantAgent and updated workflow
Tests user profile integration and restaurant recommendations
"""

import asyncio
from agents.restaurant_agent import RestaurantAgent
from agents.stay_agent import StayAgent
from shared.types import TripRequest, UserProfile, Accommodation
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()


async def test_restaurant_agent():
    """Test the RestaurantAgent with a sample request"""
    
    print("=" * 80)
    print("Testing RestaurantAgent with User Profile Integration")
    print("=" * 80)
    
    # Step 1: Create a user profile
    print("\n1. Creating User Profile...")
    user_profile = UserProfile(
        user_id="test_user_123",
        name="John Doe",
        email="john.doe@example.com",
        phone_number="+1234567890",
        date_of_birth=date(1990, 1, 1),
        budget=2000.0,
        dietary_preferences=["vegetarian", "gluten-free"],
        disability_needs=["wheelchair accessible"]
    )
    print(f"   ✓ User Profile Created:")
    print(f"     - Name: {user_profile.name}")
    print(f"     - Budget: ${user_profile.budget}")
    print(f"     - Dietary: {', '.join(user_profile.dietary_preferences)}")
    print(f"     - Accessibility: {', '.join(user_profile.disability_needs)}")
    
    # Step 2: Create a trip request
    print("\n2. Creating Trip Request...")
    request = TripRequest(
        prompt="I want a 5-day quiet nature escape with good Wi-Fi, hiking trails, and local food near Zurich.",
        user_id="test_user_123",
        duration_days=5,
        travelers=2
    )
    print(f"   ✓ Trip Request Created:")
    print(f"     - Prompt: {request.prompt}")
    print(f"     - Duration: {request.duration_days} days")
    print(f"     - Travelers: {request.travelers}")
    
    # Step 3: Test StayAgent first (to get accommodations)
    print("\n3. Testing StayAgent...")
    stay_agent = StayAgent()
    await stay_agent.initialize()
    
    try:
        stay_results = await stay_agent.process(request, user_profile)
        print(f"   ✓ StayAgent found {stay_results['count']} accommodations")
        
        if stay_results['accommodations']:
            # Select the first accommodation
            selected_acc = stay_results['accommodations'][0]
            print(f"\n   Selected Accommodation:")
            print(f"     - Name: {selected_acc.title}")
            print(f"     - Address: {selected_acc.address}")
            print(f"     - Price: ${selected_acc.price_per_night}/night")
            
            # Step 4: Test RestaurantAgent
            print("\n4. Testing RestaurantAgent...")
            restaurant_agent = RestaurantAgent()
            await restaurant_agent.initialize()
            
            # Update request with selected accommodation
            request.selected_accommodation_id = selected_acc.id
            
            restaurant_results = await restaurant_agent.process(
                request, stay_results, user_profile
            )
            
            print(f"   ✓ RestaurantAgent found {restaurant_results['count']} restaurants")
            
            if restaurant_results['restaurants']:
                print(f"\n   Recommended Restaurants:")
                for i, restaurant in enumerate(restaurant_results['restaurants'], 1):
                    print(f"\n   {i}. {restaurant.name}")
                    print(f"      - Cuisine: {restaurant.cuisine_type}")
                    print(f"      - Address: {restaurant.address}")
                    print(f"      - Price Range: {restaurant.price_range}")
                    if restaurant.average_price_per_person:
                        print(f"      - Avg Price: ${restaurant.average_price_per_person}/person")
                    if restaurant.rating:
                        print(f"      - Rating: {restaurant.rating}/5.0 ({restaurant.review_count} reviews)")
                    if restaurant.dietary_options:
                        print(f"      - Dietary Options: {', '.join(restaurant.dietary_options)}")
                    if restaurant.accessibility_features:
                        print(f"      - Accessibility: {', '.join(restaurant.accessibility_features)}")
                    if restaurant.phone:
                        print(f"      - Phone: {restaurant.phone}")
                    if restaurant.opening_hours:
                        print(f"      - Hours: {restaurant.opening_hours}")
            else:
                print("\n   ⚠ No restaurants found")
                print(f"   Raw output: {restaurant_results['raw_output'][:500]}...")
        else:
            print("\n   ⚠ No accommodations found, cannot test RestaurantAgent")
            print(f"   Raw output: {stay_results['raw_output'][:500]}...")
            
    except Exception as e:
        print(f"\n   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


async def test_full_workflow():
    """Test the full orchestrator workflow"""
    
    print("\n" + "=" * 80)
    print("Testing Full Orchestrator Workflow")
    print("=" * 80)
    
    from services.orchestrator import TripOrchestrator
    
    # Create orchestrator
    orchestrator = TripOrchestrator()
    await orchestrator.initialize()
    
    # Create user profile
    user_profile = UserProfile(
        user_id="test_user_456",
        name="Jane Smith",
        email="jane.smith@example.com",
        budget=3000.0,
        dietary_preferences=["vegan"],
        disability_needs=[]
    )
    orchestrator.register_user_profile(user_profile)
    print(f"\n✓ User profile registered: {user_profile.name}")
    
    # Create trip request
    request = TripRequest(
        prompt="I want a 3-day city break in Paris with good restaurants and museums",
        user_id="test_user_456",
        duration_days=3,
        travelers=1
    )
    print(f"✓ Trip request created: {request.prompt}")
    
    try:
        print("\n⏳ Running full workflow...")
        plan = await orchestrator.plan_trip(request, user_profile)
        
        print(f"\n✓ Trip plan generated!")
        print(f"  - Accommodations: {len(plan.accommodations)}")
        print(f"  - Restaurants: {len(plan.restaurants)}")
        print(f"  - Selected Accommodation: {plan.selected_accommodation.title if plan.selected_accommodation else 'None'}")
        
        if plan.restaurants:
            print(f"\n  Restaurants found:")
            for r in plan.restaurants[:3]:  # Show first 3
                print(f"    - {r.name} ({r.cuisine_type}) - {r.price_range}")
        
    except Exception as e:
        print(f"\n✗ Error in workflow: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\nChoose test to run:")
    print("1. Test RestaurantAgent only")
    print("2. Test Full Orchestrator Workflow")
    print("3. Run both tests")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == "1":
        asyncio.run(test_restaurant_agent())
    elif choice == "2":
        asyncio.run(test_full_workflow())
    elif choice == "3":
        asyncio.run(test_restaurant_agent())
        asyncio.run(test_full_workflow())
    else:
        print("Invalid choice. Running RestaurantAgent test by default...")
        asyncio.run(test_restaurant_agent())

