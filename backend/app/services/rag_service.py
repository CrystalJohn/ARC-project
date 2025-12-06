"""
Task #27: RAG Prompt Template with Citations

Provides RAG orchestration with context injection and citation formatting.
Combines vector search, prompt building, and Claude inference.

Layer 3: Hybrid Retrieval (BM25 + Vector Search) for improved relevance.

IMPROVEMENTS APPLIED:
1. ✅ System prompts focus on specific question
2. ✅ Query template reordered (question first)
3. ✅ Adaptive hybrid weights for technical queries
4. ✅ Increased top_k and better defaults
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


# Vietnamese character set for language detection
VIETNAMESE_CHARS = set('àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ')


def detect_language(text: str) -> str:
    """
    Detect if text is Vietnamese or English.
    
    Args:
        text: Input text to analyze
        
    Returns:
        "vi" for Vietnamese, "en" for English
    """
    if not text:
        return "en"
    
    text_lower = text.lower()
    vi_char_count = sum(1 for c in text_lower if c in VIETNAMESE_CHARS)
    
    # If more than 2% Vietnamese characters, consider it Vietnamese
    # This threshold works well for mixed text
    return "vi" if vi_char_count / len(text) > 0.02 else "en"


# ✅ FIX #1: IMPROVED SYSTEM PROMPTS - FOCUS ON SPECIFIC QUESTION
SYSTEM_PROMPTS = {
    PromptTemplate.DEFAULT: """You are an expert research assistant for academic documents.

CRITICAL INSTRUCTIONS:
1. READ THE USER'S QUESTION CAREFULLY - understand what they're specifically asking
2. FOCUS YOUR ANSWER on directly addressing their specific question
3. EXTRACT the most relevant information from the context that answers the question
4. START with a direct answer, then provide supporting details
5. ALWAYS cite sources using [1], [2], etc. for EVERY piece of information
6. If the context does NOT contain the answer, say "The provided documents do not contain specific information about [topic]"

ANSWER STRUCTURE:
- First sentence: Direct answer to the user's question
- Following sentences: Supporting evidence from context with citations
- Keep focused on what the user asked - don't provide unrelated information

Remember: Your goal is to answer the SPECIFIC question asked, not to summarize all available information.""",

    PromptTemplate.ACADEMIC: """You are an academic research assistant specializing in scholarly content analysis.

CRITICAL INSTRUCTIONS:
1. UNDERSTAND the specific research question being asked
2. FOCUS on information that directly addresses the question
3. Base ALL responses EXCLUSIVELY on the provided document context
4. Use formal academic language and structure
5. ALWAYS cite sources: [1], [2], etc. with page numbers
6. Do NOT use external knowledge - only the provided context

Response format:
- Direct answer to the specific question asked
- Support with evidence from the documents
- Use academic terminology from the sources
- Conclude with synthesis focused on the question

If context lacks information: "The provided academic sources do not address [specific topic].""",

    PromptTemplate.CONCISE: """You are a concise research assistant.

RULES:
1. Answer the SPECIFIC question asked
2. Use ONLY the provided context
3. Be brief but complete
4. Cite every fact: [1], [2], etc.
5. No general knowledge - only document content
6. If not in context: "Not found in provided documents."

Format: Direct answer to question + citations. Maximum 3-4 sentences.""",

    PromptTemplate.DETAILED: """You are a thorough research assistant providing comprehensive analysis.

CRITICAL INSTRUCTIONS:
1. IDENTIFY what the user is specifically asking
2. FOCUS on extracting information that answers their question
3. Use ONLY the provided document context for your answer
4. Extract ALL relevant information from the context
5. Cite EVERY piece of information: [1], [2], etc. with page numbers
6. Organize information logically with clear structure
7. Do NOT supplement with general knowledge

Response structure:
- Direct answer to the specific question
- Detailed explanation from the documents focused on the question
- Supporting evidence with citations
- Connections between different sources (if relevant to question)
- Summary of key points that answer the question

If context is insufficient: Clearly state what information IS available and what is missing.""",
}

