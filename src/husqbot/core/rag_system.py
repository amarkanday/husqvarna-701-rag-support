"""
Main RAG system for Husqvarna 701 Enduro support.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..storage.bigquery_client import BigQueryClient
from ..storage.vector_search import VectorSearch
from ..data.document_processor import DocumentProcessor
from ..models.embedding_models import EmbeddingModel
from ..models.generation_models import GenerationModel
from .intent_detection import IntentDetector
from .safety_enhancement import SafetyEnhancer
from .response_generation import ResponseGenerator
from .config import RAGConfig

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result of a RAG query."""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    safety_level: int
    processing_time: float
    metadata: Dict[str, Any]


class HusqvarnaRAGSystem:
    """
    Main RAG system for Husqvarna 701 Enduro technical support.
    
    This system combines Owner's Manual and Repair Manual data to provide
    comprehensive, accurate answers to motorcycle maintenance and repair questions.
    """
    
    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        config: Optional[RAGConfig] = None
    ):
        """
        Initialize the RAG system.
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud location
            config: Configuration object
        """
        self.project_id = project_id
        self.location = location
        self.config = config or RAGConfig()
        
        # Initialize components
        self.bigquery_client = BigQueryClient(project_id, location)
        self.vector_search = VectorSearch(self.bigquery_client)
        self.document_processor = DocumentProcessor()
        self.embedding_model = EmbeddingModel(self.config.embedding_model)
        self.generation_model = GenerationModel(self.config.generation_model)
        self.intent_detector = IntentDetector()
        self.safety_enhancer = SafetyEnhancer()
        self.response_generator = ResponseGenerator(self.generation_model)
        
        logger.info(f"Initialized Husqvarna RAG System for project {project_id}")
    
    async def setup_complete_system(self) -> None:
        """
        Setup the complete system including BigQuery resources and data import.
        """
        logger.info("Setting up complete RAG system...")
        
        # Create BigQuery resources
        await self.bigquery_client.create_dataset_if_not_exists()
        await self.bigquery_client.create_tables_if_not_exists()
        
        # Import and process manuals
        await self._import_manuals()
        
        logger.info("RAG system setup complete")
    
    async def _import_manuals(self) -> None:
        """Import and process Husqvarna manuals."""
        logger.info("Importing Husqvarna manuals...")
        
        # Process Owner's Manual
        owners_manual_chunks = await self.document_processor.process_manual(
            "data/manuals/owners_manual.pdf",
            manual_type="owners"
        )
        
        # Process Repair Manual
        repair_manual_chunks = await self.document_processor.process_manual(
            "data/manuals/repair_manual.pdf",
            manual_type="repair"
        )
        
        # Generate embeddings
        all_chunks = owners_manual_chunks + repair_manual_chunks
        embeddings = await self.embedding_model.generate_embeddings(all_chunks)
        
        # Store in BigQuery
        await self.bigquery_client.insert_chunks_with_embeddings(
            all_chunks, embeddings
        )
        
        logger.info(f"Imported {len(all_chunks)} chunks with embeddings")
    
    async def query_system(
        self,
        query: str,
        user_skill_level: str = "intermediate",
        max_chunks: int = 5,
        **kwargs
    ) -> QueryResult:
        """
        Query the RAG system for technical support.
        
        Args:
            query: User's question
            user_skill_level: User's skill level (beginner, intermediate, expert)
            max_chunks: Maximum number of chunks to retrieve
            **kwargs: Additional configuration options
            
        Returns:
            QueryResult with answer and metadata
        """
        import time
        start_time = time.time()
        
        try:
            # Detect intent and safety level
            intent = await self.intent_detector.detect_intent(query)
            safety_level = await self.safety_enhancer.assess_safety_level(query)
            
            # Generate query embedding
            query_embedding = await self.embedding_model.generate_embedding(query)
            
            # Search for relevant chunks
            chunks = await self.vector_search.search_similar_chunks(
                query_embedding,
                max_results=max_chunks,
                safety_level=safety_level
            )
            
            # Generate response
            context = self._build_context(chunks, intent, user_skill_level)
            response = await self.response_generator.generate_response(
                query, context, user_skill_level, **kwargs
            )
            
            # Enhance with safety warnings
            enhanced_response = await self.safety_enhancer.enhance_response(
                response, safety_level, chunks
            )
            
            processing_time = time.time() - start_time
            
            return QueryResult(
                answer=enhanced_response,
                sources=[chunk.to_dict() for chunk in chunks],
                confidence=self._calculate_confidence(chunks),
                safety_level=safety_level,
                processing_time=processing_time,
                metadata={
                    "intent": intent,
                    "user_skill_level": user_skill_level,
                    "chunks_retrieved": len(chunks)
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise
    
    def _build_context(
        self,
        chunks: List[Any],
        intent: str,
        user_skill_level: str
    ) -> str:
        """Build context from retrieved chunks."""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"Source {i} ({chunk.manual_type}, {chunk.section}):\n{chunk.content}\n"
            )
        
        context = "\n".join(context_parts)
        
        # Add intent and skill level context
        context += f"\nQuery Intent: {intent}\nUser Skill Level: {user_skill_level}"
        
        return context
    
    def _calculate_confidence(self, chunks: List[Any]) -> float:
        """Calculate confidence score based on chunk relevance."""
        if not chunks:
            return 0.0
        
        # Simple confidence calculation based on chunk scores
        scores = [chunk.similarity_score for chunk in chunks]
        return sum(scores) / len(scores)
    
    async def batch_query(
        self,
        queries: List[str],
        user_skill_level: str = "intermediate"
    ) -> List[QueryResult]:
        """
        Process multiple queries in batch.
        
        Args:
            queries: List of queries to process
            user_skill_level: User's skill level
            
        Returns:
            List of QueryResult objects
        """
        tasks = [
            self.query_system(query, user_skill_level)
            for query in queries
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics and health information."""
        try:
            chunk_count = await self.bigquery_client.get_chunk_count()
            cache_stats = await self.vector_search.get_cache_stats()
            
            return {
                "total_chunks": chunk_count,
                "cache_hit_rate": cache_stats.get("hit_rate", 0.0),
                "system_status": "healthy",
                "last_updated": cache_stats.get("last_updated")
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {"system_status": "error", "error": str(e)} 