# S3 Module Outputs

output "documents_bucket_name" {
  description = "Name of the documents S3 bucket"
  value       = aws_s3_bucket.documents.id
}

output "documents_bucket_arn" {
  description = "ARN of the documents S3 bucket"
  value       = aws_s3_bucket.documents.arn
}

output "documents_bucket_domain_name" {
  description = "Domain name of the documents S3 bucket"
  value       = aws_s3_bucket.documents.bucket_domain_name
}