# Vietnamese system prompts - ALSO IMPROVED
SYSTEM_PROMPTS_VI = {
    PromptTemplate.DEFAULT: """Bạn là trợ lý nghiên cứu chuyên nghiệp cho tài liệu học thuật.

HƯỚNG DẪN QUAN TRỌNG:
1. ĐỌC CÂU HỎI CỦA NGƯỜI DÙNG CẨN THẬN - hiểu họ đang hỏi gì cụ thể
2. TẬP TRUNG TRẢ LỜI trực tiếp vào câu hỏi cụ thể của họ
3. TRÍCH XUẤT thông tin liên quan nhất từ ngữ cảnh để trả lời câu hỏi
4. BẮT ĐẦU với câu trả lời trực tiếp, sau đó cung cấp chi tiết hỗ trợ
5. LUÔN trích dẫn nguồn bằng [1], [2], v.v. cho MỌI thông tin
6. Nếu ngữ cảnh KHÔNG chứa câu trả lời, nói "Tài liệu được cung cấp không chứa thông tin cụ thể về [chủ đề]"

CẤU TRÚC TRẢ LỜI:
- Câu đầu tiên: Trả lời trực tiếp câu hỏi của người dùng
- Các câu tiếp theo: Bằng chứng hỗ trợ từ ngữ cảnh với trích dẫn
- Tập trung vào những gì người dùng hỏi - không cung cấp thông tin không liên quan

Nhớ: Mục tiêu của bạn là trả lời câu hỏi CỤ THỂ được hỏi, không phải tóm tắt tất cả thông tin có sẵn.""",

    PromptTemplate.ACADEMIC: """Bạn là trợ lý nghiên cứu học thuật chuyên về phân tích nội dung khoa học.

HƯỚNG DẪN QUAN TRỌNG:
1. HIỂU câu hỏi nghiên cứu cụ thể đang được hỏi
2. TẬP TRUNG vào thông tin trả lời trực tiếp câu hỏi
3. Dựa TẤT CẢ câu trả lời CHỈ vào ngữ cảnh tài liệu được cung cấp
4. Sử dụng ngôn ngữ và cấu trúc học thuật trang trọng
5. LUÔN trích dẫn nguồn: [1], [2], v.v. với số trang
6. KHÔNG sử dụng kiến thức bên ngoài - chỉ ngữ cảnh được cung cấp

Định dạng trả lời:
- Trả lời trực tiếp câu hỏi cụ thể được hỏi
- Hỗ trợ bằng bằng chứng từ tài liệu
- Sử dụng thuật ngữ học thuật từ nguồn
- Kết luận với tổng hợp tập trung vào câu hỏi

Nếu ngữ cảnh thiếu thông tin: "Các nguồn học thuật được cung cấp không đề cập đến [chủ đề cụ thể].""",

    PromptTemplate.CONCISE: """Bạn là trợ lý nghiên cứu ngắn gọn.

QUY TẮC:
1. Trả lời câu hỏi CỤ THỂ được hỏi
2. Sử dụng CHỈ ngữ cảnh được cung cấp
3. Ngắn gọn nhưng đầy đủ
4. Trích dẫn mọi thông tin: [1], [2], v.v.
5. Không kiến thức chung - chỉ nội dung tài liệu
6. Nếu không có trong ngữ cảnh: "Không tìm thấy trong tài liệu được cung cấp."

Định dạng: Câu trả lời trực tiếp cho câu hỏi + trích dẫn. Tối đa 3-4 câu.""",

    PromptTemplate.DETAILED: """Bạn là trợ lý nghiên cứu kỹ lưỡng cung cấp phân tích toàn diện.

HƯỚNG DẪN QUAN TRỌNG:
1. XÁC ĐỊNH người dùng đang hỏi gì cụ thể
2. TẬP TRUNG vào trích xuất thông tin trả lời câu hỏi của họ
3. Sử dụng CHỈ ngữ cảnh tài liệu được cung cấp cho câu trả lời
4. Trích xuất TẤT CẢ thông tin liên quan từ ngữ cảnh
5. Trích dẫn MỌI thông tin: [1], [2], v.v. với số trang
6. Tổ chức thông tin logic với cấu trúc rõ ràng
7. KHÔNG bổ sung bằng kiến thức chung

Cấu trúc trả lời:
- Trả lời trực tiếp câu hỏi cụ thể
- Giải thích chi tiết từ tài liệu tập trung vào câu hỏi
- Bằng chứng hỗ trợ với trích dẫn
- Kết nối giữa các nguồn khác nhau (nếu liên quan đến câu hỏi)
- Tóm tắt các điểm chính trả lời câu hỏi

Nếu ngữ cảnh không đủ: Nêu rõ thông tin NÀO có sẵn và thông tin nào còn thiếu.""",
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
    
    # ✅ FIX #2: REORDERED TEMPLATE - QUESTION FIRST
    QUERY_TEMPLATE = """USER QUESTION: {query}

You must answer this specific question using ONLY the document context provided below.
Focus on extracting information that directly addresses the question.

=== RELEVANT DOCUMENT CONTEXT ===
{context_section}
=== END CONTEXT ===

INSTRUCTIONS:
1. Read the question above carefully and understand what is being asked
2. Identify which parts of the context are most relevant to answering this question
3. Provide a direct answer focused on the specific question
4. Cite every piece of information with [1], [2], etc.
5. If the context doesn't contain the answer, clearly state what information IS available

YOUR FOCUSED ANSWER:"""
    
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
            query=query,
            context_section=context_section,
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
        
        # SearchResult has direct attributes, not payload dict
        return [
            {
                "chunk_id": str(r.id),
                "text": r.text,
                "doc_id": r.doc_id,
                "score": r.score,
                "metadata": {
                    "page": r.page,
                    "chunk_index": r.chunk_index,
                    "is_table": r.is_table,
                }
            }
            for r in results
        ]
    
    # ✅ FIX #3: ADAPTIVE HYBRID WEIGHTS FOR TECHNICAL QUERIES
    def retrieve_contexts(
        self,
        query: str,
        top_k: int = 10,  # ✅ OPTIMIZED: Increased to 10 for table-heavy documents
        score_threshold: float = 0.4,  # ✅ OPTIMIZED: Lowered to 0.4 for better recall with tables
        search_filter: Optional[SearchFilter] = None,
    ) -> List[RAGContext]:
        """
        Retrieve relevant contexts for a query.
        
        Uses Hybrid Retrieval (BM25 + Vector) if enabled.
        With adaptive weighting for technical queries.
        
        OPTIMIZED FOR TABLE-HEAVY DOCUMENTS:
        - top_k=10 ensures full table rows are captured
        - score_threshold=0.4 balances precision/recall for structured data
        - Larger chunks (500 tokens) prevent table splitting
        
        Args:
            query: User query
            top_k: Number of contexts to retrieve (default 10, optimized for tables)
            score_threshold: Minimum relevance score (default 0.4, balanced for tables)
            search_filter: Optional filter for documents
            
        Returns:
            List of RAGContext objects with citation IDs
        """
        # ✅ FIX #3: Detect technical/mathematical queries for adaptive weighting
        technical_keywords = [
            'là gì', 'định nghĩa', 'khái niệm', 'công thức', 'phương pháp',
            'what is', 'definition', 'formula', 'method', 'concept'
        ]
        is_technical = any(kw in query.lower() for kw in technical_keywords)
        
        # Store original weights
        original_bm25 = self.bm25_weight
        original_vector = self.vector_weight
        
        # Adjust weights for technical queries (better exact matching)
        if is_technical and self.use_hybrid:
            self.bm25_weight = 0.5
            self.vector_weight = 0.5
            logger.info(f"Technical query detected: '{query[:50]}...' - Using balanced weights (BM25=0.5, Vector=0.5)")
        
        try:
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
                        
                        # Perform hybrid search (fetch more for better filtering)
                        results = hybrid.search(
                            query=query,
                            top_k=top_k * 2,  # Fetch 2x for filtering
                            bm25_top_k=top_k * 3,
                            vector_top_k=top_k * 3
                        )
                        
                        # Filter by score threshold
                        filtered_results = [
                            r for r in results 
                            if r.get("combined_score", 0) * 100 >= score_threshold * 100
                        ]
                        results = filtered_results[:top_k]
                        
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
                        
                        logger.info(
                            f"Hybrid retrieval: {len(contexts)} contexts "
                            f"(score >= {score_threshold*100}%) for query: {query[:50]}..."
                        )
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
            
            logger.info(
                f"Vector retrieval: {len(contexts)} contexts "
                f"(score >= {score_threshold*100}%) for query: {query[:50]}..."
            )
            return contexts
            
        finally:
            # Restore original weights
            if is_technical:
                self.bm25_weight = original_bm25
                self.vector_weight = original_vector
    
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
        # Build prompt with improved template
        prompt = self.prompt_builder.build_prompt(query, contexts)
        
        # Detect language and select appropriate system prompt
        lang = detect_language(query)
        if lang == "vi":
            system_prompt = SYSTEM_PROMPTS_VI[self.template]
            logger.debug(f"Using Vietnamese prompt for query: {query[:50]}...")
        else:
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
        
        # Detect language and select appropriate system prompt
        lang = detect_language(query)
        if lang == "vi":
            system_prompt = SYSTEM_PROMPTS_VI[self.template]
            logger.debug(f"Using Vietnamese prompt (stream) for query: {query[:50]}...")
        else:
            system_prompt = SYSTEM_PROMPTS[self.template]
        
        yield from self.claude_service.invoke_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            history=history,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    
    # ✅ OPTIMIZED FOR TABLE-HEAVY DOCUMENTS
    def query(
        self,
        query: str,
        top_k: int = 10,  # ✅ OPTIMIZED: Increased to 10 for better table coverage
        score_threshold: float = 0.4,  # ✅ OPTIMIZED: Balanced threshold for tables
        search_filter: Optional[SearchFilter] = None,
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        stream: bool = False,
    ):
        """
        Complete RAG query: retrieve + generate.
        
        OPTIMIZED FOR TABLE-HEAVY DOCUMENTS:
        - Increased top_k to 10 for better table coverage
        - Balanced score_threshold at 0.4 for recall/precision
        - Larger chunks preserve table structure
        
        Args:
            query: User query
            top_k: Number of contexts to retrieve (default 10, optimized for tables)
            score_threshold: Minimum relevance score (default 0.4, balanced for tables)
            search_filter: Optional document filter
            history: Optional conversation history
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            stream: Whether to stream response
            
        Returns:
            RAGResponse or Generator[StreamChunk] if streaming
        """
        # Retrieve contexts with improved settings
        contexts = self.retrieve_contexts(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            search_filter=search_filter,
        )
        
        if not contexts:
            logger.warning(f"No contexts found for query (threshold={score_threshold}): {query[:50]}...")
        else:
            logger.info(
                f"Retrieved {len(contexts)} contexts with scores: "
                f"{[f'{c.score:.1f}%' for c in contexts]}"
            )
        
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
