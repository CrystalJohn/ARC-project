# Sample Queries - Academic Research Chatbot

## Mục đích

Document này cung cấp các câu hỏi mẫu để test hệ thống RAG chatbot, đảm bảo chatbot hoạt động đúng với các loại queries khác nhau.

---

## 🎓 Category 1: Thesis & Research Queries

### Basic Queries
```
1. "Liệt kê các luận văn về machine learning"
2. "Ai là tác giả của luận văn về deep learning?"
3. "Có bao nhiêu đề tài nghiên cứu về NLP?"
4. "Tìm luận văn của sinh viên khoa CNTT năm 2024"
```

### Detailed Queries
```
5. "Tóm tắt phương pháp nghiên cứu trong luận văn 'Ứng dụng CNN trong nhận dạng hình ảnh'"
6. "Kết quả đạt được trong đề tài về sentiment analysis là gì?"
7. "Dataset nào được sử dụng trong các nghiên cứu về object detection?"
8. "So sánh accuracy của các mô hình trong luận văn về image classification"
```

### Cross-reference Queries
```
9. "So sánh phương pháp của 3 luận văn gần nhất về NLP"
10. "Những hạn chế chung được đề cập trong các nghiên cứu về chatbot"
11. "Xu hướng nghiên cứu AI trong 2 năm gần đây tại trường"
12. "Giảng viên nào hướng dẫn nhiều đề tài về data science nhất?"
```

### Expected Behavior
- ✅ Trả về kết quả với citations [1], [2], [3]...
- ✅ Mỗi citation link đến document gốc
- ✅ Hiển thị relevance score
- ✅ Tóm tắt nội dung chính xác từ documents

---

## 📖 Category 2: Student Handbook Queries

### Quy định học tập
```
1. "Điều kiện để được bảo vệ luận văn thạc sĩ là gì?"
2. "Số tín chỉ tối thiểu để tốt nghiệp đại học?"
3. "Quy định về điểm danh và nghỉ học"
4. "Thời gian tối đa để hoàn thành chương trình thạc sĩ"
```

### Quy trình thủ tục
```
5. "Quy trình xin gia hạn thời gian học như thế nào?"
6. "Thủ tục đăng ký đề tài nghiên cứu cần những gì?"
7. "Cách thức nộp đơn xin học bổng"
8. "Quy trình khiếu nại điểm thi"
```

### Chính sách
```
9. "Chính sách về đạo văn của trường quy định ra sao?"
10. "Quy định về sử dụng AI trong bài tập và luận văn"
11. "Chính sách hoàn học phí khi nghỉ học"
12. "Quy định về bảo mật thông tin sinh viên"
```

### Expected Behavior
- ✅ Trích dẫn chính xác điều khoản, số trang
- ✅ Format: "Theo Điều X, Quy chế Y [1]..."
- ✅ Cung cấp thông tin đầy đủ, không bỏ sót

---

## 📊 Category 3: Curriculum & GPA Queries

### Chương trình đào tạo
```
1. "Chương trình đào tạo ngành CNTT có những môn bắt buộc nào?"
2. "Danh sách môn tự chọn cho chuyên ngành AI"
3. "Môn tiên quyết của Machine Learning là gì?"
4. "Lộ trình học 4 năm ngành Khoa học dữ liệu"
```

### Điểm số & GPA
```
5. "Cách tính GPA theo hệ 4 của trường như thế nào?"
6. "Quy đổi điểm chữ sang điểm số"
7. "Điểm tối thiểu để đạt môn học là bao nhiêu?"
8. "Cách tính điểm trung bình tích lũy"
```

### Tín chỉ
```
9. "1 tín chỉ tương đương bao nhiêu giờ học?"
10. "Số tín chỉ tối đa được đăng ký mỗi học kỳ"
11. "Quy định về học vượt và học cải thiện"
12. "Tín chỉ thực tập tốt nghiệp được tính như thế nào?"
```

### Expected Behavior
- ✅ Hiển thị bảng biểu khi có (GPA conversion, curriculum)
- ✅ Trích dẫn đúng document nguồn
- ✅ Thông tin chính xác về số liệu

---

## 🔬 Category 4: Academic Paper Analysis

### Summary Queries
```
1. "Tóm tắt paper 'Attention is All You Need'"
2. "Abstract của nghiên cứu về BERT"
3. "Kết luận chính của paper về GPT-3"
```

