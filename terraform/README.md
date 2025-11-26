# ARC Chatbot - Terraform Infrastructure

This directory contains Terraform configuration for provisioning AWS infrastructure for the Academic Research Chatbot project.

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured with appropriate credentials
- AWS Account with necessary permissions

## Infrastructure Components

- **VPC**: Virtual Private Cloud with public and private subnets
- **EC2**: t3.small instance running FastAPI and Qdrant
- **S3**: Document storage bucket
- **DynamoDB**: DocumentMetadata and ChatHistory tables
- **Cognito**: User authentication with admin and researcher groups
- **Amplify**: React frontend hosting
- **IAM**: Roles and policies for EC2 and team members
- **ALB**: Application Load Balancer for EC2 access
- **VPC Endpoints**: Gateway (S3, DynamoDB) and Interface (Bedrock, Textract)

## Directory Structure

```
terraform/
├── main.tf              # Main configuration
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── backend.tf           # S3 backend configuration
├── terraform.tfvars     # Variable values
└── modules/
    ├── vpc/             # VPC and networking
    ├── iam/             # IAM users, roles, policies
    ├── s3/              # S3 buckets
    ├── dynamodb/        # DynamoDB tables
    ├── ec2/             # EC2 instance and ALB
    ├── cognito/         # Cognito User Pool
    └── amplify/         # Amplify app
```

## Setup Instructions

### 1. Initialize Backend (First Time Only)

Before running Terraform, create the S3 bucket and DynamoDB table for state management:

```bash
# Create S3 bucket for Terraform state
aws s3api create-bucket \
  --bucket arc-chatbot-terraform-state \
  --region ap-southeast-1 \
  --create-bucket-configuration LocationConstraint=ap-southeast-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket arc-chatbot-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-southeast-1
```

### 2. Initialize Terraform

```bash
cd terraform
terraform init
```

### 3. Review Configuration

Edit `terraform.tfvars` if needed:

```hcl
aws_region        = "ap-southeast-1"
project_name      = "arc-chatbot"
environment       = "dev"
vpc_cidr          = "10.0.0.0/16"
availability_zone = "ap-southeast-1a"
```

### 4. Validate Configuration

```bash
terraform validate
```

### 5. Plan Deployment

```bash
terraform plan
```

Review the plan output to ensure all resources are correct.

### 6. Apply Configuration

```bash
terraform apply
```

Type `yes` when prompted to confirm.

### 7. View Outputs

After successful deployment:

```bash
terraform output
```

Important outputs:
- `alb_dns_name`: URL to access the API
- `cognito_user_pool_id`: For frontend configuration
- `cognito_app_client_id`: For frontend configuration
- `documents_bucket_name`: S3 bucket for uploads

## Post-Deployment Steps

### 1. Access EC2 Instance

```bash
# Get instance ID
INSTANCE_ID=$(terraform output -raw ec2_instance_id)

# SSH via Session Manager (recommended)
aws ssm start-session --target $INSTANCE_ID

# Or SSH directly (if you have key pair configured)
# ssh -i your-key.pem ec2-user@<private-ip>
```

### 2. Verify Services

```bash
# Check Docker containers
docker ps

# Check FastAPI
curl http://localhost:8000/health

# Check Qdrant
curl http://localhost:6333/health
```

### 3. Test ALB Endpoint

```bash
ALB_DNS=$(terraform output -raw alb_dns_name)
curl http://$ALB_DNS/health
```

### 4. Create Cognito Users

```bash
# Create admin user
aws cognito-idp admin-create-user \
  --user-pool-id $(terraform output -raw cognito_user_pool_id) \
  --username admin@example.com \
  --user-attributes Name=email,Value=admin@example.com Name=email_verified,Value=true \
  --temporary-password TempPass123!

# Add to admin group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id $(terraform output -raw cognito_user_pool_id) \
  --username admin@example.com \
  --group-name admin
```

## Updating Infrastructure

```bash
# Make changes to .tf files
# Plan changes
terraform plan

# Apply changes
terraform apply
```

## Destroying Infrastructure

**Warning**: This will delete all resources and data!

```bash
terraform destroy
```

## Cost Estimation

Approximate monthly costs:
- EC2 t3.small (480h): $10.08
- EBS 30GB: $2.40
- NAT Gateway (480h): $21.60
- Bedrock Claude 3.5: ~$25.00
- Bedrock Titan: ~$0.75
- Interface VPC Endpoints: ~$14.60
- **Total**: ~$75/month

Free tier services:
- S3, DynamoDB, SQS, SNS, CloudWatch (within limits)
- Cognito (within limits)
- Textract (100 pages/month)

## Troubleshooting

### Terraform Init Fails

```bash
# Clear cache and reinitialize
rm -rf .terraform .terraform.lock.hcl
terraform init
```

### State Lock Error

```bash
# Force unlock (use with caution)
terraform force-unlock <LOCK_ID>
```

### EC2 Not Accessible

- Check security group rules
- Verify EC2 is in private subnet
- Use ALB DNS name, not EC2 IP

### ALB Health Check Failing

- SSH to EC2 and check Docker containers
- Verify FastAPI is running on port 8000
- Check `/health` endpoint returns 200

## Module Documentation

Each module has its own README with detailed configuration options:

- [VPC Module](./modules/vpc/README.md)
- [IAM Module](./modules/iam/README.md)
- [EC2 Module](./modules/ec2/README.md)
- [S3 Module](./modules/s3/README.md)
- [DynamoDB Module](./modules/dynamodb/README.md)
- [Cognito Module](./modules/cognito/README.md)
- [Amplify Module](./modules/amplify/README.md)

## Security Notes

1. **SSH Access**: Restrict EC2 security group to specific IP ranges
2. **IAM Keys**: Store access keys securely, rotate regularly
3. **S3 Buckets**: Public access is blocked by default
4. **Cognito**: Enable MFA for admin users
5. **VPC**: EC2 in private subnet, no direct internet access

## Support

For issues or questions, contact the DevOps team or refer to the project documentation.
