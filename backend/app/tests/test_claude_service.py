"""
Tests for Claude Service

Task #26: Bedrock Claude 3.5 Sonnet Integration
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json

from app.services.claude_service import (
    ClaudeService,
    ClaudeResponse,
    TokenUsage,
    StreamChunk,
    CLAUDE_MODELS,
    MODEL_PRICING,
    create_claude_service,
)


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""
    
    def test_total_tokens(self):
        """Test total_tokens property."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.total_tokens == 150
    
    def test_estimate_cost_sonnet(self):
        """Test cost estimation for Sonnet model."""
        usage = TokenUsage(input_tokens=1_000_000, output_tokens=1_000_000)
        cost = usage.estimate_cost("sonnet")
        # $3 input + $15 output = $18
        assert cost == 18.0
    
    def test_estimate_cost_haiku(self):
        """Test cost estimation for Haiku model."""
        usage = TokenUsage(input_tokens=1_000_000, output_tokens=1_000_000)
        cost = usage.estimate_cost("haiku")
        # $0.25 input + $1.25 output = $1.50
        assert cost == 1.5
    
    def test_to_dict(self):
        """Test to_dict method."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        d = usage.to_dict()
        assert d["input_tokens"] == 100
        assert d["output_tokens"] == 50
        assert d["total_tokens"] == 150


class TestClaudeResponse:
    """Tests for ClaudeResponse dataclass."""
    
    def test_to_dict(self):
        """Test to_dict method."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        response = ClaudeResponse(
            text="Hello!",
            usage=usage,
            model="sonnet",
            stop_reason="end_turn",
        )
        
        d = response.to_dict()
        assert d["text"] == "Hello!"
        assert d["model"] == "sonnet"
        assert d["usage"]["total_tokens"] == 150


