# DataTrust-AI

> **DataTrust** — Nền tảng Khảo sát Số, Xác thực & Kiểm định Chất lượng Dữ liệu Nghiên cứu Toàn diện  
> *(Digital Survey, Data Quality Verification & Advanced Econometric Analytics Platform)*

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_19_+_Vite-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📌 Giới thiệu Tổng quan (Overview)

**DataTrust** là nền tảng quản trị và kiểm định dữ liệu khảo sát số thế hệ mới, được thiết kế chuyên biệt cho các viện nghiên cứu, trường đại học, tổ chức phi chính phủ và doanh nghiệp yêu cầu chuẩn mực phương pháp luận khoa học khắt khe.

Hệ thống kết hợp giữa thu thập dữ liệu đa kênh (Web Form phản hồi thời gian thực, Khảo sát Ngoại tuyến PWA Offline-First, Quét phiếu giấy tự động OMR) với bộ động cơ kiểm định chất lượng dữ liệu độc quyền và hơn 119 phương pháp phân tích kinh tế lượng, đo lường tâm lý học (Psychometrics), suy diễn nhân quả (Causal Inference) chuyên sâu.

---

## ✨ Tính năng Cốt lõi (Key Capabilities)

### 1. Thu thập & Quản lý Khảo sát Đa kênh
- **12 Loại câu hỏi chuẩn hóa:** Likert scale, Ma trận nhiều chiều (Matrix/Grid), Xếp hạng ưu tiên (Ranking), Net Promoter Score (NPS), Phân bổ tổng điểm cố định (Constant Sum), Trắc nghiệm đơn/đa lựa chọn, Tải tệp an toàn, Câu hỏi mở kiểm duyệt tự động.
- **OMR Optical Mark Recognition:** Tự động tạo biểu mẫu phiếu trả lời trắc nghiệm dạng PDF vector, quét và nhận diện câu trả lời từ ảnh chụp phiếu giấy với độ chính xác cao.
- **Offline Sync & Caching:** Tương thích di động hoàn toàn, tiếp tục thu thập dữ liệu tại các địa bàn không có sóng viễn thông và tự động đồng bộ khi có mạng.
- **Phân luồng Logic & Kiểm soát Rào cản:** Skip logic, phân nhánh điều kiện nhiều cấp độ, giới hạn hạn ngạch (Sampling Quota) theo thời gian thực.

