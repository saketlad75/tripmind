"""
Database initialization and connection management for TripMind
"""

import sqlite3
from datetime import datetime
from typing import Optional
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "tripmind.db")


def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def init_db():
    """Initialize database and create all tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable foreign key support in SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1) Users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,          -- External user ID (from auth system)
            name TEXT NOT NULL,
            date_of_birth TEXT,                    -- store as 'YYYY-MM-DD'
            email TEXT UNIQUE NOT NULL,
            phone_number TEXT,
            country_of_residence TEXT,
            home_city TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )

    # 2) Demographics table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS demographics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            gender TEXT,
            occupation TEXT,
            veteran_status INTEGER,                -- 0 = no, 1 = yes
            disability INTEGER,                    -- 0 = no, 1 = yes
            type_of_disability TEXT,
            disability_needs TEXT,                  -- JSON array string
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )

    # 3) Travel preferences table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS travel_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            diet_preference TEXT,
            language_preferences TEXT,             -- e.g. '["english", "spanish"]' (JSON string)
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )

    # 4) Itineraries table (main trip records - stores latest version)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS itineraries (
            user_id TEXT NOT NULL,
            trip_id TEXT NOT NULL,
            itinerary TEXT NOT NULL,                -- JSON string of TripPlan (latest version) - the generated itinerary text
            PRIMARY KEY (user_id, trip_id)
        );
        """
    )

    # 5) Itinerary versions table (stores all iterations)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS itinerary_versions (
            user_id TEXT NOT NULL,
            trip_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            modified_by TEXT NOT NULL,              -- User ID who made this modification
            itinerary TEXT NOT NULL,                -- JSON string of TripPlan - the generated itinerary text
            created_at TEXT NOT NULL,                -- Timestamp when version was created
            PRIMARY KEY (user_id, trip_id, version_number),
            FOREIGN KEY (user_id, trip_id) REFERENCES itineraries(user_id, trip_id) ON DELETE CASCADE
        );
        """
    )

    # Create indexes for better query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_itineraries_user_id ON itineraries(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_itineraries_trip_id ON itineraries(trip_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_versions_user_trip ON itinerary_versions(user_id, trip_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_versions_modified_by ON itinerary_versions(modified_by);")

    conn.commit()
    conn.close()
    print(f"✅ Initialized database and tables in {DB_PATH}")


if __name__ == "__main__":
    init_db()

