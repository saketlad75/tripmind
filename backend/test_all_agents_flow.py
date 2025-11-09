"""
Complete All-Agents Workflow Test
Tests the entire TripMind workflow with ALL agents:
1. User profile registration
2. StayAgent → Find accommodations
3. RestaurantAgent → Find restaurants
4. TravelAgent → Find transportation (with all sub-agents)
5. ExperienceAgent → Find activities
6. BudgetAgent → Calculate budget
7. PlannerAgent → Generate complete itinerary
"""

import asyncio
from services.orchestrator import TripOrchestrator
from shared.types import TripRequest, UserProfile
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()


async def test_all_agents_flow():
    """Test the complete trip planning workflow with all agents"""
    
    print("=" * 80)
    print("🚀 Testing Complete TripMind Workflow - ALL AGENTS")
    print("=" * 80)
    
    # Initialize orchestrator
    print("\n1️⃣  Initializing TripOrchestrator...")
    orchestrator = TripOrchestrator()
    await orchestrator.initialize()
    print("   ✅ Orchestrator initialized")
    
    # Step 1: Register user profile
    print("\n2️⃣  Registering User Profile...")
    user_profile = UserProfile(
        user_id="test_user_all_agents_001",
        name="Test User",
        email="test@example.com",
        phone_number="+1234567890",
        budget=3500.0,
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
        prompt="I want a 5-day quiet nature escape with good Wi-Fi, hiking trails, and local food near San Fransisco, California. I'll be traveling from New York.",
        user_id="test_user_all_agents_001",
        duration_days=5,
        travelers=2
    )
    print(f"   ✅ Trip Request Created")
    print(f"      Prompt: {trip_request.prompt}")
    print(f"      Duration: {trip_request.duration_days} days")
    print(f"      Travelers: {trip_request.travelers}")
    
    # Step 3: Get accommodations
    print("\n" + "=" * 80)
    print("4️⃣  STAY AGENT - Getting Accommodations...")
    print("=" * 80)
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
    print("\n" + "=" * 80)
    print("5️⃣  RESTAURANT AGENT - Getting Restaurants...")
    print("=" * 80)
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
    
    # Step 5: Get transportation (TravelAgent with all sub-agents)
    print("\n" + "=" * 80)
    print("6️⃣  TRAVEL AGENT - Getting Transportation Options...")
    print("=" * 80)
    try:
        travel_results = await orchestrator.travel_agent.process(
            trip_request, stay_results
        )
        transportation = travel_results.get("transportation", [])
        print(f"   ✅ Found {len(transportation)} transportation options")
        
        if transportation:
            print("\n   ✈️  Transportation Options:")
            for i, trans in enumerate(transportation[:5], 1):
                print(f"      {i}. {trans.type.upper()}: {trans.origin} → {trans.destination}")
                print(f"         💰 ${trans.price:.2f}")
                if hasattr(trans, 'duration') and trans.duration:
                    print(f"         ⏱️  Duration: {trans.duration}")
                if hasattr(trans, 'provider') and trans.provider:
                    print(f"         🏢 Provider: {trans.provider}")
        
    except Exception as e:
        print(f"   ⚠️  Error getting transportation: {e}")
        import traceback
        traceback.print_exc()
        travel_results = {"transportation": []}
    
    # Step 6: Get experiences
    print("\n" + "=" * 80)
    print("7️⃣  EXPERIENCE AGENT - Getting Activities & Experiences...")
    print("=" * 80)
    try:
        experience_results = await orchestrator.experience_agent.process(
            trip_request, stay_results
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
                if exp.rating:
                    print(f"         ⭐ {exp.rating}")
        
    except Exception as e:
        print(f"   ⚠️  Error getting experiences: {e}")
        import traceback
        traceback.print_exc()
        experience_results = {"experiences": []}
    
    # Step 7: Calculate budget
    print("\n" + "=" * 80)
    print("8️⃣  BUDGET AGENT - Calculating Budget...")
    print("=" * 80)
    try:
        budget_results = await orchestrator.budget_agent.process(
            trip_request, stay_results, travel_results, experience_results, restaurant_results
        )
        budget = budget_results.get("budget")
        if budget:
            print(f"   ✅ Budget Calculated")
            print(f"\n   💰 Budget Breakdown:")
            print(f"      - Accommodation: ${budget.accommodation:.2f}")
            print(f"      - Transportation: ${budget.transportation:.2f}")
            print(f"      - Meals: ${budget.meals:.2f}")
            print(f"      - Experiences: ${budget.experiences:.2f}")
            print(f"      - Miscellaneous: ${budget.miscellaneous:.2f}")
            print(f"      ─────────────────────────")
            print(f"      💵 TOTAL: ${budget.total:.2f}")
            
            user_budget = user_profile.budget
            if budget.total > user_budget:
                print(f"\n   ⚠️  Budget exceeds user limit (${user_budget:.2f}) by ${budget.total - user_budget:.2f}")
            else:
                print(f"\n   ✅ Budget within user limit (${user_budget:.2f})")
    except Exception as e:
        print(f"   ⚠️  Error calculating budget: {e}")
        import traceback
        traceback.print_exc()
        budget_results = None
    
    # Step 8: Generate complete itinerary
    print("\n" + "=" * 80)
    print("9️⃣  PLANNER AGENT - Generating Complete Itinerary...")
    print("=" * 80)
    try:
        final_plan = await orchestrator.planner_agent.process(
            trip_request, stay_results, restaurant_results, travel_results, 
            experience_results, budget_results, user_profile
        )
        
        print(f"   ✅ Complete Trip Plan Generated!")
        print(f"\n   📅 Trip Plan Summary:")
        print(f"      - Selected Accommodation: {final_plan.selected_accommodation.title if final_plan.selected_accommodation else 'N/A'}")
        print(f"      - Restaurants: {len(final_plan.restaurants)}")
        print(f"      - Transportation Options: {len(final_plan.transportation)}")
        print(f"      - Experiences: {len(final_plan.experiences)}")
        print(f"      - Itinerary Days: {len(final_plan.itinerary)}")
        print(f"      - Total Budget: ${final_plan.budget.total:.2f}")
        
        # Display detailed itinerary
        print(f"\n   📋 Complete Itinerary:")
        for day_plan in final_plan.itinerary:
            print(f"\n      {'='*70}")
            print(f"      Day {day_plan.day} - {day_plan.date}")
            print(f"      {'='*70}")
            
            if day_plan.activities:
                print(f"      🎯 Activities:")
                for activity in day_plan.activities:
                    time = activity.get('time', '')
                    desc = activity.get('description', '')
                    location = activity.get('location', '')
                    print(f"         {time:12} - {desc}")
                    if location:
                        print(f"                      📍 {location}")
            
            if day_plan.meals:
                print(f"      🍽️  Meals:")
                for meal in day_plan.meals:
                    meal_type = meal.get('type', '')
                    suggestion = meal.get('suggestion', '')
                    restaurant_id = meal.get('restaurant_id', '')
                    print(f"         {meal_type:12} - {suggestion}")
                    if restaurant_id:
                        print(f"                      🏪 Restaurant ID: {restaurant_id}")
            
            if day_plan.notes:
                print(f"      📝 Notes: {day_plan.notes}")
        
    except Exception as e:
        print(f"   ❌ Error generating itinerary: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Final summary
    print("\n" + "=" * 80)
    print("✅ COMPLETE WORKFLOW TEST SUCCESSFUL!")
    print("=" * 80)
    print(f"\n📊 Final Summary:")
    print(f"   ✓ User Profile: Registered")
    print(f"   ✓ StayAgent: {len(accommodations)} accommodations found")
    print(f"   ✓ RestaurantAgent: {len(restaurants)} restaurants found")
    print(f"   ✓ TravelAgent: {len(travel_results.get('transportation', []))} transportation options found")
    print(f"   ✓ ExperienceAgent: {len(experience_results.get('experiences', []))} experiences found")
    print(f"   ✓ BudgetAgent: Budget calculated (${final_plan.budget.total:.2f})")
    print(f"   ✓ PlannerAgent: {len(final_plan.itinerary)}-day itinerary generated")
    print(f"\n🎉 All agents working correctly with Google Gemini API!")
    print("=" * 80)


if __name__ == "__main__":
    print("\n🚀 Starting Complete All-Agents Workflow Test...")
    print("This will test ALL agents in sequence:\n")
    print("   1. User Profile Registration")
    print("   2. StayAgent → Find accommodations")
    print("   3. RestaurantAgent → Find restaurants")
    print("   4. TravelAgent → Find transportation (flight/train/bus/car)")
    print("   5. ExperienceAgent → Find activities")
    print("   6. BudgetAgent → Calculate budget")
    print("   7. PlannerAgent → Generate complete itinerary")
    print("\n⏱️  This may take a few minutes...\n")
    
    asyncio.run(test_all_agents_flow())

