# EC2 Module Variables

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_id" {
  description = "Public subnet ID for ALB"
  type        = string
}

variable "private_subnet_id" {
  description = "Private subnet ID for EC2"
  type        = string
}

variable "instance_profile_name" {
  description = "IAM instance profile name"
  type        = string
}
