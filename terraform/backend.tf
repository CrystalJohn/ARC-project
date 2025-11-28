# Terraform Backend Configuration
# Stores state in S3 with DynamoDB locking

terraform {
  backend "s3" {
    bucket         = "arc-chatbot-terraform-state" // Tên S3 bucket
    key            = "infrastructure/terraform.tfstate" // Path trong table
    region         = "ap-southeast-1" 
    dynamodb_table = "terraform-locks" //table name cho locking
    encrypt        = true
  }
}
