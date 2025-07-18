"""
Safety enhancement for Husqvarna RAG Support System.
"""

import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SafetyEnhancer:
    """Enhances responses with safety warnings and prioritizes safety information."""
    
    def __init__(self):
        """Initialize the safety enhancer."""
        self.safety_keywords = [
            "danger", "warning", "caution", "risk", "hazard",
            "safety", "critical", "emergency", "poison", "toxic",
            "scalding", "burn", "injury", "accident", "death"
        ]
        
        self.safety_patterns = [
            r"danger of [^.]*",
            r"warning[^.]*",
            r"caution[^.]*",
            r"risk of [^.]*",
            r"hazard[^.]*",
            r"safety[^.]*",
            r"critical[^.]*",
            r"emergency[^.]*"
        ]
    
    async def assess_safety_level(self, query: str) -> int:
        """
        Assess the safety level of a query.
        
        Args:
            query: User's question
            
        Returns:
            Safety level (0-3, where 3 is highest safety concern)
        """
        query_lower = query.lower()
        
        # Count safety keywords
        safety_count = sum(
            1 for keyword in self.safety_keywords if keyword in query_lower
        )
        
        # Check for safety patterns
        pattern_matches = sum(
            1 for pattern in self.safety_patterns if re.search(pattern, query_lower)
        )
        
        # Calculate safety level
        if safety_count >= 3 or pattern_matches >= 2:
            return 3  # High safety concern
        elif safety_count >= 2 or pattern_matches >= 1:
            return 2  # Medium safety concern
        elif safety_count >= 1:
            return 1  # Low safety concern
        else:
            return 0  # No safety concern
    
    async def enhance_response(self, response: str, safety_level: int, chunks: List[Dict[str, Any]]) -> str:
        """
        Enhance response with safety warnings and prioritization.
        
        Args:
            response: Original response
            safety_level: Assessed safety level
            chunks: Retrieved chunks
            
        Returns:
            Enhanced response with safety emphasis
        """
        if safety_level == 0:
            return response
        
        # Extract safety information from chunks
        safety_info = self._extract_safety_info(chunks)
        
        if not safety_info:
            return response
        
        # Enhance response based on safety level
        enhanced_response = response
        
        if safety_level >= 2:
            # Add prominent safety warning
            safety_warning = self._create_safety_warning(safety_info, safety_level)
            enhanced_response = f"{safety_warning}\n\n{response}"
        
        # Emphasize safety keywords in the response
        enhanced_response = self._emphasize_safety_keywords(enhanced_response)
        
        return enhanced_response
    
    def _extract_safety_info(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """Extract safety-related information from chunks."""
        safety_info = []
        
        for chunk in chunks:
            content = chunk.get('content', '').lower()
            
            # Check for safety keywords
            for keyword in self.safety_keywords:
                if keyword in content:
                    # Extract the sentence containing the safety keyword
                    sentences = re.split(r'[.!?]', chunk.get('content', ''))
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            safety_info.append(sentence.strip())
                            break
        
        return list(set(safety_info))  # Remove duplicates
    
    def _create_safety_warning(self, safety_info: List[str], safety_level: int) -> str:
        """Create a safety warning based on safety information."""
        if safety_level >= 3:
            prefix = "🚨 CRITICAL SAFETY WARNING 🚨"
        else:
            prefix = "⚠️  SAFETY WARNING ⚠️"
        
        warning_text = f"{prefix}\n\n"
        
        # Include the most relevant safety information
        for info in safety_info[:2]:  # Limit to 2 most relevant
            warning_text += f"• {info}\n"
        
        warning_text += "\nPlease read and follow all safety instructions carefully."
        
        return warning_text
    
    def _emphasize_safety_keywords(self, text: str) -> str:
        """Emphasize safety keywords in the text."""
        emphasized_text = text
        
        for keyword in self.safety_keywords:
            # Use case-insensitive replacement
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            emphasized_text = pattern.sub(f"**{keyword.upper()}**", emphasized_text)
        
        return emphasized_text
    
    def is_safety_critical(self, content: str) -> bool:
        """
        Check if content contains critical safety information.
        
        Args:
            content: Content to check
            
        Returns:
            True if content contains critical safety information
        """
        content_lower = content.lower()
        
        critical_keywords = ["death", "fatal", "critical", "emergency", "poison", "toxic"]
        critical_patterns = [
            r"danger of [^.]*death",
            r"fatal[^.]*",
            r"critical[^.]*",
            r"emergency[^.]*"
        ]
        
        # Check for critical keywords
        if any(keyword in content_lower for keyword in critical_keywords):
            return True
        
        # Check for critical patterns
        if any(re.search(pattern, content_lower) for pattern in critical_patterns):
            return True
        
        return False 