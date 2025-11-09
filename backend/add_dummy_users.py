"""
Script to add 5 dummy users to the database and orchestrator
"""

import sys
import os
import json
from datetime import datetime, date, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import get_db_connection, init_db
from shared.types import UserProfile
from services.orchestrator import TripOrchestrator

# Initialize database
init_db()

# Dummy user data
dummy_users = [
    {
        "user_id": "Kartik7",
        "name": "Kartik Sharma",
        "email": "kartik.sharma@example.com",
        "phone_number": "+1-555-0101",
        "date_of_birth": "1995-03-15",
        "country_of_residence": "USA",
        "home_city": "New York",
        "gender": "Male",
        "occupation": "Software Engineer",
        "budget": 3000.0,
        "dietary_preferences": ["vegetarian"],
        "disability_needs": [],
        "veteran_status": 0,
        "disability": 0,
    },
    {
        "user_id": "sarah_jones",
        "name": "Sarah Jones",
        "email": "sarah.jones@example.com",
        "phone_number": "+1-555-0102",
        "date_of_birth": "1992-07-22",
        "country_of_residence": "USA",
        "home_city": "San Francisco",
        "gender": "Female",
        "occupation": "Marketing Manager",
        "budget": 5000.0,
        "dietary_preferences": ["vegan", "gluten-free"],
        "disability_needs": ["wheelchair accessible"],
        "veteran_status": 0,
        "disability": 1,
        "type_of_disability": "Mobility",
    },
    {
        "user_id": "mike_chen",
        "name": "Mike Chen",
        "email": "mike.chen@example.com",
        "phone_number": "+1-555-0103",
        "date_of_birth": "1988-11-08",
        "country_of_residence": "USA",
        "home_city": "Los Angeles",
        "gender": "Male",
        "occupation": "Data Scientist",
        "budget": 4000.0,
        "dietary_preferences": [],
        "disability_needs": [],
        "veteran_status": 1,
        "disability": 0,
    },
    {
        "user_id": "emily_williams",
        "name": "Emily Williams",
        "email": "emily.williams@example.com",
        "phone_number": "+1-555-0104",
        "date_of_birth": "1994-05-30",
        "country_of_residence": "USA",
        "home_city": "Chicago",
        "gender": "Female",
        "occupation": "Teacher",
        "budget": 2500.0,
        "dietary_preferences": ["halal"],
        "disability_needs": ["hearing impaired"],
        "veteran_status": 0,
        "disability": 1,
        "type_of_disability": "Hearing",
    },
    {
        "user_id": "david_brown",
        "name": "David Brown",
        "email": "david.brown@example.com",
        "phone_number": "+1-555-0105",
        "date_of_birth": "1990-09-14",
        "country_of_residence": "USA",
        "home_city": "Seattle",
        "gender": "Male",
        "occupation": "Product Manager",
        "budget": 3500.0,
        "dietary_preferences": ["vegetarian", "dairy-free"],
        "disability_needs": [],
        "veteran_status": 0,
        "disability": 0,
    },
]


def add_users_to_database():
    """Add users to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    added_count = 0
    
    for user_data in dummy_users:
        try:
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE user_id = ?", (user_data["user_id"],))
            existing = cursor.fetchone()
            
            if existing:
                print(f"⚠️  User {user_data['user_id']} already exists, skipping...")
                continue
            
            # Insert into users table
            now = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT INTO users (user_id, name, email, phone_number, date_of_birth, 
                                 country_of_residence, home_city, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_data["user_id"],
                    user_data["name"],
                    user_data["email"],
                    user_data["phone_number"],
                    user_data["date_of_birth"],
                    user_data["country_of_residence"],
                    user_data["home_city"],
                    now,
                    now,
                ),
            )
            
            # Get the internal user ID
            user_internal_id = cursor.lastrowid
            
            # Insert into demographics table
            disability_needs_json = json.dumps(user_data.get("disability_needs", []))
            cursor.execute(
                """
                INSERT INTO demographics (user_id, gender, occupation, veteran_status, 
                                        disability, type_of_disability, disability_needs)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_internal_id,
                    user_data.get("gender"),
                    user_data.get("occupation"),
                    user_data.get("veteran_status", 0),
                    user_data.get("disability", 0),
                    user_data.get("type_of_disability"),
                    disability_needs_json,
                ),
            )
            
            # Insert into travel_preferences table
            diet_preference = ", ".join(user_data.get("dietary_preferences", [])) if user_data.get("dietary_preferences") else None
            language_preferences_json = json.dumps(["english"])  # Default to English
            
            cursor.execute(
                """
                INSERT INTO travel_preferences (user_id, diet_preference, language_preferences)
                VALUES (?, ?, ?)
                """,
                (user_internal_id, diet_preference, language_preferences_json),
            )
            
            added_count += 1
            print(f"✅ Added user: {user_data['name']} ({user_data['user_id']})")
            
        except Exception as e:
            print(f"❌ Error adding user {user_data['user_id']}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    conn.close()
    print(f"\n✅ Successfully added {added_count} users to database")
    return added_count


def register_users_in_orchestrator():
    """Register users in orchestrator's in-memory storage"""
    try:
        orchestrator = TripOrchestrator()
        
        for user_data in dummy_users:
            # Create UserProfile object
            profile = UserProfile(
                user_id=user_data["user_id"],
                name=user_data["name"],
                email=user_data["email"],
                phone_number=user_data.get("phone_number"),
                date_of_birth=date.fromisoformat(user_data["date_of_birth"]) if user_data.get("date_of_birth") else None,
                budget=user_data.get("budget"),
                dietary_preferences=user_data.get("dietary_preferences", []),
                disability_needs=user_data.get("disability_needs", []),
            )
            
            # Register in orchestrator
            orchestrator.register_user_profile(profile)
            print(f"✅ Registered {user_data['name']} in orchestrator")
        
        print(f"\n✅ Successfully registered {len(dummy_users)} users in orchestrator")
        return len(dummy_users)
    except Exception as e:
        print(f"❌ Error registering users in orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return 0


if __name__ == "__main__":
    print("=" * 60)
    print("Adding 5 dummy users to database and orchestrator...")
    print("=" * 60)
    print()
    
    # Add to database
    db_count = add_users_to_database()
    
    print()
    print("=" * 60)
    print("Registering users in orchestrator...")
    print("=" * 60)
    print()
    
    # Register in orchestrator (note: this is in-memory, so it will be lost on server restart)
    # The orchestrator will load from database when needed
    # For now, we'll just add to database
    
    print()
    print("=" * 60)
    print(f"✅ Complete! Added {db_count} users to database.")
    print("=" * 60)
    print()
    print("Note: The orchestrator loads user profiles from the database")
    print("when processing trip requests, so no manual registration needed.")
    print()

