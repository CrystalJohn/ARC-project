"""
Unit tests for DocumentStatusManager.

Tests document status tracking in DynamoDB including:
- create_document() with UPLOADED status
- update_status() for state transitions
- get_document() retrieval
- list_documents() with filtering

Requirements: 9.1, 9.2, 9.3, 9.4
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from backend.app.services.document_status_manager import (
    DocumentStatusManager,
    DocumentStatus,
    VALID_TRANSITIONS
)


@pytest.fixture
def mock_dynamodb_client():
    """Create a mock DynamoDB client."""
    return MagicMock()


@pytest.fixture
def status_manager(mock_dynamodb_client):
    """Create a DocumentStatusManager with mock client."""
    return DocumentStatusManager(
        table_name="test-table",
        dynamodb_client=mock_dynamodb_client
    )


class TestCreateDocument:
    """Tests for create_document method."""
    
    def test_create_document_success(self, status_manager, mock_dynamodb_client):
        """Test successful document creation with UPLOADED status."""
        doc_id = "test-doc-123"
        filename = "paper.pdf"
        uploaded_by = "user-456"
        
        result = status_manager.create_document(doc_id, filename, uploaded_by)
        
        # Verify put_item was called
        mock_dynamodb_client.put_item.assert_called_once()
        call_args = mock_dynamodb_client.put_item.call_args
        
        # Check table name
        assert call_args.kwargs["TableName"] == "test-table"
        
        # Check item structure
        item = call_args.kwargs["Item"]
        assert item["doc_id"]["S"] == doc_id
        assert item["sk"]["S"] == "METADATA"
        assert item["status"]["S"] == "UPLOADED"
        assert item["filename"]["S"] == filename
        assert item["uploaded_by"]["S"] == uploaded_by
        assert "uploaded_at" in item
        
        # Check return value
        assert result["doc_id"] == doc_id
        assert result["status"] == "UPLOADED"
        assert result["filename"] == filename
        assert result["uploaded_by"] == uploaded_by
    
    def test_create_document_with_condition(self, status_manager, mock_dynamodb_client):
        """Test that create uses condition to prevent duplicates."""
        status_manager.create_document("doc-1", "file.pdf", "user-1")
        
        call_args = mock_dynamodb_client.put_item.call_args
        assert call_args.kwargs["ConditionExpression"] == "attribute_not_exists(doc_id)"


class TestUpdateStatus:
    """Tests for update_status method."""
    
    def test_update_to_idp_running(self, status_manager, mock_dynamodb_client):
        """Test updating status to IDP_RUNNING."""
        mock_dynamodb_client.update_item.return_value = {
            "Attributes": {
                "doc_id": {"S": "doc-123"},
                "sk": {"S": "METADATA"},
                "status": {"S": "IDP_RUNNING"},
                "updated_at": {"S": "2024-01-01T00:00:00Z"}
            }
        }
        
        result = status_manager.update_status("doc-123", DocumentStatus.IDP_RUNNING)
        
        mock_dynamodb_client.update_item.assert_called_once()
        call_args = mock_dynamodb_client.update_item.call_args
        
        assert call_args.kwargs["Key"]["doc_id"]["S"] == "doc-123"
        assert ":new_status" in call_args.kwargs["ExpressionAttributeValues"]
        assert call_args.kwargs["ExpressionAttributeValues"][":new_status"]["S"] == "IDP_RUNNING"
        
        assert result["status"] == "IDP_RUNNING"
    
    def test_update_to_embedding_done_with_counts(self, status_manager, mock_dynamodb_client):
        """Test updating to EMBEDDING_DONE with page and chunk counts."""
        mock_dynamodb_client.update_item.return_value = {
            "Attributes": {
                "doc_id": {"S": "doc-123"},
                "status": {"S": "EMBEDDING_DONE"},
                "page_count": {"N": "10"},
                "chunk_count": {"N": "25"}
            }
        }
        
        result = status_manager.update_status(
            "doc-123",
            DocumentStatus.EMBEDDING_DONE,
            page_count=10,
            chunk_count=25
        )
        
        call_args = mock_dynamodb_client.update_item.call_args
        expr_values = call_args.kwargs["ExpressionAttributeValues"]
        
        assert expr_values[":page_count"]["N"] == "10"
        assert expr_values[":chunk_count"]["N"] == "25"
        
        assert result["page_count"] == 10
        assert result["chunk_count"] == 25
    
    def test_update_to_failed_with_error(self, status_manager, mock_dynamodb_client):
        """Test updating to FAILED with error message."""
        error_msg = "PDF extraction failed: corrupted file"
        mock_dynamodb_client.update_item.return_value = {
            "Attributes": {
                "doc_id": {"S": "doc-123"},
                "status": {"S": "FAILED"},
                "error_message": {"S": error_msg}
            }
        }
        
        result = status_manager.update_status(
            "doc-123",
            DocumentStatus.FAILED,
            error_message=error_msg
        )
        
        call_args = mock_dynamodb_client.update_item.call_args
        expr_values = call_args.kwargs["ExpressionAttributeValues"]
        
        assert expr_values[":error_message"]["S"] == error_msg
        assert result["error_message"] == error_msg


class TestGetDocument:
    """Tests for get_document method."""
    
    def test_get_existing_document(self, status_manager, mock_dynamodb_client):
        """Test retrieving an existing document."""
        mock_dynamodb_client.get_item.return_value = {
            "Item": {
                "doc_id": {"S": "doc-123"},
                "sk": {"S": "METADATA"},
                "status": {"S": "UPLOADED"},
                "filename": {"S": "paper.pdf"},
                "uploaded_by": {"S": "user-1"},
                "uploaded_at": {"S": "2024-01-01T00:00:00Z"}
            }
        }
        
        result = status_manager.get_document("doc-123")
        
        assert result is not None
        assert result["doc_id"] == "doc-123"
        assert result["status"] == "UPLOADED"
        assert result["filename"] == "paper.pdf"
    
    def test_get_nonexistent_document(self, status_manager, mock_dynamodb_client):
        """Test retrieving a document that doesn't exist."""
        mock_dynamodb_client.get_item.return_value = {}
        
        result = status_manager.get_document("nonexistent")
        
        assert result is None


