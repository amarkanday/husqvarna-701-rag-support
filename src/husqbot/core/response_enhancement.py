"""
Response enhancement utilities for improved RAG quality.
"""

import logging
import re
from typing import List, Dict, Set, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class ResponseEnhancer:
    """Enhances RAG responses with advanced quality improvements."""
    
    def __init__(self):
        """Initialize the response enhancer."""
        self.technical_terms = {
            'oil': ['engine oil', 'transmission oil', 'oil level', 'oil change'],
            'brake': ['brake fluid', 'brake pads', 'brake system', 'brake lever'],
            'chain': ['drive chain', 'chain tension', 'chain lubrication'],
            'tire': ['tire pressure', 'tire tread', 'tire replacement'],
            'engine': ['engine temperature', 'engine performance', 'engine maintenance'],
            'cooling': ['coolant level', 'radiator', 'cooling system', 'overheating'],
            'electrical': ['battery', 'electrical system', 'wiring', 'fuses'],
            'suspension': ['front suspension', 'rear suspension', 'shock absorber'],
        }
        
        self.maintenance_keywords = [
            'service', 'maintenance', 'check', 'inspect', 'replace', 'adjust',
            'clean', 'lubricate', 'tighten', 'torque', 'interval'
        ]
        
        self.safety_indicators = [
            'warning', 'danger', 'caution', 'risk', 'safety', 'hazard',
            'injury', 'death', 'fire', 'explosion', 'toxic', 'hot'
        ]
    
    def expand_query(self, query: str) -> List[str]:
        """Expand a query with related terms for better retrieval.
        
        Args:
            query: Original user query
            
        Returns:
            List of expanded query variants
        """
        expanded_queries = [query]
        query_lower = query.lower()
        
        # Add technical variations
        for category, terms in self.technical_terms.items():
            if category in query_lower:
                for term in terms:
                    if term not in query_lower:
                        expanded_queries.append(f"{query} {term}")
        
        # Add maintenance context if not present
        if any(keyword in query_lower for keyword in self.maintenance_keywords):
            maintenance_context = "maintenance procedure service"
            if maintenance_context not in query_lower:
                expanded_queries.append(f"{query} {maintenance_context}")
        
        return expanded_queries[:3]  # Limit to avoid noise
    
    def rank_chunks_by_relevance(
        self, 
        chunks: List[Dict], 
        query: str
    ) -> List[Dict]:
        """Enhanced ranking of chunks based on multiple factors.
        
        Args:
            chunks: List of chunks with similarity scores
            query: Original query
            
        Returns:
            Re-ranked chunks
        """
        query_terms = set(query.lower().split())
        
        for chunk in chunks:
            content_lower = chunk['content'].lower()
            
            # Base score from similarity
            score = chunk['similarity']
            
            # Boost for exact query term matches
            exact_matches = sum(1 for term in query_terms if term in content_lower)
            score += exact_matches * 0.1
            
            # Boost for technical terms
            for term in self.maintenance_keywords:
                if term in content_lower:
                    score += 0.05
            
            # Boost for structured content (steps, lists)
            if self._has_structured_content(chunk['content']):
                score += 0.08
            
            # Boost for specific measurements/values
            if self._has_technical_data(chunk['content']):
                score += 0.06
            
            # Safety content gets priority boost
            safety_score = self._calculate_safety_relevance(chunk['content'], query)
            score += safety_score
            
            chunk['enhanced_score'] = score
        
        # Sort by enhanced score
        return sorted(chunks, key=lambda x: x['enhanced_score'], reverse=True)
    
    def _has_structured_content(self, content: str) -> bool:
        """Check if content has structured information (steps, lists)."""
        indicators = [
            r'\d+\.',  # Numbered lists
            r'[•\-\*]',  # Bullet points
            r'step \d+',  # Step indicators
            r'procedure:',  # Procedure headers
            r':\s*\n',  # Colon followed by newline (definitions)
        ]
        
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in indicators)
    
    def _has_technical_data(self, content: str) -> bool:
        """Check if content contains technical measurements or specifications."""
        patterns = [
            r'\d+\s*(mm|cm|m|in|ft)',  # Measurements
            r'\d+\s*(rpm|mph|km/h)',   # Speed/rotation
            r'\d+\s*(bar|psi|pa)',     # Pressure
            r'\d+\s*(°c|°f|celsius|fahrenheit)',  # Temperature
            r'\d+\s*(nm|ft-lb)',       # Torque
            r'\d+\s*(ml|l|oz|qt)',     # Volume
            r'\d+\s*(kg|lb|g)',        # Weight
            r'\d+\s*(v|volt|amp)',     # Electrical
        ]
        
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
    
    def _calculate_safety_relevance(self, content: str, query: str) -> float:
        """Calculate safety relevance boost for content."""
        content_lower = content.lower()
        query_lower = query.lower()
        
        safety_score = 0.0
        
        # If query mentions safety concerns, boost safety content
        if any(indicator in query_lower for indicator in self.safety_indicators):
            safety_count = sum(1 for indicator in self.safety_indicators 
                             if indicator in content_lower)
            safety_score += safety_count * 0.15
        
        return safety_score
    
    def validate_response_quality(self, response: str, query: str, chunks: List[Dict]) -> Dict:
        """Validate and score response quality.
        
        Args:
            response: Generated response
            query: Original query
            chunks: Source chunks
            
        Returns:
            Quality assessment dictionary
        """
        assessment = {
            'completeness_score': 0.0,
            'safety_score': 0.0,
            'technical_accuracy': 0.0,
            'structure_score': 0.0,
            'source_attribution': 0.0,
            'overall_score': 0.0,
            'issues': [],
            'suggestions': []
        }
        
        # Check completeness
        query_terms = set(query.lower().split())
        response_lower = response.lower()
        
        addressed_terms = sum(1 for term in query_terms if term in response_lower)
        assessment['completeness_score'] = addressed_terms / len(query_terms)
        
        # Check safety content
        safety_mentions = sum(1 for indicator in self.safety_indicators 
                            if indicator in response_lower)
        high_safety_chunks = [c for c in chunks if c['safety_level'] >= 3]
        
        if high_safety_chunks and safety_mentions == 0:
            assessment['issues'].append("High-safety content missing safety warnings")
            assessment['safety_score'] = 0.0
        else:
            assessment['safety_score'] = min(safety_mentions / max(len(high_safety_chunks), 1), 1.0)
        
        # Check technical accuracy (presence of specific data)
        has_tech_data = self._has_technical_data(response)
        assessment['technical_accuracy'] = 1.0 if has_tech_data else 0.5
        
        # Check structure
        has_structure = self._has_structured_content(response)
        assessment['structure_score'] = 1.0 if has_structure else 0.7
        
        # Check source attribution
        source_mentions = len(re.findall(r'page \d+|source:|manual', response_lower))
        assessment['source_attribution'] = min(source_mentions / 2, 1.0)
        
        # Calculate overall score
        weights = {
            'completeness_score': 0.3,
            'safety_score': 0.3,
            'technical_accuracy': 0.2,
            'structure_score': 0.1,
            'source_attribution': 0.1
        }
        
        assessment['overall_score'] = sum(
            assessment[key] * weight for key, weight in weights.items()
        )
        
        # Generate suggestions
        if assessment['completeness_score'] < 0.8:
            assessment['suggestions'].append("Address more query terms")
        if assessment['safety_score'] < 0.5:
            assessment['suggestions'].append("Include appropriate safety warnings")
        if assessment['technical_accuracy'] < 0.7:
            assessment['suggestions'].append("Add specific technical details")
        
        return assessment
    
    def enhance_chunk_context(self, chunks: List[Dict]) -> List[Dict]:
        """Add contextual information to chunks for better understanding.
        
        Args:
            chunks: List of chunks
            
        Returns:
            Enhanced chunks with context
        """
        enhanced_chunks = []
        
        for chunk in chunks:
            enhanced_chunk = chunk.copy()
            content = chunk['content']
            
            # Add content type classification
            enhanced_chunk['content_type'] = self._classify_content_type(content)
            
            # Add key entities
            enhanced_chunk['key_entities'] = self._extract_key_entities(content)
            
            # Add context summary
            enhanced_chunk['context_summary'] = self._generate_context_summary(content)
            
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def _classify_content_type(self, content: str) -> str:
        """Classify the type of content in a chunk."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['step', 'procedure', 'instruction']):
            return 'procedure'
        elif any(word in content_lower for word in ['warning', 'danger', 'caution']):
            return 'safety'
        elif self._has_technical_data(content):
            return 'specification'
        elif any(word in content_lower for word in ['check', 'inspect', 'service']):
            return 'maintenance'
        else:
            return 'general'
    
    def _extract_key_entities(self, content: str) -> List[str]:
        """Extract key technical entities from content."""
        entities = []
        
        # Extract measurements
        measurements = re.findall(r'\d+\s*(?:mm|cm|m|in|ft|bar|psi|rpm|°c|°f|nm|ml|l)', 
                                content, re.IGNORECASE)
        entities.extend(measurements)
        
        # Extract part names (capitalized words)
        parts = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        entities.extend(parts[:5])  # Limit to avoid noise
        
        return list(set(entities))
    
    def _generate_context_summary(self, content: str) -> str:
        """Generate a brief summary of chunk content."""
        # Extract first sentence or up to 100 characters
        sentences = re.split(r'[.!?]', content)
        if sentences and len(sentences[0]) > 10:
            return sentences[0].strip()[:100] + "..."
        else:
            return content[:100] + "..." if len(content) > 100 else content 