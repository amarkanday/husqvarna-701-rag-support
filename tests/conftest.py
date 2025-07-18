"""
Pytest configuration and fixtures for Husqvarna RAG Support System tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from src.husqbot.core.rag_system import HusqvarnaRAGSystem, QueryResult


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_bigquery_client():
    """Mock BigQuery client for testing."""
    client = Mock()
    client.create_dataset_if_not_exists = AsyncMock()
    client.create_tables_if_not_exists = AsyncMock()
    client.get_chunk_count = AsyncMock(return_value=1000)
    client.insert_chunks_with_embeddings = AsyncMock()
    return client


@pytest.fixture
def mock_vector_search():
    """Mock vector search for testing."""
    search = Mock()
    search.search_similar_chunks = AsyncMock()
    search.get_cache_stats = AsyncMock(return_value={
        "hit_rate": 0.75,
        "last_updated": "2024-01-01T00:00:00Z"
    })
    return search


@pytest.fixture
def mock_document_processor():
    """Mock document processor for testing."""
    processor = Mock()
    processor.process_manual = AsyncMock(return_value=[])
    return processor


@pytest.fixture
def mock_embedding_model():
    """Mock embedding model for testing."""
    model = Mock()
    model.generate_embedding = AsyncMock(return_value=[0.1] * 768)
    model.generate_embeddings = AsyncMock(return_value=[[0.1] * 768] * 10)
    return model


@pytest.fixture
def mock_generation_model():
    """Mock generation model for testing."""
    model = Mock()
    model.generate_response = AsyncMock(return_value="Test response")
    return model


@pytest.fixture
def mock_intent_detector():
    """Mock intent detector for testing."""
    detector = Mock()
    detector.detect_intent = AsyncMock(return_value="maintenance")
    return detector


@pytest.fixture
def mock_safety_enhancer():
    """Mock safety enhancer for testing."""
    enhancer = Mock()
    enhancer.assess_safety_level = AsyncMock(return_value=1)
    enhancer.enhance_response = AsyncMock(return_value="Enhanced test response")
    return enhancer


@pytest.fixture
def mock_response_generator():
    """Mock response generator for testing."""
    generator = Mock()
    generator.generate_response = AsyncMock(return_value="Generated response")
    return generator


@pytest.fixture
def sample_query_result():
    """Sample query result for testing."""
    return QueryResult(
        answer="Test answer",
        sources=[{"content": "Test source", "manual_type": "owners"}],
        confidence=0.85,
        safety_level=1,
        processing_time=1.5,
        metadata={"intent": "maintenance", "user_skill_level": "intermediate"}
    )


@pytest.fixture
def sample_chunks():
    """Sample document chunks for testing."""
    return [
        Mock(
            content="Test chunk 1",
            manual_type="owners",
            section="Maintenance",
            similarity_score=0.9,
            to_dict=lambda: {"content": "Test chunk 1", "manual_type": "owners"}
        ),
        Mock(
            content="Test chunk 2",
            manual_type="repair",
            section="Engine",
            similarity_score=0.8,
            to_dict=lambda: {"content": "Test chunk 2", "manual_type": "repair"}
        )
    ]


@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        "embedding_model": "textembedding-gecko@003",
        "generation_model": "gemini-1.5-pro",
        "max_tokens": 2048,
        "temperature": 0.2
    }


@pytest.fixture
def sample_queries():
    """Sample queries for testing."""
    return [
        "How do I check the engine oil level?",
        "What is the recommended tire pressure?",
        "Engine won't start, what should I check?"
    ]


@pytest.fixture
def mock_rag_system(
    mock_bigquery_client,
    mock_vector_search,
    mock_document_processor,
    mock_embedding_model,
    mock_generation_model,
    mock_intent_detector,
    mock_safety_enhancer,
    mock_response_generator
):
    """Mock RAG system for testing."""
    system = Mock(spec=HusqvarnaRAGSystem)
    system.project_id = "test-project"
    system.location = "us-central1"
    system.bigquery_client = mock_bigquery_client
    system.vector_search = mock_vector_search
    system.document_processor = mock_document_processor
    system.embedding_model = mock_embedding_model
    system.generation_model = mock_generation_model
    system.intent_detector = mock_intent_detector
    system.safety_enhancer = mock_safety_enhancer
    system.response_generator = mock_response_generator
    system.query_system = AsyncMock()
    system.batch_query = AsyncMock()
    system.get_system_stats = AsyncMock()
    return system 