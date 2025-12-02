"""
Unit tests for Admin API endpoints.

Tests:
- POST /api/admin/upload
- GET /api/admin/documents
- GET /api/admin/documents/{doc_id}

Requirements: 10.1, 10.2, 10.3, 10.4, 11.1, 11.2, 11.3
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from io import BytesIO

from backend.app.main import app
from backend.app.services.document_status_manager import DocumentStatus


client = TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestUploadEndpoint:
    """Tests for POST /api/admin/upload endpoint."""
    
    @patch("backend.app.api.admin.get_s3_client")
    @patch("backend.app.api.admin.get_sqs_client")
    @patch("backend.app.api.admin.get_status_manager")
    def test_upload_pdf_success(self, mock_status_mgr, mock_sqs, mock_s3):
        """Test successful PDF upload."""
        # Setup mocks
        mock_s3.return_value.put_object = MagicMock()
        mock_sqs.return_value.send_message = MagicMock()
        mock_status_mgr.return_value.create_document = MagicMock(return_value={
            "doc_id": "test-123",
            "status": "UPLOADED"
        })
        
        # Create test PDF file
        pdf_content = b"%PDF-1.4 test content"
        files = {"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")}
        
        response = client.post("/api/admin/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "doc_id" in data
        assert data["filename"] == "test.pdf"
        assert data["status"] == "UPLOADED"
        
        # Verify S3 upload was called
        mock_s3.return_value.put_object.assert_called_once()
        
        # Verify DynamoDB record was created
        mock_status_mgr.return_value.create_document.assert_called_once()
        
        # Verify SQS message was sent
        mock_sqs.return_value.send_message.assert_called_once()
    
    def test_upload_non_pdf_rejected(self):
        """Test that non-PDF files are rejected."""
        files = {"file": ("test.txt", BytesIO(b"text content"), "text/plain")}
        
        response = client.post("/api/admin/upload", files=files)
        
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]
    
    def test_upload_empty_file_rejected(self):
        """Test that empty files are rejected."""
        files = {"file": ("empty.pdf", BytesIO(b""), "application/pdf")}
        
        response = client.post("/api/admin/upload", files=files)
        
        assert response.status_code == 400
        assert "Empty" in response.json()["detail"]


class TestListDocumentsEndpoint:
    """Tests for GET /api/admin/documents endpoint."""
    
    @patch("backend.app.api.admin.get_status_manager")
    def test_list_documents_success(self, mock_status_mgr):
        """Test listing documents with default pagination."""
        mock_status_mgr.return_value.list_documents = MagicMock(return_value={
            "items": [
                {
                    "doc_id": "doc-1",
                    "filename": "paper1.pdf",
                    "status": "EMBEDDING_DONE",
                    "uploaded_at": "2025-12-02T10:00:00Z",
                    "uploaded_by": "admin",
                    "page_count": 10,
                    "chunk_count": 25
                },
                {
                    "doc_id": "doc-2",
                    "filename": "paper2.pdf",
                    "status": "UPLOADED",
                    "uploaded_at": "2025-12-02T09:00:00Z",
                    "uploaded_by": "admin"
                }
            ],
            "last_evaluated_key": None
        })
        
        response = client.get("/api/admin/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 20
    
    @patch("backend.app.api.admin.get_status_manager")
    def test_list_documents_with_status_filter(self, mock_status_mgr):
        """Test filtering documents by status."""
        mock_status_mgr.return_value.list_documents = MagicMock(return_value={
            "items": [
                {
                    "doc_id": "doc-1",
                    "filename": "paper1.pdf",
                    "status": "FAILED",
                    "uploaded_at": "2025-12-02T10:00:00Z",
                    "uploaded_by": "admin",
                    "error_message": "Processing failed"
                }
            ],
            "last_evaluated_key": None
        })
        
        response = client.get("/api/admin/documents?status=FAILED")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "FAILED"
        
        # Verify filter was passed
        mock_status_mgr.return_value.list_documents.assert_called_once()
        call_args = mock_status_mgr.return_value.list_documents.call_args
        assert call_args.kwargs["status"] == DocumentStatus.FAILED
    
    def test_list_documents_invalid_status(self):
        """Test that invalid status returns 400."""
        response = client.get("/api/admin/documents?status=INVALID")
        
        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]
    
    @patch("backend.app.api.admin.get_status_manager")
    def test_list_documents_pagination(self, mock_status_mgr):
        """Test pagination parameters."""
        mock_status_mgr.return_value.list_documents = MagicMock(return_value={
            "items": [],
            "last_evaluated_key": None
        })
        
        response = client.get("/api/admin/documents?page=2&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10


class TestGetDocumentEndpoint:
    """Tests for GET /api/admin/documents/{doc_id} endpoint."""
    
    @patch("backend.app.api.admin.get_status_manager")
    def test_get_document_success(self, mock_status_mgr):
        """Test getting a single document."""
        mock_status_mgr.return_value.get_document = MagicMock(return_value={
            "doc_id": "doc-123",
            "filename": "paper.pdf",
            "status": "EMBEDDING_DONE",
            "uploaded_at": "2025-12-02T10:00:00Z",
            "uploaded_by": "admin",
            "page_count": 15,
            "chunk_count": 42
        })
        
        response = client.get("/api/admin/documents/doc-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["doc_id"] == "doc-123"
        assert data["page_count"] == 15
        assert data["chunk_count"] == 42
    
    @patch("backend.app.api.admin.get_status_manager")
    def test_get_document_not_found(self, mock_status_mgr):
        """Test 404 when document not found."""
        mock_status_mgr.return_value.get_document = MagicMock(return_value=None)
        
        response = client.get("/api/admin/documents/nonexistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
