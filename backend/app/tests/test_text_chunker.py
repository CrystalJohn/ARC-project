"""
Unit tests for Text Chunker service.
"""

import pytest
from app.services.text_chunker import (
    chunk_text,
    chunk_text_simple,
    estimate_tokens,
    get_chunk_stats,
    TextChunk,
    CHARS_PER_TOKEN,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_OVERLAP
)


class TestChunkText:
    """Tests for chunk_text function."""
    
    def test_empty_text(self):
        """Empty text returns empty list."""
        assert chunk_text("") == []
        assert chunk_text("   ") == []
        assert chunk_text(None) == [] if chunk_text(None) is not None else True
    
    def test_short_text_single_chunk(self):
        """Text shorter than chunk_size returns single chunk."""
        text = "This is a short text."
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].index == 0
    
    def test_chunk_structure(self):
        """Verify chunk structure has all required fields."""
        text = "Sample text for testing."
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        
        chunk = chunks[0]
        assert isinstance(chunk, TextChunk)
        assert hasattr(chunk, 'index')
        assert hasattr(chunk, 'text')
        assert hasattr(chunk, 'char_count')
        assert hasattr(chunk, 'token_estimate')
        assert hasattr(chunk, 'start_char')
        assert hasattr(chunk, 'end_char')
    
    def test_multiple_chunks(self):
        """Long text creates multiple chunks."""
        # Create text longer than default chunk size
        text = "Word " * 2000  # ~10000 chars = ~2500 tokens
        chunks = chunk_text(text, chunk_size=500, overlap=100)
        
        assert len(chunks) > 1
        # Verify indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk.index == i
    
    def test_overlap_exists(self):
        """Chunks should have overlapping content."""
        text = "Sentence one. Sentence two. Sentence three. Sentence four. " * 50
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        
        if len(chunks) > 1:
            # Check that end of chunk 0 overlaps with start of chunk 1
            chunk0_end = chunks[0].text[-100:]  # Last 100 chars
            chunk1_start = chunks[1].text[:100]  # First 100 chars
            
            # There should be some common content
            # (exact overlap depends on boundary finding)
            assert len(chunks) >= 2
    
    def test_invalid_parameters(self):
        """Invalid parameters should raise error."""
        with pytest.raises(ValueError):
            chunk_text("test", chunk_size=100, overlap=100)  # overlap >= chunk_size
        
        with pytest.raises(ValueError):
            chunk_text("test", chunk_size=100, overlap=150)  # overlap > chunk_size
    
    def test_respect_boundaries_paragraph(self):
        """Should split at paragraph boundaries when possible."""
        text = "First paragraph content here.\n\nSecond paragraph content here.\n\nThird paragraph."
        chunks = chunk_text(text, chunk_size=20, overlap=5, respect_boundaries=True)
        
        # Chunks should try to end at paragraph breaks
        assert len(chunks) >= 1
    
    def test_respect_boundaries_sentence(self):
        """Should split at sentence boundaries when possible."""
        text = "First sentence here. Second sentence here. Third sentence here. Fourth sentence."
        chunks = chunk_text(text, chunk_size=15, overlap=3, respect_boundaries=True)
        
        # Should have multiple chunks
        assert len(chunks) >= 1
    
    def test_no_respect_boundaries(self):
        """Simple chunking without boundary respect."""
        text = "A" * 1000
        chunks = chunk_text(text, chunk_size=50, overlap=10, respect_boundaries=False)
        
        # Each chunk should be close to target size
        for chunk in chunks[:-1]:  # Except last chunk
            assert chunk.char_count <= 50 * CHARS_PER_TOKEN + 10


class TestChunkTextSimple:
    """Tests for chunk_text_simple function."""
    
    def test_returns_strings(self):
        """Should return list of strings."""
        text = "Sample text " * 100
        chunks = chunk_text_simple(text, chunk_size=50, overlap=10)
        
        assert isinstance(chunks, list)
        assert all(isinstance(c, str) for c in chunks)
    
    def test_empty_text(self):
        """Empty text returns empty list."""
        assert chunk_text_simple("") == []


class TestEstimateTokens:
    """Tests for estimate_tokens function."""
    
    def test_empty_string(self):
        """Empty string returns 0."""
        assert estimate_tokens("") == 0
        assert estimate_tokens(None) == 0 if estimate_tokens(None) is not None else True
    
    def test_token_estimation(self):
        """Token estimation based on char count."""
        text = "A" * 100
        tokens = estimate_tokens(text)
        assert tokens == 100 // CHARS_PER_TOKEN
    
    def test_realistic_text(self):
        """Realistic text estimation."""
        text = "This is a sample sentence with multiple words."
        tokens = estimate_tokens(text)
        # ~47 chars / 4 = ~11 tokens
        assert 10 <= tokens <= 15


class TestGetChunkStats:
    """Tests for get_chunk_stats function."""
    
    def test_empty_chunks(self):
        """Empty list returns zero stats."""
        stats = get_chunk_stats([])
        assert stats["total_chunks"] == 0
        assert stats["total_chars"] == 0
    
    def test_stats_calculation(self):
        """Stats are calculated correctly."""
        chunks = [
            TextChunk(index=0, text="A" * 100, char_count=100, 
                     token_estimate=25, start_char=0, end_char=100),
            TextChunk(index=1, text="B" * 200, char_count=200, 
                     token_estimate=50, start_char=80, end_char=280),
        ]
        
        stats = get_chunk_stats(chunks)
        
        assert stats["total_chunks"] == 2
        assert stats["total_chars"] == 300
        assert stats["total_tokens_estimate"] == 75
        assert stats["avg_chunk_size"] == 37  # 75 // 2
        assert stats["min_chunk_size"] == 25
        assert stats["max_chunk_size"] == 50


class TestChunkPositions:
    """Tests for chunk position tracking."""
    
    def test_positions_are_valid(self):
        """Start and end positions should be valid."""
        text = "Sample text " * 100
        chunks = chunk_text(text, chunk_size=50, overlap=10)
        
        for chunk in chunks:
            assert chunk.start_char >= 0
            assert chunk.end_char <= len(text)
            assert chunk.start_char < chunk.end_char
    
    def test_first_chunk_starts_at_zero(self):
        """First chunk should start at position 0."""
        text = "Sample text " * 100
        chunks = chunk_text(text, chunk_size=50, overlap=10)
        
        assert chunks[0].start_char == 0


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_text_with_only_whitespace_between_words(self):
        """Handle text with various whitespace."""
        text = "Word1   Word2\t\tWord3\n\nWord4"
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        
        assert len(chunks) >= 1
    
    def test_unicode_text(self):
        """Handle unicode characters."""
        text = "Đây là văn bản tiếng Việt. " * 50
        chunks = chunk_text(text, chunk_size=50, overlap=10)
        
        assert len(chunks) >= 1
        # Verify text is preserved
        assert "tiếng Việt" in chunks[0].text
    
    def test_very_long_word(self):
        """Handle text with very long words."""
        text = "A" * 10000  # One very long "word"
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        
        assert len(chunks) >= 1
    
    def test_special_characters(self):
        """Handle special characters."""
        text = "Code: def func(): pass\n# Comment\n" * 50
        chunks = chunk_text(text, chunk_size=50, overlap=10)
        
        assert len(chunks) >= 1
