# Task Dependencies & Expected Outputs

**Project:** Academic Research Chatbot  
**Duration:** 25/11/2025 - 14/12/2025

---

## 🏷️ M0 – Bootstrapping & Learning (25/11 - 29/11)

**Task #1:** Setup AWS Account, IAM Users & Policies - **DevOps** → Kết quả: IAM users, roles, policies cho tất cả services (EC2, S3, DynamoDB, Bedrock, Textract, Amplify)

**Task #2:** Create VPC, Subnets, IGW, NAT Gateway - **DevOps** → Kết quả: VPC ID, Public/Private Subnet IDs, routing tables hoạt động

**Task #3:** Setup Terraform project structure - **DevOps & Tech Lead** → Kết quả: Terraform folder structure, modules cơ bản, state backend (S3)

**Task #4:** Setup VPC Endpoints - **DevOps & Backend+IDP** → Kết quả: VPC Endpoints cho S3, DynamoDB, Textract, Bedrock đã test kết nối

**Task #5:** Setup EC2 t3.small with Security Groups - **Backend+IDP & DevOps** → Kết quả: EC2 instance running, SG cho ports 22, 80, 443, 8000 (FastAPI), 6333 (Qdrant)

**Task #6:** Install Docker, FastAPI boilerplate on EC2 - **Backend+IDP** → Kết quả: Docker running, FastAPI app respond /health endpoint

**Task #7:** Study Bedrock Claude 3.5 & Titan Embeddings APIs - **Backend+IDP & Tech Lead** → Kết quả: Sample code gọi được Claude & Titan, document API notes

**Task #8:** Setup S3 buckets for documents - **Backend+IDP & DevOps** → Kết quả: S3 bucket với proper naming, versioning, lifecycle rules

**Task #9:** Create DynamoDB table for document metadata - **Backend+IDP & DevOps** → Kết quả: DynamoDB table với schema (PK, SK, GSI), sample CRUD operations

**Task #10:** Study Textract AnalyzeDocument API - **Backend+IDP** → Kết quả: Sample code extract text từ PDF, document API notes

**Task #11:** Setup Amplify project with React - **Frontend & DevOps** → Kết quả: Amplify app deployed, React boilerplate với routing

**Task #12:** Configure Cognito User Pools - **Frontend & DevOps & Backend+IDP** → Kết quả: User Pool với 2 groups (admin, researcher), test login flow, JWT token structure documented

---

## 🏷️ M1 – IDP & Ingestion (30/11 - 04/12)

**Task #13:** Create SQS queue for document processing - **Backend+IDP & DevOps** → Kết quả: SQS queue với DLQ, proper visibility timeout, IAM permissions

**Task #14:** Implement PDF detection (digital vs scanned) - **Backend+IDP** → Kết quả: Function phân biệt digital/scanned PDF, unit tests pass

**Task #15:** Implement PyPDF2 extraction for digital PDFs - **Backend+IDP** → Kết quả: Extract text từ digital PDF, handle multi-page, encoding issues

**Task #16:** Implement Textract extraction for scanned PDFs - **Backend+IDP** → Kết quả: Textract integration hoạt động, extract text từ scanned PDF

**Task #17:** Implement text chunking (1000 tokens, 200 overlap) - **Backend+IDP & Tech Lead** → Kết quả: Chunking function với configurable size/overlap, preserve context

**Task #18:** Implement SQS Worker for Textract → Titan → Qdrant - **Backend+IDP & Tech Lead** → Kết quả: Worker process messages, full pipeline hoạt động end-to-end

**Task #19:** Setup Qdrant vector database on EC2 - **Backend+IDP & DevOps & Tech Lead** → Kết quả: Qdrant container running, collection created, test insert/search

**Task #20:** Implement Titan Embeddings integration (1024-dim) - **Backend+IDP** → Kết quả: Function generate embeddings, batch processing support

**Task #21:** Create document status tracking in DynamoDB - **Backend+IDP** → Kết quả: Status field (pending, processing, completed, failed), update logic

**Task #22:** Implement POST /api/admin/upload endpoint - **Backend+IDP** → Kết quả: Upload PDF → S3, create metadata in DynamoDB, return document ID

**Task #23:** Implement GET /api/admin/documents endpoint - **Backend+IDP** → Kết quả: List documents với pagination, filter by status

