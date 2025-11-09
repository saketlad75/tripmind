-- ============================================================================
-- TripMind - Itinerary Tables Creation Script
-- ============================================================================
-- This script creates the tables for storing itineraries and their versions
-- Run this script to create the tables in your SQLite database
-- ============================================================================

-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- ============================================================================
-- 1. ITINERARIES TABLE
-- ============================================================================
-- Main trip records - stores latest version of each itinerary
-- ============================================================================
CREATE TABLE IF NOT EXISTS itineraries (
    trip_id TEXT PRIMARY KEY,                  -- Unique trip identifier
    user_id TEXT NOT NULL,                     -- User who created the trip
    itinerary TEXT NOT NULL                     -- Full TripPlan JSON (latest version)
);

-- ============================================================================
-- 2. ITINERARY_VERSIONS TABLE
-- ============================================================================
-- Stores all iterations/versions of each itinerary
-- Each modification creates a new version (no overwriting)
-- ============================================================================
CREATE TABLE IF NOT EXISTS itinerary_versions (
    trip_id TEXT NOT NULL,                      -- Links to itineraries.trip_id
    version_number INTEGER NOT NULL,            -- Version number (1, 2, 3, ...)
    itinerary TEXT NOT NULL,                    -- Full TripPlan JSON data
    PRIMARY KEY (trip_id, version_number),
    FOREIGN KEY (trip_id) REFERENCES itineraries(trip_id) ON DELETE CASCADE
);

-- ============================================================================
-- INDEXES for better query performance
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_itineraries_user_id ON itineraries(user_id);
CREATE INDEX IF NOT EXISTS idx_versions_trip_id ON itinerary_versions(trip_id);

-- ============================================================================
-- Example Queries
-- ============================================================================

-- Get all trips for a user
-- SELECT * FROM itineraries WHERE user_id = 'user_001' ORDER BY created_at DESC;

-- Get latest version of an itinerary
-- SELECT itinerary FROM itineraries WHERE trip_id = 'trip_123';

-- Get specific version of an itinerary
-- SELECT itinerary FROM itinerary_versions 
-- WHERE trip_id = 'trip_123' AND version_number = 2;

-- Get all versions of an itinerary
-- SELECT version_number, itinerary FROM itinerary_versions 
-- WHERE trip_id = 'trip_123' 
-- ORDER BY version_number ASC;

-- ============================================================================
-- End of Script
-- ============================================================================

