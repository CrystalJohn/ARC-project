# CI/CD Module Outputs

output "pipeline_name" {
  description = "CodePipeline name"
  value       = aws_codepipeline.main.name
}

output "pipeline_arn" {
  description = "CodePipeline ARN"
  value       = aws_codepipeline.main.arn
}

output "artifacts_bucket" {
  description = "S3 bucket for pipeline artifacts"
  value       = aws_s3_bucket.artifacts.bucket
}

output "gitlab_connection_arn" {
  description = "CodeStar GitLab connection ARN"
  value       = aws_codestarconnections_connection.gitlab.arn
}

output "gitlab_connection_status" {
  description = "GitLab connection status (needs manual approval in console)"
  value       = aws_codestarconnections_connection.gitlab.connection_status
}

output "codebuild_frontend_name" {
  description = "Frontend CodeBuild project name"
  value       = aws_codebuild_project.frontend.name
}

output "codebuild_backend_name" {
  description = "Backend CodeBuild project name"
  value       = aws_codebuild_project.backend.name
}
