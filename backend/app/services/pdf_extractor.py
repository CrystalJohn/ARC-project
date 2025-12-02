"""
Task #15: PyPDF2 Text Extraction for Digital PDFs

Extract text từ digital PDF sử dụng PyPDF2.
Xử lý multi-page, encoding issues, và metadata.
"""

import io
import re
from typing import Union, List, Optional
from pathlib import Path
from dataclasses import dataclass

import PyPDF2


@dataclass
class PageContent:
    """Content của một trang PDF."""
    page_number: int
    text: str
    char_count: int


@dataclass
class PDFContent:
    """Kết quả extract từ PDF."""
    total_pages: int
    pages: List[PageContent]
    full_text: str
    total_chars: int
    metadata: dict
    errors: List[str]


def extract_text_from_pdf(
    file_input: Union[str, Path, bytes, io.BytesIO],
    max_pages: Optional[int] = None,
    clean_text: bool = True
) -> PDFContent:
    """
    Extract text từ digital PDF.
    
    Args:
        file_input: Đường dẫn file, bytes, hoặc BytesIO
        max_pages: Giới hạn số trang extract (None = tất cả)
        clean_text: Có clean text không (remove extra whitespace)
        
    Returns:
        PDFContent với text từ tất cả các trang
    """
    pages = []
    errors = []
    metadata = {}
    
    try:
        reader = _get_pdf_reader(file_input)
        
        if reader is None:
            return PDFContent(
                total_pages=0,
                pages=[],
                full_text="",
                total_chars=0,
                metadata={},
                errors=["Cannot read PDF file"]
            )
        
        # Extract metadata
        metadata = _extract_metadata(reader)
        
        total_pages = len(reader.pages)
        pages_to_extract = total_pages if max_pages is None else min(max_pages, total_pages)
        
        for i in range(pages_to_extract):
            try:
                page = reader.pages[i]
                text = page.extract_text() or ""
                
                if clean_text:
                    text = _clean_text(text)
                
                pages.append(PageContent(
                    page_number=i + 1,
                    text=text,
                    char_count=len(text)
                ))
            except Exception as e:
                errors.append(f"Error extracting page {i + 1}: {str(e)}")
                pages.append(PageContent(
                    page_number=i + 1,
                    text="",
                    char_count=0
                ))
        
        # Combine all text
        full_text = "\n\n".join([p.text for p in pages if p.text])
        total_chars = sum(p.char_count for p in pages)
        
        return PDFContent(
            total_pages=total_pages,
            pages=pages,
            full_text=full_text,
            total_chars=total_chars,
            metadata=metadata,
            errors=errors
        )
        
    except Exception as e:
        return PDFContent(
            total_pages=0,
            pages=[],
            full_text="",
            total_chars=0,
            metadata={},
            errors=[f"Failed to process PDF: {str(e)}"]
        )


def extract_text_simple(
    file_input: Union[str, Path, bytes, io.BytesIO]
) -> str:
    """
    Extract text đơn giản - chỉ trả về full text.
    
    Args:
        file_input: Đường dẫn file, bytes, hoặc BytesIO
        
    Returns:
        Full text từ PDF hoặc empty string nếu lỗi
    """
    result = extract_text_from_pdf(file_input)
    return result.full_text


def extract_text_by_page(
    file_input: Union[str, Path, bytes, io.BytesIO]
) -> List[str]:
    """
    Extract text theo từng trang.
    
    Args:
        file_input: Đường dẫn file, bytes, hoặc BytesIO
        
    Returns:
        List text của từng trang
    """
    result = extract_text_from_pdf(file_input)
    return [p.text for p in result.pages]


def _get_pdf_reader(
    file_input: Union[str, Path, bytes, io.BytesIO]
) -> Optional[PyPDF2.PdfReader]:
    """Tạo PdfReader từ nhiều loại input."""
    try:
        if isinstance(file_input, (str, Path)):
            return PyPDF2.PdfReader(str(file_input))
        elif isinstance(file_input, bytes):
            return PyPDF2.PdfReader(io.BytesIO(file_input))
        elif isinstance(file_input, io.BytesIO):
            file_input.seek(0)
            return PyPDF2.PdfReader(file_input)
        else:
            raise ValueError(f"Unsupported input type: {type(file_input)}")
    except Exception as e:
        print(f"Error creating PDF reader: {e}")
        return None


def _extract_metadata(reader: PyPDF2.PdfReader) -> dict:
    """Extract metadata từ PDF."""
    metadata = {}
    try:
        if reader.metadata:
            meta = reader.metadata
            metadata = {
                "title": meta.get("/Title", ""),
                "author": meta.get("/Author", ""),
                "subject": meta.get("/Subject", ""),
                "creator": meta.get("/Creator", ""),
                "producer": meta.get("/Producer", ""),
                "creation_date": str(meta.get("/CreationDate", "")),
                "modification_date": str(meta.get("/ModDate", ""))
            }
            # Clean None values
            metadata = {k: v for k, v in metadata.items() if v}
    except Exception:
        pass
    return metadata


def _clean_text(text: str) -> str:
    """
    Clean extracted text:
    - Remove excessive whitespace
    - Fix common encoding issues
    - Normalize line breaks
    """
    if not text:
        return ""
    
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with double newline (paragraph break)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Fix common ligatures
    ligatures = {
        'ﬁ': 'fi',
        'ﬂ': 'fl',
        'ﬀ': 'ff',
        'ﬃ': 'ffi',
        'ﬄ': 'ffl',
    }
    for lig, replacement in ligatures.items():
        text = text.replace(lig, replacement)
    
    # Remove null characters
    text = text.replace('\x00', '')
    
    # Strip final result
    return text.strip()


def get_page_count(file_input: Union[str, Path, bytes, io.BytesIO]) -> int:
    """Lấy số trang của PDF."""
    try:
        reader = _get_pdf_reader(file_input)
        if reader:
            return len(reader.pages)
    except Exception:
        pass
    return 0
