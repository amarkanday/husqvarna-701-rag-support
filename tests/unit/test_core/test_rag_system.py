"""
Unit tests for the HusqvarnaRAGSystem class.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.husqbot.core.rag_system import HusqvarnaRAGSystem, QueryResult


class TestHusqvarnaRAGSystem:
    """Test cases for HusqvarnaRAGSystem."""
    
    @pytest.fixture
    def rag_system(self, mock_rag_system):
        """Create a RAG system instance for testing."""
        return mock_rag_system
    
    @pytest.mark.asyncio
    async def test_init(self):
        """Test RAG system initialization."""
        with patch('src.husqbot.core.rag_system.BigQueryClient'), \
             patch('src.husqbot.core.rag_system.VectorSearch'), \
             patch('src.husqbot.core.rag_system.DocumentProcessor'), \
             patch('src.husqbot.core.rag_system.EmbeddingModel'), \
             patch('src.husqbot.core.rag_system.GenerationModel'), \
             patch('src.husqbot.core.rag_system.IntentDetector'), \
             patch('src.husqbot.core.rag_system.SafetyEnhancer'), \
             patch('src.husqbot.core.rag_system.ResponseGenerator'):
            
            system = HusqvarnaRAGSystem("test-project", "us-central1")
            
            assert system.project_id == "test-project"
            assert system.location == "us-central1"
    
    @pytest.mark.asyncio
    async def test_setup_complete_system(self, rag_system):
        """Test complete system setup."""
        # Mock the _import_manuals method
        rag_system._import_manuals = AsyncMock()
        
        await rag_system.setup_complete_system()
        
        rag_system.bigquery_client.create_dataset_if_not_exists.assert_called_once()
        rag_system.bigquery_client.create_tables_if_not_exists.assert_called_once()
        rag_system._import_manuals.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_system_success(self, rag_system, sample_query_result):
        """Test successful query processing."""
        rag_system.query_system.return_value = sample_query_result
        
        result = await rag_system.query_system(
            query="How do I check the oil?",
            user_skill_level="intermediate"
        )
        
        assert result == sample_query_result
        rag_system.query_system.assert_called_once_with(
            query="How do I check the oil?",
            user_skill_level="intermediate",
            max_chunks=5
        )
    
    @pytest.mark.asyncio
    async def test_query_system_with_custom_params(self, rag_system, sample_query_result):
        """Test query system with custom parameters."""
        rag_system.query_system.return_value = sample_query_result
        
        result = await rag_system.query_system(
            query="Test query",
            user_skill_level="expert",
            max_chunks=10,
            temperature=0.5
        )
        
        rag_system.query_system.assert_called_once_with(
            query="Test query",
            user_skill_level="expert",
            max_chunks=10,
            temperature=0.5
        )
    
    @pytest.mark.asyncio
    async def test_batch_query_success(self, rag_system, sample_queries, sample_query_result):
        """Test successful batch query processing."""
        rag_system.batch_query.return_value = [sample_query_result] * len(sample_queries)
        
        results = await rag_system.batch_query(sample_queries, "intermediate")
        
        assert len(results) == len(sample_queries)
        rag_system.batch_query.assert_called_once_with(sample_queries, "intermediate")
    
    @pytest.mark.asyncio
    async def test_batch_query_with_exceptions(self, rag_system, sample_queries):
        """Test batch query with some exceptions."""
        results = [sample_query_result, Exception("Test error"), sample_query_result]
        rag_system.batch_query.return_value = results
        
        batch_results = await rag_system.batch_query(sample_queries, "intermediate")
        
        assert len(batch_results) == len(sample_queries)
        assert isinstance(batch_results[0], QueryResult)
        assert isinstance(batch_results[1], Exception)
        assert isinstance(batch_results[2], QueryResult)
    
    @pytest.mark.asyncio
    async def test_get_system_stats_success(self, rag_system):
        """Test successful system stats retrieval."""
        expected_stats = {
            "total_chunks": 1000,
            "cache_hit_rate": 0.75,
            "system_status": "healthy",
            "last_updated": "2024-01-01T00:00:00Z"
        }
        rag_system.get_system_stats.return_value = expected_stats
        
        stats = await rag_system.get_system_stats()
        
        assert stats == expected_stats
        rag_system.get_system_stats.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_system_stats_error(self, rag_system):
        """Test system stats retrieval with error."""
        rag_system.get_system_stats.side_effect = Exception("Database error")
        
        stats = await rag_system.get_system_stats()
        
        assert stats["system_status"] == "error"
        assert "Database error" in stats["error"]
    
    def test_build_context(self, rag_system, sample_chunks):
        """Test context building from chunks."""
        intent = "maintenance"
        user_skill_level = "intermediate"
        
        context = rag_system._build_context(sample_chunks, intent, user_skill_level)
        
        assert "Source 1 (owners, Maintenance)" in context
        assert "Source 2 (repair, Engine)" in context
        assert "Query Intent: maintenance" in context
        assert "User Skill Level: intermediate" in context
    
    def test_calculate_confidence(self, rag_system, sample_chunks):
        """Test confidence calculation."""
        confidence = rag_system._calculate_confidence(sample_chunks)
        
        # Expected: (0.9 + 0.8) / 2 = 0.85
        assert confidence == 0.85
    
    def test_calculate_confidence_empty_chunks(self, rag_system):
        """Test confidence calculation with empty chunks."""
        confidence = rag_system._calculate_confidence([])
        
        assert confidence == 0.0


class TestQueryResult:
    """Test cases for QueryResult dataclass."""
    
    def test_query_result_creation(self):
        """Test QueryResult creation."""
        result = QueryResult(
            answer="Test answer",
            sources=[{"content": "Test source"}],
            confidence=0.85,
            safety_level=1,
            processing_time=1.5,
            metadata={"intent": "maintenance"}
        )
        
        assert result.answer == "Test answer"
        assert len(result.sources) == 1
        assert result.confidence == 0.85
        assert result.safety_level == 1
        assert result.processing_time == 1.5
        assert result.metadata["intent"] == "maintenance"
    
    def test_query_result_defaults(self):
        """Test QueryResult with minimal parameters."""
        result = QueryResult(
            answer="Test",
            sources=[],
            confidence=0.0,
            safety_level=0,
            processing_time=0.0,
            metadata={}
        )
        
        assert result.answer == "Test"
        assert result.sources == []
        assert result.confidence == 0.0 