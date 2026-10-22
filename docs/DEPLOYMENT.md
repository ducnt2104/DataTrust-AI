# DataTrust AI — Deployment & Execution Guide

## 1. Yêu Cầu Môi Trường (System Prerequisites)
- Node.js >= 18 (Đã kiểm tra hoạt động trên Node v26.7.0).
- Python >= 3.10 (Đã kiểm tra hoạt động trên Python 3.15).
- SQLite 3 có hỗ trợ WAL mode.
- Git.

## 2. Cài Đặt Phụ Thuộc (Dependencies Installation)

### Backend:
```powershell
cd backend
pip install -r requirements.txt
```

### Frontend:
```powershell
cd frontend
npm install
```

## 3. Cấu Hình Biến Môi Trường (Environment Variables)

Tạo file `.env` tại thư mục gốc hoặc `backend/.env`:
```env
PORT=8000
DATABASE_URL=sqlite:///./datatrust.db
PUBLIC_BASE_URL=http://localhost:5173
# Cấu hình AI tuỳ chọn (khi để trống, hệ thống sử dụng Fallback Deterministic NLP Engine)
GEMINI_API_KEY=
```

## 4. Khởi Chạy Ứng Dụng (Running Services)

### Chạy Backend API (Cổng 8000):
```powershell
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Chạy Frontend Client (Cổng 5173):
```powershell
cd frontend
npm run dev
```

Truy cập:
- Trình quản trị khảo sát & Dashboard: `http://localhost:5173/`
- Khảo sát công khai mẫu: `http://localhost:5173/s/{public_slug}`
- Swagger API Docs: `http://localhost:8000/docs`
