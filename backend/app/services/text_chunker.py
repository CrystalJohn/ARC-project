"""
Task #17: Text Chunking Service

Chia text thành các chunks với configurable size và overlap.
Preserve context bằng cách split theo paragraph/sentence boundaries.
"""

import re
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class TextChunk:
    """Một chunk của text."""
    index: int
    text: str
    char_count: int
    token_estimate: int  # Ước tính tokens (~4 chars/token)
    start_char: int      # Vị trí bắt đầu trong original text
    end_char: int        # Vị trí kết thúc trong original text


# Default settings
DEFAULT_CHUNK_SIZE = 1000      # tokens
DEFAULT_OVERLAP = 200          # tokens
CHARS_PER_TOKEN = 4            # Ước tính trung bình


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    respect_boundaries: bool = True
) -> List[TextChunk]:
    """
    Chia text thành các chunks.
    
    Args:
        text: Text cần chia
        chunk_size: Kích thước mỗi chunk (tokens)
        overlap: Số tokens overlap giữa các chunks
        respect_boundaries: Có cố gắng split theo paragraph/sentence không
        
    Returns:
        List các TextChunk
    """
    if not text or not text.strip():
        return []
    
    # Convert token size to char size
    chunk_chars = chunk_size * CHARS_PER_TOKEN
    overlap_chars = overlap * CHARS_PER_TOKEN
    
    # Validate parameters
    if chunk_chars <= overlap_chars:
        raise ValueError("chunk_size must be greater than overlap")
    
    if respect_boundaries:
        return _chunk_with_boundaries(text, chunk_chars, overlap_chars)
    else:
        return _chunk_simple(text, chunk_chars, overlap_chars)


def _chunk_simple(
    text: str,
    chunk_chars: int,
    overlap_chars: int
) -> List[TextChunk]:
    """Simple chunking - cắt theo character count."""
    chunks = []
    start = 0
    index = 0
    
    while start < len(text):
        end = min(start + chunk_chars, len(text))
        chunk_text = text[start:end]
        
        chunks.append(TextChunk(
            index=index,
            text=chunk_text,
            char_count=len(chunk_text),
            token_estimate=len(chunk_text) // CHARS_PER_TOKEN,
            start_char=start,
            end_char=end
        ))
        
        # Move start position (với overlap)
        start = end - overlap_chars
        if start >= len(text) - overlap_chars:
            break
        index += 1
    
    return chunks


def _chunk_with_boundaries(
    text: str,
    chunk_chars: int,
    overlap_chars: int
) -> List[TextChunk]:
    """
    Chunking với respect cho paragraph/sentence boundaries.
    Cố gắng không cắt giữa câu.
    """
    chunks = []
    start = 0
    index = 0
    
    # Nếu text ngắn hơn chunk size, trả về 1 chunk
    if len(text) <= chunk_chars:
        return [TextChunk(
            index=0,
            text=text.strip(),
            char_count=len(text.strip()),
            token_estimate=len(text.strip()) // CHARS_PER_TOKEN,
            start_char=0,
            end_char=len(text)
        )]
    
    while start < len(text):
        # Tính end position
        end = min(start + chunk_chars, len(text))
        
        # Nếu chưa hết text, tìm boundary tốt nhất
        if end < len(text):
            end = _find_best_boundary(text, start, end, chunk_chars)
        
        chunk_text_content = text[start:end].strip()
        
        if chunk_text_content:  # Chỉ add chunk nếu có content
            chunks.append(TextChunk(
                index=index,
                text=chunk_text_content,
                char_count=len(chunk_text_content),
                token_estimate=len(chunk_text_content) // CHARS_PER_TOKEN,
                start_char=start,
                end_char=end
            ))
            index += 1
        
        # Nếu đã đến cuối text, dừng
        if end >= len(text):
            break
        
        # Tính start position cho chunk tiếp theo (với overlap)
        step = chunk_chars - overlap_chars
        start = start + step
        
        # Đảm bảo không vượt quá text length
        if start >= len(text):
            break
    
    return chunks


def _find_best_boundary(
    text: str,
    start: int,
    end: int,
    chunk_chars: int
) -> int:
    """
    Tìm vị trí boundary tốt nhất để cắt chunk.
    Ưu tiên: paragraph > sentence > word
    """
    search_start = max(start, end - chunk_chars // 4)  # Tìm trong 25% cuối
    search_text = text[search_start:end]
    
    # 1. Tìm paragraph break (double newline)
    para_match = list(re.finditer(r'\n\n+', search_text))
    if para_match:
        return search_start + para_match[-1].end()
    
    # 2. Tìm sentence break
    sentence_match = list(re.finditer(r'[.!?]\s+', search_text))
    if sentence_match:
        return search_start + sentence_match[-1].end()
    
    # 3. Tìm word break
    word_match = list(re.finditer(r'\s+', search_text))
    if word_match:
        return search_start + word_match[-1].start()
    
    # 4. Fallback: cắt tại end
    return end


def _find_overlap_boundary(
    text: str,
    overlap_start: int,
    end: int
) -> int:
    """
    Tìm vị trí bắt đầu overlap tốt (đầu câu hoặc paragraph).
    """
    search_text = text[overlap_start:end]
    
    # Tìm đầu paragraph
    para_match = re.search(r'\n\n+', search_text)
    if para_match:
        return overlap_start + para_match.end()
    
    # Tìm đầu câu
    sentence_match = re.search(r'[.!?]\s+', search_text)
    if sentence_match:
        return overlap_start + sentence_match.end()
    
    return overlap_start


def chunk_text_simple(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP
) -> List[str]:
    """
    Convenience function - chỉ trả về list text strings.
    """
    chunks = chunk_text(text, chunk_size, overlap)
    return [c.text for c in chunks]


def estimate_tokens(text: str) -> int:
    """Ước tính số tokens trong text."""
    if not text:
        return 0
    return len(text) // CHARS_PER_TOKEN


def get_chunk_stats(chunks: List[TextChunk]) -> dict:
    """Lấy thống kê về chunks."""
    if not chunks:
        return {
            "total_chunks": 0,
            "total_chars": 0,
            "total_tokens_estimate": 0,
            "avg_chunk_size": 0,
            "min_chunk_size": 0,
            "max_chunk_size": 0
        }
    
    char_counts = [c.char_count for c in chunks]
    token_counts = [c.token_estimate for c in chunks]
    
    return {
        "total_chunks": len(chunks),
        "total_chars": sum(char_counts),
        "total_tokens_estimate": sum(token_counts),
        "avg_chunk_size": sum(token_counts) // len(chunks),
        "min_chunk_size": min(token_counts),
        "max_chunk_size": max(token_counts)
    }
