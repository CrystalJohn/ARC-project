"""
Task #19: Qdrant Vector Database Client

Provides interface for storing and searching document embeddings.
Collection: documents | Dimensions: 1024 | Metric: Cosine
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType,
)

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result from Qdrant."""
    id: str
    score: float
    doc_id: str
    chunk_index: int
    page: int
    text: str
    is_table: bool


class QdrantVectorStore:
    """
    Qdrant vector store for document embeddings.
    
    Requirements:
    - 6.1: Collection with 1024-dim vectors and cosine similarity
    - 6.2: Payload indexing for doc_id, page, is_table
    - 6.3: Persist vectors to disk
    - 6.4: Recover vectors after restart
    """
    
    COLLECTION_NAME = "documents"
    VECTOR_SIZE = 1024
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        grpc_port: int = 6334,
        prefer_grpc: bool = False,
    ):
        """
        Initialize Qdrant client.
        
        Args:
            host: Qdrant server host
            port: Qdrant REST API port
            grpc_port: Qdrant gRPC port
            prefer_grpc: Use gRPC instead of REST
        """
        self.host = host
        self.port = port
        self.grpc_port = grpc_port
        
        self.client = QdrantClient(
            host=host,
            port=port,
            grpc_port=grpc_port,
            prefer_grpc=prefer_grpc,
        )
        
        logger.info(f"Connected to Qdrant at {host}:{port}")
    
    def ensure_collection(self) -> bool:
        """
        Ensure collection exists with correct configuration.
        Creates collection if it doesn't exist.
        
        Returns:
            True if collection exists or was created
        """
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.COLLECTION_NAME in collection_names:
                logger.info(f"Collection '{self.COLLECTION_NAME}' already exists")
                return True
            
            # Create collection with 1024-dim vectors and cosine similarity
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            
            # Create payload indexes for filtering
            self._create_payload_indexes()
            
            logger.info(f"Created collection '{self.COLLECTION_NAME}'")
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            return False
    
    def _create_payload_indexes(self):
        """Create payload indexes for efficient filtering."""
        try:
            # Index for doc_id (keyword for exact match)
            self.client.create_payload_index(
                collection_name=self.COLLECTION_NAME,
                field_name="doc_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            
            # Index for page (integer)
            self.client.create_payload_index(
                collection_name=self.COLLECTION_NAME,
                field_name="page",
                field_schema=PayloadSchemaType.INTEGER,
            )
            
            # Index for is_table (bool as keyword)
            self.client.create_payload_index(
                collection_name=self.COLLECTION_NAME,
                field_name="is_table",
                field_schema=PayloadSchemaType.BOOL,
            )
            
            logger.info("Created payload indexes")
            
        except Exception as e:
            logger.warning(f"Error creating indexes (may already exist): {e}")
    
    def upsert_vectors(
        self,
        doc_id: str,
        texts: List[str],
        vectors: List[List[float]],
        pages: Optional[List[int]] = None,
        is_tables: Optional[List[bool]] = None,
    ) -> int:
        """
        Upsert document vectors to Qdrant.
        
        Args:
            doc_id: Document ID
            texts: List of chunk texts
            vectors: List of embedding vectors (1024-dim each)
            pages: Optional list of page numbers
            is_tables: Optional list of is_table flags
            
        Returns:
            Number of vectors upserted
        """
        if len(texts) != len(vectors):
            raise ValueError("texts and vectors must have same length")
        
        if not vectors:
            return 0
        
        # Validate vector dimensions
        for i, vec in enumerate(vectors):
            if len(vec) != self.VECTOR_SIZE:
                raise ValueError(
                    f"Vector {i} has {len(vec)} dimensions, expected {self.VECTOR_SIZE}"
                )
        
        # Default values
        if pages is None:
            pages = [1] * len(texts)
        if is_tables is None:
            is_tables = [False] * len(texts)
        
        # Create points
        points = []
        for i, (text, vector, page, is_table) in enumerate(
            zip(texts, vectors, pages, is_tables)
        ):
            point_id = str(uuid.uuid4())
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "doc_id": doc_id,
                        "chunk_index": i,
                        "page": page,
                        "text": text,
                        "is_table": is_table,
                    },
                )
            )
        
        # Upsert in batches
        batch_size = 100
        total_upserted = 0
        
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=batch,
                wait=True,  # Wait for persistence
            )
            total_upserted += len(batch)
        
        logger.info(f"Upserted {total_upserted} vectors for doc_id={doc_id}")
        return total_upserted
    
    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        doc_id: Optional[str] = None,
        score_threshold: float = 0.0,
    ) -> List[SearchResult]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query embedding vector (1024-dim)
            top_k: Number of results to return
            doc_id: Optional filter by document ID
            score_threshold: Minimum similarity score
            
        Returns:
            List of SearchResult objects
        """
        if len(query_vector) != self.VECTOR_SIZE:
            raise ValueError(
                f"Query vector has {len(query_vector)} dimensions, "
                f"expected {self.VECTOR_SIZE}"
            )
        
        # Build filter
        query_filter = None
        if doc_id:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=doc_id),
                    )
                ]
            )
        
        # Search using query_points (qdrant-client >= 1.7)
        results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True,
        )
        
        # Convert to SearchResult
        search_results = []
        for hit in results.points:
            payload = hit.payload or {}
            search_results.append(
                SearchResult(
                    id=str(hit.id),
                    score=hit.score,
                    doc_id=payload.get("doc_id", ""),
                    chunk_index=payload.get("chunk_index", 0),
                    page=payload.get("page", 1),
                    text=payload.get("text", ""),
                    is_table=payload.get("is_table", False),
                )
            )
        
        return search_results
    
    def delete_document(self, doc_id: str) -> int:
        """
        Delete all vectors for a document.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            Number of points deleted
        """
        # Get count before delete
        count_before = self.get_document_count(doc_id)
        
        # Delete by filter
        self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="doc_id",
                            match=MatchValue(value=doc_id),
                        )
                    ]
                )
            ),
            wait=True,
        )
        
        logger.info(f"Deleted {count_before} vectors for doc_id={doc_id}")
        return count_before
    
    def get_document_count(self, doc_id: str) -> int:
        """Get number of vectors for a document."""
        result = self.client.count(
            collection_name=self.COLLECTION_NAME,
            count_filter=Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=doc_id),
                    )
                ]
            ),
        )
        return result.count
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            info = self.client.get_collection(self.COLLECTION_NAME)
            return {
                "name": self.COLLECTION_NAME,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value,
                "vector_size": self.VECTOR_SIZE,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Check if Qdrant is healthy."""
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False


# Convenience function for creating store
def create_qdrant_store(
    host: str = "localhost",
    port: int = 6333,
) -> QdrantVectorStore:
    """Create and initialize Qdrant vector store."""
    store = QdrantVectorStore(host=host, port=port)
    store.ensure_collection()
    return store
