# S3 Module Variables

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "ec2_role_arn" {
  description = "ARN of the EC2 IAM role for bucket policy"
  type        = string
}
