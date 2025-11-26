#!/bin/bash
# Git Setup Script for ARC Project

echo "🚀 Setting up Git for ARC Project..."

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing Git repository..."
    git init
    
    echo "🔗 Adding GitLab remote..."
    git remote add origin https://gitlab.com/academy-research-chatbot-arc/ARC-project.git
else
    echo "✅ Git already initialized"
fi

# Configure Git (optional - comment out if already configured globally)
echo "⚙️  Configuring Git..."
read -p "Enter your name: " git_name
read -p "Enter your email: " git_email
git config user.name "$git_name"
git config user.email "$git_email"

# Check current branch
current_branch=$(git branch --show-current)
if [ -z "$current_branch" ]; then
    echo "🌿 Creating main branch..."
    git checkout -b main
fi

# Stage all files
echo "📝 Staging files..."
git add .

# Show status
echo "📊 Git status:"
git status

# Commit
echo "💾 Creating initial commit..."
git commit -m "feat: initial project setup with Terraform infrastructure

- Add Terraform modules for VPC, IAM, EC2, S3, DynamoDB, Cognito, Amplify
- Add project documentation and specs
- Add .gitignore for Terraform and Python
- Add CONTRIBUTING.md with Git workflow guidelines"

# Push to GitLab
echo "🚀 Pushing to GitLab..."
git push -u origin main

echo "✅ Done! Your code is now on GitLab."
echo "🌐 Visit: https://gitlab.com/academy-research-chatbot-arc/ARC-project"
