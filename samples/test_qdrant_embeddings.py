"""
Test Qdrant + Embeddings Integration

Task #19 & #20: Test vector database and embeddings together
Run this on EC2 after starting Qdrant with docker-compose.
"""

import sys
sys.path.insert(0, '../backend')

from app.services.qdrant_client import QdrantVectorStore, create_qdrant_store
from app.services.embeddings_service import EmbeddingsService


def test_qdrant_connection():
    """Test Qdrant connection and collection setup."""
    print("=" * 50)
    print("Testing Qdrant Connection...")
    
    store = QdrantVectorStore(host="localhost", port=6333)
    
    # Health check
    if store.health_check():
        print("✅ Qdrant is healthy")
    else:
        print("❌ Qdrant is not responding")
        return False
    
    # Ensure collection exists
    if store.ensure_collection():
        print("✅ Collection 'documents' ready")
    else:
        print("❌ Failed to create collection")
        return False
    
    # Get collection info
    info = store.get_collection_info()
    print(f"   Collection info: {info}")
    
    return True


def test_embeddings_service():
    """Test embeddings generation."""
    print("=" * 50)
    print("Testing Embeddings Service...")
    
    service = EmbeddingsService(region="ap-southeast-1")
    
    # Test single embedding
    text = "This is a test document about machine learning."
    embedding = service.embed_text(text)
    
    print(f"✅ Generated embedding with {len(embedding)} dimensions")
    print(f"   First 5 values: {embedding[:5]}")
    
    # Test batch embedding
    texts = [
        "Document about artificial intelligence",
        "Research paper on neural networks",
        "Study of deep learning algorithms",
    ]
    embeddings = service.embed_texts(texts)
    
    print(f"✅ Generated {len(embeddings)} embeddings in batch")
    
    return embeddings


def test_vector_storage_and_search(embeddings):
    """Test storing and searching vectors."""
    print("=" * 50)
    print("Testing Vector Storage & Search...")
    
    store = create_qdrant_store(host="localhost", port=6333)
    service = EmbeddingsService(region="ap-southeast-1")
    
    # Sample documents
    doc_id = "test-doc-001"
    texts = [
        "Machine learning is a subset of artificial intelligence.",
        "Neural networks are inspired by biological neurons.",
        "Deep learning uses multiple layers of neural networks.",
    ]
    
    # Generate embeddings
    vectors = service.embed_texts(texts)
    print(f"✅ Generated {len(vectors)} embeddings")
    
    # Store vectors
    count = store.upsert_vectors(
        doc_id=doc_id,
        texts=texts,
        vectors=vectors,
        pages=[1, 1, 2],
    )
    print(f"✅ Stored {count} vectors for doc_id={doc_id}")
    
    # Search
    query = "What is deep learning?"
    query_vector = service.embed_query(query)
    
    results = store.search(query_vector, top_k=3)
    print(f"\n🔍 Search results for: '{query}'")
    for i, result in enumerate(results):
        print(f"   {i+1}. Score: {result.score:.4f}")
        print(f"      Text: {result.text[:50]}...")
        print(f"      Page: {result.page}, Chunk: {result.chunk_index}")
    
    # Cleanup
    deleted = store.delete_document(doc_id)
    print(f"\n🗑️ Cleaned up {deleted} vectors")
    
    return True


def main():
    print("\n🚀 Qdrant + Embeddings Integration Test\n")
    
    # Test 1: Qdrant connection
    if not test_qdrant_connection():
        print("\n❌ Qdrant test failed. Make sure Qdrant is running:")
        print("   cd backend && docker-compose up -d")
        return
    
    # Test 2: Embeddings service
    try:
        embeddings = test_embeddings_service()
    except Exception as e:
        print(f"❌ Embeddings test failed: {e}")
        return
    
    # Test 3: Vector storage and search
    try:
        test_vector_storage_and_search(embeddings)
    except Exception as e:
        print(f"❌ Vector storage test failed: {e}")
        return
    
    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
