"""
Tests for Chat API

Task #28: POST /api/chat endpoint
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.api.chat import (
    ChatRequest,
    ChatResponse,
    CitationResponse,
    UsageResponse,
    get_rag_service,
    _convert_rag_response,
)
from app.services.rag_service import RAGResponse, Citation
from app.services.claude_service import TokenUsage


client = TestClient(app)


class TestChatRequest:
    """Tests for ChatRequest model."""
    
    def test_valid_request(self):
        """Test valid chat request."""
        request = ChatRequest(query="What is X?")
        assert request.query == "What is X?"
        assert request.conversation_id is None
        assert request.template == "default"
        assert request.top_k == 5
    
    def test_request_with_all_fields(self):
        """Test request with all optional fields."""
        request = ChatRequest(
            query="Test query",
            conversation_id="conv-123",
            doc_ids=["doc-1", "doc-2"],
            template="academic",
            top_k=10,
            stream=True,
        )
        assert request.doc_ids == ["doc-1", "doc-2"]
        assert request.template == "academic"
        assert request.stream is True
    
    def test_query_min_length(self):
        """Test query minimum length validation."""
        with pytest.raises(ValueError):
            ChatRequest(query="")
    
    def test_top_k_range(self):
        """Test top_k range validation."""
        # Valid range
        request = ChatRequest(query="test", top_k=1)
        assert request.top_k == 1
        
        request = ChatRequest(query="test", top_k=20)
        assert request.top_k == 20


class TestConvertRAGResponse:
    """Tests for _convert_rag_response function."""
    
    def test_converts_correctly(self):
        """Test RAGResponse to ChatResponse conversion."""
        rag_response = RAGResponse(
            answer="The answer is...",
            citations=[
                Citation(id=1, doc_id="doc-1", page=5, text_snippet="snippet", score=0.9)
            ],
            usage=TokenUsage(input_tokens=100, output_tokens=50),
            model="sonnet",
            contexts_used=3,
            query="What is X?",
        )
        
        chat_response = _convert_rag_response(rag_response, "conv-123")
        
        assert chat_response.answer == "The answer is..."
        assert chat_response.conversation_id == "conv-123"
        assert len(chat_response.citations) == 1
        assert chat_response.citations[0].id == 1
        assert chat_response.usage.total_tokens == 150
        assert chat_response.model == "sonnet"


class TestChatEndpoint:
    """Tests for POST /api/chat endpoint."""
    
    @pytest.fixture
    def mock_rag_service(self):
        """Mock RAG service."""
        with patch("app.api.chat.get_rag_service") as mock_get:
            mock_service = MagicMock()
            mock_get.return_value = mock_service
            yield mock_service
    
    def test_chat_success(self, mock_rag_service):
        """Test successful chat request."""
        # Setup mock response
        mock_rag_service.query.return_value = RAGResponse(
            answer="Based on [1], the answer is...",
            citations=[
                Citation(id=1, doc_id="doc-1", page=1, text_snippet="context", score=0.85)
            ],
            usage=TokenUsage(input_tokens=200, output_tokens=100),
            model="sonnet",
            contexts_used=3,
            query="What is X?",
        )
        
        response = client.post(
            "/api/chat",
            json={"query": "What is X?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "citations" in data
        assert "conversation_id" in data
        assert data["model"] == "sonnet"
    
    def test_chat_with_doc_filter(self, mock_rag_service):
        """Test chat with document filter."""
        mock_rag_service.query.return_value = RAGResponse(
            answer="Answer",
            citations=[],
            usage=TokenUsage(input_tokens=100, output_tokens=50),
            model="sonnet",
            contexts_used=0,
            query="test",
        )
        
        response = client.post(
            "/api/chat",
            json={
                "query": "Test query",
                "doc_ids": ["doc-1", "doc-2"]
            }
        )
        
        assert response.status_code == 200
        # Verify filter was passed
        call_args = mock_rag_service.query.call_args
        assert call_args.kwargs.get("search_filter") is not None
    
    def test_chat_with_template(self, mock_rag_service):
        """Test chat with custom template."""
        mock_rag_service.query.return_value = RAGResponse(
            answer="Academic answer",
            citations=[],
            usage=TokenUsage(input_tokens=100, output_tokens=50),
            model="sonnet",
            contexts_used=1,
            query="test",
        )
        
        response = client.post(
            "/api/chat",
            json={
                "query": "Test query",
                "template": "academic"
            }
        )
        
        assert response.status_code == 200
        mock_rag_service.set_template.assert_called()
    
    def test_chat_invalid_template(self, mock_rag_service):
        """Test chat with invalid template."""
        response = client.post(
            "/api/chat",
            json={
                "query": "Test query",
                "template": "invalid_template"
            }
        )
        
        assert response.status_code == 400
        assert "Invalid template" in response.json()["detail"]
    
    def test_chat_empty_query(self):
        """Test chat with empty query."""
        response = client.post(
            "/api/chat",
            json={"query": ""}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_chat_generates_conversation_id(self, mock_rag_service):
        """Test that conversation_id is generated if not provided."""
        mock_rag_service.query.return_value = RAGResponse(
            answer="Answer",
            citations=[],
            usage=TokenUsage(input_tokens=100, output_tokens=50),
            model="sonnet",
            contexts_used=1,
            query="test",
        )
        
        response = client.post(
            "/api/chat",
            json={"query": "Test query"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"].startswith("conv-")
    
    def test_chat_preserves_conversation_id(self, mock_rag_service):
        """Test that provided conversation_id is preserved."""
        mock_rag_service.query.return_value = RAGResponse(
            answer="Answer",
            citations=[],
            usage=TokenUsage(input_tokens=100, output_tokens=50),
            model="sonnet",
            contexts_used=1,
            query="test",
        )
        
        response = client.post(
            "/api/chat",
            json={
                "query": "Test query",
                "conversation_id": "my-conv-123"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["conversation_id"] == "my-conv-123"


class TestChatHealthEndpoint:
    """Tests for GET /api/chat/health endpoint."""
    
    def test_health_check_healthy(self):
        """Test health check when all components healthy."""
        with patch("app.api.chat.get_rag_service") as mock_get:
            mock_service = MagicMock()
            mock_service.health_check.return_value = {
                "qdrant": True,
                "claude": True,
                "embeddings": True,
            }
            mock_get.return_value = mock_service
            
            response = client.get("/api/chat/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    def test_health_check_degraded(self):
        """Test health check when some components unhealthy."""
        with patch("app.api.chat.get_rag_service") as mock_get:
            mock_service = MagicMock()
            mock_service.health_check.return_value = {
                "qdrant": True,
                "claude": False,
                "embeddings": True,
            }
            mock_get.return_value = mock_service
            
            response = client.get("/api/chat/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"


# ============== Task #29: Chat History Endpoint Tests ==============

class TestChatHistoryEndpoints:
    """Tests for chat history endpoints (Task #29)."""
    
    @pytest.fixture
    def mock_history_manager(self):
        """Mock ChatHistoryManager."""
        with patch("app.api.chat.get_chat_history_manager") as mock_get:
            mock_manager = MagicMock()
            mock_get.return_value = mock_manager
            yield mock_manager
    
    def test_list_conversations(self, mock_history_manager):
        """Test GET /api/chat/history endpoint."""
        mock_history_manager.list_conversations.return_value = {
            "conversations": [
                {
                    "conversation_id": "conv-123",
                    "user_id": "user-1",
                    "last_message": "Hello...",
                    "last_message_at": "2025-12-04T10:00:00Z",
                },
                {
                    "conversation_id": "conv-456",
                    "user_id": "user-1",
                    "last_message": "What is...",
                    "last_message_at": "2025-12-04T09:00:00Z",
                },
            ],
            "last_evaluated_key": None,
        }
        
        response = client.get("/api/chat/history?user_id=user-1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["conversations"]) == 2
        assert data["has_more"] is False
    
    def test_list_conversations_with_pagination(self, mock_history_manager):
        """Test list conversations with pagination."""
        mock_history_manager.list_conversations.return_value = {
            "conversations": [{"conversation_id": "conv-1"}],
            "last_evaluated_key": {"pk": "user-1", "sk": "conv-1"},
        }
        
        response = client.get("/api/chat/history?user_id=user-1&limit=1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_more"] is True
    
    def test_get_conversation_history(self, mock_history_manager):
        """Test GET /api/chat/history/{conversation_id} endpoint."""
        from app.services.chat_history_manager import ChatMessage, MessageRole
        
        mock_history_manager.get_conversation_history.return_value = [
            ChatMessage(
                conversation_id="conv-123",
                role=MessageRole.USER,
                content="What is AI?",
                created_at="2025-12-04T10:00:00Z",
                user_id="user-1",
                message_id="msg-001",
            ),
            ChatMessage(
                conversation_id="conv-123",
                role=MessageRole.ASSISTANT,
                content="AI stands for...",
                created_at="2025-12-04T10:00:01Z",
                user_id="user-1",
                message_id="msg-002",
            ),
        ]
        
        response = client.get("/api/chat/history/conv-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "conv-123"
        assert data["total"] == 2
        assert len(data["messages"]) == 2
    
    def test_delete_conversation(self, mock_history_manager):
        """Test DELETE /api/chat/history/{conversation_id} endpoint."""
        mock_history_manager.delete_conversation.return_value = 5
        
        response = client.delete("/api/chat/history/conv-123?user_id=user-1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "conv-123"
        assert data["deleted_messages"] == 5
        assert data["status"] == "deleted"


class TestChatWithHistory:
    """Tests for chat endpoint with history integration."""
    
    @pytest.fixture
    def mock_services(self):
        """Mock both RAG and history services."""
        with patch("app.api.chat.get_rag_service") as mock_rag, \
             patch("app.api.chat.get_chat_history_manager") as mock_history:
            
            mock_rag_service = MagicMock()
            mock_history_manager = MagicMock()
            
            mock_rag.return_value = mock_rag_service
            mock_history.return_value = mock_history_manager
            
            yield mock_rag_service, mock_history_manager
    
    def test_chat_saves_messages(self, mock_services):
        """Test that chat saves user and assistant messages."""
        mock_rag_service, mock_history_manager = mock_services
        
        mock_rag_service.query.return_value = RAGResponse(
            answer="The answer is...",
            citations=[],
            usage=TokenUsage(input_tokens=100, output_tokens=50),
            model="sonnet",
            contexts_used=1,
            query="test",
        )
        mock_history_manager.get_history_for_context.return_value = []
        
        response = client.post(
            "/api/chat",
            json={
                "query": "What is X?",
                "conversation_id": "conv-123",
                "user_id": "user-1",
            }
        )
        
        assert response.status_code == 200
        
        # Verify user message was saved
        mock_history_manager.save_user_message.assert_called_once()
        call_args = mock_history_manager.save_user_message.call_args
        assert call_args.kwargs["conversation_id"] == "conv-123"
        assert call_args.kwargs["content"] == "What is X?"
        
        # Verify assistant message was saved
        mock_history_manager.save_assistant_message.assert_called_once()
    
    def test_chat_loads_history_for_context(self, mock_services):
        """Test that chat loads history for existing conversation."""
        mock_rag_service, mock_history_manager = mock_services
        
        mock_history_manager.get_history_for_context.return_value = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]
        
        mock_rag_service.query.return_value = RAGResponse(
            answer="Follow-up answer",
            citations=[],
            usage=TokenUsage(input_tokens=100, output_tokens=50),
            model="sonnet",
            contexts_used=1,
            query="test",
        )
        
        response = client.post(
            "/api/chat",
            json={
                "query": "Follow-up question",
                "conversation_id": "conv-123",
                "include_history": True,
            }
        )
        
        assert response.status_code == 200
        
        # Verify history was loaded
        mock_history_manager.get_history_for_context.assert_called_once()
        
        # Verify history was passed to RAG
        call_args = mock_rag_service.query.call_args
        assert call_args.kwargs.get("history") is not None
    
    def test_chat_skips_history_when_disabled(self, mock_services):
        """Test that chat skips history when include_history=False."""
        mock_rag_service, mock_history_manager = mock_services
        
        mock_rag_service.query.return_value = RAGResponse(
            answer="Answer",
            citations=[],
            usage=TokenUsage(input_tokens=100, output_tokens=50),
            model="sonnet",
            contexts_used=1,
            query="test",
        )
        
        response = client.post(
            "/api/chat",
            json={
                "query": "Question",
                "conversation_id": "conv-123",
                "include_history": False,
            }
        )
        
        assert response.status_code == 200
        
        # History should not be loaded when disabled
        mock_history_manager.get_history_for_context.assert_not_called()
