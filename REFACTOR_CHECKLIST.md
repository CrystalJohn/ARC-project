# Frontend Refactor Checklist

## ✅ CÓ - Upload via UI đã hoạt động!

## 🔒 API Contracts - KHÔNG ĐƯỢC THAY ĐỔI

### Upload API
```javascript
// Request
POST /api/admin/upload?uploaded_by=username
FormData: { file: File }
Headers: { 'Authorization': 'Bearer token' }

// Response
{ doc_id, filename, status, message }
```

### List API
```javascript
// Request
GET /api/admin/documents?page=1&page_size=20&status=uploaded

// Response
{ items[], total, page, page_size, has_more }
```

### Chat API
```javascript
// Request
POST /api/chat/query
{ query, history[], top_k, score_threshold, model, template, stream }

// Response
{ answer, citations[], usage, model, contexts_used, query }
```

## ⚠️ Critical Rules

1. **snake_case** - Tất cả field names: `uploaded_by`, `page_size`, `doc_id`, `top_k`
2. **FormData field** - PHẢI là `'file'` không phải `'document'`
3. **Authorization** - PHẢI là `Bearer ${token}`
4. **Endpoints** - Giữ nguyên URLs: `/api/admin/upload`, `/api/admin/documents`

## ✅ Có thể thay đổi

- Component structure
- State management
- Styling/UI
- Variable names (trong frontend)
- File organization

## 🧪 Quick Test

```javascript
// Test upload
const result = await adminService.uploadDocument(file)
console.assert(result.doc_id)

// Test list
const data = await adminService.listDocuments({ page: 1, pageSize: 20 })
console.assert(data.page_size === 20)
```
