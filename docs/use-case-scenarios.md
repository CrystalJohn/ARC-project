# Use Case Scenarios - Academic Research Chatbot

## Tổng quan

Document này mô tả các kịch bản sử dụng cụ thể của Academic Research Chatbot, giúp team hiểu rõ cách hệ thống phục vụ 50 researchers trong việc tra cứu 750 academic papers.

---

## 🎯 Đối tượng sử dụng

### 1. Researchers (50 users)
- Sinh viên nghiên cứu
- Giảng viên
- Nghiên cứu sinh
- Staff học thuật

### 2. Admins (2-3 users)
- Quản trị viên thư viện
- IT support
- Content managers

---

## 📚 Kịch bản 1: Tra cứu Thesis/Project Repository

### Mô tả
Researcher muốn tìm hiểu về các đề tài nghiên cứu đã thực hiện trong trường để tham khảo cho luận văn của mình.

### Flow
```
1. Researcher đăng nhập → Chat interface
2. Hỏi: "Có những đề tài nào về machine learning đã được thực hiện trong 2 năm gần đây?"
3. System tìm kiếm trong thesis repository
4. Trả về danh sách đề tài với citations [1], [2], [3]...
5. Researcher click citation để xem chi tiết thesis
```

### Câu hỏi mẫu
- "Liệt kê các luận văn về deep learning trong khoa CNTT"
- "Ai là người hướng dẫn nhiều đề tài về NLP nhất?"
- "Tóm tắt phương pháp nghiên cứu trong luận văn của Nguyễn Văn A"
- "So sánh kết quả của các đề tài về image classification"

### Expected Output
```json
{
  "answer": "Trong 2 năm gần đây, có 15 đề tài về machine learning...[1][2][3]",
  "citations": [
    {"id": 1, "title": "Ứng dụng CNN trong nhận dạng...", "author": "Nguyễn A", "year": 2024},
    {"id": 2, "title": "Transfer Learning cho bài toán...", "author": "Trần B", "year": 2023}
  ]
}
```

---

## 📖 Kịch bản 2: Tra cứu Student Handbook

### Mô tả
Researcher cần tìm hiểu quy định, chính sách của trường liên quan đến học tập và nghiên cứu.

### Tài liệu nguồn
- `SO-TAY-SINH-VIEN-K18.pdf` - Sổ tay sinh viên khóa 18
- Các quy chế, quy định đào tạo khác

### Flow
```
1. Researcher đăng nhập
2. Hỏi về quy định cụ thể
3. System tìm trong student handbook documents
4. Textract extract text + tables từ PDF (Table Extraction)
5. Trả về thông tin chính xác với trích dẫn nguồn
```

### Câu hỏi mẫu (dựa trên Sổ tay Sinh viên K18)
- "Quy định về điểm danh và nghỉ học của sinh viên K18?"
- "Điều kiện để được xét học bổng là gì?"
- "Quy trình xin phúc khảo điểm thi như thế nào?"
- "Sinh viên cần đạt bao nhiêu tín chỉ để tốt nghiệp?"
- "Quy định về kỷ luật học tập của trường?"
- "Thời gian đăng ký môn học mỗi học kỳ?"
- "Cách tính điểm trung bình tích lũy (GPA)?"

### Expected Output
```json
{
  "answer": "Theo Sổ tay Sinh viên K18 [1], quy định về điểm danh:\n1. Sinh viên phải tham dự ít nhất 80% số tiết học...\n2. Nghỉ quá 20% sẽ bị cấm thi...",
  "citations": [
    {"id": 1, "title": "Sổ tay Sinh viên K18", "page": 12, "section": "Quy định học vụ"}
  ]
}
```

### Tables trong Sổ tay (Textract Table Extraction)
Textract sẽ tự động extract các bảng như:
- Bảng quy đổi điểm chữ → điểm số → GPA
- Bảng học phí theo ngành/khóa
- Bảng thời khóa biểu mẫu
- Bảng danh mục môn học

---

## 📊 Kịch bản 3: Tra cứu Curriculum & GPA Information

### Mô tả
Researcher cần thông tin về chương trình đào tạo, môn học, và cách tính điểm.

### Flow
```
1. Researcher đăng nhập
2. Hỏi về curriculum hoặc GPA
3. System tìm trong curriculum documents
4. Trả về thông tin với bảng biểu nếu có
```

### Câu hỏi mẫu
- "Chương trình đào tạo ngành CNTT có những môn bắt buộc nào?"
- "Cách tính GPA theo hệ 4 của trường như thế nào?"
- "Môn tiên quyết của Machine Learning là gì?"
- "Số tín chỉ tối thiểu để tốt nghiệp là bao nhiêu?"
- "Danh sách môn tự chọn cho chuyên ngành AI"

