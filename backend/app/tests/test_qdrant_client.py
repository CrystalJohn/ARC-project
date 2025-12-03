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
        # Mock query_points response (qdrant-client >= 1.7)
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
        mock_result = MagicMock()
        mock_result.points = [mock_hit]
        vector_store.client.query_points.return_value = mock_result
        
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
        mock_result = MagicMock()
        mock_result.points = []
        vector_store.client.query_points.return_value = mock_result
        
        query_vector = [0.1] * 1024
        vector_store.search(query_vector, doc_id="specific-doc")
        
        # Verify query_points was called with filter
        call_args = vector_store.client.query_points.call_args
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
    
    def test_search_result_to_dict(self):
        """Test SearchResult to_dict method."""
        result = SearchResult(
            id="point-1",
            score=0.9,
            doc_id="doc-1",
            chunk_index=2,
            page=5,
            text="test content",
            is_table=True,
        )
        
        d = result.to_dict()
        assert d["id"] == "point-1"
        assert d["score"] == 0.9
        assert d["doc_id"] == "doc-1"
        assert d["chunk_index"] == 2
        assert d["page"] == 5
        assert d["text"] == "test content"
        assert d["is_table"] is True


class TestRAGContext:
    """Tests for RAGContext dataclass (Task #25)."""
    
    def test_rag_context_creation(self):
        """Test RAGContext can be created."""
        from app.services.qdrant_client import RAGContext
        
        ctx = RAGContext(
            text="relevant content",
            doc_id="doc-1",
            page=3,
            chunk_index=5,
            score=0.85,
            citation_id=1,
            is_table=False,
        )
        
        assert ctx.text == "relevant content"
        assert ctx.citation_id == 1
        assert ctx.score == 0.85
    
    def test_rag_context_to_dict(self):
        """Test RAGContext to_dict method."""
        from app.services.qdrant_client import RAGContext
        
        ctx = RAGContext(
            text="content",
            doc_id="doc-1",
            page=1,
            chunk_index=0,
            score=0.9,
            citation_id=2,
        )
        
        d = ctx.to_dict()
        assert d["citation_id"] == 2
        assert d["score"] == 0.9


class TestSearchFilter:
    """Tests for SearchFilter dataclass (Task #25)."""
    
    def test_search_filter_defaults(self):
        """Test SearchFilter default values."""
        from app.services.qdrant_client import SearchFilter
        
        f = SearchFilter()
        assert f.doc_ids is None
        assert f.page_min is None
        assert f.page_max is None
        assert f.is_table is None
        assert f.exclude_doc_ids is None
    
    def test_search_filter_with_values(self):
        """Test SearchFilter with values."""
        from app.services.qdrant_client import SearchFilter
        
        f = SearchFilter(
            doc_ids=["doc-1", "doc-2"],
            page_min=1,
            page_max=10,
            is_table=False,
        )
        
        assert f.doc_ids == ["doc-1", "doc-2"]
        assert f.page_min == 1
        assert f.page_max == 10


class TestBuildFilter:
    """Tests for _build_filter method (Task #25)."""
    
    @pytest.fixture
    def vector_store(self):
        """Create vector store with mocked client."""
        with patch('app.services.qdrant_client.QdrantClient') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            mock_instance.get_collections.return_value = MagicMock(collections=[])
            return QdrantVectorStore(host="localhost", port=6333)
    
    def test_build_filter_none(self, vector_store):
        """Test _build_filter returns None when no filter."""
        result = vector_store._build_filter(None, None)
        assert result is None
    
    def test_build_filter_legacy_doc_id(self, vector_store):
        """Test _build_filter with legacy doc_id."""
        result = vector_store._build_filter(None, "doc-123")
        assert result is not None
        assert len(result.must) == 1
    
    def test_build_filter_multiple_doc_ids(self, vector_store):
        """Test _build_filter with multiple doc_ids."""
        from app.services.qdrant_client import SearchFilter
        
        f = SearchFilter(doc_ids=["doc-1", "doc-2", "doc-3"])
        result = vector_store._build_filter(f)
        
        assert result is not None
        assert len(result.must) == 1
    
    def test_build_filter_single_doc_id(self, vector_store):
        """Test _build_filter with single doc_id in list."""
        from app.services.qdrant_client import SearchFilter
        
        f = SearchFilter(doc_ids=["doc-1"])
        result = vector_store._build_filter(f)
        
        assert result is not None
    
    def test_build_filter_page_range(self, vector_store):
        """Test _build_filter with page range."""
        from app.services.qdrant_client import SearchFilter
        
        f = SearchFilter(page_min=5, page_max=10)
        result = vector_store._build_filter(f)
        
        assert result is not None
        assert len(result.must) == 1
    
    def test_build_filter_is_table(self, vector_store):
        """Test _build_filter with is_table filter."""
        from app.services.qdrant_client import SearchFilter
        
        f = SearchFilter(is_table=True)
        result = vector_store._build_filter(f)
        
        assert result is not None
    
    def test_build_filter_exclude_docs(self, vector_store):
        """Test _build_filter with exclude_doc_ids."""
        from app.services.qdrant_client import SearchFilter
        
        f = SearchFilter(exclude_doc_ids=["doc-bad"])
        result = vector_store._build_filter(f)
        
        assert result is not None
        assert result.must_not is not None


