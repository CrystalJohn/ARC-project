# Hướng Dẫn Push Code Lên GitLab

## Phương Án 1: Sử Dụng Script Tự Động (Khuyến Nghị)

### Trên Windows (PowerShell):

```powershell
# Mở PowerShell trong thư mục project
cd D:\AWS\ARC-project

# Chạy script
.\git-setup.ps1
```

### Trên Linux/Mac:

```bash
# Mở terminal trong thư mục project
cd /path/to/ARC-project

# Cho phép thực thi script
chmod +x git-setup.sh

# Chạy script
./git-setup.sh
```

## Phương Án 2: Thực Hiện Thủ Công

### Bước 1: Khởi tạo Git (nếu chưa có)

```bash
cd D:\AWS\ARC-project
git init
```

### Bước 2: Cấu hình Git

```bash
# Cấu hình tên và email
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Kiểm tra cấu hình
git config --list
```

### Bước 3: Thêm Remote GitLab

```bash
git remote add origin https://gitlab.com/academy-research-chatbot-arc/ARC-project.git

# Kiểm tra remote
git remote -v
```

### Bước 4: Tạo Branch Main

```bash
git checkout -b main
```

### Bước 5: Stage Files

```bash
# Thêm tất cả files
git add .

# Hoặc thêm từng thư mục
git add terraform/
git add .kiro/
git add README.md
git add .gitignore

# Kiểm tra status
git status
```

### Bước 6: Commit

```bash
git commit -m "feat: initial project setup with Terraform infrastructure

- Add Terraform modules for VPC, IAM, EC2, S3, DynamoDB, Cognito, Amplify
- Add project documentation and specs
- Add .gitignore for Terraform and Python
- Add CONTRIBUTING.md with Git workflow guidelines"
```

### Bước 7: Push Lên GitLab

```bash
# Push lần đầu
git push -u origin main

# Nếu gặp lỗi authentication, sử dụng Personal Access Token
# Thay <your-token> bằng token của bạn
git remote set-url origin https://oauth2:<your-token>@gitlab.com/academy-research-chatbot-arc/ARC-project.git
git push -u origin main
```

## Tạo GitLab Personal Access Token

1. Đăng nhập GitLab: https://gitlab.com
2. Click avatar → **Settings**
3. Sidebar → **Access Tokens**
4. Tạo token mới:
   - Name: `ARC-Project-Token`
   - Expiration: 90 days
   - Scopes: ✅ `read_repository`, ✅ `write_repository`
5. Click **Create personal access token**
6. Copy token (chỉ hiện 1 lần!)

## Sử Dụng Token Để Push

```bash
# Cách 1: Thêm token vào URL
git remote set-url origin https://oauth2:YOUR_TOKEN_HERE@gitlab.com/academy-research-chatbot-arc/ARC-project.git

# Cách 2: Git sẽ hỏi username/password
# Username: your-gitlab-username
# Password: YOUR_TOKEN_HERE (paste token)
```

## Kiểm Tra Sau Khi Push

1. Mở GitLab: https://gitlab.com/academy-research-chatbot-arc/ARC-project
2. Kiểm tra files đã được push
3. Xem commit history

## Cấu Trúc Files Đã Push

```
ARC-project/
├── .gitignore                    # Ignore Terraform state, secrets
├── README.md                     # Project overview
├── CONTRIBUTING.md               # Git workflow guide
├── GIT_PUSH_GUIDE.md            # This file
├── git-setup.sh                 # Auto setup script (Linux/Mac)
├── git-setup.ps1                # Auto setup script (Windows)
├── knowledge-project.md         # Project knowledge base
├── task-output-project.md       # Task dependencies
├── .kiro/                       # Kiro specs
│   └── specs/
│       ├── m0-infrastructure-setup/
│       │   ├── requirements.md
│       │   ├── design.md
│       │   └── tasks.md
│       └── m1-idp-ingestion/
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
└── terraform/                   # Infrastructure code
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── backend.tf
    ├── terraform.tfvars
    ├── README.md
    └── modules/
        ├── vpc/
        ├── iam/
        ├── ec2/
        ├── s3/
        ├── dynamodb/
        ├── cognito/
        └── amplify/
```

## Files KHÔNG Push (trong .gitignore)

❌ `.terraform/` - Terraform cache
❌ `*.tfstate` - Terraform state (chứa sensitive data)
❌ `*.tfvars` - Variable values (có thể chứa secrets)
❌ `.env` - Environment variables
❌ `*.pem`, `*.key` - SSH keys
❌ `node_modules/` - Node dependencies

## Làm Việc Với Team

### Pull Latest Changes

```bash
git pull origin main
```

### Tạo Feature Branch

```bash
# Tạo branch mới từ main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Làm việc trên branch
# ... edit files ...

# Commit và push
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

### Tạo Merge Request

1. Vào GitLab repository
2. Click **Merge Requests** → **New merge request**
3. Source: `feature/your-feature-name`
4. Target: `main`
5. Fill description
6. Assign reviewers
7. Click **Create merge request**

## Troubleshooting

### Lỗi: "remote origin already exists"

```bash
git remote remove origin
git remote add origin https://gitlab.com/academy-research-chatbot-arc/ARC-project.git
```

### Lỗi: "Authentication failed"

```bash
# Sử dụng Personal Access Token
git remote set-url origin https://oauth2:YOUR_TOKEN@gitlab.com/academy-research-chatbot-arc/ARC-project.git
```

### Lỗi: "Updates were rejected"

```bash
# Pull trước khi push
git pull origin main --rebase
git push origin main
```

### Xem Remote URL

```bash
git remote -v
```

### Xóa File Đã Commit Nhầm

```bash
# Xóa file khỏi Git nhưng giữ local
git rm --cached filename

# Thêm vào .gitignore
echo "filename" >> .gitignore

# Commit
git commit -m "chore: remove sensitive file"
git push origin main
```

## Best Practices

✅ **DO:**
- Commit thường xuyên với message rõ ràng
- Pull trước khi push
- Review code trước khi commit
- Sử dụng .gitignore đúng cách
- Tạo branch cho mỗi feature

❌ **DON'T:**
- Commit secrets, API keys, passwords
- Commit Terraform state files
- Force push lên main branch
- Commit files lớn (>100MB)
- Commit trực tiếp lên main (nên dùng branch)

## Useful Git Commands

```bash
# Xem status
git status

# Xem history
git log --oneline

# Xem changes
git diff

# Undo last commit (giữ changes)
git reset --soft HEAD~1

# Undo changes (mất changes)
git reset --hard HEAD

# Xem branches
git branch -a

# Switch branch
git checkout branch-name

# Delete branch
git branch -d branch-name
```

## Support

Nếu gặp vấn đề:
1. Check error message
2. Google error message
3. Ask team members
4. Check GitLab documentation

---

**Good luck! 🚀**
