"""
RouteAnalyzerAgent - Intelligently determines the best transportation mode
based on origin and destination geography
"""

from typing import Dict, Any, Optional, Tuple
from agents.gemini_search_agent import GeminiSearchAgent
import json
import re


class RouteAnalyzerAgent:
    """Agent that analyzes routes to determine the best transportation mode"""
    
    def __init__(self):
        self.gemini_search = GeminiSearchAgent()
    
    async def initialize(self):
        """Initialize the agent"""
        await self.gemini_search.initialize()
    
    async def analyze_route(
        self,
        origin: str,
        destination: str
    ) -> Dict[str, Any]:
        """
        Analyze the route and determine the best transportation mode
        
        Args:
            origin: Origin location
            destination: Destination location
            
        Returns:
            Dictionary with recommended mode and reasoning
        """
        prompt = f"""Analyze the transportation route from {origin} to {destination}.

Determine the BEST and MOST PRACTICAL transportation mode for this route. Consider:
1. Geography: Is it international? Same country? Same continent?
2. Distance: Short distance (under 50km)? Medium (50-500km)? Long (over 500km)?
3. Accessibility: Are there direct train connections? Is it accessible by land?
4. Practicality: What is the most common and practical way to travel this route?
5. Context: Is it an airport transfer? Local transportation? Long-distance travel?

Possible modes:
- "flight" - For international travel, long distances (over 1000km), or when no direct land connection exists
- "train" - For European routes, same country, medium distances (100-1000km), or when high-speed rail is available
- "bus" - For budget options, short-medium distances (50-500km), same country/region, when user explicitly wants budget travel
- "car" or "cab" - For very short distances (under 50km), airport transfers, or local transportation between specific addresses

Return your analysis as JSON:
{{
  "recommended_mode": "flight" or "train" or "car" or "bus",
  "reasoning": "Brief explanation why this mode is best",
  "alternative_modes": ["list", "of", "alternatives", "if", "any"],
  "distance_category": "short" or "medium" or "long",
  "is_international": true or false,
  "is_same_continent": true or false
}}

Be intelligent and practical. For example:
- New York to Zurich = flight (international, across ocean)
- London to Paris = train (Eurostar exists, same continent)
- Paris to Berlin = train (European high-speed rail)
- Los Angeles to Tokyo = flight (international, across ocean)
- New York to Boston = train or bus (same country, short distance)
- Airport to city center = car/cab (very short distance, airport transfer)
- Airport to hotel = car/cab (local transportation, specific addresses)"""

        try:
            result = await self.gemini_search.search(
                custom_prompt=prompt,
                format_json=True
            )
            
            # Parse the result
            analysis = self._parse_analysis(result["raw_output"], origin, destination)
            return analysis
            
        except Exception as e:
            # Fallback: use simple heuristics
            return self._fallback_analysis(origin, destination)
    
    def _parse_analysis(self, output: str, origin: str, destination: str) -> Dict[str, Any]:
        """Parse the analysis from Gemini output"""
        # Try to extract JSON
        try:
            if "```json" in output:
                json_start = output.find("```json") + 7
                json_end = output.find("```", json_start)
                json_str = output[json_start:json_end].strip()
                data = json.loads(json_str)
                return data
            else:
                # Try to find JSON in the text
                json_match = re.search(r'\{[^{}]*"recommended_mode"[^{}]*\}', output, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                    return data
        except (json.JSONDecodeError, ValueError, AttributeError):
            pass
        
        # Fallback analysis
        return self._fallback_analysis(origin, destination)
    
    def _fallback_analysis(self, origin: str, destination: str) -> Dict[str, Any]:
        """Fallback analysis using simple heuristics"""
        origin_lower = origin.lower()
        destination_lower = destination.lower()
        
        # Check if same country (simple heuristic)
        us_cities = ["new york", "los angeles", "chicago", "boston", "san francisco", "miami", "usa", "united states"]
        europe_cities = ["london", "paris", "berlin", "zurich", "rome", "madrid", "amsterdam", "france", "germany", "switzerland", "uk", "italy", "spain"]
        asia_cities = ["tokyo", "seoul", "beijing", "shanghai", "singapore", "bangkok", "japan", "china", "korea"]
        
        origin_is_us = any(city in origin_lower for city in us_cities)
        origin_is_europe = any(city in origin_lower for city in europe_cities)
        origin_is_asia = any(city in origin_lower for city in asia_cities)
        
        dest_is_us = any(city in destination_lower for city in us_cities)
        dest_is_europe = any(city in destination_lower for city in europe_cities)
        dest_is_asia = any(city in destination_lower for city in asia_cities)
        
        # Determine mode
        if origin_is_us and dest_is_europe:
            return {"recommended_mode": "flight", "reasoning": "International travel across Atlantic Ocean", "is_international": True}
        elif origin_is_us and dest_is_asia:
            return {"recommended_mode": "flight", "reasoning": "International travel across Pacific Ocean", "is_international": True}
        elif origin_is_europe and dest_is_europe:
            return {"recommended_mode": "train", "reasoning": "European cities with high-speed rail connections", "is_international": True, "is_same_continent": True}
        elif origin_is_us and dest_is_us:
            return {"recommended_mode": "flight", "reasoning": "Domestic US travel - flights are most practical", "is_international": False}
        else:
            # Default to flight for international, train for same continent
            return {"recommended_mode": "flight", "reasoning": "International travel", "is_international": True}

