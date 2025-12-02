# Knowledge Preparation - Academic Research Chatbot

> Tài liệu kiến thức nền tảng cho dự án Academic Research Chatbot for Students

---

## 📚 Mục lục

1. [Amazon EC2](#1-amazon-ec2)
2. [FastAPI Framework](#2-fastapi-framework)
3. [Tại sao chọn FastAPI?](#3-tại-sao-chọn-fastapi)
4. [Kiến trúc tổng quan](#4-kiến-trúc-tổng-quan)

---

## 1. Amazon EC2

### 1.1 EC2 là gì?

**EC2 (Elastic Compute Cloud)** là dịch vụ máy chủ ảo của AWS, cho phép thuê máy tính trên cloud với cấu hình linh hoạt (CPU, RAM, Storage). Chỉ trả tiền cho những gì sử dụng.

### 1.2 Các loại Instance phổ biến

| Family | Đặc điểm | Use Case |
|--------|----------|----------|
| **t3/t3a** | Burstable, giá rẻ | Dev/test, web apps nhỏ |
| **m6i/m7i** | Cân bằng CPU/RAM | Production web servers |
| **c6i/c7i** | CPU mạnh | AI inference, xử lý nặng |
| **r6i/r7i** | RAM lớn | Database, caching |

### 1.3 Instance cho dự án

```hcl
# Terraform configuration
instance_type = "t3.small"  # 2 vCPU, 2GB RAM - phù hợp cho dev/staging
```

**Khuyến nghị scale:**
- Development: `t3.small` (2 vCPU, 2GB RAM)
- Staging: `t3.medium` (2 vCPU, 4GB RAM)
- Production: `t3.large` hoặc `m6i.large` (2 vCPU, 8GB RAM)

---

## 2. FastAPI Framework

### 2.1 FastAPI là gì?

**FastAPI** là framework Python hiện đại để xây dựng REST API, nổi bật với:

- ⚡ **Async/await** - Xử lý nhiều request đồng thời
- 📄 **Auto-generate docs** - Swagger UI tự động
- ✅ **Type hints** - Validation tự động
- 🚀 **Hiệu năng cao** - Ngang Golang, NodeJS

### 2.2 Ví dụ cơ bản

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Academic Research Chatbot API")

class ChatRequest(BaseModel):
    user_id: str
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[str]

@app.get("/health")
async def health_check():
    """Health check endpoint cho ALB"""
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chatbot endpoint"""
    # Gọi Bedrock Claude để trả lời
    return ChatResponse(
        answer="...",
        sources=["paper1.pdf"]
    )
```

---

## 3. Tại sao chọn FastAPI?

### 3.1 Ba lý do chính

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI = Lựa chọn tối ưu                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│   │   PYTHON    │   │    ASYNC    │   │   MODERN    │          │
│   │  Ecosystem  │ + │   Native    │ + │  Features   │          │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘          │
│          │                 │                 │                  │
│          ▼                 ▼                 ▼                  │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│   │ • boto3     │   │ • Xử lý     │   │ • Type      │          │
│   │ • langchain │   │   song song │   │   hints     │          │
│   │ • PyPDF2    │   │ • Không     │   │ • Auto      │          │
│   │ • transform │   │   blocking  │   │   docs      │          │
│   └─────────────┘   └─────────────┘   └─────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Giải thích chi tiết

#### 🐍 Python Ecosystem (Hệ sinh thái AI)

**Vấn đề**: Chatbot cần gọi AI (Claude/Bedrock) để trả lời câu hỏi.

**Thực tế**: 90% thư viện AI/ML được viết bằng Python:

| Thư viện | Chức năng |
|----------|-----------|
| `boto3` | Gọi AWS Bedrock (Claude AI) |
| `langchain` | Xây dựng chatbot pipeline |
| `PyPDF2` | Đọc file PDF papers |
| `sentence-transformers` | Tìm papers liên quan |

**Kết luận**: Dùng FastAPI (Python) = dùng trực tiếp các thư viện này.

#### ⚡ Async Native (Xử lý đồng thời)

**Vấn đề**: Gọi AI mất 3-5 giây. Nếu 10 students hỏi cùng lúc?

**Không có Async (Flask):**
```
Student A hỏi → Chờ 5s → Trả lời A
Student B hỏi → Chờ 5s → Trả lời B  (B phải đợi A xong)
Student C hỏi → Chờ 5s → Trả lời C  (C phải đợi B xong)
────────────────────────────────────
Tổng thời gian: 15 giây
```

**Có Async (FastAPI):**
```
Student A hỏi ─┐
Student B hỏi ─┼─→ Xử lý song song → Trả lời cả 3
Student C hỏi ─┘
────────────────────────────────────
Tổng thời gian: ~5 giây
```

#### 🔧 Modern Features

**Type hints** - Khai báo kiểu dữ liệu:
```python
# ❌ Không có type hints - dễ sai
def chat(request):
    question = request["question"]  # Lỗi nếu thiếu key

# ✅ Có type hints - FastAPI tự validate
def chat(request: ChatRequest):
    question = request.question  # Tự động báo lỗi nếu sai
```

**Auto docs** - Tài liệu API tự động:
```
Truy cập: http://your-api/docs
→ Giao diện Swagger UI test API trên browser
→ Frontend dev không cần hỏi "API gửi gì, nhận gì?"
```

### 3.3 So sánh với các Framework khác

| Framework | Ngôn ngữ | Async | AI Libs | Đánh giá cho dự án |
|-----------|----------|-------|---------|-------------------|
| **FastAPI** | Python | ✅ | ✅ | ⭐ Tối ưu |
| Flask | Python | ❌ | ✅ | Blocking, chậm |
| Django | Python | ⚠️ | ✅ | Overkill |
| Express | Node.js | ✅ | ❌ | Thiếu AI libs |
| Gin | Go | ✅ | ❌ | Thiếu AI libs |

---

## 4. Kiến trúc tổng quan

### 4.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              ACADEMIC RESEARCH CHATBOT ARCHITECTURE             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Student Browser                                               │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────┐     ┌──────────────────────────────────────┐     │
│   │ Amplify │────▶│  ALB (Application Load Balancer)     │     │
│   │ (React) │     │  • SSL termination                   │     │
│   └─────────┘     │  • Health checks (/health)           │     │
│                   └──────────────────┬───────────────────┘     │
│                                      │                          │
│                                      ▼                          │
│                   ┌──────────────────────────────────────┐     │
│                   │  EC2 Instance (Private Subnet)       │     │
│                   │  ┌────────────────────────────────┐  │     │
│                   │  │  FastAPI Application (Port 8000)│  │     │
│                   │  │  • POST /chat                  │  │     │
│                   │  │  • POST /upload-paper          │  │     │
│                   │  │  • GET  /search-papers         │  │     │
│                   │  │  • GET  /health                │  │     │
│                   │  └────────────────────────────────┘  │     │
│                   └──────────────────┬───────────────────┘     │
│                                      │                          │
│          ┌───────────────────────────┼───────────────────┐     │
│          ▼                           ▼                   ▼     │
│   ┌────────────┐            ┌────────────┐       ┌──────────┐ │
│   │  DynamoDB  │            │  S3 Bucket │       │ Bedrock  │ │
│   │  • Users   │            │  • PDFs    │       │ • Claude │ │
│   │  • History │            │  • Papers  │       │ • LLM    │ │
│   └────────────┘            └────────────┘       └──────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Request Flow

```
┌────────────────────────────────────────────────────────────────┐
│                      CHATBOT REQUEST FLOW                       │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Student gửi câu hỏi                                        │
│     │                                                           │
│     ▼                                                           │
│  2. React App (Amplify) → POST /chat                           │
│     │                                                           │
│     ▼                                                           │
│  3. ALB forward request → EC2 (FastAPI)                        │
│     │                                                           │
│     ▼                                                           │
│  4. FastAPI xử lý:                                             │
│     ├─→ Xác thực user (Cognito)                                │
│     ├─→ Tìm papers liên quan (DynamoDB/S3)                     │
│     └─→ Gọi Bedrock Claude với context                         │
│     │                                                           │
│     ▼                                                           │
│  5. Trả response về cho Student                                │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 4.3 Terraform Components

| Component | File | Mục đích |
|-----------|------|----------|
| VPC | `modules/vpc/` | Network isolation |
| EC2 + ALB | `modules/ec2/` | FastAPI server |
| DynamoDB | `modules/dynamodb/` | Data storage |
| S3 | `modules/s3/` | PDF storage |
| Cognito | `modules/cognito/` | Authentication |
| IAM | `modules/iam/` | Permissions |
| Amplify | `modules/amplify/` | Frontend hosting |

---

## 📖 Tài liệu tham khảo

- [AWS EC2 Instance Types](https://docs.aws.amazon.com/ec2/latest/instancetypes/instance-types.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS Bedrock Developer Guide](https://docs.aws.amazon.com/bedrock/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

---

*Cập nhật lần cuối: November 2024*
