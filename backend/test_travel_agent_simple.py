"""
Simple test for TravelAgent
Tests basic functionality
"""

import asyncio
from agents.travel_agent import TravelAgent
from shared.types import TripRequest
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()


async def test_travel_agent():
    """Simple test of TravelAgent"""
    
    print("=" * 80)
    print("TRAVEL AGENT - SIMPLE TEST")
    print("=" * 80)
    
    # Test case: Simple domestic trip
    request = TripRequest(
        prompt="I want to travel from New York to Boston for a weekend trip",
        destination="Boston, MA",
        start_date=date.today() + timedelta(days=20),
        duration_days=2,
        budget=500.0,
        travelers=1,
        preferences={
            "origin": {"text": "New York, NY"},
            "priority": "balanced"
        }
    )
    
    print(f"\n📍 Origin: {request.preferences['origin']['text']}")
    print(f"🎯 Destination: {request.destination}")
    print(f"💰 Budget: ${request.budget}")
    print(f"👥 Travelers: {request.travelers}")
    print(f"📅 Start Date: {request.start_date}")
    
    print("\n" + "-" * 80)
    print("Initializing TravelAgent...")
    print("-" * 80)
    
    agent = TravelAgent()
    await agent.initialize()
    
    print("\n" + "-" * 80)
    print("Processing request...")
    print("-" * 80)
    
    try:
        results = await agent.process(request)
        
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        
        print(f"\n✅ Success! Found {results['count']} transportation options")
        print(f"📍 Origin: {results['origin']}")
        print(f"🎯 Destination: {results['destination']}")
        print(f"🚀 Recommended Mode: {results['recommended_mode'].upper()}")
        
        # Show summary
        print(f"\n📊 Summary:")
        print(f"   - Flights: {len(results.get('flights', []))}")
        print(f"   - Trains: {len(results.get('trains', []))}")
        print(f"   - Buses: {len(results.get('buses', []))}")
        print(f"   - Cars/Cabs: {len(results.get('cars', []))}")
        print(f"   - Airport Transfers: {len(results.get('airport_to_destination', []))}")
        
        # Show top 3 options
        all_options = results.get('transportation', [])
        if all_options:
            print(f"\n🔝 Top 3 Options:")
            for i, option in enumerate(all_options[:3], 1):
                duration = option.duration_minutes or 0
                hours = duration // 60
                minutes = duration % 60
                print(f"\n   {i}. {option.provider} ({option.type})")
                print(f"      💰 ${option.price:.2f} | ⏱️  {hours}h {minutes}m")
                if option.carbon_emissions_kg:
                    print(f"      🌱 {option.carbon_emissions_kg} kg CO₂ ({option.carbon_score})")
                if option.recommended:
                    print(f"      ⭐ RECOMMENDED")
        
        print("\n" + "=" * 80)
        print("✅ TEST PASSED - TravelAgent is working correctly!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_travel_agent())
    exit(0 if success else 1)

