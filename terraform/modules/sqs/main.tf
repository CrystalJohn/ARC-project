# SQS Module - Document Processing Queue

# Dead Letter Queue (DLQ)
resource "aws_sqs_queue" "document_processing_dlq" {
  name                      = "${var.project_name}-${var.environment}-document-processing-dlq"
  message_retention_seconds = var.message_retention_seconds
  
  # Enable server-side encryption
  sqs_managed_sse_enabled = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-document-processing-dlq"
    Environment = var.environment
    Purpose     = "Dead letter queue for failed document processing"
  }
}

# Main Document Processing Queue
resource "aws_sqs_queue" "document_processing" {
  name                       = "${var.project_name}-${var.environment}-document-processing"
  visibility_timeout_seconds = var.visibility_timeout
  message_retention_seconds  = var.message_retention_seconds
  delay_seconds              = 0
  max_message_size           = 262144  # 256 KB
  receive_wait_time_seconds  = 20      # Long polling

  # Enable server-side encryption
  sqs_managed_sse_enabled = true

  # Redrive policy - send to DLQ after max_receive_count failures
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.document_processing_dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-document-processing"
    Environment = var.environment
    Purpose     = "Queue for document processing pipeline"
  }
}

# Queue Policy - Allow S3 to send notifications
resource "aws_sqs_queue_policy" "document_processing_policy" {
  queue_url = aws_sqs_queue.document_processing.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowS3Notifications"
        Effect    = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.document_processing.arn
        Condition = {
          ArnLike = {
            "aws:SourceArn" = var.s3_bucket_arn
          }
        }
      }
    ]
  })
}
