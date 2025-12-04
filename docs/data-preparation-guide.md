# Data Preparation Guide - Academic Research Chatbot

## Mục đích

Hướng dẫn chuẩn bị và tổ chức tài liệu để upload vào hệ thống RAG chatbot, đảm bảo chất lượng tìm kiếm và trả lời tối ưu.

---

## 📁 Loại tài liệu nên upload

### Ưu tiên cao (Must Have)

| Loại | Mô tả | Số lượng ước tính |
|------|-------|-------------------|
| **Thesis/Dissertations** | Luận văn thạc sĩ, tiến sĩ | 300-400 files |
| **Student Handbook** | Quy chế, quy định đào tạo | 10-20 files |
| **Curriculum Documents** | Chương trình đào tạo các ngành | 20-30 files |
| **Research Papers** | Bài báo khoa học của giảng viên | 200-300 files |

### Ưu tiên trung bình (Should Have)

| Loại | Mô tả | Số lượng ước tính |
|------|-------|-------------------|
| **Course Syllabi** | Đề cương môn học | 50-100 files |
| **Lab Manuals** | Hướng dẫn thực hành | 30-50 files |
| **Conference Proceedings** | Kỷ yếu hội thảo | 50-100 files |

### Ưu tiên thấp (Nice to Have)

| Loại | Mô tả | Số lượng ước tính |
|------|-------|-------------------|
| **Lecture Notes** | Bài giảng (nếu có bản PDF) | Tùy chọn |
| **Project Reports** | Báo cáo đồ án | Tùy chọn |
| **Newsletter/Announcements** | Thông báo quan trọng | Tùy chọn |

---

## 📄 Format tài liệu tối ưu

### Định dạng file

| Format | Hỗ trợ | Chất lượng OCR | Ghi chú |
|--------|--------|----------------|---------|
| **PDF (digital)** | ✅ Tốt nhất | N/A | Text có thể copy |
| **PDF (scanned)** | ✅ Hỗ trợ | Tốt | Cần Textract OCR |
| **PDF (hybrid)** | ✅ Hỗ trợ | Trung bình | Mix text + image |

### Yêu cầu chất lượng PDF

#### Digital PDF (Ưu tiên)
```
✅ Text có thể select/copy
✅ Fonts embedded
✅ Bookmarks/TOC nếu có
✅ Searchable
```

#### Scanned PDF
```
✅ Resolution >= 300 DPI
✅ Không bị nghiêng, mờ
✅ Contrast tốt (text đen, nền trắng)
✅ Không có watermark che text
```

### Tables trong PDF
```
✅ Textract Table Extraction tự động detect tables
✅ Hỗ trợ: Simple tables, merged cells, nested tables
✅ Output: Row/column structure preserved
✅ Metadata: is_table flag để identify table chunks
✅ Best practice: Tránh tables quá phức tạp (>10 columns)
```

### Kích thước file

| Metric | Khuyến nghị | Tối đa |
|--------|-------------|--------|
| File size | < 10 MB | 50 MB |
| Số trang | < 100 pages | 500 pages |
| Text length | < 50,000 words | 200,000 words |

---

## 📝 Naming Conventions

### Format chuẩn

```
[TYPE]_[YEAR]_[AUTHOR/DEPT]_[TITLE_SHORT].pdf
```

### Ví dụ theo loại

#### Thesis
```
THESIS_2024_NguyenVanA_CNN_Image_Classification.pdf
THESIS_2023_TranThiB_NLP_Sentiment_Analysis.pdf
DISSERTATION_2024_LeVanC_Deep_Learning_Healthcare.pdf
```

#### Student Handbook
```
HANDBOOK_2024_Graduate_Regulations.pdf
HANDBOOK_2024_Undergraduate_Academic_Policy.pdf
HANDBOOK_2024_Research_Ethics_Guidelines.pdf
```

#### Curriculum
```
CURRICULUM_2024_CS_Bachelor_Program.pdf
CURRICULUM_2024_AI_Master_Program.pdf
CURRICULUM_2024_DS_Course_Catalog.pdf
```

#### Research Papers
```
PAPER_2024_NguyenA_BERT_Vietnamese_NER.pdf
PAPER_2023_TranB_Object_Detection_Survey.pdf
PAPER_2024_LeC_Transformer_Applications.pdf
```

### Quy tắc đặt tên

| Rule | Đúng ✅ | Sai ❌ |
|------|---------|--------|
| Không dấu tiếng Việt | NguyenVanA | Nguyễn_Văn_A |
| Underscore thay space | Deep_Learning | Deep Learning |
| Không ký tự đặc biệt | CNN_Model | CNN@Model#1 |
| Viết hoa chữ cái đầu | Image_Classification | image_classification |
| Năm 4 chữ số | 2024 | 24 |

---

## 🗂️ Cấu trúc thư mục S3

```
s3://academic-chatbot-documents-{account-id}/
├── uploads/                    # Raw uploads (trigger IDP)
│   ├── thesis/
│   │   ├── 2024/
│   │   └── 2023/
│   ├── handbook/
│   ├── curriculum/
│   └── papers/
├── processed/                  # After IDP processing
│   └── {doc_id}/
│       ├── original.pdf
│       ├── extracted_text.json
│       └── metadata.json
└── archive/                    # Old versions
```

---

## 📋 Metadata Requirements

### Bắt buộc (Required)

| Field | Type | Mô tả | Ví dụ |
|-------|------|-------|-------|
| `title` | string | Tiêu đề tài liệu | "Ứng dụng CNN trong nhận dạng" |
| `doc_type` | enum | Loại tài liệu | thesis, handbook, curriculum, paper |
| `year` | number | Năm xuất bản | 2024 |
| `language` | string | Ngôn ngữ | vi, en |

