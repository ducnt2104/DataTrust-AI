# DataTrust AI — Implementation Backlog (Updated)

Trạng thái:
- [x] **P0-1:** Khởi tạo cấu trúc dự án Frontend & Backend & Git & Tài liệu kiến trúc.
- [x] **P0-2:** Xây dựng Backend Database (SQLite với WAL mode) & Core Models & Migrations (`backend/app/database.py`).
- [x] **P0-3:** Xây dựng DataTrust Quality Engine (Hamming distance, straightlining, logic rules, timing, composite score: `backend/app/engine/quality_engine.py`).
- [x] **P0-4:** Xây dựng Surveys API (CRUD, Autosave, Publish flow, Closed status: `backend/app/routes/surveys.py`).
- [x] **P0-5:** Xây dựng Public Survey API (Lấy schema công khai, kiểm tra trạng thái, tiếp nhận nộp bài: `backend/app/routes/public.py`).
- [x] **P0-6:** Xây dựng Frontend Public Survey Page (`/s/:slug`) hỗ trợ đầy đủ 12 loại câu hỏi, logic rẽ nhánh và validation (`frontend/src/pages/PublicSurveyPage.tsx`).
- [x] **P0-7:** Xây dựng Frontend Survey Builder (Trình soạn thảo câu hỏi, phân loại, logic rẽ nhánh, xem trước, xuất bản, mã QR trực tiếp: `frontend/src/pages/SurveyBuilderPage.tsx`).
- [x] **P0-8:** Xây dựng Review Center (Danh sách phản hồi, chi tiết cảnh báo, đối chiếu 2 phản hồi side-by-side, ghi nhận quyết định xác minh: `frontend/src/pages/ResponsesListPage.tsx`, `ResponseDetailPage.tsx`, `ResponseComparePage.tsx`).
- [x] **P0-9:** Xây dựng Real Analytics Dashboard (Tính toán số liệu thực, biểu đồ từng câu hỏi, kiểm tra cỡ mẫu $N < 5$: `frontend/src/pages/SurveyAnalyticsPage.tsx`).
- [x] **P0-10:** Xây dựng Export & Import Center (Raw, Reviewed, Verified Clean CSV UTF-8 BOM / JSON: `frontend/src/pages/ExportImportPage.tsx`).
- [x] **P1-1:** Xây dựng AI Survey Assistant Adapter (Hỗ trợ gợi ý câu hỏi & kiểm định câu hỏi dẫn dắt/kép; cơ chế fallback thông minh: `backend/app/engine/ai_assistant.py`).
- [x] **P1-2:** Xây dựng CSV Import & Schema Mapping (`backend/app/routes/export_import.py`).
- [x] **P0-11:** Bộ kiểm thử tự động toàn diện TEST-01 đến TEST-12 đạt 100% tỷ lệ vượt qua và Báo cáo kiểm định `docs/TEST_RESULTS.md`.
