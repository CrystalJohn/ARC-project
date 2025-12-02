"""
Run SQS Worker for IDP Pipeline

Usage: python run_worker.py
"""
import os
import sys

# Set default region
os.environ.setdefault("AWS_REGION", "ap-southeast-1")

from app.services.sqs_worker import SQSWorker

# Configuration
QUEUE_URL = os.getenv(
    "SQS_QUEUE_URL",
    "https://sqs.ap-southeast-1.amazonaws.com/427995028618/arc-chatbot-dev-document-processing"
)
BUCKET = os.getenv("S3_BUCKET", "arc-chatbot-documents-427995028618")
REGION = os.getenv("AWS_REGION", "ap-southeast-1")


def main():
    print(f"Starting SQS Worker...")
    print(f"Queue URL: {QUEUE_URL}")
    print(f"Bucket: {BUCKET}")
    print(f"Region: {REGION}")
    print("-" * 50)
    
    worker = SQSWorker(
        queue_url=QUEUE_URL,
        documents_bucket=BUCKET,
        region=REGION
    )
    
    # Process messages (max 10 iterations for testing, None for infinite)
    max_iter = int(sys.argv[1]) if len(sys.argv) > 1 else None
    worker.start(max_iterations=max_iter)


if __name__ == "__main__":
    main()
