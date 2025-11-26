# Academic Research Chatbot - Project Knowledge Base

## 📋 Project Overview

| Item | Value |
|------|-------|
| **Project Type** | AWS Internship (Basic AWS Knowledge) |
| **Team** | 4 interns |
| **Timeline** | 20 days (EC2 runs continuously) |
| **Budget** | Maximum ~$60/month |
| **Users** | 50 researchers |
| **Documents** | 750 academic papers |

**Solution:** IDP (Textract) + RAG (Qdrant + Bedrock Claude 3.5 Sonnet) for academic research chatbot with citations.

---

## 🏗️ Architecture Components

```
Frontend:     Route 53 → CloudFront → Amplify (React App) → Cognito (admins, researchers)
Backend:      ALB → EC2 t3.small (FastAPI + Qdrant + Worker) in Private Subnet
AI/ML:        Bedrock Claude 3.5 Sonnet (LLM) + Titan Embeddings v2 (1024-dim)
IDP:          SQS → EC2 Worker → Textract (OCR + Tables) → Embeddings → Qdrant
Data:         S3 (documents) + DynamoDB (metadata, chat history)
Monitoring:   CloudWatch (4 alarms) + SNS (email)
CI/CD:        GitLab → CodePipeline → CodeBuild → CodeDeploy → S3
```

### VPC Endpoints
| Type | Services | Cost |
|------|----------|------|
| Gateway Endpoint | S3, DynamoDB | FREE |
| Interface Endpoint | Textract, Bedrock Runtime | ~$7.30/month each |

### NAT Gateway
- **Purpose:** OS/package updates & optional external APIs
- **NOT used for:** App data path (IDP/RAG uses VPC Interface Endpoints)

### Key Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| NAT | NAT Gateway | Managed, simpler for interns (vs NAT Instance $3/month) |
| Vector DB | Qdrant (self-hosted) | Save $90/month vs OpenSearch Serverless |
| Processing | EC2 Worker | No timeout, direct Qdrant access (vs Lambda) |
| IDP | Hybrid | PyPDF2 (digital) + Textract (scanned, 100 pages/month free) |

---

## 🔄 Two Main Flows

### Flow 1: Researcher Chat (Solid Lines)
```
① Researchers → ② Route53 → ③ CloudFront → ④ Amplify → ⑤ Cognito
→ ⑥ IGW → ⑦ ALB → ⑧ EC2 → ⑨ Bedrock Titan (embed) → ⑩ Qdrant (search)
→ ⑪ Bedrock Claude (generate) → ⑫ DynamoDB (save) → Return answer + citations
```

### Flow 2: Developer Upload & IDP (Solid + Dashed)
```
Upload (Solid):
① Dev → ② Route53 → ③ CloudFront → ④ Amplify → ⑤ Cognito
→ ⑥ IGW → ⑦ ALB → ⑧ EC2 → ⑨ S3 (upload) → ⑩ DynamoDB (UPLOADED) → ⑪ SQS

Background IDP (Dashed):
⑫ SQS → ⑬ EC2 Worker → ⑭ DynamoDB (IDP_RUNNING) → ⑮ Textract (OCR)
→ ⑯ Normalize/Chunk → ⑰ Bedrock Titan (embed) → ⑱ Qdrant (upsert)
→ ⑲ DynamoDB (EMBEDDING_DONE)
```

---

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

### Free Tier Used
| Category | Services | Notes |
|----------|----------|-------|
| **12-month Free Tier** | S3, CloudFront, Cognito | Low traffic expected |
| **Always Free** | DynamoDB, SQS, SNS, CloudWatch | Within free quotas |
| **3-month Free Tier** | Textract AnalyzeDocument | 100 pages/month |

---

## 🔧 Technical Specs

**EC2 t3.small (2GB RAM):**
- FastAPI: ~200MB
- Qdrant: ~400MB (7,500 vectors)
- Worker: ~100MB
- EBS: 30GB gp3

**Document Processing:**
- Chunk: 1000 tokens, 200 overlap
- ~10 chunks/document
- Metadata: doc_id, page, section, is_table

**API Endpoints:**
- `POST /api/chat` - Researcher query
- `POST /api/admin/upload` - Admin upload
- `GET /api/admin/documents` - List with status

---

## 👥 Team Roles (4 Interns)

| Role | Focus |
|------|-------|
| Tech Lead | Architecture, EC2, FastAPI, Textract |
| ML Engineer | Bedrock, Qdrant, IDP pipeline |
| Frontend | React, S3/CloudFront, Cognito |
| DevOps/QA | Terraform, CI/CD, CloudWatch |

**Learning overhead:** ~5-7 days (Bedrock, Textract, Qdrant)

---

## 📅 Timeline (20 Days)

| Week | Focus |
|------|-------|
| 1 (Days 1-5) | AWS setup, VPC, EC2, S3, DynamoDB |
| 2 (Days 6-10) | Backend APIs, IDP pipeline, integration |
| 3 (Days 11-15) | Testing, error handling, optimization |
| 4 (Days 16-20) | Deployment, documentation, handover |

---

## ⚠️ Key Risks

| Risk | Mitigation |
|------|------------|
| EC2 SPOF | CloudWatch alarm, auto-restart |
| Claude budget | Rate limiting, fallback to Haiku |
| Timeline tight | Reduce scope if needed |
| Learning curve | Pre-study, pair programming |

---

## 📊 Assessment: 8.2/10 - FEASIBLE ✅

**Strengths:** Clear problem, cost-optimized, proven stack
**Weaknesses:** Tight timeline, learning curve for interns
**Conditions:** Basic AWS knowledge, MVP quality accepted, $60 budget

---

*Last Updated: November 2024*
