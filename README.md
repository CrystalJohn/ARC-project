
# Academic Research Chatbot (ARC)

RAG-based chatbot for academic research papers using AWS infrastructure.

## 📋 Project Overview

- **Type**: AWS Internship Project
- **Team**: 4 interns (Tech Lead, Backend+IDP, Frontend, DevOps)
- **Timeline**: 20 days
- **Budget**: ~$60/month
- **Users**: 50 researchers
- **Documents**: 750 academic papers

## 🏗️ Architecture

```
Frontend:     Route 53 → CloudFront → Amplify (React) → Cognito
Backend:      ALB → EC2 t3.small (FastAPI + Qdrant + Worker)
AI/ML:        Bedrock Claude 3.5 Sonnet + Titan Embeddings v2
IDP:          SQS → EC2 Worker → Textract → Embeddings → Qdrant
Data:         S3 (documents) + DynamoDB (metadata, chat history)
```

## 📁 Project Structure

```
ARC-project/
├── terraform/              # Infrastructure as Code
│   ├── modules/           # Terraform modules
│   │   ├── vpc/
│   │   ├── iam/
│   │   ├── ec2/
│   │   ├── s3/
│   │   ├── dynamodb/
│   │   ├── cognito/
│   │   └── amplify/
│   └── README.md
├── backend/               # FastAPI application (to be created)
├── frontend/              # React application (to be created)
├── samples/               # AWS service sample code (to be created)
├── docs/                  # Documentation (to be created)
├── .kiro/                 # Kiro specs
│   └── specs/
│       ├── m0-infrastructure-setup/
│       └── m1-idp-ingestion/
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.0
- AWS CLI configured
- Docker (for local development)
- Node.js >= 18 (for frontend)
- Python >= 3.11 (for backend)

### 1. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

See [terraform/README.md](terraform/README.md) for detailed instructions.

### 2. Setup Backend (Coming Soon)

```bash
cd backend
# Instructions to be added
```

### 3. Setup Frontend (Coming Soon)

```bash
cd frontend
# Instructions to be added
```

## 📚 Documentation

- [Infrastructure Setup](terraform/README.md)
- [Project Knowledge Base](knowledge-project.md)
- [Task Dependencies](task-output-project.md)
- [M0 Spec - Infrastructure Setup](.kiro/specs/m0-infrastructure-setup/)
- [M1 Spec - IDP & Ingestion](.kiro/specs/m1-idp-ingestion/)

## 💰 Cost Breakdown (~$60/month)

| Service | Cost |
|---------|------|
| EC2 t3.small (480h) | $10.08 |
| EBS 30GB | $2.40 |
| NAT Gateway (480h) | $21.60 |
| Bedrock Claude 3.5 | $25.00 |
| Bedrock Titan | $0.75 |
| CloudWatch + Data | $1.90 |
| **TOTAL** | **~$60** |

## 🔧 Tech Stack

**Infrastructure:**
- AWS (VPC, EC2, S3, DynamoDB, Cognito, Amplify)
- Terraform (IaC)

**Backend:**
- FastAPI (Python)
- Qdrant (Vector DB)
- AWS Bedrock (Claude 3.5 Sonnet, Titan Embeddings v2)
- AWS Textract (OCR)
- SQS (Message Queue)

**Frontend:**
- React
- AWS Amplify
- AWS Cognito (Auth)

## 👥 Team Roles

| Role | Responsibilities |
|------|------------------|
| Tech Lead | Architecture, EC2, FastAPI, Textract |
| Backend+IDP | Bedrock, Qdrant, IDP pipeline |
| Frontend | React, Amplify, Cognito |
| DevOps | Terraform, CI/CD, CloudWatch |

## 📅 Milestones

- **M0** (Days 1-5): Infrastructure Setup
- **M1** (Days 6-10): IDP & Ingestion Pipeline
- **M2** (Days 11-15): RAG Chat API
- **M3** (Days 16-20): Frontend & Monitoring

## 🔐 Security

- EC2 in private subnet
- S3 buckets with encryption and blocked public access
- IAM least-privilege policies
- Cognito for authentication
- VPC endpoints for AWS services

## 📝 License

This project is for educational purposes as part of an AWS internship program.
