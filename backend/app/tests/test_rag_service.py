"""
Tests for RAG Service

Task #27: RAG Prompt Template with Citations
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List

from app.services.rag_service import (
    RAGService,
    RAGResponse,
    RAGPromptBuilder,
    Citation,
    PromptTemplate,
    SYSTEM_PROMPTS,
    create_rag_service,
)
from app.services.qdrant_client import RAGContext
from app.services.claude_service import TokenUsage, ClaudeResponse


class TestCitation:
    """Tests for Citation dataclass."""
    
    def test_citation_creation(self):
        """Test Citation creation."""
        citation = Citation(
            id=1,
            doc_id="doc-123",
            page=5,
            text_snippet="This is a snippet...",
            score=0.85,
        )
        
        assert citation.id == 1
        assert citation.doc_id == "doc-123"
        assert citation.page == 5
        assert citation.score == 0.85


class TestRAGResponse:
    """Tests for RAGResponse dataclass."""
    
    def test_to_dict(self):
        """Test RAGResponse to_dict method."""
        citations = [
            Citation(id=1, doc_id="doc-1", page=1, text_snippet="text", score=0.9),
        ]
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        
        response = RAGResponse(
            answer="The answer is...",
            citations=citations,
            usage=usage,
            model="sonnet",
            contexts_used=3,
            query="What is X?",
        )
        
        d = response.to_dict()
        assert d["answer"] == "The answer is..."
        assert len(d["citations"]) == 1
        assert d["citations"][0]["id"] == 1
        assert d["model"] == "sonnet"
        assert d["contexts_used"] == 3


class TestPromptTemplate:
    """Tests for PromptTemplate enum."""
    
    def test_all_templates_have_system_prompts(self):
        """Test all templates have corresponding system prompts."""
        for template in PromptTemplate:
            assert template in SYSTEM_PROMPTS
            assert len(SYSTEM_PROMPTS[template]) > 0
    
    def test_system_prompts_contain_citation_instruction(self):
        """Test all system prompts mention citations."""
        for template, prompt in SYSTEM_PROMPTS.items():
            assert "[1]" in prompt or "cite" in prompt.lower()


class TestRAGPromptBuilder:
    """Tests for RAGPromptBuilder class."""
    
    @pytest.fixture
    def sample_contexts(self) -> List[RAGContext]:
        """Create sample RAGContext list."""
        return [
            RAGContext(
                text="First context about topic A.",
                doc_id="doc-1",
                page=1,
                chunk_index=0,
                score=0.9,
                citation_id=1,
            ),
            RAGContext(
                text="Second context about topic B.",
                doc_id="doc-2",
                page=5,
                chunk_index=2,
                score=0.8,
                citation_id=2,
            ),
        ]
    
    def test_build_context_section(self, sample_contexts):
        """Test building context section."""
        section = RAGPromptBuilder.build_context_section(sample_contexts)
        
        assert "[1]" in section
        assert "[2]" in section
        assert "doc-1" in section
        assert "doc-2" in section
        assert "Page 1" in section
        assert "Page 5" in section
        assert "First context" in section
        assert "Second context" in section
    
    def test_build_context_section_empty(self):
        """Test building context section with no contexts."""
        section = RAGPromptBuilder.build_context_section([])
        assert "No relevant context" in section
    
    def test_build_prompt(self, sample_contexts):
        """Test building complete prompt."""
        query = "What is topic A?"
        prompt = RAGPromptBuilder.build_prompt(query, sample_contexts)
        
        assert "What is topic A?" in prompt
        assert "[1]" in prompt
        assert "First context" in prompt
        assert "CONTEXT:" in prompt
        assert "USER QUESTION:" in prompt
    
    def test_extract_citations(self, sample_contexts):
        """Test extracting citations from contexts."""
        citations = RAGPromptBuilder.extract_citations(sample_contexts)
        
        assert len(citations) == 2
        assert citations[0].id == 1
        assert citations[0].doc_id == "doc-1"
        assert citations[1].id == 2
        assert citations[1].page == 5
    
    def test_extract_citations_truncates_long_text(self):
        """Test that long text is truncated in snippets."""
        contexts = [
            RAGContext(
                text="A" * 200,  # Long text
                doc_id="doc-1",
                page=1,
                chunk_index=0,
                score=0.9,
                citation_id=1,
            ),
        ]
        
        citations = RAGPromptBuilder.extract_citations(contexts)
        
        assert len(citations[0].text_snippet) == 103  # 100 + "..."
        assert citations[0].text_snippet.endswith("...")


class TestRAGService:
    """Tests for RAGService class."""
    
    @pytest.fixture
    def mock_services(self):
        """Mock all dependent services."""
        with patch("app.services.rag_service.QdrantVectorStore") as mock_qdrant, \
             patch("app.services.rag_service.EmbeddingService") as mock_embed, \
             patch("app.services.rag_service.ClaudeService") as mock_claude:
            
            # Setup mock instances
            mock_qdrant_instance = MagicMock()
            mock_embed_instance = MagicMock()
            mock_claude_instance = MagicMock()
            
            mock_qdrant.return_value = mock_qdrant_instance
            mock_embed.return_value = mock_embed_instance
            mock_claude.return_value = mock_claude_instance
            
            yield {
                "qdrant": mock_qdrant_instance,
                "embed": mock_embed_instance,
                "claude": mock_claude_instance,
            }
    
    @pytest.fixture
    def rag_service(self, mock_services):
        """Create RAG service with mocked dependencies."""
        return RAGService()
    
    def test_init_default(self, mock_services):
        """Test default initialization."""
        service = RAGService()
        assert service.template == PromptTemplate.DEFAULT
    
    def test_init_with_template(self, mock_services):
        """Test initialization with custom template."""
        service = RAGService(template=PromptTemplate.ACADEMIC)
        assert service.template == PromptTemplate.ACADEMIC
    
    def test_set_template(self, rag_service):
        """Test changing template."""
        rag_service.set_template(PromptTemplate.CONCISE)
        assert rag_service.template == PromptTemplate.CONCISE
    
    def test_set_model(self, rag_service, mock_services):
        """Test changing model."""
        rag_service.set_model("haiku")
        mock_services["claude"].switch_model.assert_called_with("haiku")
    
    def test_retrieve_contexts(self, rag_service, mock_services):
        """Test context retrieval."""
        # Setup mocks
        mock_services["embed"].embed_text.return_value = [0.1] * 1024
        mock_services["qdrant"].search_for_rag.return_value = [
            RAGContext(
                text="Context text",
                doc_id="doc-1",
                page=1,
                chunk_index=0,
                score=0.9,
                citation_id=1,
            )
        ]
        
        contexts = rag_service.retrieve_contexts("test query")
        
        assert len(contexts) == 1
        mock_services["embed"].embed_text.assert_called_with("test query")
        mock_services["qdrant"].search_for_rag.assert_called_once()
    
    def test_generate_answer(self, rag_service, mock_services):
        """Test answer generation."""
        contexts = [
            RAGContext(
                text="Context text",
                doc_id="doc-1",
                page=1,
                chunk_index=0,
                score=0.9,
                citation_id=1,
            )
        ]
        
        mock_services["claude"].invoke.return_value = ClaudeResponse(
            text="The answer based on [1] is...",
            usage=TokenUsage(input_tokens=100, output_tokens=50),
            model="sonnet",
        )
        
        response = rag_service.generate_answer("What is X?", contexts)
        
        assert isinstance(response, RAGResponse)
        assert "[1]" in response.answer
        assert len(response.citations) == 1
        assert response.contexts_used == 1
    
    def test_query_complete_pipeline(self, rag_service, mock_services):
        """Test complete query pipeline."""
        # Setup mocks
        mock_services["embed"].embed_text.return_value = [0.1] * 1024
        mock_services["qdrant"].search_for_rag.return_value = [
            RAGContext(
                text="Relevant context",
                doc_id="doc-1",
                page=1,
                chunk_index=0,
                score=0.85,
                citation_id=1,
            )
        ]
        mock_services["claude"].invoke.return_value = ClaudeResponse(
            text="Answer with [1] citation",
            usage=TokenUsage(input_tokens=200, output_tokens=100),
            model="sonnet",
        )
        
        response = rag_service.query("What is the topic?")
        
        assert isinstance(response, RAGResponse)
        assert response.query == "What is the topic?"
        assert response.model == "sonnet"
    
    def test_query_no_contexts(self, rag_service, mock_services):
        """Test query when no contexts found."""
        mock_services["embed"].embed_text.return_value = [0.1] * 1024
        mock_services["qdrant"].search_for_rag.return_value = []
        mock_services["claude"].invoke.return_value = ClaudeResponse(
            text="I couldn't find relevant information.",
            usage=TokenUsage(input_tokens=50, output_tokens=20),
            model="sonnet",
        )
        
        response = rag_service.query("Unknown topic")
        
        assert response.contexts_used == 0
    
    def test_health_check(self, rag_service, mock_services):
        """Test health check."""
        mock_services["qdrant"].health_check.return_value = True
        mock_services["claude"].health_check.return_value = True
        
        health = rag_service.health_check()
        
        assert health["qdrant"] is True
        assert health["claude"] is True
        assert health["embeddings"] is True


class TestCreateRAGService:
    """Tests for create_rag_service function."""
    
    def test_creates_service(self):
        """Test convenience function creates service."""
        with patch("app.services.rag_service.QdrantVectorStore"), \
             patch("app.services.rag_service.EmbeddingService"), \
             patch("app.services.rag_service.ClaudeService"):
            
            service = create_rag_service(template="academic")
            
            assert isinstance(service, RAGService)
            assert service.template == PromptTemplate.ACADEMIC
