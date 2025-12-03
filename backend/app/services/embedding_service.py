"""
Embedding Service using Cohere Embed via AWS Bedrock

Generates embeddings for text chunks using Cohere Embed English v3 model.
"""
import json
import logging
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CohereEmbeddingService:
    """
    Embedding service using Cohere Embed English v3 via Bedrock.
    
    Model: cohere.embed-english-v3 (1024 dimensions)
    """
    
    MODEL_ID = "cohere.embed-multilingual-v3"  # Supports Vietnamese and 100+ languages
    VECTOR_SIZE = 1024  # Cohere outputs 1024 dimensions
    BATCH_SIZE = 96  # Cohere supports batch processing up to 96 texts
    
    def __init__(self, region: str = "ap-southeast-1"):
        self.bedrock_region = region  # Use ap-southeast-1 for Cohere
        self.region = region
        self.client = boto3.client("bedrock-runtime", region_name=self.bedrock_region)
        logger.info(f"Initialized Cohere Embedding Service (Bedrock: {self.bedrock_region})")
    
    def embed_text(self, text: str, input_type: str = "search_document") -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            input_type: "search_document" for indexing, "search_query" for searching
            
        Returns:
            List of floats (1024 dimensions) or None on error
        """
        try:
            # Truncate text if too long (Cohere limit is ~512 tokens)
            if len(text) > 2000:
                text = text[:2000]
            
            body = json.dumps({
                "texts": [text],
                "input_type": input_type
            })
            
            response = self.client.invoke_model(
                modelId=self.MODEL_ID,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            result = json.loads(response["body"].read())
            embeddings = result.get("embeddings", [])
            
            return embeddings[0] if embeddings else None
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"Bedrock API error: {error_code} - {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def embed_texts(self, texts: List[str], input_type: str = "search_document") -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts (batch processing).
        
        Args:
            texts: List of texts to embed
            input_type: "search_document" for indexing, "search_query" for searching
            
        Returns:
            List of embeddings (1024 dimensions each)
        """
        if not texts:
            return []
        
        all_embeddings = []
        
        # Process in batches of BATCH_SIZE
        for i in range(0, len(texts), self.BATCH_SIZE):
            batch = texts[i:i + self.BATCH_SIZE]
            
            # Truncate texts if too long
            batch = [t[:2000] if len(t) > 2000 else t for t in batch]
            
            try:
                body = json.dumps({
                    "texts": batch,
                    "input_type": input_type
                })
                
                response = self.client.invoke_model(
                    modelId=self.MODEL_ID,
                    body=body,
                    contentType="application/json",
                    accept="application/json"
                )
                
                result = json.loads(response["body"].read())
                embeddings = result.get("embeddings", [])
                all_embeddings.extend(embeddings)
                
            except Exception as e:
                logger.error(f"Error generating batch embeddings: {e}")
                # Return None for failed batch
                all_embeddings.extend([None] * len(batch))
        
        return all_embeddings


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
