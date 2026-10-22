# DataTrust AI — Test Plan (TEST-01 to TEST-12)

Kế hoạch kiểm thử bao phủ toàn bộ 12 ca kiểm thử theo yêu cầu nghiệm thu:

| Mã Kiểm Thử | Tên Bài Kiểm Thử | Mục Tiêu & Tiêu Chí Nghiệm Thu | Phương Pháp |
|---|---|---|---|
| **TEST-01** | Tạo & Lưu Khảo Sát | Tạo khảo sát mới qua API/UI, thêm các loại câu hỏi, lưu và tải lại không mất dữ liệu. | Tự động hóa API + Unit Test |
| **TEST-02** | Validation & Logic Rẽ Nhánh | Ràng buộc trường bắt buộc, kiểm tra kiểu dữ liệu và thực thi logic ẩn hiện câu hỏi. | Unit Test + Client Validation |
| **TEST-03** | Xuất Bản & Sinh Link Thực | Khảo sát chuyển sang trạng thái `published`, sinh link `/s/:slug` và mã QR hoạt động. Thử truy cập bản `draft` bị chặn. | API Test + Route Verification |
| **TEST-04** | Gửi Phản Hồi Thật | Mở public survey, điền câu trả lời hợp lệ, submit thành công, kiểm tra dữ liệu ghi vào database với đúng `survey_id` và `question_id`. | End-to-End API Test |
| **TEST-05** | Xử Lý Lỗi Mạng & Khảo Sát Đóng | Thử gửi khi khảo sát đã đóng (`closed`) hoặc sai schema, xác nhận hệ thống báo lỗi chính xác, không ghi nhận giả. | Negative Test Case |
| **TEST-06** | Quality Engine & Heuristic Risk | Chạy fixture kiểm thử phát hiện: trùng lặp hoàn toàn, gần trùng lặp, straightlining, mâu thuẫn logic, làm bài quá nhanh. | Pytest Automated Test Suite |
| **TEST-07** | Review Center & Đối Chiếu | Mở chi tiết phản hồi, xem cờ cảnh báo, đối chiếu 2 phản hồi gần trùng side-by-side, cập nhật quyết định xác minh (`verified_valid`, `verified_fraud`). | Integration Test |
| **TEST-08** | Real Analytics Dashboard | Dashboard tính toán trực tiếp từ DB thực tế, không dùng số liệu hardcode. Hiển thị thông báo khi $N < 5$. | Integration Test |
| **TEST-09** | Xuất Dữ Liệu Thực (Export) | Xuất CSV/JSON theo 3 phạm vi: Raw, Reviewed, Verified Clean. Kiểm tra mã hóa UTF-8 tiếng Việt và ánh xạ cột chính xác. | Export Verification Test |
| **TEST-10** | Giao Diện Responsive & Empty State | Kiểm tra layout trên Desktop, Mobile, Tablet; hiển thị Empty State khi chưa có dữ liệu. | UI Build & Component Check |
| **TEST-11** | Bảo Mật & Phân Quyền | Ngăn chặn truy cập bản nháp qua link công khai; kiểm tra chống SQL Injection / XSS. | Security Audit Test |
| **TEST-12** | Đánh Giá Toàn Hành Trình (E2E) | **Tạo khảo sát -> Lưu -> Xuất bản -> Lấy link -> Gửi phản hồi -> Phân tích chất lượng -> Rà soát -> Xác minh -> Xuất bộ dữ liệu sạch.** | Full E2E Journey Runner |