class TestListDocuments:
    """Tests for list_documents method."""
    
    def test_list_all_documents(self, status_manager, mock_dynamodb_client):
        """Test listing all documents without filter."""
        mock_dynamodb_client.scan.return_value = {
            "Items": [
                {
                    "doc_id": {"S": "doc-1"},
                    "status": {"S": "UPLOADED"},
                    "filename": {"S": "file1.pdf"}
                },
                {
                    "doc_id": {"S": "doc-2"},
                    "status": {"S": "EMBEDDING_DONE"},
                    "filename": {"S": "file2.pdf"}
                }
            ]
        }
        
        result = status_manager.list_documents()
        
        mock_dynamodb_client.scan.assert_called_once()
        assert len(result["items"]) == 2
        assert result["items"][0]["doc_id"] == "doc-1"
        assert result["items"][1]["doc_id"] == "doc-2"
    
    def test_list_documents_with_status_filter(self, status_manager, mock_dynamodb_client):
        """Test listing documents filtered by status."""
        mock_dynamodb_client.query.return_value = {
            "Items": [
                {
                    "doc_id": {"S": "doc-1"},
                    "status": {"S": "FAILED"},
                    "error_message": {"S": "Error"}
                }
            ]
        }
        
        result = status_manager.list_documents(status=DocumentStatus.FAILED)
        
        mock_dynamodb_client.query.assert_called_once()
        call_args = mock_dynamodb_client.query.call_args
        
        assert call_args.kwargs["IndexName"] == "status-index"
        assert call_args.kwargs["ExpressionAttributeValues"][":status"]["S"] == "FAILED"
        assert len(result["items"]) == 1
    
    def test_list_documents_with_pagination(self, status_manager, mock_dynamodb_client):
        """Test pagination with last_evaluated_key."""
        last_key = {"doc_id": {"S": "doc-10"}, "sk": {"S": "METADATA"}}
        mock_dynamodb_client.scan.return_value = {
            "Items": [],
            "LastEvaluatedKey": last_key
        }
        
        result = status_manager.list_documents(page_size=10)
        
        assert result["last_evaluated_key"] == last_key


class TestDocumentStatusEnum:
    """Tests for DocumentStatus enum."""
    
    def test_status_values(self):
        """Test all status values are defined."""
        assert DocumentStatus.UPLOADED.value == "UPLOADED"
        assert DocumentStatus.IDP_RUNNING.value == "IDP_RUNNING"
        assert DocumentStatus.EMBEDDING_DONE.value == "EMBEDDING_DONE"
        assert DocumentStatus.FAILED.value == "FAILED"
    
    def test_valid_transitions_defined(self):
        """Test valid transitions are properly defined."""
        assert DocumentStatus.IDP_RUNNING in VALID_TRANSITIONS[DocumentStatus.UPLOADED]
        assert DocumentStatus.FAILED in VALID_TRANSITIONS[DocumentStatus.UPLOADED]
        assert DocumentStatus.EMBEDDING_DONE in VALID_TRANSITIONS[DocumentStatus.IDP_RUNNING]
        assert DocumentStatus.FAILED in VALID_TRANSITIONS[DocumentStatus.IDP_RUNNING]
        # Terminal states have no valid transitions
        assert len(VALID_TRANSITIONS[DocumentStatus.EMBEDDING_DONE]) == 0
        assert len(VALID_TRANSITIONS[DocumentStatus.FAILED]) == 0
