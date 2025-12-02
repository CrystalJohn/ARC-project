"""
Task #20: Embeddings Service using Bedrock

Generates 1024-dimensional embeddings using Cohere Embed Multilingual v3.
Supports batch processing and exponential backoff retry.
"""

import json
import time
import logging
from typing import List, Optional
from dataclasses import dataclass

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    text: str
    embedding: List[float]
    dimensions: int


class EmbeddingsService:
    """
    Embeddings service using AWS Bedrock.
    
    Uses Cohere Embed Multilingual v3 for 1024-dimensional embeddings.
    
    Requirements:
    - 7.1: Return 1024-dimensional vectors
    - 7.2: Batch processing up to 25 texts per API call
    - 7.3: Exponential backoff with max 5 retries
    - 7.4: Log errors and mark documents as FAILED
    """
    
    # Cohere supports batch embedding natively
    MODEL_ID = "cohere.embed-multilingual-v3"
    BATCH_SIZE = 25  # Cohere supports up to 96, but we use 25 per spec
    VECTOR_SIZE = 1024
    MAX_RETRIES = 5
    
    def __init__(
        self,
        region: str = "ap-southeast-1",
        bedrock_client: Optional[boto3.client] = None,
    ):
        """
        Initialize embeddings service.
        
        Args:
            region: AWS region
            bedrock_client: Optional pre-configured Bedrock client
        """
        self.region = region
        self.client = bedrock_client or boto3.client(
            'bedrock-runtime',
            region_name=region
        )
        
        logger.info(f"Initialized EmbeddingsService with model {self.MODEL_ID}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            1024-dimensional embedding vector
        """
        embeddings = self.embed_texts([text])
        return embeddings[0] if embeddings else []
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with batch processing.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of 1024-dimensional embedding vectors
        """
        if not texts:
            return []
        
        all_embeddings = []
        
        # Process in batches of BATCH_SIZE
        for i in range(0, len(texts), self.BATCH_SIZE):
            batch = texts[i:i + self.BATCH_SIZE]
            batch_embeddings = self._embed_batch_with_retry(batch)
            all_embeddings.extend(batch_embeddings)
            
            # Log progress for large batches
            if len(texts) > self.BATCH_SIZE:
                logger.info(
                    f"Embedded batch {i // self.BATCH_SIZE + 1}/"
                    f"{(len(texts) + self.BATCH_SIZE - 1) // self.BATCH_SIZE}"
                )
        
        return all_embeddings
    
    def _embed_batch_with_retry(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a batch of texts with exponential backoff retry.
        
        Retry delays: 1s, 2s, 4s, 8s, 16s (exponential backoff)
        
        Args:
            texts: Batch of texts (max BATCH_SIZE)
            
        Returns:
            List of embedding vectors
        """
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                return self._embed_batch(texts)
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                last_error = e
                
                # Check if it's a throttling error
                if error_code in ['ThrottlingException', 'TooManyRequestsException']:
                    delay = 2 ** attempt  # 1, 2, 4, 8, 16 seconds
                    logger.warning(
                        f"Throttled on attempt {attempt + 1}/{self.MAX_RETRIES}, "
                        f"retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    # Non-throttling error, don't retry
                    logger.error(f"Bedrock API error: {e}")
                    raise
                    
            except Exception as e:
                last_error = e
                delay = 2 ** attempt
                logger.warning(
                    f"Error on attempt {attempt + 1}/{self.MAX_RETRIES}: {e}, "
                    f"retrying in {delay}s..."
                )
                time.sleep(delay)
        
        # All retries exhausted
        logger.error(f"Failed after {self.MAX_RETRIES} retries: {last_error}")
        raise last_error
    
    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a batch of texts using Cohere model.
        
        Args:
            texts: Batch of texts
            
        Returns:
            List of embedding vectors
        """
        # Cohere Embed API request body
        body = json.dumps({
            "texts": texts,
            "input_type": "search_document",  # For document storage
            # "truncate": "END"  # Optional: truncate long texts
        })
        
        response = self.client.invoke_model(
            modelId=self.MODEL_ID,
            body=body,
        )
        
        result = json.loads(response['body'].read())
        embeddings = result.get('embeddings', [])
        
        # Validate dimensions
        for i, emb in enumerate(embeddings):
            if len(emb) != self.VECTOR_SIZE:
                logger.warning(
                    f"Unexpected embedding dimension: {len(emb)} "
                    f"(expected {self.VECTOR_SIZE})"
                )
        
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        
        Uses 'search_query' input type for better search results.
        
        Args:
            query: Search query text
            
        Returns:
            1024-dimensional embedding vector
        """
        body = json.dumps({
            "texts": [query],
            "input_type": "search_query",  # For query embedding
        })
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.invoke_model(
                    modelId=self.MODEL_ID,
                    body=body,
                )
                
                result = json.loads(response['body'].read())
                embeddings = result.get('embeddings', [])
                
                if embeddings:
                    return embeddings[0]
                return []
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                
                if error_code in ['ThrottlingException', 'TooManyRequestsException']:
                    delay = 2 ** attempt
                    logger.warning(f"Throttled, retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise
        
        raise Exception(f"Failed to embed query after {self.MAX_RETRIES} retries")
    
    def health_check(self) -> bool:
        """Check if embeddings service is healthy."""
        try:
            # Try to embed a simple text
            embedding = self.embed_text("health check")
            return len(embedding) == self.VECTOR_SIZE
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Convenience function
def create_embeddings_service(
    region: str = "ap-southeast-1",
) -> EmbeddingsService:
    """Create embeddings service instance."""
    return EmbeddingsService(region=region)
