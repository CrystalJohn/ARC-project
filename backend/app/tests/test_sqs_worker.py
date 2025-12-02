"""
Unit tests for SQS Worker service.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from app.services.sqs_worker import (
    SQSWorker,
    ProcessingResult,
    ProcessingStatus,
    process_single_document
)
from app.services.pdf_detector import PDFType


class TestSQSWorkerInit:
    """Tests for SQSWorker initialization."""
    
    def test_init_with_required_params(self):
        """Test initialization with required parameters."""
        with patch('boto3.client'):
            worker = SQSWorker(
                queue_url="https://sqs.ap-southeast-1.amazonaws.com/123/test-queue",
                documents_bucket="test-bucket"
            )
            assert worker.queue_url == "https://sqs.ap-southeast-1.amazonaws.com/123/test-queue"
            assert worker.documents_bucket == "test-bucket"
            assert worker.region == "ap-southeast-1"
    
    def test_init_with_callbacks(self):
        """Test initialization with callbacks."""
        embed_fn = Mock()
        store_fn = Mock()
        status_fn = Mock()
        
        with patch('boto3.client'):
            worker = SQSWorker(
                queue_url="https://sqs.example.com/queue",
                documents_bucket="bucket",
                embeddings_callback=embed_fn,
                store_vectors_callback=store_fn,
                update_status_callback=status_fn
            )
            assert worker.embeddings_callback == embed_fn
            assert worker.store_vectors_callback == store_fn
            assert worker.update_status_callback == status_fn


class TestParseS3Event:
    """Tests for S3 event parsing."""
    
    def test_parse_valid_s3_event(self):
        """Test parsing valid S3 event."""
        with patch('boto3.client'):
            worker = SQSWorker(queue_url="url", documents_bucket="bucket")
            
            event = {
                "Records": [{
                    "s3": {
                        "bucket": {"name": "my-bucket"},
                        "object": {"key": "uploads/doc123.pdf", "size": 1024}
                    },
                    "eventTime": "2025-12-02T00:00:00Z"
                }]
            }
            
            result = worker._parse_s3_event(event)
            
            assert result is not None
            assert result['bucket'] == "my-bucket"
            assert result['key'] == "uploads/doc123.pdf"
            assert result['size'] == 1024
    
    def test_parse_sns_wrapped_event(self):
        """Test parsing SNS-wrapped S3 event."""
        with patch('boto3.client'):
            worker = SQSWorker(queue_url="url", documents_bucket="bucket")
            
            inner_event = {
                "Records": [{
                    "s3": {
                        "bucket": {"name": "my-bucket"},
                        "object": {"key": "doc.pdf"}
                    }
                }]
            }
            
            sns_wrapped = {
                "Message": json.dumps(inner_event)
            }
            
            result = worker._parse_s3_event(sns_wrapped)
            
            assert result is not None
            assert result['bucket'] == "my-bucket"
    
    def test_parse_invalid_event(self):
        """Test parsing invalid event returns None."""
        with patch('boto3.client'):
            worker = SQSWorker(queue_url="url", documents_bucket="bucket")
            
            result = worker._parse_s3_event({"invalid": "data"})
            assert result is None
    
    def test_parse_empty_records(self):
        """Test parsing event with empty Records."""
        with patch('boto3.client'):
            worker = SQSWorker(queue_url="url", documents_bucket="bucket")
            
            result = worker._parse_s3_event({"Records": []})
            assert result is None


class TestExtractDocumentId:
    """Tests for document ID extraction."""
    
    def test_extract_from_simple_key(self):
        """Test extracting ID from simple key."""
        with patch('boto3.client'):
            worker = SQSWorker(queue_url="url", documents_bucket="bucket")
            
            assert worker._extract_document_id("document.pdf") == "document"
    
    def test_extract_from_path_key(self):
        """Test extracting ID from path key."""
        with patch('boto3.client'):
            worker = SQSWorker(queue_url="url", documents_bucket="bucket")
            
            assert worker._extract_document_id("uploads/2025/doc123.pdf") == "doc123"
    
    def test_extract_with_multiple_dots(self):
        """Test extracting ID from key with multiple dots."""
        with patch('boto3.client'):
            worker = SQSWorker(queue_url="url", documents_bucket="bucket")
            
            assert worker._extract_document_id("my.document.name.pdf") == "my.document.name"


class TestProcessDocument:
    """Tests for document processing."""
    
    def test_process_digital_pdf_success(self):
        """Test successful processing of digital PDF."""
        with patch('boto3.client'):
            worker = SQSWorker(queue_url="url", documents_bucket="bucket")
            
            # Mock S3 download
            worker._download_from_s3 = Mock(return_value=b"fake pdf content")
            
            # Mock PDF detection and extraction
            with patch('app.services.sqs_worker.detect_pdf_type', return_value=PDFType.DIGITAL):
                mock_content = Mock()
                mock_content.full_text = "This is extracted text " * 100
                mock_content.total_chars = 2400
                mock_content.total_pages = 5
                mock_content.metadata = {}
                
                with patch('app.services.sqs_worker.extract_text_from_pdf', return_value=mock_content):
                    with patch('app.services.sqs_worker.chunk_text') as mock_chunk:
                        mock_chunk.return_value = [Mock(text="chunk1"), Mock(text="chunk2")]
                        
                        result = worker._process_document("bucket", "doc.pdf", "doc")
                        
                        assert result.status == ProcessingStatus.COMPLETED
                        assert result.chunks_count == 2
                        assert result.document_id == "doc"
    
    def test_process_scanned_pdf_skipped(self):
        """Test scanned PDF is skipped."""
        with patch('boto3.client'):
            worker = SQSWorker(queue_url="url", documents_bucket="bucket")
            worker._download_from_s3 = Mock(return_value=b"fake pdf")
            
            with patch('app.services.sqs_worker.detect_pdf_type', return_value=PDFType.SCANNED):
                result = worker._process_document("bucket", "scan.pdf", "scan")
                
                assert result.status == ProcessingStatus.SKIPPED
                assert "Textract" in result.error_message
    
    def test_process_unknown_pdf_failed(self):
        """Test unknown PDF type fails."""
        with patch('boto3.client'):
            worker = SQSWorker(queue_url="url", documents_bucket="bucket")
            worker._download_from_s3 = Mock(return_value=b"fake pdf")
            
            with patch('app.services.sqs_worker.detect_pdf_type', return_value=PDFType.UNKNOWN):
                result = worker._process_document("bucket", "bad.pdf", "bad")
                
                assert result.status == ProcessingStatus.FAILED
    
    def test_process_download_failure(self):
        """Test handling of S3 download failure."""
        with patch('boto3.client'):
            worker = SQSWorker(queue_url="url", documents_bucket="bucket")
            worker._download_from_s3 = Mock(return_value=None)
            
            result = worker._process_document("bucket", "missing.pdf", "missing")
            
            assert result.status == ProcessingStatus.FAILED
            assert "download" in result.error_message.lower()
    
    def test_process_no_text_extracted(self):
        """Test handling when no text is extracted."""
        with patch('boto3.client'):
            worker = SQSWorker(queue_url="url", documents_bucket="bucket")
            worker._download_from_s3 = Mock(return_value=b"fake pdf")
            
            with patch('app.services.sqs_worker.detect_pdf_type', return_value=PDFType.DIGITAL):
                mock_content = Mock()
                mock_content.full_text = ""
                
                with patch('app.services.sqs_worker.extract_text_from_pdf', return_value=mock_content):
                    result = worker._process_document("bucket", "empty.pdf", "empty")
                    
                    assert result.status == ProcessingStatus.FAILED
                    assert "No text" in result.error_message


class TestCallbacks:
    """Tests for callback functionality."""
    
    def test_embeddings_callback_called(self):
        """Test embeddings callback is called for each chunk."""
        embed_fn = Mock(return_value=[0.1, 0.2, 0.3])
        
        with patch('boto3.client'):
            worker = SQSWorker(
                queue_url="url",
                documents_bucket="bucket",
                embeddings_callback=embed_fn
            )
            worker._download_from_s3 = Mock(return_value=b"fake pdf")
            
            with patch('app.services.sqs_worker.detect_pdf_type', return_value=PDFType.DIGITAL):
                mock_content = Mock()
                mock_content.full_text = "text " * 100
                mock_content.total_chars = 500
                mock_content.total_pages = 1
                mock_content.metadata = {}
                
                with patch('app.services.sqs_worker.extract_text_from_pdf', return_value=mock_content):
                    mock_chunks = [Mock(text="chunk1"), Mock(text="chunk2")]
                    with patch('app.services.sqs_worker.chunk_text', return_value=mock_chunks):
                        worker._process_document("bucket", "doc.pdf", "doc")
                        
                        assert embed_fn.call_count == 2
    
    def test_store_vectors_callback_called(self):
        """Test store vectors callback is called."""
        embed_fn = Mock(return_value=[0.1, 0.2])
        store_fn = Mock()
        
        with patch('boto3.client'):
            worker = SQSWorker(
                queue_url="url",
                documents_bucket="bucket",
                embeddings_callback=embed_fn,
                store_vectors_callback=store_fn
            )
            worker._download_from_s3 = Mock(return_value=b"fake pdf")
            
            with patch('app.services.sqs_worker.detect_pdf_type', return_value=PDFType.DIGITAL):
                mock_content = Mock()
                mock_content.full_text = "text"
                mock_content.total_chars = 4
                mock_content.total_pages = 1
                mock_content.metadata = {}
                
                with patch('app.services.sqs_worker.extract_text_from_pdf', return_value=mock_content):
                    with patch('app.services.sqs_worker.chunk_text', return_value=[Mock(text="c1")]):
                        worker._process_document("bucket", "doc.pdf", "doc")
                        
                        store_fn.assert_called_once()
    
    def test_update_status_callback_called(self):
        """Test update status callback is called."""
        status_fn = Mock()
        
        with patch('boto3.client'):
            worker = SQSWorker(
                queue_url="url",
                documents_bucket="bucket",
                update_status_callback=status_fn
            )
            
            worker._update_status("doc123", ProcessingStatus.COMPLETED, {"key": "value"})
            
            status_fn.assert_called_once_with("doc123", "completed", {"key": "value"})


class TestWorkerLoop:
    """Tests for worker loop."""
    
    def test_stop_worker(self):
        """Test worker can be stopped."""
        with patch('boto3.client'):
            worker = SQSWorker(queue_url="url", documents_bucket="bucket")
            worker.running = True
            
            worker.stop()
            
            assert worker.running is False
    
    def test_worker_initial_state(self):
        """Test worker initial state."""
        with patch('boto3.client'):
            worker = SQSWorker(queue_url="url", documents_bucket="bucket")
            
            assert worker.running is False
            assert worker.processed_count == 0
            assert worker.error_count == 0


class TestProcessSingleDocument:
    """Tests for process_single_document helper."""
    
    def test_process_single_document(self):
        """Test processing single document without SQS."""
        with patch('boto3.client'):
            with patch.object(SQSWorker, '_process_document') as mock_process:
                mock_process.return_value = ProcessingResult(
                    document_id="test",
                    status=ProcessingStatus.COMPLETED,
                    chunks_count=5,
                    total_chars=1000
                )
                
                result = process_single_document("bucket", "test.pdf")
                
                assert result.status == ProcessingStatus.COMPLETED
                assert result.document_id == "test"
