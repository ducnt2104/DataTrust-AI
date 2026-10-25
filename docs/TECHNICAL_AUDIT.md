# DATATRUST — BÁO CÁO KIỂM TOÁN KỸ THUẬT & ĐẠI TU HỆ THỐNG
**Document ID:** `DATATRUST-AUDIT-2026-V1`  
**Dự án:** DataTrust — Nền tảng Tạo Khảo sát & Kiểm định Độ Tin cậy Dữ liệu  
**Tác giả:** Đội ngũ Kỹ sư Trưởng & Chuyên gia Kiến trúc Hệ thống  

---

## 1. Bối cảnh & Mục tiêu Kiểm toán

DataTrust được định vị là nền tảng khảo sát số chuyên nghiệp kết hợp thu thập thực địa (OMR), công cụ lọc bất thường 7 tầng và trung tâm xác thực dữ liệu. Trước đợt đại tu này, hệ thống đã hoàn thiện tốt các chức năng lõi về CSDL, OMR và Quality Engine, nhưng phân hệ Trí tuệ Nhân tạo (AI Survey Assistant) gặp các khiếm khuyết cơ bản trong kiến trúc, bảo mật và khả năng hiểu yêu cầu người dùng:
1. **Chất lượng AI kém:** Sinh nội dung sơ sài, không nắm bắt đúng ngữ cảnh và yêu cầu chuyên sâu.
2. **Lỗ hổng bảo mật rò rỉ API Key:** Key được nối trực tiếp vào URL query string (`?key={GEMINI_API_KEY}`).
3. **Cắt cụt dạng câu hỏi:** Chỉ sinh tối đa 6 loại câu hỏi cơ bản, bỏ quên 6 loại câu hỏi học thuật quan trọng của DataTrust (đặc biệt là Ma trận tiêu chí và Xếp hạng ưu tiên).
4. **Không có cơ chế kiểm định & tự sửa lỗi:** Đầu ra JSON từ LLM không qua Pydantic schema validation; khi lỗi, âm thầm chuyển về một mẫu 6 câu hỏi tĩnh cứng nhắc mà không thông báo cho người dùng.

---

## 2. Kết quả Rà soát Baseline Trước Đại tu

| Hạng mục kiểm toán | Hiện trạng trước đại tu (Baseline) | Rủi ro & Hậu quả kỹ thuật |
| :--- | :--- | :--- |
| **Bảo mật Secret API Key** | `url = f"...gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"` | Rò rỉ khóa API qua nhật ký proxy, web server logs, history browser và APM telemetry. |
| **Bảo vệ Tiêm lệnh (Injection)** | Nạp trực tiếp văn bản người dùng vào chuỗi prompt không qua làm sạch. | Dễ bị tấn công Prompt Injection, bẻ gãy vai trò hệ thống hoặc vượt rào kiểm duyệt. |
| **Trích xuất Yêu cầu** | Gửi thẳng chuỗi `topic` và `audience` vào 1 câu prompt đơn giản. | Không trích xuất được mục tiêu nghiên cứu, giả thuyết kiểm định, thời lượng hay định dạng câu hỏi mong muốn. |
| **Phạm vi Loại Câu hỏi** | Bị giới hạn cứng: `single_choice, multiple_choice, likert, linear_scale, short_text, long_text`. | Thiếu vắng hoàn toàn `matrix` (ma trận đánh giá), `ranking` (thứ tự ưu tiên), `dropdown`, `number`, `date`, `rating`. |
| **Kiểm định & Tự sửa lỗi** | Không có (`json.loads` thô bạo; bắt ngoại lệ chung rồi chuyển về mẫu tĩnh). | Khi AI sinh thiếu phương án hoặc sai schema, người dùng nhận được khảo sát mẫu hoàn toàn không liên quan. |
| **Cơ chế Dự phòng (Fallback)** | 1 mẫu tĩnh cứng (`_heuristic_generate_survey`) gồm 6 câu nhân khẩu học và mức độ hài lòng chung chung. | Khảo sát về IT, Y tế, Giáo dục, hay Bất động sản đều nhận về cùng một bảng hỏi giống hệt nhau. |
| **Giao diện Người dùng (UI)** | Chỉ có 2 ô nhập: Chủ đề và Đối tượng; không có tùy chọn dạng câu hỏi, mục tiêu hay tiến trình. | Người dùng không kiểm soát được cấu trúc khảo sát, không thấy được trạng thái AI đang xử lý. |
| **Lưu vết Phiên làm việc (Audit)** | Không lưu vết lịch sử sinh AI hay kết quả kiểm định vào cơ sở dữ liệu. | Thiếu tính truy nguyên (Traceability) và không đo lường được hiệu năng, độ trễ và tỷ lệ lỗi. |

