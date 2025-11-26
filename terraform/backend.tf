# Terraform Backend Configuration
# Stores state in S3 with DynamoDB locking

terraform {
  backend "s3" {
    bucket         = "arc-chatbot-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "ap-southeast-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