### Expected Output với Table
```json
{
  "answer": "Theo chương trình đào tạo [1], cách quy đổi điểm như sau:\n\n| Điểm chữ | Điểm số | Điểm hệ 4 |\n|----------|---------|----------|\n| A | 8.5-10 | 4.0 |\n| B+ | 8.0-8.4 | 3.5 |...",
  "citations": [
    {"id": 1, "title": "Chương trình đào tạo CNTT 2024", "page": 8, "is_table": true}
  ]
}
```

---

## 🔬 Kịch bản 4: Nghiên cứu chuyên sâu Academic Papers

### Mô tả
Researcher cần phân tích, so sánh, tổng hợp thông tin từ nhiều papers học thuật.

### Flow
```
1. Researcher đăng nhập
2. Đặt câu hỏi nghiên cứu phức tạp
3. System tìm kiếm cross-reference nhiều papers
4. Tổng hợp và trả về với multiple citations
```

### Câu hỏi mẫu
- "So sánh các phương pháp object detection trong các paper gần đây"
- "Tổng hợp các dataset được sử dụng trong nghiên cứu NLP tiếng Việt"
- "Những hạn chế chung của các nghiên cứu về sentiment analysis là gì?"
- "Xu hướng nghiên cứu về transformer models trong 3 năm qua"

### Expected Output
```json
{
  "answer": "Dựa trên phân tích 8 papers [1][2][3][4][5][6][7][8], các phương pháp object detection có thể chia thành 3 nhóm chính:\n\n1. **Two-stage detectors**: RCNN family [1][2]\n2. **One-stage detectors**: YOLO, SSD [3][4][5]\n3. **Transformer-based**: DETR [6][7][8]...",
  "citations": [
    {"id": 1, "title": "Faster R-CNN: Towards Real-Time...", "author": "Ren et al."},
    {"id": 2, "title": "Mask R-CNN", "author": "He et al."}
  ]
}
```

---

## 👨‍💼 Kịch bản 5: Admin Upload Documents

### Mô tả
Admin cần upload tài liệu mới vào hệ thống để researchers có thể tra cứu.

### Flow
```
1. Admin đăng nhập với role admin
2. Truy cập Admin Dashboard
3. Drag & drop PDF files
4. Monitor processing status
5. Verify documents đã indexed
```

### Các loại documents cần upload
| Loại | Ví dụ | Ưu tiên |
|------|-------|---------|
| Thesis/Dissertations | Luận văn thạc sĩ, tiến sĩ | Cao |
| Student Handbook | Quy chế, quy định | Cao |
| Curriculum | Chương trình đào tạo | Cao |
| Research Papers | Bài báo khoa học | Trung bình |
| Course Materials | Syllabus, lecture notes | Thấp |

### Status Flow
```
UPLOADED → IDP_RUNNING → EMBEDDING_DONE
                ↓
              FAILED (nếu lỗi)
```

---

## 🔄 Kịch bản 6: Conversation Context

### Mô tả
Researcher tiếp tục hội thoại với context từ câu hỏi trước.

### Flow
```
User: "Các đề tài về NLP có những phương pháp nào?"
Bot: "Có 3 phương pháp chính: [1] Rule-based, [2] Statistical, [3] Deep Learning..."

User: "Phương pháp thứ 3 được áp dụng như thế nào?"
Bot: "Deep Learning trong NLP [3] được áp dụng qua các bước: 1. Tokenization..."
     (System hiểu "phương pháp thứ 3" từ context trước)
```

### Lưu ý
- Giữ context trong 10 message pairs gần nhất
- Conversation ID được track trong DynamoDB
- User có thể xem lại chat history

---

## ⚠️ Edge Cases & Limitations

### 1. Không tìm thấy thông tin
```
User: "Nghiên cứu về quantum computing ở trường"
Bot: "Tôi không tìm thấy tài liệu nào về quantum computing trong cơ sở dữ liệu hiện tại. 
      Có thể chủ đề này chưa được upload hoặc không có trong phạm vi tài liệu của trường."
```

### 2. Câu hỏi ngoài phạm vi
```
User: "Thời tiết hôm nay thế nào?"
Bot: "Tôi là chatbot hỗ trợ tra cứu tài liệu học thuật. 
      Tôi có thể giúp bạn tìm thông tin về thesis, quy định, chương trình đào tạo..."
```

### 3. Thông tin cần cập nhật
```
User: "Học phí năm 2025 là bao nhiêu?"
Bot: "Theo tài liệu mới nhất tôi có (2024) [1], học phí là X triệu/năm. 
      Vui lòng kiểm tra với phòng đào tạo để có thông tin cập nhật nhất."
```

---

## 📈 Success Metrics

| Metric | Target | Đo lường |
|--------|--------|----------|
| Query Response Time | < 5 seconds | CloudWatch |
| Citation Accuracy | > 90% | Manual review |
| User Satisfaction | > 4/5 stars | Feedback form |
| Document Coverage | 750 papers | Admin dashboard |
| Daily Active Users | 20-30 | Analytics |

---

*Last Updated: December 2024*
