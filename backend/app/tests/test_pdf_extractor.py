"""
Unit tests for PDF extractor service.
"""

import io
import pytest
from unittest.mock import Mock, patch

from app.services.pdf_extractor import (
    extract_text_from_pdf,
    extract_text_simple,
    extract_text_by_page,
    get_page_count,
    _clean_text,
    PDFContent,
    PageContent
)


class TestExtractTextFromPDF:
    """Tests for extract_text_from_pdf function."""
    
    def test_extract_single_page(self):
        """Extract text từ PDF 1 trang."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "Hello World"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = None
        
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=mock_reader):
            result = extract_text_from_pdf("test.pdf")
            
            assert result.total_pages == 1
            assert len(result.pages) == 1
            assert result.pages[0].text == "Hello World"
            assert result.full_text == "Hello World"
            assert result.total_chars == 11
            assert len(result.errors) == 0
    
    def test_extract_multi_page(self):
        """Extract text từ PDF nhiều trang."""
        mock_pages = []
        for i in range(3):
            page = Mock()
            page.extract_text.return_value = f"Page {i + 1} content"
            mock_pages.append(page)
        
        mock_reader = Mock()
        mock_reader.pages = mock_pages
        mock_reader.metadata = None
        
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=mock_reader):
            result = extract_text_from_pdf("test.pdf")
            
            assert result.total_pages == 3
            assert len(result.pages) == 3
            assert "Page 1 content" in result.full_text
            assert "Page 2 content" in result.full_text
            assert "Page 3 content" in result.full_text
    
    def test_extract_with_max_pages(self):
        """Extract với giới hạn số trang."""
        mock_pages = [Mock() for _ in range(10)]
        for i, page in enumerate(mock_pages):
            page.extract_text.return_value = f"Page {i + 1}"
        
        mock_reader = Mock()
        mock_reader.pages = mock_pages
        mock_reader.metadata = None
        
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=mock_reader):
            result = extract_text_from_pdf("test.pdf", max_pages=3)
            
            assert result.total_pages == 10  # Total pages in PDF
            assert len(result.pages) == 3    # Only extracted 3
    
    def test_extract_empty_page(self):
        """Handle trang không có text."""
        mock_page = Mock()
        mock_page.extract_text.return_value = ""
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = None
        
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=mock_reader):
            result = extract_text_from_pdf("test.pdf")
            
            assert result.total_pages == 1
            assert result.pages[0].text == ""
            assert result.total_chars == 0
    
    def test_extract_with_none_text(self):
        """Handle khi extract_text trả về None."""
        mock_page = Mock()
        mock_page.extract_text.return_value = None
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = None
        
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=mock_reader):
            result = extract_text_from_pdf("test.pdf")
            
            assert result.pages[0].text == ""
    
    def test_extract_reader_error(self):
        """Handle khi không đọc được PDF."""
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=None):
            result = extract_text_from_pdf("test.pdf")
            
            assert result.total_pages == 0
            assert len(result.errors) > 0
            assert "Cannot read PDF" in result.errors[0]
    
    def test_extract_page_error(self):
        """Handle lỗi khi extract một trang cụ thể."""
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1"
        
        mock_page2 = Mock()
        mock_page2.extract_text.side_effect = Exception("Extraction failed")
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_reader.metadata = None
        
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=mock_reader):
            result = extract_text_from_pdf("test.pdf")
            
            assert len(result.pages) == 2
            assert result.pages[0].text == "Page 1"
            assert result.pages[1].text == ""
            assert len(result.errors) == 1
            assert "page 2" in result.errors[0].lower()


class TestExtractTextSimple:
    """Tests for extract_text_simple function."""
    
    def test_simple_extraction(self):
        """Test simple text extraction."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "Simple text"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = None
        
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=mock_reader):
            result = extract_text_simple("test.pdf")
            assert result == "Simple text"
    
    def test_simple_extraction_error(self):
        """Test simple extraction với lỗi."""
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=None):
            result = extract_text_simple("test.pdf")
            assert result == ""


class TestExtractTextByPage:
    """Tests for extract_text_by_page function."""
    
    def test_by_page_extraction(self):
        """Test extraction theo trang."""
        mock_pages = []
        for i in range(3):
            page = Mock()
            page.extract_text.return_value = f"Page {i + 1}"
            mock_pages.append(page)
        
        mock_reader = Mock()
        mock_reader.pages = mock_pages
        mock_reader.metadata = None
        
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=mock_reader):
            result = extract_text_by_page("test.pdf")
            
            assert len(result) == 3
            assert result[0] == "Page 1"
            assert result[1] == "Page 2"
            assert result[2] == "Page 3"


class TestCleanText:
    """Tests for _clean_text function."""
    
    def test_remove_multiple_spaces(self):
        """Remove multiple spaces."""
        text = "Hello    World"
        assert _clean_text(text) == "Hello World"
    
    def test_remove_multiple_newlines(self):
        """Remove excessive newlines."""
        text = "Para 1\n\n\n\n\nPara 2"
        assert _clean_text(text) == "Para 1\n\nPara 2"
    
    def test_strip_lines(self):
        """Strip whitespace from lines."""
        text = "  Line 1  \n  Line 2  "
        result = _clean_text(text)
        assert "  Line" not in result
    
    def test_fix_ligatures(self):
        """Fix common ligatures."""
        text = "ﬁle ﬂow oﬀer"
        result = _clean_text(text)
        assert "fi" in result
        assert "fl" in result
        assert "ff" in result
    
    def test_remove_null_chars(self):
        """Remove null characters."""
        text = "Hello\x00World"
        assert _clean_text(text) == "HelloWorld"
    
    def test_empty_string(self):
        """Handle empty string."""
        assert _clean_text("") == ""
        assert _clean_text(None) == ""


class TestGetPageCount:
    """Tests for get_page_count function."""
    
    def test_page_count(self):
        """Get correct page count."""
        mock_reader = Mock()
        mock_reader.pages = [Mock(), Mock(), Mock()]
        
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=mock_reader):
            assert get_page_count("test.pdf") == 3
    
    def test_page_count_error(self):
        """Return 0 on error."""
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=None):
            assert get_page_count("test.pdf") == 0


class TestMetadataExtraction:
    """Tests for metadata extraction."""
    
    def test_extract_metadata(self):
        """Extract PDF metadata."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "Content"
        
        mock_metadata = Mock()
        mock_metadata.get.side_effect = lambda key, default="": {
            "/Title": "Test Document",
            "/Author": "Test Author"
        }.get(key, default)
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = mock_metadata
        
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=mock_reader):
            result = extract_text_from_pdf("test.pdf")
            
            assert result.metadata.get("title") == "Test Document"
            assert result.metadata.get("author") == "Test Author"
