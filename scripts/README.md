# Cognito Setup Scripts

Scripts to setup test users in AWS Cognito User Pool for local development.

## Prerequisites

1. **AWS CLI installed and configured:**
   ```bash
   aws configure
   ```
   
2. **IAM Permissions:**
   Your AWS user needs these Cognito permissions:
   - `cognito-idp:AdminCreateUser`
   - `cognito-idp:AdminSetUserPassword`
   - `cognito-idp:AdminAddUserToGroup`
   - `cognito-idp:CreateGroup`

## Usage

### Option 1: Python Script (Recommended)

```bash
# Install boto3 if not already installed
pip install boto3

# Run script
python scripts/setup-cognito-users.py
```

### Option 2: Bash Script

```bash
# Make executable
chmod +x scripts/setup-cognito-users.sh

# Run script
./scripts/setup-cognito-users.sh
```

### Option 3: PowerShell (Windows)

```powershell
# Run from project root
python scripts/setup-cognito-users.py
```

## Test Users Created

| Email | Password | Group | Role |
|-------|----------|-------|------|
| admin@arc.com | Admin123! | admin | Can upload documents |
| researcher@arc.com | Researcher123! | researcher | Can only chat |

## After Setup

1. Start frontend dev server:
   ```bash
   npm run dev
   ```

2. Open browser: `http://localhost:5173/login`

3. Login with test credentials

4. Test features:
   - Admin: Can access `/admin` page
   - Researcher: Redirected from `/admin` to `/chat`

## Troubleshooting

**Error: "An error occurred (NotAuthorizedException)"**
- Check AWS credentials: `aws sts get-caller-identity`
- Verify IAM permissions

**Error: "User already exists"**
- Users already created, you can login directly
- Or delete users first:
  ```bash
  aws cognito-idp admin-delete-user \
    --user-pool-id ap-southeast-1_8KB4JYvsX \
    --username admin@arc.com \
    --region ap-southeast-1
  ```

**Error: "ResourceNotFoundException: Group not found"**
- Script will auto-create groups
- Or create manually in Cognito Console

## Manual Setup (Alternative)

If scripts don't work, create users manually in AWS Console:

1. Go to Cognito Console → User Pools → `arc-chatbot-users`
2. Click "Create user"
3. Fill in email, set password, mark email as verified
4. Add user to appropriate group (admin/researcher)

## Security Notes

⚠️ **These are TEST credentials only!**
- Do NOT use in production
- Change passwords after testing
- Delete test users when done

## Next Steps

After users are created:
- ✅ Test login flow
- ✅ Test protected routes
- ✅ Test admin vs researcher access
- ✅ Continue with Task #36 (Chat Interface)
