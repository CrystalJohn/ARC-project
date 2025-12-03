"""
Task #26: Bedrock Claude 3.5 Sonnet Integration

Provides Claude API wrapper with streaming support and token counting.
Model: anthropic.claude-3-5-sonnet-20240620-v1:0
"""

import json
import logging
from typing import Optional, Generator, Dict, Any, List
from dataclasses import dataclass, field
import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)

# Model configurations
CLAUDE_MODELS = {
    "sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "haiku": "anthropic.claude-3-haiku-20240307-v1:0",
}

# Pricing per 1M tokens (USD)
MODEL_PRICING = {
    "sonnet": {"input": 3.0, "output": 15.0},
    "haiku": {"input": 0.25, "output": 1.25},
}

# Token estimation: ~4 chars per token for English
CHARS_PER_TOKEN = 4


@dataclass
class TokenUsage:
    """Token usage statistics."""
    input_tokens: int = 0
    output_tokens: int = 0
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
    
    def estimate_cost(self, model: str = "sonnet") -> float:
        """Estimate cost in USD."""
        pricing = MODEL_PRICING.get(model, MODEL_PRICING["sonnet"])
        input_cost = (self.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class ClaudeResponse:
    """Response from Claude API."""
    text: str
    usage: TokenUsage
    model: str
    stop_reason: str = "end_turn"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "usage": self.usage.to_dict(),
            "model": self.model,
            "stop_reason": self.stop_reason,
        }


@dataclass
class StreamChunk:
    """Chunk from streaming response."""
    text: str
    is_final: bool = False
    usage: Optional[TokenUsage] = None


