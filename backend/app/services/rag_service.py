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
import re
from typing import List, Dict, Any, Optional, Generator, Set
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
from app.services.language_context import (
    LanguageContext,
    get_language_context,
    get_language_instruction,
    get_language_switch_message,
    detect_query_language,
)

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

CITATION PRIORITY (IMPORTANT):
- Citations are ordered by relevance: [1] = HIGHEST score, [2] = second highest, etc.
- PRIORITIZE using [1] in your answer as it's the most relevant context
- Use ALL provided citations when possible, especially high-score ones
- If [1] doesn't directly answer the question, still reference it if related

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

ƯU TIÊN TRÍCH DẪN (QUAN TRỌNG):
- Trích dẫn được sắp xếp theo độ liên quan: [1] = điểm CAO NHẤT, [2] = cao thứ hai, v.v.
- ƯU TIÊN sử dụng [1] trong câu trả lời vì đây là ngữ cảnh liên quan nhất
- Sử dụng TẤT CẢ trích dẫn được cung cấp khi có thể, đặc biệt là những trích dẫn có điểm cao
- Nếu [1] không trả lời trực tiếp câu hỏi, vẫn tham chiếu nếu liên quan

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

⚠️ CITATION PRIORITY RULES (MUST FOLLOW):
1. [1] has the HIGHEST relevance score - it is the MOST relevant to the query
2. You MUST use [1] in your answer - it contains the most relevant information
3. Use ALL provided citations [1], [2], [3] when they contain relevant information
4. Start your answer by referencing [1] first, then add details from [2], [3]

Example format:
✅ GOOD: "Theo [1], lập trình hướng đối tượng là... Các đặc điểm chính bao gồm... [2]. Ngoài ra, [3] cho thấy..."
❌ BAD: Ignoring [1] and only using [2] or [3]

INSTRUCTIONS:
1. Read the question above carefully and understand what is being asked
2. START your answer using information from [1] (highest relevance)
3. Add supporting details from [2], [3] as needed
4. Cite EVERY piece of information with [1], [2], etc.
5. If [1] doesn't directly answer the question, still reference it and explain why

