"""
Tests for Embeddings Service

Task #20: Implement Titan Embeddings integration (using Cohere)
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from botocore.exceptions import ClientError

from app.services.embeddings_service import (
    EmbeddingsService,
    EmbeddingResult,
    create_embeddings_service,
)


class TestEmbeddingsService:
    """Tests for EmbeddingsService class."""
    
    @pytest.fixture
    def mock_bedrock_client(self):
        """Create mock Bedrock client."""
        mock = MagicMock()
        return mock
    
    @pytest.fixture
    def embeddings_service(self, mock_bedrock_client):
        """Create embeddings service with mocked client."""
        return EmbeddingsService(
            region="ap-southeast-1",
            bedrock_client=mock_bedrock_client,
        )
    
    def _create_mock_response(self, embeddings):
        """Helper to create mock Bedrock response."""
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps({
            "embeddings": embeddings
        }).encode()
        return {"body": mock_body}
    
    def test_init_creates_client(self):
        """Test initialization creates Bedrock client."""
        with patch('boto3.client') as mock_boto:
            service = EmbeddingsService(region="us-east-1")
            mock_boto.assert_called_once_with(
                'bedrock-runtime',
                region_name="us-east-1"
            )
    
    def test_embed_text_single(self, embeddings_service, mock_bedrock_client):
        """Test embedding a single text."""
        expected_embedding = [0.1] * 1024
        mock_bedrock_client.invoke_model.return_value = self._create_mock_response(
            [expected_embedding]
        )
        
        result = embeddings_service.embed_text("test text")
        
        assert len(result) == 1024
        assert result == expected_embedding
    
    def test_embed_texts_batch(self, embeddings_service, mock_bedrock_client):
        """Test embedding multiple texts."""
        embeddings = [[0.1] * 1024, [0.2] * 1024, [0.3] * 1024]
        mock_bedrock_client.invoke_model.return_value = self._create_mock_response(
            embeddings
        )
        
        texts = ["text 1", "text 2", "text 3"]
        results = embeddings_service.embed_texts(texts)
        
        assert len(results) == 3
        assert all(len(emb) == 1024 for emb in results)
    
    def test_embed_texts_empty_returns_empty(self, embeddings_service):
        """Test empty input returns empty list."""
        result = embeddings_service.embed_texts([])
        assert result == []
    
    def test_embed_texts_batches_large_input(self, embeddings_service, mock_bedrock_client):
        """Test that large inputs are batched correctly."""
        # Create 50 texts (should be 2 batches of 25)
        texts = [f"text {i}" for i in range(50)]
        
        # Mock returns 25 embeddings per call
        batch_embeddings = [[0.1] * 1024 for _ in range(25)]
        mock_bedrock_client.invoke_model.return_value = self._create_mock_response(
            batch_embeddings
        )
        
        results = embeddings_service.embed_texts(texts)
        
        # Should have called invoke_model twice (2 batches)
        assert mock_bedrock_client.invoke_model.call_count == 2
        assert len(results) == 50
    
    def test_embed_texts_retries_on_throttling(self, embeddings_service, mock_bedrock_client):
        """Test exponential backoff on throttling."""
        # First call throttled, second succeeds
        throttle_error = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "InvokeModel"
        )
        expected_embedding = [[0.1] * 1024]
        
        mock_bedrock_client.invoke_model.side_effect = [
            throttle_error,
            self._create_mock_response(expected_embedding),
        ]
        
        with patch('time.sleep'):  # Don't actually sleep in tests
            result = embeddings_service.embed_texts(["test"])
        
        assert len(result) == 1
        assert mock_bedrock_client.invoke_model.call_count == 2
    
    def test_embed_texts_max_retries_exceeded(self, embeddings_service, mock_bedrock_client):
        """Test failure after max retries."""
        throttle_error = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "InvokeModel"
        )
        
        # Always throttle
        mock_bedrock_client.invoke_model.side_effect = throttle_error
        
        with patch('time.sleep'):
            with pytest.raises(ClientError):
                embeddings_service.embed_texts(["test"])
        
        # Should have tried MAX_RETRIES times
        assert mock_bedrock_client.invoke_model.call_count == 5
    
    def test_embed_texts_non_throttle_error_not_retried(
        self, embeddings_service, mock_bedrock_client
    ):
        """Test non-throttling errors are not retried."""
        other_error = ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid input"}},
            "InvokeModel"
        )
        
        mock_bedrock_client.invoke_model.side_effect = other_error
        
        with pytest.raises(ClientError):
            embeddings_service.embed_texts(["test"])
        
        # Should only try once
        assert mock_bedrock_client.invoke_model.call_count == 1
    
    def test_embed_query_uses_search_query_type(
        self, embeddings_service, mock_bedrock_client
    ):
        """Test embed_query uses search_query input type."""
        expected_embedding = [0.1] * 1024
        mock_bedrock_client.invoke_model.return_value = self._create_mock_response(
            [expected_embedding]
        )
        
        result = embeddings_service.embed_query("search query")
        
        # Verify input_type was search_query
        call_args = mock_bedrock_client.invoke_model.call_args
        body = json.loads(call_args.kwargs['body'])
        assert body['input_type'] == 'search_query'
        assert len(result) == 1024
    
    def test_health_check_success(self, embeddings_service, mock_bedrock_client):
        """Test health check when service is healthy."""
        expected_embedding = [0.1] * 1024
        mock_bedrock_client.invoke_model.return_value = self._create_mock_response(
            [expected_embedding]
        )
        
        assert embeddings_service.health_check() is True
    
    def test_health_check_failure(self, embeddings_service, mock_bedrock_client):
        """Test health check when service is down."""
        mock_bedrock_client.invoke_model.side_effect = Exception("Service unavailable")
        
        assert embeddings_service.health_check() is False
    
    def test_vector_size_constant(self, embeddings_service):
        """Test VECTOR_SIZE is 1024."""
        assert embeddings_service.VECTOR_SIZE == 1024
    
    def test_batch_size_constant(self, embeddings_service):
        """Test BATCH_SIZE is 25."""
        assert embeddings_service.BATCH_SIZE == 25
    
    def test_max_retries_constant(self, embeddings_service):
        """Test MAX_RETRIES is 5."""
        assert embeddings_service.MAX_RETRIES == 5


class TestCreateEmbeddingsService:
    """Tests for create_embeddings_service function."""
    
    def test_creates_service(self):
        """Test convenience function creates service."""
        with patch('boto3.client'):
            service = create_embeddings_service(region="us-west-2")
            assert isinstance(service, EmbeddingsService)
            assert service.region == "us-west-2"


class TestEmbeddingDimensions:
    """Property tests for embedding dimensions."""
    
    def test_all_embeddings_have_correct_dimension(self):
        """
        **Feature: m1-idp-ingestion, Property 9: Titan Embedding Dimension**
        
        Verify all embeddings are 1024 dimensions.
        **Validates: Requirements 7.1**
        """
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            
            # Generate various text inputs
            test_texts = [
                "short",
                "medium length text with more words",
                "a" * 1000,  # Long text
                "Special chars: @#$%^&*()",
                "Unicode: 日本語 한국어 العربية",
            ]
            
            # Mock returns 1024-dim embeddings
            embeddings = [[0.1] * 1024 for _ in test_texts]
            mock_body = MagicMock()
            mock_body.read.return_value = json.dumps({
                "embeddings": embeddings
            }).encode()
            mock_client.invoke_model.return_value = {"body": mock_body}
            
            service = EmbeddingsService(bedrock_client=mock_client)
            results = service.embed_texts(test_texts)
            
            # All embeddings should be 1024 dimensions
            for i, emb in enumerate(results):
                assert len(emb) == 1024, f"Embedding {i} has wrong dimension"


class TestBatchProcessing:
    """Property tests for batch processing."""
    
    def test_batch_size_respected(self):
        """
        **Feature: m1-idp-ingestion, Property 10: Embedding Batch Processing**
        
        Verify batches of up to 25 texts.
        **Validates: Requirements 7.2**
        """
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            
            # Track batch sizes
            batch_sizes = []
            
            def track_batch_size(modelId, body):
                data = json.loads(body)
                batch_sizes.append(len(data['texts']))
                
                embeddings = [[0.1] * 1024 for _ in data['texts']]
                mock_body = MagicMock()
                mock_body.read.return_value = json.dumps({
                    "embeddings": embeddings
                }).encode()
                return {"body": mock_body}
            
            mock_client.invoke_model.side_effect = track_batch_size
            
            service = EmbeddingsService(bedrock_client=mock_client)
            
            # Test with 60 texts (should be 3 batches: 25, 25, 10)
            texts = [f"text {i}" for i in range(60)]
            service.embed_texts(texts)
            
            # Verify no batch exceeds 25
            assert all(size <= 25 for size in batch_sizes)
            assert batch_sizes == [25, 25, 10]
