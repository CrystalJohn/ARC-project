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


# ============ TEXTRACT EXTRACTOR TESTS (Task #16) ============

from app.services.pdf_extractor import TextractExtractor, extract_pdf_auto


class TestTextractExtractor:
    """Tests for TextractExtractor class."""
    
    def test_init(self):
        """Test initialization."""
        with patch('boto3.client') as mock_boto:
            extractor = TextractExtractor(region="ap-southeast-1")
            mock_boto.assert_called_with("textract", region_name="ap-southeast-1")
            assert extractor.region == "ap-southeast-1"
    
    def test_extract_from_bytes_detect_text(self):
        """Test sync text detection from bytes."""
        mock_response = {
            "Blocks": [
                {"BlockType": "PAGE", "Id": "page1", "Page": 1},
                {"BlockType": "LINE", "Id": "line1", "Text": "Hello World", "Page": 1},
                {"BlockType": "LINE", "Id": "line2", "Text": "Second line", "Page": 1}
            ]
        }
        
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.detect_document_text.return_value = mock_response
            mock_boto.return_value = mock_client
            
            extractor = TextractExtractor()
            result = extractor.extract_from_bytes(b"fake pdf", extract_tables=False)
            
            assert result.extraction_method == "textract"
            assert result.total_pages == 1
            assert "Hello World" in result.full_text
            assert "Second line" in result.full_text
    
    def test_extract_from_bytes_analyze_document(self):
        """Test sync document analysis with tables."""
        mock_response = {
            "Blocks": [
                {"BlockType": "PAGE", "Id": "page1", "Page": 1},
                {"BlockType": "LINE", "Id": "line1", "Text": "Document text", "Page": 1},
                {
                    "BlockType": "TABLE", "Id": "table1", "Page": 1,
                    "Relationships": [{"Type": "CHILD", "Ids": ["cell1", "cell2"]}]
                },
                {
                    "BlockType": "CELL", "Id": "cell1", "RowIndex": 1, "ColumnIndex": 1,
                    "Relationships": [{"Type": "CHILD", "Ids": ["word1"]}]
                },
                {
                    "BlockType": "CELL", "Id": "cell2", "RowIndex": 1, "ColumnIndex": 2,
                    "Relationships": [{"Type": "CHILD", "Ids": ["word2"]}]
                },
                {"BlockType": "WORD", "Id": "word1", "Text": "Cell1"},
                {"BlockType": "WORD", "Id": "word2", "Text": "Cell2"}
            ]
        }
        
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.analyze_document.return_value = mock_response
            mock_boto.return_value = mock_client
            
            extractor = TextractExtractor()
            result = extractor.extract_from_bytes(b"fake pdf", extract_tables=True)
            
            assert result.extraction_method == "textract"
            assert "Document text" in result.full_text
            assert len(result.pages) == 1
            assert len(result.pages[0].tables) == 1
            assert result.pages[0].tables[0][0] == ["Cell1", "Cell2"]
    
    def test_extract_from_bytes_error(self):
        """Test error handling."""
        from botocore.exceptions import ClientError
        
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.detect_document_text.side_effect = ClientError(
                {"Error": {"Code": "InvalidParameterException", "Message": "Invalid"}},
                "DetectDocumentText"
            )
            mock_boto.return_value = mock_client
            
            extractor = TextractExtractor()
            result = extractor.extract_from_bytes(b"fake pdf", extract_tables=False)
            
            assert len(result.errors) > 0
            assert "InvalidParameterException" in result.errors[0]
    
    def test_extract_multipage(self):
        """Test multi-page extraction."""
        mock_response = {
            "Blocks": [
                {"BlockType": "LINE", "Id": "line1", "Text": "Page 1 text", "Page": 1},
                {"BlockType": "LINE", "Id": "line2", "Text": "Page 2 text", "Page": 2},
                {"BlockType": "LINE", "Id": "line3", "Text": "Page 3 text", "Page": 3}
            ]
        }
        
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.detect_document_text.return_value = mock_response
            mock_boto.return_value = mock_client
            
            extractor = TextractExtractor()
            result = extractor.extract_from_bytes(b"fake pdf", extract_tables=False)
            
            assert result.total_pages == 3
            assert len(result.pages) == 3
            assert result.pages[0].page_number == 1
            assert result.pages[1].page_number == 2
            assert result.pages[2].page_number == 3