**Task #24:** Configure S3 event notification to SQS - **DevOps & Backend+IDP** → Kết quả: S3 ObjectCreated trigger SQS, test với sample upload

---

## 🏷️ M2 – RAG Chat API (05/12 - 09/12)

**Task #25:** Implement vector search in Qdrant - **Backend+IDP & Tech Lead** → Kết quả: Search function với top-k results, filter by metadata, relevance scores

**Task #26:** Implement Bedrock Claude 3.5 Sonnet integration - **Backend+IDP & Tech Lead** → Kết quả: Claude API wrapper, streaming support, token counting

**Task #27:** Build RAG prompt template with citations - **Backend+IDP & Tech Lead** → Kết quả: Prompt template với context injection, citation format [1], [2]...

**Task #28:** Implement POST /api/chat endpoint - **Backend+IDP** → Kết quả: Chat endpoint nhận query, trả response với citations, conversation_id

**Task #29:** Implement chat history storage in DynamoDB - **Backend+IDP** → Kết quả: Store messages với conversation_id, retrieve history cho context

**Task #30:** Add rate limiting for Claude API calls - **Backend+IDP & DevOps** → Kết quả: Rate limiter (requests/min), queue mechanism, 429 response

**Task #31:** Implement fallback to Claude Haiku on budget limit - **Backend+IDP** → Kết quả: Budget tracking, auto-switch to Haiku khi vượt threshold

**Task #32:** Add error handling & retry logic for Bedrock - **Backend+IDP** → Kết quả: Retry với exponential backoff, graceful error messages

**Task #33:** Setup ALB with health checks - **DevOps** → Kết quả: ALB created, health check path /health, target group configured

**Task #34:** Configure ALB → EC2 routing - **DevOps & Backend+IDP** → Kết quả: ALB route traffic to EC2, HTTPS termination, test API qua ALB

---

## 🏷️ M3 – Frontend & Monitoring (10/12 - 14/12)

**Task #35:** Implement login page with Cognito - **Frontend** → Kết quả: Login/Register UI, Cognito integration, redirect after auth

**Task #36:** Build chat interface UI - **Frontend & Backend+IDP** → Kết quả: Chat UI với message bubbles, input box, loading states, API integration

**Task #37:** Display citations with document links - **Frontend & Backend+IDP** → Kết quả: Citations hiển thị inline, click để xem source document

**Task #38:** Build admin dashboard for document upload - **Frontend & Backend+IDP** → Kết quả: Upload form, drag-drop, progress bar, call /api/admin/upload

**Task #39:** Show document processing status - **Frontend & Backend+IDP** → Kết quả: Status badges (pending/processing/done/failed), auto-refresh

**Task #40:** Implement chat history view - **Frontend & Backend+IDP** → Kết quả: List previous conversations, click để load history

**Task #41:** Setup Route 53 domain - **DevOps** → Kết quả: Domain configured, DNS records cho ALB và CloudFront

**Task #42:** Configure CloudFront distribution - **DevOps & Frontend** → Kết quả: CloudFront cho Amplify, caching rules, custom domain

**Task #43:** Setup CloudWatch alarms (4 alarms) - **DevOps** → Kết quả: Alarms cho EC2 CPU, ALB 5xx, DynamoDB throttle, Lambda errors

**Task #44:** Configure SNS email notifications - **DevOps** → Kết quả: SNS topic, email subscription, test alarm notification

**Task #45:** Setup CodePipeline CI/CD - **DevOps & Backend+IDP** → Kết quả: Pipeline từ GitLab → Build → Deploy, trigger on push

**Task #46:** Configure CodeBuild & CodeDeploy - **DevOps & Backend+IDP** → Kết quả: buildspec.yml, appspec.yml, deployment scripts

**Task #47:** Write API documentation - **Backend+IDP** → Kết quả: OpenAPI/Swagger spec, endpoint descriptions, request/response examples

**Task #48:** Create infrastructure documentation - **DevOps & Tech Lead** → Kết quả: Architecture diagram, resource inventory, runbook cho operations

---

## 📊 Role Summary

| Role | Total Tasks | Solo | Collaboration |
|------|-------------|------|---------------|
| **Tech Lead** | 10 | 0 | 10 (pair/review) |
| **Backend+IDP** | 35 | 12 | 23 |
| **Frontend** | 8 | 1 | 7 |
| **DevOps** | 18 | 5 | 13 |

---

*Generated: November 2025*
