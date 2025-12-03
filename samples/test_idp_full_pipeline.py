"""
Full IDP Pipeline Test with Qdrant Storage

Test flow: Upload PDF → Extract → Chunk → Embed → Store in Qdrant → Search
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.pdf_extractor import extract_pdf_auto
from app.services.text_chunker import chunk_text
from app.services.embedding_service import CohereEmbeddingService
from app.services.qdrant_client import QdrantVectorStore


def test_full_pipeline(pdf_path: str, qdrant_host: str = "localhost"):
    """Test complete IDP pipeline with Qdrant storage."""
    print("=" * 60)
    print("Full IDP Pipeline Test (with Qdrant)")
    print("=" * 60)
    
    doc_id = os.path.basename(pdf_path).replace('.pdf', '')
    
    # 1. Read PDF
    print(f"\n[1/6] Reading PDF: {pdf_path}")
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    print(f"      Doc ID: {doc_id}")
    
    # 2. Extract text
    print("\n[2/6] Extracting text...")
    content = extract_pdf_auto(pdf_bytes, use_textract_for_scanned=False)
    print(f"      Pages: {content.total_pages}, Chars: {content.total_chars:,}")
    
    if not content.full_text:
        print("      ERROR: No text extracted!")
        return False
    
    # 3. Chunk text
    print("\n[3/6] Chunking text...")
    chunks = chunk_text(content.full_text)
    print(f"      Chunks: {len(chunks)}")
    
    # Limit to first 10 chunks for testing
    test_chunks = chunks[:10]
    print(f"      Testing with: {len(test_chunks)} chunks")
    
    # 4. Generate embeddings
    print("\n[4/6] Generating embeddings...")
    service = CohereEmbeddingService(region='ap-southeast-1')
    texts = [c.text for c in test_chunks]
    embeddings = service.embed_texts(texts)
    
    valid_embeddings = [e for e in embeddings if e is not None]
    print(f"      Embeddings: {len(valid_embeddings)}/{len(test_chunks)}")
    
    if not valid_embeddings:
        print("      ERROR: No embeddings generated!")
        return False
    
    # 5. Store in Qdrant
    print(f"\n[5/6] Storing in Qdrant ({qdrant_host})...")
    try:
        store = QdrantVectorStore(host=qdrant_host, port=6333)
        store.ensure_collection()
        
        # Delete existing vectors for this doc
        store.delete_document(doc_id)
        
        # Upsert new vectors
        pages = [i + 1 for i in range(len(test_chunks))]  # Simple page numbering
        count = store.upsert_vectors(
            doc_id=doc_id,
            texts=texts,
            vectors=valid_embeddings,
            pages=pages
        )
        print(f"      Stored: {count} vectors")
        
        # Get collection info
        info = store.get_collection_info()
        print(f"      Collection: {info.get('name')}, Total vectors: {info.get('vectors_count')}")
        
    except Exception as e:
        print(f"      ERROR connecting to Qdrant: {e}")
        print("      Make sure Qdrant is running: docker-compose up -d qdrant")
        return False
    
    # 6. Test search
    print("\n[6/6] Testing search...")
    query = "data structures and algorithms"
    query_embedding = service.embed_text(query, input_type="search_query")
    
    if query_embedding:
        results = store.search(query_embedding, top_k=3, doc_id=doc_id)
        print(f"      Query: '{query}'")
        print(f"      Results: {len(results)}")
        for i, r in enumerate(results):
            print(f"      [{i+1}] Score: {r.score:.4f}, Page: {r.page}")
            print(f"          Text: {r.text[:100]}...")
    else:
        print("      ERROR: Could not generate query embedding")
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("FULL PIPELINE SUCCESS!")
    print("=" * 60)
    print(f"  Document:    {doc_id}")
    print(f"  Pages:       {content.total_pages}")
    print(f"  Chunks:      {len(chunks)} (tested {len(test_chunks)})")
    print(f"  Vectors:     {count} stored in Qdrant")
    print(f"  Search:      {len(results)} results found")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    pdf_path = 'data-structures-sample.pdf'
    qdrant_host = 'localhost'
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    if len(sys.argv) > 2:
        qdrant_host = sys.argv[2]
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found: {pdf_path}")
        sys.exit(1)
    
    success = test_full_pipeline(pdf_path, qdrant_host)
    sys.exit(0 if success else 1)