### Khuyến nghị (Recommended)

| Field | Type | Mô tả | Ví dụ |
|-------|------|-------|-------|
| `author` | string | Tác giả | "Nguyễn Văn A" |
| `department` | string | Khoa/Bộ môn | "Khoa CNTT" |
| `advisor` | string | Người hướng dẫn | "PGS.TS Trần B" |
| `keywords` | array | Từ khóa | ["machine learning", "CNN"] |
| `abstract` | string | Tóm tắt | "Nghiên cứu này..." |

### Tùy chọn (Optional)

| Field | Type | Mô tả |
|-------|------|-------|
| `isbn` | string | Mã ISBN nếu có |
| `doi` | string | DOI của paper |
| `conference` | string | Tên hội thảo |
| `journal` | string | Tên tạp chí |

---

## ✅ Pre-upload Checklist

### Kiểm tra file

- [ ] File format là PDF
- [ ] File size < 50 MB
- [ ] File không bị corrupt (mở được)
- [ ] File không password protected
- [ ] Nội dung đọc được (không quá mờ)

### Kiểm tra nội dung

- [ ] Tài liệu có giá trị học thuật
- [ ] Không chứa thông tin nhạy cảm/cá nhân
- [ ] Không vi phạm bản quyền
- [ ] Ngôn ngữ phù hợp (Tiếng Việt hoặc Tiếng Anh)

### Kiểm tra metadata

- [ ] Tên file theo naming convention
- [ ] Có đủ thông tin title, type, year
- [ ] Author/department chính xác

---

## 🔄 Upload Process

### Step 1: Chuẩn bị batch

```bash
# Tạo folder theo loại
mkdir -p upload_batch/thesis
mkdir -p upload_batch/handbook
mkdir -p upload_batch/curriculum
mkdir -p upload_batch/papers

# Copy files vào đúng folder
cp *.pdf upload_batch/thesis/
```

### Step 2: Validate files

```python
# Script kiểm tra files
import os
from PyPDF2 import PdfReader

def validate_pdf(filepath):
    try:
        reader = PdfReader(filepath)
        pages = len(reader.pages)
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        
        return {
            "valid": True,
            "pages": pages,
            "size_mb": round(size_mb, 2)
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}
```

### Step 3: Upload via Admin Dashboard

1. Login với admin account
2. Truy cập Admin Dashboard
3. Drag & drop files (max 10 files/batch)
4. Monitor processing status
5. Verify EMBEDDING_DONE status

### Step 4: Verify indexing

```bash
# Test query để verify
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Tìm luận văn vừa upload"}'
```

---

## ⚠️ Common Issues & Solutions

### Issue 1: OCR Quality thấp

**Triệu chứng:** Text extracted bị sai nhiều
**Nguyên nhân:** Scan quality thấp, hình nghiêng
**Giải pháp:**
- Re-scan với 300+ DPI
- Sử dụng auto-deskew
- Tăng contrast

### Issue 2: File quá lớn

**Triệu chứng:** Upload timeout hoặc processing chậm
**Nguyên nhân:** File > 50MB hoặc > 500 pages
**Giải pháp:**
- Compress PDF
- Split thành multiple files
- Remove unnecessary images

### Issue 3: Encoding issues

**Triệu chứng:** Ký tự lạ trong extracted text
**Nguyên nhân:** Font không embed, encoding sai
**Giải pháp:**
- Re-export PDF với fonts embedded
- Convert to PDF/A format

### Issue 4: Tables không extract đúng

**Triệu chứng:** Bảng biểu bị vỡ layout
**Nguyên nhân:** Complex table structure hoặc merged cells
**Giải pháp:**
- Textract Table Extraction sẽ tự động detect và extract tables
- Textract AnalyzeDocument API với `FeatureTypes=["TABLES"]` sẽ:
  - Nhận diện cấu trúc row/column
  - Preserve cell relationships
  - Handle merged cells
  - Extract header rows
- Verify với `is_table: true` flag trong metadata
- Nếu table quá phức tạp, consider simplify layout trước khi upload

---

## 📊 Quality Metrics

### Document Quality Score

| Metric | Weight | Criteria |
|--------|--------|----------|
| Text Extractability | 30% | % text có thể extract |
| OCR Confidence | 25% | Textract confidence score |
| Metadata Completeness | 20% | Required fields filled |
| File Quality | 15% | Size, pages, format |
| Content Relevance | 10% | Academic value |

### Target Metrics

| Metric | Target |
|--------|--------|
| Average extraction rate | > 95% |
| OCR confidence | > 85% |
| Metadata completeness | 100% required, 80% recommended |
| Processing success rate | > 98% |

---

## 📅 Upload Schedule Recommendation

### Initial Load (Week 1-2)

| Day | Task | Volume |
|-----|------|--------|
| 1-2 | Student Handbooks | 20 files |
| 3-4 | Curriculum Documents | 30 files |
| 5-7 | Thesis batch 1 | 100 files |
| 8-10 | Thesis batch 2 | 100 files |
| 11-14 | Research Papers | 200 files |

### Ongoing Maintenance

- Weekly: New thesis uploads (5-10 files)
- Monthly: Updated handbooks/curriculum
- Quarterly: Research paper batches

---

## 🔐 Security Considerations

### Sensitive Data

**KHÔNG upload:**
- Thông tin cá nhân sinh viên (CMND, địa chỉ, SĐT)
- Điểm số cá nhân
- Thông tin tài chính
- Tài liệu mật/nội bộ chưa được phép công khai

### Access Control

- Chỉ admin mới có quyền upload
- Documents được encrypt at rest (S3 SSE)
- Access logs được ghi nhận

---

*Last Updated: December 2024*
