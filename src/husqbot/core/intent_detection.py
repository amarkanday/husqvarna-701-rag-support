"""
Intent detection for Husqvarna RAG Support System.
"""

import logging
import re

logger = logging.getLogger(__name__)


class IntentDetector:
    """Detects the intent of user queries."""
    
    def __init__(self):
        """Initialize the intent detector."""
        self.intent_patterns = {
            "maintenance": [
                r"check|inspect|verify|test|examine",
                r"oil|tire|chain|brake|fluid|filter",
                r"level|pressure|tension|condition",
                r"how often|when to|service interval"
            ],
            "troubleshooting": [
                r"problem|issue|fault|error|won't|doesn't|not working",
                r"start|run|idle|overheat|stall|rough",
                r"what's wrong|what should I do|why",
                r"diagnose|fix|repair|solve"
            ],
            "specifications": [
                r"spec|specification|capacity|size|dimension",
                r"pressure|temperature|torque|clearance",
                r"what is|how much|how many",
                r"weight|volume|measurement"
            ],
            "procedure": [
                r"how to|procedure|steps|instructions",
                r"replace|install|remove|adjust|change",
                r"do I|can I|should I",
                r"process|method|technique"
            ],
            "safety": [
                r"safety|danger|warning|caution|risk",
                r"safe|unsafe|hazard|precaution",
                r"what if|is it safe|should I worry",
                r"emergency|critical|important"
            ]
        }
    
    async def detect_intent(self, query: str) -> str:
        """
        Detect the intent of a user query.
        
        Args:
            query: User's question
            
        Returns:
            Detected intent category
        """
        query_lower = query.lower()
        
        # Count matches for each intent
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
            intent_scores[intent] = score
        
        # Return the intent with the highest score
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            if intent_scores[best_intent] > 0:
                return best_intent
        
        # Default to general if no clear intent
        return "general"
    
    def get_intent_confidence(self, query: str, intent: str) -> float:
        """
        Get confidence score for detected intent.
        
        Args:
            query: User's question
            intent: Detected intent
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        query_lower = query.lower()
        patterns = self.intent_patterns.get(intent, [])
        
        if not patterns:
            return 0.0
        
        matches = 0
        for pattern in patterns:
            if re.search(pattern, query_lower):
                matches += 1
        
        return min(matches / len(patterns), 1.0) 