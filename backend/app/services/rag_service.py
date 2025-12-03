"""
Task #27: RAG Prompt Template with Citations

Provides RAG orchestration with context injection and citation formatting.
Combines vector search, prompt building, and Claude inference.
"""

import logging
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass, field
from enum import Enum

from app.services.qdrant_client import (
    QdrantVectorStore,
    SearchFilter,
    RAGContext,
)
from app.services.embedding_service import CohereEmbeddingService as EmbeddingService
from app.services.claude_service import (
    ClaudeService,
    ClaudeResponse,
    StreamChunk,
    TokenUsage,
)

logger = logging.getLogger(__name__)


class PromptTemplate(Enum):
    """Available prompt templates."""
    DEFAULT = "default"
    ACADEMIC = "academic"
    CONCISE = "concise"
    DETAILED = "detailed"


# System prompts for different templates
SYSTEM_PROMPTS = {
    PromptTemplate.DEFAULT: """You are a helpful research assistant for an academic chatbot.
Your role is to answer questions based on the provided document context.
Always cite your sources using [1], [2], etc. format when referencing information.
If the context doesn't contain relevant information to answer the question, say so clearly.
Be accurate and helpful.""",

    PromptTemplate.ACADEMIC: """You are an academic research assistant specializing in scholarly content.
Provide well-structured, academic-style responses based on the provided context.
Always cite sources using [1], [2], etc. format. Include page numbers when relevant.
Use formal language appropriate for academic discourse.
If information is not in the context, acknowledge the limitation.""",

    PromptTemplate.CONCISE: """You are a concise research assistant.
Answer questions briefly and directly based on the provided context.
Use citations [1], [2], etc. Keep responses short but informative.
If context lacks relevant info, say so briefly.""",

    PromptTemplate.DETAILED: """You are a thorough research assistant.
Provide comprehensive, detailed answers based on the provided context.
Always cite sources using [1], [2], etc. Explain concepts fully.
Include relevant details, examples, and connections between sources.
If context is insufficient, explain what additional information would be helpful.""",
}


@dataclass
class Citation:
    """Citation reference in response."""
    id: int  # [1], [2], etc.
    doc_id: str
    page: int
    text_snippet: str  # First 100 chars of source
    score: float


@dataclass
class RAGResponse:
    """Response from RAG pipeline."""
    answer: str
    citations: List[Citation]
    usage: TokenUsage
    model: str
    contexts_used: int
    query: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": [
                {
                    "id": c.id,
                    "doc_id": c.doc_id,
                    "page": c.page,
                    "text_snippet": c.text_snippet,
                    "score": c.score,
                }
                for c in self.citations
            ],
            "usage": self.usage.to_dict(),
            "model": self.model,
            "contexts_used": self.contexts_used,
            "query": self.query,
        }


class RAGPromptBuilder:
    """
    Builds RAG prompts with context injection and citation formatting.
    """
    
    CONTEXT_TEMPLATE = """[{citation_id}] (Document: {doc_id}, Page {page})
{text}"""
    
    QUERY_TEMPLATE = """Based on the following context from research documents, answer the user's question.
Use citations like [1], [2] to reference the source documents when you use information from them.

CONTEXT:
{context_section}

---

USER QUESTION:
{query}

Please provide a helpful answer based on the context above. Remember to cite your sources."""
    
    @classmethod
    def build_context_section(cls, contexts: List[RAGContext]) -> str:
        """Build formatted context section from RAGContext list."""
        if not contexts:
            return "No relevant context found."
        
        parts = []
        for ctx in contexts:
            part = cls.CONTEXT_TEMPLATE.format(
                citation_id=ctx.citation_id,
                doc_id=ctx.doc_id,
                page=ctx.page,
                text=ctx.text.strip(),
            )
            parts.append(part)
        
        return "\n\n---\n\n".join(parts)
    
    @classmethod
    def build_prompt(
        cls,
        query: str,
        contexts: List[RAGContext],
    ) -> str:
        """Build complete RAG prompt with context and query."""
        context_section = cls.build_context_section(contexts)
        
        return cls.QUERY_TEMPLATE.format(
            context_section=context_section,
            query=query,
        )
    
    @classmethod
    def extract_citations(cls, contexts: List[RAGContext]) -> List[Citation]:
        """Extract citation objects from contexts."""
        return [
            Citation(
                id=ctx.citation_id,
                doc_id=ctx.doc_id,
                page=ctx.page,
                text_snippet=ctx.text[:100] + "..." if len(ctx.text) > 100 else ctx.text,
                score=ctx.score,
            )
            for ctx in contexts
        ]