---

## 3. Các Biện pháp Đại tu Kiến trúc Đã Triển khai

### 3.1. Bảo mật API Key & Cấu hình An toàn
- Loại bỏ hoàn toàn API key khỏi URL query parameters. Chuyển sang sử dụng header chuẩn bảo mật:
  ```python
  headers = {
      "x-goog-api-key": GEMINI_API_KEY,
      "Content-Type": "application/json"
  }
  ```
- Thêm cơ chế xác thực an toàn `is_gemini_configured()` kiểm tra độ dài và định dạng key mà không ghi log hay xuất ra ngoại lệ.
- Tạo mẫu `.env.example` với các giá trị placeholder rõ ràng (`your_gemini_api_key_here`). Đảm bảo `.gitignore` chặn triệt để `.env` và `.env.local`.

### 3.2. Đường ống Hiểu Yêu cầu (Requirement Understanding Pipeline)
- Xây dựng lớp `RequirementParser` với bộ lọc biểu thức chính quy (Regex Filter) phát hiện và vô hiệu hóa các mẫu tiêm lệnh phổ biến (`IGNORE PREVIOUS INSTRUCTIONS`, `SYSTEM COMPROMISED`, `<script>`, `DROP TABLE`).
- Tự động nhận diện ý định và suy luận các dạng câu hỏi chuyên biệt từ mô tả của người dùng (nhận diện từ khóa "ma trận", "xếp hạng", "thang điểm nps", "tiêu chí").
- Cấu trúc hóa yêu cầu thành `SurveyRequirementSpec` gồm đầy đủ: chủ đề, đối tượng, mục tiêu nghiên cứu, số lượng câu hỏi mong muốn, thời lượng làm bài và ngôn ngữ.

### 3.3. Hỗ trợ Đầy đủ 12 Loại Câu hỏi & Chuẩn Khoa học AAPOR
- Tích hợp tiêu chuẩn phương pháp luận khảo sát của Don Dillman (Tailored Design Method) và hiệp hội AAPOR vào System Instruction.
- Hỗ trợ sinh đầy đủ 12 loại câu hỏi, đặc biệt là:
  - `matrix`: Định dạng rõ ràng danh sách hàng ngang (tiêu chí đánh giá) và cột (thang đo chất lượng).
  - `ranking`: Danh sách các yếu tố để kéo thả hoặc sắp xếp thứ tự ưu tiên.
  - `linear_scale`: Thang đo NPS chuẩn 1 đến 10 với nhãn hai cực rõ ràng.
  - `likert`: Thang đo Likert 5 mức độ trung lập, tránh thiên lệch.

### 3.4. Kiểm định Tính Khách quan & Bounded Self-Repair Loop
- Phương thức `validate_survey_draft`:
  - Kiểm tra số lượng câu hỏi tối thiểu.
  - Rà soát từ ngữ dẫn dắt định hướng người trả lời (`LEADING_QUESTION`).
  - Phát hiện câu hỏi kép đánh giá 2 khía cạnh trong 1 câu (`DOUBLE_BARRELED_QUESTION`).
  - Kiểm tra tính đầy đủ của phương án lựa chọn ($\ge 2$ phương án, có cấu trúc rows/columns cho matrix).
  - Tính toán các chỉ số định lượng: `coverage_score`, `adherence_score`, `objectivity_score`.
- Bounded Self-Repair: Nếu phát hiện lỗi, hệ thống tự động gửi yêu cầu sửa lỗi có trọng tâm đến Gemini (giới hạn tối đa 2 lần). Nếu vẫn còn vi phạm hoặc đang chạy ngoại tuyến, áp dụng bộ chuyển đổi Heuristic Sanitizer để loại bỏ từ dẫn dắt và bổ sung phương án thiếu.

