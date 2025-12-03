"""
End-to-End IDP Pipeline Test

Test flow: Upload PDF → Extract → Chunk → Embed → Qdrant
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.pdf_extractor import extract_pdf_auto
from app.services.text_chunker import chunk_text
from app.services.embedding_service import CohereEmbeddingService


def test_pipeline(pdf_path: str):
    """Test complete IDP pipeline with a PDF file."""
    print("=" * 60)
    print("IDP Pipeline End-to-End Test")
    print("=" * 60)
    
    # 1. Read PDF
    print(f"\n[1/4] Reading PDF: {pdf_path}")
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    print(f"      File size: {len(pdf_bytes):,} bytes")
    
    # 2. Extract text
    print("\n[2/4] Extracting text...")
    content = extract_pdf_auto(pdf_bytes, use_textract_for_scanned=False)
    print(f"      Method: {content.extraction_method}")
    print(f"      Pages: {content.total_pages}")
    print(f"      Total chars: {content.total_chars:,}")
    print(f"      Errors: {content.errors if content.errors else 'None'}")
    
    if not content.full_text:
        print("      ERROR: No text extracted!")
        return False
    
    print(f"      Preview: {content.full_text[:200]}...")
    
    # 3. Chunk text
    print("\n[3/4] Chunking text...")
    chunks = chunk_text(content.full_text)
    print(f"      Chunks created: {len(chunks)}")
    if chunks:
        print(f"      First chunk: {len(chunks[0].text)} chars")
        print(f"      Preview: {chunks[0].text[:100]}...")
    
    # 4. Generate embeddings
    print("\n[4/4] Generating embeddings...")
    service = CohereEmbeddingService(region='ap-southeast-1')
    
    # Test with first 3 chunks only (to save API calls)
    test_chunks = chunks[:3] if len(chunks) > 3 else chunks
    texts = [c.text for c in test_chunks]
    
    embeddings = service.embed_texts(texts)
    
    success_count = sum(1 for e in embeddings if e is not None)
    print(f"      Embeddings generated: {success_count}/{len(test_chunks)}")
    
    if embeddings and embeddings[0]:
        print(f"      Vector dimensions: {len(embeddings[0])}")
        print(f"      First 5 values: {embeddings[0][:5]}")
    
    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"  PDF Pages:        {content.total_pages}")
    print(f"  Total Characters: {content.total_chars:,}")
    print(f"  Chunks Created:   {len(chunks)}")
    print(f"  Embeddings OK:    {success_count}/{len(test_chunks)}")
    print(f"  Vector Dims:      {len(embeddings[0]) if embeddings and embeddings[0] else 0}")
    print("=" * 60)
    
    return success_count == len(test_chunks)


if __name__ == '__main__':
    # Use test PDF
    pdf_path = 'test-sample.pdf'
    
    if not os.path.exists(pdf_path):
        pdf_path = 'data-structures-sample.pdf'
    
    if not os.path.exists(pdf_path):
        print("ERROR: No test PDF found!")
        print("Please provide a PDF file: python test_idp_pipeline.py <path_to_pdf>")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    
    success = test_pipeline(pdf_path)
    sys.exit(0 if success else 1)
