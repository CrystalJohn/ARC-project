# S3 Module - Document Storage

data "aws_caller_identity" "current" {}

# S3 Bucket for Documents
resource "aws_s3_bucket" "documents" {
  bucket = "${var.project_name}-documents-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.project_name}-${var.environment}-documents"
  }
}

# Enable Versioning
resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable Server-Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block Public Access
resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle Rules
resource "aws_s3_bucket_lifecycle_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    filter {}  # Apply to all objects

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
  }

  rule {
    id     = "delete-incomplete-multipart"
    status = "Enabled"

    filter {}  # Apply to all objects

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# Bucket Policy
resource "aws_s3_bucket_policy" "documents" {
  bucket = aws_s3_bucket.documents.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowEC2RoleAccess"
        Effect = "Allow"
        Principal = {
          AWS = var.ec2_role_arn
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.documents.arn,
          "${aws_s3_bucket.documents.arn}/*"
        ]
      }
    ]
  })
}
