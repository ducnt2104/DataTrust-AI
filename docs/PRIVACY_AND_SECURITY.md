# DataTrust AI — Chính Sách Quyền Riêng Tư & An Toàn Dữ Liệu
## Tuân Thủ Nghị Định 356/2025/NĐ-CP & Luật Bảo Vệ Dữ Liệu Cá Nhân

**Tài liệu mã số:** `DT-SEC-2026-V1`  
**Cập nhật lần cuối:** 2026-10-23  
**Phạm vi áp dụng:** Nền tảng DataTrust AI (Khảo sát số hoá trực tuyến, Số hoá phiếu giấy OMR và Động cơ Kiểm định Chất lượng Dữ liệu).

---

## 1. Giới Thiệu & Căn Cứ Pháp Lý

DataTrust AI được thiết kế tuân thủ nghiêm ngặt các tiêu chuẩn an toàn thông tin và quyền riêng tư theo pháp luật Việt Nam và các hướng dẫn học thuật quốc tế:
1. **Nghị định 356/2025/NĐ-CP** quy định chi tiết một số điều của Luật Bảo vệ dữ liệu cá nhân.
2. **Luật Bảo vệ Dữ liệu Cá nhân 2025** (Personal Data Protection Law).
3. **Quy chế Nghiên cứu Khoa học & Đạo đức Dữ liệu** trong khảo sát xã hội học và giáo dục.

Mục tiêu cốt lõi: Bảo vệ quyền riêng tư của người tham gia khảo sát, ngăn ngừa rò rỉ dữ liệu nhạy cảm (PII), đồng thời bảo đảm tính toàn vẹn, xác thực và minh bạch của bộ dữ liệu phục vụ nghiên cứu khoa học.

---

## 2. 4 Nguyên Tắc Cốt Lõi Về Quyền Riêng Tư (Decree 356 Compliance)

### 2.1. Tối Thiểu Hóa Dữ Liệu (Data Minimization)
- Hệ thống chỉ thu thập các trường dữ liệu cần thiết phục vụ trực tiếp cho mục đích nghiên cứu đã công bố.
- Khảo sát mặc định **không thu thập** số CMND/CCCD, số điện thoại, địa chỉ nhà riêng hoặc tài khoản ngân hàng trừ khi đề tài có phê duyệt đạo đức nghiên cứu đặc biệt.
- Thông tin thiết bị (`client_metadata`) chỉ ghi nhận các thông số kỹ thuật tối thiểu (User-Agent rút gọn, độ phân giải màn hình, hệ điều hành) để phục vụ kiểm định chất lượng phản hồi (phát hiện bot/spam), không lấy vị trí GPS chính xác của người dùng.

### 2.2. Ẩn Danh Hóa & Phân Tách Danh Tính (Pseudonymization & Tokenization)
- Mọi phản hồi (`responses`) được gán định danh ngẫu nhiên chuẩn quốc tế **UUID v4** (ví dụ `c6b9e28f-7c1a-4d29-a80b-920db5df03a3`), hoàn toàn không liên kết với thông tin định danh cá nhân trực tiếp.
- Khóa chính định danh người tham gia không bao giờ được lưu trữ chung với câu trả lời khảo sát.
- Khi xuất dữ liệu (`Export Center`), hệ thống tự động loại bỏ mọi metadata kỹ thuật nhận dạng cá nhân trong các tệp xuất cho mục đích công bố mở (Clean Dataset).

### 2.3. Mã Hóa Đường Truyền & Lưu Trữ An Toàn (Encryption in Transit & at Rest)
- **Đường truyền (In Transit):** 100% kết nối giữa Trình duyệt và Máy chủ bắt buộc thông qua giao thức HTTPS bảo mật với chuẩn TLS 1.3, mã hóa AES-256-GCM.
- **Lưu trữ (At Rest):** Cơ sở dữ liệu SQLite được bảo vệ bằng phân quyền hệ điều hành cấp file (`chmod 600`), chạy ở chế độ ghi nhật ký Write-Ahead Logging (WAL) với kiểm tra toàn vẹn định kỳ.
- **Chống tấn công & Gian lận:**
  - **Rate Limiting:** Giới hạn 40 yêu cầu/phút trên mỗi IP để ngăn chặn tấn công DoS, vét cạn hoặc gửi phiếu tự động hàng loạt.
  - **Idempotency Guard:** Tự động phát hiện và chặn ghi nhận 2 lần khi người dùng vô tình click đúp nút "Nộp phiếu" trong vòng 3 giây.
  - **SQL Injection Prevention:** 100% câu truy vấn được tham số hóa (Parameterized Queries) thông qua Pydantic v2 và SQLite driver, loại trừ hoàn toàn nguy cơ SQL Injection.

