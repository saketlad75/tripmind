"""
Seed database with dummy data - 3 users with complete profiles
"""

import sqlite3
import sys
import os
from datetime import datetime, date
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_db_connection, DB_PATH


def seed_database():
    """Populate database with dummy user data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing data (optional - comment out if you want to keep existing data)
        cursor.execute("DELETE FROM travel_preferences")
        cursor.execute("DELETE FROM demographics")
        cursor.execute("DELETE FROM users")
        
        # User 1: John Doe - Business Traveler
        cursor.execute(
            """
            INSERT INTO users (user_id, name, date_of_birth, email, phone_number, 
                             country_of_residence, home_city, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "user_001",
                "John Doe",
                "1985-05-15",
                "john.doe@example.com",
                "+1-555-0101",
                "United States",
                "New York",
                datetime.now().isoformat(),
                datetime.now().isoformat()
            )
        )
        user1_id = cursor.lastrowid
        
        cursor.execute(
            """
            INSERT INTO demographics (user_id, gender, occupation, veteran_status, 
                                    disability, type_of_disability, disability_needs)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user1_id, "Male", "Software Engineer", 0, 0, None, json.dumps([]))
        )
        
        cursor.execute(
            """
            INSERT INTO travel_preferences (user_id, diet_preference, language_preferences)
            VALUES (?, ?, ?)
            """,
            (user1_id, "None", json.dumps(["english"]))
        )
        
        # User 2: Sarah Smith - Family Traveler
        cursor.execute(
            """
            INSERT INTO users (user_id, name, date_of_birth, email, phone_number, 
                             country_of_residence, home_city, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "user_002",
                "Sarah Smith",
                "1990-08-22",
                "sarah.smith@example.com",
                "+1-555-0102",
                "United States",
                "Los Angeles",
                datetime.now().isoformat(),
                datetime.now().isoformat()
            )
        )
        user2_id = cursor.lastrowid
        
        cursor.execute(
            """
            INSERT INTO demographics (user_id, gender, occupation, veteran_status, 
                                    disability, type_of_disability, disability_needs)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user2_id, "Female", "Marketing Manager", 0, 0, None, json.dumps([]))
        )
        
        cursor.execute(
            """
            INSERT INTO travel_preferences (user_id, diet_preference, language_preferences)
            VALUES (?, ?, ?)
            """,
            (user2_id, "Vegetarian", json.dumps(["english", "spanish"]))
        )
        
        # User 3: Michael Chen - Solo Adventure Traveler
        cursor.execute(
            """
            INSERT INTO users (user_id, name, date_of_birth, email, phone_number, 
                             country_of_residence, home_city, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "user_003",
                "Michael Chen",
                "1992-12-03",
                "michael.chen@example.com",
                "+1-555-0103",
                "United States",
                "San Francisco",
                datetime.now().isoformat(),
                datetime.now().isoformat()
            )
        )
        user3_id = cursor.lastrowid
        
        cursor.execute(
            """
            INSERT INTO demographics (user_id, gender, occupation, veteran_status, 
                                    disability, type_of_disability, disability_needs)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user3_id, "Male", "Photographer", 1, 1, "Hearing Impaired", json.dumps(["hearing impaired"]))
        )
        
        cursor.execute(
            """
            INSERT INTO travel_preferences (user_id, diet_preference, language_preferences)
            VALUES (?, ?, ?)
            """,
            (user3_id, "Vegan", json.dumps(["english", "mandarin"]))
        )
        
        conn.commit()
        print("✅ Successfully seeded database with 3 users:")
        print("   1. John Doe (user_001) - Business Traveler")
        print("   2. Sarah Smith (user_002) - Family Traveler")
        print("   3. Michael Chen (user_003) - Solo Adventure Traveler")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        conn.close()


def verify_data():
    """Verify the seeded data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n📊 Verifying seeded data...\n")
    
    # Check users
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()["count"]
    print(f"Users: {user_count}")
    
    cursor.execute("SELECT user_id, name, email FROM users")
    users = cursor.fetchall()
    for user in users:
        print(f"  - {user['name']} ({user['user_id']}) - {user['email']}")
    
    # Check demographics
    cursor.execute("SELECT COUNT(*) as count FROM demographics")
    demo_count = cursor.fetchone()["count"]
    print(f"\nDemographics: {demo_count}")
    
    # Check travel preferences
    cursor.execute("SELECT COUNT(*) as count FROM travel_preferences")
    pref_count = cursor.fetchone()["count"]
    print(f"Travel Preferences: {pref_count}")
    
    # Check disability_needs in demographics
    print(f"\nDisability Needs (from demographics):")
    cursor.execute("SELECT d.user_id, d.disability_needs, u.name FROM demographics d JOIN users u ON d.user_id = u.id")
    demos = cursor.fetchall()
    for demo in demos:
        disability = json.loads(demo['disability_needs']) if demo['disability_needs'] else []
        print(f"  - {demo['name']} ({demo['user_id']}): {', '.join(disability) if disability else 'None'}")
    
    conn.close()


if __name__ == "__main__":
    print("🌱 Seeding database with dummy data...")
    seed_database()
    verify_data()
    print("\n✅ Database seeding complete!")