### 2. Bộ Động cơ Kiểm định Chất lượng Dữ liệu Toàn diện (Data Quality Engine)
- **Kiểm định Gian lận & Phân phối:** Định luật Benford bậc một/bậc hai (First & Second Digit Benford's Law), chỉ số đồng đều entropy, phân tích mô hình trả lời thẳng hàng (Straightlining detection).
- **Tốc độ Phản hồi Bất thường (Speeder & Outlier Detection):** Phát hiện đáp viên hoàn thành quá nhanh dựa trên phân phối log-normal thời gian đọc nhận thức (Cognitive pacing analysis).
- **Chỉ số Bẫy chú ý (Attention Check) & Độ tin cậy:** Tính toán điểm tín nhiệm mẫu (Data Trust Score), phân loại phản hồi rác, bot tự động hoặc gian lận có tổ chức.
- **Niêm phong Chuỗi Kiểm toán SHA-256:** Mỗi hành động phân tích, xuất dữ liệu hoặc phê duyệt phiếu đều được ghi nhận vào chuỗi sổ cái bất biến (Audit Ledger) phục vụ bảo vệ tính trung thực học thuật.

### 3. Phân tích Thống kê, Kinh tế lượng & Suy diễn Nhân quả Nâng cao
- **Đo lường & Tâm lý học:** Mô hình Rasch (1PL), Mô hình IRT 2PL/4PL, Đánh giá Sai lệch Chức năng Câu hỏi (DIF Analysis), Phân tích Nhân tố Khám phá (EFA), Khẳng định (CFA), Phân tích Bi-Factor, Bất biến Đo lường Đa nhóm (Measurement Invariance & MGSEM), Độ tin cậy thang đo (Cronbach's $\alpha$, McDonald's $\omega$).
- **Suy diễn Nhân quả Hiện đại (Modern Causal Inference):**
  - **Difference-in-Differences (DiD):** DiD truyền thống, DiD đa kỳ bất đồng bộ (Staggered DiD - Callaway & Sant'Anna 2021; Goodman-Bacon 2021), Synthetic Difference-in-Differences (SDID - Arkhangelsky et al. 2021).
  - **Regression Discontinuity Design (RDD):** RDD liên tục sắc nét/mờ, RDD ngẫu nhiên cục bộ cho biến chạy rời rạc (Local Randomization RDD - Cattaneo et al. 2015).
  - **Instrumental Variables:** Hồi quy 2SLS, Hồi quy phân vị biến công cụ (IV Quantile Regression - Chernozhukov & Hansen 2005).
  - **Doubly Robust & Machine Learning:** AIPW Doubly Robust Estimation, Targeted Maximum Likelihood Estimation (TMLE), Double/Debiased Machine Learning (DML - Chernozhukov et al. 2018), Causal Forest & Causal Trees (Athey & Wager).
  - **Interactive Fixed Effects & Panel Factor Models:** Mô hình yếu tố tiềm ẩn bảng điều khiển (Bai 2009 Econometrica).
  - **Sequential Mediation:** Phân rã tác động gián tiếp tuần hoàn qua nhiều biến trung gian (VanderWeele 2014; Steen et al. 2012).
  - **Policy Learning:** Học quy tắc phân bổ chính sách cá thể hóa tối ưu (Athey & Wager 2021).
- **Trực quan hóa Đồ họa Khoa học:** Hơn 100 biểu đồ SVG vector kép khoa học chuẩn mực với bảng tham số và thuyết minh học thuật tự động chuẩn **APA 7th Edition**.

---

## 🛠️ Kiến trúc Hệ thống & Ngăn xếp Công nghệ (Tech Stack)

```
DataTrust-AI/
├── backend/                  # RESTful API Backend (Python / FastAPI)
│   ├── app/
│   │   ├── engine/           # 40+ Động cơ thống kê, suy diễn nhân quả & chất lượng dữ liệu
│   │   ├── routes/           # FastAPI Endpoints (surveys, analytics, responses, paper, audit)
│   │   ├── middleware/       # Rate limiting, audit verification, security headers
│   │   ├── config.py         # Cấu hình môi trường & AI Service
│   │   ├── database.py       # SQLite / SQLAlchemy persistent store
│   │   └── schemas.py        # Pydantic Schemas cho toàn bộ 119+ API endpoints
│   └── tests/                # Bộ kiểm thử tự động toàn diện (pytest)
│
├── frontend/                 # Single Page Application (React 19 + TypeScript + Vite)
│   ├── src/
│   │   ├── api/client.ts     # Type-safe API Client tương thích 100% backend
│   │   ├── components/       # 60+ UI Cards phân tích & trực quan hóa khoa học
│   │   ├── pages/            # Dashboard, Survey Builder, Analytics, Paper OMR, Public Form
│   │   └── types/survey.ts   # TypeScript Interfaces & Contract definitions
│   └── index.html
│
└── docs/                     # Tài liệu kiến trúc, đặc tả API & nhật ký nghiên cứu
    ├── API_CONTRACT.md       # Đặc tả 119 hợp đồng API chi tiết
    ├── ARCHITECTURE.md       # Thiết kế kiến trúc tổng thể
    └── SECURITY_ASSESSMENT.md
```

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy (Getting Started)

### 1. Yêu cầu Tiên quyết
- **Python:** Phiên bản 3.11 trở lên
- **Node.js:** Phiên bản 18 trở lên (khuyên dùng Node 20+)
- **Git**

### 2. Khởi chạy Backend

```bash
# Di chuyển vào thư mục backend
cd backend

# Tạo và kích hoạt môi trường ảo (khuyến nghị)
python -m venv .venv
# Trên Windows:
.venv\Scripts\activate
# Trên macOS / Linux:
source .venv/bin/activate

# Cài đặt các gói phụ thuộc
pip install -r requirements.txt

# Khởi động máy chủ backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend sẽ khả dụng tại: `http://localhost:8000`  
Tài liệu Swagger API tương tác: `http://localhost:8000/docs`

### 3. Khởi chạy Frontend

```bash
# Mở một terminal mới và di chuyển vào frontend
cd frontend

# Cài đặt dependencies
npm install

# Khởi chạy máy chủ phát triển
npm run dev
```

Giao diện người dùng sẽ chạy tại: `http://localhost:5173`

---

## 🧪 Kiểm thử Tự động (Testing)

Hệ thống được trang bị bộ kiểm thử tự động toàn diện đảm bảo độ ổn định và tính đúng đắn toán học:

```bash
# Chạy toàn bộ backend unit & integration tests
pytest

# Kiểm tra cú pháp và build production frontend
npm --prefix frontend run build
```

---

## 📄 Bản quyền (License)

Dự án được phân phối dưới giấy phép [MIT License](LICENSE).
