# Changelog

## [Unreleased] - 2025-01-XX

### Added
- **UserProfile Model**: Added user profile system to store user preferences
  - Personal information (name, email, phone, DOB)
  - Budget preferences
  - Dietary preferences (vegetarian, vegan, gluten-free, halal, etc.)
  - Disability/accessibility needs (wheelchair accessible, hearing impaired, etc.)

- **RestaurantAgent**: New agent using Dedalus Labs to find restaurants
  - Searches restaurants near selected accommodation
  - Considers user's dietary preferences and accessibility needs
  - Filters by budget constraints
  - Returns structured restaurant data with ratings, prices, and booking info

- **Restaurant Model**: New data model for restaurant listings
  - Cuisine type, price range, ratings
  - Dietary options and accessibility features
  - Location, contact info, opening hours

- **Updated Workflow**: RestaurantAgent now runs after StayAgent
  - Workflow: Stay → Restaurant → Travel → Experience → Budget → Planner

- **API Endpoints**:
  - `POST /api/trips/users/{user_id}/profile` - Create/update user profile
  - `GET /api/trips/users/{user_id}/profile` - Get user profile
  - Updated `POST /api/trips/plan` - Now requires user_id and uses profile data

### Changed
- **TripRequest**: Now only requires `prompt` and `user_id`
  - All other fields (destination, budget, dates) are optional
  - Budget and preferences come from user profile
  - Added `selected_accommodation_id` field for restaurant agent

- **TripPlan**: Now includes `restaurants` list

### Architecture
- User profile data stored in orchestrator (in-memory, for production use database)
- RestaurantAgent uses same Dedalus Labs setup as StayAgent
- Workflow automatically fetches user profile when planning trip

