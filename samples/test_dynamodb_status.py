"""
Test script to verify DynamoDB document status tracking.

Usage:
    python samples/test_dynamodb_status.py

This will:
1. Create a test document with UPLOADED status
2. Update status to IDP_RUNNING
3. Update status to EMBEDDING_DONE with counts
4. List all documents
5. Clean up test document
"""

import sys
import uuid
sys.path.insert(0, '.')

from backend.app.services.document_status_manager import (
    DocumentStatusManager,
    DocumentStatus
)


def main():
    # Initialize manager - uses default table name from env or arc-chatbot-dev-document-metadata
    print("Initializing DocumentStatusManager...")
    manager = DocumentStatusManager(
        table_name="arc-chatbot-dev-document-metadata",
        region_name="ap-southeast-1"
    )
    print(f"Table: {manager.table_name}")
    print(f"Region: {manager.region_name}")
    print()
    
    # Generate test doc_id
    doc_id = f"test-{uuid.uuid4().hex[:8]}"
    print(f"Test document ID: {doc_id}")
    print("-" * 50)
    
    try:
        # 1. Create document
        print("\n1. Creating document with UPLOADED status...")
        result = manager.create_document(
            doc_id=doc_id,
            filename="test-paper.pdf",
            uploaded_by="test-user"
        )
        print(f"   Created: {result}")
        
        # 2. Update to IDP_RUNNING
        print("\n2. Updating status to IDP_RUNNING...")
        result = manager.update_status(doc_id, DocumentStatus.IDP_RUNNING)
        print(f"   Updated: status={result.get('status')}")
        
        # 3. Update to EMBEDDING_DONE with counts
        print("\n3. Updating status to EMBEDDING_DONE with counts...")
        result = manager.update_status(
            doc_id,
            DocumentStatus.EMBEDDING_DONE,
            page_count=10,
            chunk_count=25
        )
        print(f"   Updated: status={result.get('status')}, pages={result.get('page_count')}, chunks={result.get('chunk_count')}")
        
        # 4. Get document
        print("\n4. Getting document...")
        doc = manager.get_document(doc_id)
        print(f"   Document: {doc}")
        
        # 5. List all documents
        print("\n5. Listing all documents...")
        docs = manager.list_documents(page_size=5)
        print(f"   Found {len(docs['items'])} documents")
        for d in docs['items']:
            print(f"   - {d.get('doc_id')}: {d.get('status')}")
        
        print("\n" + "=" * 50)
        print("SUCCESS! DynamoDB status tracking is working.")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        raise
    
    finally:
        # Cleanup - delete test document
        print(f"\nCleaning up test document {doc_id}...")
        try:
            manager._client.delete_item(
                TableName=manager.table_name,
                Key={
                    "doc_id": {"S": doc_id},
                    "sk": {"S": "METADATA"}
                }
            )
            print("   Deleted.")
        except Exception as e:
            print(f"   Cleanup failed: {e}")


if __name__ == "__main__":
    main()