class RAGService:
    """
    RAG orchestration service.
    
    Combines vector search, prompt building, and Claude inference
    into a complete RAG pipeline.
    """
    
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        region_name: str = "ap-southeast-1",
        model: str = "sonnet",
        template: PromptTemplate = PromptTemplate.DEFAULT,
    ):
        """
        Initialize RAG service.
        
        Args:
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
            region_name: AWS region for Bedrock
            model: Claude model alias (sonnet/haiku)
            template: Prompt template to use
        """
        self.vector_store = QdrantVectorStore(host=qdrant_host, port=qdrant_port)
        self.embedding_service = EmbeddingService(region_name=region_name)
        self.claude_service = ClaudeService(region_name=region_name, model=model)
        self.template = template
        self.prompt_builder = RAGPromptBuilder()
        
        logger.info(f"Initialized RAG service with model={model}, template={template.value}")
    
    def set_template(self, template: PromptTemplate) -> None:
        """Change prompt template."""
        self.template = template
        logger.info(f"Changed template to: {template.value}")
    
    def set_model(self, model: str) -> None:
        """Change Claude model."""
        self.claude_service.switch_model(model)
    
    def retrieve_contexts(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.3,
        search_filter: Optional[SearchFilter] = None,
    ) -> List[RAGContext]:
        """
        Retrieve relevant contexts for a query.
        
        Args:
            query: User query
            top_k: Number of contexts to retrieve
            score_threshold: Minimum relevance score
            search_filter: Optional filter for documents
            
        Returns:
            List of RAGContext objects with citation IDs
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)
        
        # Search vector store
        contexts = self.vector_store.search_for_rag(
            query_vector=query_embedding,
            top_k=top_k,
            score_threshold=score_threshold,
            search_filter=search_filter,
        )
        
        logger.info(f"Retrieved {len(contexts)} contexts for query: {query[:50]}...")
        return contexts
    
    def generate_answer(
        self,
        query: str,
        contexts: List[RAGContext],
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> RAGResponse:
        """
        Generate answer using Claude with retrieved contexts.
        
        Args:
            query: User query
            contexts: Retrieved contexts
            history: Optional conversation history
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            
        Returns:
            RAGResponse with answer and citations
        """
        # Build prompt
        prompt = self.prompt_builder.build_prompt(query, contexts)
        system_prompt = SYSTEM_PROMPTS[self.template]
        
        # Generate response
        response = self.claude_service.invoke(
            prompt=prompt,
            system_prompt=system_prompt,
            history=history,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        # Extract citations
        citations = self.prompt_builder.extract_citations(contexts)
        
        return RAGResponse(
            answer=response.text,
            citations=citations,
            usage=response.usage,
            model=response.model,
            contexts_used=len(contexts),
            query=query,
        )
    
    def generate_answer_stream(
        self,
        query: str,
        contexts: List[RAGContext],
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Generator[StreamChunk, None, None]:
        """
        Generate streaming answer using Claude.
        
        Args:
            query: User query
            contexts: Retrieved contexts
            history: Optional conversation history
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            
        Yields:
            StreamChunk objects with text fragments
        """
        prompt = self.prompt_builder.build_prompt(query, contexts)
        system_prompt = SYSTEM_PROMPTS[self.template]
        
        yield from self.claude_service.invoke_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            history=history,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    
    def query(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.3,
        search_filter: Optional[SearchFilter] = None,
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        stream: bool = False,
    ):
        """
        Complete RAG query: retrieve + generate.
        
        Args:
            query: User query
            top_k: Number of contexts to retrieve
            score_threshold: Minimum relevance score
            search_filter: Optional document filter
            history: Optional conversation history
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            stream: Whether to stream response
            
        Returns:
            RAGResponse or Generator[StreamChunk] if streaming
        """
        # Retrieve contexts
        contexts = self.retrieve_contexts(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            search_filter=search_filter,
        )
        
        if not contexts:
            logger.warning(f"No contexts found for query: {query[:50]}...")
        
        # Generate answer
        if stream:
            return self.generate_answer_stream(
                query=query,
                contexts=contexts,
                history=history,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        else:
            return self.generate_answer(
                query=query,
                contexts=contexts,
                history=history,
                max_tokens=max_tokens,
                temperature=temperature,
            )
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all components."""
        return {
            "qdrant": self.vector_store.health_check(),
            "claude": self.claude_service.health_check(),
            "embeddings": True,  # Embedding service doesn't have health check
        }


# Convenience function
def create_rag_service(
    qdrant_host: str = "localhost",
    qdrant_port: int = 6333,
    region_name: str = "ap-southeast-1",
    model: str = "sonnet",
    template: str = "default",
) -> RAGService:
    """Create RAG service instance."""
    template_enum = PromptTemplate(template)
    return RAGService(
        qdrant_host=qdrant_host,
        qdrant_port=qdrant_port,
        region_name=region_name,
        model=model,
        template=template_enum,
    )
