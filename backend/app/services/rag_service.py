"""
Task #27: RAG Prompt Template with Citations

Provides RAG orchestration with context injection and citation formatting.
Combines vector search, prompt building, and Claude inference.

Layer 3: Hybrid Retrieval (BM25 + Vector Search) for improved relevance.
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
from app.services.bm25_search import BM25Index, HybridRetriever, BM25Result

logger = logging.getLogger(__name__)


class PromptTemplate(Enum):
    """Available prompt templates."""
    DEFAULT = "default"
    ACADEMIC = "academic"
    CONCISE = "concise"
    DETAILED = "detailed"


# System prompts for different templates
SYSTEM_PROMPTS = {
    PromptTemplate.DEFAULT: """You are an expert research assistant for academic documents.

CRITICAL INSTRUCTIONS:
1. ALWAYS answer based ONLY on the provided document context below
2. NEVER use your general knowledge - only use information from the context
3. ALWAYS cite sources using [1], [2], etc. for EVERY piece of information
4. If the context contains relevant information, extract and present it clearly
5. If the context does NOT contain the answer, say "The provided documents do not contain specific information about [topic]"

When answering:
- Quote or paraphrase directly from the context
- Be specific and detailed using the document content
- Organize your answer clearly with the information found
- Include page numbers when citing: "According to [1] (page X)..."

Remember: Your knowledge comes ONLY from the provided context, not from training data.""",

    PromptTemplate.ACADEMIC: """You are an academic research assistant specializing in scholarly content analysis.

CRITICAL INSTRUCTIONS:
1. Base ALL responses EXCLUSIVELY on the provided document context
2. Use formal academic language and structure
3. ALWAYS cite sources: [1], [2], etc. with page numbers
4. Synthesize information across multiple sources when relevant
5. Do NOT use external knowledge - only the provided context

Response format:
- Start with a direct answer to the question
- Support with evidence from the documents
- Use academic terminology from the sources
- Conclude with synthesis or implications

