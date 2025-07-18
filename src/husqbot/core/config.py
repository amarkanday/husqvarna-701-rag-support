"""
Configuration for Husqvarna RAG Support System.
"""

from dataclasses import dataclass


@dataclass
class RAGConfig:
    """Configuration for the RAG system."""
    
    # Model configurations
    embedding_model: str = "textembedding-gecko@003"
    generation_model: str = "gemini-1.5-pro"
    
    # Generation parameters
    max_tokens: int = 2048
    temperature: float = 0.2
    
    # Retrieval parameters
    max_chunks: int = 5
    chunk_overlap: int = 200
    chunk_size: int = 1000
    
    # Database configurations
    dataset_id: str = "husqvarna_rag_dataset"
    table_id: str = "manual_chunks"
    
    # Cache configurations
    cache_ttl_hours: int = 24
    cache_max_size: int = 1000
    
    # Safety configurations
    min_safety_level: int = 1
    emphasize_warnings: bool = True
    
    # API configurations
    rate_limit: int = 100
    timeout: int = 30 