class TestStreamChunk:
    """Tests for StreamChunk dataclass."""
    
    def test_stream_chunk_creation(self):
        """Test StreamChunk creation."""
        chunk = StreamChunk(text="Hello", is_final=False)
        assert chunk.text == "Hello"
        assert chunk.is_final is False
        assert chunk.usage is None
    
    def test_final_chunk_with_usage(self):
        """Test final chunk with usage stats."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        chunk = StreamChunk(text="", is_final=True, usage=usage)
        assert chunk.is_final is True
        assert chunk.usage.total_tokens == 150


class TestClaudeService:
    """Tests for ClaudeService class."""
    
    @pytest.fixture
    def mock_boto_client(self):
        """Create mock boto3 client."""
        with patch("app.services.claude_service.boto3") as mock_boto:
            mock_client = MagicMock()
            mock_boto.client.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def claude_service(self, mock_boto_client):
        """Create Claude service with mocked client."""
        return ClaudeService(region_name="ap-southeast-1", model="sonnet")
    
    def test_init_default_model(self, mock_boto_client):
        """Test initialization with default model."""
        service = ClaudeService()
        assert service.model_alias == "sonnet"
        assert service.model_id == CLAUDE_MODELS["sonnet"]
    
    def test_init_haiku_model(self, mock_boto_client):
        """Test initialization with Haiku model."""
        service = ClaudeService(model="haiku")
        assert service.model_alias == "haiku"
        assert service.model_id == CLAUDE_MODELS["haiku"]
    
    def test_switch_model(self, claude_service):
        """Test model switching."""
        claude_service.switch_model("haiku")
        assert claude_service.model_alias == "haiku"
        assert claude_service.model_id == CLAUDE_MODELS["haiku"]
    
    def test_switch_model_invalid(self, claude_service):
        """Test switching to invalid model raises error."""
        with pytest.raises(ValueError, match="Unknown model"):
            claude_service.switch_model("invalid")
    
    def test_estimate_tokens(self, claude_service):
        """Test token estimation."""
        # ~4 chars per token
        text = "a" * 100
        tokens = claude_service.estimate_tokens(text)
        assert tokens == 26  # 100 // 4 + 1
    
    def test_build_messages_simple(self, claude_service):
        """Test building messages with simple prompt."""
        messages, system = claude_service._build_messages("Hello")
        
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert system is None
    
    def test_build_messages_with_system(self, claude_service):
        """Test building messages with system prompt."""
        messages, system = claude_service._build_messages(
            "Hello",
            system_prompt="You are helpful."
        )
        
        assert len(messages) == 1
        assert system == "You are helpful."
    
    def test_build_messages_with_history(self, claude_service):
        """Test building messages with conversation history."""
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        messages, _ = claude_service._build_messages("How are you?", history=history)
        
        assert len(messages) == 3
        assert messages[0]["content"] == "Hi"
        assert messages[1]["content"] == "Hello!"
        assert messages[2]["content"] == "How are you?"
    
    def test_invoke_success(self, claude_service, mock_boto_client):
        """Test successful invoke."""
        # Mock response
        mock_response = {
            "body": MagicMock()
        }
        mock_response["body"].read.return_value = json.dumps({
            "content": [{"text": "Hello there!"}],
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "stop_reason": "end_turn",
        })
        mock_boto_client.invoke_model.return_value = mock_response
        
        response = claude_service.invoke("Say hello")
        
        assert response.text == "Hello there!"
        assert response.usage.input_tokens == 10
        assert response.usage.output_tokens == 5
        assert response.model == "sonnet"
    
    def test_invoke_with_system_prompt(self, claude_service, mock_boto_client):
        """Test invoke with system prompt."""
        mock_response = {
            "body": MagicMock()
        }
        mock_response["body"].read.return_value = json.dumps({
            "content": [{"text": "Response"}],
            "usage": {"input_tokens": 20, "output_tokens": 10},
        })
        mock_boto_client.invoke_model.return_value = mock_response
        
        claude_service.invoke("Hello", system_prompt="Be brief")
        
        # Verify system was included in request
        call_args = mock_boto_client.invoke_model.call_args
        body = json.loads(call_args.kwargs["body"])
        assert body.get("system") == "Be brief"
    
    def test_invoke_with_context(self, claude_service, mock_boto_client):
        """Test invoke_with_context for RAG."""
        mock_response = {
            "body": MagicMock()
        }
        mock_response["body"].read.return_value = json.dumps({
            "content": [{"text": "Based on [1], the answer is..."}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
        })
        mock_boto_client.invoke_model.return_value = mock_response
        
        contexts = [
            {"citation_id": 1, "text": "Context 1", "doc_id": "doc-1", "page": 1},
            {"citation_id": 2, "text": "Context 2", "doc_id": "doc-2", "page": 3},
        ]
        
        response = claude_service.invoke_with_context(
            query="What is X?",
            contexts=contexts,
        )
        
        assert "[1]" in response.text
        
        # Verify context was included in prompt
        call_args = mock_boto_client.invoke_model.call_args
        body = json.loads(call_args.kwargs["body"])
        prompt = body["messages"][0]["content"]
        assert "Context 1" in prompt
        assert "[1]" in prompt
        assert "doc-1" in prompt


class TestClaudeServiceStreaming:
    """Tests for streaming functionality."""
    
    @pytest.fixture
    def mock_boto_client(self):
        """Create mock boto3 client."""
        with patch("app.services.claude_service.boto3") as mock_boto:
            mock_client = MagicMock()
            mock_boto.client.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def claude_service(self, mock_boto_client):
        """Create Claude service with mocked client."""
        return ClaudeService(region_name="ap-southeast-1")
    
    def test_invoke_stream(self, claude_service, mock_boto_client):
        """Test streaming invoke."""
        # Mock streaming response
        stream_events = [
            {"chunk": {"bytes": json.dumps({
                "type": "message_start",
                "message": {"usage": {"input_tokens": 10}}
            }).encode()}},
            {"chunk": {"bytes": json.dumps({
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "Hello"}
            }).encode()}},
            {"chunk": {"bytes": json.dumps({
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": " World"}
            }).encode()}},
            {"chunk": {"bytes": json.dumps({
                "type": "message_delta",
                "usage": {"output_tokens": 5}
            }).encode()}},
            {"chunk": {"bytes": json.dumps({
                "type": "message_stop"
            }).encode()}},
        ]
        
        mock_boto_client.invoke_model_with_response_stream.return_value = {
            "body": iter(stream_events)
        }
        
        chunks = list(claude_service.invoke_stream("Say hello"))
        
        # Should have text chunks and final chunk
        text_chunks = [c for c in chunks if c.text]
        final_chunks = [c for c in chunks if c.is_final]
        
        assert len(text_chunks) == 2
        assert text_chunks[0].text == "Hello"
        assert text_chunks[1].text == " World"
        assert len(final_chunks) == 1
        assert final_chunks[0].usage.input_tokens == 10


class TestCreateClaudeService:
    """Tests for create_claude_service function."""
    
    def test_creates_service(self):
        """Test convenience function creates service."""
        with patch("app.services.claude_service.boto3"):
            service = create_claude_service(model="haiku")
            assert isinstance(service, ClaudeService)
            assert service.model_alias == "haiku"