If context lacks information: "The provided academic sources do not address [specific topic].""",

    PromptTemplate.CONCISE: """You are a concise research assistant.

RULES:
1. Answer ONLY from the provided context
2. Be brief but complete
3. Cite every fact: [1], [2], etc.
4. No general knowledge - only document content
5. If not in context: "Not found in provided documents."

Format: Direct answer + citations. Maximum 3-4 sentences.""",

    PromptTemplate.DETAILED: """You are a thorough research assistant providing comprehensive analysis.

CRITICAL INSTRUCTIONS:
1. Use ONLY the provided document context for your answer
2. Extract ALL relevant information from the context
3. Cite EVERY piece of information: [1], [2], etc. with page numbers
4. Organize information logically with clear structure
5. Do NOT supplement with general knowledge

Response structure:
- Direct answer to the question
- Detailed explanation from the documents
- Supporting evidence with citations
- Connections between different sources
- Summary of key points

If context is insufficient: Clearly state what information IS available and what is missing.""",
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
    
    QUERY_TEMPLATE = """You must answer the following question using ONLY the document context provided below.
Do NOT use any external knowledge. Extract and present information directly from these documents.

=== DOCUMENT CONTEXT ===
{context_section}
=== END CONTEXT ===

USER QUESTION: {query}

INSTRUCTIONS:
1. Read the context carefully and find information relevant to the question
2. Answer using ONLY information from the context above
3. Cite every piece of information with [1], [2], etc.
4. If the context contains the answer, provide a detailed response
5. If the context does NOT contain the answer, say "The provided documents do not contain information about [topic]"

YOUR ANSWER:"""
    
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
    
    Layer 3: Supports Hybrid Retrieval (BM25 + Vector) for better relevance.
    """
    
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        region_name: str = "ap-southeast-1",
        model: str = "sonnet",
        template: PromptTemplate = PromptTemplate.DEFAULT,
        use_hybrid: bool = True,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7,
    ):
        """
        Initialize RAG service.
        
        Args:
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
            region_name: AWS region for Bedrock
            model: Claude model alias (sonnet/haiku)
            template: Prompt template to use
            use_hybrid: Enable hybrid retrieval (BM25 + Vector)
            bm25_weight: Weight for BM25 in hybrid search
            vector_weight: Weight for vector search in hybrid
        """
        self.vector_store = QdrantVectorStore(host=qdrant_host, port=qdrant_port)
        self.embedding_service = EmbeddingService(region_name=region_name)
        self.claude_service = ClaudeService(region_name=region_name, model=model)
        self.template = template
        self.prompt_builder = RAGPromptBuilder()
        
        # Layer 3: Hybrid Retrieval
        self.use_hybrid = use_hybrid
        self.bm25_index = BM25Index() if use_hybrid else None
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self._bm25_initialized = False
        
        logger.info(f"Initialized RAG service with model={model}, template={template.value}, hybrid={use_hybrid}")
    
    def set_template(self, template: PromptTemplate) -> None:
        """Change prompt template."""
        self.template = template
        logger.info(f"Changed template to: {template.value}")
    
    def set_model(self, model: str) -> None:
        """Change Claude model."""
        self.claude_service.switch_model(model)
    
    def _init_bm25_from_qdrant(self) -> None:
        """Initialize BM25 index from Qdrant data."""
        if not self.use_hybrid or self._bm25_initialized:
            return
        
        try:
            # Get all documents from Qdrant
            all_points = self.vector_store.get_all_points(limit=10000)
            
            if not all_points:
                logger.warning("No documents in Qdrant for BM25 indexing")
                return
            
            # Index documents in BM25
            for point in all_points:
                payload = point.get("payload", {})
                self.bm25_index.add_document(
                    chunk_id=str(point.get("id", "")),
                    text=payload.get("text", ""),
                    doc_id=payload.get("doc_id", ""),
                    metadata=payload
                )
            
            self._bm25_initialized = True
            logger.info(f"BM25 index initialized with {len(all_points)} documents")
            
        except Exception as e:
            logger.error(f"Failed to initialize BM25 index: {e}")
    
    def _vector_search_fn(self, query: str, top_k: int) -> List[Dict]:
        """Vector search function for hybrid retriever."""
        query_embedding = self.embedding_service.embed_text(query)
        
        results = self.vector_store.search(
            query_vector=query_embedding,
            top_k=top_k,
            score_threshold=0.0  # Get all results, filter later
        )
        
        return [
            {
                "chunk_id": str(r.id),
                "text": r.payload.get("text", ""),
                "doc_id": r.payload.get("doc_id", ""),
                "score": r.score,
                "metadata": r.payload
            }
            for r in results
        ]
    
    def retrieve_contexts(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.3,
        search_filter: Optional[SearchFilter] = None,
    ) -> List[RAGContext]:
        """
        Retrieve relevant contexts for a query.
        
        Uses Hybrid Retrieval (BM25 + Vector) if enabled.
        
        Args:
            query: User query
            top_k: Number of contexts to retrieve
            score_threshold: Minimum relevance score
            search_filter: Optional filter for documents
            
        Returns:
            List of RAGContext objects with citation IDs
        """
        # Try hybrid retrieval first
        if self.use_hybrid:
            try:
                # Initialize BM25 if needed
                self._init_bm25_from_qdrant()
                
                if self._bm25_initialized and self.bm25_index.doc_count > 0:
                    # Create hybrid retriever
                    hybrid = HybridRetriever(
                        bm25_index=self.bm25_index,
                        vector_search_fn=lambda q, k: self._vector_search_fn(q, k),
                        bm25_weight=self.bm25_weight,
                        vector_weight=self.vector_weight
                    )
                    
                    # Perform hybrid search
                    results = hybrid.search(
                        query=query,
                        top_k=top_k,
                        bm25_top_k=top_k * 3,
                        vector_top_k=top_k * 3
                    )
                    
                    # Convert to RAGContext
                    contexts = []
                    for i, r in enumerate(results):
                        metadata = r.get("metadata", {})
                        contexts.append(RAGContext(
                            citation_id=i + 1,
                            doc_id=r.get("doc_id", ""),
                            page=metadata.get("page", 1),
                            text=r.get("text", ""),
                            score=r.get("combined_score", 0) * 100,  # Scale to percentage
                            metadata=metadata
                        ))
                    
                    logger.info(f"Hybrid retrieval: {len(contexts)} contexts for query: {query[:50]}...")
                    return contexts
                    
            except Exception as e:
                logger.warning(f"Hybrid retrieval failed, falling back to vector: {e}")
        
        # Fallback to vector-only search
        query_embedding = self.embedding_service.embed_text(query)
        
        contexts = self.vector_store.search_for_rag(
            query_vector=query_embedding,
            top_k=top_k,
            score_threshold=score_threshold,
            search_filter=search_filter,
        )
        
        logger.info(f"Vector retrieval: {len(contexts)} contexts for query: {query[:50]}...")
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
