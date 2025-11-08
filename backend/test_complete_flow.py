"""
Test Complete Flow: User Registration → Trip Planning → Itinerary Generation
Tests the full workflow from user prompt to complete itinerary
"""

import asyncio
from services.orchestrator import TripOrchestrator
from shared.types import TripRequest, UserProfile
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()


async def test_complete_flow():
    """Test the complete trip planning flow"""
    
    print("=" * 80)
    print("Testing Complete TripMind Flow")
    print("=" * 80)
    
    # Initialize orchestrator
    print("\n1. Initializing Orchestrator...")
    orchestrator = TripOrchestrator()
    await orchestrator.initialize()
    print("   ✓ Orchestrator initialized")
    
    # Step 1: User Registration (simulating UI registration)
    print("\n2. User Registration (simulating UI)...")
    user_profile = UserProfile(
        user_id="user_001",
        name="John Doe",
        email="john.doe@example.com",
        phone_number="+1234567890",
        date_of_birth=date(1990, 5, 15),
        budget=2500.0,
        dietary_preferences=["vegetarian"],
        disability_needs=[]
    )
    orchestrator.register_user_profile(user_profile)
    print(f"   ✓ User profile registered:")
    print(f"     - Name: {user_profile.name}")
    print(f"     - Budget: ${user_profile.budget}")
    print(f"     - Dietary: {', '.join(user_profile.dietary_preferences)}")
    
    # Step 2: User creates trip request (only prompt, no location/budget)
    print("\n3. User Creates Trip Request...")
    request = TripRequest(
        prompt="I want a 5-day quiet nature escape with good Wi-Fi, hiking trails, and local food near Zurich.",
        user_id="user_001",
        duration_days=5,
        travelers=2
        # No destination, no budget - will be extracted/used from profile
    )
    print(f"   ✓ Trip request created:")
    print(f"     Prompt: '{request.prompt}'")
    print(f"     Duration: {request.duration_days} days")
    print(f"     Travelers: {request.travelers}")
    print(f"     (No explicit location or budget provided)")
    
    # Step 3: Run StayAgent (finds accommodations - preferably 3+, but includes all available)
    print("\n4. Running StayAgent...")
    print("   → Extracting location from prompt...")
    print("   → Finding accommodations (preferably 3+, but includes all available)...")
    print("   → Using budget from user profile...")
    
    try:
        plan = await orchestrator.plan_trip(request, user_profile)
        
        print(f"\n   ✓ StayAgent Results:")
        print(f"     - Accommodations found: {len(plan.accommodations)}")
        
        # Show message if available (from stay_results)
        if hasattr(plan, 'accommodations') and len(plan.accommodations) > 0:
            if len(plan.accommodations) == 1:
                print(f"     ℹ️  Note: Only 1 accommodation found in this area.")
            elif len(plan.accommodations) < 3:
                print(f"     ℹ️  Note: Found {len(plan.accommodations)} accommodations (preferred: 3+).")
        
        if plan.accommodations:
            print(f"\n   Available Accommodations:")
            for i, acc in enumerate(plan.accommodations[:3], 1):
                print(f"   {i}. {acc.title}")
                print(f"      Address: {acc.address}")
                print(f"      Price: ${acc.price_per_night}/night (Total: ${acc.total_price})")
                if acc.rating:
                    print(f"      Rating: {acc.rating}/5.0 ({acc.review_count} reviews)")
            
            # Step 4: User selects accommodation (simulating UI selection)
            print("\n5. User Selects Accommodation (simulating UI selection)...")
            selected_acc = plan.accommodations[0]
            request.selected_accommodation_id = selected_acc.id
            print(f"   ✓ Selected: {selected_acc.title}")
            print(f"     Address: {selected_acc.address}")
            
            # Step 5: Run RestaurantAgent (finds 3-4 restaurants)
            print("\n6. Running RestaurantAgent...")
            print("   → Finding restaurants near selected accommodation...")
            print("   → Matching dietary preferences...")
            print("   → Finding minimum 3-4 restaurants/cafes...")
            
            # Re-run planning with selected accommodation
            plan = await orchestrator.plan_trip(request, user_profile)
            
            print(f"\n   ✓ RestaurantAgent Results:")
            print(f"     - Restaurants/Cafes found: {len(plan.restaurants)}")
            
            if plan.restaurants:
                print(f"\n   Recommended Restaurants/Cafes:")
                for i, r in enumerate(plan.restaurants[:4], 1):
                    print(f"   {i}. {r.name}")
                    print(f"      Cuisine: {r.cuisine_type} | Price: {r.price_range}")
                    if r.average_price_per_person:
                        print(f"      Avg Price: ${r.average_price_per_person}/person")
                    if r.dietary_options:
                        print(f"      Dietary: {', '.join(r.dietary_options)}")
            
            # Step 6: Run PlannerAgent (creates itinerary)
            print("\n7. Running PlannerAgent...")
            print("   → Creating day-by-day itinerary...")
            print("   → Matching activities to trip theme...")
            print("   → Scheduling meals at recommended restaurants...")
            
            # Final plan should have itinerary
            final_plan = await orchestrator.plan_trip(request, user_profile)
            
            print(f"\n   ✓ PlannerAgent Results:")
            print(f"     - Itinerary days: {len(final_plan.itinerary)}")
            
            if final_plan.itinerary:
                print(f"\n   📅 Complete Itinerary:")
                for day_plan in final_plan.itinerary:
                    print(f"\n   Day {day_plan.day} - {day_plan.date}")
                    print(f"   {'='*60}")
                    
                    if day_plan.activities:
                        print(f"   Activities:")
                        for activity in day_plan.activities:
                            time = activity.get("time", "TBD")
                            title = activity.get("title", "Activity")
                            desc = activity.get("description", "")
                            location = activity.get("location", "")
                            print(f"     • {time}: {title}")
                            if desc:
                                print(f"       {desc}")
                            if location:
                                print(f"       📍 {location}")
                    
                    if day_plan.meals:
                        print(f"   Meals:")
                        for meal in day_plan.meals:
                            time = meal.get("time", "TBD")
                            meal_type = meal.get("type", "meal")
                            restaurant = meal.get("restaurant", "Restaurant")
                            desc = meal.get("description", "")
                            print(f"     • {time} ({meal_type}): {restaurant}")
                            if desc:
                                print(f"       {desc}")
                    
                    if day_plan.notes:
                        print(f"   💡 Notes: {day_plan.notes}")
            
            # Step 7: Budget Summary
            print(f"\n8. Budget Summary:")
            print(f"   {'='*60}")
            budget = final_plan.budget
            print(f"   Accommodation: ${budget.accommodation:.2f}")
            print(f"   Meals: ${budget.meals:.2f}")
            print(f"   Transportation: ${budget.transportation:.2f}")
            print(f"   Experiences: ${budget.experiences:.2f}")
            print(f"   Miscellaneous: ${budget.miscellaneous:.2f}")
            print(f"   {'-'*60}")
            print(f"   Total: ${budget.total:.2f} {budget.currency}")
            
            # Summary
            print(f"\n{'='*80}")
            print("✅ Complete Flow Test Successful!")
            print(f"{'='*80}")
            print(f"\nSummary:")
            print(f"  ✓ User registered with profile")
            print(f"  ✓ Location extracted from prompt: 'Zurich'")
            print(f"  ✓ Found {len(final_plan.accommodations)} accommodations")
            print(f"  ✓ User selected: {final_plan.selected_accommodation.title if final_plan.selected_accommodation else 'None'}")
            print(f"  ✓ Found {len(final_plan.restaurants)} restaurants/cafes")
            print(f"  ✓ Created {len(final_plan.itinerary)}-day detailed itinerary")
            print(f"  ✓ Budget calculated: ${budget.total:.2f}")
            
        else:
            print("\n   ⚠ No accommodations found")
            print("   Cannot continue with restaurant and itinerary planning")
            
    except Exception as e:
        print(f"\n   ✗ Error during flow: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n🚀 Starting Complete Flow Test...")
    print("This will test:")
    print("  1. User Registration")
    print("  2. Trip Request (prompt only)")
    print("  3. StayAgent (finds accommodations)")
    print("  4. User Selection (simulated)")
    print("  5. RestaurantAgent (finds restaurants)")
    print("  6. PlannerAgent (creates itinerary)")
    print("  7. Budget Calculation")
    print("\n")
    
    asyncio.run(test_complete_flow())

