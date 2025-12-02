# Main Terraform configuration for ARC Chatbot Infrastructure
# This file orchestrates all modules to provision AWS resources

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  az           = var.availability_zone
}

# IAM Module
module "iam" {
  source = "./modules/iam"
  
  project_name = var.project_name
  environment  = var.environment
}

# S3 Module
module "s3" {
  source = "./modules/s3"
  
  project_name    = var.project_name
  environment     = var.environment
  ec2_role_arn    = module.iam.ec2_role_arn
}

# DynamoDB Module
module "dynamodb" {
  source = "./modules/dynamodb"
  
  project_name = var.project_name
  environment  = var.environment
}

# EC2 Module
module "ec2" {
  source = "./modules/ec2"
  
  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = [module.vpc.public_subnet_id, module.vpc.public_subnet_2_id]
  private_subnet_id     = module.vpc.private_subnet_id
  instance_profile_name = module.iam.ec2_instance_profile_name
}

# Cognito Module
module "cognito" {
  source = "./modules/cognito"
  
  project_name = var.project_name
  environment  = var.environment
}

# SQS Module - Document Processing Queue
module "sqs" {
  source = "./modules/sqs"
  
  project_name  = var.project_name
  environment   = var.environment
  s3_bucket_arn = module.s3.documents_bucket_arn
}

# Amplify Module
# TODO: Uncomment after setting up Git repository
# module "amplify" {
#   source = "./modules/amplify"
#   
#   project_name       = var.project_name
#   environment        = var.environment
#   repository_url     = "https://gitlab.com/academy-research-chatbot-arc/ARC-project.git"
#   cognito_pool_id    = module.cognito.user_pool_id
#   cognito_client_id  = module.cognito.app_client_id
#   api_url            = module.ec2.alb_dns_name
# }
