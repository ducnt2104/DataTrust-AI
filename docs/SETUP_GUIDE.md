# DATATRUST — HƯỚNG DẪN CÀI ĐẶT & VẬN HÀNH HỆ THỐNG
**Mã tài liệu:** `DATATRUST-SETUP-2026-V1`  
**Dự án:** DataTrust  

---

## 1. Yêu Cầu Môi Trường (Prerequisites)

- **Python:** Phiên bản 3.10 trở lên (khuyến nghị Python 3.11 hoặc 3.12).
- **Node.js:** Phiên bản 18 trở lên (khuyến nghị Node.js 20 LTS) và trình quản lý gói `npm`.
- **Hệ điều hành:** Hỗ trợ đầy đủ Windows (PowerShell), macOS và Linux.

---

## 2. Thiết Lập Biến Môi Trường & Bảo Mật Khóa API

### 2.1. Cấu hình tệp `.env` an toàn
Tại thư mục gốc của dự án hoặc thư mục `backend/`:
1. Tạo một tệp `.env` mới dựa trên mẫu `.env.example`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Nội dung tệp `.env` mẫu:
   ```ini
   PORT=8000
   PUBLIC_BASE_URL=http://localhost:5173
   DATABASE_PATH=backend/data/datatrust.db

   # Cấu hình Google Gemini AI
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   AI_FALLBACK_MODEL=gemini-2.0-flash
   AI_REQUEST_TIMEOUT_SECONDS=45.0
   ```

### 2.2. Hướng dẫn lấy và cấu hình khóa Google Gemini API mới
> [!IMPORTANT]
> **Tuyệt đối KHÔNG chia sẻ khóa API mới vào cuộc hội thoại chat hay commit vào kho mã nguồn Git.**

1. Truy cập trang chính thức của Google AI Studio: [https://aistudio.google.com/](https://aistudio.google.com/).
2. Đăng nhập bằng tài khoản Google của bạn và nhấn **"Get API key"**.
3. Tạo một khóa API mới cho dự án.
4. Mở tệp `.env` trên máy tính cục bộ của bạn bằng trình soạn thảo (Notepad, VS Code, v.v.).
5. Dán khóa API vừa tạo vào dòng:
   ```ini
   GEMINI_API_KEY=AIzaSy...
   ```
6. Lưu tệp `.env`. Hệ thống sẽ tự động nhận diện khóa và kích hoạt mô hình Gemini 2.5 Flash trên header HTTPS bảo mật mà không để lộ khóa ra bên ngoài.
7. *Lưu ý:* Nếu bạn chưa cấu hình khóa API ngay, hệ thống sẽ tự động kích hoạt **Động cơ Hình mẫu Khoa học Cục bộ (Deterministic Archetype Engine)** hỗ trợ 100% tính năng mà không bị gián đoạn.

---

## 3. Khởi Chạy Dịch Vụ Backend (FastAPI)

1. Cài đặt các thư viện Python cần thiết:
   ```powershell
   cd backend
   pip install -r requirements.txt
   ```
2. Khởi chạy máy chủ phát triển (Development Server):
   ```powershell
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
3. Kiểm tra trạng thái máy chủ:
   - Swagger API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Health Check: [http://localhost:8000/api/health](http://localhost:8000/api/health)
   - AI Engine Status: [http://localhost:8000/api/ai/status](http://localhost:8000/api/ai/status)

---

## 4. Khởi Chạy Giao Diện Người Dùng (React SPA)

1. Mở một cửa sổ dòng lệnh mới và chuyển vào thư mục `frontend`:
   ```powershell
   cd frontend
   npm install
   ```
2. Khởi chạy máy chủ phát triển giao diện (Vite Dev Server):
   ```powershell
   npm run dev
   ```
3. Truy cập ứng dụng tại trình duyệt: [http://localhost:5173](http://localhost:5173)

---

## 5. Thực Thi Bộ Kiểm Thử Tự Động (Automated Testing)

### 5.1. Chạy toàn bộ 36 bài kiểm thử tự động Backend (Pytest):
```powershell
pytest
```
*Kết quả chuẩn mong đợi:* Toàn bộ 36 test suites đều vượt qua với tỷ lệ thành công 100%.

### 5.2. Chạy bộ kiểm chuẩn AI Survey Benchmark (10 ca kiểm thử):
```powershell
$env:PYTHONPATH="backend"; python -m app.engine.ai_benchmark
```
*Kết quả chuẩn mong đợi:* Tỷ lệ tuân thủ dạng câu hỏi 100%, tỷ lệ kháng tiêm lệnh độc hại 100%, thời gian xử lý trung bình dưới 15ms.

### 5.3. Kiểm tra đóng gói giao diện Production (TypeScript & Vite Build):
```powershell
cd frontend
npm run build
```
*Kết quả chuẩn mong đợi:* Build thành công với 0 lỗi TypeScript strict (0 errors).
