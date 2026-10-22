# DataTrust AI — API Contract Specification

Tất cả các API trả về định dạng JSON chuẩn. Mã lỗi HTTP tuân thủ nghiêm ngặt (200: OK, 201: Created, 400: Bad Request, 404: Not Found, 422: Validation Error, 500: Internal Server Error).

---

## 1. Surveys Management (Quản Trị Khảo Sát)

### `GET /api/surveys`
- **Mô tả:** Lấy danh sách khảo sát (hỗ trợ lọc theo `status`).
- **Response:** `200 OK`
  ```json
  [
    {
      "id": "uuid",
      "title": "Khảo sát nghiên cứu trải nghiệm số",
      "description": "Mô tả...",
      "status": "published",
      "public_slug": "trai-nghiem-so-2026",
      "version": 1,
      "questions_count": 8,
      "responses_count": 24,
      "created_at": "2026-10-22T06:00:00Z",
      "updated_at": "2026-10-22T06:15:00Z"
    }
  ]
  ```

### `POST /api/surveys`
- **Mô tả:** Tạo một khảo sát mới (mặc định trạng thái `draft`).
- **Request Body:**
  ```json
  {
    "title": "Khảo sát ý kiến người tiêu dùng",
    "description": "Thu thập đánh giá chất lượng sản phẩm",
    "instructions": "Vui lòng trả lời trung thực các câu hỏi dưới đây."
  }
  ```
- **Response:** `201 Created`

### `GET /api/surveys/:id`
- **Mô tả:** Lấy thông tin chi tiết một cuộc khảo sát, bao gồm danh sách câu hỏi và cấu hình logic.
- **Response:** `200 OK`

### `PUT /api/surveys/:id`
- **Mô tả:** Cập nhật thông tin khảo sát và danh sách câu hỏi (Autosave / Manual Save).
- **Request Body:**
  ```json
  {
    "title": "Tiêu đề mới",
    "description": "Mô tả mới",
    "instructions": "Hướng dẫn mới",
    "questions": [
      {
        "id": "q1-uuid",
        "order_index": 0,
        "question_type": "single_choice",
        "title": "Bạn bao nhiêu tuổi?",
        "description": "Chọn nhóm tuổi phù hợp",
        "is_required": true,
        "options": [
          {"id": "opt_1", "label": "Dưới 18"},
          {"id": "opt_2", "label": "18 - 35"},
          {"id": "opt_3", "label": "Trên 35"}
        ],
        "logic_rules": []
      }
    ]
  }
  ```
- **Response:** `200 OK`

### `POST /api/surveys/:id/publish`
- **Mô tả:** Kiểm tra tính hợp lệ và xuất bản khảo sát sang trạng thái `published`, sinh link công khai và mã QR.
- **Response:** `200 OK`
  ```json
  {
    "id": "uuid",
    "status": "published",
    "public_slug": "khao-sat-tieu-dung-x49b",
    "public_url": "/s/khao-sat-tieu-dung-x49b",
    "qr_code_data": "data:image/png;base64,...",
    "published_at": "2026-10-22T06:20:00Z"
  }
  ```

### `POST /api/surveys/:id/close`
- **Mô tả:** Đóng khảo sát, không nhận thêm câu trả lời từ link công khai.
- **Response:** `200 OK`

---

## 2. Public Survey (Khảo Sát Công Khai Cho Người Tham Gia)

### `GET /api/public/surveys/:slug_or_id`
- **Mô tả:** Tải schema khảo sát cho người tham gia. Không yêu cầu đăng nhập.
- **Kiểm tra:** Nếu khảo sát là `draft` hoặc `closed`, trả về thông báo lỗi nghiệp vụ rõ ràng (HTTP 403 / 404).
- **Response:** `200 OK` (Chỉ bao gồm các trường hiển thị, không rò rỉ dữ liệu phản hồi hay thông tin nội bộ).

### `POST /api/public/surveys/:slug_or_id/submit`
- **Mô tả:** Người tham gia nộp câu trả lời.
- **Request Body:**
  ```json
  {
    "started_at": "2026-10-22T06:25:00Z",
    "submitted_at": "2026-10-22T06:27:30Z",
    "client_metadata": {
      "screen_width": 1920,
      "screen_height": 1080,
      "user_agent_short": "Mozilla/5.0 Windows Chrome"
    },
    "answers": {
      "q1-uuid": "opt_2",
      "q2-uuid": ["opt_a", "opt_c"],
      "q3-uuid": "Rất hài lòng"
    }
  }
  ```
- **Response:** `201 Created`
  ```json
  {
    "response_id": "resp-uuid",
    "message": "Phản hồi của bạn đã được ghi nhận thành công.",
    "status": "recorded"
  }
  ```

---

## 3. Quality Assurance & Responses (Chất Lượng & Rà Soát)

### `GET /api/surveys/:id/responses`
- **Mô tả:** Lấy danh sách phản hồi kèm điểm rủi ro, phân loại mức độ và trạng thái rà soát. Hỗ trợ lọc theo `risk_level` ('low', 'medium', 'high') và `review_status`.

### `GET /api/surveys/:id/responses/:response_id`
- **Mô tả:** Lấy chi tiết câu trả lời, điểm phân rã từng chỉ báo (`S_dup`, `S_pat`, `S_logic`, `S_speed`, `S_text`), danh sách cờ cảnh báo (Flags) và phản hồi gần giống nhất để đối chiếu.

### `PATCH /api/surveys/:id/responses/:response_id/review`
- **Mô tả:** Cập nhật quyết định xác minh của người quản trị.
- **Request Body:**
  ```json
  {
    "review_status": "verified_valid",
    "review_notes": "Đã đối chiếu với người trả lời qua email xác nhận"
  }
  ```

### `GET /api/surveys/:id/compare`
- **Query params:** `?resp1=id1&resp2=id2`
- **Mô tả:** Đối chiếu 2 phản hồi song song: Tỷ lệ tương đồng, danh sách câu trả lời trùng và khác biệt.

### `GET /api/surveys/:id/analytics`
- **Mô tả:** Lấy thống kê tổng hợp thực từ database: Phân bố số lượng, thời gian, biểu đồ tần suất từng phương án cho từng câu hỏi, cảnh báo thiếu mẫu ($n < 5$).

---

## 4. Export & Import

### `GET /api/surveys/:id/export`
- **Query params:** `?scope=verified_clean|reviewed|raw&format=csv|json`
- **Mô tả:** Xuất dữ liệu thật tương ứng với bộ lọc phạm vi.

### `POST /api/surveys/:id/import`
- **Mô tả:** Nhập dữ liệu phản hồi từ file CSV có hỗ trợ ánh xạ cột.
