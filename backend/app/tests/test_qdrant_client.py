"""
Tests for Qdrant Vector Store Client

Task #19: Setup Qdrant vector database on EC2
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import uuid

from app.services.qdrant_client import (
    QdrantVectorStore,
    SearchResult,
    create_qdrant_store,
)


class TestQdrantVectorStore:
    """Tests for QdrantVectorStore class."""
    
    @pytest.fixture
    def mock_qdrant_client(self):
        """Create mock Qdrant client."""
        with patch('app.services.qdrant_client.QdrantClient') as mock:
            yield mock
    
    @pytest.fixture
    def vector_store(self, mock_qdrant_client):
        """Create vector store with mocked client."""
        mock_instance = MagicMock()
        mock_qdrant_client.return_value = mock_instance
        
        # Mock get_collections to return empty list
        mock_instance.get_collections.return_value = MagicMock(collections=[])
        
        store = QdrantVectorStore(host="localhost", port=6333)
        return store
    
    def test_init_creates_client(self, mock_qdrant_client):
        """Test that initialization creates Qdrant client."""
        store = QdrantVectorStore(host="test-host", port=1234)
        
        mock_qdrant_client.assert_called_once_with(
            host="test-host",
            port=1234,
            grpc_port=6334,
            prefer_grpc=False,
        )
    
    def test_ensure_collection_creates_new(self, vector_store):
        """Test collection creation when it doesn't exist."""
        # Mock empty collections
        vector_store.client.get_collections.return_value = MagicMock(collections=[])
        
        result = vector_store.ensure_collection()
        
        assert result is True
        vector_store.client.create_collection.assert_called_once()
    
    def test_ensure_collection_exists(self, vector_store):
        """Test when collection already exists."""
        # Mock existing collection
        mock_collection = MagicMock()
        mock_collection.name = "documents"
        vector_store.client.get_collections.return_value = MagicMock(
            collections=[mock_collection]
        )
        
        result = vector_store.ensure_collection()
        
        assert result is True
        vector_store.client.create_collection.assert_not_called()
    
    def test_upsert_vectors_success(self, vector_store):
        """Test successful vector upsert."""
        doc_id = "test-doc-123"
        texts = ["chunk 1", "chunk 2"]
        vectors = [[0.1] * 1024, [0.2] * 1024]
        
        result = vector_store.upsert_vectors(doc_id, texts, vectors)
        
        assert result == 2
        vector_store.client.upsert.assert_called_once()
    
    def test_upsert_vectors_validates_dimensions(self, vector_store):
        """Test that upsert validates vector dimensions."""
        doc_id = "test-doc"
        texts = ["chunk 1"]
        vectors = [[0.1] * 512]  # Wrong dimension
        
        with pytest.raises(ValueError, match="expected 1024"):
            vector_store.upsert_vectors(doc_id, texts, vectors)
    
    def test_upsert_vectors_validates_length_match(self, vector_store):
        """Test that texts and vectors must have same length."""
        doc_id = "test-doc"
        texts = ["chunk 1", "chunk 2"]
        vectors = [[0.1] * 1024]  # Only one vector
        
        with pytest.raises(ValueError, match="same length"):
            vector_store.upsert_vectors(doc_id, texts, vectors)
    
    def test_upsert_empty_returns_zero(self, vector_store):
        """Test that empty input returns 0."""
        result = vector_store.upsert_vectors("doc", [], [])
        assert result == 0
    
    def test_search_returns_results(self, vector_store):
        """Test search returns SearchResult objects."""
        # Mock search response
        mock_hit = MagicMock()
        mock_hit.id = "point-123"
        mock_hit.score = 0.95
        mock_hit.payload = {
            "doc_id": "doc-1",
            "chunk_index": 0,
            "page": 1,
            "text": "test content",
            "is_table": False,
        }
        vector_store.client.search.return_value = [mock_hit]
        
        query_vector = [0.1] * 1024
        results = vector_store.search(query_vector, top_k=5)
        
        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].doc_id == "doc-1"
        assert results[0].score == 0.95
        assert results[0].text == "test content"
    
    def test_search_validates_query_dimension(self, vector_store):
        """Test search validates query vector dimension."""
        query_vector = [0.1] * 512  # Wrong dimension
        
        with pytest.raises(ValueError, match="expected 1024"):
            vector_store.search(query_vector)
    
    def test_search_with_doc_filter(self, vector_store):
        """Test search with document ID filter."""
        vector_store.client.search.return_value = []
        
        query_vector = [0.1] * 1024
        vector_store.search(query_vector, doc_id="specific-doc")
        
        # Verify filter was passed
        call_args = vector_store.client.search.call_args
        assert call_args.kwargs.get('query_filter') is not None
    
    def test_delete_document(self, vector_store):
        """Test document deletion."""
        # Mock count
        vector_store.client.count.return_value = MagicMock(count=5)
        
        result = vector_store.delete_document("doc-to-delete")
        
        assert result == 5
        vector_store.client.delete.assert_called_once()
    
    def test_get_document_count(self, vector_store):
        """Test getting document vector count."""
        vector_store.client.count.return_value = MagicMock(count=10)
        
        count = vector_store.get_document_count("test-doc")
        
        assert count == 10
    
    def test_get_collection_info(self, vector_store):
        """Test getting collection info."""
        mock_info = MagicMock()
        mock_info.vectors_count = 100
        mock_info.points_count = 100
        mock_info.status.value = "green"
        vector_store.client.get_collection.return_value = mock_info
        
        info = vector_store.get_collection_info()
        
        assert info["name"] == "documents"
        assert info["vectors_count"] == 100
        assert info["vector_size"] == 1024
    
    def test_health_check_success(self, vector_store):
        """Test health check when Qdrant is healthy."""
        vector_store.client.get_collections.return_value = MagicMock()
        
        assert vector_store.health_check() is True
    
    def test_health_check_failure(self, vector_store):
        """Test health check when Qdrant is down."""
        vector_store.client.get_collections.side_effect = Exception("Connection failed")
        
        assert vector_store.health_check() is False


class TestSearchResult:
    """Tests for SearchResult dataclass."""
    
    def test_search_result_creation(self):
        """Test SearchResult can be created with all fields."""
        result = SearchResult(
            id="point-1",
            score=0.9,
            doc_id="doc-1",
            chunk_index=0,
            page=1,
            text="test",
            is_table=False,
        )
        
        assert result.id == "point-1"
        assert result.score == 0.9
        assert result.doc_id == "doc-1"


class TestCreateQdrantStore:
    """Tests for create_qdrant_store function."""
    
    def test_creates_and_initializes_store(self):
        """Test convenience function creates store."""
        with patch('app.services.qdrant_client.QdrantClient') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            mock_instance.get_collections.return_value = MagicMock(collections=[])
            
            store = create_qdrant_store(host="localhost", port=6333)
            
            assert isinstance(store, QdrantVectorStore)
            mock_instance.create_collection.assert_called_once()
