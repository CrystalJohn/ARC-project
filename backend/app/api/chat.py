"""
Task #28: POST /api/chat endpoint
Task #29: Chat history storage in DynamoDB
Task #30: Rate limiting for Claude API calls
Task #31: Fallback to Claude Haiku on budget limit

Chat API for RAG-based question answering with citations.
Includes conversation history storage and retrieval for context.
Includes rate limiting to prevent API abuse.
Includes automatic model fallback based on budget.
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.rag_service import RAGService, PromptTemplate, RAGResponse
from app.services.qdrant_client import SearchFilter
from app.services.chat_history_manager import (
    ChatHistoryManager,
    ChatMessage,
    MessageRole,
)
from app.services.rate_limiter import (
    RateLimiter,
    RateLimitExceeded,
    get_rate_limiter,
)
from app.services.budget_manager import get_budget_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request payload."""
    query: str = Field(..., min_length=1, max_length=2000, description="User question")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for history")
    user_id: Optional[str] = Field("anonymous", description="User ID for history tracking")
    doc_ids: Optional[List[str]] = Field(None, description="Filter by specific documents")
    template: Optional[str] = Field("default", description="Prompt template: default, academic, concise, detailed")
    top_k: Optional[int] = Field(3, ge=1, le=10, description="Number of context chunks (max 3 for best quality)")
    stream: Optional[bool] = Field(False, description="Enable streaming response")
    include_history: Optional[bool] = Field(True, description="Include conversation history in context")
    language: Optional[str] = Field("auto", description="Response language: 'vi', 'en', or 'auto' for automatic detection")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the main data structures discussed?",
                "conversation_id": None,
                "user_id": "anonymous",
                "doc_ids": None,
                "template": "default",
                "top_k": 5,
                "stream": False,
                "include_history": True
            }
        }


class CitationResponse(BaseModel):
    """Citation in response."""
    id: int
    doc_id: str
    page: int
    text_snippet: str
    score: float


class UsageResponse(BaseModel):
    """Token usage in response."""
    input_tokens: int
    output_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    """Chat response payload."""
    answer: str
    citations: List[CitationResponse]
    conversation_id: str
    usage: UsageResponse
    model: str
    contexts_used: int
    query: str
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Based on [1], the main data structures are...",
                "citations": [
                    {"id": 1, "doc_id": "doc-123", "page": 5, "text_snippet": "Arrays are...", "score": 0.85}
                ],
                "conversation_id": "conv-abc123",
                "usage": {"input_tokens": 500, "output_tokens": 200, "total_tokens": 700},
                "model": "sonnet",
                "contexts_used": 3,
                "query": "What are the main data structures?",
                "timestamp": "2025-12-04T10:30:00Z"
            }
        }


# Global service instances (lazy initialization)
_rag_service: Optional[RAGService] = None
_chat_history_manager: Optional[ChatHistoryManager] = None


