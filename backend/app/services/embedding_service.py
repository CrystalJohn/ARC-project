"""
Embedding Service using Cohere via AWS Bedrock

Generates embeddings for text chunks using Cohere Embed model.
"""
import json
import logging
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CohereEmbeddingService:
    """
    Embedding service using Cohere Embed via Bedrock.
    
    Model: cohere.embed-english-v3 (1024 dimensions)
    """
    
    MODEL_ID = "cohere.embed-english-v3"
    VECTOR_SIZE = 1024
    BATCH_SIZE = 96  # Cohere supports up to 96 texts per request
    
    def __init__(self, region: str = "ap-southeast-1"):
        self.region = region
        self.client = boto3.client("bedrock-runtime", region_name=region)
        logger.info(f"Initialized Cohere Embedding Service in {region}")
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats (1024 dimensions) or None on error
        """
        result = self.embed_texts([text])
        return result[0] if result else None
    
    def embed_texts(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (1024 dimensions each)
        """
        if not texts:
            return []
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.BATCH_SIZE):
            batch = texts[i:i + self.BATCH_SIZE]
            batch_embeddings = self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    def _embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Embed a batch of texts."""
        try:
            # Prepare request body for Cohere
            body = json.dumps({
                "texts": texts,
                "input_type": "search_document",  # or "search_query" for queries
                "truncate": "END"  # Truncate long texts from end
            })
            
            response = self.client.invoke_model(
                modelId=self.MODEL_ID,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            result = json.loads(response["body"].read())
            embeddings = result.get("embeddings", [])
            
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"Bedrock API error: {error_code} - {e}")
            return [None] * len(texts)
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return [None] * len(texts)


def create_embedding_callback(region: str = "ap-southeast-1"):
    """
    Create embedding callback function for SQS Worker.
    
    Returns:
        Function that takes text and returns embedding vector
    """
    service = CohereEmbeddingService(region=region)
    
    def callback(text: str) -> Optional[List[float]]:
        return service.embed_text(text)
    
    return callback
