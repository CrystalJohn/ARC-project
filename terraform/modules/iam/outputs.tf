# IAM Module Outputs

output "ec2_role_arn" {
  description = "ARN of the EC2 IAM role"
  value       = aws_iam_role.ec2_role.arn
}

output "ec2_role_name" {
  description = "Name of the EC2 IAM role"
  value       = aws_iam_role.ec2_role.name
}

output "ec2_instance_profile_name" {
  description = "Name of the EC2 instance profile"
  value       = aws_iam_instance_profile.ec2_profile.name
}

output "ec2_instance_profile_arn" {
  description = "ARN of the EC2 instance profile"
  value       = aws_iam_instance_profile.ec2_profile.arn
}

# User Access Keys (sensitive)
output "tech_lead_access_key_id" {
  description = "Access key ID for tech lead user"
  value       = aws_iam_access_key.tech_lead_key.id
  sensitive   = true
}

output "tech_lead_secret_access_key" {
  description = "Secret access key for tech lead user"
  value       = aws_iam_access_key.tech_lead_key.secret
  sensitive   = true
}

output "backend_idp_access_key_id" {
  description = "Access key ID for backend+IDP user"
  value       = aws_iam_access_key.backend_idp_key.id
  sensitive   = true
}

output "backend_idp_secret_access_key" {
  description = "Secret access key for backend+IDP user"
  value       = aws_iam_access_key.backend_idp_key.secret
  sensitive   = true
}

output "frontend_access_key_id" {
  description = "Access key ID for frontend user"
  value       = aws_iam_access_key.frontend_key.id
  sensitive   = true
}

output "frontend_secret_access_key" {
  description = "Secret access key for frontend user"
  value       = aws_iam_access_key.frontend_key.secret
  sensitive   = true
}

output "devops_access_key_id" {
  description = "Access key ID for devops user"
  value       = aws_iam_access_key.devops_key.id
  sensitive   = true
}

output "devops_secret_access_key" {
  description = "Secret access key for devops user"
  value       = aws_iam_access_key.devops_key.secret
  sensitive   = true
}

# Console Login Passwords (sensitive)
output "tech_lead_password" {
  description = "Initial console password for tech lead user"
  value       = aws_iam_user_login_profile.tech_lead_login.password
  sensitive   = true
}

output "backend_idp_password" {
  description = "Initial console password for backend+IDP user"
  value       = aws_iam_user_login_profile.backend_idp_login.password
  sensitive   = true
}

output "frontend_password" {
  description = "Initial console password for frontend user"
  value       = aws_iam_user_login_profile.frontend_login.password
  sensitive   = true
}

output "devops_password" {
  description = "Initial console password for devops user"
  value       = aws_iam_user_login_profile.devops_login.password
  sensitive   = true
}