### 2.4. Quyền Yêu Cầu Xóa / Ẩn Danh Dữ Liệu (Right to Erasure / Anonymization)
- Đáp ứng Điều 14 & Điều 17 Nghị định 356/2025/NĐ-CP về quyền rút lại sự đồng ý và quyền yêu cầu xóa dữ liệu của chủ thể dữ liệu:
- Cung cấp API chuyên dụng:
  ```http
  POST /api/surveys/{survey_id}/privacy/anonymize
  ```
- Khi được kích hoạt, hệ thống:
  1. Xóa sạch `client_metadata_json` (chuyển thành `{"anonymized": true}`).
  2. Xóa thông tin điều tra viên cá nhân (`enumerator_id = NULL`).
  3. Ghi vết lịch sử kiểm toán bất biến (Audit Trail) phục vụ công tác thanh tra mà không vi phạm nguyên tắc bảo vệ danh tính.

---

## 3. Không Chia Sẻ Dữ Liệu Thô Với Bên Thứ Ba (Zero Third-Party Raw PII Transmission)

- Phân hệ Hỗ trợ AI (`AIAssistant`) của DataTrust AI được thiết kế với cơ chế ưu tiên:
  1. Sử dụng **Deterministic Local NLP Engine** chạy trực tiếp trên máy chủ nội bộ để phân tích ngữ nghĩa, thống kê từ khóa và phát hiện văn bản lặp lại mà không gửi bất kỳ dữ liệu nào ra bên ngoài internet.
  2. Trong trường hợp kích hoạt mô hình ngôn ngữ lớn (LLM API) thông qua Gemini/OpenAI, hệ thống chủ động lọc bỏ mọi chuỗi ký tự có định dạng email, số điện thoại hoặc tên riêng trước khi gửi yêu cầu phân tích.

---

## 4. Bằng Chứng Mật Mã Học Chống Giả Mạo (Tamper-Evident SHA-256 Digest)

Nhằm đảm bảo bộ dữ liệu nghiên cứu không bị chỉnh sửa trái phép sau khi thu thập:
- Phân hệ Báo cáo Kiểm toán Chất lượng (`/api/surveys/{id}/audit/report`) tính toán mã băm mật mã học **SHA-256**:
  $$\text{Audit Digest} = \text{SHA256}(\text{SurveyID} + \text{ResponsesCount} + \text{ValidCount} + \text{FraudCount} + \text{Timestamps})$$
- Bất kỳ hành vi thêm, xóa, sửa bản ghi nào trong cơ sở dữ liệu sẽ lập tức làm thay đổi mã SHA-256, giúp hội đồng khoa học và cơ quan quản lý dễ dàng phát hiện dữ liệu bị can thiệp.

---

## 5. Hướng Dẫn Vận Hành An Toàn Dành Cho Quản Trị Viên

1. **Bảo vệ file CSDL:** Định kỳ sao lưu file `datatrust.db` vào thư mục an toàn và mã hóa bản sao lưu.
2. **Quản lý biến môi trường:** Lưu trữ các khóa API trong file `.env`, không commit `.env` vào kho lưu trữ Git công khai.
3. **Thu hồi quyền truy cập:** Khi khảo sát kết thúc giai đoạn thu thập dữ liệu, quản trị viên nên chuyển trạng thái khảo sát sang `closed` để đóng cổng nhận phản hồi công khai.
4. **Cung cấp Báo cáo Kiểm toán:** Khi công bố kết quả nghiên cứu khoa học, đính kèm `Quality Audit Report` và mã băm SHA-256 để minh chứng tính minh bạch và độ tin cậy của dữ liệu.