YOUR FOCUSED ANSWER (must include [1]):"""
    
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
        # Rank contexts by score before building prompt
        # This ensures [1] is always the most relevant
        ranked_contexts = cls.rank_contexts_by_score(contexts)
        context_section = cls.build_context_section(ranked_contexts)
        
        return cls.QUERY_TEMPLATE.format(
            query=query,
            context_section=context_section,
        )
    
    @classmethod
    def rank_contexts_by_score(cls, contexts: List[RAGContext], force_rerank: bool = False) -> List[RAGContext]:
        """
        Rank contexts by score and assign citation IDs accordingly.
        
        This ensures:
        - [1] = highest score (most relevant)
        - [2] = second highest
        - etc.
        
        Args:
            contexts: List of RAGContext objects
            force_rerank: Force re-ranking even if already ranked
            
        Returns:
            Sorted contexts with reassigned citation IDs
        """
        if not contexts:
            return contexts
        
        # Check if already properly ranked (skip if [1] has highest score)
        if not force_rerank and len(contexts) > 1:
            is_sorted = all(
                contexts[i].score >= contexts[i+1].score 
                for i in range(len(contexts)-1)
            )
            if is_sorted and contexts[0].citation_id == 1:
                logger.debug("Contexts already ranked by score, skipping re-rank")
                return contexts
        
        # Sort by score descending (highest first)
        sorted_contexts = sorted(contexts, key=lambda x: x.score, reverse=True)
        
        # Reassign citation IDs based on rank
        for idx, context in enumerate(sorted_contexts, 1):
            context.citation_id = idx
        
        # Log ranking for debugging
        logger.info(
            f"✅ Citation ranking by score: "
            f"{[(c.citation_id, f'{c.score:.1f}%', c.doc_id[:20] if c.doc_id else 'unknown') for c in sorted_contexts]}"
        )
        
        return sorted_contexts
    
    @classmethod
    def extract_citations(cls, contexts: List[RAGContext]) -> List[Citation]:
        """Extract citation objects from contexts with full text for highlighting."""
        # Ensure contexts are ranked by score before extracting
        ranked_contexts = cls.rank_contexts_by_score(contexts)
        
        return [
            Citation(
                id=ctx.citation_id,
                doc_id=ctx.doc_id,
                page=ctx.page,
                # Return full text (up to 1000 chars) for comprehensive citation display
                text_snippet=ctx.text[:1000] + "..." if len(ctx.text) > 1000 else ctx.text,
                score=ctx.score,
            )
            for ctx in ranked_contexts
        ]


def validate_citations(answer: str, contexts: List[RAGContext]) -> Dict[str, Any]:
    """
    Validate citation quality in the generated answer.
    
    Checks:
    - Which citations were actually used
    - Whether high-score contexts were cited
    - Citation coverage percentage
    
    Args:
        answer: Generated answer text
        contexts: List of contexts provided to LLM
        
    Returns:
        Dictionary with validation metrics and warnings
    """
    if not contexts:
        return {
            "cited_ids": set(),
            "citation_coverage": 0,
            "high_score_usage": 1.0,
            "warnings": []
        }
    
    # Extract citation IDs from answer [1], [2], etc.
    cited_ids: Set[int] = set(map(int, re.findall(r'\[(\d+)\]', answer)))
    
    # Find high-score contexts (>= 60%)
    high_score_threshold = 60.0
    high_score_contexts = [c for c in contexts if c.score >= high_score_threshold]
    high_score_cited = [c for c in high_score_contexts if c.citation_id in cited_ids]
    
    # Calculate metrics
    citation_coverage = len(cited_ids) / len(contexts) if contexts else 0
    high_score_usage = len(high_score_cited) / len(high_score_contexts) if high_score_contexts else 1.0
    
    # Generate warnings
    warnings = []
    
    # Warning if [1] (highest score) not cited
    if contexts and 1 not in cited_ids:
        warnings.append(f"⚠️ Citation [1] (highest score: {contexts[0].score:.1f}%) not used in answer")
    
    # Warning if high-score contexts not used
    if high_score_usage < 1.0:
        unused = [c.citation_id for c in high_score_contexts if c.citation_id not in cited_ids]
        warnings.append(f"⚠️ High-score contexts not cited: {unused}")
    
    # Log validation results
    logger.info(
        f"📊 Citation validation: cited={sorted(cited_ids)}, "
        f"coverage={citation_coverage:.0%}, high_score_usage={high_score_usage:.0%}"
    )
    
    return {
        "cited_ids": cited_ids,
        "citation_coverage": citation_coverage,
        "high_score_usage": high_score_usage,
        "warnings": warnings
    }


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
        # IMPORTANT: Use input_type="search_query" for queries (not "search_document")
        # Cohere Embed v3 optimizes vectors differently for queries vs documents
        query_embedding = self.embedding_service.embed_text(query, input_type="search_query")
        
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
    
    # ✅ FIX #3: ADAPTIVE HYBRID WEIGHTS FOR TECHNICAL QUERIES (Thread-safe)
    def retrieve_contexts(
        self,
        query: str,
        top_k: int = 3,  # Only top 3 most relevant results
        score_threshold: float = 0.3,  # 30% minimum - balanced for recall
        search_filter: Optional[SearchFilter] = None,
    ) -> List[RAGContext]:
        """
        Retrieve relevant contexts for a query.
        
        Uses Hybrid Retrieval (BM25 + Vector) if enabled.
        With adaptive weighting for technical queries.
        
        THREAD-SAFE: Uses local variables for weights to avoid race conditions.
        
        Args:
            query: User query
            top_k: Number of contexts to retrieve
            score_threshold: Minimum relevance score (default 0.3 = 30%)
            search_filter: Optional filter for documents
            
        Returns:
            List of RAGContext objects sorted by score with citation IDs
        """
        # ✅ FIX: Detect technical queries for adaptive weighting
        technical_keywords = [
            'là gì', 'định nghĩa', 'khái niệm', 'công thức', 'phương pháp',
            'what is', 'definition', 'formula', 'method', 'concept'
        ]
        is_technical = any(kw in query.lower() for kw in technical_keywords)
        
        # ✅ FIX #1: Use LOCAL variables instead of mutating instance state (thread-safe)
        bm25_w = 0.5 if is_technical else self.bm25_weight
        vector_w = 0.5 if is_technical else self.vector_weight
        
        if is_technical and self.use_hybrid:
            logger.info(f"Technical query detected: '{query[:50]}...' - Using balanced weights (BM25=0.5, Vector=0.5)")
        
        contexts = []
        
        # Try hybrid retrieval first
        if self.use_hybrid:
            try:
                # Initialize BM25 if needed
                self._init_bm25_from_qdrant()
                
                if self._bm25_initialized and self.bm25_index.doc_count > 0:
                    # ✅ FIX: Create hybrid retriever with LOCAL weights (thread-safe)
                    hybrid = HybridRetriever(
                        bm25_index=self.bm25_index,
                        vector_search_fn=lambda q, k: self._vector_search_fn(q, k),
                        bm25_weight=bm25_w,  # ✅ Local variable
                        vector_weight=vector_w  # ✅ Local variable
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
                    
                    # Convert to RAGContext (citation_id will be reassigned after sorting)
                    for r in results:
                        metadata = r.get("metadata", {})
                        contexts.append(RAGContext(
                            citation_id=0,  # Will be assigned after sorting
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
                    
            except Exception as e:
                logger.warning(f"Hybrid retrieval failed, falling back to vector: {e}")
                contexts = []  # Reset for fallback
        
        # Fallback to vector-only search if hybrid failed or not enabled
        if not contexts:
            query_embedding = self.embedding_service.embed_text(query, input_type="search_query")
            
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
        
        # ✅ FIX #2: Sort by score and assign citation IDs BEFORE returning
        if contexts:
            # Sort by score descending (highest first)
            contexts = sorted(contexts, key=lambda x: x.score, reverse=True)
            
            # Assign citation IDs based on rank: [1] = highest score
            for idx, ctx in enumerate(contexts, 1):
                ctx.citation_id = idx
            
            logger.info(
                f"✅ Citations ranked by score: "
                f"{[(c.citation_id, f'{c.score:.1f}%') for c in contexts]}"
            )
        
        return contexts
    
    def generate_answer(
        self,
        query: str,
        contexts: List[RAGContext],
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        language_preference: Optional[str] = None,
    ) -> RAGResponse:
        """
        Generate answer using Claude with retrieved contexts.
        
        Args:
            query: User query
            contexts: Retrieved contexts
            history: Optional conversation history
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            language_preference: Explicit language preference ("vi", "en", or None for auto)
            
        Returns:
            RAGResponse with answer and citations
        """
        # Get language context with conversation awareness
        lang_context = get_language_context(
            query=query,
            history=history,
            user_language_preference=language_preference
        )
        
        # Build prompt with improved template
        prompt = self.prompt_builder.build_prompt(query, contexts)
        
        # Select appropriate system prompt based on response language
        if lang_context.response_language == "vi":
            system_prompt = SYSTEM_PROMPTS_VI[self.template]
            logger.debug(f"Using Vietnamese prompt for query: {query[:50]}...")
        else:
            system_prompt = SYSTEM_PROMPTS[self.template]
        
        # Add explicit language instruction
        language_instruction = get_language_instruction(lang_context)
        system_prompt = system_prompt + "\n" + language_instruction
        
        # Generate response
        response = self.claude_service.invoke(
            prompt=prompt,
            system_prompt=system_prompt,
            history=history,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        # Add language switch notification if needed
        answer = response.text
        switch_msg = get_language_switch_message(lang_context)
        if switch_msg:
            answer = switch_msg + "\n\n" + answer
        
        # Validate citation quality
        validation = validate_citations(answer, contexts)
        if validation["warnings"]:
            for warning in validation["warnings"]:
                logger.warning(f"Citation quality: {warning}")
            logger.info(
                f"Citation metrics: coverage={validation['citation_coverage']:.0%}, "
                f"high_score_usage={validation['high_score_usage']:.0%}, "
                f"cited={validation['cited_ids']}"
            )
        
        # Extract citations
        citations = self.prompt_builder.extract_citations(contexts)
        
        return RAGResponse(
            answer=answer,
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
    
    def _handle_translation_request(
        self,
        query: str,
        history: List[Dict[str, str]],
        lang_context: LanguageContext,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> RAGResponse:
        """
        Handle translation/language switch requests.
        
        Instead of searching RAG, uses the last assistant response
        and translates it to the target language.
        
        Args:
            query: User's translation request
            history: Conversation history
            lang_context: Language context with target language
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            stream: Whether to stream response
            
        Returns:
            RAGResponse with translated content
        """
        # Find last assistant message to translate
        last_assistant_msg = None
        for msg in reversed(history):
            if msg.get("role") == "assistant":
                last_assistant_msg = msg.get("content", "")
                break
        
        if not last_assistant_msg:
            # No previous response to translate
            if lang_context.target_language == "vi":
                return RAGResponse(
                    answer="Không có câu trả lời trước đó để dịch.",
                    citations=[],
                    usage=TokenUsage(input_tokens=0, output_tokens=0),
                    model=self.claude_service.model_alias,
                    contexts_used=0,
                    query=query,
                )
            else:
                return RAGResponse(
                    answer="No previous response to translate.",
                    citations=[],
                    usage=TokenUsage(input_tokens=0, output_tokens=0),
                    model=self.claude_service.model_alias,
                    contexts_used=0,
                    query=query,
                )
        
        # Build translation prompt
        if lang_context.target_language == "vi":
            system_prompt = """Bạn là trợ lý dịch thuật chuyên nghiệp.