class ClaudeService:
    """
    Claude 3.5 Sonnet service with streaming support.
    
    Features:
    - Sync and streaming inference
    - Token counting and cost estimation
    - Automatic retry with exponential backoff
    - Model switching (Sonnet/Haiku)
    """
    
    ANTHROPIC_VERSION = "bedrock-2023-05-31"
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TEMPERATURE = 0.7
    
    def __init__(
        self,
        region_name: str = "ap-southeast-1",
        model: str = "sonnet",
        max_retries: int = 3,
    ):
        """
        Initialize Claude service.
        
        Args:
            region_name: AWS region
            model: Model alias ("sonnet" or "haiku")
            max_retries: Max retry attempts
        """
        self.region_name = region_name
        self.model_alias = model
        self.model_id = CLAUDE_MODELS.get(model, CLAUDE_MODELS["sonnet"])
        
        # Configure boto3 with retries
        config = Config(
            region_name=region_name,
            retries={"max_attempts": max_retries, "mode": "adaptive"},
        )
        
        self.client = boto3.client("bedrock-runtime", config=config)
        logger.info(f"Initialized Claude service with model: {self.model_id}")
    
    def switch_model(self, model: str) -> None:
        """Switch to different model (sonnet/haiku)."""
        if model in CLAUDE_MODELS:
            self.model_alias = model
            self.model_id = CLAUDE_MODELS[model]
            logger.info(f"Switched to model: {self.model_id}")
        else:
            raise ValueError(f"Unknown model: {model}. Use 'sonnet' or 'haiku'")
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text."""
        return len(text) // CHARS_PER_TOKEN + 1
    
    def _build_messages(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> tuple[List[Dict], Optional[str]]:
        """Build messages array for Claude API."""
        messages = []
        
        # Add history if provided
        if history:
            messages.extend(history)
        
        # Add current user message
        messages.append({"role": "user", "content": prompt})
        
        return messages, system_prompt
    
    def invoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> ClaudeResponse:
        """
        Invoke Claude synchronously.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            history: Optional conversation history
            max_tokens: Maximum output tokens
            temperature: Sampling temperature (0-1)
            
        Returns:
            ClaudeResponse with text and usage
        """
        messages, system = self._build_messages(prompt, system_prompt, history)
        
        # Build request body
        body = {
            "anthropic_version": self.ANTHROPIC_VERSION,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }
        
        if system:
            body["system"] = system
        
        # Invoke model
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
        )
        
        # Parse response
        result = json.loads(response["body"].read())
        
        text = result["content"][0]["text"]
        usage = TokenUsage(
            input_tokens=result.get("usage", {}).get("input_tokens", 0),
            output_tokens=result.get("usage", {}).get("output_tokens", 0),
        )
        
        return ClaudeResponse(
            text=text,
            usage=usage,
            model=self.model_alias,
            stop_reason=result.get("stop_reason", "end_turn"),
        )

    
    def invoke_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> Generator[StreamChunk, None, None]:
        """
        Invoke Claude with streaming response.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            history: Optional conversation history
            max_tokens: Maximum output tokens
            temperature: Sampling temperature (0-1)
            
        Yields:
            StreamChunk objects with text fragments
        """
        messages, system = self._build_messages(prompt, system_prompt, history)
        
        # Build request body
        body = {
            "anthropic_version": self.ANTHROPIC_VERSION,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }
        
        if system:
            body["system"] = system
        
        # Invoke with streaming
        response = self.client.invoke_model_with_response_stream(
            modelId=self.model_id,
            body=json.dumps(body),
        )
        
        # Process stream
        usage = TokenUsage()
        
        for event in response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            
            # Handle different event types
            if chunk["type"] == "content_block_delta":
                delta = chunk.get("delta", {})
                if delta.get("type") == "text_delta":
                    yield StreamChunk(text=delta.get("text", ""))
            
            elif chunk["type"] == "message_delta":
                # Final message with usage stats
                delta_usage = chunk.get("usage", {})
                usage.output_tokens = delta_usage.get("output_tokens", 0)
            
            elif chunk["type"] == "message_start":
                # Initial message with input token count
                message = chunk.get("message", {})
                msg_usage = message.get("usage", {})
                usage.input_tokens = msg_usage.get("input_tokens", 0)
            
            elif chunk["type"] == "message_stop":
                # Stream complete
                yield StreamChunk(text="", is_final=True, usage=usage)
    
    def invoke_with_context(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        stream: bool = False,
    ):
        """
        Invoke Claude with RAG context.
        
        Formats contexts with citation markers for RAG responses.
        
        Args:
            query: User query
            contexts: List of RAGContext dicts with text, citation_id, doc_id, page
            system_prompt: Optional system prompt (will be enhanced with RAG instructions)
            history: Optional conversation history
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            stream: Whether to stream response
            
        Returns:
            ClaudeResponse or Generator[StreamChunk] if streaming
        """
        # Build context section
        context_parts = []
        for ctx in contexts:
            citation_id = ctx.get("citation_id", 0)
            text = ctx.get("text", "")
            doc_id = ctx.get("doc_id", "unknown")
            page = ctx.get("page", 1)
            
            context_parts.append(
                f"[{citation_id}] (Document: {doc_id}, Page {page})\n{text}"
            )
        
        context_section = "\n\n---\n\n".join(context_parts)
        
        # Build RAG prompt
        rag_prompt = f"""Based on the following context, answer the user's question.
Use citations like [1], [2] to reference the source documents.
If the context doesn't contain relevant information, say so.

CONTEXT:
{context_section}

USER QUESTION:
{query}"""
        
        # Enhance system prompt
        rag_system = system_prompt or ""
        rag_system += """
You are a helpful research assistant. Answer questions based on the provided context.
Always cite your sources using [1], [2], etc. format.
Be concise and accurate."""
        
        if stream:
            return self.invoke_stream(
                prompt=rag_prompt,
                system_prompt=rag_system.strip(),
                history=history,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        else:
            return self.invoke(
                prompt=rag_prompt,
                system_prompt=rag_system.strip(),
                history=history,
                max_tokens=max_tokens,
                temperature=temperature,
            )
    
    def health_check(self) -> bool:
        """Check if Claude service is available."""
        try:
            response = self.invoke(
                prompt="Say 'OK' only.",
                max_tokens=10,
                temperature=0,
            )
            return len(response.text) > 0
        except Exception as e:
            logger.error(f"Claude health check failed: {e}")
            return False


# Convenience function
def create_claude_service(
    region_name: str = "ap-southeast-1",
    model: str = "sonnet",
) -> ClaudeService:
    """Create Claude service instance."""
    return ClaudeService(region_name=region_name, model=model)