### Methodology Queries
```
4. "Phương pháp nghiên cứu trong paper về ResNet là gì?"
5. "Architecture của mô hình trong paper về YOLO"
6. "Training process được mô tả như thế nào trong paper X?"
```

### Comparison Queries
```
7. "So sánh BERT và GPT về architecture"
8. "Điểm khác biệt giữa CNN và Transformer trong NLP"
9. "Performance comparison của các object detection models"
```

### Expected Behavior
- ✅ Tổng hợp từ nhiều sources
- ✅ Multiple citations khi so sánh
- ✅ Giữ nguyên technical terms

---

## 🔄 Category 5: Conversation Context Queries

### Multi-turn Conversation
```
Turn 1: "Các phương pháp machine learning phổ biến là gì?"
Turn 2: "Phương pháp đầu tiên được áp dụng như thế nào?"
Turn 3: "Cho ví dụ cụ thể về nó"
Turn 4: "So sánh với phương pháp thứ hai"
```

### Follow-up Questions
```
Turn 1: "Luận văn của Nguyễn Văn A về chủ đề gì?"
Turn 2: "Kết quả đạt được là gì?"
Turn 3: "Hạn chế của nghiên cứu này?"
Turn 4: "Có đề xuất hướng phát triển không?"
```

### Expected Behavior
- ✅ Hiểu context từ câu trước
- ✅ Resolve pronouns (nó, phương pháp đó, nghiên cứu này)
- ✅ Maintain conversation flow

---

## ⚠️ Category 6: Edge Cases & Error Handling

### Out of Scope Queries
```
1. "Thời tiết hôm nay thế nào?"
   Expected: "Tôi là chatbot hỗ trợ tra cứu tài liệu học thuật..."

2. "Viết code Python cho tôi"
   Expected: "Tôi có thể giúp bạn tìm tài liệu về Python..."

3. "Cho tôi số điện thoại của giảng viên X"
   Expected: "Tôi không có thông tin liên hệ cá nhân..."
```

### No Results Queries
```
4. "Nghiên cứu về quantum computing ở trường"
   Expected: "Tôi không tìm thấy tài liệu về quantum computing..."

5. "Luận văn năm 2030"
   Expected: "Không có tài liệu nào từ năm 2030..."
```

### Ambiguous Queries
```
6. "Cho tôi thông tin về AI"
   Expected: Hỏi clarification hoặc trả về overview với multiple citations

7. "Điểm"
   Expected: "Bạn muốn hỏi về điểm GPA, điểm thi, hay quy định về điểm?"
```

### Outdated Information
```
8. "Học phí năm 2025"
   Expected: "Theo tài liệu mới nhất (2024), học phí là... Vui lòng kiểm tra với phòng đào tạo."
```

---

## 📝 Category 7: Citation Verification Queries

### Single Citation
```
Query: "Định nghĩa machine learning theo tài liệu của trường"
Expected: Answer với [1] link đến đúng document, đúng page
```

### Multiple Citations
```
Query: "So sánh 3 phương pháp object detection"
Expected: Answer với [1][2][3] mỗi citation từ paper khác nhau
```

### Table Citation
```
Query: "Bảng quy đổi điểm GPA"
Expected: Citation với is_table: true, hiển thị bảng formatted
```

---

## 🧪 Test Checklist

### Functional Tests
- [ ] Basic query returns relevant results
- [ ] Citations are clickable and accurate
- [ ] Conversation context is maintained
- [ ] Error messages are user-friendly
- [ ] Tables are rendered correctly

### Performance Tests
- [ ] Response time < 5 seconds
- [ ] Handles concurrent users (10+)
- [ ] Large documents processed correctly

### Edge Case Tests
- [ ] Out of scope queries handled gracefully
- [ ] No results scenario works
- [ ] Ambiguous queries get clarification

### Citation Tests
- [ ] Single citation accuracy
- [ ] Multiple citations from different sources
- [ ] Page numbers are correct
- [ ] Document titles match

---

## 📊 Query Complexity Levels

| Level | Description | Example | Expected Time |
|-------|-------------|---------|---------------|
| Simple | Single fact lookup | "Điểm tối thiểu để đạt?" | < 2s |
| Medium | Summary/explanation | "Tóm tắt luận văn X" | < 4s |
| Complex | Cross-reference/comparison | "So sánh 5 papers về NLP" | < 6s |
| Conversation | Multi-turn with context | Follow-up questions | < 3s each |

---

*Last Updated: December 2024*
