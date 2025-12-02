"""
Unit tests for PDF detector service.
"""

import io
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.services.pdf_detector import (
    detect_pdf_type,
    get_pdf_info,
    is_digital_pdf,
    is_scanned_pdf,
    PDFType,
    MIN_CHARS_PER_PAGE
)


class TestDetectPDFType:
    """Tests for detect_pdf_type function."""
    
    def test_digital_pdf_with_text(self):
        """PDF với nhiều text nên được detect là digital."""
        # Mock PdfReader với text
        mock_page = Mock()
        mock_page.extract_text.return_value = "A" * 100  # 100 chars
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page, mock_page, mock_page]
        
        with patch('app.services.pdf_detector._get_pdf_reader', return_value=mock_reader):
            result = detect_pdf_type("test.pdf")
            assert result == PDFType.DIGITAL
    
    def test_scanned_pdf_no_text(self):
        """PDF không có text nên được detect là scanned."""
        mock_page = Mock()
        mock_page.extract_text.return_value = ""  # No text
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        
        with patch('app.services.pdf_detector._get_pdf_reader', return_value=mock_reader):
            result = detect_pdf_type("test.pdf")
            assert result == PDFType.SCANNED
    
    def test_scanned_pdf_little_text(self):
        """PDF với ít text (< threshold) nên được detect là scanned."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "ABC"  # Only 3 chars
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        
        with patch('app.services.pdf_detector._get_pdf_reader', return_value=mock_reader):
            result = detect_pdf_type("test.pdf")
            assert result == PDFType.SCANNED
    
    def test_threshold_boundary_below(self):
        """PDF với chars = threshold - 1 nên là scanned."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "A" * (MIN_CHARS_PER_PAGE - 1)
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        
        with patch('app.services.pdf_detector._get_pdf_reader', return_value=mock_reader):
            result = detect_pdf_type("test.pdf")
            assert result == PDFType.SCANNED
    
    def test_threshold_boundary_at(self):
        """PDF với chars = threshold nên là digital."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "A" * MIN_CHARS_PER_PAGE
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        
        with patch('app.services.pdf_detector._get_pdf_reader', return_value=mock_reader):
            result = detect_pdf_type("test.pdf")
            assert result == PDFType.DIGITAL
    
    def test_empty_pdf(self):
        """PDF không có trang nên return UNKNOWN."""
        mock_reader = Mock()
        mock_reader.pages = []
        
        with patch('app.services.pdf_detector._get_pdf_reader', return_value=mock_reader):
            result = detect_pdf_type("test.pdf")
            assert result == PDFType.UNKNOWN
    
    def test_reader_error(self):
        """Khi không đọc được PDF nên return UNKNOWN."""
        with patch('app.services.pdf_detector._get_pdf_reader', return_value=None):
            result = detect_pdf_type("test.pdf")
            assert result == PDFType.UNKNOWN
    
    def test_custom_threshold(self):
        """Test với custom threshold."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "A" * 30  # 30 chars
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        
        with patch('app.services.pdf_detector._get_pdf_reader', return_value=mock_reader):
            # Default threshold (50) -> scanned
            result1 = detect_pdf_type("test.pdf")
            assert result1 == PDFType.SCANNED
            
            # Lower threshold (20) -> digital
            result2 = detect_pdf_type("test.pdf", min_chars_per_page=20)
            assert result2 == PDFType.DIGITAL


class TestGetPDFInfo:
    """Tests for get_pdf_info function."""
    
    def test_digital_pdf_info(self):
        """Test lấy info từ digital PDF."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "Sample text content " * 10
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page, mock_page]
        
        with patch('app.services.pdf_detector._get_pdf_reader', return_value=mock_reader):
            info = get_pdf_info("test.pdf")
            
            assert info["pdf_type"] == PDFType.DIGITAL
            assert info["total_pages"] == 2
            assert info["avg_chars_per_page"] > MIN_CHARS_PER_PAGE
            assert "Sample text" in info["sample_text"]
            assert info["error"] is None
    
    def test_scanned_pdf_info(self):
        """Test lấy info từ scanned PDF."""
        mock_page = Mock()
        mock_page.extract_text.return_value = ""
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        
        with patch('app.services.pdf_detector._get_pdf_reader', return_value=mock_reader):
            info = get_pdf_info("test.pdf")
            
            assert info["pdf_type"] == PDFType.SCANNED
            assert info["total_pages"] == 1
            assert info["avg_chars_per_page"] == 0
    
    def test_error_handling(self):
        """Test error handling khi không đọc được PDF."""
        with patch('app.services.pdf_detector._get_pdf_reader', return_value=None):
            info = get_pdf_info("test.pdf")
            
            assert info["pdf_type"] == PDFType.UNKNOWN
            assert info["error"] is not None


class TestConvenienceFunctions:
    """Tests for is_digital_pdf and is_scanned_pdf."""
    
    def test_is_digital_pdf_true(self):
        """is_digital_pdf returns True for digital PDF."""
        with patch('app.services.pdf_detector.detect_pdf_type', return_value=PDFType.DIGITAL):
            assert is_digital_pdf("test.pdf") is True
    
    def test_is_digital_pdf_false(self):
        """is_digital_pdf returns False for scanned PDF."""
        with patch('app.services.pdf_detector.detect_pdf_type', return_value=PDFType.SCANNED):
            assert is_digital_pdf("test.pdf") is False
    
    def test_is_scanned_pdf_true(self):
        """is_scanned_pdf returns True for scanned PDF."""
        with patch('app.services.pdf_detector.detect_pdf_type', return_value=PDFType.SCANNED):
            assert is_scanned_pdf("test.pdf") is True
    
    def test_is_scanned_pdf_false(self):
        """is_scanned_pdf returns False for digital PDF."""
        with patch('app.services.pdf_detector.detect_pdf_type', return_value=PDFType.DIGITAL):
            assert is_scanned_pdf("test.pdf") is False


class TestInputTypes:
    """Tests for different input types."""
    
    def test_bytes_input(self):
        """Test với bytes input."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "A" * 100
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        
        with patch('app.services.pdf_detector._get_pdf_reader', return_value=mock_reader):
            result = detect_pdf_type(b"fake pdf bytes")
            assert result == PDFType.DIGITAL
    
    def test_bytesio_input(self):
        """Test với BytesIO input."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "A" * 100
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        
        with patch('app.services.pdf_detector._get_pdf_reader', return_value=mock_reader):
            result = detect_pdf_type(io.BytesIO(b"fake pdf bytes"))
            assert result == PDFType.DIGITAL
