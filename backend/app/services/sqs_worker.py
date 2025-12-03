"""
Task #18: SQS Worker for Document Processing Pipeline

Worker polls SQS queue và xử lý documents:
S3 Event → SQS → Worker → Extract → Chunk → Embeddings → Qdrant
"""

import json
import time
import logging
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum

import boto3
from botocore.exceptions import ClientError

from .pdf_detector import detect_pdf_type, PDFType
from .pdf_extractor import extract_text_from_pdf, extract_pdf_auto, TextractExtractor
from .text_chunker import chunk_text, TextChunk

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProcessingStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"  # For scanned PDFs when Textract not available


@dataclass
class ProcessingResult:
    """Result of document processing."""
    document_id: str
    status: ProcessingStatus
    chunks_count: int
    total_chars: int
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SQSWorker:
    """
    Worker để process documents từ SQS queue.
    
    Flow:
    1. Receive message từ SQS
    2. Parse S3 event notification
    3. Download PDF từ S3
    4. Detect PDF type (digital/scanned)
    5. Extract text
    6. Chunk text
    7. Generate embeddings (callback)
    8. Store vectors (callback)
    9. Update document status
    10. Delete message từ SQS
    """
    
    def __init__(
        self,
        queue_url: str,
        documents_bucket: str,
        region: str = "ap-southeast-1",
        visibility_timeout: int = 300,
        max_messages: int = 1,
        wait_time: int = 20,
        # Callbacks for embeddings and vector storage
        embeddings_callback: Optional[Callable[[str], list]] = None,
        store_vectors_callback: Optional[Callable[[str, list, list, dict], bool]] = None,
        update_status_callback: Optional[Callable[[str, str, dict], bool]] = None,
    ):
        """
        Initialize SQS Worker.
        
        Args:
            queue_url: SQS queue URL
            documents_bucket: S3 bucket name for documents
            region: AWS region
            visibility_timeout: Message visibility timeout
            max_messages: Max messages to receive per poll
            wait_time: Long polling wait time
            embeddings_callback: Function to generate embeddings (text -> vector)
            store_vectors_callback: Function to store vectors (doc_id, chunks, vectors, metadata)
            update_status_callback: Function to update document status (doc_id, status, metadata)
        """
        self.queue_url = queue_url
        self.documents_bucket = documents_bucket
        self.region = region
        self.visibility_timeout = visibility_timeout
        self.max_messages = max_messages
        self.wait_time = wait_time
        
        # AWS clients
        self.sqs = boto3.client('sqs', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        
        # Callbacks
        self.embeddings_callback = embeddings_callback
        self.store_vectors_callback = store_vectors_callback
        self.update_status_callback = update_status_callback
        
        # Worker state
        self.running = False
        self.processed_count = 0
        self.error_count = 0
    
    def start(self, max_iterations: Optional[int] = None):
        """
        Start worker loop.
        
        Args:
            max_iterations: Max iterations (None = infinite)
        """
        self.running = True
        iteration = 0
        
        logger.info(f"Starting SQS Worker for queue: {self.queue_url}")
        
        while self.running:
            if max_iterations and iteration >= max_iterations:
                logger.info(f"Reached max iterations: {max_iterations}")
                break
            
            try:
                messages = self._receive_messages()
                
                if not messages:
                    logger.debug("No messages received, waiting...")
                    continue
                
                for message in messages:
                    self._process_message(message)
                
                iteration += 1
                
            except KeyboardInterrupt:
                logger.info("Received interrupt, stopping worker...")
                self.stop()
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                self.error_count += 1
                time.sleep(5)  # Back off on error
        
        logger.info(f"Worker stopped. Processed: {self.processed_count}, Errors: {self.error_count}")
    
    def stop(self):
        """Stop worker loop."""
        self.running = False
    
    def _receive_messages(self) -> list:
        """Receive messages from SQS queue."""
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=self.max_messages,
                WaitTimeSeconds=self.wait_time,
                VisibilityTimeout=self.visibility_timeout,
                MessageAttributeNames=['All']
            )
            return response.get('Messages', [])
        except ClientError as e:
            logger.error(f"Error receiving messages: {e}")
            return []
    
    def _process_message(self, message: dict):
        """Process a single SQS message."""
        receipt_handle = message['ReceiptHandle']
        
        try:
            # Parse S3 event from message body
            body = json.loads(message['Body'])
            s3_event = self._parse_s3_event(body)
            
            if not s3_event:
                logger.warning("Invalid S3 event, skipping message")
                self._delete_message(receipt_handle)
                return
            
            bucket = s3_event['bucket']
            key = s3_event['key']
            document_id = self._extract_document_id(key)
            
            logger.info(f"Processing document: {document_id} from s3://{bucket}/{key}")
            
            # Update status to PROCESSING
            self._update_status(document_id, ProcessingStatus.PROCESSING)
            
            # Process the document
            result = self._process_document(bucket, key, document_id)
            
            # Update final status
            self._update_status(
                document_id, 
                result.status,
                {
                    "chunks_count": result.chunks_count,
                    "total_chars": result.total_chars,
                    "error_message": result.error_message
                }
            )
            
            # Delete message on success
            if result.status in [ProcessingStatus.COMPLETED, ProcessingStatus.SKIPPED]:
                self._delete_message(receipt_handle)
                self.processed_count += 1
            else:
                # Don't delete on failure - let it retry or go to DLQ
                self.error_count += 1
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.error_count += 1
    
    def _parse_s3_event(self, body: dict) -> Optional[dict]:
        """Parse S3 event notification from SQS message body."""
        try:
            # Handle SNS wrapped messages
            if 'Records' not in body and 'Message' in body:
                body = json.loads(body['Message'])
            
            if 'Records' not in body:
                return None
            
            record = body['Records'][0]
            if 's3' not in record:
                return None
            
            return {
                'bucket': record['s3']['bucket']['name'],
                'key': record['s3']['object']['key'],
                'size': record['s3']['object'].get('size', 0),
                'event_time': record.get('eventTime')
            }
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing S3 event: {e}")
            return None
    
    def _extract_document_id(self, key: str) -> str:
        """Extract document ID from S3 key."""
        # Assume key format: uploads/{document_id}.pdf or {document_id}.pdf
        filename = key.split('/')[-1]
        return filename.rsplit('.', 1)[0]  # Remove extension
    
    def _process_document(
        self, 
        bucket: str, 
        key: str, 
        document_id: str
    ) -> ProcessingResult:
        """
        Process a document: download, extract, chunk, embed, store.
        """
        try:
            # 1. Download PDF from S3
            logger.info(f"Downloading from s3://{bucket}/{key}")
            pdf_bytes = self._download_from_s3(bucket, key)
            
            if not pdf_bytes:
                return ProcessingResult(
                    document_id=document_id,
                    status=ProcessingStatus.FAILED,
                    chunks_count=0,
                    total_chars=0,
                    error_message="Failed to download file from S3"
                )
            
            # 2. Detect PDF type
            pdf_type = detect_pdf_type(pdf_bytes)
            logger.info(f"PDF type detected: {pdf_type}")
            
            if pdf_type == PDFType.UNKNOWN:
                return ProcessingResult(
                    document_id=document_id,
                    status=ProcessingStatus.FAILED,
                    chunks_count=0,
                    total_chars=0,
                    error_message="Unknown PDF type - cannot process"
                )
            
            # 3. Extract text (auto-detect: PyPDF2 for digital, Textract for scanned)
            logger.info("Extracting text from PDF...")
            pdf_content = extract_pdf_auto(
                pdf_bytes, 
                use_textract_for_scanned=True,
                textract_region=self.region
            )
            logger.info(f"Extraction method: {pdf_content.extraction_method}")
            
            if not pdf_content.full_text:
                return ProcessingResult(
                    document_id=document_id,
                    status=ProcessingStatus.FAILED,
                    chunks_count=0,
                    total_chars=0,
                    error_message="No text extracted from PDF"
                )
            
            # 4. Chunk text
            logger.info("Chunking text...")
            chunks = chunk_text(pdf_content.full_text)
            logger.info(f"Created {len(chunks)} chunks")
            
            # 5. Generate embeddings (if callback provided)
            vectors = []
            if self.embeddings_callback and chunks:
                logger.info("Generating embeddings...")
                for chunk in chunks:
                    try:
                        vector = self.embeddings_callback(chunk.text)
                        vectors.append(vector)
                    except Exception as e:
                        logger.error(f"Error generating embedding: {e}")
                        vectors.append(None)
            
            # 6. Store vectors (if callback provided)
            if self.store_vectors_callback and vectors:
                logger.info("Storing vectors...")
                chunk_texts = [c.text for c in chunks]
                metadata = {
                    "document_id": document_id,
                    "bucket": bucket,
                    "key": key,
                    "total_pages": pdf_content.total_pages,
                    "pdf_metadata": pdf_content.metadata
                }
                self.store_vectors_callback(document_id, chunk_texts, vectors, metadata)
            
            return ProcessingResult(
                document_id=document_id,
                status=ProcessingStatus.COMPLETED,
                chunks_count=len(chunks),
                total_chars=pdf_content.total_chars,
                metadata={
                    "total_pages": pdf_content.total_pages,
                    "vectors_generated": len([v for v in vectors if v])
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            return ProcessingResult(
                document_id=document_id,
                status=ProcessingStatus.FAILED,
                chunks_count=0,
                total_chars=0,
                error_message=str(e)
            )
    
    def _download_from_s3(self, bucket: str, key: str) -> Optional[bytes]:
        """Download file from S3."""
        try:
            response = self.s3.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Error downloading from S3: {e}")
            return None
    
    def _delete_message(self, receipt_handle: str):
        """Delete message from SQS queue."""
        try:
            self.sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
        except ClientError as e:
            logger.error(f"Error deleting message: {e}")
    
    def _update_status(
        self, 
        document_id: str, 
        status: ProcessingStatus,
        metadata: Optional[dict] = None
    ):
        """Update document status via callback."""
        if self.update_status_callback:
            try:
                self.update_status_callback(document_id, status.value, metadata or {})
            except Exception as e:
                logger.error(f"Error updating status: {e}")


def process_single_document(
    bucket: str,
    key: str,
    region: str = "ap-southeast-1"
) -> ProcessingResult:
    """
    Process a single document without SQS.
    Useful for testing or manual processing.
    """
    worker = SQSWorker(
        queue_url="",  # Not used
        documents_bucket=bucket,
        region=region
    )
    
    document_id = worker._extract_document_id(key)
    return worker._process_document(bucket, key, document_id)