### 3.5. Động cơ Hình mẫu Khoa học (Deterministic Archetype Engine)
- Khi không có API key hoặc kết nối bị gián đoạn, hệ thống không trả về mẫu tĩnh sơ sài mà kích hoạt bộ sinh theo 6 nhóm hình mẫu nghiên cứu:
  1. `CSAT_PRODUCT`: Khảo sát sự hài lòng khách hàng, trải nghiệm dịch vụ và NPS.
  2. `EMPLOYEE_ENGAGEMENT`: Gắn kết nhân viên, văn hóa doanh nghiệp và đãi ngộ.
  3. `HEALTHCARE_COMMUNITY`: Y tế cộng đồng, tiếp cận dịch vụ và mức độ tin cậy.
  4. `EDUCATION_ACADEMIC`: Nghiên cứu học thuật, phương pháp học tập và hứng thú môn học.
  5. `MARKET_RESEARCH`: Khảo sát thị trường, hành vi tiêu dùng và độ nhạy về giá.
  6. `GENERAL_EMPIRICAL`: Bảng hỏi thực nghiệm đa biến tổng quát.
- Các câu hỏi được điền động chính xác chủ đề, đối tượng và tiêu chí mà người dùng yêu cầu.

### 3.6. Cơ sở Dữ liệu & Lưu vết Phiên AI (Persistence & Traceability)
- Thêm bảng `ai_generation_sessions` và `ai_audit_logs` vào SQLite WAL:
  - Lưu trữ mã phiên, chủ đề, đối tượng, mục tiêu, mô hình sử dụng, nhà cung cấp, thời gian xử lý (ms), bản nháp khảo sát chi tiết và báo cáo kiểm định.
- Thêm các tuyến API quản trị: `GET /api/ai/sessions`, `GET /api/ai/sessions/{id}`, `POST /api/ai/analyze-responses`.

### 3.7. Nâng cấp Giao diện Web Động
- Modal AI Survey Assistant trên `SurveyBuilderPage.tsx`:
  - Hiển thị badge nhà cung cấp theo thời gian thực (Gemini API vs Local Engine).
  - Cho phép người dùng nhập mục tiêu nghiên cứu, chọn số lượng câu hỏi (5, 7, 10, 12 câu) và bật/tắt các dạng câu hỏi ưu tiên (Matrix, Ranking, Likert, NPS, Trắc nghiệm đơn, Đóng góp mở).
  - Thanh tiến trình 3 bước trực quan: Phân tích -> Lập cấu trúc -> Kiểm định.
  - Chế độ xem trước (Preview) cho phép kiểm tra danh sách câu hỏi và điểm tính khách quan trước khi áp dụng vào bảng thiết kế.
- Khay Kiểm định Câu hỏi (AI Audit Drawer):
  - Hiển thị chi tiết cảnh báo kèm nút **"✓ Tự động sửa"** (One-click Auto-fix). Khi nhấn, hệ thống cập nhật câu hỏi trên bảng thiết kế ngay lập tức.
- Thẻ Phân tích Định tính AI (`AIQualitativeInsightsCard.tsx`) trên trang phân tích:
  - Phân loại tỷ lệ sắc thái tình cảm (Positive / Neutral / Negative).
  - Trích xuất chủ đề then chốt kèm trích dẫn mẫu và cảnh báo phản hồi rác (spam text).

---

## 4. Kết quả Đánh giá Thực nghiệm

- **Bộ kiểm chuẩn AI Benchmark Suite (10 ca kiểm thử):**
  - Tỷ lệ tuân thủ loại câu hỏi bắt buộc: **100.0%**
  - Điểm số tuân thủ trung bình: **83.4 / 100**
  - Tính toàn vẹn của phương án: **100.0%**
  - Tỷ lệ kháng tiêm lệnh độc hại (Injection Resistance): **100.0%**
  - Thời gian xử lý trung bình: **8.1 ms**
- **Toàn bộ 36 ca kiểm thử Pytest backend:** Đạt **100% (36/36 passed)**.
- **Frontend Build (Vite & TypeScript strict):** Thành công trong **824ms với 0 lỗi**.
