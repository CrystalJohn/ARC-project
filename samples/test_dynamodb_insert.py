"""
Insert a test document to DynamoDB (without cleanup).

Usage:
    python samples/test_dynamodb_insert.py

This will create a document that stays in DynamoDB for you to view in Console.
"""

import sys
import uuid
sys.path.insert(0, '.')

from backend.app.services.document_status_manager import (
    DocumentStatusManager,
    DocumentStatus
)


def main():
    print("Initializing DocumentStatusManager...")
    manager = DocumentStatusManager(
        table_name="arc-chatbot-dev-document-metadata",
        region_name="ap-southeast-1"
    )
    
    # Generate test doc_id
    doc_id = f"demo-{uuid.uuid4().hex[:8]}"
    
    # Create document
    print(f"\nCreating document: {doc_id}")
    result = manager.create_document(
        doc_id=doc_id,
        filename="sample-research-paper.pdf",
        uploaded_by="admin-user"
    )
    print(f"Created: {result}")
    
    # Update to EMBEDDING_DONE
    print("\nUpdating to EMBEDDING_DONE...")
    result = manager.update_status(
        doc_id,
        DocumentStatus.EMBEDDING_DONE,
        page_count=15,
        chunk_count=42
    )
    print(f"Updated: {result}")
    
    print("\n" + "=" * 50)
    print("Document created! Check AWS Console to see it.")
    print(f"doc_id: {doc_id}")
    print("=" * 50)


if __name__ == "__main__":
    main()
