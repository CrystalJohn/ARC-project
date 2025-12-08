"""
Debug script to check Qdrant data and embedding quality.
"""
import os
import sys
os.environ.setdefault("AWS_REGION", "ap-southeast-1")

from app.services.qdrant_client import QdrantVectorStore
from app.services.embedding_service import CohereEmbeddingService

def main():
    print("=" * 60)
    print("Qdrant Debug - Check Data Quality")
    print("=" * 60)
    
    # Connect to Qdrant
    qdrant = QdrantVectorStore(host="localhost", port=6333)
    
    # Get collection info
    info = qdrant.get_collection_info()
    print(f"\nCollection info: {info}")
    
    # Get sample points
    print("\n" + "=" * 60)
    print("Sample Points (first 5)")
    print("=" * 60)
    
    points = qdrant.get_all_points(limit=5)
    
    for i, point in enumerate(points):
        payload = point.get("payload", {})
        text = payload.get("text", "")[:200]
        doc_id = payload.get("doc_id", "")
        page = payload.get("page", 1)
        
        print(f"\n[{i+1}] doc_id: {doc_id}, page: {page}")
        print(f"    Text preview: {text}...")
        
        # Check for encoding issues
        has_encoding_issue = False
        for char in text:
            if ord(char) > 127 and char not in 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ':
                # Check if it's a valid Vietnamese character or common punctuation
                if char not in '–—''""…•·×÷±≤≥≠≈∞∑∏√∫∂∆∇∈∉∋∌∩∪⊂⊃⊄⊅⊆⊇⊈⊉⊊⊋':
                    has_encoding_issue = True
                    print(f"    ⚠️ Possible encoding issue: char '{char}' (ord={ord(char)})")
                    break
        
        if not has_encoding_issue:
            print(f"    ✅ Text encoding looks OK")
    
    # Test embedding similarity
    print("\n" + "=" * 60)
    print("Test Embedding Similarity")
    print("=" * 60)
    
    embedding_service = CohereEmbeddingService(region="ap-southeast-1")
    
    # Test query
    test_queries = [
        "giải thuật là gì",
        "độ khó giải thuật",
        "algorithm complexity"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        
        # Generate query embedding
        query_embedding = embedding_service.embed_text(query, input_type="search_query")
        
        if query_embedding:
            # Search
            results = qdrant.search(
                query_vector=query_embedding,
                top_k=3,
                score_threshold=0.0  # Get all results
            )
            
            print(f"  Found {len(results)} results:")
            for r in results:
                print(f"    - Score: {r.score:.4f} ({r.score*100:.2f}%), doc: {r.doc_id}, page: {r.page}")
                print(f"      Text: {r.text[:100]}...")
        else:
            print("  ❌ Failed to generate embedding")
    
    print("\n" + "=" * 60)
    print("Diagnosis")
    print("=" * 60)
    
    if points:
        # Check if scores are very low
        print("\nIf scores are < 10%, the documents may have been embedded with a different model.")
        print("Solution: Re-process all documents with the current embedding model.")
        print("\nRun: python reprocess_documents.py")
        print("Then: python run_worker.py")

if __name__ == "__main__":
    main()
