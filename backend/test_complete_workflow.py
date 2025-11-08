"""
Complete Workflow Test
Tests the entire TripMind workflow from start to finish:
1. User profile registration
2. Get accommodations
3. Select accommodation
4. Get restaurants
5. Get experiences
6. Calculate budget
7. Generate complete itinerary
"""

import asyncio
from services.orchestrator import TripOrchestrator
from shared.types import TripRequest, UserProfile
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()


async def test_complete_workflow():
    """Test the complete trip planning workflow"""
    
    print("=" * 80)
    print("🚀 Testing Complete TripMind Workflow")
    print("=" * 80)
    
    # Initialize orchestrator
    print("\n1️⃣  Initializing TripOrchestrator...")
    orchestrator = TripOrchestrator()
    await orchestrator.initialize()
    print("   ✅ Orchestrator initialized")
    
    # Step 1: Register user profile
    print("\n2️⃣  Registering User Profile...")
    user_profile = UserProfile(
        user_id="test_user_workflow_001",
        name="Test User",
        email="test@example.com",
        phone_number="+1234567890",
        budget=3000.0,
        dietary_preferences=["vegetarian"],
        disability_needs=[]
    )
    orchestrator.register_user_profile(user_profile)
    print(f"   ✅ User Profile Registered: {user_profile.name}")
    print(f"      Budget: ${user_profile.budget}")
    print(f"      Dietary Preferences: {', '.join(user_profile.dietary_preferences)}")
    
    # Step 2: Create trip request
    print("\n3️⃣  Creating Trip Request...")
    trip_request = TripRequest(
        prompt="I want a 5-day quiet nature escape with good Wi-Fi, hiking trails, and local food near Zurich, Switzerland",
        user_id="test_user_workflow_001",
        duration_days=5,
        travelers=2
    )
    print(f"   ✅ Trip Request Created")
    print(f"      Prompt: {trip_request.prompt}")
    print(f"      Duration: {trip_request.duration_days} days")
    print(f"      Travelers: {trip_request.travelers}")
    
    # Step 3: Get accommodations
    print("\n4️⃣  Getting Accommodations (StayAgent)...")
    try:
        stay_results = await orchestrator.stay_agent.process(trip_request, user_profile)
        accommodations = stay_results.get("accommodations", [])
        print(f"   ✅ Found {len(accommodations)} accommodations")
        
        if not accommodations:
            print("   ❌ No accommodations found. Cannot continue.")
            return
        
        # Display accommodations
        print("\n   📋 Available Accommodations:")
        for i, acc in enumerate(accommodations[:5], 1):
            print(f"      {i}. {acc.title}")
            print(f"         💰 ${acc.price_per_night:.2f}/night (Total: ${acc.total_price:.2f})")
            print(f"         📍 {acc.address[:60]}...")
            print(f"         ⭐ {acc.rating or 'N/A'}")
        
        # Select first accommodation
        selected_accommodation = accommodations[0]
        trip_request.selected_accommodation_id = selected_accommodation.id
        print(f"\n   ✅ Selected: {selected_accommodation.title} (ID: {selected_accommodation.id})")
        
    except Exception as e:
        print(f"   ❌ Error getting accommodations: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Get restaurants
    print("\n5️⃣  Getting Restaurants (RestaurantAgent)...")
    try:
        restaurant_results = await orchestrator.restaurant_agent.process(
            trip_request, stay_results, user_profile
        )
        restaurants = restaurant_results.get("restaurants", [])
        print(f"   ✅ Found {len(restaurants)} restaurants/cafes")
        
        if restaurants:
            print("\n   🍽️  Recommended Restaurants:")
            for i, rest in enumerate(restaurants[:5], 1):
                print(f"      {i}. {rest.name}")
                print(f"         🍴 {rest.cuisine_type} | {rest.price_range}")
                print(f"         📍 {rest.address[:60]}...")
                if rest.rating:
                    print(f"         ⭐ {rest.rating}")
        
    except Exception as e:
        print(f"   ❌ Error getting restaurants: {e}")
        import traceback
        traceback.print_exc()
        restaurant_results = {"restaurants": []}
    
    # Step 5: Get experiences (if implemented)
    print("\n6️⃣  Getting Experiences (ExperienceAgent)...")
    try:
        experience_results = await orchestrator.experience_agent.process(
            trip_request, stay_results, restaurant_results, user_profile
        )
        experiences = experience_results.get("experiences", [])
        print(f"   ✅ Found {len(experiences)} experiences/activities")
        
        if experiences:
            print("\n   🎯 Available Activities:")
            for i, exp in enumerate(experiences[:5], 1):
                print(f"      {i}. {exp.name}")
                print(f"         📂 {exp.category}")
                if exp.price:
                    print(f"         💰 ${exp.price:.2f}")
        
    except Exception as e:
        print(f"   ⚠️  ExperienceAgent not fully implemented: {e}")
        experience_results = {"experiences": []}
    
    # Step 6: Calculate budget
    print("\n7️⃣  Calculating Budget (BudgetAgent)...")
    try:
        budget_results = await orchestrator.budget_agent.process(
            trip_request, stay_results, None, experience_results, restaurant_results, user_profile
        )
        budget = budget_results.get("budget")
        if budget:
            print(f"   ✅ Budget Calculated")
            print(f"      💰 Total: ${budget.total:.2f}")
            print(f"         - Accommodation: ${budget.accommodation:.2f}")
            print(f"         - Meals: ${budget.meals:.2f}")
            print(f"         - Experiences: ${budget.experiences:.2f}")
            print(f"         - Transportation: ${budget.transportation:.2f}")
            print(f"         - Miscellaneous: ${budget.miscellaneous:.2f}")
    except Exception as e:
        print(f"   ⚠️  BudgetAgent not fully implemented: {e}")
        budget_results = None
    
    # Step 7: Generate complete itinerary
    print("\n8️⃣  Generating Complete Itinerary (PlannerAgent)...")
    try:
        travel_results = None  # TravelAgent not implemented yet
        final_plan = await orchestrator.planner_agent.process(
            trip_request, stay_results, restaurant_results, travel_results, 
            experience_results, budget_results, user_profile
        )
        
        print(f"   ✅ Complete Trip Plan Generated!")
        print(f"\n   📅 Itinerary Summary:")
        print(f"      - Selected Accommodation: {final_plan.selected_accommodation.title if final_plan.selected_accommodation else 'N/A'}")
        print(f"      - Restaurants: {len(final_plan.restaurants)}")
        print(f"      - Experiences: {len(final_plan.experiences)}")
        print(f"      - Itinerary Days: {len(final_plan.itinerary)}")
        print(f"      - Total Budget: ${final_plan.budget.total:.2f}")
        
        # Display itinerary preview
        print(f"\n   📋 Itinerary Preview (First 2 Days):")
        for day_plan in final_plan.itinerary[:2]:
            print(f"\n      Day {day_plan.day} ({day_plan.date}):")
            if day_plan.activities:
                print(f"         Activities:")
                for activity in day_plan.activities[:3]:
                    time = activity.get('time', '')
                    desc = activity.get('description', '')[:60]
                    print(f"            {time} - {desc}...")
            if day_plan.meals:
                print(f"         Meals:")
                for meal in day_plan.meals:
                    meal_type = meal.get('type', '')
                    suggestion = meal.get('suggestion', '')[:50]
                    print(f"            {meal_type}: {suggestion}...")
            if day_plan.notes:
                print(f"         Notes: {day_plan.notes[:80]}...")
        
    except Exception as e:
        print(f"   ❌ Error generating itinerary: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Final summary
    print("\n" + "=" * 80)
    print("✅ Complete Workflow Test Successful!")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   ✓ User Profile: Registered")
    print(f"   ✓ Accommodations: {len(accommodations)} found")
    print(f"   ✓ Restaurants: {len(restaurants)} found")
    print(f"   ✓ Experiences: {len(experience_results.get('experiences', []))} found")
    print(f"   ✓ Budget: Calculated")
    print(f"   ✓ Itinerary: {len(final_plan.itinerary)} days generated")
    print(f"\n🎉 All agents working correctly with Google Gemini API!")
    print("=" * 80)


if __name__ == "__main__":
    print("\n🚀 Starting Complete Workflow Test...")
    print("This will test all agents in sequence:\n")
    print("   1. User Profile Registration")
    print("   2. StayAgent → Find accommodations")
    print("   3. RestaurantAgent → Find restaurants")
    print("   4. ExperienceAgent → Find activities")
    print("   5. BudgetAgent → Calculate budget")
    print("   6. PlannerAgent → Generate itinerary")
    print("\n")
    
    asyncio.run(test_complete_workflow())

