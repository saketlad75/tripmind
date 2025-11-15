"""
Test script for the chat API endpoint
Tests the /api/trips/chat endpoint that integrates with the UI
"""

import asyncio
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"


async def test_chat_api():
    """Test the chat API endpoint"""
    
    print("=" * 80)
    print("🧪 Testing Chat API Endpoint")
    print("=" * 80)
    
    # Step 1: Create user profile
    print("\n1️⃣  Creating User Profile...")
    user_id = "test_chat_user_001"
    profile_data = {
        "user_id": user_id,
        "name": "Chat Test User",
        "email": "chattest@example.com",
        "phone_number": "+1234567890",
        "budget": 3500.0,
        "dietary_preferences": ["vegetarian"],
        "disability_needs": []
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/trips/users/{user_id}/profile",
                json=profile_data
            )
            response.raise_for_status()
            print(f"   ✅ User profile created: {response.json()['name']}")
        except Exception as e:
            print(f"   ❌ Error creating profile: {e}")
            return
    
    # Step 2: Send first chat message (create new trip)
    print("\n2️⃣  Sending First Chat Message (Create New Trip)...")
    chat_request = {
        "prompt": "I want a 5-day quiet nature escape with good Wi-Fi, hiking trails, and local food near San Francisco, California. I'll be traveling from New York.",
        "user_id": user_id
        # trip_id not provided - will create new trip
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout for agent processing
        try:
            print("   ⏳ Processing (this may take a few minutes)...")
            response = await client.post(
                f"{BASE_URL}/api/trips/chat",
                json=chat_request
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"   ✅ Trip plan created!")
            print(f"   📋 Trip ID: {result['trip_id']}")
            print(f"   📝 Status: {result['status']}")
            print(f"   💬 Message: {result['message']}")
            
            trip_id = result['trip_id']
            trip_plan = result['trip_plan']
            
            print(f"\n   📊 Trip Plan Summary:")
            print(f"      - Accommodations: {len(trip_plan.get('accommodations', []))}")
            print(f"      - Restaurants: {len(trip_plan.get('restaurants', []))}")
            print(f"      - Transportation: {len(trip_plan.get('transportation', []))}")
            print(f"      - Experiences: {len(trip_plan.get('experiences', []))}")
            print(f"      - Itinerary Days: {len(trip_plan.get('itinerary', []))}")
            if trip_plan.get('budget'):
                print(f"      - Total Budget: ${trip_plan['budget']['total']:.2f}")
            
        except Exception as e:
            print(f"   ❌ Error creating trip plan: {e}")
            import traceback
            traceback.print_exc()
            return
    
    # Step 3: Retrieve the trip plan
    print("\n3️⃣  Retrieving Trip Plan...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/api/trips/chat/{user_id}/{trip_id}"
            )
            response.raise_for_status()
            retrieved_plan = response.json()
            print(f"   ✅ Trip plan retrieved successfully")
            
            # Safely get selected accommodation
            selected_acc = retrieved_plan.get('selected_accommodation')
            if selected_acc and isinstance(selected_acc, dict):
                print(f"      - Selected Accommodation: {selected_acc.get('title', 'N/A')}")
            else:
                print(f"      - Selected Accommodation: N/A (not selected yet)")
            
            print(f"      - Accommodations: {len(retrieved_plan.get('accommodations', []))}")
            print(f"      - Restaurants: {len(retrieved_plan.get('restaurants', []))}")
            print(f"      - Transportation: {len(retrieved_plan.get('transportation', []))}")
            print(f"      - Experiences: {len(retrieved_plan.get('experiences', []))}")
        except Exception as e:
            print(f"   ❌ Error retrieving trip plan: {e}")
            import traceback
            traceback.print_exc()
            return
    
    # Step 4: Update trip plan with new prompt
    print("\n4️⃣  Updating Trip Plan with New Prompt...")
    update_request = {
        "prompt": "Actually, I want to add more hiking activities and prefer budget-friendly restaurants.",
        "user_id": user_id,
        "trip_id": trip_id  # Provide trip_id to update existing plan
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            print("   ⏳ Processing update (this may take a few minutes)...")
            response = await client.post(
                f"{BASE_URL}/api/trips/chat",
                json=update_request
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"   ✅ Trip plan updated!")
            print(f"   📝 Status: {result['status']}")
            print(f"   💬 Message: {result['message']}")
            
            updated_plan = result['trip_plan']
            print(f"\n   📊 Updated Trip Plan Summary:")
            print(f"      - Restaurants: {len(updated_plan.get('restaurants', []))}")
            print(f"      - Experiences: {len(updated_plan.get('experiences', []))}")
            
        except httpx.HTTPStatusError as e:
            print(f"   ❌ Error updating trip plan: {e}")
            if e.response.status_code == 500:
                try:
                    error_detail = e.response.json()
                    print(f"   📋 Error details: {error_detail}")
                except:
                    print(f"   📋 Error response: {e.response.text}")
            import traceback
            traceback.print_exc()
            return
        except Exception as e:
            print(f"   ❌ Error updating trip plan: {e}")
            import traceback
            traceback.print_exc()
            return
    
    print("\n" + "=" * 80)
    print("✅ Chat API Test Complete!")
    print("=" * 80)
    print("\n📝 Summary:")
    print("   ✓ User profile created")
    print("   ✓ New trip plan created via chat")
    print("   ✓ Trip plan retrieved")
    print("   ✓ Trip plan updated via chat")
    print("\n🎉 All tests passed!")


if __name__ == "__main__":
    print("\n🚀 Starting Chat API Test...")
    print("Make sure the backend server is running on http://localhost:8000")
    print("Run: cd backend && uvicorn main:app --reload\n")
    
    asyncio.run(test_chat_api())

