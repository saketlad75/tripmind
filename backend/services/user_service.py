"""
User Service - Fetches user data from database and converts to UserProfile
"""

from typing import Optional
import json
from shared.types import UserProfile
from database.db import get_db_connection


class UserService:
    """Service for fetching and managing user data from database"""
    
    def get_user_from_db(self, user_id: str) -> Optional[dict]:
        """
        Fetch complete user data from database
        
        Args:
            user_id: External user_id (string like "Kartik7") or internal id
        
        Returns:
            Dictionary with user, demographics, and travel_preferences data
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # First try to find by external user_id (string like "Kartik7")
            cursor.execute(
                """
                SELECT u.id, u.user_id, u.name, u.date_of_birth, u.email, 
                       u.phone_number, u.country_of_residence, u.home_city,
                       u.created_at, u.updated_at
                FROM users u
                WHERE u.user_id = ?
                """,
                (user_id,)
            )
            user_row = cursor.fetchone()
            
            # If not found by user_id, try as internal id (integer)
            if not user_row:
                try:
                    user_id_int = int(user_id)
                    cursor.execute(
                        """
                        SELECT u.id, u.user_id, u.name, u.date_of_birth, u.email, 
                               u.phone_number, u.country_of_residence, u.home_city,
                               u.created_at, u.updated_at
                        FROM users u
                        WHERE u.id = ?
                        """,
                        (user_id_int,)
                    )
                    user_row = cursor.fetchone()
                except ValueError:
                    pass  # user_id is not a number, already tried user_id
            
            if not user_row:
                return None
            
            user_data = dict(user_row)
            
            # Get demographics (using internal id)
            cursor.execute(
                """
                SELECT gender, occupation, veteran_status, disability, 
                       type_of_disability, disability_needs
                FROM demographics
                WHERE user_id = ?
                """,
                (user_data['id'],)  # Use internal id for foreign key
            )
            demo_row = cursor.fetchone()
            
            if demo_row:
                user_data['demographics'] = dict(demo_row)
            else:
                user_data['demographics'] = {}
            
            # Get travel preferences
            cursor.execute(
                """
                SELECT diet_preference, language_preferences
                FROM travel_preferences
                WHERE user_id = ?
                """,
                (user_data['id'],)
            )
            pref_row = cursor.fetchone()
            
            if pref_row:
                user_data['travel_preferences'] = dict(pref_row)
            else:
                user_data['travel_preferences'] = {}
            
            return user_data
            
        finally:
            conn.close()
    
    def to_user_profile(self, user_id: str, user_data: Optional[dict] = None) -> Optional[UserProfile]:
        """
        Convert database user data to UserProfile object
        
        Args:
            user_id: User ID
            user_data: Optional pre-fetched user data (if None, will fetch from DB)
            
        Returns:
            UserProfile object or None if user not found
        """
        if user_data is None:
            user_data = self.get_user_from_db(user_id)
        
        if not user_data:
            return None
        
        # Extract disability needs from demographics
        disability_needs = []
        if user_data.get('demographics') and user_data['demographics'].get('disability_needs'):
            try:
                disability_needs = json.loads(user_data['demographics']['disability_needs'])
            except:
                disability_needs = []
        
        # Extract dietary preferences from travel_preferences
        dietary_preferences = []
        if user_data.get('travel_preferences'):
            diet_pref = user_data['travel_preferences'].get('diet_preference')
            if diet_pref and diet_pref.lower() not in ['none', 'null', '']:
                # Parse comma-separated diet preferences
                if ',' in diet_pref:
                    dietary_preferences = [p.strip().lower() for p in diet_pref.split(',')]
                else:
                    dietary_preferences = [diet_pref.strip().lower()]
        
        # Note: budget and other fields removed from user_profiles table
        # They will come from the prompt or be inferred
        
        # Use external user_id if available, otherwise use internal id
        external_user_id = user_data.get('user_id') or str(user_data['id'])
        
        return UserProfile(
            user_id=external_user_id,  # Use external user_id (e.g., "Kartik7")
            name=user_data['name'],
            email=user_data['email'],
            phone_number=user_data.get('phone_number'),
            date_of_birth=user_data.get('date_of_birth'),
            budget=None,  # Budget not stored in database, will be set from prompt or user input
            dietary_preferences=dietary_preferences,
            disability_needs=disability_needs
        )
    
    def get_user_context_for_agents(self, user_id: str) -> dict:
        """
        Get user context data to enhance agent prompts
        This includes data that should influence search but isn't in UserProfile
        
        Returns:
            Dictionary with additional context (home_city, occupation, etc.)
        """
        user_data = self.get_user_from_db(user_id)
        if not user_data:
            return {}
        
        context = {
            'home_city': user_data.get('home_city'),
            'country_of_residence': user_data.get('country_of_residence'),
            'occupation': user_data.get('demographics', {}).get('occupation'),
            'gender': user_data.get('demographics', {}).get('gender'),
            'veteran_status': user_data.get('demographics', {}).get('veteran_status'),
            'language_preferences': []
        }
        
        # Extract language preferences
        if user_data.get('travel_preferences') and user_data['travel_preferences'].get('language_preferences'):
            try:
                context['language_preferences'] = json.loads(
                    user_data['travel_preferences']['language_preferences']
                )
            except:
                pass
        
        return context

