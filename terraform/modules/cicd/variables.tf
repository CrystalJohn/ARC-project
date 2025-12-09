# CI/CD Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS Region"
  type        = string
}

variable "gitlab_repository" {
  description = "GitLab repository (org/repo format)"
  type        = string
  default     = "academy-research-chatbot-arc/ARC-project"
}

variable "gitlab_branch" {
  description = "GitLab branch to track"
  type        = string
  default     = "tech-lead"
}

variable "frontend_bucket_name" {
  description = "S3 bucket name for frontend hosting"
  type        = string
}

variable "frontend_bucket_arn" {
  description = "S3 bucket ARN for frontend hosting"
  type        = string
}

variable "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for cache invalidation"
  type        = string
  default     = ""
}

variable "api_url" {
  description = "Backend API URL"
  type        = string
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  type        = string
}

variable "cognito_client_id" {
  description = "Cognito App Client ID"
  type        = string
}
