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

from typing import List, Dict
from google.cloud import bigquery
import vertexai
from vertexai.language_models import TextGenerationModel
from ..models.embeddings import EmbeddingGenerator


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
    """Core RAG system for Husqvarna 701 technical support."""
    
    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        dataset_id: str = "husqvarna_rag_dataset",
        table_id: str = "document_chunks",
        max_chunks: int = 5
    ):
        """Initialize the RAG system.
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
            dataset_id: BigQuery dataset ID
            table_id: BigQuery table ID
            max_chunks: Maximum number of chunks to retrieve
        """
        self.project_id = project_id
        self.location = location
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.max_chunks = max_chunks
        
        # Initialize clients
        self.bq_client = bigquery.Client()
        vertexai.init(project=project_id, location=location)
        self.embedding_generator = EmbeddingGenerator(project_id, location)
        self.llm = TextGenerationModel.from_pretrained("gemini-1.0-pro")
    
    def query(
        self,
        query: str,
        skill_level: str = "intermediate"
    ) -> str:
        """Process a user query.
        
        Args:
            query: User's question
            skill_level: User's skill level (beginner/intermediate/expert)
            
        Returns:
            Generated response
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embeddings([query])[0]
        
        # Retrieve relevant chunks
        chunks = self._retrieve_chunks(query_embedding)
        
        # Generate response
        response = self._generate_response(query, chunks, skill_level)
        
        return response
    
    def _retrieve_chunks(self, query_embedding: List[float]) -> List[Dict]:
        """Retrieve relevant chunks using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            
        Returns:
            List of relevant chunks
        """
        # Construct similarity query
        embedding_str = str(query_embedding)
        query = f"""
        SELECT
            chunk_id,
            content,
            source,
            page_number,
            safety_level,
            (
                SELECT cosine_similarity(embedding, {embedding_str})
            ) as similarity
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        ORDER BY similarity DESC
        LIMIT {self.max_chunks}
        """
        
        # Execute query
        query_job = self.bq_client.query(query)
        results = query_job.result()
        
        # Convert to list of dictionaries
        chunks = []
        for row in results:
            chunk = {
                'chunk_id': row.chunk_id,
                'content': row.content,
                'source': row.source,
                'page_number': row.page_number,
                'safety_level': row.safety_level,
                'similarity': row.similarity
            }
            chunks.append(chunk)
        
        return chunks
    
    def _generate_response(
        self,
        query: str,
        chunks: List[Dict],
        skill_level: str
    ) -> str:
        """Generate response using retrieved chunks.
        
        Args:
            query: User's question
            chunks: Retrieved relevant chunks
            skill_level: User's skill level
            
        Returns:
            Generated response
        """
        # Construct prompt
        context = "\n\n".join(
            [f"Source: {c['source']} (Page {c['page_number']})\n{c['content']}"
             for c in chunks]
        )
        
        prompt = f"""You are a Husqvarna 701 motorcycle technical expert.
        Answer the following question for a {skill_level} user.
        Use ONLY the provided context. If you cannot answer from the context,
        say so.
        
        Context:
        {context}
        
        Question: {query}
        
        Answer:"""
        
        # Check for safety warnings
        has_safety_warning = any(c['safety_level'] >= 2 for c in chunks)
        
        # Generate response
        response = self.llm.predict(prompt).text
        
        # Add safety warning if needed
        if has_safety_warning:
            response = (
                "⚠️ SAFETY WARNING: This procedure involves safety risks. "
                "Follow all safety guidelines carefully.\n\n"
            ) + response
        
        return response 