class TestSearchForRAG:
    """Tests for search_for_rag method (Task #25)."""
    
    @pytest.fixture
    def vector_store(self):
        """Create vector store with mocked client."""
        with patch('app.services.qdrant_client.QdrantClient') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            mock_instance.get_collections.return_value = MagicMock(collections=[])
            return QdrantVectorStore(host="localhost", port=6333)
    
    def test_search_for_rag_returns_rag_context(self, vector_store):
        """Test search_for_rag returns RAGContext objects."""
        from app.services.qdrant_client import RAGContext
        
        # Mock query_points response
        mock_hit = MagicMock()
        mock_hit.id = "point-1"
        mock_hit.score = 0.85
        mock_hit.payload = {
            "doc_id": "doc-1",
            "chunk_index": 0,
            "page": 1,
            "text": "relevant content",
            "is_table": False,
        }
        mock_result = MagicMock()
        mock_result.points = [mock_hit]
        vector_store.client.query_points.return_value = mock_result
        
        query_vector = [0.1] * 1024
        results = vector_store.search_for_rag(query_vector, top_k=5)
        
        assert len(results) == 1
        assert isinstance(results[0], RAGContext)
        assert results[0].citation_id == 1
        assert results[0].text == "relevant content"
    
    def test_search_for_rag_assigns_citation_ids(self, vector_store):
        """Test citation IDs are assigned sequentially."""
        from app.services.qdrant_client import RAGContext
        
        # Mock multiple results
        mock_hits = []
        for i in range(3):
            hit = MagicMock()
            hit.id = f"point-{i}"
            hit.score = 0.9 - i * 0.1
            hit.payload = {
                "doc_id": f"doc-{i}",
                "chunk_index": i,
                "page": 1,
                "text": f"content {i}",
                "is_table": False,
            }
            mock_hits.append(hit)
        
        mock_result = MagicMock()
        mock_result.points = mock_hits
        vector_store.client.query_points.return_value = mock_result
        
        query_vector = [0.1] * 1024
        results = vector_store.search_for_rag(query_vector, top_k=5, deduplicate=False)
        
        assert results[0].citation_id == 1
        assert results[1].citation_id == 2
        assert results[2].citation_id == 3


class TestDeduplicateResults:
    """Tests for _deduplicate_results method (Task #25)."""
    
    @pytest.fixture
    def vector_store(self):
        """Create vector store with mocked client."""
        with patch('app.services.qdrant_client.QdrantClient') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            mock_instance.get_collections.return_value = MagicMock(collections=[])
            return QdrantVectorStore(host="localhost", port=6333)
    
    def test_deduplicate_empty(self, vector_store):
        """Test deduplication with empty list."""
        result = vector_store._deduplicate_results([])
        assert result == []
    
    def test_deduplicate_removes_adjacent_lower_score(self, vector_store):
        """Test deduplication removes adjacent chunks with lower scores."""
        results = [
            SearchResult("1", 0.9, "doc-1", 0, 1, "text 0", False),
            SearchResult("2", 0.7, "doc-1", 1, 1, "text 1", False),  # Adjacent, lower score
        ]
        
        deduplicated = vector_store._deduplicate_results(results)
        
        # Should keep first (higher score), remove second (adjacent, lower)
        assert len(deduplicated) == 1
        assert deduplicated[0].chunk_index == 0
    
    def test_deduplicate_keeps_different_docs(self, vector_store):
        """Test deduplication keeps chunks from different docs."""
        results = [
            SearchResult("1", 0.9, "doc-1", 0, 1, "text", False),
            SearchResult("2", 0.8, "doc-2", 0, 1, "text", False),
        ]
        
        deduplicated = vector_store._deduplicate_results(results)
        
        assert len(deduplicated) == 2
    
    def test_deduplicate_keeps_non_adjacent(self, vector_store):
        """Test deduplication keeps non-adjacent chunks from same doc."""
        results = [
            SearchResult("1", 0.9, "doc-1", 0, 1, "text 0", False),
            SearchResult("2", 0.8, "doc-1", 5, 2, "text 5", False),  # Not adjacent
        ]
        
        deduplicated = vector_store._deduplicate_results(results)
        
        assert len(deduplicated) == 2


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
