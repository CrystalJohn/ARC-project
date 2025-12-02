# SQS Module Outputs

output "queue_url" {
  description = "URL of the document processing queue"
  value       = aws_sqs_queue.document_processing.url
}

output "queue_arn" {
  description = "ARN of the document processing queue"
  value       = aws_sqs_queue.document_processing.arn
}

output "queue_name" {
  description = "Name of the document processing queue"
  value       = aws_sqs_queue.document_processing.name
}

output "dlq_url" {
  description = "URL of the dead letter queue"
  value       = aws_sqs_queue.document_processing_dlq.url
}

output "dlq_arn" {
  description = "ARN of the dead letter queue"
  value       = aws_sqs_queue.document_processing_dlq.arn
}

output "dlq_name" {
  description = "Name of the dead letter queue"
  value       = aws_sqs_queue.document_processing_dlq.name
}
