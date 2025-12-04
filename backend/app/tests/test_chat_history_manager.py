"""
Unit tests for ChatHistoryManager (Task #29)

Tests chat history storage and retrieval in DynamoDB.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

from app.services.chat_history_manager import (
    ChatHistoryManager,
    ChatMessage,
    MessageRole,
    Conversation,
)


@pytest.fixture
def mock_dynamodb_client():
    """Create mock DynamoDB client."""
    return Mock()


@pytest.fixture
def chat_history_manager(mock_dynamodb_client):
    """Create ChatHistoryManager with mock client."""
    return ChatHistoryManager(
        table_name="test-chat-history",
        dynamodb_client=mock_dynamodb_client,
        region_name="ap-southeast-1",
    )


class TestChatMessage:
    """Tests for ChatMessage dataclass."""
    
    def test_to_dict_basic(self):
        """Test basic message to dict conversion."""
        msg = ChatMessage(
            conversation_id="conv-123",
            role=MessageRole.USER,
            content="Hello",
            created_at="2025-12-04T10:00:00Z",
            user_id="user-1",
        )
        
        result = msg.to_dict()
        
        assert result["conversation_id"] == "conv-123"
        assert result["role"] == "user"
        assert result["content"] == "Hello"
        assert result["user_id"] == "user-1"
    
    def test_to_dict_with_citations(self):
        """Test message with citations."""
        msg = ChatMessage(
            conversation_id="conv-123",
            role=MessageRole.ASSISTANT,
            content="Based on [1]...",
            created_at="2025-12-04T10:00:00Z",
            citations=[{"id": 1, "doc_id": "doc-1", "page": 5}],
            usage={"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
            model="sonnet",
        )
        
        result = msg.to_dict()
        
        assert result["citations"] == [{"id": 1, "doc_id": "doc-1", "page": 5}]
        assert result["usage"]["total_tokens"] == 150
        assert result["model"] == "sonnet"


class TestSaveMessage:
    """Tests for saving messages."""
    
    def test_save_user_message(self, chat_history_manager, mock_dynamodb_client):
        """Test saving a user message."""
        mock_dynamodb_client.put_item.return_value = {}
        
        result = chat_history_manager.save_user_message(
            conversation_id="conv-123",
            content="What is machine learning?",
            user_id="user-1",
        )
        
        assert result.conversation_id == "conv-123"
        assert result.role == MessageRole.USER
        assert result.content == "What is machine learning?"
        assert result.user_id == "user-1"
        assert result.message_id is not None
        
        mock_dynamodb_client.put_item.assert_called_once()
        call_args = mock_dynamodb_client.put_item.call_args
        item = call_args.kwargs["Item"]
        assert item["role"]["S"] == "user"
        assert item["content"]["S"] == "What is machine learning?"
    
    def test_save_assistant_message_with_metadata(self, chat_history_manager, mock_dynamodb_client):
        """Test saving assistant message with citations and usage."""
        mock_dynamodb_client.put_item.return_value = {}
        
        citations = [{"id": 1, "doc_id": "doc-1", "page": 5, "score": 0.85}]
        usage = {"input_tokens": 500, "output_tokens": 200, "total_tokens": 700}
        
        result = chat_history_manager.save_assistant_message(
            conversation_id="conv-123",
            content="Machine learning is...",
            user_id="user-1",
            citations=citations,
            usage=usage,
            model="sonnet",
        )
        
        assert result.role == MessageRole.ASSISTANT
        assert result.citations == citations
        assert result.usage == usage
        assert result.model == "sonnet"
        
        call_args = mock_dynamodb_client.put_item.call_args
        item = call_args.kwargs["Item"]
        assert "citations" in item
        assert item["model"]["S"] == "sonnet"
        assert item["usage"]["M"]["total_tokens"]["N"] == "700"


class TestGetConversationHistory:
    """Tests for retrieving conversation history."""
    
    def test_get_conversation_history(self, chat_history_manager, mock_dynamodb_client):
        """Test getting messages for a conversation."""
        mock_dynamodb_client.query.return_value = {
            "Items": [
                {
                    "conversation_id": {"S": "conv-123"},
                    "role": {"S": "user"},
                    "content": {"S": "Hello"},
                    "created_at": {"S": "2025-12-04T10:00:00Z"},
                    "user_id": {"S": "user-1"},
                    "message_id": {"S": "msg-001"},
                },
                {
                    "conversation_id": {"S": "conv-123"},
                    "role": {"S": "assistant"},
                    "content": {"S": "Hi there!"},
                    "created_at": {"S": "2025-12-04T10:00:01Z"},
                    "user_id": {"S": "user-1"},
                    "message_id": {"S": "msg-002"},
                },
            ]
        }
        
        messages = chat_history_manager.get_conversation_history("conv-123")
        
        assert len(messages) == 2
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Hello"
        assert messages[1].role == MessageRole.ASSISTANT
        assert messages[1].content == "Hi there!"
        
        mock_dynamodb_client.query.assert_called_once()
        call_args = mock_dynamodb_client.query.call_args
        assert call_args.kwargs["IndexName"] == "conversation-index"
    
    def test_get_history_for_context(self, chat_history_manager, mock_dynamodb_client):
        """Test getting history formatted for Claude context."""
        mock_dynamodb_client.query.return_value = {
            "Items": [
                {
                    "conversation_id": {"S": "conv-123"},
                    "role": {"S": "user"},
                    "content": {"S": "What is AI?"},
                    "created_at": {"S": "2025-12-04T10:00:00Z"},
                    "user_id": {"S": "user-1"},
                },
                {
                    "conversation_id": {"S": "conv-123"},
                    "role": {"S": "assistant"},
                    "content": {"S": "AI stands for..."},
                    "created_at": {"S": "2025-12-04T10:00:01Z"},
                    "user_id": {"S": "user-1"},
                },
            ]
        }
        
        history = chat_history_manager.get_history_for_context("conv-123", max_messages=10)
        
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "What is AI?"}
        assert history[1] == {"role": "assistant", "content": "AI stands for..."}
    
    def test_get_empty_history(self, chat_history_manager, mock_dynamodb_client):
        """Test getting history for non-existent conversation."""
        mock_dynamodb_client.query.return_value = {"Items": []}
        
        messages = chat_history_manager.get_conversation_history("conv-nonexistent")
        
        assert len(messages) == 0


class TestListConversations:
    """Tests for listing user conversations."""
    
    def test_list_conversations(self, chat_history_manager, mock_dynamodb_client):
        """Test listing conversations for a user."""
        mock_dynamodb_client.query.return_value = {
            "Items": [
                {
                    "user_id": {"S": "user-1"},
                    "sk": {"S": "CONV#conv-123#MSG#2025-12-04T10:00:00Z"},
                    "conversation_id": {"S": "conv-123"},
                    "role": {"S": "user"},
                    "content": {"S": "First conversation message"},
                    "created_at": {"S": "2025-12-04T10:00:00Z"},
                },
                {
                    "user_id": {"S": "user-1"},
                    "sk": {"S": "CONV#conv-456#MSG#2025-12-04T09:00:00Z"},
                    "conversation_id": {"S": "conv-456"},
                    "role": {"S": "assistant"},
                    "content": {"S": "Second conversation response"},
                    "created_at": {"S": "2025-12-04T09:00:00Z"},
                },
            ]
        }
        
        result = chat_history_manager.list_conversations("user-1", limit=10)
        
        assert len(result["conversations"]) == 2
        assert result["conversations"][0]["conversation_id"] == "conv-123"
        assert "last_message" in result["conversations"][0]
    
    def test_list_conversations_empty(self, chat_history_manager, mock_dynamodb_client):
        """Test listing conversations for user with no history."""
        mock_dynamodb_client.query.return_value = {"Items": []}
        
        result = chat_history_manager.list_conversations("new-user")
        
        assert len(result["conversations"]) == 0


class TestDeleteConversation:
    """Tests for deleting conversations."""
    
    def test_delete_conversation(self, chat_history_manager, mock_dynamodb_client):
        """Test deleting a conversation."""
        mock_dynamodb_client.query.return_value = {
            "Items": [
                {
                    "conversation_id": {"S": "conv-123"},
                    "role": {"S": "user"},
                    "content": {"S": "Message 1"},
                    "created_at": {"S": "2025-12-04T10:00:00Z"},
                    "user_id": {"S": "user-1"},
                },
                {
                    "conversation_id": {"S": "conv-123"},
                    "role": {"S": "assistant"},
                    "content": {"S": "Message 2"},
                    "created_at": {"S": "2025-12-04T10:00:01Z"},
                    "user_id": {"S": "user-1"},
                },
            ]
        }
        mock_dynamodb_client.delete_item.return_value = {}
        
        deleted = chat_history_manager.delete_conversation("conv-123", "user-1")
        
        assert deleted == 2
        assert mock_dynamodb_client.delete_item.call_count == 2


class TestParseMessage:
    """Tests for parsing DynamoDB items."""
    
    def test_parse_message_with_usage(self, chat_history_manager):
        """Test parsing message with usage info."""
        item = {
            "conversation_id": {"S": "conv-123"},
            "role": {"S": "assistant"},
            "content": {"S": "Response text"},
            "created_at": {"S": "2025-12-04T10:00:00Z"},
            "user_id": {"S": "user-1"},
            "message_id": {"S": "msg-001"},
            "model": {"S": "sonnet"},
            "usage": {
                "M": {
                    "input_tokens": {"N": "500"},
                    "output_tokens": {"N": "200"},
                    "total_tokens": {"N": "700"},
                }
            },
        }
        
        msg = chat_history_manager._parse_message(item)
        
        assert msg.model == "sonnet"
        assert msg.usage["input_tokens"] == 500
        assert msg.usage["output_tokens"] == 200
        assert msg.usage["total_tokens"] == 700
    
    def test_parse_message_with_citations(self, chat_history_manager):
        """Test parsing message with citations."""
        import json
        citations = [{"id": 1, "doc_id": "doc-1", "page": 5}]
        
        item = {
            "conversation_id": {"S": "conv-123"},
            "role": {"S": "assistant"},
            "content": {"S": "Based on [1]..."},
            "created_at": {"S": "2025-12-04T10:00:00Z"},
            "user_id": {"S": "user-1"},
            "citations": {"S": json.dumps(citations)},
        }
        
        msg = chat_history_manager._parse_message(item)
        
        assert msg.citations == citations


class TestHelperMethods:
    """Tests for helper methods."""
    
    def test_build_sk(self, chat_history_manager):
        """Test sort key generation."""
        sk = chat_history_manager._build_sk("conv-123", "2025-12-04T10:00:00Z")
        assert sk == "CONV#conv-123#MSG#2025-12-04T10:00:00Z"
    
    def test_generate_message_id(self, chat_history_manager):
        """Test message ID generation."""
        msg_id = chat_history_manager._generate_message_id()
        assert msg_id.startswith("msg-")
        assert len(msg_id) == 16  # "msg-" + 12 hex chars
    
    def test_serialize_deserialize_json(self, chat_history_manager):
        """Test JSON serialization/deserialization."""
        data = {"key": "value", "list": [1, 2, 3]}
        
        serialized = chat_history_manager._serialize_json(data)
        deserialized = chat_history_manager._deserialize_json(serialized)
        
        assert deserialized == data
