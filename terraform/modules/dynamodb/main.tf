# DynamoDB Module - Document Metadata and Chat History

# DocumentMetadata Table
resource "aws_dynamodb_table" "document_metadata" {
  name           = "${var.project_name}-${var.environment}-document-metadata"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "doc_id"
  range_key      = "sk"

  attribute {
    name = "doc_id"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "uploaded_at"
    type = "S"
  }

  # GSI for querying by status
  global_secondary_index {
    name            = "status-index"
    hash_key        = "status"
    range_key       = "uploaded_at"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-document-metadata"
  }
}

# ChatHistory Table
resource "aws_dynamodb_table" "chat_history" {
  name           = "${var.project_name}-${var.environment}-chat-history"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"
  range_key      = "sk"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  attribute {
    name = "conversation_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  # GSI for querying by conversation
  global_secondary_index {
    name            = "conversation-index"
    hash_key        = "conversation_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-chat-history"
  }
}
