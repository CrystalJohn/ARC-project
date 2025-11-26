# Amplify Module Outputs

output "app_id" {
  description = "ID of the Amplify app"
  value       = aws_amplify_app.main.id
}

output "app_arn" {
  description = "ARN of the Amplify app"
  value       = aws_amplify_app.main.arn
}

output "default_domain" {
  description = "Default domain of the Amplify app"
  value       = aws_amplify_app.main.default_domain
}

output "branch_name" {
  description = "Name of the Amplify branch"
  value       = aws_amplify_branch.main.branch_name
}
