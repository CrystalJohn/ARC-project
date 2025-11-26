# Git Setup Script for ARC Project (PowerShell)

Write-Host "🚀 Setting up Git for ARC Project..." -ForegroundColor Green

# Check if git is initialized
if (-not (Test-Path .git)) {
    Write-Host "📦 Initializing Git repository..." -ForegroundColor Yellow
    git init
    
    Write-Host "🔗 Adding GitLab remote..." -ForegroundColor Yellow
    git remote add origin https://gitlab.com/academy-research-chatbot-arc/ARC-project.git
} else {
    Write-Host "✅ Git already initialized" -ForegroundColor Green
}

# Configure Git (optional)
Write-Host "⚙️  Configuring Git..." -ForegroundColor Yellow
$gitName = Read-Host "Enter your name"
$gitEmail = Read-Host "Enter your email"
git config user.name "$gitName"
git config user.email "$gitEmail"

# Check current branch
$currentBranch = git branch --show-current
if ([string]::IsNullOrEmpty($currentBranch)) {
    Write-Host "🌿 Creating main branch..." -ForegroundColor Yellow
    git checkout -b main
}

# Stage all files
Write-Host "📝 Staging files..." -ForegroundColor Yellow
git add .

# Show status
Write-Host "📊 Git status:" -ForegroundColor Cyan
git status

# Commit
Write-Host "💾 Creating initial commit..." -ForegroundColor Yellow
git commit -m "feat: initial project setup with Terraform infrastructure

- Add Terraform modules for VPC, IAM, EC2, S3, DynamoDB, Cognito, Amplify
- Add project documentation and specs
- Add .gitignore for Terraform and Python
- Add CONTRIBUTING.md with Git workflow guidelines"

# Push to GitLab
Write-Host "🚀 Pushing to GitLab..." -ForegroundColor Yellow
git push -u origin main

Write-Host "✅ Done! Your code is now on GitLab." -ForegroundColor Green
Write-Host "🌐 Visit: https://gitlab.com/academy-research-chatbot-arc/ARC-project" -ForegroundColor Cyan
