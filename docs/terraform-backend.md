# Terraform Backend Configuration

## Overview

Terraform backend stores the state file remotely in S3 and uses DynamoDB for state locking to enable team collaboration.

## Resources

### S3 Bucket
- **Name:** `arc-chatbot-terraform-state`
- **Region:** ap-southeast-1
- **Versioning:** Enabled
- **Encryption:** AES256 (Server-side)
- **Public Access:** Blocked
- **Purpose:** Store terraform.tfstate file

### DynamoDB Table
- **Name:** `terraform-locks`
- **Partition Key:** LockID (String)
- **Billing Mode:** On-demand (PAY_PER_REQUEST)
- **Purpose:** State locking to prevent concurrent modifications

## Setup Instructions

### Option 1: Run Setup Script (Recommended)

**Windows (PowerShell):**
```powershell
.\setup-terraform-backend.ps1
```

**Linux/Mac:**
```bash
chmod +x setup-terraform-backend.sh
./setup-terraform-backend.sh
```

### Option 2: Manual Setup

**1. Create S3 Bucket:**
```bash
aws s3api create-bucket \
  --bucket arc-chatbot-terraform-state \
  --region ap-southeast-1 \
  --create-bucket-configuration LocationConstraint=ap-southeast-1
```

**2. Enable Versioning:**
```bash
aws s3api put-bucket-versioning \
  --bucket arc-chatbot-terraform-state \
  --versioning-configuration Status=Enabled
```

**3. Enable Encryption:**
```bash
aws s3api put-bucket-encryption \
  --bucket arc-chatbot-terraform-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

**4. Block Public Access:**
```bash
aws s3api put-public-access-block \
  --bucket arc-chatbot-terraform-state \
  --public-access-block-configuration \
    BlockPublicAcls=true,\
    IgnorePublicAcls=true,\
    BlockPublicPolicy=true,\
    RestrictPublicBuckets=true
```

**5. Create DynamoDB Table:**
```bash
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-southeast-1
```

## Verification

**Check S3 Bucket:**
```bash
aws s3 ls | grep arc-chatbot-terraform-state
```

**Check DynamoDB Table:**
```bash
aws dynamodb describe-table \
  --table-name terraform-locks \
  --region ap-southeast-1 \
  --query 'Table.[TableName,TableStatus]'
```

**Expected Output:**
```
["terraform-locks", "ACTIVE"]
```

## Usage

### Initialize Terraform
```bash
cd terraform
terraform init
```

**Expected Output:**
```
Initializing the backend...

Successfully configured the backend "s3"!
```

### View State File
```bash
# List state files in S3
aws s3 ls s3://arc-chatbot-terraform-state/infrastructure/

# Download state file (for inspection only)
aws s3 cp s3://arc-chatbot-terraform-state/infrastructure/terraform.tfstate .
```

### Check Lock Status
```bash
# List locks in DynamoDB
aws dynamodb scan \
  --table-name terraform-locks \
  --region ap-southeast-1
```

## Backend Configuration

**File:** `terraform/backend.tf`

```hcl
terraform {
  backend "s3" {
    bucket         = "arc-chatbot-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "ap-southeast-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

## Team Collaboration

**How it works:**

1. **DevOps runs terraform apply:**
   - Acquires lock in DynamoDB
   - Reads state from S3
   - Makes changes
   - Saves state to S3
   - Releases lock

2. **Backend Engineer runs terraform apply (same time):**
   - Tries to acquire lock
   - Waits because DevOps has lock
   - After DevOps finishes, acquires lock
   - Reads updated state from S3
   - No conflicts!

## State File Location

```
s3://arc-chatbot-terraform-state/infrastructure/terraform.tfstate
```

## Cost

- **S3 Storage:** ~$0.01/month (state file is ~100KB)
- **DynamoDB:** FREE (within free tier, very few operations)
- **Total:** ~$0.01/month

## Security

**State file contains sensitive information:**
- Resource IDs
- IP addresses
- Configuration details

**Security measures:**
- ✅ Encryption at rest (AES256)
- ✅ Encryption in transit (HTTPS)
- ✅ Public access blocked
- ✅ IAM-based access control
- ✅ Versioning enabled (backup)

## Troubleshooting

### Error: "Error acquiring the state lock"

**Cause:** Another user is running terraform, or previous run didn't release lock

**Solution:**
```bash
# Check who has the lock
aws dynamodb scan --table-name terraform-locks --region ap-southeast-1

# Force unlock (use with caution!)
terraform force-unlock <LOCK_ID>
```

### Error: "Failed to get existing workspaces"

**Cause:** Backend not initialized

**Solution:**
```bash
cd terraform
terraform init
```

### Error: "NoSuchBucket"

**Cause:** S3 bucket doesn't exist

**Solution:**
```bash
# Run setup script
.\setup-terraform-backend.ps1
```

## Cleanup (If needed)

**To delete backend resources:**

```bash
# Delete S3 bucket (must be empty first)
aws s3 rm s3://arc-chatbot-terraform-state --recursive
aws s3api delete-bucket --bucket arc-chatbot-terraform-state --region ap-southeast-1

# Delete DynamoDB table
aws dynamodb delete-table --table-name terraform-locks --region ap-southeast-1
```

**⚠️ Warning:** Only delete if you're sure you don't need the state file!

## References

- [Terraform S3 Backend](https://www.terraform.io/docs/language/settings/backends/s3.html)
- [State Locking](https://www.terraform.io/docs/language/state/locking.html)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)

---

**Last Updated:** November 2025  
**Maintained by:** DevOps Team
