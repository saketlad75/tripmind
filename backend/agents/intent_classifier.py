"""
Intent Classifier - Classifies user follow-up prompts into categories
"""

from typing import Dict, Any
import re


class IntentClassifier:
    """Classifies user intent from follow-up prompts"""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    def classify(self, prompt: str) -> Dict[str, Any]:
        """
        Classify user intent from prompt
        
        Returns:
            {
                "intent": "modify" | "query" | "chat",
                "category": "accommodation" | "transportation" | "restaurant" | "experience" | "budget" | "general",
                "action": "add" | "change" | "remove" | "replace" | "find" | "info" | "chat",
                "confidence": float
            }
        """
        prompt_lower = prompt.lower()
        
        # Intent patterns
        modify_keywords = [
            "add", "change", "modify", "update", "replace", "remove", "delete",
            "switch", "edit", "make it", "make them"
        ]
        
        query_keywords = [
            "what", "which", "where", "when", "how", "why", "tell me", "explain",
            "describe", "information", "details", "about", "more about", "is the",
            "are the", "can you tell", "do you know"
        ]
        
        chat_keywords = [
            "hello", "hi", "hey", "thanks", "thank you", "ok", "okay", "sure", "yes", "no"
        ]
        
        # Determine primary intent - prioritize query keywords
        # Check for query first (questions should be queries, not modifications)
        has_query = any(keyword in prompt_lower for keyword in query_keywords)
        
        # Check for modify keywords (but only if not a question)
        has_modify = any(keyword in prompt_lower for keyword in modify_keywords) and not has_query
        
        # Check for chat keywords (greetings, etc.)
        has_chat = any(keyword in prompt_lower for keyword in chat_keywords) and not has_query
        
        # Category detection
        category = "general"
        if any(word in prompt_lower for word in ["hotel", "accommodation", "stay", "lodging", "place to stay"]):
            category = "accommodation"
        elif any(word in prompt_lower for word in ["flight", "train", "bus", "car", "transport", "travel", "transportation", "ride"]):
            category = "transportation"
        elif any(word in prompt_lower for word in ["restaurant", "food", "meal", "dining", "eat", "cafe", "lunch", "dinner", "breakfast"]):
            category = "restaurant"
        elif any(word in prompt_lower for word in ["activity", "experience", "thing to do", "attraction", "tour", "sightseeing"]):
            category = "experience"
        elif any(word in prompt_lower for word in ["budget", "cost", "price", "expensive", "cheap", "affordable", "money"]):
            category = "budget"
        
        # Action detection
        action = "info"
        if any(word in prompt_lower for word in ["add", "more", "additional", "extra"]):
            action = "add"
        elif any(word in prompt_lower for word in ["change", "modify", "update", "switch", "replace"]):
            action = "change"
        elif any(word in prompt_lower for word in ["remove", "delete", "cancel"]):
            action = "remove"
        elif any(word in prompt_lower for word in ["find", "get", "show", "give"]):
            action = "find"
        elif has_query:
            action = "info"
        elif has_chat:
            action = "chat"
        
        # Determine final intent - prioritize queries
        if has_query:
            intent = "query"
            confidence = 0.9
        elif has_modify:
            intent = "modify"
            confidence = 0.8
        elif has_chat:
            intent = "chat"
            confidence = 0.9
        else:
            # Default to query if unclear (questions are more common)
            intent = "query"
            confidence = 0.5
        
        return {
            "intent": intent,
            "category": category,
            "action": action,
            "confidence": confidence,
            "original_prompt": prompt
        }

