# Contributing Guide

## Git Workflow

### Initial Setup

```bash
# Clone the repository
git clone https://gitlab.com/academy-research-chatbot-arc/ARC-project.git
cd ARC-project

# Configure Git
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Feature branches
- `fix/*` - Bug fix branches

### Working on a Feature

```bash
# Create a new branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Make changes
# ... edit files ...

# Stage and commit
git add .
git commit -m "feat: add your feature description"

# Push to GitLab
git push origin feature/your-feature-name

# Create Merge Request on GitLab
```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```bash
git commit -m "feat(terraform): add VPC module"
git commit -m "fix(backend): resolve S3 upload issue"
git commit -m "docs: update README with setup instructions"
```

### Code Review Process

1. Create Merge Request on GitLab
2. Assign reviewers (at least 1 team member)
3. Address review comments
4. Get approval
5. Merge to develop

### Terraform Changes

```bash
# Before committing Terraform changes
cd terraform
terraform fmt -recursive
terraform validate

# Commit
git add terraform/
git commit -m "feat(terraform): add EC2 module"
```

### Python Code Changes

```bash
# Format code
black backend/
flake8 backend/

# Run tests
pytest backend/tests/

# Commit
git add backend/
git commit -m "feat(backend): add document upload endpoint"
```

### React Code Changes

```bash
# Format code
cd frontend
npm run lint
npm run format

# Run tests
npm test

# Commit
git add frontend/
git commit -m "feat(frontend): add chat interface"
```

## Pull Request Template

When creating a Merge Request, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation update
- [ ] Infrastructure change

## Testing
- [ ] Tested locally
- [ ] Unit tests added/updated
- [ ] Integration tests pass

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No sensitive data committed

## Related Issues
Closes #issue_number
```

## Best Practices

### Do's ✅
- Write clear commit messages
- Keep commits atomic (one logical change per commit)
- Pull latest changes before starting work
- Test your changes before committing
- Update documentation when needed
- Use `.gitignore` to exclude sensitive files

### Don'ts ❌
- Don't commit sensitive data (API keys, passwords)
- Don't commit large binary files
- Don't commit `node_modules/` or `.terraform/`
- Don't force push to `main` or `develop`
- Don't commit directly to `main`

## Sensitive Data

**Never commit:**
- AWS access keys
- Terraform state files (`*.tfstate`)
- Environment variables (`.env`)
- SSH keys (`*.pem`, `*.key`)
- Passwords or secrets

**Use instead:**
- AWS Secrets Manager
- Environment variables
- Terraform variables
- GitLab CI/CD variables

## Getting Help

- Ask in team chat
- Review existing code
- Check documentation
- Contact team lead

---

Happy coding! 🚀
