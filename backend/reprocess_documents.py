"""
Re-process all documents in DynamoDB to regenerate Qdrant vectors.

This script:
1. Deletes old vectors from Qdrant (to ensure clean re-embedding)
2. Resets document status to UPLOADED
3. Sends SQS messages to trigger re-processing

Usage: python reprocess_documents.py
"""
import os
import json
import boto3

os.environ.setdefault("AWS_REGION", "ap-southeast-1")

from app.services.document_status_manager import DocumentStatusManager, DocumentStatus
from app.services.qdrant_client import QdrantVectorStore

# Configuration
SQS_QUEUE_URL = os.getenv(
    "SQS_QUEUE_URL",
    "https://sqs.ap-southeast-1.amazonaws.com/427995028618/arc-chatbot-dev-document-processing"
)
S3_BUCKET = os.getenv("S3_BUCKET", "arc-chatbot-documents-427995028618")
REGION = os.getenv("AWS_REGION", "ap-southeast-1")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

def main():
    print("=" * 60)
    print("Re-process Documents (with Qdrant cleanup)")
    print("=" * 60)
    
    # Connect to Qdrant
    print("\nConnecting to Qdrant...")
    qdrant = QdrantVectorStore(host=QDRANT_HOST, port=QDRANT_PORT)
    qdrant_info = qdrant.get_collection_info()
    print(f"Qdrant collection: {qdrant_info.get('vectors_count', 0)} vectors")
    
    # Get all documents from DynamoDB
    status_manager = DocumentStatusManager(region_name=REGION)
    result = status_manager.list_documents(page_size=1000)
    documents = result["items"]
    
    print(f"Found {len(documents)} documents in DynamoDB")
    
    # Show status breakdown
    status_counts = {}
    for d in documents:
        status = d.get("status", "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
    print(f"Status breakdown: {status_counts}")
    
    # Re-process ALL documents (not just EMBEDDING_DONE)
    docs_to_process = [d for d in documents if d.get("doc_id") and d.get("filename")]
    print(f"Documents to re-process: {len(docs_to_process)}")
    
    if not docs_to_process:
        print("No documents to re-process")
        return
    
    done_docs = docs_to_process
    
    # Send SQS messages to re-process
    sqs = boto3.client("sqs", region_name=REGION)
    
    for doc in done_docs:
        doc_id = doc["doc_id"]
        filename = doc["filename"]
        s3_key = f"uploads/{doc_id}/{filename}"
        
        print(f"\nRe-processing: {filename}")
        print(f"  doc_id: {doc_id}")
        print(f"  s3_key: {s3_key}")
        
        # Step 1: Delete old vectors from Qdrant
        try:
            deleted_count = qdrant.delete_document(doc_id)
            print(f"  Deleted {deleted_count} old vectors from Qdrant")
        except Exception as e:
            print(f"  Warning: Could not delete old vectors: {e}")
        
        # Step 2: Reset status to UPLOADED and REMOVE lock to allow re-processing
        try:
            status_manager._client.update_item(
                TableName=status_manager.table_name,
                Key={
                    "doc_id": {"S": doc_id},
                    "sk": {"S": "METADATA"}
                },
                UpdateExpression="SET #status = :status REMOVE worker_id, lock_time",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": {"S": "UPLOADED"}
                }
            )
            print(f"  Status reset to UPLOADED, lock removed")
        except Exception as e:
            print(f"  Error resetting status: {e}")
            continue
        
        # Step 3: Send SQS message
        message_body = json.dumps({
            "Records": [{
                "s3": {
                    "bucket": {"name": S3_BUCKET},
                    "object": {"key": s3_key}
                }
            }],
            "doc_id": doc_id
        })
        
        try:
            response = sqs.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody=message_body
            )
            print(f"  SQS message sent: {response.get('MessageId', 'N/A')[:8]}...")
        except Exception as e:
            print(f"  Error sending SQS message: {e}")
    
    print("\n" + "=" * 60)
    print("Done! Run the worker to process documents:")
    print("  cd backend && python run_worker.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
