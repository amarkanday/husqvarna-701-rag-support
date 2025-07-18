"""
Vector search functionality for Husqvarna RAG Support System.
"""

import logging
from typing import List, Dict, Any, Optional
from .bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class VectorSearch:
    """Handles vector similarity search operations."""
    
    def __init__(self, bigquery_client: BigQueryClient):
        """
        Initialize vector search.
        
        Args:
            bigquery_client: BigQuery client instance
        """
        self.bigquery_client = bigquery_client
        self.cache = {}  # Simple in-memory cache
        
        logger.info("Initialized vector search")
    
    async def search_similar_chunks(
        self,
        query_embedding: List[float],
        max_results: int = 5,
        safety_level: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            max_results: Maximum number of results
            safety_level: Optional safety level filter
            **kwargs: Additional search parameters
            
        Returns:
            List of similar chunks with metadata
        """
        try:
            chunks = await self.bigquery_client.search_similar_chunks(
                query_embedding=query_embedding,
                max_results=max_results,
                safety_level=safety_level
            )
            
            # Add cache entry
            cache_key = self._create_cache_key(query_embedding, max_results, safety_level)
            self.cache[cache_key] = {
                "chunks": chunks,
                "timestamp": self._get_timestamp()
            }
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            raise
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics dictionary
        """
        if not self.cache:
            return {
                "hit_rate": 0.0,
                "total_entries": 0,
                "last_updated": None
            }
        
        total_entries = len(self.cache)
        # Simple cache hit rate estimation
        hit_rate = min(0.75, total_entries / 100)  # Placeholder
        
        return {
            "hit_rate": hit_rate,
            "total_entries": total_entries,
            "last_updated": self._get_timestamp()
        }
    
    def _create_cache_key(
        self, 
        embedding: List[float], 
        max_results: int, 
        safety_level: Optional[int]
    ) -> str:
        """Create a cache key for the search parameters."""
        # Use a simple hash of the first few embedding values
        embedding_hash = hash(tuple(embedding[:10]))
        return f"{embedding_hash}_{max_results}_{safety_level}"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def clear_cache(self) -> None:
        """Clear the search cache."""
        self.cache.clear()
        logger.info("Vector search cache cleared") 