Dịch nội dung sau sang tiếng Việt một cách tự nhiên và chính xác.
Giữ nguyên format, citations [1], [2], và thuật ngữ kỹ thuật quan trọng."""
            prompt = f"Dịch nội dung sau sang tiếng Việt:\n\n{last_assistant_msg}"
        else:
            system_prompt = """You are a professional translation assistant.
Translate the following content to English naturally and accurately.
Preserve the format, citations [1], [2], and important technical terms."""
            prompt = f"Translate the following to English:\n\n{last_assistant_msg}"
        
        # Generate translation
        response = self.claude_service.invoke(
            prompt=prompt,
            system_prompt=system_prompt,
            history=None,  # Don't include history for translation
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        # Add language switch notification
        if lang_context.target_language == "vi":
            prefix = "📝 **Bản dịch tiếng Việt:**\n\n"
        else:
            prefix = "📝 **English translation:**\n\n"
        
        return RAGResponse(
            answer=prefix + response.text,
            citations=[],  # No new citations for translation
            usage=response.usage,
            model=response.model,
            contexts_used=0,
            query=query,
        )
    
    # ✅ OPTIMIZED FOR PRECISION
    def query(
        self,
        query: str,
        top_k: int = 3,  # Only top 3 most relevant results
        score_threshold: float = 0.3,  # 30% minimum - balanced for recall
        search_filter: Optional[SearchFilter] = None,
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        stream: bool = False,
        language_preference: Optional[str] = None,
    ):
        """
        Complete RAG query: retrieve + generate.
        
        OPTIMIZED FOR PRECISION:
        - top_k=3 for focused, high-quality results
        - score_threshold=0.3 (30%) balanced for recall
        - Only returns results that are truly relevant to the query
        - Bilingual support with conversation-aware language detection
        - Translation request handling (uses history instead of RAG search)
        
        Args:
            query: User query
            top_k: Number of contexts to retrieve (default 3)
            score_threshold: Minimum relevance score (default 0.5 = 50%)
            search_filter: Optional document filter
            history: Optional conversation history
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            stream: Whether to stream response
            language_preference: Explicit language preference ("vi", "en", or None for auto)
            
        Returns:
            RAGResponse or Generator[StreamChunk] if streaming
        """
        # ✅ Check for translation request FIRST
        lang_context = get_language_context(
            query=query,
            history=history,
            user_language_preference=language_preference
        )
        
        if lang_context.is_translation_request and history:
            logger.info(f"Translation request detected: translating to {lang_context.target_language}")
            return self._handle_translation_request(
                query=query,
                history=history,
                lang_context=lang_context,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream,
            )
        
        # Retrieve contexts with improved settings
        contexts = self.retrieve_contexts(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            search_filter=search_filter,
        )
        
        if not contexts:
            logger.warning(f"No contexts found for query (threshold={score_threshold}): {query[:50]}...")
            
            # Return empty context feedback with language-aware message
            lang_context = get_language_context(
                query=query,
                history=history,
                user_language_preference=language_preference
            )
            
            if lang_context.response_language == "vi":
                empty_message = (
                    "⚠️ Không tìm thấy thông tin liên quan trong tài liệu.\n\n"
                    "Vui lòng thử:\n"
                    "- Đặt câu hỏi cụ thể hơn\n"
                    "- Sử dụng từ khóa khác\n"
                    "- Kiểm tra xem tài liệu đã được upload chưa"
                )
            else:
                empty_message = (
                    "⚠️ No relevant information found in the documents.\n\n"
                    "Please try:\n"
                    "- Asking a more specific question\n"
                    "- Using different keywords\n"
                    "- Checking if documents have been uploaded"
                )
            
            return RAGResponse(
                answer=empty_message,
                citations=[],
                usage=TokenUsage(input_tokens=0, output_tokens=0),
                model=self.claude_service.model_alias,
                contexts_used=0,
                query=query,
            )
        
        # CRITICAL: Sort contexts by score and reassign citation IDs
        # This ensures [1] = highest score, [2] = second highest, etc.
        contexts = self.prompt_builder.rank_contexts_by_score(contexts)
        
        logger.info(
            f"Retrieved {len(contexts)} contexts (sorted by score): "
            f"{[(c.citation_id, f'{c.score:.1f}%') for c in contexts]}"
        )
        
        # Generate answer with language awareness
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
                language_preference=language_preference,
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
