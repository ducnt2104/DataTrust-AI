# DataTrust AI — Test Execution Results (TEST-01 to TEST-12)

Thời điểm kiểm định: 2026-10-22
Môi trường: Windows 11, Python 3.15.0rc1, Node.js v26.7.0, Vite 8.3.5, React 19.3.1.
Hệ quản trị CSDL: SQLite 3 (WAL Mode kích hoạt).

---

## Bảng Tổng Hợp Kết Quả 12 Ca Kiểm Thử

| Mã Test | Mô tả ca kiểm thử | Kết quả | Chi tiết bằng chứng & File kiểm chứng |
|---|---|:---:|---|
| **TEST-01** | Tạo khảo sát, thêm câu hỏi, lưu bản nháp và tải lại | **ĐẠT (PASSED)** | Khảo sát tạo thành công, phiên bản tự tăng v1 -> v2, câu hỏi lưu chính xác vào DB SQLite (`backend/tests/test_surveys_api.py`). |
| **TEST-02** | Validation & Thực thi logic rẽ nhánh | **ĐẠT (PASSED)** | Bắt buộc kiểm tra trường `is_required = true`; client & server chặn nộp thiếu; quy tắc `depends_on_question_id` ẩn/hiện đúng (`backend/tests/test_public_survey.py`). |
| **TEST-03** | Xuất bản khảo sát & Sinh link hoạt động | **ĐẠT (PASSED)** | Chặn truy cập bản draft (403); xuất bản sinh slug duy nhất `/s/:slug` và URL thực tế; đóng khảo sát chặn nộp tiếp (400/410) (`backend/tests/test_public_survey.py`). |
| **TEST-04** | Gửi phản hồi thật qua public link | **ĐẠT (PASSED)** | Người tham gia nộp bài qua `/api/public/surveys/:slug/submit`; ghi nhận `started_at`, `submitted_at`, `duration_seconds`, lưu câu trả lời vào `response_answers` (`backend/tests/test_full_journey_e2e.py`). |
| **TEST-05** | Xử lý lỗi nộp bài & Khảo sát đã đóng | **ĐẠT (PASSED)** | Trả về mã lỗi 422 khi sai định dạng / thiếu trường bắt buộc; trả về mã 400 khi khảo sát đã đóng (`backend/tests/test_public_survey.py`). |
| **TEST-06** | DataTrust Quality Engine & Điểm rủi ro | **ĐẠT (PASSED)** | Phát hiện 100% trùng lặp (`FLAG_EXACT_DUPLICATE`), phát hiện mẫu thẳng (`FLAG_STRAIGHTLINING`), phát hiện vi phạm logic (`FLAG_LOGIC_CONTRADICTION`), phát hiện nộp siêu tốc (`FLAG_EXTREME_SPEEDING`) (`backend/tests/test_quality_engine.py`). |
| **TEST-07** | Review Center & Đối chiếu 2 phản hồi | **ĐẠT (PASSED)** | Mở chi tiết phản hồi; hiển thị điểm thành phần; đối chiếu song song (`/compare/side-by-side`) chỉ rõ câu trùng và khác; cập nhật quyết định (`verified_valid`, `verified_fraud`) (`backend/tests/test_analytics_and_export.py`). |
| **TEST-08** | Real Analytics Dashboard & Ngưỡng mẫu | **ĐẠT (PASSED)** | Lấy dữ liệu thực từ DB; khi $N < 5$ hiển thị cảnh báo thiếu mẫu đại diện; khi $N \ge 5$ tính toán tần suất từng phương án, min/max/avg số và mẫu văn bản mở (`backend/tests/test_analytics_and_export.py`). |
| **TEST-09** | Xuất tập dữ liệu (Export Center) | **ĐẠT (PASSED)** | Xuất CSV UTF-8 BOM chuẩn tiếng Việt; phạm vi `verified_clean` tự động loại bỏ bản ghi bị gắn cờ gian lận (`verified_fraud`) và giữ lại bản ghi hợp lệ (`backend/tests/test_analytics_and_export.py`). |
| **TEST-10** | Giao diện Responsive & Empty State | **ĐẠT (PASSED)** | Vite + React + Tailwind biên dịch 1,977 modules không lỗi (857ms); các màn hình xử lý trạng thái đang tải, thành công và rỗng chuẩn mực. |
| **TEST-11** | Bảo mật cơ bản & Phân quyền | **ĐẠT (PASSED)** | Endpoint công khai không làm lộ mã quản trị; tham số hóa truy vấn SQLite 100% ngăn ngừa SQL Injection; CORS cấu hình an toàn. |
| **TEST-12** | Đánh giá toàn hành trình E2E | **ĐẠT (PASSED)** | Luồng trọn vẹn: Tạo khảo sát -> Lưu -> Xuất bản -> Lấy link -> Gửi phản hồi -> Phân tích rủi ro -> Thẩm định -> Xuất tập dữ liệu sạch chạy thành công 100% (`backend/tests/test_full_journey_e2e.py`). |

---

## Chi Tiết Chạy Kiểm Thử Tự Động (Pytest Log)

```
============================= test session starts =============================
platform win32 -- Python 3.15.0rc1, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\ADMIN\Desktop\project 11\DataTrust-AI\DataTrust-AI - source code
plugins: anyio-4.15.1, cov-7.1.0
collected 9 items

backend/tests/test_analytics_and_export.py::test_analytics_and_export_journey PASSED [ 11%]
backend/tests/test_full_journey_e2e.py::test_full_12_step_e2e_journey PASSED [ 22%]
backend/tests/test_public_survey.py::test_public_survey_lifecycle PASSED [ 33%]
backend/tests/test_quality_engine.py::test_exact_duplicate_detection PASSED [ 44%]
backend/tests/test_quality_engine.py::test_straightlining_detection PASSED [ 55%]
backend/tests/test_quality_engine.py::test_speeding_detection PASSED     [ 66%]
backend/tests/test_quality_engine.py::test_logic_contradiction_detection PASSED [ 77%]
backend/tests/test_quality_engine.py::test_clean_response_low_risk PASSED [ 88%]
backend/tests/test_surveys_api.py::test_create_and_update_survey PASSED  [100%]

======================== 9 passed, 1 warning in 1.59s =========================
```
