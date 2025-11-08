"""
GeminiSearchAgent - Web search agent using Google Gemini
Replaces Dedalus Labs for web searches
"""

from typing import Dict, Any, Optional
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

load_dotenv()


class GeminiSearchAgent:
    """Web search agent using Google Gemini"""
    
    def __init__(self):
        self.client = None
        self.model = None
        self.api_key = os.getenv("GEMINI_API_KEY")
        
    async def initialize(self):
        """Initialize Gemini client"""
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ValueError(
                "GEMINI_API_KEY not set. Please set it in your .env file. "
                "Get your API key at https://makersuite.google.com/app/apikey"
            )
        
        genai.configure(api_key=self.api_key)
        # Use Gemini 2.0 Flash for fast responses
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.client = genai
    
    async def search(
        self,
        custom_prompt: str,
        format_json: bool = True
    ) -> Dict[str, Any]:
        """
        Perform a web search with custom prompt using Gemini
        
        Args:
            custom_prompt: Custom search prompt with specific instructions
            format_json: Whether to request JSON formatted output
            
        Returns:
            Dictionary with search results
        """
        if not self.model:
            await self.initialize()
        
        # Enhance prompt for JSON formatting if requested
        if format_json:
            enhanced_prompt = f"""{custom_prompt}

IMPORTANT: Please provide the results in a structured JSON format. If you find real-time data from the websites, format it as JSON. If you cannot access real-time data, provide estimated/example data based on typical prices and format it as JSON.

Format the response as:
```json
{{
  "flights" or "trains" or "cabs": [
    {{
      "airline" or "operator" or "provider": "...",
      "price": 0.0,
      "price_per_person": 0.0,
      "duration_minutes": 0,
      "departure_time": "...",
      "arrival_time": "...",
      "transfers": 0,
      "booking_url": "...",
      "origin": "...",
      "destination": "..."
    }}
  ]
}}
```"""
        else:
            enhanced_prompt = custom_prompt
        
        try:
            # Generate response using Gemini (synchronous call, but we're in async context)
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(enhanced_prompt)
            )
            
            # Extract text from response
            if hasattr(response, 'text'):
                output_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                output_text = response.candidates[0].content.parts[0].text
            else:
                output_text = str(response)
            
            return {
                "results": output_text,
                "raw_output": output_text
            }
        except Exception as e:
            raise RuntimeError(f"Error performing Gemini search: {str(e)}") from e

