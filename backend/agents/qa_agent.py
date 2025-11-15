"""
QA Agent - Answers questions about the itinerary
Uses LLM to provide natural language responses about trip details
"""

from typing import Dict, Any, Optional
from shared.types import TripPlan


class QAAgent:
    """Agent that answers questions about the itinerary"""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    async def initialize(self):
        """Initialize the agent"""
        pass
    
    async def answer_question(self, question: str, itinerary: TripPlan) -> str:
        """
        Answer a question about the itinerary
        
        Args:
            question: User's question
            itinerary: The current trip plan
            
        Returns:
            Natural language answer
        """
        question_lower = question.lower()
        
        # Extract information from itinerary
        info = self._extract_itinerary_info(itinerary)
        
        # Answer based on question type
        if any(word in question_lower for word in ["carbon", "emission", "co2", "environment", "green"]):
            return self._answer_carbon_question(question, info)
        elif any(word in question_lower for word in ["budget", "cost", "price", "expensive", "cheap", "money"]):
            return self._answer_budget_question(question, info)
        elif any(word in question_lower for word in ["accommodation", "hotel", "stay", "lodging"]):
            return self._answer_accommodation_question(question, info)
        elif any(word in question_lower for word in ["transport", "flight", "train", "bus", "travel", "how to get"]):
            return self._answer_transportation_question(question, info)
        elif any(word in question_lower for word in ["restaurant", "food", "meal", "dining", "eat"]):
            return self._answer_restaurant_question(question, info)
        elif any(word in question_lower for word in ["activity", "experience", "thing to do", "attraction"]):
            return self._answer_experience_question(question, info)
        elif any(word in question_lower for word in ["day", "schedule", "itinerary", "plan", "what happens"]):
            return self._answer_schedule_question(question, info)
        else:
            return self._answer_general_question(question, info)
    
    def _extract_itinerary_info(self, itinerary: TripPlan) -> Dict[str, Any]:
        """Extract key information from itinerary"""
        info = {
            "destination": itinerary.request.destination,
            "duration": itinerary.request.duration_days,
            "travelers": itinerary.request.travelers,
            "accommodation": None,
            "transportation": [],
            "restaurants": [],
            "experiences": [],
            "budget": itinerary.budget,
            "itinerary_days": []
        }
        
        if itinerary.selected_accommodation:
            acc = itinerary.selected_accommodation
            info["accommodation"] = {
                "name": acc.title,
                "address": acc.address,
                "price_per_night": acc.price_per_night,
                "total_price": acc.total_price,
                "amenities": acc.amenities
            }
        
        if itinerary.transportation:
            for trans in itinerary.transportation[:3]:
                info["transportation"].append({
                    "type": trans.type,
                    "origin": trans.origin,
                    "destination": trans.destination,
                    "provider": trans.provider,
                    "price": trans.price,
                    "duration": trans.duration_minutes,
                    "carbon": trans.carbon_emissions_kg
                })
        
        if itinerary.restaurants:
            for rest in itinerary.restaurants[:5]:
                info["restaurants"].append({
                    "name": rest.name,
                    "cuisine": rest.cuisine_type,
                    "address": rest.address,
                    "price_range": rest.price_range
                })
        
        if itinerary.experiences:
            for exp in itinerary.experiences[:5]:
                info["experiences"].append({
                    "name": exp.name,
                    "category": exp.category,
                    "price": exp.price,
                    "duration": exp.duration_hours
                })
        
        for day in itinerary.itinerary:
            day_info = {
                "day": day.day,
                "date": day.date.strftime("%B %d, %Y"),
                "activities": len(day.activities),
                "meals": len(day.meals)
            }
            info["itinerary_days"].append(day_info)
        
        return info
    
    def _answer_carbon_question(self, question: str, info: Dict[str, Any]) -> str:
        """Answer questions about carbon emissions"""
        if not info["transportation"]:
            return "I don't have carbon emission information for the transportation options in your itinerary."
        
        total_carbon = sum(t.get("carbon", 0) or 0 for t in info["transportation"])
        top_trans = info["transportation"][0]
        
        response = f"🌱 **Carbon Emissions:**\n\n"
        response += f"Your main transportation ({top_trans['type']} from {top_trans['origin']} to {top_trans['destination']}) "
        response += f"produces approximately {top_trans.get('carbon', 0):.0f} kg of CO₂.\n\n"
        
        if total_carbon > 0:
            response += f"Total carbon footprint for transportation: ~{total_carbon:.0f} kg CO₂.\n\n"
        
        # Add context
        if top_trans.get('carbon', 0) > 2000:
            response += "💡 **Tip:** This is a long-distance journey. Consider offsetting your carbon footprint or choosing more eco-friendly options for future trips."
        elif top_trans.get('carbon', 0) < 100:
            response += "✅ This is a relatively low-carbon travel option!"
        
        return response
    
    def _answer_budget_question(self, question: str, info: Dict[str, Any]) -> str:
        """Answer questions about budget"""
        budget = info["budget"]
        
        response = f"💰 **Budget Breakdown:**\n\n"
        response += f"**Total Cost:** ${budget.total:.2f}\n\n"
        response += f"Breakdown:\n"
        response += f"  • Accommodation: ${budget.accommodation:.2f}\n"
        response += f"  • Transportation: ${budget.transportation:.2f}\n"
        response += f"  • Experiences: ${budget.experiences:.2f}\n"
        response += f"  • Meals: ${budget.meals:.2f}\n"
        response += f"  • Miscellaneous: ${budget.miscellaneous:.2f}\n\n"
        
        if info.get("accommodation"):
            response += f"**Accommodation:** {info['accommodation']['name']} - ${info['accommodation']['price_per_night']:.2f}/night\n"
        
        if info["transportation"]:
            top_trans = info["transportation"][0]
            response += f"**Transportation:** {top_trans['type']} - ${top_trans['price']:.2f}\n"
        
        return response
    
    def _answer_accommodation_question(self, question: str, info: Dict[str, Any]) -> str:
        """Answer questions about accommodation"""
        if not info["accommodation"]:
            return "I don't have accommodation information in your itinerary."
        
        acc = info["accommodation"]
        response = f"🏨 **Accommodation:**\n\n"
        response += f"**{acc['name']}**\n"
        response += f"📍 {acc['address']}\n"
        response += f"💰 ${acc['price_per_night']:.2f} per night (Total: ${acc['total_price']:.2f})\n"
        
        if acc.get("amenities"):
            response += f"\n**Amenities:** {', '.join(acc['amenities'][:5])}\n"
        
        return response
    
    def _answer_transportation_question(self, question: str, info: Dict[str, Any]) -> str:
        """Answer questions about transportation"""
        if not info["transportation"]:
            return "I don't have transportation information in your itinerary."
        
        response = f"🚗 **Transportation Options:**\n\n"
        
        for i, trans in enumerate(info["transportation"][:3], 1):
            response += f"**Option {i}:**\n"
            response += f"  Type: {trans['type'].upper()}\n"
            response += f"  Route: {trans['origin']} → {trans['destination']}\n"
            response += f"  Provider: {trans['provider']}\n"
            if trans.get('duration'):
                hours = trans['duration'] // 60
                minutes = trans['duration'] % 60
                response += f"  Duration: {hours}h {minutes}m\n"
            response += f"  Price: ${trans['price']:.2f}\n"
            if trans.get('carbon'):
                response += f"  Carbon: {trans['carbon']:.0f} kg CO₂\n"
            response += "\n"
        
        return response
    
    def _answer_restaurant_question(self, question: str, info: Dict[str, Any]) -> str:
        """Answer questions about restaurants"""
        if not info["restaurants"]:
            return "I don't have restaurant information in your itinerary."
        
        response = f"🍽️  **Restaurants in Your Itinerary:**\n\n"
        
        for i, rest in enumerate(info["restaurants"], 1):
            response += f"**{i}. {rest['name']}**\n"
            response += f"   Cuisine: {rest['cuisine']}\n"
            response += f"   Location: {rest['address']}\n"
            response += f"   Price Range: {rest['price_range']}\n\n"
        
        return response
    
    def _answer_experience_question(self, question: str, info: Dict[str, Any]) -> str:
        """Answer questions about experiences"""
        if not info["experiences"]:
            return "I don't have specific experience information in your itinerary, but you can explore local attractions and activities."
        
        response = f"🎯 **Experiences & Activities:**\n\n"
        
        for i, exp in enumerate(info["experiences"], 1):
            response += f"**{i}. {exp['name']}**\n"
            response += f"   Category: {exp['category']}\n"
            if exp.get('price'):
                response += f"   Price: ${exp['price']:.2f}\n"
            if exp.get('duration'):
                response += f"   Duration: {exp['duration']} hours\n"
            response += "\n"
        
        return response
    
    def _answer_schedule_question(self, question: str, info: Dict[str, Any]) -> str:
        """Answer questions about the schedule"""
        response = f"📅 **Trip Schedule:**\n\n"
        response += f"**Destination:** {info['destination']}\n"
        response += f"**Duration:** {info['duration']} days\n"
        response += f"**Travelers:** {info['travelers']}\n\n"
        
        response += f"**Daily Breakdown:**\n"
        for day_info in info["itinerary_days"]:
            response += f"  Day {day_info['day']} ({day_info['date']}): "
            response += f"{day_info['activities']} activities, {day_info['meals']} meals\n"
        
        return response
    
    def _answer_general_question(self, question: str, info: Dict[str, Any]) -> str:
        """Answer general questions"""
        response = f"📋 **Your Trip Summary:**\n\n"
        response += f"**Destination:** {info['destination']}\n"
        response += f"**Duration:** {info['duration']} days\n"
        response += f"**Travelers:** {info['travelers']}\n"
        response += f"**Total Budget:** ${info['budget'].total:.2f}\n\n"
        
        if info["accommodation"]:
            response += f"**Accommodation:** {info['accommodation']['name']}\n"
        
        if info["transportation"]:
            top_trans = info["transportation"][0]
            response += f"**Transportation:** {top_trans['type']} from {top_trans['origin']} to {top_trans['destination']}\n"
        
        response += f"\n**Restaurants:** {len(info['restaurants'])} options\n"
        response += f"**Experiences:** {len(info['experiences'])} options\n"
        
        return response