class TestExtractFromS3:
    """Tests for S3 extraction with async API."""
    
    def test_start_async_job(self):
        """Test starting async job."""
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.start_document_analysis.return_value = {"JobId": "job123"}
            mock_boto.return_value = mock_client
            
            extractor = TextractExtractor()
            result = extractor.extract_from_s3(
                "test-bucket", "test.pdf",
                wait_for_completion=False
            )
            
            assert result.metadata.get("job_id") == "job123"
            assert result.metadata.get("status") == "IN_PROGRESS"
    
    def test_wait_for_completion_success(self):
        """Test waiting for job completion."""
        mock_response = {
            "JobStatus": "SUCCEEDED",
            "Blocks": [
                {"BlockType": "LINE", "Id": "line1", "Text": "Extracted text", "Page": 1}
            ]
        }
        
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.start_document_analysis.return_value = {"JobId": "job123"}
            mock_client.get_document_analysis.return_value = mock_response
            mock_boto.return_value = mock_client
            
            extractor = TextractExtractor()
            result = extractor.extract_from_s3(
                "test-bucket", "test.pdf",
                wait_for_completion=True,
                poll_interval=0.1
            )
            
            assert "Extracted text" in result.full_text
            assert len(result.errors) == 0
    
    def test_wait_for_completion_failed(self):
        """Test job failure handling."""
        mock_response = {
            "JobStatus": "FAILED",
            "StatusMessage": "Document processing failed"
        }
        
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_client.start_document_analysis.return_value = {"JobId": "job123"}
            mock_client.get_document_analysis.return_value = mock_response
            mock_boto.return_value = mock_client
            
            extractor = TextractExtractor()
            result = extractor.extract_from_s3(
                "test-bucket", "test.pdf",
                wait_for_completion=True,
                poll_interval=0.1
            )
            
            assert len(result.errors) > 0
            assert "failed" in result.errors[0].lower()


class TestExtractPdfAuto:
    """Tests for auto PDF extraction."""
    
    def test_digital_pdf_uses_pypdf2(self):
        """Digital PDF should use PyPDF2."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "A" * 100  # 100 chars per page
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = None
        
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=mock_reader):
            result = extract_pdf_auto("test.pdf", use_textract_for_scanned=True)
            
            assert result.extraction_method == "pypdf2"
    
    def test_scanned_pdf_uses_textract(self):
        """Scanned PDF (low text) should use Textract."""
        # PyPDF2 returns very little text
        mock_page = Mock()
        mock_page.extract_text.return_value = "A" * 10  # Only 10 chars
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = None
        
        # Textract response
        textract_response = {
            "Blocks": [
                {"BlockType": "LINE", "Id": "line1", "Text": "Scanned text", "Page": 1}
            ]
        }
        
        # Use bytes input to avoid file open
        pdf_bytes = b"fake pdf content"
        
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=mock_reader):
            with patch('boto3.client') as mock_boto:
                mock_client = Mock()
                mock_client.analyze_document.return_value = textract_response
                mock_boto.return_value = mock_client
                
                result = extract_pdf_auto(pdf_bytes, use_textract_for_scanned=True)
                
                assert result.extraction_method == "textract"
                assert "Scanned text" in result.full_text
    
    def test_scanned_pdf_without_textract(self):
        """Scanned PDF without Textract fallback."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "A" * 10
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_reader.metadata = None
        
        with patch('app.services.pdf_extractor._get_pdf_reader', return_value=mock_reader):
            result = extract_pdf_auto("test.pdf", use_textract_for_scanned=False)
            
            assert result.extraction_method == "pypdf2"