def get_rag_service() -> RAGService:
    """Get or create RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService(
            qdrant_host="localhost",
            qdrant_port=6333,
            region_name="ap-southeast-1",
            model="sonnet",
            use_hybrid=False,  # Disabled - BM25 init issue, vector-only works well
            # TODO: Fix BM25 initialization before enabling hybrid
            # bm25_weight=0.3,
            # vector_weight=0.7,
        )
    return _rag_service


def get_chat_history_manager() -> ChatHistoryManager:
    """Get or create ChatHistoryManager instance."""
    global _chat_history_manager
    if _chat_history_manager is None:
        _chat_history_manager = ChatHistoryManager()
    return _chat_history_manager


def _convert_rag_response(
    rag_response: RAGResponse,
    conversation_id: str,
) -> ChatResponse:
    """Convert RAGResponse to ChatResponse."""
    return ChatResponse(
        answer=rag_response.answer,
        citations=[
            CitationResponse(
                id=c.id,
                doc_id=c.doc_id,
                page=c.page,
                text_snippet=c.text_snippet,
                score=c.score,
            )
            for c in rag_response.citations
        ],
        conversation_id=conversation_id,
        usage=UsageResponse(
            input_tokens=rag_response.usage.input_tokens,
            output_tokens=rag_response.usage.output_tokens,
            total_tokens=rag_response.usage.total_tokens,
        ),
        model=rag_response.model,
        contexts_used=rag_response.contexts_used,
        query=rag_response.query,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, response: Response):
    """
    Send a chat message and get RAG-based response with citations.
    
    The endpoint retrieves relevant document chunks from the vector database,
    builds a prompt with context, and generates an answer using Claude.
    Conversation history is stored in DynamoDB and used for context.
    Rate limiting is applied per user and globally.
    
    - **query**: The user's question (required)
    - **conversation_id**: Optional ID to continue a conversation
    - **user_id**: User identifier for history tracking
    - **doc_ids**: Optional list of document IDs to search within
    - **template**: Prompt template style (default, academic, concise, detailed)
    - **top_k**: Number of context chunks to retrieve (1-20)
    - **include_history**: Include conversation history in context (default: true)
    """
    try:
        rag_service = get_rag_service()
        history_manager = get_chat_history_manager()
        rate_limiter = get_rate_limiter()
        
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or f"conv-{uuid.uuid4().hex[:12]}"
        user_id = request.user_id or "anonymous"
        
        # Estimate tokens for rate limiting (~4 chars per token)
        estimated_tokens = len(request.query) // 4 + 2000  # query + context + response
        
        # Check and acquire rate limit
        try:
            rate_limiter.acquire(
                user_id=user_id,
                estimated_tokens=estimated_tokens,
                wait=False
            )
        except RateLimitExceeded as e:
            # Add rate limit headers
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["Retry-After"] = str(int(e.retry_after))
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. {str(e)}",
                headers={"Retry-After": str(int(e.retry_after))}
            )
        
        # Add rate limit headers
        status = rate_limiter.check_rate_limit(user_id)
        response.headers["X-RateLimit-Remaining"] = str(status.requests_remaining)
        response.headers["X-RateLimit-Reset"] = str(int(status.reset_at))
        
        # Set template if specified
        if request.template:
            try:
                template = PromptTemplate(request.template)
                rag_service.set_template(template)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid template: {request.template}. Use: default, academic, concise, detailed"
                )
        
        # Build search filter
        search_filter = None
        if request.doc_ids:
            search_filter = SearchFilter(doc_ids=request.doc_ids)
        
        # Get conversation history for context
        history = None
        if request.include_history and request.conversation_id:
            try:
                history = history_manager.get_history_for_context(
                    conversation_id=conversation_id,
                    max_messages=10,
                )
                logger.debug(f"Loaded {len(history)} messages from history")
            except Exception as e:
                logger.warning(f"Failed to load history: {e}")
                history = None
        
        # Save user message to history
        try:
            history_manager.save_user_message(
                conversation_id=conversation_id,
                content=request.query,
                user_id=user_id,
            )
        except Exception as e:
            logger.warning(f"Failed to save user message: {e}")
        
        # Determine language preference
        language_pref = None
        if request.language and request.language != "auto":
            language_pref = request.language
        
        # Execute RAG query with history and language preference
        rag_response = rag_service.query(
            query=request.query,
            top_k=request.top_k or 3,
            search_filter=search_filter,
            history=history,
            stream=False,
            language_preference=language_pref,
        )
        
        # Save assistant response to history
        try:
            history_manager.save_assistant_message(
                conversation_id=conversation_id,
                content=rag_response.answer,
                user_id=user_id,
                citations=[c.__dict__ if hasattr(c, '__dict__') else c for c in rag_response.citations] if rag_response.citations else None,
                usage=rag_response.usage.to_dict() if rag_response.usage else None,
                model=rag_response.model,
            )
        except Exception as e:
            logger.warning(f"Failed to save assistant message: {e}")
        
        # Record actual token usage for rate limiter
        if rag_response.usage:
            rate_limiter.record_usage(user_id, rag_response.usage.total_tokens)
        
        # Convert and return response
        return _convert_rag_response(rag_response, conversation_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Send a chat message and get streaming RAG-based response.
    
    Returns Server-Sent Events (SSE) stream with text chunks.
    """
    try:
        rag_service = get_rag_service()
        
        # Set template
        if request.template:
            try:
                template = PromptTemplate(request.template)
                rag_service.set_template(template)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid template: {request.template}")
        
        # Build search filter
        search_filter = None
        if request.doc_ids:
            search_filter = SearchFilter(doc_ids=request.doc_ids)
        
        # Retrieve contexts first
        contexts = rag_service.retrieve_contexts(
            query=request.query,
            top_k=request.top_k or 5,
            search_filter=search_filter,
        )
        
        # Generate streaming response
        async def generate():
            try:
                for chunk in rag_service.generate_answer_stream(
                    query=request.query,
                    contexts=contexts,
                ):
                    if chunk.text:
                        yield f"data: {chunk.text}\n\n"
                    if chunk.is_final:
                        yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f"data: [ERROR] {str(e)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stream chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def chat_health():
    """Check health of chat service components."""
    try:
        rag_service = get_rag_service()
        health = rag_service.health_check()
        
        all_healthy = all(health.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "components": health,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@router.get("/rate-limit")
async def get_rate_limit_status(
    user_id: str = Query("anonymous", description="User ID to check"),
):
    """
    Get current rate limit status for a user.
    
    Returns remaining requests/tokens and reset time.
    """
    try:
        rate_limiter = get_rate_limiter()
        status = rate_limiter.check_rate_limit(user_id)
        stats = rate_limiter.get_stats()
        
        return {
            "user_id": user_id,
            "status": status.to_dict(),
            "global_stats": stats,
        }
    except Exception as e:
        logger.error(f"Failed to get rate limit status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/budget")
async def get_budget_status(
    user_id: str = Query("anonymous", description="User ID to check"),
):
    """
    Get current budget status and model recommendation.
    
    Returns spending info and whether Haiku fallback is active.
    """
    try:
        budget_manager = get_budget_manager()
        status = budget_manager.get_status(user_id)
        user_spending = budget_manager.get_user_spending(user_id)
        stats = budget_manager.get_stats()
        
        return {
            "user_id": user_id,
            "status": status.to_dict(),
            "user_spending": user_spending,
            "global_stats": stats,
        }
    except Exception as e:
        logger.error(f"Failed to get budget status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Chat History Endpoints ==============

class ConversationListResponse(BaseModel):
    """Response for listing conversations."""
    conversations: List[Dict[str, Any]]
    has_more: bool


class ConversationHistoryResponse(BaseModel):
    """Response for conversation history."""
    conversation_id: str
    messages: List[Dict[str, Any]]
    total: int


@router.get("/history", response_model=ConversationListResponse)
async def list_conversations(
    user_id: str = Query("anonymous", description="User ID"),
    limit: int = Query(20, ge=1, le=100, description="Max conversations to return"),
):
    """
    List conversations for a user.
    
    Returns a list of conversations with their last message preview.
    """
    try:
        history_manager = get_chat_history_manager()
        result = history_manager.list_conversations(
            user_id=user_id,
            limit=limit,
        )
        
        return ConversationListResponse(
            conversations=result["conversations"],
            has_more=result.get("last_evaluated_key") is not None,
        )
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200, description="Max messages to return"),
):
    """
    Get messages for a specific conversation.
    
    Returns messages in chronological order (oldest first).
    """
    try:
        history_manager = get_chat_history_manager()
        messages = history_manager.get_conversation_history(
            conversation_id=conversation_id,
            limit=limit,
            ascending=True,
        )
        
        return ConversationHistoryResponse(
            conversation_id=conversation_id,
            messages=[msg.to_dict() for msg in messages],
            total=len(messages),
        )
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user_id: str = Query("anonymous", description="User ID"),
):
    """
    Delete a conversation and all its messages.
    """
    try:
        history_manager = get_chat_history_manager()
        deleted = history_manager.delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        
        return {
            "conversation_id": conversation_id,
            "deleted_messages": deleted,
            "status": "deleted",
        }
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
