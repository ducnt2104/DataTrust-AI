# DataTrust — API Contract Specification

Tất cả các API trả về định dạng JSON chuẩn hoặc tệp nhị phân tương ứng. Mã lỗi HTTP tuân thủ nghiêm ngặt (200: OK, 201: Created, 400: Bad Request, 403: Forbidden, 404: Not Found, 422: Validation Error, 429: Too Many Requests, 500: Internal Server Error).

---

## 1. Surveys Management (Quản Trị Khảo Sát)

### `GET /api/surveys`
- **Mô tả:** Lấy danh sách khảo sát (hỗ trợ lọc theo `status`).
- **Response:** `200 OK`

### `POST /api/surveys`
- **Mô tả:** Tạo một khảo sát mới (mặc định trạng thái `draft`).
- **Response:** `201 Created`

### `GET /api/surveys/:id`
- **Mô tả:** Lấy thông tin chi tiết một cuộc khảo sát, bao gồm danh sách câu hỏi và cấu hình logic.
- **Response:** `200 OK`

### `PUT /api/surveys/:id`
- **Mô tả:** Cập nhật thông tin khảo sát, danh sách câu hỏi và cấu hình nâng cao `settings` (Tự động lưu lịch sử snapshot vào `survey_versions` khi có thay đổi câu hỏi).
- **Cấu hình `settings` hỗ trợ:**
  - `alert_webhook_url`: URL nhận webhook thời gian thực (Slack/Teams/SIEM).
  - `webhook_secret`: Khóa bí mật HMAC-SHA256 (RFC 2104).
  - `quality_settings.speeder_min_seconds`: Ngưỡng thời gian nộp bài tối thiểu (Speeders).
  - `quality_settings.straightlining_threshold`: Tỷ lệ trả lời cùng một cột phương án liên tục.
  - `quality_settings.geofence`: Cấu hình ranh giới thực địa (`enabled: bool`, `target_lat: float`, `target_lon: float`, `max_radius_km: float`, `location_name: str`).
- **Response:** `200 OK`

### `POST /api/surveys/:id/publish`
- **Mô tả:** Kiểm tra tính hợp lệ và xuất bản khảo sát sang trạng thái `published`, sinh link công khai và mã QR.
- **Response:** `200 OK`

### `POST /api/surveys/:id/close`
- **Mô tả:** Đóng khảo sát, không nhận thêm câu trả lời từ link công khai.
- **Response:** `200 OK`

### `POST /api/surveys/:id/reopen`
- **Mô tả:** Mở lại khảo sát đã đóng để tiếp tục thu thập dữ liệu thực địa.
- **Response:** `200 OK`

### `POST /api/surveys/:id/duplicate`
- **Mô tả:** Nhân bản toàn bộ cấu trúc câu hỏi, quy tắc logic sang một khảo sát mới ở trạng thái `draft`.
- **Response:** `201 Created`

### `GET /api/surveys/:id/versions`
- **Mô tả:** Lấy danh sách lịch sử tất cả các phiên bản của cấu trúc khảo sát (Schema Evolution).
- **Response:** `200 OK`

### `GET /api/surveys/:id/versions/:version_num`
- **Mô tả:** Lấy chi tiết toàn bộ câu hỏi và cấu trúc tại một phiên bản lịch sử cụ thể phục vụ đối soát và phục hồi 1-click.
- **Response:** `200 OK`

### `POST /api/surveys/:id/settings/test-webhook`
- **Mô tả:** Kiểm tra kết nối và gửi thử nghiệm gói tin cảnh báo webhook đến hệ thống giám sát bên ngoài (Slack, Teams, SIEM) kèm chữ ký HMAC-SHA256.
- **Request Body:** `{"webhook_url": "https://...", "webhook_secret": "optional_secret"}`
- **Response:** `200 OK` (`{"success": true, "status_code": 200, "latency_ms": 45.2, ...}`)

---

## 2. Public Survey (Khảo Sát Công Khai Cho Người Tham Gia)

### `GET /api/public/surveys/:slug_or_id`
- **Mô tả:** Tải schema khảo sát cho người tham gia. Không yêu cầu đăng nhập.
- **Kiểm tra:** Nếu khảo sát là `draft` hoặc `closed`, trả về thông báo lỗi nghiệp vụ rõ ràng (HTTP 403 / 404).
- **Response:** `200 OK`

### `POST /api/public/surveys/:slug_or_id/submit`
- **Mô tả:** Người tham gia nộp câu trả lời trực tuyến (có bảo vệ rate-limit và chống double-click). Tự động kích hoạt 7 tầng kiểm định chất lượng và phát tán webhook cảnh báo nếu rủi ro cao.
- **Response:** `201 Created`

### `POST /api/public/surveys/:slug_or_id/batch-sync`
- **Mô tả:** Đồng bộ hàng loạt lên đến 100 phiếu ngoại tuyến từ thiết bị thực địa trong 1 transaction CSDL SQLite duy nhất.
- **Bảo vệ Idempotency:** Nhận dạng `client_uuid` để bỏ qua an toàn các phiếu đã đồng bộ nếu đường truyền bị ngắt giữa chừng.
- **Response:** `200 OK`

---

## 3. Quality Assurance & Responses (Chất Lượng & Rà Soát)

### `GET /api/surveys/:id/responses`
- **Mô tả:** Lấy danh sách phản hồi kèm điểm rủi ro, phân loại mức độ và trạng thái rà soát. Hỗ trợ lọc theo `risk_level` và `review_status`.

### `GET /api/surveys/:id/responses/:response_id`
- **Mô tả:** Lấy chi tiết câu trả lời, điểm phân rã từng chỉ báo (`S_dup`, `S_pat`, `S_logic`, `S_speed`, `S_text`, `S_enum`), danh sách cờ cảnh báo (Flags) và phản hồi gần giống nhất.

### `PATCH /api/surveys/:id/responses/:response_id/review`
- **Mô tả:** Cập nhật quyết định xác minh của người quản trị, ghi nhận vào chuỗi băm kiểm toán SHA-256 bất biến.

### `POST /api/surveys/:id/responses/batch-review`
- **Mô tả:** Thẩm định hàng loạt danh sách phản hồi (Duyệt hợp lệ, Gắn cờ gian lận, Chuyển xem xét lại) trong 1 transaction duy nhất.

### `POST /api/surveys/:id/responses/cleansing/preview`
- **Mô tả:** Mô phỏng quy trình làm sạch dữ liệu tự động (Don Dillman / AAPOR Presets: Speeders, Straightlining, Mâu thuẫn logic, Rủi ro cao). So sánh mẫu sạch và mức tăng độ tin cậy thang đo Cronbach's Alpha trước vs sau khi làm sạch.

### `POST /api/surveys/:id/responses/cleansing/apply`
- **Mô tả:** Thực thi làm sạch dữ liệu: tự động gắn nhãn loại trừ `verified_fraud` kèm lý do cụ thể và gắn nhãn `verified_valid` cho mẫu sạch. Ghi sự kiện vào chuỗi băm bất biến.

### `GET /api/surveys/:id/compare`
- **Query params:** `?resp1=id1&resp2=id2`
- **Mô tả:** Đối chiếu 2 phản hồi song song: Tỷ lệ tương đồng, danh sách câu trả lời trùng và khác biệt.

### `GET /api/surveys/:id/analytics`
- **Mô tả:** Lấy thống kê tổng hợp thực từ database: Phân bố số lượng, thời gian, biểu đồ tần suất từng phương án cho từng câu hỏi, cảnh báo thiếu mẫu.

### `GET /api/surveys/:id/analytics/crosstab`
- **Query params:** `?row_var=qid1&col_var=qid2&scope=all|verified_clean`
- **Mô tả:** Bảng Ngẫu Nhiên 2 chiều (Contingency Table), kiểm định độc lập Chi-Square ($\chi^2$), $p$-value vi giây, và hệ số tương quan Cramer's V.

### `GET /api/surveys/:id/analytics/benford`
- **Mô tả:** Kiểm định phân bố chữ số đầu tiên theo Luật Benford (Benford's Law) phát hiện dữ liệu số bịa đặt nhân tạo.

### `GET /api/surveys/:id/analytics/qualitative`
- **Mô tả:** Phân tích ngữ nghĩa văn bản tiếng Việt thực tế: nhận diện từ ghép, đảo nghĩa phủ định, trích xuất trích dẫn người tham gia và phân cụm 6 chủ đề chuyên ngành.

---

## 4. Academic Dossier & Statistical Syntax Export

### `GET /api/surveys/:id/export/academic-dossier`
- **Query params:** `?scope=all|verified_clean|reviewed`
- **Mô tả:** Đóng gói toàn bộ Hồ Sơ Nghiên Cứu Khoa Học dạng tệp `.ZIP` chuẩn bị bảo vệ đề tài, kỷ yếu hội thảo, luận văn (KHKT, ISEF, ViSEF, ĐH) gồm 8 tệp:
  1. `dataset_clean.csv` (Mã hóa biến số `VAR001...`, tương thích SPSS, Stata, R, Python, UTF-8 BOM, kháng CWE-1236)
  2. `dataset_labeled.csv` (Tiêu đề tiếng Việt đầy đủ cho Excel)
  3. `spss_syntax.sps` (Cú pháp tự động nạp IBM SPSS, Variable Labels, Value Labels, Missing Values 999)
  4. `stata_syntax.do` (Mã Stata Do-File: import delimited, label variable, label define, label values, describe, summarize)
  5. `run_analysis.R` (Script R: nạp dữ liệu, chuyển đổi Factors, tính Cronbach's Alpha)
  6. `analyze_data.py` (Script Python Pandas: thống kê mô tả, tần số và ma trận tương quan)
  7. `CODEBOOK.md` (Từ điển dữ liệu chuẩn Don Dillman & AAPOR)
  8. `INTEGRITY_CERTIFICATE_SHA256.json` (Chứng chỉ kiểm toán mật mã học chứa mã băm đối soát)
  9. `README_RESEARCH_DOSSIER.md` (Hướng dẫn chạy và kiểm tra mã băm trên PowerShell/Linux)

### `GET /api/surveys/:id/export/manuscript`
- **Query params:** `?format=markdown|html|latex&scope=all|verified_clean`
- **Mô tả:** Tự động biên soạn Bản Thảo Nghiên Cứu Khoa Học Hoàn Chỉnh (Complete Scientific Research Manuscript) dựa trên số liệu thực chứng và chứng chỉ mật mã học:
  - `format=markdown`: Trả về tài liệu Markdown (.md) chuẩn GitHub & KaTeX gồm 9 chương hoàn chỉnh (Abstract, Methodology, Data Cleansing, Cronbach's Alpha, Funnel, Chi-Square, Qualitative NLP, SHA-256 Ledger, References).
  - `format=html`: Trả về trang HTML độc lập có CSS in ấn chuyên nghiệp (`@media print`), bảng KPI tổng quan và typography chuẩn bài báo quốc tế.
  - `format=latex`: Trả về mã nguồn LaTeX (.tex) hoàn chỉnh sẵn sàng tải lên Overleaf hoặc biên dịch bằng `pdflatex`.

### `GET /api/surveys/:id/codebook`
- **Query params:** `?format=json|spss|r|stata`
- **Mô tả:** Tải riêng lẻ Từ điển dữ liệu hoặc cú pháp thống kê tương ứng theo định dạng yêu cầu.

### `GET /api/surveys/:id/paper/printable-html`
- **Mô tả:** Xuất giao diện in ấn mẫu phiếu khảo sát giấy chuẩn khổ A4 kèm mã QR và mốc căn góc OMR.

---

## 5. Audit Trail & Legal Compliance (Kiểm Định & Pháp Lý)

### `GET /api/surveys/:id/audit-report`
- **Mô tả:** Lấy Báo cáo Kiểm định Chất lượng Dữ liệu Độc lập tuân thủ Nghị định 356/2025/NĐ-CP, Luật Bảo vệ Dữ liệu Cá nhân 2025 và Tiêu chuẩn AAPOR (2003) kèm hệ số Cronbach's Alpha và mã băm kiểm toán.

### `GET /api/surveys/:id/audit-report/printable-certificate`
- **Mô tả:** Xuất Chứng Thư Thẩm Định Chất Lượng & Tính Toàn Vẹn Dữ Liệu dạng trang HTML chuẩn in ấn khổ A4 (Print / Save as PDF) kèm dấu bảo an kỹ thuật số, định danh băm SHA-256 và mã QR xác thực phục vụ kẹp hồ sơ bảo vệ đề tài, luận văn khoa học hoặc giải thưởng KHKT / ViSEF / ISEF.

### `GET /api/surveys/:id/audit-trail`
- **Mô tả:** Báo cáo xác thực toán học toàn bộ chuỗi băm kiểm toán SHA-256 bất biến (`is_chain_valid`, `head_hash`, `genesis_hash`, `tampered_at_index`).

### `POST /api/surveys/:id/audit/simulate-attack`
- **Mô tả:** Thực thi Giả Lập Tấn Công Đối Kháng Thực Nghiệm (Adversarial Red-Team Live Simulation) trực tiếp trong sandbox:
  - Kiểm thử 6 kịch bản tấn công: SQL Injection Parameterized Defense, XSS Sanitization, CWE-1236 CSV Formula Neutralization, SHA-256 Ledger Anti-Tamper, Speeder Bot (Layer 1), Straightliner Satisficing (Layer 2).
  - Trả về cấu trúc `RedTeamSimulationResult`: `overall_status`, `compliance_score` (100%), `attacks_tested`, `attacks_deflected`, `total_duration_ms`, `standards_verified` và danh sách chi tiết `attack_results`.
  - Tự động ghi vết sự kiện `RED_TEAM_AUDIT_SIMULATION` vào Sổ cái kiểm toán SHA-256 bất biến.

### `POST /api/surveys/:id/privacy/anonymize`
- **Mô tả:** Thực thi quyền ẩn danh hóa / xóa siêu dữ liệu thiết bị (IP, User-Agent) và làm mờ câu trả lời văn bản PII theo Nghị định 356/2025/NĐ-CP.

---

## 6. System Maintenance & Database Health

### `POST /api/system/maintenance/wal-checkpoint`
- **Mô tả:** Thực thi `PRAGMA wal_checkpoint(TRUNCATE)` và `PRAGMA optimize`, thu nhỏ tệp WAL về 0 bytes.

### `POST /api/system/maintenance/vacuum`
- **Mô tả:** Thu hồi phân mảnh CSDL SQLite, tính toán dung lượng đĩa giải phóng được (`freed_bytes`).

### `POST /api/system/maintenance/backup`
- **Mô tả:** Sao lưu nóng nguyên tử thông qua SQLite Online Backup API không khóa thao tác ghi thực địa.

### `GET /api/system/diagnostics`
- **Mô tả:** Kiểm tra chẩn đoán toàn diện sức khỏe hệ thống: dung lượng tệp CSDL trên đĩa (bytes, MB), kiểm tra toàn vẹn cấu trúc B-Tree (`PRAGMA integrity_check`), chế độ nhật ký (`journal_mode = WAL`), số lượng bản ghi toàn bộ 7 bảng và xác thực toán học tính bất biến của Chuỗi băm kiểm toán SHA-256 (`verify_audit_chain`).

---

## 7. Academic Research Demo Seeder (Khởi Tạo Dữ Liệu Nghiên Cứu Mẫu)

### `POST /api/surveys/seed-academic-demo`
- **Mô tả:** Khởi tạo Khảo sát Nghiên cứu Khoa học Mẫu chuẩn quốc tế (7 câu hỏi đo lường) kèm 35 phản hồi thực nghiệm:
  - 28 phản hồi hợp lệ (Clean Responses) với độ tin cậy thang đo Cronbach's Alpha $\ge 0.80$ (tối ưu hóa khoảng cách Hamming $\le 66.7\%$).
  - 7 phản hồi cảnh báo bất thường: 3 Speeders ($< 5$s), 2 Straightliners ($100\%$ cùng 1 mức đánh giá), 1 Gibberish Text ("aaaaaaaaaaaaaaaaaaaa"), 1 High-Risk Composite.
  - Chuỗi băm kiểm toán SHA-256 bất biến toàn vẹn $100\%$.
  - Trả về: `survey_id`, `public_slug`, `title`, `total_responses: 35`, `clean_count: 28`, `flagged_count: 7`, `data_trust_index: 80.0`, `cronbach_alpha: 0.884`.

### `POST /api/surveys/:id/seed-demo-responses?count=15`
- **Mô tả:** Nạp nhanh các phản hồi mẫu thực tế vào một khảo sát bất kỳ đã tồn tại, tự động sinh các câu trả lời phù hợp với cấu trúc câu hỏi (single choice, rating, linear scale, text, number) và tính toán điểm rủi ro qua 7-Layer Quality Engine.

---

## 8. Enumerator Analytics & Field Geofencing (Quản Lý & Giám Sát Điều Tra Viên Thực Địa)

### `GET /api/surveys/:id/enumerators`
- **Mô tả:** Phân tích toàn diện hiệu suất và rủi ro giả mạo số liệu của từng điều tra viên (Interviewer / Field Group Falsification Detection):
  - **Phương sai & Z-Score:** Đo độ lệch chuẩn Z-score về phương sai câu trả lời đóng (`variance_z_score < -1.75` cảnh báo làm bài rập khuôn).
  - **Tốc độ phi lý (Teleportation Detection):** Phát hiện di chuyển siêu tốc giữa 2 điểm phỏng vấn (`impossible_speed_detected`, `max_speed_kmh > 120km/h`).
  - **Cụm tọa độ tĩnh (Stationary Cluster):** Phát hiện điều tra viên ngồi một chỗ tự điền phiếu (`stationary_cluster_detected`, cụm < 5m hoặc Bán kính hồi chuyển Radius of Gyration $R_g < 20$m qua $\ge 4$ phiếu).
  - **Kiểm định Ranh giới Địa lý (Geofencing Compliance):** Tự động đối chiếu tọa độ với cấu hình `geofence` của khảo sát, tính khoảng cách trắc địa Haversine tới tâm (`distance_from_center_km`), đếm số điểm vi phạm (`geofence_breach_count`) và gắn cờ bất thường khi ra ngoài bán kính cho phép.
  - Trả về: `EnumeratorAnalyticsOut` gồm `survey_id`, `total_enumerators`, `total_field_responses`, `geofence_setting` và danh sách chi tiết `enumerators`.

### `GET /api/surveys/:id/enumerators/export`
- **Mô tả:** Xuất danh sách kiểm toán và phân tích bất thường theo từng điều tra viên dạng tệp CSV có UTF-8 BOM tương thích 100% Microsoft Excel, bao gồm các cột: Mã Điều tra viên, Tổng số phiếu, Phiếu giấy OMR, Phiếu trực tuyến, Thời gian TB, Điểm rủi ro TB, Số phiếu rủi ro cao, Z-score, Độ phủ GPS, Bán kính Rg, Diện tích bao phủ, Số điểm vi phạm ranh giới, Cảnh báo vi phạm vùng, Tốc độ tối đa, Cảnh báo tốc độ phi lý, Cảnh báo tọa độ tĩnh, Trạng thái bất thường và Lý do cảnh báo chi tiết.

---

## 9. Public Verification & Trust Registry (Cổng Tra Cứu & Xác Thực Chứng Thư Độc Lập)

### `GET /api/public/verify/:identifier`
- **Mô tả:** Tra cứu mở và kiểm chứng tức thời tính hợp lệ, toàn vẹn và chữ ký băm mật mã học của bất kỳ chứng thư hoặc hồ sơ khảo sát nào mà không cần đăng nhập quản trị.
- **Tham số `identifier`:**
  - Mã chứng thư chuẩn: `DT-CERT-2026-XXXXXXXX` hoặc `CERT-DATATRUST-XXXXXXXX`.
  - Mã khảo sát UUID hoặc Public Slug.
  - Mã băm đỉnh sổ cái kiểm toán SHA-256 (64 hex characters).
- **Giới hạn an toàn:** Sliding Window Rate Limiter 60 requests/phút/IP chống tấn công quét tự động (Brute-force / Scraping).
- **Phản hồi (`PublicCertificateVerificationOut`):**
  - `status`: `'VERIFIED_VALID' | 'TAMPERED' | 'NOT_FOUND'`
  - `certificate_id`: Mã chứng chỉ chính thức
  - `survey_id`, `survey_title`, `survey_description`, `public_slug`, `issued_at`
  - `total_responses`, `clean_responses`, `excluded_responses`, `trust_index` (%)
  - `cronbach_alpha`: Hệ số độ tin cậy thang đo
  - `reliability_verdict`: Đánh giá chất lượng thang đo theo chuẩn Nunnally & Bernstein
  - `ledger_chain_valid`: Boolean xác nhận tính toàn vẹn chuỗi sổ cái
  - `ledger_head_hash`: Mã băm đỉnh chuỗi SHA-256
  - `ledger_genesis_hash`: Mã băm khởi nguyên chuỗi
  - `total_audit_events`: Tổng số sự kiện kiểm toán được ký số trong chuỗi
  - `verification_verdict`: Tuyên ngôn xác thực khoa học
  - `compliance_standards`: Danh sách tiêu chuẩn quốc tế (AAPOR, Don Dillman, Nghị định 356/2025/NĐ-CP, W3C Verifiable Data)
  - `printable_certificate_url`: Đường dẫn tải chứng thư khổ in A4

### `GET /api/public/verify?q=...`
- **Mô tả:** Tra cứu chứng thư kiểm định công khai thông qua Query Parameter URL.

---

## 10. Psychometric Scale Reliability Engine (Độ Tin Cậy Thang Đo Tâm Lý Học)

### `GET /api/surveys/:id/analytics/reliability?scope=verified_clean`
- **Mô tả:** Phân tích chuyên sâu độ tin cậy thang đo (Item-Total Statistics & Scale Reliability Analysis) theo chuẩn mực quốc tế Nunnally & Bernstein (1994) và IBM SPSS Statistics:
  - Hệ số Cronbach's Alpha ($\alpha$) mẫu thô và chuẩn hóa (Standardized $\alpha$).
  - Thống kê Item-Total từng câu hỏi: Điểm trung bình ($M_j$), Phương sai ($S_j^2$), Độ lệch chuẩn ($S_j$).
  - Điểm trung bình thang đo nếu loại biến ($M_{-j}$) và Phương sai thang đo nếu loại biến ($S_{-j}^2$).
  - Tương quan biến - tổng hiệu chỉnh (Corrected Item-Total Correlation $r_{it}$). Cảnh báo đỏ nếu $r_{it} < 0.30$ (biến không phân biệt được đối tượng đo lường).
  - Cronbach's Alpha nếu loại biến ($\alpha_{-j}$): Chỉ rõ nếu loại bỏ câu hỏi có làm tăng độ tin cậy thang đo hay không.
  - Phân loại học thuật (Academic Rating): `XUẤT SẮC (α ≥ 0.90)`, `RẤT TỐT (0.80 ≤ α < 0.90)`, `ĐẠT CHUẨN (0.70 ≤ α < 0.80)`, `CHẤP NHẬN ĐƯỢC (0.60 ≤ α < 0.70)`, `KHÔNG ĐẠT (α < 0.60)`.
  - Khuyến nghị hành động từng câu: `Giữ lại`, `Cần xem xét hiệu chỉnh`, hoặc `Khuyến nghị loại bỏ`.

---

## 11. Automated Academic Dossier Verification Script (Kịch Bản Kiểm Chứng Tự Động)

### `GET /api/surveys/:id/export/academic-dossier?scope=verified_clean`
- **Mô tả:** Gói nén `.ZIP` trọn bộ hồ sơ nghiên cứu học thuật chuẩn mực quốc tế bao gồm thêm công cụ kiểm toán độc lập:
  1. `verify_dossier.py`: Công cụ dòng lệnh (CLI) độc lập, thuần Python Standard Library (không cần cài thêm thư viện ngoài). Tự động nạp `INTEGRITY_CERTIFICATE_SHA256.json`, tính toán mã băm SHA-256 từng tệp trong thư mục giải nén và đối soát 100% khớp chữ ký mật mã học.
  2. `README_RESEARCH_DOSSIER.md`: Hướng dẫn chi tiết cách thức chạy `python verify_dossier.py` cho Giám khảo hội đồng và Kiểm toán viên.
  3. `INTEGRITY_CERTIFICATE_SHA256.json`: Chứng chỉ kiểm toán chứa mã băm của 8 tệp thành phần và trạng thái chuỗi khối nhẹ (`chain_valid`, `head_hash`, `genesis_hash`).
  4. Bộ tệp mã nguồn phân tích: `dataset_clean.csv`, `dataset_labeled.csv`, `spss_syntax.sps`, `stata_syntax.do`, `run_analysis.R`, `analyze_data.py`, `CODEBOOK.md`, `RESEARCH_MANUSCRIPT.md`.

---

## 12. Sampling Quotas & Demographic Stratification Control (Hạn Ngạch Mẫu)

### `GET /api/surveys/:id/analytics/quotas`
- **Mô tả:** Truy vấn danh sách các ô hạn ngạch mẫu (Quota Cells), số lượng mục tiêu ($N$), số lượng đã đạt thực tế, tỷ lệ hoàn thành (%) và trạng thái (`open`, `almost_full`, `filled`).
- **Phản hồi (`SamplingQuotaReportOut`):**
  - `total_quota_cells`, `filled_cells`, `open_cells`
  - `overall_target_sum`, `overall_achieved_sum`, `overall_completion_pct`
  - `cells`: Mảng tiến độ từng ô hạn ngạch

### `PUT /api/surveys/:id/analytics/quotas`
- **Mô tả:** Cập nhật danh sách quy tắc hạn ngạch mẫu (`SaveQuotasRequest`). Ghi nhật ký vào chuỗi kiểm toán bất biến SHA-256 (`UPDATE_SAMPLING_QUOTAS`).
- **Hành động khi đầy hạn ngạch (`action`):**
  - `flag_overflow`: Gắn nhãn `QUOTA_OVERFLOW` vào cờ kiểm định chất lượng, vẫn tiếp nhận dữ liệu.
  - `screen_out`: Ngắt bài làm khảo sát với thông báo lịch sự, đánh dấu `review_status = 'quota_screened_out'` để bảo vệ tính đại diện của mẫu cốt lõi.

---

## 13. Post-Stratification Raking Engine (Cân Bằng Trọng Số Sau Thu Thập IPF)

### `POST /api/surveys/:id/analytics/raking`
- **Mô tả:** Thực thi thuật toán Cân bằng Trọng số Mẫu Đa chiều (Deming-Stephan Iterative Proportional Fitting - IPF) theo chuẩn mực AAPOR/ESOMAR.
- **Tham số đầu vào (`DemographicRakingRequest`):**
  - `target_margins`: Tỷ trọng dân số chuẩn mục tiêu (Census Benchmarks) theo từng biến phân tầng (VD: Giới tính, Khu vực địa lý, Nhóm tuổi).
  - `scope`: `'verified_clean'` hoặc `'all'`.
  - `max_iterations`: Số vòng lặp tối đa (mặc định 50).
  - `convergence_tol`: Ngưỡng sai số hội tụ (mặc định 0.001).
  - `trim_min`, `trim_max`: Giới hạn cắt xén trọng số (Weight Trimming: [0.2, 5.0]) kiểm soát phương sai ngoại lai.
- **Phản hồi (`DemographicRakingOut`):**
  - `converged`: Boolean xác nhận hội tụ.
  - `iterations`: Số vòng lặp thực tế.
  - `sample_size`: Cỡ mẫu danh nghĩa ($N$).
  - `design_effect_deff`: Hệ số thiết kế của Kish ($\text{Deff} = 1 + \text{CV}_w^2$).
  - `effective_sample_size_neff`: Cỡ mẫu hiệu dụng của Kish ($N_{\text{eff}} = N / \text{Deff}$).
  - `statistical_efficiency_pct`: Hiệu suất thống kê ($N_{\text{eff}} / N \times 100\%$).
  - `weight_stats`: Min, Max, Mean (chuẩn 1.0), Std.
  - `marginal_comparisons`: Bảng đối chiếu phân bố biên chi tiết: Chưa cân (%) vs Dân số mục tiêu (%) vs Đã cân (%) vs Mức giảm sai lệch (Bias Reduction).

### `POST /api/surveys/:id/analytics/raking/export-csv`
- **Mô tả:** Xuất và tải tệp CSV bộ dữ liệu có thêm cột trọng số cá thể `statistical_weight_wi` cho từng người tham gia, tương thích 100% với các hàm phân tích mẫu phức hợp trong R (`survey::svydesign`), Python (`statsmodels.stats.weightstats`), và SPSS (`WEIGHT BY statistical_weight_wi.`).

---

## 14. Differential Item Functioning (DIF) & Measurement Invariance Engine

### `GET /api/surveys/:id/analytics/dif`
- **Mô tả:** Thực hiện kiểm định Bất biến Đo lường & Hàm mục Sai lệch theo phương pháp luận Mantel-Haenszel (Holland & Thayer, 1988) và tiêu chuẩn phân loại 3 cấp độ của Viện Khảo thí Giáo dục Hoa Kỳ (Educational Testing Service - ETS).
- **Mục đích:** Xác định liệu một câu hỏi thang đo có thiên vị bất công đối với một nhóm dân số học (Focal group) so với nhóm tham chiếu (Reference group) khi hai người có cùng mức độ năng lực/thái độ tổng thể hay không.
- **Tham số truy vấn (Query Parameters):**
  - `grouping_question_id`: ID câu hỏi phân nhóm nhân khẩu học (VD: Giới tính, Vùng miền, Trình độ học vấn).
  - `reference_group`: Tên giá trị nhóm tham chiếu (VD: `"Nam"`, `"Thành thị"`).
  - `focal_group`: Tên giá trị nhóm tâm điểm cần kiểm định thiên lệch (VD: `"Nữ"`, `"Nông thôn"`).
  - `scope`: `'verified_clean'` (mặc định) hoặc `'all'`.
  - `strata_count`: Số phân tầng tổng điểm năng lực (mặc định 4 - quartiles).
- **Phản hồi (`DIFReportOut`):**
  - `reference_group`, `focal_group`, `sample_reference`, `sample_focal`, `total_eval_sample`, `strata_count`
  - `class_a_count`: Số câu hỏi Class A (Công bằng / Không thiên lệch đáng kể: $|\Delta| < 1.0$ hoặc $p \ge 0.05$).
  - `class_b_count`: Số câu hỏi Class B (Thiên lệch vừa phải: $1.0 \le |\Delta| < 1.5$ và $p < 0.05$).
  - `class_c_count`: Số câu hỏi Class C (Thiên lệch nghiêm trọng: $|\Delta| \ge 1.5$ và $p < 0.05$).
  - `overall_verdict`: `'ĐẠT_CHUẨN_BẤT_BIẾN_ĐO_LƯỜNG'` | `'CÓ_THIÊN_LỆCH_VỪA_PHẢI'` | `'PHÁT_HIỆN_THIÊN_LỆCH_NGHIÊM_TRỌNG'` | `'CHƯA_ĐỦ_MẪU'`
  - `summary`: Tóm tắt học thuật khoa học
  - `items`: Danh sách kết quả từng câu hỏi thang đo:
    - `median_threshold`: Ngưỡng nhị phân hóa (phân vị 50%)
    - `chi2_mh`: Thống kê kiểm định $\chi^2_{\text{MH}}$ (hiệu chỉnh liên tục)
    - `p_value`: Giá trị xác suất chính xác theo hàm $P(\chi^2_1 \ge x)$
    - `alpha_odds_ratio`: Tỷ số chênh chung Mantel-Haenszel ($\alpha_{\text{MH}}$)
    - `delta_ets`: Chỉ số Delta ETS ($\Delta_{\text{MH}} = -2.35 \cdot \ln(\alpha_{\text{MH}})$)
    - `ets_class`: `'A'`, `'B'`, `'C'`
    - `favored_group`: Nhóm hưởng lợi thế bất công (`Trung lập`, `Ưu thế cho 'Reference'`, hoặc `Ưu thế cho 'Focal'`)
    - `action_recommendation`: Khuyến nghị học thuật (`Giữ lại`, `Cần theo dõi`, `Khuyến nghị loại bỏ hoặc viết lại`)

---

## 15. Multilingual Survey Translation & i18n Engine (Bản Địa Hóa Đa Ngôn Ngữ)

### `POST /api/surveys/:id/translations/auto-translate`
- **Mô tả:** Tự động dịch toàn bộ tiêu đề, mô tả, chỉ dẫn nghiên cứu và danh sách câu hỏi/phương án sang ngôn ngữ đích (mặc định: `target_lang=en`) dựa trên Từ điển khảo sát học thuật chuyên sâu (Likert CSAT, tần suất, nhân khẩu học).
- **Lưu trữ:** Lưu trực tiếp vào cấu hình `settings_json.translations[target_lang]` của khảo sát và ghi nhận vào Sổ cái kiểm toán SHA-256 bất biến.
- **Query Params:** `?target_lang=en`
- **Response:** `200 OK` (Bản dịch JSON đầy đủ)

### `GET /api/surveys/:id/translations`
- **Mô tả:** Lấy danh sách toàn bộ các ngôn ngữ khả dụng và nội dung bản dịch đã lưu của cuộc khảo sát.
- **Response:** `200 OK` (`{"survey_id": "...", "available_languages": ["vi", "en"], "translations": {...}}`)

### `PUT /api/surveys/:id/translations/:lang`
- **Mô tả:** Cập nhật thủ công hoặc tinh chỉnh nội dung bản dịch cho một ngôn ngữ cụ thể (`lang`), ghi vết audit log.
- **Request Body:** JSON cấu trúc bản dịch `{ "title": "...", "description": "...", "instructions": "...", "questions": {...} }`
- **Response:** `200 OK`

### `GET /api/public/surveys/:slug_or_id?lang=:lang`
- **Mô tả:** Tải biểu mẫu khảo sát công khai theo ngôn ngữ chỉ định. Nếu `lang != "vi"` và tồn tại bản dịch, tự động trả về tiêu đề, chỉ dẫn và danh sách câu hỏi/lựa chọn đã được bản địa hóa.
- **Phản hồi:** Trả về kèm danh sách `available_languages` và `current_language` giúp giao diện người dùng hiển thị bộ chuyển đổi ngôn ngữ 1-click.

---

## 16. Cognitive Burden & Inattention Pacing Engine (Gánh Nặng Nhận Thức & Nhịp Độ Trả Lời)

### `GET /api/surveys/:id/analytics/cognitive-pacing`
- **Mô tả:** Phân tích gánh nặng nhận thức và nhịp độ trả lời theo mô hình Couper et al. (2001), Krosnick (1991), Tourangeau & Yan (2008) và Don Dillman (2014).
- **Mục đích:**
  - Đo lường dung lượng từ ngữ (Word Count) và thời gian đọc lý thuyết tối thiểu ($E[T]$).
  - So sánh thời gian thực tế với thời gian lý thuyết qua Tỷ số nhịp độ (Pacing Ratio = Actual / Expected).
  - Phân loại 4 nhóm hành vi nhận thức người trả lời: Severe Speeding (< 0.30x), Rushed (0.30x – 0.65x), Optimal (0.65x – 1.80x), Deliberate/Distracted (> 1.80x).
  - Tính điểm gánh nặng nhận thức từng câu hỏi (Cognitive Burden Score 0-100) và phát hiện vi phạm quy luật Miller (7±2 phương án), prompt quá dài (>35 từ), hoặc ma trận phức tạp.
  - Đo lường độ dốc mệt mỏi nhận thức (Fatigue Slope Gradient) qua thứ tự câu hỏi và tự động sinh diễn giải học thuật chuẩn APA 7th Edition.
- **Phản hồi:**
  - `survey_level`:
    - `total_survey_words`, `expected_reading_seconds`, `expected_reading_minutes`
    - `actual_sample_size`, `actual_median_seconds`, `actual_mean_seconds`
    - `overall_pacing_ratio`, `engagement_level`, `engagement_desc`
    - `respondent_pacing_distribution`: Phân bố số lượng phản hồi theo 4 phân tầng
    - `average_question_burden`, `high_burden_questions_count`
    - `fatigue_slope`, `fatigue_risk`, `fatigue_note`
    - `apa_interpretation`: Đoạn văn mẫu APA 7th Edition
  - `question_analyses`: Danh sách phân tích chi tiết từng câu hỏi (title_words, num_options, cognitive_burden_score, burden_tier, risk_factors, redesign_recommendation chuẩn Don Dillman).

## 17. Multivariate Outlier & Mahalanobis Distance Detection Engine (Dị Biệt Đa Biến)

### `GET /api/surveys/:id/analytics/multivariate-outliers`
- **Mô tả:** Phân tích điểm dị biệt đa biến (Multivariate Outlier Detection) bằng khoảng cách Mahalanobis bình phương ($D_M^2$) và phân phối Chi-Square ($\chi^2$).
- **Cơ sở phương pháp luận:**
  - Mahalanobis, P. C. (1936). On the generalised distance in statistics.
  - Rousseeuw, P. J., & Van Zomeren, B. C. (1990). Unmasking multivariate outliers and leverage points. JASA.
  - Tabachnick, B. G., & Fidell, L. S. (2019). Using Multivariate Statistics. Pearson (7th Edition).
- **Tham số Query:**
  - `scope`: `all` (toàn bộ phản hồi) hoặc `verified_clean` (chỉ xét phản hồi hợp lệ). Mặc định `all`.
  - `question_ids`: Chuỗi ID các câu hỏi thang đo cách nhau bằng dấu phẩy (tùy chọn). Mặc định tự động nhận diện tất cả câu hỏi dạng rating, scale, NPS, likert hoặc single_choice có thang điểm.
- **Thuật toán & Kỹ thuật:**
  - Đảo ma trận hiệp phương sai mẫu $\mathbf{\Sigma}^{-1}$ bằng phương pháp khử Gauss-Jordan với chọn phần tử trụ tối đại (Pivoting).
  - Tự động bổ sung Ridge Regularization $\lambda = \max(10^{-4}, 0.01 \cdot \text{trace}(\mathbf{\Sigma})/p)$ để bảo vệ ma trận chống suy biến do hiện tượng cộng tuyến cao (Collinearity Protection).
  - Tính toán chính xác giá trị $p$-value bằng hàm Gamma không đầy đủ chính quy hóa (Regularized Lower Incomplete Gamma) kết hợp khai triển chuỗi Taylor và liên phân số (Continued Fraction).
  - Phân loại 3 cấp độ dị biệt: *Normal Multivariate Range* ($p \ge 0.01$), *Moderate Outlier* ($0.001 \le p < 0.01$), và *Extreme Anomaly* ($p < 0.001$).
- **Phản hồi:**
  - `status`: `SUCCESS` | `INSUFFICIENT_SAMPLE` | `INSUFFICIENT_VARIABLES` | `SINGULAR_MATRIX`.
  - `sample_size`, `degrees_of_freedom`, `scale_variables_count`.
  - `scale_variable_ids`, `scale_variable_titles`.
  - `mean_d2`, `median_d2`, `max_d2`, `critical_chi2_001`.
  - `total_outliers_count`, `extreme_outliers_count`, `moderate_outliers_count`, `outlier_rate_pct`.
  - `apa_interpretation`: Văn bản diễn giải chuẩn mực học thuật theo APA 7th Edition.
  - `outliers_summary`: Danh sách top 25 phản hồi có khoảng cách $D_M^2$ dị biệt nhất kèm vector câu trả lời thực tế $\mathbf{x}_i$.

## 18. Exploratory Factor Analysis (EFA) & Scree Plot Dimension Reduction Engine

### `GET /api/surveys/:id/analytics/efa`
- **Mô tả:** Phân tích Nhân tố Khám phá (Exploratory Factor Analysis - EFA) và Rút gọn Thứ nguyên dữ liệu khảo sát.
- **Cơ sở phương pháp luận:**
  - Kaiser, H. F. (1974). An index of factorial simplicity. Psychometrika.
  - Bartlett, M. S. (1950). Tests of significance in factor analysis. British Journal of Psychology.
  - Cattell, R. B. (1966). The scree test for the number of factors. Multivariate Behavioral Research.
  - Kaiser, H. F. (1958). The varimax criterion for analytic rotation in factor analysis. Psychometrika.
  - Hair, J. F., et al. (2010). Multivariate Data Analysis. Pearson (7th Edition).
- **Tham số Query:**
  - `scope`: `all` (toàn bộ phản hồi) hoặc `verified_clean` (chỉ xét phản hồi hợp lệ). Mặc định `all`.
  - `rotation`: `varimax` (xoay trực giao Varimax chuẩn hóa Kaiser) hoặc `none` (chưa xoay). Mặc định `varimax`.
  - `min_eigenvalue`: Ngưỡng trị riêng Kaiser trích xuất nhân tố (mặc định `1.0`).
  - `forced_factors`: Số lượng nhân tố chỉ định cố định (tùy chọn).
  - `question_ids`: Chuỗi ID các câu hỏi thang đo cách nhau bằng dấu phẩy (tùy chọn).
- **Quy trình Thuật toán:**
  - Kiểm định KMO (Kaiser-Meyer-Olkin) toàn diện và đo lường độ thích hợp mẫu từng biến ($MSA_j$) qua ma trận tương quan riêng Anti-image ($Q$).
  - Kiểm định Bartlett's Test of Sphericity: $\chi^2 = - \left(N - 1 - \frac{2p+5}{6}\right) \ln(\det(\mathbf{R}))$, với $df = \frac{p(p-1)}{2}$.
  - Phân rã trị riêng chính xác bằng Thuật toán Jacobi Eigenvalue Decomposition trên ma trận tương quan $\mathbf{R}$ thực đối xứng.
  - Phép xoay trực giao Varimax lặp 2 chiều planar Jacobi rotation tối đa hóa phương sai hệ số tải.
  - Tính toán độ chung (Communalities $h_j^2$) và gán nhân tố chính (Primary Factor).
  - Sinh đoạn diễn giải khoa học chuẩn mực APA 7th Edition.
- **Phản hồi:**
  - `status`: `SUCCESS` | `INSUFFICIENT_SAMPLE` | `INSUFFICIENT_VARIABLES` | `ERROR`.
  - `sample_size`, `variables_count`, `variable_ids`, `scale_variable_titles`.
  - `kmo_overall`, `kmo_verdict`, `is_kmo_acceptable`.
  - `bartlett_chi2`, `bartlett_df`, `bartlett_p_value`, `is_bartlett_significant`.
  - `factors_extracted_count`, `rotation_method`, `cumulative_variance_extracted_pct`, `is_variance_sufficient`.
  - `eigenvalue_stats`: Bảng trị riêng, % phương sai, % phương sai tích lũy, và cờ trích xuất Kaiser.
  - `scree_plot_data`: Tập điểm tọa độ vẽ biểu đồ Scree Plot (Cattell 1966) kèm đường ngưỡng Kaiser $\lambda = 1.0$.
  - `factors`: Tên các nhân tố trích xuất.
  - `rotated_factor_variance`: Bảng phương sai giải thích của từng nhân tố sau xoay.
  - `items`: Danh sách biến quan sát kèm $MSA_j$, độ chung $h^2$, vector hệ số tải $\mathbf{\lambda}_j$, và cờ đạt chuẩn theo Hair et al. ($\ge 0.50$).
  - `weak_loadings_count`, `low_communalities_count`.
  - `apa_interpretation`: Đoạn văn bản mẫu APA 7th Edition.

## 19. Hypothesis Testing T-Test Engine (Kiểm Định Giả Thuyết & Kích Thước Hiệu Ứng)

### `POST /api/surveys/:id/analytics/ttest/independent`
- **Mô tả:** Kiểm định T-Test 2 nhóm độc lập (Independent Samples T-Test). So sánh sự khác biệt điểm số giữa 2 nhóm đối tượng (ví dụ: Nam vs Nữ, Thực nghiệm vs Đối chứng).
- **Cơ sở phương pháp luận:**
  - Student (1908), Welch (1947), Levene (1960), Brown & Forsythe (1974), Cohen (1988), Hedges (1981).
- **Yêu cầu Body:**
  ```json
  {
    "grouping_question_id": "string",
    "group1_value": "string",
    "group2_value": "string",
    "target_question_id": "string",
    "scope": "all" // hoặc "verified_clean"
  }
  ```
- **Thuật toán & Kỹ thuật:**
  - Kiểm định tính đồng nhất phương sai Levene (Brown-Forsythe biến thể trung vị chống nhiễu ngoại lai) với thống kê $F$ và $p$-value vi phân chính xác.
  - Tự động quyết định phương pháp tối ưu:
    - Nếu phương sai đồng nhất ($p \ge 0.05$): Áp dụng Student's $t$-test với phương sai gộp $S_p^2$ và bậc tự do $df = n_1 + n_2 - 2$.
    - Nếu phương sai không đồng nhất ($p < 0.05$): Áp dụng Welch's $t$-test với hiệu chỉnh Welch-Satterthwaite degrees of freedom ($\nu$).
  - Tính toán kích thước hiệu ứng chuẩn mực: Cohen's $d = \frac{\bar{x}_1 - \bar{x}_2}{S_p}$ và Hedges' $g$ (hiệu chỉnh mẫu nhỏ).
  - Ước lượng khoảng tin cậy 95% cho chênh lệch trung bình $[\Delta M \pm t_{\text{crit}} \cdot SE]$.
  - Tự động xuất báo cáo học thuật chuẩn mực theo format APA 7th Edition.

### `POST /api/surveys/:id/analytics/ttest/paired`
- **Mô tả:** Kiểm định T-Test mẫu ghép cặp / phụ thuộc (Paired Samples T-Test). So sánh sự thay đổi trước và sau can thiệp (Pre vs Post) trên cùng một tập đối tượng khảo sát.
- **Yêu cầu Body:**
  ```json
  {
    "pre_question_id": "string",
    "post_question_id": "string",
    "scope": "all" // hoặc "verified_clean"
  }
  ```
- **Thuật toán & Kỹ thuật:**
  - Ghép cặp từng quan sát $(x_{1i}, x_{2i})$, tính chuỗi chênh lệch $d_i = x_{1i} - x_{2i}$.
  - Tính hệ số tương quan Pearson $r_{12}$ giữa 2 lần đo.
  - Tính thống kê $t = \frac{\bar{d}}{S_d / \sqrt{N}}$ với bậc tự do $df = N - 1$.
  - Tính kích thước hiệu ứng Cohen's $d_z = \frac{\bar{d}}{S_d}$ và Hedges' $g_z$.
  - Khoảng tin cậy 95% của chênh lệch trung bình và đoạn diễn giải APA 7th Edition.

## 20. One-Way ANOVA & Post-Hoc Tukey HSD Engine (Phân Tích Phương Sai & So Sánh Cặp Hậu Nghiệm)

### `POST /api/surveys/:id/analytics/anova`
- **Mô tả:** Phân tích phương sai một chiều (One-Way Analysis of Variance - ANOVA) kiểm định sự khác biệt giá trị trung bình giữa $K \ge 3$ nhóm đối tượng phân loại, kết hợp kiểm định tính đồng nhất phương sai Levene, tính toán kích thước hiệu ứng Eta-squared ($\eta^2$), Omega-squared ($\omega^2$), và kiểm định so sánh cặp hậu nghiệm Tukey-Kramer HSD.
- **Cơ sở phương pháp luận:**
  - Fisher, R. A. (1925). Statistical Methods for Research Workers.
  - Tukey, J. W. (1949). Comparing individual means in the analysis of variance. Biometrics.
  - Kramer, C. Y. (1956). Extension of multiple range tests to group means with unequal numbers of replications. Biometrics.
  - Levene, H. (1960). Robust tests for equality of variances.
  - Olejnik, S., & Algina, J. (2003). Generalized eta and omega squared statistics. Psychological Methods.
- **Yêu cầu Body:**
  ```json
  {
    "grouping_question_id": "string",
    "target_question_id": "string",
    "scope": "all" // hoặc "verified_clean"
  }
  ```
- **Thuật toán & Quy trình Tính toán:**
  1. **Thống kê mô tả từng nhóm:** Tính $N_k, \bar{X}_k, SD_k, Mdn_k, SE_k$, và khoảng tin cậy 95% $CI = [\bar{X}_k \pm 1.96 \cdot SE_k]$.
  2. **Kiểm định tính đồng nhất phương sai Levene (Brown-Forsythe Medians):**
     $$Z_{ki} = |X_{ki} - \tilde{X}_k|$$
     Tính biến thiên giữa và trong nhóm của $Z$ để suy ra thống kê Fisher $F_{\text{Levene}}$ và $p$-value vi phân chính xác.
  3. **Bảng Phân tích Phương sai Tổng quát (Omnibus ANOVA Table):**
     - $SS_{\text{between}} = \sum_{k=1}^K n_k (\bar{X}_k - \bar{X})^2, \quad df_{\text{between}} = K - 1$
     - $SS_{\text{within}} = \sum_{k=1}^K \sum_{i=1}^{n_k} (X_{ki} - \bar{X}_k)^2, \quad df_{\text{within}} = N - K$
     - $MS_{\text{between}} = \frac{SS_{\text{between}}}{df_{\text{between}}}, \quad MS_{\text{within}} = \frac{SS_{\text{within}}}{df_{\text{within}}}$
     - $F = \frac{MS_{\text{between}}}{MS_{\text{within}}}, \quad p = I_{\frac{df_2}{df_2 + df_1 F}}\left(\frac{df_2}{2}, \frac{df_1}{2}\right)$
  4. **Kích thước Hiệu ứng Chuẩn mực:**
     - $\eta^2 = \frac{SS_{\text{between}}}{SS_{\text{total}}}$ (Độ lớn hiệu ứng theo chuẩn Cohen: Nhỏ < .06, Trung bình .06 - .14, Lớn > .14)
     - $\omega^2 = \frac{SS_{\text{between}} - df_{\text{between}} \cdot MS_{\text{within}}}{SS_{\text{total}} + MS_{\text{within}}}$ (Ước lượng không thiên lệch cho mẫu hữu hạn).
  5. **Kiểm định Hậu nghiệm Tukey-Kramer HSD ($K(K-1)/2$ cặp):**
     $$SE_{\text{Tukey}} = \sqrt{\frac{MS_{\text{within}}}{2} \left(\frac{1}{n_1} + \frac{1}{n_2}\right)}, \quad q = \frac{|\bar{X}_1 - \bar{X}_2|}{SE_{\text{Tukey}}}$$
     So sánh $q$ với giá trị tới hạn Studentized Range $q_{\text{crit}}(\alpha = .05, K, df_{\text{within}})$. Thiết lập khoảng tin cậy 95% và cờ ý nghĩa thống kê cho từng cặp.
  6. **Diễn giải học thuật APA 7th Edition:** Tự động tổng hợp kết quả $F(df_1, df_2)$, $p$-value, $\eta^2$, $\omega^2$, và các cặp khác biệt hậu nghiệm có ý nghĩa.

## 21. Bivariate Correlation Analysis Suite (Ma Trận Tương Quan Đôi & Heatmap Trực Quan)

### `GET /api/surveys/:id/analytics/correlation`
- **Mô tả:** Phân tích ma trận tương quan đôi giữa tất cả các biến thang đo định lượng (hoặc tập biến được chỉ định), hỗ trợ hệ số tương quan tuyến tính Pearson ($r$) và hệ số tương quan thứ bậc phi tham số Spearman ($\rho$). Bao gồm kiểm định ý nghĩa thống kê 2 phía, khoảng tin cậy 95% chuyển đổi Fisher $z$, và sàng lọc nguy cơ đa cộng tuyến ($|r| \ge .85$).
- **Cơ sở phương pháp luận:**
  - Pearson, K. (1895). Notes on regression and inheritance in the case of two parents.
  - Spearman, C. (1904). The proof and measurement of association between two things.
  - Fisher, R. A. (1915). Frequency distribution of the values of the correlation coefficient.
  - Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences.
  - Tabachnick, B. G., & Fidell, L. S. (2019). Using Multivariate Statistics (7th ed.).
- **Query Parameters:**
  - `method`: `"pearson"` (mặc định) hoặc `"spearman"`.
  - `scope`: `"all"` (mặc định) hoặc `"verified_clean"`.
  - `question_ids`: Chuỗi ID các câu hỏi dạng phẩy cách (tùy chọn, nếu bỏ trống hệ thống tự phát hiện toàn bộ câu hỏi thang đo).
- **Thuật toán & Quy trình Tính toán:**
  1. **Hệ số tương quan Pearson $r$:**
     $$r = \frac{\sum_{i=1}^N (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^N (x_i - \bar{x})^2 \sum_{i=1}^N (y_i - \bar{y})^2}}$$
  2. **Hệ số tương quan thứ bậc Spearman $\rho$:**
     - Xếp hạng thập phân các quan sát ($ranks_x, ranks_y$) kèm xử lý hòa thứ bậc (ties).
     - Tính Pearson $r$ trên chuỗi hạng (công thức chính xác kể cả khi có giá trị trùng lặp).
  3. **Kiểm định ý nghĩa thống kê 2 phía (Two-Tailed $p$-value):**
     $$t = r \sqrt{\frac{N - 2}{1 - r^2}}, \quad df = N - 2$$
     Sử dụng hàm liên phân số Beta không đầy đủ chính quy hóa để tính chính xác xác suất vi phân $p$.
  4. **Khoảng tin cậy 95% qua chuyển đổi Fisher $z$:**
     $$z = \frac{1}{2} \ln \left(\frac{1 + r}{1 - r}\right), \quad SE_z = \frac{1}{\sqrt{N - 3}}, \quad z \pm 1.96 \cdot SE_z \to CI = \tanh(z)$$
  5. **Sàng lọc Đa cộng tuyến (Multicollinearity Screening):**
     Phát hiện các cặp có $|r| \ge 0.85$ (Tabachnick & Fidell, 2019) cảnh báo rủi ro cho các mô hình hồi quy đa biến OLS/SEM.
  6. **Diễn giải học thuật APA 7th Edition:**
     Tự động tổng hợp cặp tương quan cao nhất, tỷ lệ cặp đạt ý nghĩa ($p < .05$), và đánh giá rủi ro đa cộng tuyến.

## 22. Multiple Linear Regression OLS & Multicollinearity VIF Engine (Hồi Quy Tuyến Tính Đa Biến & VIF)

### `POST /api/surveys/:id/analytics/regression`
- **Mô tả:** Khớp mô hình hồi quy tuyến tính đa biến OLS (Ordinary Least Squares) dự báo giá trị của một biến phụ thuộc liên tục ($Y$) từ tập hợp các biến độc lập dự báo ($X_1, X_2, \dots, X_p$). Tự động tính toán kiểm định Omnibus $F$-test, bảng ANOVA mô hình, hệ số chưa chuẩn hóa $B$, sai số chuẩn $SE_B$, hệ số chuẩn hóa Beta ($\beta$), thống kê $t$ và $p$-value, khoảng tin cậy 95%, chỉ số phóng đại phương sai (VIF - Variance Inflation Factor), độ chấp nhận (Tolerance), và đoạn diễn giải học thuật APA 7th Edition.
- **Cơ sở phương pháp luận:**
  - Legendre, A. M. (1805) & Gauss, C. F. (1809) (Bình phương Cực tiểu OLS).
  - Hair, J. F., Black, W. C., Babin, B. J., & Anderson, R. E. (2010). Multivariate Data Analysis.
  - Kline, R. B. (2015). Principles and Practice of Structural Equation Modeling.
  - Cohen, J., Cohen, P., West, S. G., & Aiken, L. S. (2003). Applied Multiple Regression/Correlation Analysis.
- **Yêu cầu Body:**
  ```json
  {
    "dependent_question_id": "string",
    "predictor_question_ids": ["string", "string"],
    "scope": "all" // hoặc "verified_clean"
  }
  ```
- **Thuật toán & Quy trình Tính toán:**
  1. **Thiết lập Ma trận và Ước lượng Tham số OLS:**
     - Thiết lập ma trận $\mathbf{X}$ kích thước $N \times (p + 1)$ (với cột hằng số $\mathbf{1}$) và vector $\mathbf{Y}$.
     - Giải hệ phương trình chuẩn tắc: $\mathbf{\beta} = (\mathbf{X}^T \mathbf{X})^{-1} \mathbf{X}^T \mathbf{Y}$ bằng thuật toán khử Gauss-Jordan kèm partial pivoting và ổn định hóa Ridge ($\lambda = 10^{-7}$).
  2. **Độ phù hợp của Mô hình (Model Fit):**
     - $SS_{\text{tot}} = \sum (y_i - \bar{y})^2, \quad SS_{\text{res}} = \sum (y_i - \hat{y}_i)^2, \quad SS_{\text{reg}} = SS_{\text{tot}} - SS_{\text{res}}$
     - $R^2 = 1 - \frac{SS_{\text{res}}}{SS_{\text{tot}}}, \quad R^2_{\text{adj}} = 1 - (1 - R^2) \frac{N - 1}{N - p - 1}$
     - $F = \frac{SS_{\text{reg}} / p}{SS_{\text{res}} / (N - p - 1)}, \quad p = I_{\frac{df_2}{df_2 + df_1 F}}\left(\frac{df_2}{2}, \frac{df_1}{2}\right)$
     - Sai số chuẩn ước lượng: $S_e = \sqrt{MS_{\text{res}}}$.
  3. **Hệ số Hồi quy & Kiểm định Giả thuyết Từng Biến:**
     - Sai số chuẩn hệ số: $SE(B_j) = \sqrt{MS_{\text{res}} \cdot [(\mathbf{X}^T \mathbf{X})^{-1}]_{jj}}$
     - Thống kê $t = \frac{B_j}{SE(B_j)}, \quad p$-value 2 phía qua phân phối Student's $t$ ($df = N - p - 1$).
     - Hệ số chuẩn hóa: $\beta_j = B_j \cdot \frac{SD(X_j)}{SD(Y)}$.
     - Khoảng tin cậy 95%: $[B_j \pm 1.96 \cdot SE(B_j)]$.
  4. **Chẩn đoán Đa cộng tuyến (VIF & Tolerance):**
     - Thực hiện hồi quy phụ từng biến độc lập $X_j$ theo $p - 1$ biến độc lập còn lại để suy ra $R_j^2$.
     - $\text{Tolerance}_j = 1 - R_j^2, \quad VIF_j = \frac{1}{\text{Tolerance}_j}$
     - Phân loại rủi ro: $VIF < 5$ (Thấp / Đạt chuẩn), $5 \le VIF < 10$ (Trung bình), $VIF \ge 10$ (Cao / Vi phạm nghiêm trọng).
  5. **Báo cáo Diễn giải Học thuật APA 7th Edition:**
     Tự động xuất báo cáo $F(p, N - p - 1) = \dots, p = \dots, R^2 = \dots, R^2_{\text{adj}} = \dots$, danh sách các biến dự báo có ý nghĩa thống kê theo thứ tự độ lớn Beta $\beta$, và kết luận chẩn đoán đa cộng tuyến VIF.

## 23. Survey Logic & Branching Directed Acyclic Graph (DAG) Engine

### `GET /api/surveys/:id/logic/validate`
- **Mô tả:** Phân tích cấu trúc đồ thị luồng khảo sát (Survey Flow Graph $G = (V, E)$), tự động phát hiện các lỗi thiết kế logic phân nhánh trước khi phát hành theo chuẩn phương pháp luận Don Dillman và Groves et al.
- **Cơ sở phương pháp luận:**
  - Dillman, D. A., Smyth, J. D., & Christian, L. M. (2014). Internet, Phone, Mail, and Mixed-Mode Surveys: The Tailored Design Method.
  - Groves, R. M. et al. (2009). Survey Methodology.
  - Tarjan, R. E. (1972). Depth-first search and linear graph algorithms.
  - McCabe, T. J. (1976). A Complexity Measure. IEEE Transactions on Software Engineering.
- **Quy trình Kiểm định & Thuật toán:**
  1. **Phát hiện Vòng lặp Luẩn quẩn (Deadly Cycles):**
     Sử dụng thuật toán DFS 3 trạng thái màu (White = chưa duyệt, Gray = đang trong ngăn xếp đệ quy, Black = đã duyệt xong) để phát hiện chu trình phụ thuộc khép kín ($q_1 \to q_2 \dots \to q_1$) làm treo khảo sát.
  2. **Phát hiện Tham chiếu Gãy (Dangling References):**
     Quét toàn bộ các quy tắc rẽ nhánh trỏ vào `question_id` không tồn tại hoặc đã bị xóa.
  3. **Phát hiện Nghịch đảo Trật tự Thời gian (Causal Inversion):**
     Kiểm tra các câu hỏi phụ thuộc vào câu hỏi xuất hiện sau trong bảng câu hỏi ($order(dep) \ge order(current)$).
  4. **Phát hiện Câu hỏi Mồ côi / Không Thể Tiếp Cận (Unreachable Traps):**
     Phân tích tính tiếp cận (Reachability Graph) từ câu hỏi gốc ($q_0$) để tìm các câu hỏi không bao giờ được hiển thị trong bất kỳ kịch bản nào.
  5. **Kiểm tra Mâu thuẫn Điều kiện Nội tại (Contradictory Rules):**
     Phát hiện các quy tắc cùng `action: show` nhưng yêu cầu các giá trị mutually exclusive từ cùng một câu hỏi phụ thuộc.
  6. **Độ phức tạp Nhánh McCabe Cyclomatic Complexity:**
     $$M = E - V + 2P$$
     Đo lường số lượng đường đi độc lập tuyến tính qua bảng câu hỏi.
  7. **Liệt kê Lộ trình Khảo sát Khả dĩ (Path Enumeration):**
     Tự động trích xuất các kịch bản trải nghiệm người dùng mẫu qua bảng câu hỏi (Lộ trình tiêu chuẩn, Lộ trình rẽ nhánh theo từng điều kiện).
  8. **Điểm Sức Khỏe Logic (Logic Health Score: 0 - 100):**
     Phân loại trạng thái hệ thống: `OPTIMAL`, `WARNING`, `CRITICAL`.

### `POST /api/surveys/:id/logic/simulate`
- **Mô tả:** Mô phỏng trải nghiệm thực tế của người trả lời qua bảng câu hỏi dựa trên các câu trả lời giả định được cung cấp trong thời gian thực.
- **Yêu cầu Body:**
  ```json
  {
    "answers": {
      "question_id_1": "Có",
      "question_id_2": "Windows"
    }
  }
  ```
- **Kết quả trả về:**
  - `total_questions`: Tổng số câu hỏi trong khảo sát.
  - `visible_count`: Số lượng câu hỏi hiển thị.
  - `hidden_count`: Số lượng câu hỏi bị ẩn / bỏ qua.
  - `visible_questions`: Danh sách ID các câu hỏi hiển thị.
  - `hidden_questions`: Danh sách ID các câu hỏi bị ẩn.
  - `skipped_reasons`: Từ điển giải thích lý do từng câu hỏi bị ẩn (VD: "Ẩn do điều kiện trên câu hỏi 'Laptop' không thỏa mãn").
  - `completion_ratio`: Tỷ lệ phần trăm câu hỏi người dùng trải qua so với toàn bộ bảng hỏi.

## 24. Statistical Power Analysis & Sample Size Estimator Engine (Lực Thống Kê & Ước Lượng Cỡ Mẫu)

### `POST /api/surveys/:id/analytics/power-analysis`
- **Mô tả:** Đánh giá độ nhạy và lực kiểm định thống kê Post-Hoc ($1 - \beta$) trên tập mẫu thực tế đã thu thập của khảo sát, ước tính cỡ mẫu tối thiểu theo công thức Cochran (1977) với hiệu chỉnh tổng thể hữu hạn (Finite Population Correction - FPC), tính toán cỡ mẫu cho T-Test 2 nhóm (Cohen's $d$) và tương quan Pearson ($r$), tạo dữ liệu vẽ đường cong Lực thống kê SVG (Power Curve), và tự động soạn thảo đoạn văn bản trích dẫn học thuật chuẩn APA 7th Edition.
- **Cơ sở phương pháp luận:**
  - Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences (2nd ed.). Lawrence Erlbaum Associates.
  - Cochran, W. G. (1977). Sampling Techniques (3rd ed.). John Wiley & Sons.
  - Yamane, T. (1967). Statistics: An Introductory Analysis (2nd ed.). Harper and Row.
  - Faul, F., Erdfelder, E., Lang, A. G., & Buchner, A. (2007). G*Power 3: A flexible statistical power analysis program.
  - Chow, S. C., Shao, J., & Wang, H. (2008). Sample Size Calculations in Clinical Research.
- **Yêu cầu Body:**
  ```json
  {
    "analysis_type": "ttest", // "ttest" hoặc "correlation"
    "confidence_level": 0.95, // 0.90, 0.95, 0.99
    "margin_of_error": 0.05, // e.g. 0.03, 0.05, 0.08
    "population_size": 1000, // Tùy chọn: quy mô dân số (FPC)
    "effect_size": 0.50, // Cohen's d hoặc Pearson r
    "target_power": 0.80, // Mặc định 0.80 (chuển Cohen)
    "alpha": 0.05, // Mức ý nghĩa thống kê
    "scope": "verified_clean" // "all" hoặc "verified_clean"
  }
  ```
- **Thuật toán & Quy trình Tính toán:**
  1. **Công thức Cỡ mẫu Tỷ lệ Cochran & Yamane (FPC):**
     $$n_0 = \frac{Z_{1 - \alpha/2}^2 \cdot p(1 - p)}{e^2}, \quad n_{\text{adj}} = \frac{n_0}{1 + \frac{n_0 - 1}{N_{\text{pop}}}}$$
  2. **Lực kiểm định T-Test 2 Nhóm Độc lập (Cohen 1988):**
     $$\delta = |d| \sqrt{\frac{n_{\text{group}}}{2}}, \quad Z_{\beta} = \delta - Z_{1 - \alpha/2}, \quad \text{Power} = \Phi(Z_{\beta})$$
     $$n_{\text{per\_group}} = 2 \left(\frac{Z_{1 - \alpha/2} + Z_{1 - \beta}}{d}\right)^2$$
  3. **Lực kiểm định Tương quan Pearson $r$ (Fisher $z$):**
     $$Z_r = \frac{1}{2} \ln \left(\frac{1 + |r|}{1 - |r|}\right), \quad \delta = Z_r \sqrt{N - 3}, \quad Z_{\beta} = \delta - Z_{1 - \alpha/2}, \quad \text{Power} = \Phi(Z_{\beta})$$
  4. **Biên độ sai số thực tế đạt được ở 95% Confidence Level:**
     $$e_{\text{achieved}} = 1.96 \cdot \sqrt{\frac{0.25}{N_{\text{realized}}}}$$
  5. **Phân hạng Độ thỏa đáng Cỡ mẫu:**
     - `ADEQUATE` (Đủ lực thống kê $\ge 80\%$ cho Medium Effect).
     - `MODERATE` (Đạt $\ge 80\%$ cho Large Effect nhưng $< 80\%$ cho Medium).
     - `UNDERPOWERED` ($< 80\%$ cho cả hiệu ứng trung bình và lớn).
  6. **Đoạn Trích dẫn APA 7th Edition Tự động:**
     Xuất chuẩn trích dẫn báo cáo đề tài, luận văn, hoặc kỷ yếu hội thảo.

## 25. Split-Ballot & Question Wording Experimentation Engine (Thử Nghiệm Tách Phiếu A/B & Hiệu Ứng Đóng Khung Từ Ngữ)

### `POST /api/surveys/:id/analytics/split-ballot`
- **Mô tả:** Phân tích thử nghiệm tách phiếu ngẫu nhiên (Split-Ballot Survey Experiment) nhúng trong cùng một cuộc khảo sát. So sánh tỷ lệ hoàn thành, phân phối phương án, mức độ sai biệt điểm số giữa các nhánh A/B (Welch's T-Test hoặc Pearson Chi-Square), tính toán Khoảng cách biến thiên toàn phần (Total Variation Distance - TVD), và tính Chỉ số Biến Dạng Từ Ngữ (Manipulated Wording Distortion Index - MWDI).
- **Cơ sở phương pháp luận:**
  - Schuman, H., & Presser, S. (1981). Questions and Answers in Attitude Surveys: Experiments on Question Form, Wording, and Context. Academic Press.
  - Tourangeau, R., Rips, L. J., & Rasinski, K. (2000). The Psychology of Survey Response. Cambridge University Press.
  - Welch, B. L. (1947). The generalization of 'Student's' problem when several different population variances are involved.
  - Cramér, H. (1946). Mathematical Methods of Statistics. Princeton University Press.
- **Yêu cầu Body:**
  ```json
  {
    "question_id": "string",
    "scope": "verified_clean" // hoặc "all"
  }
  ```
- **Thuật toán & Quy trình Tính toán:**
  1. **Phân bổ Nhánh Ngẫu nhiên Xác định (Deterministic Hash Assignment):**
     $$\text{hash\_val} = \text{MD5}(\text{survey\_id} + \text{salt} + \text{client\_seed}), \quad \text{arm} = \text{arm\_keys}[\text{hash\_val} \pmod K]$$
  2. **So sánh Thang đo Định lượng (Welch's Independent Samples T-Test):**
     $$t = \frac{\bar{X}_A - \bar{X}_B}{\sqrt{\frac{s_A^2}{N_A} + \frac{s_B^2}{N_B}}}, \quad df \approx \frac{\left(\frac{s_A^2}{N_A} + \frac{s_B^2}{N_B}\right)^2}{\frac{(s_A^2/N_A)^2}{N_A - 1} + \frac{(s_B^2/N_B)^2}{N_B - 1}}, \quad d = \frac{\bar{X}_A - \bar{X}_B}{s_{\text{pooled}}}$$
  3. **So sánh Phân loại Định tính (Chi-Square & Total Variation Distance):**
     $$\chi^2 = \sum \frac{(O_{ij} - E_{ij})^2}{E_{ij}}, \quad V = \sqrt{\frac{\chi^2}{N \min(R-1, C-1)}}, \quad \text{TVD} = \frac{1}{2} \sum_{k} |p_{A, k} - p_{B, k}|$$
  4. **Chỉ số Biến Dạng Từ Ngữ (Manipulated Wording Distortion Index - MWDI):**
     - $MWDI \in [0, 1]$.
     - `FRAME_ROBUST` ($MWDI < 0.12$): Kháng đóng khung, ý kiến ổn định.
     - `MODERATELY_SENSITIVE` ($0.12 \le MWDI < 0.28$): Nhạy cảm vừa phải.
     - `HIGHLY_PLASTIC` ($MWDI \ge 0.28$): Tính dẻo cao, cách hành văn gây thiên lệch nghiêm trọng.
  5. **Báo cáo Diễn giải APA 7th Edition Tự động.**

## 26. Rasch Model 1-PL & Wright Map Calibration Engine (Mô Hình Đo Lường Tâm Trắc Học Rasch 1-PL & Bản Đồ Wright Map)

### `POST /api/surveys/:id/analytics/rasch`
### `GET /api/surveys/:id/analytics/rasch`
- **Mô tả:** Hiệu chuẩn mô hình đo lường tâm trắc học Rasch 1-PL (1-Parameter Logistic Model trong Item Response Theory - IRT). Ước lượng độ khó câu hỏi ($b_i$) và năng lực tiềm ẩn của người trả lời ($\theta_n$) trên cùng một thước đo tuyến tính Logit. Đánh giá chỉ số độ phù hợp Infit MNSQ và Outfit MNSQ theo tiêu chuẩn Wright & Linacre (1994), độ tin cậy phân tách (Item & Person Separation Reliability), và xây dựng trực quan hóa bản đồ Wright Map (Person-Item Map).
- **Cơ sở phương pháp luận:**
  - Rasch, G. (1960). Probabilistic Models for Some Intelligence and Attainment Tests. Danish Institute for Educational Research.
  - Wright, B. D., & Stone, M. H. (1979). Best Test Design. MESA Press.
  - Wright, B. D., & Linacre, J. M. (1994). Reasonable mean-square fit values. Rasch Measurement Transactions, 8(3), 370.
  - Bond, T. G., & Fox, C. M. (2015). Applying the Rasch Model: Fundamental Measurement in the Human Sciences. Routledge.
- **Yêu cầu Body:**
  ```json
  {
    "scope": "verified_clean" // hoặc "all"
  }
  ```
- **Thuật toán & Quy trình Tính toán:**
  1. **Số hóa Ma trận Khảo sát (Dichotomous & Threshold Binarization):**
     Chuyển đổi thang đo Likert/Rating Scale, Yes/No, Boolean sang ma trận nhị phân $X_{ni} \in \{0, 1\}$.
  2. **Ước lượng Tham số bằng Thuật toán PROX & Joint Maximum Likelihood Estimation (JMLE):**
     $$P(X_{ni} = 1 | \theta_n, b_i) = \frac{e^{\theta_n - b_i}}{1 + e^{\theta_n - b_i}}$$
     - PROX Khởi tạo: $b_i^{(0)} = \ln\left(\frac{N - S_i}{S_i}\right), \quad \theta_n^{(0)} = \ln\left(\frac{R_n}{L - R_n}\right)$.
     - Vòng lặp Newton-Raphson JMLE:
       $$\Delta \theta_n = \frac{R_n - \sum_i P_{ni}}{\sum_i P_{ni}(1 - P_{ni})}, \quad \Delta b_i = \frac{\sum_n P_{ni} - S_i}{\sum_n P_{ni}(1 - P_{ni})}$$
     - Ràng buộc chuẩn hóa thang đo gốc: $\sum_{i=1}^L b_i = 0$.
  3. **Thống kê Kiểm định Độ phù hợp Infit & Outfit Mean-Square (MNSQ):**
     $$z_{ni} = \frac{X_{ni} - P_{ni}}{\sqrt{W_{ni}}}, \quad \text{Outfit}_i = \frac{1}{N}\sum_{n=1}^N z_{ni}^2, \quad \text{Infit}_i = \frac{\sum_{n=1}^N (X_{ni} - P_{ni})^2}{\sum_{n=1}^N W_{ni}}$$
     - `OPTIMAL_FIT` ($0.7 \le MNSQ \le 1.3$): Phù hợp tối ưu cho đo lường.
     - `UNDERFIT_NOISY` ($MNSQ > 1.3$): Nhiễu, câu hỏi không nhất quán với cấu trúc thang đo.
     - `OVERFIT_REDUNDANT` ($MNSQ < 0.7$): Dư thừa, phương sai bị gò ép quá mức.
  4. **Bản đồ Wright Map (Person-Item Alignment Map):**
     Phân chia trục logit từ $-3.0$ đến $+3.0$ theo bước $0.5$. Cột trái biểu thị mật độ phân bố năng lực người trả lời $\theta$, cột phải biểu thị vị trí ngưỡng độ khó câu hỏi $b_i$.
  5. **Độ lệch Nhắm mục tiêu (Targeting Gap):**
     $$\text{Gap} = \bar{\theta} - \bar{b} = \bar{\theta} - 0.0$$
  6. **Độ tin cậy Tách biệt & Đoạn Diễn giải APA 7th Edition Tự động.**

## 27. Respondent Clustering & Typology Segmentation Engine (Phân Cụm Người Trả Lời & Phân Khúc Đối Tượng)

### `POST /api/surveys/:id/analytics/clusters`
### `GET /api/surveys/:id/analytics/clusters`
- **Mô tả:** Phân tích phân cụm người trả lời khảo sát thành các phân khúc đối tượng và hồ sơ nhân vật (Personas) dựa trên kỹ thuật học không giám sát K-Means++ và hệ số phân tách Silhouette. Tự động chuẩn hóa ma trận điểm Z-score, đánh giá đường cong khuỷu tay (Elbow WCSS curve) trên các mốc $K = 2 \dots 5$, đo lường mức độ phân hóa câu hỏi bằng tỷ số ANOVA $F$-ratio và $\eta^2$, và tạo dựng bản mô tả chân dung đối tượng tự động.
- **Cơ sở phương pháp luận:**
  - Lloyd, S. (1982). Least squares quantization in PCM. IEEE Transactions on Information Theory.
  - Arthur, D., & Vassilvitskii, S. (2007). K-means++: The advantages of careful seeding. SODA '07.
  - Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. Journal of Computational and Applied Mathematics.
  - Hair, J. F., Black, W. C., Babin, B. J., & Anderson, R. E. (2010). Multivariate Data Analysis.
- **Yêu cầu Body:**
  ```json
  {
    "question_ids": ["string", "string"], // Tùy chọn, mặc định lấy toàn bộ câu hỏi thang đo
    "k": 3, // Tùy chọn: 2, 3, 4, 5. Nếu bỏ trống hệ thống tự chọn K tối ưu theo Silhouette
    "scope": "verified_clean" // hoặc "all"
  }
  ```
- **Thuật toán & Quy trình Tính toán:**
  1. **Chuẩn hóa Z-Score Đa chiều (Standardization):**
     $$z_{ij} = \frac{x_{ij} - \bar{x}_j}{s_j}$$
  2. **Khởi tạo Tâm cụm K-Means++ (Arthur & Vassilvitskii, 2007):**
     Chọn tâm cụm đầu tiên ngẫu nhiên; các tâm tiếp theo chọn với xác suất tỉ lệ với bình phương khoảng cách Euclidean $D(x)^2$ tới tâm cụm gần nhất.
  3. **Lặp Cực tiểu hóa Tổng bình phương Nội cụm (Within-Cluster Sum of Squares - WCSS):**
     $$\text{WCSS} = \sum_{k=1}^K \sum_{i \in C_k} \|z_i - \mu_k\|^2$$
  4. **Đánh giá Hệ số Phân tách Silhouette (Rousseeuw, 1987):**
     $$s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}, \quad s_{\text{overall}} = \frac{1}{N}\sum_{i=1}^N s(i)$$
     - `STRONG_CLUSTERING` ($s \ge 0.45$): Cấu trúc phân cụm rất rõ nét và phân hóa tự nhiên.
     - `ACCEPTABLE_CLUSTERING` ($0.25 \le s < 0.45$): Cấu trúc phân cụm hợp lý.
     - `WEAK_CLUSTERING` ($s < 0.25$): Cấu trúc phân cụm yếu / dữ liệu đồng nhất.
  5. **Mức độ Phân hóa Câu hỏi (ANOVA F-ratio & Eta-Squared):**
     $$F_j = \frac{MS_{\text{between}}}{MS_{\text{within}}}, \quad \eta_j^2 = \frac{SS_{\text{between}}}{SS_{\text{total}}}$$
     Xếp hạng câu hỏi nào thúc đẩy sự khác biệt ý kiến sâu sắc nhất giữa các nhóm.
  6. **Tự động Tổng hợp Hồ sơ Nhân vật (Personas) & Trích dẫn APA 7th Edition.**

---

### 11.23. Phân tích Ma Trận Tương Đồng Cặp & Mạng Lưới Thông Đồng (Pairwise Similarity & Collusion Syndicate Engine)
- **Phương thức:** `POST` & `GET`
- **Đường dẫn:** `/api/surveys/{id}/analytics/pairwise-similarity`
- **Mục tiêu:** Quét toàn bộ tổ hợp cặp phản hồi $N \times (N-1)/2$, đo khoảng cách tương đồng trên câu hỏi đóng (Hamming distance) và câu hỏi mở (3-gram / token Jaccard), phát hiện trùng lặp bot farm, chia sẻ dấu vân tay thiết bị (`device_id`) và địa chỉ IP, trích xuất các vòng thông đồng (Connected Components) và đánh giá chỉ số liêm chính mẫu theo tiêu chuẩn AAPOR (2003) và ISO 20252:2019.
- **Tham số Request Body (hoặc Query Params với GET):**
  ```json
  {
    "threshold": 0.80, // Ngưỡng tương đồng tối thiểu (0.50 - 1.0)
    "max_matrix_size": 60, // Kích thước tối đa của ma trận heatmap (10 - 200)
    "scope": "all" // "all" hoặc "verified_clean"
  }
  ```
- **Thuật toán & Quy trình Tính toán:**
  1. **Khoảng cách Tương đồng Câu hỏi Đóng (Categorical Hamming Match):**
     $$S_{\text{closed}}(i, j) = \frac{\sum_{k=1}^K \mathbb{I}(v_{ik} == v_{jk} \land v_{ik} \neq "")}{\sum_{k=1}^K \mathbb{I}(v_{ik} \neq "" \lor v_{jk} \neq "")}$$
  2. **Độ tương đồng Văn bản Câu hỏi Mở (3-gram Character Jaccard):**
     $$J(T_i, T_j) = \frac{|G_3(T_i) \cap G_3(T_j)|}{|G_3(T_i) \cup G_3(T_j)|}$$
  3. **Độ tương đồng Tổng hợp (Composite Similarity Score):**
     $$S_{\text{comp}}(i, j) = 0.70 \times S_{\text{closed}}(i, j) + 0.30 \times S_{\text{open}}(i, j)$$
  4. **Nhận diện Dấu vân tay Số & Thời gian (Digital Footprint & Timing):**
     Phát hiện `same_device`, `same_ip`, `same_enumerator`, và nộp dồn dập $\Delta t \le 120\text{s}$. Flag `is_collusion_syndicate` nếu $S \ge 0.75$ kèm dấu hiệu chung phần cứng.
  5. **Bóc tách Vòng Lừa đảo bằng Đồ thị Thành phần Liên thông (Connected Components):**
     Xây dựng đồ thị vô hướng $G = (V, E)$ với $E = \{(i, j) \mid S(i, j) \ge \text{threshold} \lor \text{collusion}\}$. Tìm các thành phần liên thông kích thước $\ge 2$, xác định `threat_level` (`CRITICAL`, `HIGH`, `MEDIUM`), thời gian bao phủ và khuyến nghị cách ly.
  6. **Đánh giá Chỉ số Liêm chính Mẫu (Data Integrity Index) & Trích dẫn APA 7th / ISO 20252.**

---

### 11.24. Kiểm Định Không Gian Thực Địa, DBSCAN & Geo-Fencing (Spatial Analytics Engine)
- **Phương thức:** `POST` & `GET`
- **Đường dẫn:** `/api/surveys/{id}/analytics/spatial`
- **Mục tiêu:** Kiểm định tính liêm chính tọa độ GPS thực địa theo chuẩn ISO 20252:2019 (Mục 4.5.3) và AAPOR Fieldwork Standards. Phát hiện hiện tượng điều tra viên ngồi một chỗ khai khống dữ liệu (Coffee-Shop Congregation Fraud) bằng thuật toán mật độ DBSCAN, phát hiện dịch chuyển tức thời bất khả thi (Teleportation / GPS Spoofing) và kiểm tra vi phạm ranh giới đa giác Geo-Fence bằng thuật toán Ray-Casting.
- **Tham số Request Body (hoặc Query Params với GET):**
  ```json
  {
    "eps_meters": 75.0, // Bán kính láng giềng mật độ DBSCAN (mét, 10 - 2000m)
    "min_samples": 3, // Số điểm tối thiểu để hình thành cụm mật độ (2 - 20)
    "max_speed_kmh": 120.0, // Vận tốc di chuyển tối đa cho phép giữa 2 lần nộp liên tiếp (km/h)
    "geofence_polygon": [[10.7600, 106.6800], [10.7600, 106.7150], [10.7950, 106.7150], [10.7950, 106.6800]], // Đa giác ranh giới tùy chọn
    "scope": "all" // "all" hoặc "verified_clean"
  }
  ```
- **Thuật toán & Quy trình Tính toán:**
  1. **Khoảng cách Trắc địa Đường chim bay Haversine (Mặt cầu Trái Đất):**
     $$d = 2 R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right), \quad R = 6,371,000\text{ m}$$
  2. **Phân cụm Mật độ Không gian DBSCAN (Ester et al., 1996):**
     Xác định các điểm lõi có $\ge \text{min\_samples}$ láng giềng trong bán kính $\epsilon$. Mở rộng cụm kết nối mật độ. Phát hiện cụm cà phê nếu $\ge 3$ phiếu cùng 1 ĐTV trong thời gian $\le 2\text{ giờ}$ hoặc $\ge 5$ phiếu tập trung trong bán kính hẹp.
  3. **Phát hiện Vận tốc Dịch chuyển Bất khả thi (Teleportation Anomaly):**
     Tính khoảng cách $\Delta d$ và độ trễ thời gian $\Delta t$ giữa các phản hồi liên tiếp của cùng một ĐTV/thiết bị. Vận tốc $v = \frac{\Delta d}{\Delta t / 3600}$. Cảnh báo `CRITICAL` nếu $v > 120\text{ km/h}$ với $\Delta d > 0.5\text{ km}$.
  4. **Kiểm tra Ranh giới Đa giác Geo-Fence (Thuật toán Ray-Casting):**
     Kiểm định điểm nằm trong đa giác theo định lý đường cong Jordan. Nếu ngoài đa giác, đo khoảng cách ngắn nhất tới cạnh ranh giới.
  5. **Độ Phân tán Không gian Chuẩn (Spatial Standard Distance Deviation - Bachi 1962):**
     $$SDD = \sqrt{\frac{1}{N}\sum_{i=1}^N \text{Haversine}^2(P_i, \bar{P})}$$
  6. **Đoạn văn Kiểm toán Thực địa Chuẩn ISO 20252:2019 & AAPOR Verification.**

---

### 11.25. Quy trình Cách Ly Gian Lận Hàng Loạt Tự Động (Batch Anomaly Quarantine Pipeline)
- **Phương thức:** `POST`
- **Đường dẫn:** `/api/surveys/{id}/responses/batch-quarantine-anomalies`
- **Mục tiêu:** Tự động quét và thi hành cách ly hoặc gắn cờ gian lận hàng loạt trên toàn bộ dữ liệu khảo sát, tích hợp đa chiều các dấu hiệu bất thường: mạng lưới thông đồng (Collusion Syndicate Rings), tụ tập GPS tĩnh quán cà phê (Coffee-Shop Fraud), vận tốc di chuyển phi thực tế (> 120 km/h), vi phạm ranh giới địa bàn (Geofence Breach), người làm siêu tốc (Speeders), hoa văn rập khuôn (Straightlining) và ngưỡng điểm rủi ro tổng hợp.
- **Tính năng An toàn & Minh bạch:**
  - Hỗ trợ chế độ `dry_run = true` để mô phỏng trước tác động mà không thay đổi CSDL.
  - Tự động ghi nhật ký kiểm toán bất biến SHA-256 (`BATCH_ANOMALIES_QUARANTINED`) vào Sổ cái bảo mật (Tamper-Evident Ledger).
- **Tham số Request Body (`BatchAnomalyQuarantineRequest`):**
  ```json
  {
    "quarantine_syndicates": true,
    "quarantine_coffee_shop": true,
    "quarantine_impossible_velocity": true,
    "quarantine_geofence_violations": false,
    "quarantine_speeders": true,
    "quarantine_straightlining": true,
    "min_risk_score": 75.0,
    "action": "verified_fraud",
    "custom_note": null,
    "dry_run": false
  }
  ```
- **Cấu trúc Response (`BatchAnomalyQuarantineResult`):**
  - `success`: `true`
  - `survey_id`: ID khảo sát
  - `dry_run`: Trạng thái mô phỏng
  - `total_evaluated`: Tổng số phản hồi đã quét
  - `quarantined_count`: Số phản hồi bị cách ly
  - `reasons_breakdown`: Phân rã số lượng theo từng loại vi phạm (`collusion_syndicate`, `coffee_shop_congregation`, `impossible_travel`, `geofence_breach`, `speeder`, `straightlining`, `high_risk_score`)
  - `items`: Danh sách chi tiết các phiếu bị cách ly kèm lý do và trạng thái trước/sau
  - `audit_log_id`: Mã băm kiểm toán ledger SHA-256 (null nếu dry_run)
  - `timestamp`: Thời gian thực thi ISO 8601

---

### 11.26. Phục Hồi Dữ Liệu Cách Ly Minh Bạch (Reversible Quarantine Rollback)
- **Phương thức:** `POST`
- **Đường dẫn:** `/api/surveys/{id}/responses/batch-restore-quarantined`
- **Mục tiêu:** Cho phép kiểm toán viên hoặc trưởng nhóm điều tra hoàn tác và khôi phục các phản hồi đã bị cách ly/bị loại về trạng thái Chưa duyệt (`unverified`) hoặc Hợp lệ (`verified_valid`), đảm bảo hệ thống có cơ chế kiểm soát lỗi (Fault-Tolerant) và khả năng đảo ngược minh bạch.
- **Tham số Request Body (`BatchRestoreQuarantineRequest`):**
  ```json
  {
    "response_ids": null,
    "restore_to_status": "unverified",
    "reason": "Khôi phục sau thẩm tra thực địa"
  }
  ```
- **Cấu trúc Response (`BatchRestoreQuarantineResult`):**
  - `success`: `true`
  - `survey_id`: ID khảo sát
  - `restored_count`: Số phản hồi được phục hồi
  - `restored_ids`: Danh sách ID các phản hồi đã phục hồi
  - `audit_log_id`: Mã băm sự kiện kiểm toán ledger SHA-256
  - `timestamp`: Thời gian ghi nhận ISO 8601

---

## 31. Statistical Mediation & Path Analysis Engine (Mô Hình Tác Động Trung Gian PROCESS Model 4)

### `POST /api/surveys/:id/analytics/mediation`
- **Mô tả:** Phân tích mô hình tác động trung gian đơn (Simple Mediation Analysis) dự báo cơ chế truyền dẫn tác động từ Biến độc lập ($X$) qua Biến trung gian ($M$) đến Biến phụ thuộc ($Y$). Tuân thủ quy trình kiểm định 4 bước của Baron & Kenny (1986), mô hình PROCESS Model 4 của Hayes (2018), kiểm định Sobel (1982), kiểm định tái lấy mẫu Bootstrap không tham số 95% CI (Preacher & Hayes 2004, 2008), và tỷ lệ giải thích phương sai VAF (Hair et al., 2017).
- **Cơ sở phương pháp luận:**
  - Baron, R. M., & Kenny, D. A. (1986). The moderator-mediator variable distinction in social psychological research.
  - Preacher, K. J., & Hayes, A. F. (2004, 2008). Asymptotic and resampling strategies for assessing and comparing indirect effects in multiple mediator models.
  - Hayes, A. F. (2018). Introduction to Mediation, Moderation, and Conditional Process Analysis (2nd ed.).
  - Sobel, M. E. (1982). Asymptotic intervals for indirect effects in structural equations models.
  - Hair, J. F., Hult, G. T. M., Ringle, C. M., & Sarstedt, M. (2017). A Primer on Partial Least Squares Structural Equation Modeling (PLS-SEM).
- **Yêu cầu Request Body (`MediationAnalysisRequest`):**
  ```json
  {
    "x_question_id": "string",
    "m_question_id": "string",
    "y_question_id": "string",
    "scope": "all", // hoặc "verified_clean"
    "bootstrap_samples": 1000
  }
  ```
- **Quy trình Tính toán & Thuật toán:**
  1. **Bước 1 (Mô hình tổng thể - Total Effect):**
     $$Y = c_0 + c X + e_1$$
     Ước lượng hệ số $c$, $SE_c$, $t_c$, $p_c$, $R_1^2$, $F_1$.
  2. **Bước 2 (Mô hình tác động lên trung gian - Path $a$):**
     $$M = a_0 + a X + e_2$$
     Ước lượng hệ số $a$, $SE_a$, $t_a$, $p_a$, $R_2^2$, $F_2$.
  3. **Bước 3 & 4 (Mô hình đồng thời - Direct Effect $c'$ & Path $b$):**
     $$Y = c'_0 + c' X + b M + e_3$$
     Ước lượng hệ số trực tiếp $c'$, hệ số đường dẫn $b$, $R_3^2$, $\Delta R^2 = R_3^2 - R_1^2$.
  4. **Tác động gián tiếp (Indirect Effect):**
     $$indirect = a \cdot b, \quad \beta_{\text{indirect}} = \beta_a \cdot \beta_b$$
  5. **Kiểm định Sobel Test (1982) & Các biến thể:**
     - Sobel: $z = \frac{a \cdot b}{\sqrt{b^2 s_a^2 + a^2 s_b^2}}$
     - Aroian (1947): $z = \frac{a \cdot b}{\sqrt{b^2 s_a^2 + a^2 s_b^2 + s_a^2 s_b^2}}$
     - Goodman (1960): $z = \frac{a \cdot b}{\sqrt{b^2 s_a^2 + a^2 s_b^2 - s_a^2 s_b^2}}$
     - $p$-value 2 phía qua phân phối chuẩn tắc $2(1 - \Phi(|z|))$.
  6. **Kiểm định Tái Lấy Mẫu Không Tham Số Bootstrap (Preacher & Hayes 2008):**
     - Thực hiện $B$ vòng lặp lấy mẫu hoàn lại kích thước $N$.
     - Ước lượng phân phối thực nghiệm của $a^{(k)} \cdot b^{(k)}$.
     - Trích xuất khoảng phân vị 95% $[CI_{\text{lower}}, CI_{\text{upper}}]$.
     - Kết luận có ý nghĩa nếu khoảng tin cậy không bao hàm giá trị 0.
  7. **Tỷ Lệ Giải Thích Phương Sai VAF (Variance Accounted For):**
     $$\text{VAF} = \frac{a \cdot b}{c} \times 100\%$$
     - $\text{VAF} > 80\%$: Trung gian toàn phần (Full Mediation).
     - $20\% \le \text{VAF} \le 80\%$: Trung gian một phần (Partial Mediation).
     - $\text{VAF} < 20\%$: Không có tác động trung gian (No Mediation).
  8. **Cấu trúc Response (`MediationAnalysisOut`):**
     - `status`: `"OK"` | `"INSUFFICIENT_SAMPLE"` | `"ERROR"`
     - `sample_size`: Số lượng quan sát hoàn chỉnh $N$
     - `variables`: Nhãn của 3 biến $X, M, Y$
     - `steps`: Chi tiết 3 bước hồi quy (hệ số, SE, $t$, $p$, $R^2$)
     - `effects_summary`: Tác động tổng thể $c$, trực tiếp $c'$, gián tiếp $ab$, tỷ số $ab / c'$, VAF (%)
     - `significance_tests`: Sobel test, Aroian test, Goodman test, Bootstrap 95% CI
     - `conclusion`: Phân loại trung gian, giải thích chi tiết, đoạn văn APA 7th Edition
     - `diagram`: Tọa độ các nút và đường dẫn SVG trực quan hóa sơ đồ đường dẫn.

---

## 32. Non-Parametric Hypothesis Testing Engine (Kiểm Định Phi Tham Số Mann-Whitney U, Wilcoxon Signed-Rank, Kruskal-Wallis & Dunn Post-Hoc)

### `POST /api/surveys/:id/analytics/mann-whitney-u`
- **Mô tả:** Kiểm định phi tham số Mann-Whitney $U$ (Wilcoxon Rank-Sum test) so sánh sự khác biệt về phân phối trung vị giữa 2 nhóm độc lập (không đòi hỏi giả định phân phối chuẩn của dữ liệu). Thích hợp cho thang đo Likert, thang đo thứ bậc (ordinal) hoặc dữ liệu có độ lệch cao (skewed distributions).
- **Yêu cầu Request Body (`MannWhitneyURequest`):**
  ```json
  {
    "target_question_id": "string",
    "group_question_id": "string",
    "group_a_value": "Nam",
    "group_b_value": "Nữ",
    "scope": "all"
  }
  ```
- **Thuật toán & Quy chuẩn Thống kê:**
  1. Gộp toàn bộ dữ liệu 2 nhóm ($n_1 + n_2$), xếp hạng (rank) tăng dần, gán hạng trung bình (fractional average rank) cho các giá trị bằng nhau (ties).
  2. Tính tổng hạng: $R_1, R_2$.
  3. Giá trị thống kê $U$:
     $$U_1 = n_1 n_2 + \frac{n_1(n_1+1)}{2} - R_1, \quad U_2 = n_1 n_2 - U_1, \quad U = \min(U_1, U_2)$$
  4. Kỳ vọng & phương sai có hiệu chỉnh ties:
     $$\mu_U = \frac{n_1 n_2}{2}, \quad \sigma_U = \sqrt{\frac{n_1 n_2}{12} \left(N+1 - \frac{\sum (t_i^3 - t_i)}{N(N-1)}\right)}$$
  5. Trị số $z$ chuẩn hóa và giá trị $p$ hai phía (two-tailed $p$-value).
  6. Kích thước hiệu ứng (Effect Sizes):
     - Hệ số tương quan hạng Rosenthal: $r = \frac{|z|}{\sqrt{N}}$ (0.1 nhỏ, 0.3 trung bình, 0.5 lớn).
     - Rank-biserial correlation: $r_{rb} = 1 - \frac{2U}{n_1 n_2}$.
     - Xác suất vượt trội / Common Language Effect Size: $\text{CLES} = \frac{U_1}{n_1 n_2} \times 100\%$.
  7. Báo cáo học thuật APA 7th Edition: `W = 120.00, z = -2.15, p = .0315, r = .38 (Medium effect)`.

---

### `POST /api/surveys/:id/analytics/wilcoxon-signed-rank`
- **Mô tả:** Kiểm định cặp phi tham số Wilcoxon Signed-Rank test so sánh 2 điều kiện đo lường lặp lại (repeated measures / paired pre-post) trên cùng một mẫu người trả lời khi hiệu số không tuân theo phân phối chuẩn.
- **Yêu cầu Request Body (`WilcoxonSignedRankRequest`):**
  ```json
  {
    "question_1_id": "string",
    "question_2_id": "string",
    "scope": "all"
  }
  ```
- **Thuật toán & Quy chuẩn Thống kê:**
  1. Tính hiệu số từng cặp: $d_i = x_{1i} - x_{2i}$.
  2. Loại bỏ các cặp không có biến thiên ($d_i = 0$), thu được kích thước mẫu hữu hiệu $N_r$.
  3. Xếp hạng giá trị tuyệt đối $|d_i|$, gán hạng trung bình cho các giá trị bằng nhau.
  4. Tính tổng hạng dương ($W^+$) và tổng hạng âm ($W^-$).
  5. Trị số $W = \min(W^+, W^-)$.
  6. Kỳ vọng & độ lệch chuẩn có hiệu chỉnh ties:
     $$\mu_W = \frac{N_r(N_r+1)}{4}, \quad \sigma_W = \sqrt{\frac{N_r(N_r+1)(2N_r+1)}{24} - \frac{\sum (t_i^3 - t_i)}{48}}$$
  7. Matched-pairs rank-biserial correlation: $r_{prb} = \frac{W^+ - W^-}{W^+ + W^-}$.
  8. Trình bày APA 7th Edition và diễn giải khoa học.

---

### `POST /api/surveys/:id/analytics/kruskal-wallis`
- **Mô tả:** Kiểm định phi tham số Kruskal-Wallis $H$-test (One-Way ANOVA on Ranks) so sánh phân phối của $k \ge 3$ nhóm độc lập. Tích hợp kiểm định hậu nghiệm cặp Dunn's Test với hiệu chỉnh Bonferroni nhằm chỉ rõ cặp nhóm nào có sự sai khác có ý nghĩa thống kê.
- **Yêu cầu Request Body (`KruskalWallisRequest`):**
  ```json
  {
    "target_question_id": "string",
    "group_question_id": "string",
    "scope": "all"
  }
  ```
- **Thuật toán & Quy chuẩn Thống kê:**
  1. Gộp tất cả $N$ quan sát của $k$ nhóm, gán hạng toàn cục (global ranks) với hiệu chỉnh fractional ties.
  2. Tính tổng hạng $R_j$ và trung bình hạng $\bar{R}_j$ cho từng nhóm $j=1..k$.
  3. Thống kê Kruskal-Wallis $H$:
     $$H = \frac{12}{N(N+1)} \sum_{j=1}^k \frac{R_j^2}{n_j} - 3(N+1)$$
  4. Hệ số hiệu chỉnh ties: $C_{\text{ties}} = 1 - \frac{\sum (t_i^3 - t_i)}{N^3 - N}$, suy ra $H_{adj} = \frac{H}{C_{\text{ties}}}$.
  5. Giá trị $p$-value dựa trên phân phối Chi-Square $\chi^2$ với bậc tự do $df = k - 1$.
  6. Kích thước hiệu ứng Epsilon-squared: $\epsilon^2 = \frac{H_{adj} - k + 1}{N - k}$.
  7. **Kiểm định hậu nghiệm Dunn's Test (1964):**
     $$z_{ij} = \frac{|\bar{R}_i - \bar{R}_j|}{\sigma_{diff}}, \quad \sigma_{diff} = \sqrt{\left(\frac{N(N+1)}{12} - \frac{\sum(t_m^3 - t_m)}{12(N-1)}\right) \left(\frac{1}{n_i} + \frac{1}{n_j}\right)}$$
     - Hiệu chỉnh Bonferroni: $p_{adj} = \min(1.0, p_{raw} \times m)$ với $m = \frac{k(k-1)}{2}$.
  8. Xuất bảng so sánh cặp, đoạn văn APA 7th Edition và ghi nhận vết kiểm toán bất biến SHA-256.

---

## 33. Missing Data Pattern Diagnostics & Imputation Engine (Kiểm Định Mô Thức Khuyết Thiếu Little's MCAR & Bù Khuyết Đa Phương Pháp)

### `POST /api/surveys/:id/analytics/missing-data-diagnostics`
- **Mô tả:** Khảo sát chi tiết mô thức khuyết thiếu dữ liệu (missing data patterns), tỷ lệ non-response theo từng biến số và từng đối tượng khảo sát, nhận diện các tổ hợp mẫu khuyết (distinct patterns), và thực hiện kiểm định Little's MCAR Test (1988) nhằm đánh giá dữ liệu có thỏa mãn cơ chế Hoàn toàn Ngẫu nhiên (MCAR) hay phụ thuộc điều kiện (MAR/MNAR).
- **Cơ sở phương pháp luận:**
  - Little, R. J. (1988). A test of missing completely at random for multivariate data with missing values. *Journal of the American Statistical Association*, 83(404), 1198-1202.
  - Rubin, D. B. (1976). Inference and missing data. *Biometrika*, 63(3), 581-592.
  - Schafer, J. L. (1997). *Analysis of Incomplete Multivariate Data*. Chapman & Hall/CRC.
- **Yêu cầu Request Body (`MissingDataDiagnosticsRequest`):**
  ```json
  {
    "question_ids": null, // null = tự động lấy tất cả câu hỏi định lượng/thang đo
    "scope": "all" // hoặc "verified_clean"
  }
  ```
- **Thuật toán & Quy chuẩn Thống kê:**
  1. Xây dựng ma trận nhị phân chỉ báo $R_{ip} \in \{0, 1\}$ (1: quan sát, 0: khuyết thiếu).
  2. Tính tỷ lệ ô khuyết tổng thể, tỷ lệ khuyết từng biến số ($r_p$), số ca hoàn chỉnh ($N_{comp}$) và số ca khuyết thiếu ($N_{incomp}$).
  3. Nhận diện các tổ hợp mô thức khuyết $S_1, \dots, S_J$ cùng tần số xuất hiện $N_j$ và tỷ lệ $\%$.
  4. **Kiểm định Little's MCAR Test (1988):**
     - Ước lượng vector trung bình ML $\hat{\mu}$ và ma trận hiệp phương sai $\hat{\Sigma}$ (với regularization chống suy biến ma trận).
     - Với mỗi mô thức $j$ có $N_j$ đối tượng và tập biến quan sát $obs_j$:
       $$d_j^2 = (\bar{y}_{obs, j} - \hat{\mu}_{obs, j})' \hat{\Sigma}_{obs, j}^{-1} (\bar{y}_{obs, j} - \hat{\mu}_{obs, j})$$
     - Tổng thống kê kiểm định:
       $$d^2 = \sum_{j=1}^J N_j d_j^2$$
     - Bậc tự do: $df = \sum_{j=1}^J P_j - P$ với $P_j = |obs_j|$.
     - Mức ý nghĩa $p$-value dựa trên phân phối $\chi^2(df)$:
       - $p > 0.05$: Chấp nhận $H_0$ (MCAR). Dữ liệu phân bố ngẫu nhiên hoàn toàn. Việc xóa bỏ dòng khuyết (Listwise deletion) không gây chệch hệ thống.
       - $p \le 0.05$: Bác bỏ $H_0$ (MAR/MNAR). Dữ liệu có cấu trúc khuyết thiếu có điều kiện. Việc xóa bỏ dòng khuyết sẽ làm sai lệch nghiêm trọng; bắt buộc sử dụng bù khuyết kỳ vọng cực đại (EM) hoặc ghép cặp giá trị dự báo (PMM).
  5. Xuất đoạn văn học thuật APA 7th Edition: `Little's MCAR test: χ²(df) = d², p = .xxxx`.

---

### `POST /api/surveys/:id/analytics/missing-data-imputation`
- **Mô tả:** Động cơ bù khuyết dữ liệu đa thuật toán với kiểm soát cận biên thang đo khảo sát và phân tích bảo toàn tham số thống kê trước/sau bù khuyết.
- **Yêu cầu Request Body (`MissingDataImputationRequest`):**
  ```json
  {
    "question_ids": null,
    "method": "em", // 'em' | 'pmm' | 'hot_deck' | 'mean' | 'median'
    "scope": "all"
  }
  ```
- **Các Thuật Toán Bù Khuyết Hỗ Trợ:**
  1. **`em` (Expectation-Maximization Imputation - Dempster et al. 1977):**
     - Ước lượng các thống kê đủ (sufficient statistics) $\mu, \Sigma$ qua thuật toán lặp EM.
     - Bước E-step: Tính kỳ vọng có điều kiện qua phép chiếu hồi quy tuyến tính:
       $$\hat{y}_{mis} = \hat{\mu}_{mis} + \hat{\Sigma}_{mis, obs} \hat{\Sigma}_{obs, obs}^{-1} (y_{obs} - \hat{\mu}_{obs})$$
  2. **`pmm` (Predictive Mean Matching - Little 1988, Rubin 1986):**
     - Tính giá trị dự báo hồi quy $\hat{y}_i$, sau đó ghép với quan sát thực tế của nhà tài trợ (donor) $k$ có giá trị dự báo $\hat{y}_k$ gần nhất. Đảm bảo giá trị bù khuyết 100% tuân thủ các điểm thang đo rời rạc (1 đến 5).
  3. **`hot_deck` (Nearest-Neighbor Donor - Andridge & Little 2010):**
     - Tìm người trả lời có khoảng cách khoảng cách Euclid chuẩn hóa ngắn nhất trên các biến chung được quan sát và sao chép giá trị gốc.
  4. **`mean` & `median`:** Bù bằng giá trị trung bình hoặc trung vị của cột.
- **Đánh Giá Bảo Toàn Phương Sai & Chẩn Đoán:**
  - Bảng đối sánh trước và sau bù khuyết: `original_mean`, `imputed_mean`, `mean_delta_pct`, `original_std`, `imputed_std`.
  - Phân loại mức độ bảo toàn: `HIGH` (độ lệch $< 5\%$), `MODERATE` ($5\% - 15\%$), `DRIFT_ALERT` ($> 15\%$).
  - Niêm phong vết kiểm toán bất biến SHA-256 `MISSING_DATA_IMPUTATION_EXECUTED`.

---

## 34. Score Equating & Concordance Transformation Engine (Chuẩn Hóa & Liên Kết Thang Đo Đa Dạng)

### `POST /api/surveys/:id/analytics/scale-equating`
- **Mô tả:** Thiết lập hàm liên kết và bảng quy đổi tương đương (Concordance Table) giữa hai thang đo hoặc hai câu hỏi khảo sát có miền giá trị khác nhau (ví dụ: Likert 5 sao ⟷ NPS 10 điểm ⟷ Likert 7 mức ⟷ Thang điểm chuẩn 100). Đảm bảo dữ liệu khảo sát có thể hợp nhất sóng nghiên cứu dọc (Longitudinal waves) mà không gây biến dạng phân phối thực nghiệm.
- **Cơ sở phương pháp luận:**
  - Kolen, M. J., & Brennan, R. L. (2014). *Test Equating, Scaling, and Linking: Methods and Practices* (3rd ed.). Springer.
  - Angoff, W. H. (1971). Scales, norms, and equivalent scores. *Educational Measurement*, 2, 508-600.
  - Holland, P. W., & Thayer, D. T. (1987). Notes on loglinear models for equating. *ETS Research Report Series*.
  - Braun, H. I., & Holland, P. W. (1982). Observed-score test equating: A review. *Test Equating*, 9-49.
- **Yêu cầu Request Body (`ScaleEquatingRequest`):**
  ```json
  {
    "source_question_id": "string",
    "target_question_id": "string",
    "scope": "all" // hoặc "verified_clean"
  }
  ```
- **Thuật toán & Quy chuẩn Thống kê:**
  1. **Thống kê mô tả & Kiểm soát miền giá trị:**
     - Tính $\mu_X, \sigma_X, \text{Skew}_X$ và $\mu_Y, \sigma_Y, \text{Skew}_Y$.
     - Nhận diện ngưỡng lý thuyết (theoretical bounds) dựa trên loại câu hỏi (`nps`: 0-10, `rating`/`likert`: 1-5).
  2. **Linear Equating (Tucker / Levine Observed-Score Equating):**
     $$l_Y(x) = \frac{\sigma_Y}{\sigma_X} (x - \mu_X) + \mu_Y = \alpha x + \beta$$
     - Hệ số góc $\alpha = \frac{\sigma_Y}{\sigma_X}$, độ lệch gốc $\beta = \mu_Y - \alpha \mu_X$.
     - Bảo toàn chính xác trung bình $\mu_Y$ và phương sai $\sigma_Y^2$.
  3. **Equipercentile Equating (Kolen & Brennan 2014):**
     - Chuyển đổi liên tục qua khoảng hiệu dụng $[s - 0.5, s + 0.5]$ và điểm giữa phân vị (midpoint percentile rank):
       $$PR(x) = \left[ F^*(x - 0.5) + \frac{1}{2} \frac{f(x)}{N_X} \right] \times 100\%$$
     - Nghịch đảo trên hàm phân phối tích lũy của $Y$:
       $$e_Y(x) = (y - 0.5) + \frac{P - G^*(y - 0.5)}{g(y) / N_Y}$$
     - Áp dụng ngoại suy tuyến tính (Linear extrapolation) cho các điểm nằm ngoài miền hỗ trợ thực nghiệm của mẫu.
  4. **Bảng Quy Đổi Tương Đương (Concordance Table):**
     - Điểm nguồn $X$, Thứ hạng phân vị $PR(x)$, Điểm quy đổi tuyến tính, Điểm quy đổi phân vị $e_Y(x)$, Điểm làm tròn nguyên, Điểm chuẩn hóa $T$-Score ($50 + 10 \cdot z$), Điểm Stanine (1-9).
  5. **Phân tích Độ Bất Đồng & Đánh Giá Mức Độ Đồng Quy:**
     - Sai lệch tối đa $|l_Y(x) - e_Y(x)|$ trên miền quan sát thực tế:
       - $< 0.25$: `EXCELLENT` (Đồng quy hoàn hảo, phân phối đối xứng tương đồng).
       - $0.25 - 0.75$: `MODERATE` (Khác biệt vừa phải, khuyến nghị ưu tiên Equipercentile).
       - $> 0.75$: `SKEWED_DIVERGENCE` (Phân kỳ lệch tâm do độ lệch hoặc hiệu ứng trần/sàn).
  6. **Đoạn văn học thuật APA 7th Edition:** Xuất mẫu câu trích dẫn khoa học tiêu chuẩn.
  7. **Niêm phong kiểm toán bất biến:** Tự động ghi nhận `SCALE_EQUATING_ANALYSIS_PERFORMED` trên sổ cái băm SHA-256.

---

## 35. Multi-Group Measurement Invariance Engine (Kiểm Định Bất Biến Đo Lường Đa Nhóm Theo Cấu Trúc Yếu Tố)

### `POST /api/surveys/:id/analytics/measurement-invariance`
- **Mô tả:** Đánh giá tính tương đương của thang đo qua các nhóm nhân khẩu học hoặc các sóng khảo sát thời gian khác nhau (Multi-Group Confirmatory Factor Analysis). Tuân thủ quy trình kiểm định 4 cấp bậc thứ bậc (Hierarchical Invariance Testing) theo tiêu chuẩn Vandenberg & Lance (2000), Cheung & Rensvold (2002) và Chen (2007) nhằm xác định điều kiện tiên quyết cho việc so sánh điểm trung bình hoặc tương quan giữa các nhóm.
- **Cơ sở phương pháp luận:**
  - Vandenberg, R. J., & Lance, C. E. (2000). A review and synthesis of the measurement invariance literature. *Organizational Research Methods*, 3(1), 4-70.
  - Cheung, G. W., & Rensvold, R. B. (2002). Evaluating goodness-of-fit indexes for testing measurement invariance. *Structural Equation Modeling*, 9(2), 233-255.
  - Chen, F. F. (2007). Sensitivity of goodness of fit indexes to lack of measurement invariance. *Structural Equation Modeling*, 14(3), 464-504.
  - Meredith, W. (1993). Measurement invariance, factor analysis and factorial invariance. *Psychometrika*, 58(4), 525-543.
- **Yêu cầu Request Body (`MeasurementInvarianceRequest`):**
  ```json
  {
    "grouping_question_id": "string",
    "scale_question_ids": ["string", "string", "string"],
    "scope": "all" // hoặc "verified_clean"
  }
  ```
- **Hệ Thống 4 Cấp Bậc Thứ Bậc:**
  1. **Cấp 1: Configural Invariance (Bất biến hình thức):**
     - Đánh giá cùng cấu trúc nhân tố (cùng các chỉ báo quy về cùng nhân tố tiềm ẩn) trên tất cả các nhóm mà không đặt bất kỳ ràng buộc đẳng thức tham số nào.
     - Mô hình đường cơ sở (Baseline model) với $\chi^2_{\text{conf}}$, $df$, $\text{CFI}_{\text{conf}}$, $\text{RMSEA}_{\text{conf}}$.
  2. **Cấp 2: Metric / Weak Invariance (Bất biến độ dốc / tải trọng yếu tố):**
     - Đặt ràng buộc đẳng thức tải trọng yếu tố $\Lambda_1 = \Lambda_2 = \dots = \Lambda_G$.
     - Tiêu chuẩn chấp nhận: $\Delta \text{CFI} \ge -0.010$ và $\Delta \text{RMSEA} \le +0.015$.
     - Ý nghĩa: Cho phép so sánh hiệp phương sai, tương quan và hệ số hồi quy giữa các nhóm.
  3. **Cấp 3: Scalar / Strong Invariance (Bất biến hệ số chặn / thang đo):**
     - Đặt ràng buộc đồng thời cả tải trọng $\Lambda$ lẫn hệ số chặn $\tau_1 = \tau_2 = \dots = \tau_G$.
     - Tiêu chuẩn chấp nhận: $\Delta \text{CFI} \ge -0.010$ và $\Delta \text{RMSEA} \le +0.015$.
     - Ý nghĩa: **Điều kiện tiên quyết bắt buộc** để so sánh điểm trung bình tiềm ẩn (Latent Means) hoặc điểm tổng hợp thang đo giữa các nhóm mà không bị sai lệch do phản ứng câu hỏi (DIF).
  4. **Cấp 4: Strict Invariance (Bất biến phương sai phần dư):**
     - Đặt ràng buộc bổ sung phương sai sai số đo lường $\Theta_1 = \Theta_2 = \dots = \Theta_G$.
     - Ý nghĩa: Phương sai quan sát và độ tin cậy thang đo giống hệt nhau trên các phân nhóm.
- **Phân Tích Độ Ổn Định Từng Chỉ Báo (Item Stability):**
  - Trích xuất ma trận tải trọng $\Lambda_g$ và hệ số chặn $\tau_g$ cho từng câu hỏi theo nhóm.
  - Nhận diện chỉ báo có độ lệch vượt ngưỡng ($> 0.35$) để gợi ý hiệu chỉnh bảng câu hỏi.
- **Đoạn văn học thuật APA 7th Edition:** Xuất mẫu câu trích dẫn khoa học hoàn chỉnh.
- **Niêm phong kiểm toán bất biến:** Tự động ghi nhận `MEASUREMENT_INVARIANCE_EVALUATED` trên sổ cái băm SHA-256.

---

## 36. Common Method Bias / Variance (CMB/CMV) Diagnostics Engine (Chẩn Đoán Sai Lệch Phương Pháp Chung Podsakoff & Lindell)

### `POST /api/surveys/:id/analytics/common-method-bias`
- **Mô tả:** Động cơ chẩn đoán toàn diện sai lệch phương pháp chung (Common Method Bias / Variance - CMB/CMV) phát sinh khi cùng một người trả lời cung cấp dữ liệu cho cả biến độc lập lẫn biến phụ thuộc trong cùng một thời điểm và công cụ đo lường. Hệ thống tích hợp đồng thời 3 kỹ thuật chẩn đoán vàng học thuật:
  1. **Kiểm định Nhân tố Đơn Harman (Harman's Single-Factor Test - Harman 1976, Podsakoff et al. 2003)**
  2. **Kỹ thuật Biến Đánh Dấu (Marker Variable Technique - Lindell & Whitney 2001)**
  3. **Mô hình Nhân tố Phương pháp Chung Ẩn (Unmeasured Latent Common Method Factor - ULMCF - Podsakoff et al. 2003, Williams et al. 1989)**
- **Cơ sở phương pháp luận học thuật:**
  - Podsakoff, P. M., MacKenzie, S. B., Lee, J.-Y., & Podsakoff, N. P. (2003). Common method biases in behavioral research: A critical review of the literature and recommended remedies. *Journal of Applied Psychology*, 88(5), 879-903.
  - Lindell, M. K., & Whitney, D. J. (2001). Accounting for common method variance in cross-sectional research designs: Cheating-glove or statistical reality? *Journal of Applied Psychology*, 86(1), 114-121.
  - Harman, H. H. (1976). *Modern Factor Analysis*. University of Chicago Press.
  - Williams, L. J., Cote, J. A., & Buckley, M. R. (1989). Lack of method variance in self-reported affect and perceptions at work: Reality or artifact? *Journal of Applied Psychology*, 74(3), 462-468.
- **Yêu cầu Request Body (`CommonMethodBiasRequest`):**
  ```json
  {
    "scale_question_ids": ["q1", "q2", "q3", "q4"], // Tùy chọn, nếu bỏ trống hệ thống tự phát hiện toàn bộ câu hỏi thang đo
    "marker_question_id": "q_marker", // Tùy chọn, nếu bỏ trống hệ thống tự ước lượng proxy r_M từ mức tương quan dương thấp nhất
    "scope": "all" // hoặc "verified_clean"
  }
  ```
- **Quy Trình & Thuật Toán Chẩn Đoán:**
  1. **Harman's Single-Factor Test:**
     - Phân tích nhân tố khám phá (EFA) không xoay trên toàn bộ biến quan sát.
     - Tính tỷ lệ phương sai giải thích bởi nhân tố đầu tiên: $\text{Var}_1 = \frac{\lambda_1}{\sum \lambda_j} \times 100\%$.
     - Ngưỡng cho phép: $\text{Var}_1 < 50.0\%$. Nếu $\ge 50.0\%$, báo cáo cảnh báo nghiêm trọng về CMB.
     - Đếm số lượng nhân tố có trị riêng $\lambda \ge 1.0$ (Kaiser-Guttman criterion).
  2. **Marker Variable Technique (Lindell & Whitney 2001):**
     - Xác định hệ số tương quan biến đánh dấu $r_M$: Nếu người dùng chỉ định câu hỏi marker, $r_M = \min_{s} r(M, S_s)$; nếu không, $r_M = \min_{i < j, r_{ij} > 0} r_{ij}$.
     - Hiệu chỉnh từng cặp tương quan thực chất:
       $$r_{XY.M} = \frac{r_{XY} - r_M}{1 - r_M}$$
     - Kiểm định mức ý nghĩa thống kê của tương quan hiệu chỉnh:
       $$t = r_{XY.M} \sqrt{\frac{N - 3}{1 - r_{XY.M}^2}}, \quad p = 2(1 - F_{\text{Student-}t}(|t|, df=N-3))$$
     - Tính tỷ lệ giữ nguyên ý nghĩa thống kê (% Retention Rate): Tỷ lệ các cặp duy trì $p < .05$ sau khi kiểm soát sai số phương pháp chung.
  3. **Unmeasured Latent Common Method Factor (ULMCF):**
     - Mô hình hóa nhân tố phương pháp chung trực giao với các cấu trúc nội dung.
     - Ước lượng tỷ lệ phương sai giải thích bởi nhân tố phương pháp: $\text{CMV} = \frac{\bar{R}^2_{\text{method}}}{1 + \bar{R}^2_{\text{method}}} \times 100\%$.
     - Đối sánh với chuẩn thực nghiệm hành vi Williams et al. (1989): $\text{CMV} \le 25.0\%$.
  4. **Tổng hợp Phân loại Rủi ro & Khuyến nghị Khắc phục:**
     - `overall_risk`: `"LOW"`, `"MODERATE"`, `"HIGH"`.
     - Xuất đoạn trích minh bạch học thuật theo chuẩn APA 7th Edition.
     - Khuyến nghị biện pháp thủ tục (tách biệt thời gian, đảo trật tự câu hỏi, neo thang đo phân tán) và biện pháp thống kê (CFA Marker Variable modeling).
- **Niêm phong kiểm toán:** Tự động ghi nhận `COMMON_METHOD_BIAS_DIAGNOSED` vào chuỗi sổ cái SHA-256.

---

## 37. Statistical Moderation & Interaction Effects Analysis Engine (PROCESS Model 1 - Hayes 2018, Aiken & West 1991)

### `POST /api/surveys/:id/analytics/moderation`
- **Mô tả:** Động cơ phân tích tác động điều tiết (Moderation Analysis) và hiệu ứng tương tác có điều kiện (Conditional Process Analysis - PROCESS Model 1 của Andrew F. Hayes). Xác định khi nào hoặc trong điều kiện nào thì mối quan hệ giữa biến độc lập $X$ và biến phụ thuộc $Y$ được tăng cường, suy giảm hoặc đảo chiều dưới tác động của biến điều tiết $W$.
- **Cơ sở phương pháp luận học thuật:**
  - Hayes, A. F. (2018). *Introduction to Mediation, Moderation, and Conditional Process Analysis: A Regression-Based Approach* (2nd ed.). Guilford Press.
  - Aiken, L. S., & West, S. G. (1991). *Multiple Regression: Testing and Interpreting Interactions*. Sage Publications.
  - Johnson, P. O., & Neyman, J. (1936). Tests of certain linear hypotheses and their application to some educational problems. *Statistical Research Memoirs*, 1, 57-93.
  - Bauer, D. J., & Curran, P. J. (2005). Probing interactions in fixed and multilevel regression: Inferential and graphical techniques. *Multivariate Behavioral Research*, 40(3), 373-400.
- **Yêu cầu Request Body (`ModerationAnalysisRequest`):**
  ```json
  {
    "independent_question_id": "string",
    "moderator_question_id": "string",
    "dependent_question_id": "string",
    "center_variables": true, // Mean-centering X và W để triệt tiêu đa cộng tuyến (VIF)
    "scope": "all" // hoặc "verified_clean"
  }
  ```
- **Quy Trình & Thuật Toán Phân Tích:**
  1. **Chuẩn hóa Mean-Centering (Aiken & West 1991):**
     $$X^* = X - \bar{X}, \quad W^* = W - \bar{W}, \quad XW = X^* \cdot W^*$$
     Triệt tiêu hoàn toàn tương quan phi bản chất giữa biến bậc 1 và số hạng tương tác bậc 2, giữ VIF ở mức tối ưu $< 2.0$.
  2. **Mô hình Hồi quy Phân bậc (Hierarchical OLS):**
     - Mô hình 1 (Chỉ tác động chính): $Y = i_1 + b_1 X^* + b_2 W^* + e_1 \implies R_1^2$
     - Mô hình 2 (Toàn phần kèm tương tác): $Y = i_2 + b_1 X^* + b_2 W^* + b_3 (X^* W^*) + e_2 \implies R_2^2$
     - Kiểm định gia tăng phương sai:
       $$\Delta R^2 = R_2^2 - R_1^2, \quad F_{\Delta} = \frac{\Delta R^2 / 1}{(1 - R_2^2) / (N - 4)}$$
     - Tác động điều tiết có ý nghĩa thống kê nếu $p(F_{\Delta}) < 0.05$ (đồng thuận với kiểm định Student-$t$ hai phía của hệ số $b_3$).
  3. **Phân tích Độ dốc Đơn (Simple Slopes / Pick-a-Point Technique):**
     - Đánh giá tác động có điều kiện của $X$ lên $Y$ tại 3 mức chuẩn của $W$:
       - Mức thấp (Low): $\bar{W} - 1\text{SD}$
       - Mức trung bình (Mean): $\bar{W}$
       - Mức cao (High): $\bar{W} + 1\text{SD}$
     - Sai số chuẩn điều kiện: $s_{\theta} = \sqrt{\text{Var}(b_1) + 2W\text{Cov}(b_1, b_3) + W^2 \text{Var}(b_3)}$.
     - Trích xuất $t$-statistic, $p$-value và khoảng tin cậy 95% CI cho từng độ dốc.
  4. **Kỹ thuật Johnson-Neyman (1936; Bauer & Curran 2005):**
     - Giải phương trình bậc hai $A W^2 + B W + C = 0$ để tìm điểm chuyển tiếp ý nghĩa liên tục (Regions of Significance) mà tại đó $t = t_{\text{crit}}$ ($\alpha = 0.05$).
     - Xác định tỷ lệ % quan sát trong mẫu rơi vào miền có ý nghĩa thống kê.
  5. **Tọa độ Đồ thị Tương tác 2D:**
     - Tự động sinh tọa độ các đoạn thẳng hồi quy tại $X \pm 1\text{SD}$ cho cả 3 mức của $W$, phục vụ vẽ trực tiếp trên canvas/SVG.
  6. **Đoạn trích APA 7th Edition:** Xuất mẫu báo cáo học thuật hoàn chỉnh kèm giá trị $\Delta R^2$, $F$, $p$, $b_3$ và Johnson-Neyman intervals.
- **Niêm phong kiểm toán:** Tự động ghi nhận `MODERATION_ANALYSIS_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 38. Moderated Mediation & Conditional Indirect Effects Engine (PROCESS Model 7 - Hayes 2018)

### `POST /api/surveys/:id/analytics/moderated-mediation`
- **Mô tả:** Động cơ phân tích tác động trung gian bị điều tiết (Moderated Mediation Analysis - PROCESS Model 7 của Andrew F. Hayes). Kiểm định xem tác động gián tiếp của biến độc lập $X$ lên biến phụ thuộc $Y$ thông qua biến trung gian $M$ có thay đổi một cách có hệ thống theo các mức độ khác nhau của biến điều tiết $W$ (giai đoạn 1: $X \to M$ bị điều tiết bởi $W$).
- **Cơ sở phương pháp luận học thuật:**
  - Hayes, A. F. (2018). *Introduction to Mediation, Moderation, and Conditional Process Analysis: A Regression-Based Approach* (2nd ed.). Guilford Press.
  - Hayes, A. F. (2015). An index and test of linear moderated mediation. *Multivariate Behavioral Research*, 50(1), 1-22.
  - Preacher, K. J., Rucker, D. D., & Hayes, A. F. (2007). Addressing moderated mediation hypotheses: Theory, methods, and prescriptions. *Multivariate Behavioral Research*, 42(1), 185-227.
- **Yêu cầu Request Body (`ModeratedMediationRequest`):**
  ```json
  {
    "independent_question_id": "string",
    "mediator_question_id": "string",
    "moderator_question_id": "string",
    "dependent_question_id": "string",
    "center_variables": true,
    "num_bootstrap": 500,
    "scope": "all"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn kiểm định:**
  1. **Mean-Centering:** Chuẩn hóa trung bình $X^* = X - \bar{X}$, $W^* = W - \bar{W}$ nhằm triệt tiêu hiện tượng đa cộng tuyến giữa số hạng chính và số hạng tích tương tác $X \cdot W$.
  2. **Giai đoạn 1 (Stage 1 OLS Model - Biến Trung gian M):**
     $$M = a_0 + a_1 X + a_2 W + a_3 (X \cdot W) + \varepsilon_M$$
     Đo lường mức độ điều tiết của $W$ lên quan hệ $X \to M$ thông qua hệ số tương tác $a_3$.
  3. **Giai đoạn 2 (Stage 2 OLS Model - Biến Phụ thuộc Y):**
     $$Y = c_0 + c' X + b M + \varepsilon_Y$$
     Đo lường tác động trực tiếp của $X$ lên $Y$ ($c'$) và tác động của trung gian $M$ lên $Y$ ($b$).
  4. **Chỉ số Trung Gian Bị Điều Tiết (Index of Moderated Mediation - Hayes 2015):**
     $$\omega = a_3 \cdot b$$
     Đại lượng vô hướng lượng hóa độ dốc tuyến tính của tác động gián tiếp theo sự thay đổi của biến điều tiết $W$.
  5. **Tái lấy mẫu Bootstrap phi tham số (Non-parametric Percentile Bootstrap):**
     - Thực thi từ 200 đến 1,000 lần lặp tái lấy mẫu có hoàn lại.
     - Xác định khoảng tin cậy 95% Percentile Bootstrap $[CI_{\text{lower}}, CI_{\text{upper}}]$.
     - Kết luận: Nếu khoảng tin cậy 95% không bao hàm giá trị 0 ($0 \notin [CI_{\text{lower}}, CI_{\text{upper}}]$), tác động trung gian bị điều tiết được xác nhận có ý nghĩa thống kê ở mức $\alpha = 0.05$.
  6. **Tác động Gián tiếp có Điều kiện (Conditional Indirect Effects - Pick-a-Point):**
     - Đánh giá tác động gián tiếp $f(W) = (a_1 + a_3 W) \cdot b$ tại 3 mức độ của biến điều tiết $W$:
       - Mức Thấp: $W = \bar{W} - 1\text{SD}$
       - Mức Trung bình: $W = \bar{W}$
       - Mức Cao: $W = \bar{W} + 1\text{SD}$
     - Mỗi mức độ được cung cấp độ lệch chuẩn Bootstrap (BootSE) và khoảng tin cậy 95% BootCI tương ứng.
  7. **Đoạn trích APA 7th Edition:** Tự động tạo văn bản học thuật công bố chuẩn quốc tế (publication-ready narrative) kèm các chỉ số thống kê $R^2$, $F$, $p$, $\omega$, BootSE, và 95% BootCI.
- **Niêm phong kiểm toán:** Tự động ghi nhận sự kiện `MODERATED_MEDIATION_EVALUATED` kèm mã băm SHA-256 vào chuỗi sổ cái bất biến.

---

## 39. Two-Stage Complex Survey Sampling & Taylor Series Linearization Engine (Cochran 1977, Kish 1965, Horvitz & Thompson 1952)

### `POST /api/surveys/:id/analytics/complex-sampling`
- **Mô tả:** Động cơ phân tích thiết kế mẫu phức hợp hai giai đoạn (Two-Stage Cluster Sampling & Complex Design Weighting). Ước lượng giá trị trung bình và tổng có trọng số Horvitz-Thompson, hiệu chỉnh sai số chuẩn bằng Tuyến tính hóa chuỗi Taylor (Taylor Series Linearization / Cluster-robust sandwich estimator), tính toán Hiệu ứng thiết kế (Design Effect - DEFF, DEFT), Hệ số tương quan nội cụm (Intraclass Correlation - ICC / Kish's $\rho$) và Cỡ mẫu hiệu dụng thực tế ($n_{\text{eff}}$).
- **Cơ sở phương pháp luận học thuật:**
  - Horvitz, D. G., & Thompson, D. J. (1952). A generalization of sampling without replacement from a finite universe. *Journal of the American Statistical Association*, 47(260), 663-685.
  - Cochran, W. G. (1977). *Sampling Techniques* (3rd ed.). John Wiley & Sons.
  - Kish, L. (1965). *Survey Sampling*. John Wiley & Sons.
  - Wolter, K. M. (2007). *Introduction to Variance Estimation* (2nd ed.). Springer.
  - Heeringa, S. G., West, B. T., & Berglund, P. A. (2017). *Applied Survey Data Analysis* (2nd ed.). CRC Press / Chapman & Hall.
- **Yêu cầu Request Body (`ComplexSamplingRequest`):**
  ```json
  {
    "target_question_id": "string",
    "cluster_question_id": "string",
    "stratum_question_id": "string | null",
    "weight_question_id": "string | null",
    "scope": "all"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn kiểm định:**
  1. **Ước lượng Horvitz-Thompson (HT Ratio Estimator):**
     $$\bar{y}_w = \frac{\sum_{h=1}^H \sum_{i=1}^{n_h} \sum_{j=1}^{m_{hi}} w_{hij} y_{hij}}{\sum_{h=1}^H \sum_{i=1}^{n_h} \sum_{j=1}^{m_{hi}} w_{hij}}$$
     Độ lệch do trọng số: $\Delta M = \bar{y}_w - \bar{y}_{\text{raw}}$.
  2. **Tuyến tính hóa chuỗi Taylor (Taylor Series Linearization Variance):**
     - Đại diện tuyến tính hóa của tỷ số:
       $$z_{hij} = \frac{w_{hij} (y_{hij} - \bar{y}_w)}{\hat{N}}$$
     - Tổng tuyến tính cụm: $z_{hi\cdot} = \sum_j z_{hij}$
     - Phương sai nội tầng:
       $$v_h = \frac{n_h}{n_h - 1} \sum_{i=1}^{n_h} (z_{hi\cdot} - \bar{z}_{h\cdot\cdot})^2$$
     - Phương sai phức hợp toàn phần: $v_{\text{complex}} = \sum_h v_h$, $\text{SE}_{\text{complex}} = \sqrt{v_{\text{complex}}}$.
     - Cơ chế Lonely PSU: Khi $n_h = 1$, tự động quy tâm theo trung bình tổng thể tránh sập ma trận.
  3. **Hiệu ứng thiết kế (Design Effect - DEFF & DEFT):**
     $$\text{DEFF} = \frac{v_{\text{complex}}(\bar{y}_w)}{v_{\text{srs}}(\bar{y}_w)}, \quad \text{DEFT} = \sqrt{\text{DEFF}}$$
     Lượng hóa mức độ phóng đại phương sai do hiện tượng tương quan giữa các quan sát trong cùng cụm (PSU).
  4. **Tương quan nội cụm (Intraclass Correlation - ICC / Kish's roh $\rho$):**
     $$\text{ICC} = \frac{\text{DEFF} - 1}{\bar{m} - 1}$$
     Đo lường mức độ tương đồng giữa các cá thể trong cùng một đơn vị lấy mẫu cấp 1 (trường học, bệnh viện, cụm dân cư).
  5. **Cỡ mẫu hiệu dụng (Effective Sample Size $n_{\text{eff}}$):**
     $$n_{\text{eff}} = \frac{n}{\text{DEFF}}$$
     Xác định cỡ mẫu ngẫu nhiên đơn giản tương đương, phản ánh % suy giảm hiệu quả do thiết kế mẫu cụm.
  6. **Đoạn trích APA 7th Edition:** Xuất bản tường thuật khoa học hoàn chỉnh bao gồm cỡ mẫu $N$, số cụm, số tầng, kích thước cụm trung bình $\bar{m}$ và $CV(m)$, trung bình có trọng số $\bar{y}_w$, SE Taylor, 95% Taylor CI, DEFF, ICC và $n_{\text{eff}}$.
- **Niêm phong kiểm toán:** Tự động ghi nhận `COMPLEX_SAMPLING_EVALUATED` vào chuỗi sổ cái SHA-256.





















---

## 40. Propensity Score Matching (PSM) & Inverse Probability Weighting (IPW) Causal Inference Engine

- **Mục đích:** Đánh giá tác động can thiệp nhân quả (Causal Treatment Effects) trên dữ liệu khảo sát và nghiên cứu quan sát theo khung suy luận chuẩn tắc của **Rosenbaum & Rubin (1983)**, **Austin (2011)**, và **Stuart (2010)**. Giải quyết triệt để vấn đề độ lệch do tự chọn mẫu (selection bias) và biến gây nhiễu quan sát được (confounding variables) bằng cách ghép cặp 1:1 không thay thế (Greedy Nearest Neighbor Matching with Caliper Restriction) và đối sánh với mô hình Inverse Probability Weighting (IPW).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/propensity-matching`
- **Payload (`PSMAnalysisRequest`):**
  ```json
  {
    "treatment_question_id": "string",
    "treatment_value": "any (default '1')",
    "outcome_question_id": "string",
    "covariate_question_ids": ["string"],
    "caliper_factor": 0.20,
    "scope": "all"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn kiểm định:**
  1. **Ước lượng Điểm Xu Hướng (Propensity Score Estimation):**
     $$e(\mathbf{X}) = P(Z = 1 \mid \mathbf{X}) = \frac{1}{1 + e^{-(\beta_0 + \mathbf{X} \boldsymbol{\beta})}}$$
     Sử dụng mô hình Hồi quy Logistic OLS nhị phân với thuật toán lặp cực đại Newton-Raphson / IRLS và hiệu chỉnh điều chuẩn Ridge $\lambda = 10^{-4}$ để đảm bảo hội tụ số học tuyệt đối.
  2. **Biến đổi Logit của Điểm Xu Hướng:**
     $$\text{logit}(e_i) = \ln\left(\frac{e_i}{1 - e_i}\right)$$
     Khoảng cách ghép cặp được tính toán trên thang logit nhằm bảo toàn tính chuẩn hóa và đối xứng phân phối (Rosenbaum & Rubin, 1985).
  3. **Thuật toán Ghép Cặp Láng Giềng Gần Nhất 1:1 Có Ngưỡng Caliper (Austin 2011):**
     $$\delta = \text{caliper\_factor} \times \text{SD}(\text{logit}(e)) \quad (\text{Mặc định: } 0.20 \times \text{SD}_{\text{logit}})$$
     Cặp can thiệp $(T_i)$ và đối chứng $(C_j)$ được ghép cặp khi và chỉ khi:
     $$| \text{logit}(e_i) - \text{logit}(e_j) | \le \delta$$
     Mỗi đối tượng nhóm chứng chỉ được ghép tối đa 1 lần (ghép không hoàn lại - without replacement).
  4. **Chẩn Đoán Cân Bằng Đồng Biến (Covariate Balance Diagnostics):**
     - Chênh lệch trung bình chuẩn hóa (Standardized Mean Difference - SMD):
       $$\text{SMD} = \frac{\bar{X}_{\text{treat}} - \bar{X}_{\text{control}}}{\sqrt{\frac{s_{\text{treat}}^2 + s_{\text{control}}^2}{2}}}$$
       Tiêu chuẩn chấp thuận của Austin (2011) & Stuart (2010): $|\text{SMD}| < 0.10$.
     - Tỷ số phương sai (Variance Ratio - VR):
       $$\text{VR} = \frac{s_{\text{treat}}^2}{s_{\text{control}}^2}$$
       Tiêu chuẩn chấp thuận của Rubin (2001): $0.50 \le \text{VR} \le 2.00$.
     - Tỷ lệ giảm độ lệch bias (% Bias Reduction):
       $$\% \text{Bias Reduction} = \frac{|\text{SMD}_{\text{raw}}| - |\text{SMD}_{\text{matched}}|}{|\text{SMD}_{\text{raw}}|} \times 100\%$$
  5. **Ước Lượng Tác Động Can Thiệp Bình Quân trên Nhóm Can Thiệp (ATT - Average Treatment Effect on the Treated):**
     $$\widehat{\text{ATT}} = \frac{1}{M} \sum_{k=1}^M (Y_{k,\text{treat}} - Y_{k,\text{control}})$$
     Kiểm định ý nghĩa thống kê bằng kiểm định $t$ bắt cặp (Paired Samples Student's $t$-test) và khoảng tin cậy 95% CI.
  6. **Đối Sánh với Trọng Số Nghịch Đảo Xác Suất (Inverse Probability Weighting - IPW):**
     $$w_i = Z_i + (1 - Z_i) \frac{e_i}{1 - e_i}$$
     $$\widehat{\text{ATT}}_{\text{IPW}} = \frac{\sum Z_i Y_i}{\sum Z_i} - \frac{\sum (1 - Z_i) w_i Y_i}{\sum (1 - Z_i) w_i}$$
     Trọng số được kiểm soát chặn biên $[0.01, 0.99]$ để phòng chống hiện tượng trọng số cực đoan.
  7. **Trực Quan Hóa Tọa Độ Love Plot & Biểu Đồ Vùng Hỗ Trợ Chung (Common Support Histogram):**
     Phân tích phân phối tần suất 10 phân khoảng của điểm xu hướng giữa nhóm can thiệp và nhóm đối chứng để kiểm chứng giả định Vùng hỗ trợ chung (Common Support / Positivity Assumption).
  8. **Đoạn Trích Dẫn Chuẩn APA 7th Edition:**
     Tự động biên soạn báo cáo học thuật đầy đủ gồm quy mô mẫu $N$, số cặp ghép $M$, tỷ lệ ghép thành công, chênh lệch thô chưa ghép, giá trị ước lượng ATT, sai số chuẩn SE, $t$-stat, $p$-value, khoảng tin cậy 95% CI, kích thước hiệu ứng Cohen's $d$, kết quả chẩn đoán cân bằng SMD lớn nhất, và đối sánh trọng số IPW.
- **Niêm phong kiểm toán:** Tự động ghi nhận `PROPENSITY_SCORE_MATCHING_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 41. Structural Topic Modeling (STM) & Latent Dirichlet Allocation (LDA) Engine

- **Mục đích:** Khai phá tự động các chủ đề ngữ nghĩa tiềm ẩn (latent semantic themes) trong các phản hồi văn bản mở (`long_text`, `short_text`) theo phương pháp luận chuẩn mực của **Blei, Ng & Jordan (2003)** và **Roberts et al. (2014)**. Hỗ trợ tiền xử lý văn bản tiếng Việt chuyên sâu, đánh giá độ mạch lạc ngữ nghĩa UMass Coherence (Mimno et al., 2011), và phân tích tác động của biến đồng biến kiểm soát (STM Covariate Effects).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/topic-modeling`
- **Payload (`TopicModelAnalysisRequest`):**
  ```json
  {
    "text_question_id": "string",
    "covariate_question_id": "string | null",
    "num_topics": 3,
    "num_iterations": 60,
    "scope": "all"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn kiểm định:**
  1. **Tiền xử lý Văn bản Tiếng Việt Khảo sát:**
     - Chuẩn hóa chữ thường, loại bỏ số và ký tự đặc biệt.
     - Nhận diện và ghép các từ ghép khảo sát thông dụng: `chất_lượng`, `dịch_vụ`, `bảo_mật`, `khách_hàng`, `giao_diện`, `tốc_độ`, `hỗ_trợ`, `dễ_sử_dụng`, v.v.
     - Lọc bỏ danh sách từ dừng (Vietnamese stopwords) tiêu chuẩn gồm hơn 60 từ phổ biến.
     - Lọc từ vựng có độ dài $\ge 2$ ký tự, giới hạn tối đa 400 từ vựng xuất hiện nhiều nhất.
  2. **Thuật toán Lấy Mẫu Collapsed Gibbs Sampling (Griffiths & Steyvers, 2004):**
     $$P(z_i = k \mid \mathbf{z}_{-i}, \mathbf{w}) \propto \frac{n_{k,-i}^{(v)} + \beta}{\sum_{v=1}^V (n_{k,-i}^{(v)} + \beta)} \cdot (n_{d,-i}^{(k)} + \alpha)$$
     Với $\alpha = 50.0 / K$ và $\beta = 0.10$. Lặp qua $I = 60$ vòng để đạt trạng thái cân bằng dừng Markov chain.
  3. **Ước lượng Phân phối Xác suất Hậu nghiệm:**
     - Phân phối Chủ đề - Từ vựng $\boldsymbol{\Phi}$:
       $$\phi_{k,v} = \frac{n_k^{(v)} + \beta}{n_k + V \beta}$$
     - Phân phối Tài liệu - Chủ đề $\boldsymbol{\Theta}$:
       $$\theta_{d,k} = \frac{n_{d,k} + \alpha}{N_d + K \alpha}$$
  4. **Chẩn đoán Mạch lạc Ngữ nghĩa UMass Semantic Coherence (Mimno et al., 2011):**
     $$C_{\text{UMass}}(k, V^{(k)}) = \frac{2}{M(M-1)} \sum_{m=2}^M \sum_{l=1}^{m-1} \ln\left(\frac{D(v_m^{(k)}, v_l^{(k)}) + 1}{D(v_l^{(k)})}\right)$$
     Tính toán trên top $M = 10$ từ khóa hàng đầu của từng chủ đề.
  5. **Chỉ số Độc quyền Từ vựng (Exclusivity - Bischof & Airoldi, 2012):**
     Đo lường mức độ đặc thù của từ vựng đối với chủ đề $k$ so với các chủ đề còn lại.
  6. **Tác động Biến Điều Kiện Cấu Trúc (STM Feature - Roberts et al., 2014):**
     Ước lượng hệ số hồi quy $\beta$ và hệ số tương quan Pearson $r$ giữa giá trị biến đồng biến (ví dụ: điểm đánh giá hài lòng) và tỷ trọng chủ đề $\theta_{d,k}$ của từng phản hồi.
  7. **Đoạn Trích Dẫn Chuẩn APA 7th Edition:**
     Tự động biên soạn báo cáo học thuật đầy đủ gồm quy mô ngữ liệu $N$, số lượng chủ đề $K$, kích thước từ vựng $V$, siêu tham số Dirichlet, điểm mạch lạc $C_{\text{UMass}}$, chủ đề thống trị kèm danh sách từ khóa tiêu biểu, và liên kết cấu trúc biến điều kiện.
- **Niêm phong kiểm toán:** Tự động ghi nhận `STRUCTURAL_TOPIC_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 42. Psychometric Network Analysis & Gaussian Graphical Models (GGM)

- **Mục đích:** Mô hình hóa các mục/câu hỏi khảo sát như một hệ thống mạng lưới tương tác động học (dynamical interaction network) theo trường phái đo lường mạng lưới tâm lý học (**Borsboom & Cramer, 2013**; **Epskamp et al., 2012, 2018**; **Robinaugh et al., 2016**). Thay thế giả định biến tiềm ẩn truyền thống bằng các liên kết tương quan riêng phần (Partial Correlations) trực tiếp giữa các triệu chứng / câu hỏi khảo sát, bố trí lực lò xo Fruchterman-Reingold (1991), và tính toán các chỉ số trung tâm mạng lưới (Node Centrality).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/psychometric-network`
- **Payload (`PsychometricNetworkRequest`):**
  ```json
  {
    "question_ids": ["string"] (hoặc null để tự động nạp toàn bộ câu hỏi thang đo),
    "regularization_threshold": 0.05,
    "scope": "all"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn kiểm định:**
  1. **Ma trận Hiệp phương sai & Ma trận Nghịch đảo Precision Matrix:**
     Đảo ma trận tương quan $\mathbf{\Sigma}$ thành ma trận chính xác $\mathbf{\Omega} = \mathbf{\Sigma}^{-1}$ thông qua phép khử Gauss-Jordan có chọn phần tử trụ lớn nhất (Partial Pivoting) và điều chuẩn Ridge $\lambda = 10^{-4}$ để loại trừ hiện tượng suy biến ma trận (Singularity).
  2. **Ước lượng Tương quan Riêng phần (Partial Correlation Matrix):**
     $$r_{jk \cdot \text{rest}} = - \frac{\Omega_{jk}}{\sqrt{\Omega_{jj} \Omega_{kk}}}$$
     Đại diện cho mối liên hệ có điều kiện trực tiếp giữa mục $j$ và $k$ sau khi đã kiểm soát toàn bộ các mục còn lại trong hệ thống mạng lưới.
  3. **Ngưỡng Điều chuẩn Cắt giảm Cạnh Nhiễu (Regularization Thresholding):**
     Loại bỏ các cạnh liên kết yếu có $|r_{jk \cdot \text{rest}}| < \text{threshold}$ (mặc định $0.05$) để đảm bảo mạng lưới đồ thị thưa thớt, dễ giải thích và không bị nhiễu thống kê.
  4. **Các Chỉ Số Trung Tâm Mạng Lưới (Node Centrality Indices):**
     - **Strength Centrality ($C_{\text{Str}}$):** Tổng giá trị tuyệt đối trọng số các cạnh kết nối đến nút $i$:
       $$C_{\text{Strength}}(i) = \sum_{j \ne i} |w_{ij}|$$
     - **Expected Influence ($C_{\text{EI}}$ - Robinaugh et al., 2016):** Tổng trọng số có tính dấu của các cạnh kết nối, phân biệt liên kết kích hoạt dương (+) và ức chế âm (-):
       $$C_{\text{EI}}(i) = \sum_{j \ne i} w_{ij}$$
     - **Closeness Centrality ($C_{\text{Clo}}$):** Nghịch đảo tổng khoảng cách ngắn nhất (Dijkstra shortest paths $d(i, j) = 1 / |w_{ij}|$) từ nút $i$ đến toàn bộ các nút khác:
       $$C_{\text{Closeness}}(i) = \frac{P - 1}{\sum_{j \ne i} d(i, j)}$$
     - **Betweenness Centrality ($C_{\text{Bet}}$):** Tần suất nút $i$ nằm trên đường đi ngắn nhất giữa tất cả các cặp nút $(s, t)$ khác trong đồ thị.
     - Toàn bộ 4 chỉ số đều được tính toán thêm giá trị chuẩn hóa $z$-score ($M = 0.0, SD = 1.0$).
  5. **Thuật toán Bố trí Lực Lò xo Fruchterman-Reingold (1991):**
     Tính toán tọa độ vector 2D $(x_i, y_i)$ trong khung hiển thị SVG thông qua cân bằng lực đẩy tĩnh điện giữa mọi cặp nút ($f_r = k^2 / d$) và lực kéo đàn hồi giữa các nút có cạnh ($f_a = d^2 |w_{ij}| / k$) qua 50 vòng lặp làm nguội (cooling schedule).
  6. **Chỉ số Mạng lưới Toàn cục (Global Topology Metrics):**
     Mật độ mạng lưới (Network Density), Độ thưa thớt (Sparsity %), Trọng số cạnh trung bình $|w|$, và Nút trung tâm cốt lõi (Core Node).
  7. **Đoạn Trích Dẫn Chuẩn APA 7th Edition:**
     Tự động biên soạn báo cáo học thuật đầy đủ gồm quy mô mẫu $N$, số lượng nút $P$, số cạnh hoạt động $E$, mật độ mạng lưới, liên kết riêng phần mạnh nhất, và nút trung tâm điều tiết cốt lõi (Core indicator).
- **Niêm phong kiểm toán:** Tự động ghi nhận `PSYCHOMETRIC_NETWORK_ANALYSIS_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 43. Item Response Theory (IRT) 2-Parameter Logistic (2PL) & Item Characteristic Curves (ICC)

- **Mục đích:** Ước lượng mô hình Lý thuyết Ứng đáp Câu hỏi 2 Tham số Logistic (**Birnbaum, 1968**; **Bock & Aitkin, 1981**; **Baker, 2001**; **Reckase, 2009**) phục vụ hiệu chuẩn độ phân biệt câu hỏi ($a_i$), độ khó/ngưỡng ủng hộ ($b_i$), dựng đường cong đặc trưng ICC và hàm thông tin khảo sát TIF/SE, tính điểm năng lực/thái độ ẩn của từng người làm bài qua phương pháp Expected A Posteriori (EAP), và kiểm định độ phù hợp câu hỏi $S-X^2$.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/irt-2pl`
- **Payload (`IRT2PLAnalysisRequest`):**
  ```json
  {
    "question_ids": ["string"] (hoặc null để tự động nạp các câu hỏi thang đo/nhị phân),
    "binarization_threshold": null (hoặc số thực để binarize câu hỏi Likert đa mức),
    "max_em_iter": 35,
    "scope": "all"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Mô hình Xác suất 2PL Logistic:**
     $$P_i(\theta) = \frac{1}{1 + \exp\left(-D a_i (\theta - b_i)\right)}$$
     với hằng số quy chuẩn $D = 1.702$ (xấp xỉ hàm tích phân chuẩn tắc Normal Ogive của Lord & Novick).
     - Tham số độ phân biệt $a_i$: Đo lường độ dốc của đường cong ICC tại điểm uốn $\theta = b_i$. Phân loại theo tiêu chuẩn Baker (2001): Rất thấp ($a < 0.65$), Trung bình ($0.65 \le a < 1.35$), Cao ($1.35 \le a < 1.70$), và Rất cao ($a \ge 1.70$).
     - Tham số độ khó / ngưỡng ủng hộ $b_i$: Điểm trên trục năng lực/thái độ ẩn $\theta$ tại đó xác suất ủng hộ/đạt mục câu hỏi bằng $50\%$ ($P_i(b_i) = 0.50$).
  2. **Thuật toán Ước lượng Hợp lý Cực đại Biên kết hợp Kỳ vọng - Cực đại (MML-EM; Bock & Aitkin, 1981):**
     - Sử dụng 31 điểm cầu phương chuẩn tắc Gauss-Hermite $\theta_q \in [-3.0, +3.0]$ với trọng số tiền nghiệm $W(\theta_q) \sim \mathcal{N}(0, 1)$.
     - **Bước E (Expectation):** Tính xác suất hậu nghiệm của người trả lời $j$ tại node $q$:
       $$P(\theta_q \mid \mathbf{y}_j) = \frac{L_j(\theta_q) W(\theta_q)}{\sum_k L_j(\theta_k) W(\theta_k)}$$
       và tính kỳ vọng số người $\bar{N}_q$ cùng số người đạt mục $\bar{r}_{iq}$ tại từng node.
     - **Bước M (Maximization):** Cực đại hóa hàm hợp lý M-step bằng hồi quy logistic có trọng số (Newton-Raphson/IRLS) cập nhật liên hoàn cặp tham số $(\alpha_i, \beta_i)$ với điều chuẩn ma trận Hessian.
  3. **Ước lượng Điểm Năng Lực Ẩn Người Làm Bài (EAP Person Scoring):**
     $$\hat{\theta}_j = \sum_{q=1}^Q \theta_q P(\theta_q \mid \mathbf{y}_j), \quad \text{SE}(\hat{\theta}_j) = \sqrt{\sum_{q=1}^Q (\theta_q - \hat{\theta}_j)^2 P(\theta_q \mid \mathbf{y}_j)}$$
  4. **Hàm Thông Tin Câu Hỏi (IIF) & Hàm Thông Tin Bài Khảo Sát (TIF):**
     $$I_i(\theta) = D^2 a_i^2 P_i(\theta) (1 - P_i(\theta)), \quad I(\theta) = \sum_{i=1}^P I_i(\theta), \quad \text{SE}(\theta) = \frac{1}{\sqrt{I(\theta)}}$$
     Tự động xác định khoảng năng lực đo lường tối ưu $[\theta_1, \theta_2]$ nơi $I(\theta) \ge 0.5 \times I_{\max}$.
  5. **Độ Tin Cậy Biên IRT (Marginal Reliability; Green et al., 1984):**
     $$\bar{\rho}_{\text{IRT}} = \frac{\operatorname{Var}(\hat{\theta})}{\operatorname{Var}(\hat{\theta}) + \overline{\text{SE}^2}}$$
  6. **Đường Cong Vector SVG:**
     Tự động tạo tọa độ điểm và đường dẫn `svg_path` cho toàn bộ các đường cong ICC và đường cong TIF / SE.
  7. **Đoạn Trích Dẫn Chuẩn APA 7th Edition:**
     Tự động sinh đoạn văn bản báo cáo học thuật đầy đủ gồm quy mô mẫu $N$, số câu hỏi $P$, độ tin cậy biên $\bar{\rho}_{\text{IRT}}$, độ phân biệt trung bình $M_a$, độ khó trung bình $M_b$, các câu hỏi cực trị, và dải đo lường tối ưu.
- **Niêm phong kiểm toán:** Tự động ghi nhận `IRT_2PL_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 44. Survival Analysis & Time-to-Drop-off Engine (Kaplan-Meier & Cox Proportional Hazards)

- **Mục đích:** Mô hình hóa thời gian duy trì tham gia khảo sát của người trả lời và xác suất sống sót liên tục theo thời gian thực địa (**Kaplan & Meier, 1958**; **Cox, 1972**; **Mantel, 1966**; **Couper, 2001**). Cho phép phát hiện các điểm rơi rụng (drop-off bottlenecks) theo tiến trình thời gian thay vì các tỷ lệ tĩnh, kiểm định sự khác biệt duy trì giữa các nhóm (Log-Rank Test) và ước lượng tỷ số nguy cơ tức thời (Hazard Ratio).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/survival-dropoff`
- **Payload (`SurvivalAnalysisRequest`):**
  ```json
  {
    "grouping_question_id": null (hoặc ID câu hỏi phân nhóm nhân khẩu học),
    "time_milestones": [60.0, 180.0, 300.0, 600.0],
    "scope": "all"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Ước lượng Sống sót Phi tham số Kaplan-Meier:**
     $$\hat{S}(t) = \prod_{t_i \le t} \left(1 - \frac{d_i}{n_i}\right)$$
     với $t_i$ là các mốc thời gian xảy ra biến cố bỏ dở, $d_i$ là số người bỏ dở tại $t_i$, và $n_i$ là số người còn đang tham gia (at-risk) ngay trước $t_i$.
  2. **Phương sai & Khoảng tin cậy 95% Greenwood:**
     $$\widehat{\operatorname{Var}}(\hat{S}(t)) = \hat{S}(t)^2 \sum_{t_i \le t} \frac{d_i}{n_i (n_i - d_i)}, \quad 95\% \text{ CI} = [\hat{S}(t) \pm 1.96 \cdot \text{SE}_{\text{Greenwood}}]$$
  3. **Thời gian Sống sót Trung vị (Median Survival Time):**
     Mốc thời gian $t_{0.5}$ nhỏ nhất mà tại đó $\hat{S}(t) \le 0.50$. Nếu tỷ lệ hoàn thành vượt quá $50\%$, hệ thống ghi nhận chính xác trạng thái vượt ngưỡng $50\%$ duy trì.
  4. **Tỷ lệ Duy trì tại các Mốc Then chốt (Survival Milestones):**
     Tự động đánh giá tỷ lệ duy trì (%) và tỷ lệ bỏ dở (%) tại các mốc thời gian chuẩn $1$ phút, $3$ phút, $5$ phút, và $10$ phút.
  5. **Kiểm định Log-Rank Mantel-Cox (So sánh 2 Nhóm):**
     $$O_1 = \sum d_{1i}, \quad E_1 = \sum d_i \frac{n_{1i}}{n_i}, \quad V_1 = \sum \frac{d_i n_{1i} n_{2i} (n_i - d_i)}{n_i^2 (n_i - 1)}$$
     $$\chi^2 = \frac{(O_1 - E_1)^2}{V_1}, \quad df = 1, \quad p = \operatorname{erfc}\left(\sqrt{\frac{\chi^2}{2}}\right)$$
  6. **Tỷ số Nguy cơ Cox Proportional Hazards (HR):**
     $$\text{HR} = \frac{O_1 / E_1}{O_2 / E_2}, \quad \text{SE}(\ln \text{HR}) \approx \sqrt{\frac{1}{E_1} + \frac{1}{E_2}}$$
  7. **Đồ thị Hàm Bậc Thang Vector SVG:**
     Tự động tính toán đường dẫn bậc thang `svg_path` chuẩn xác cho đường cong toàn thể và từng nhóm so sánh.
  8. **Đoạn Trích Dẫn Chuẩn APA 7th Edition:**
     Tự động biên soạn báo cáo học thuật đầy đủ gồm quy mô $N$, số ca hoàn thành vs bỏ dở, thời gian trung vị, thống kê $\chi^2$ Log-Rank, $p$-value, và Hazard Ratio $HR$ kèm $95\%$ CI.
- **Niêm phong kiểm toán:** Tự động ghi nhận `SURVIVAL_ANALYSIS_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 45. Multilevel Modeling / Hierarchical Linear Models (HLM / MLM)

- **Mục đích:** Phân tích dữ liệu khảo sát có cấu trúc phân tầng thứ bậc (người trả lời lồng ghép trong địa bàn dân cư, trường học, doanh nghiệp, hoặc nhóm điều tra viên) nhằm giải quyết vi phạm giả định độc lập quan sát (**Raudenbush & Bryk, 2002**; **Snijders & Bosker, 2012**; **Hox et al., 2017**). Cung cấp phân rã phương sai và hệ số tương quan nội cụm (ICC), ước lượng hệ số chặn ngẫu nhiên và độ dốc ngẫu nhiên (Random Intercepts & Random Slopes), co rút tham số Bayes thực nghiệm (Empirical Bayes Shrinkage), và kiểm định tỷ số hợp lý (LRT) so sánh với mô hình OLS gộp.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/multilevel`
- **Payload (`MultilevelAnalysisRequest`):**
  ```json
  {
    "outcome_question_id": "string (UUID câu hỏi biến kết quả Y)",
    "predictor_question_id": "string (UUID câu hỏi biến dự báo X, tùy chọn)",
    "cluster_question_id": "string (UUID câu hỏi biến phân cụm tầng 2, tùy chọn)",
    "centering": "grand_mean" | "group_mean" | "none",
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Mô hình Rỗng Không Điều Kiện (Unconditional Null Model):**
     $$Y_{ij} = \gamma_{00} + u_{0j} + e_{ij}, \quad u_{0j} \sim \mathcal{N}(0, \tau_{00}), \quad e_{ij} \sim \mathcal{N}(0, \sigma^2)$$
  2. **Hệ số Tương quan Nội cụm (Intraclass Correlation Coefficient - ICC):**
     $$\text{ICC} = \frac{\tau_{00}}{\tau_{00} + \sigma^2}$$
     Phân loại theo chuẩn khoa học: Thấp ($< 0.05$), Trung bình ($0.05 \le \text{ICC} < 0.15$), Cao ($\ge 0.15$ - Bắt buộc áp dụng HLM).
  3. **Mô hình 2 Tầng Đầy đủ với Hệ số Chặn & Độ Dốc Ngẫu Nhiên:**
     $$Y_{ij} = (\gamma_{00} + u_{0j}) + (\gamma_{10} + u_{1j}) X_{ij} + e_{ij}$$
  4. **Co rút Tham số Bayes Thực nghiệm (Empirical Bayes Shrinkage):**
     $$\hat{\beta}_{0j}^{\text{EB}} = \lambda_j \bar{Y}_j + (1 - \lambda_j) \gamma_{00}, \quad \lambda_j = \frac{\tau_{00}}{\tau_{00} + \sigma^2 / n_j}$$
     Giảm thiểu phương sai sai số đối với các cụm/điều tra viên có cỡ mẫu nhỏ ($n_j < 5$).
  5. **Tỷ lệ Phương sai Giải thích Tầng 1 & Tầng 2 (Snijders & Bosker, 2012):**
     $$R^2_{\text{Level 1}} = 1 - \frac{\sigma^2_{\text{full}} + \tau_{00\text{,full}}}{\sigma^2_{\text{null}} + \tau_{00\text{,null}}}, \quad R^2_{\text{Level 2}} = 1 - \frac{\sigma^2_{\text{full}} / \tilde{n} + \tau_{00\text{,full}}}{\sigma^2_{\text{null}} / \tilde{n} + \tau_{00\text{,null}}}$$
  6. **Kiểm định Tỷ số Hợp lý Likelihood Ratio Test (HLM vs OLS):**
     $$\Delta -2\text{LL} = -2\text{LL}_{\text{OLS}} - (-2\text{LL}_{\text{HLM}}), \quad df = 2, \quad p = \operatorname{erfc}\left(\sqrt{\frac{\Delta -2\text{LL}}{2}}\right)$$
  7. **Đường Quỹ đạo Vector SVG:**
     Tự động tạo tọa độ đường quỹ đạo trực quan cho từng cụm và đường trung bình tổng thể.
  8. **Đoạn Thuyết minh Chuẩn APA 7th Edition:**
     Tự động biên soạn báo cáo đầy đủ bao gồm $N$, $J$, $\tilde{n}$, $\text{ICC}$, các hệ số cố định $\gamma_{00}, \gamma_{10}$, phương sai ngẫu nhiên $\tau_{00}, \sigma^2$, và thống kê $\Delta -2\text{LL}$ kèm $p$-value.
- **Niêm phong kiểm toán:** Tự động ghi nhận `MULTILEVEL_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 46. Choice-Based Conjoint Analysis (CBC / DCE) & Market Simulator

- **Mục đích:** Mô hình hóa các quyết định đánh đổi thuộc tính sản phẩm hoặc chính sách dựa trên Lý thuyết Tiện ích Ngẫu nhiên (**McFadden, 1974** - Giải Nobel Kinh tế 2000; **Luce, 1959**; **Green & Srinivasan, 1990**). Tự động phân rã tiện ích từng phần (Part-Worth Utilities), lượng hóa tỷ trọng độ quan trọng tương đối (Relative Importance %), ước lượng giá trị sẵn sàng chi trả (Willingness to Pay - WTP; **Hensher et al., 2005**), và mô phỏng thị phần lựa chọn theo quy tắc Logit.
- **Endpoints:**
  - `POST /api/surveys/{survey_id}/analytics/conjoint`: Ước lượng mô hình Conjoint và xếp hạng thuộc tính.
  - `POST /api/surveys/{survey_id}/analytics/conjoint-simulate`: Mô phỏng thị phần cho các hồ sơ sản phẩm đối đầu.
- **Payload (`ConjointAnalysisRequest`):**
  ```json
  {
    "rating_question_id": "string (UUID câu hỏi đánh giá sở thích/điểm ưa chuộng)",
    "attribute_question_ids": ["UUID_thuoc_tinh_1", "UUID_thuoc_tinh_2", ...],
    "price_question_id": "string (UUID thuộc tính giá, tùy chọn để tính WTP)",
    "scope": "all" | "verified_clean"
  }
  ```
- **Payload (`ConjointSimulationRequest`):**
  ```json
  {
    "rating_question_id": "string (UUID câu hỏi đánh giá)",
    "attribute_question_ids": ["UUID_thuoc_tinh_1", "UUID_thuoc_tinh_2"],
    "candidate_profiles": [
      {
        "id": "Hồ sơ Phương án A",
        "attributes": { "Thương hiệu": "Apple", "Mức giá": "20 Triệu" }
      },
      {
        "id": "Hồ sơ Phương án B",
        "attributes": { "Thương hiệu": "Xiaomi", "Mức giá": "10 Triệu" }
      }
    ],
    "scope": "all"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Mã hóa Hiệu ứng Zero-Sum (Effects Coding):**
     Với mỗi thuộc tính $m$ có $L_m$ mức độ, mức độ cuối cùng đóng vai trò mức tham chiếu $L_{m\text{,ref}}$. Ma trận thiết kế gán $+1$ cho mức độ khảo sát, $-1$ cho mức tham chiếu, và $0$ cho các mức khác. Đảm bảo:
     $$\sum_{l=1}^{L_m} \beta_{ml} = 0$$
  2. **Độ Quan trọng Tương đối của Thuộc tính (Attribute Relative Importance %):**
     $$\text{Range}_m = \max_l(\beta_{ml}) - \min_l(\beta_{ml}), \quad W_m = \frac{\text{Range}_m}{\sum_{k} \text{Range}_k} \times 100\%$$
  3. **Định giá Sẵn sàng Chi trả (Willingness-to-Pay - WTP):**
     $$\text{WTP}_{ml} = -\frac{\beta_{ml}}{\beta_{\text{Price}}}$$
     với $\beta_{\text{Price}}$ là tiện ích biên trên mỗi đơn vị giá cả.
  4. **Mô phỏng Thị phần Lựa chọn (Choice Share Market Simulator):**
     $$U_i = \beta_0 + \sum_{m} \beta_{m, l(i)}, \quad P(i) = \frac{\exp(U_i)}{\sum_j \exp(U_j)} \times 100\%$$
  5. **Biểu đồ Phân bổ Trọng số Vector SVG:**
     Tự động tạo biểu đồ thanh ngang SVG chuẩn hóa với tỷ lệ phần trăm trực quan.
  6. **Đoạn Thuyết minh Chuẩn APA 7th Edition:**
     Tự động biên soạn báo cáo đầy đủ gồm $N$, $R^2$, thuộc tính chi phối hàng đầu, mức tối ưu nhất, và định giá WTP gia tăng.
- **Niêm phong kiểm toán:** Tự động ghi nhận `CONJOINT_MODEL_EVALUATED` và `CONJOINT_SIMULATION_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 47. Latent Class Analysis (LCA) & Finite Mixture Segmentation

- **Mục đích:** Phân đoạn mẫu người trả lời thành các phân khúc tiềm ẩn chưa quan sát được (latent typologies/classes) dựa trên các biến định tính hoặc thứ bậc (**Lazarsfeld & Henry, 1968**; **Goodman, 1974**; **McLachlan & Peel, 2000**). Tự động ước lượng tỷ lệ phân bố lớp (class prevalences), xác suất phản hồi điều kiện (item response probabilities), xác suất hậu nghiệm (posterior probabilities $\tau_{ik}$), và lựa chọn giải pháp số lớp tối ưu theo tiêu chuẩn BIC và hệ số Entropy (**Celeux & Soromenho, 1996**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/lca`
- **Payload (`LCAAnalysisRequest`):**
  ```json
  {
    "item_question_ids": ["UUID_cau_hoi_1", "UUID_cau_hoi_2", "UUID_cau_hoi_3"],
    "num_classes": null (hoặc số nguyên 2, 3, 4 để ấn định số lớp),
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Thuật toán Kỳ vọng - Cực đại hóa (Expectation-Maximization - EM):**
     - **E-Step:** Tính toán xác suất hậu nghiệm:
       $$\tau_{ik} = P(C_i = k \mid Y_i) = \frac{\pi_k \prod_{j=1}^J P(Y_{ij} \mid C_i = k)}{\sum_{m=1}^K \pi_m \prod_{j=1}^J P(Y_{ij} \mid C_i = m)}$$
     - **M-Step:** Cập nhật tỷ lệ tiền nghiệm $\pi_k$ và xác suất có điều kiện $\theta_{kjp}$:
       $$\pi_k = \frac{1}{N} \sum_{i=1}^N \tau_{ik}, \quad \theta_{kjp} = \frac{\sum_{i: Y_{ij} = p} \tau_{ik}}{\sum_{i=1}^N \tau_{ik}}$$
  2. **Tiêu chuẩn So sánh và Lựa chọn Mô hình (Model Enumeration):**
     - Bayesian Information Criterion (BIC; **Schwarz, 1978**):
       $$\text{BIC} = -2 \ln L + P_K \ln(N)$$
     - Akaike Information Criterion (AIC):
       $$\text{AIC} = -2 \ln L + 2 P_K$$
     - Sample-Size Adjusted BIC (SABIC; **Sclove, 1987**):
       $$\text{SABIC} = -2 \ln L + P_K \ln\left(\frac{N + 2}{24}\right)$$
  3. **Độ Tách biệt Phân lớp (Entropy Classification Metric; Celeux & Soromenho, 1996):**
     $$E_K = 1 - \frac{\sum_{i=1}^N \sum_{k=1}^K -\tau_{ik} \ln(\tau_{ik})}{N \ln(K)}$$
     với $E_K \ge 0.80$ là phân tách rất tốt (High Separation).
  4. **Đồ thị Tọa độ Song song Vector SVG (Profile Plot):**
     Tự động tạo đồ thị đường biểu diễn xác suất lựa chọn trên từng câu hỏi cho mỗi lớp ẩn.
  5. **Đoạn Thuyết minh Chuẩn APA 7th Edition:**
     Tự động biên soạn báo cáo đầy đủ gồm $N$, số chỉ báo, số lớp tối ưu $K^*$, giá trị $\text{BIC}$, hệ số Entropy $E$, và tỷ lệ phân bố của từng phân đoạn kèm cỡ mẫu gán theo chế độ hậu nghiệm cực đại (modal assignment).
- **Niêm phong kiểm toán:** Tự động ghi nhận `LCA_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 48. Difference-in-Differences (DiD) & Two-Way Fixed Effects (TWFE) Policy Evaluation

- **Mục đích:** Đánh giá tác động nhân quả của can thiệp chính sách, chiến dịch truyền thông hoặc thử nghiệm khảo sát tự nhiên (**Card & Krueger, 1994**; **Angrist & Pischke, 2009** - Giải Nobel Kinh tế 2021; **Bertrand et al., 2004**; **Callaway & Sant'Anna, 2021**). Bóc tách hiệu ứng can thiệp thuần túy trên nhóm thụ hưởng (Average Treatment Effect on the Treated - ATT) bằng cách loại trừ đồng thời độ lệch chọn ban đầu (selection bias) và xu thế trôi tự nhiên theo thời gian (macroeconomic drift).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/did`
- **Payload (`DiDAnalysisRequest`):**
  ```json
  {
    "outcome_question_id": "string (UUID câu hỏi biến kết quả đo lường Y)",
    "treatment_question_id": "string (UUID câu hỏi phân nhóm Treatment vs Control)",
    "time_question_id": "string (UUID câu hỏi phân loại thời điểm Pre vs Post)",
    "treatment_value": "Nhãn nhóm can thiệp (tùy chọn)",
    "post_value": "Nhãn thời điểm sau can thiệp (tùy chọn)",
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Ước lượng DiD Điểm (Point Estimator):**
     $$\hat{\delta}_{\text{DiD}} = (\bar{Y}_{\text{Post, Treat}} - \bar{Y}_{\text{Pre, Treat}}) - (\bar{Y}_{\text{Post, Control}} - \bar{Y}_{\text{Pre, Control}})$$
  2. **Mô hình Hồi quy Hai chiều Cố định (Two-Way Fixed Effects - TWFE):**
     $$Y_{it} = \beta_0 + \beta_1 \text{Treated}_i + \beta_2 \text{Post}_t + \delta_{\text{DiD}} (\text{Treated}_i \times \text{Post}_t) + \epsilon_{it}$$
     - $\beta_0$: Mức cơ sở (Control Pre).
     - $\beta_1$: Chênh lệch cơ sở trước can thiệp giữa hai nhóm (Baseline selection).
     - $\beta_2$: Xu thế thay đổi chung theo thời gian (Natural drift).
     - $\delta_{\text{DiD}}$: Tác động nhân quả can thiệp thuần túy (ATT).
  3. **Đường Quỹ đạo Phản thực tế (Counterfactual Trajectory):**
     Theo giả định Xu hướng Song song (Parallel Trends Assumption):
     $$\hat{Y}_{\text{Counterfactual}} = \bar{Y}_{\text{Pre, Treat}} + (\bar{Y}_{\text{Post, Control}} - \bar{Y}_{\text{Pre, Control}})$$
     Mức thay đổi tương đối (% gain):
     $$\text{Relative Gain} = \frac{\hat{\delta}_{\text{DiD}}}{\hat{Y}_{\text{Counterfactual}}} \times 100\%$$
  4. **Đồ thị Vector SVG Quỹ đạo Causal Trajectory:**
     Tự động tạo đồ thị đường biểu diễn trực quan: đường thực tế nhóm Can thiệp, đường thực tế nhóm Đối chứng, đường nét đứt Phản thực tế, và khoảng cách hiệu ứng $\delta$ có đánh dấu mũi tên.
  5. **Đoạn Thuyết minh Chuẩn APA 7th Edition:**
     Tự động biên soạn báo cáo học thuật đầy đủ gồm quy mô mẫu $N$, hệ số $\beta_1, \beta_2$, hiệu ứng $\delta$, sai số chuẩn $\text{SE}$, thống kê $t$, $p$-value, khoảng tin cậy $95\%$ CI, và tỷ lệ phần trăm thay đổi so với phản thực tế.
- **Niêm phong kiểm toán:** Tự động ghi nhận `DID_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.

## 49. Structural Equation Modeling (SEM) & Path Analysis Engine

- **Mục đích:** Mô hình hóa đồng thời cấu trúc phụ thuộc nhân quả đa tầng giữa nhiều biến quan sát, phân tách tác động trực tiếp (Direct Effect), tác động gián tiếp (Indirect / Mediation Effect) và tác động tổng thể (Total Effect), kèm theo hệ thống chỉ số độ phù hợp mô hình toàn diện (**Wright, 1934**; **Jöreskog, 1970**; **Bentler, 1990**; **Tucker & Lewis, 1973**; **Hu & Bentler, 1999**; **Kline, 2015**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/sem`
- **Payload (`SEMAnalysisRequest`):**
  ```json
  {
    "paths": [
      { "source": "UUID_câu_hỏi_X", "target": "UUID_câu_hỏi_M" },
      { "source": "UUID_câu_hỏi_M", "target": "UUID_câu_hỏi_Y" },
      { "source": "UUID_câu_hỏi_X", "target": "UUID_câu_hỏi_Y" }
    ],
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Hệ Phương trình Cấu trúc Đồng thời (Simultaneous Structural Regressions):**
     Với mỗi biến nội sinh $Y_m \in \mathcal{Y}_{\text{endog}}$ có các biến dự báo $X_{m1}, \dots, X_{mk}$:
     $$Y_m = \alpha_m + \sum_{k} B_{mk} X_{mk} + \epsilon_m$$
     - Hệ số đường dẫn chưa chuẩn hóa $B_{mk}$, sai số chuẩn $SE(B_{mk})$, $z$-value, $p$-value hai phía và khoảng tin cậy $95\%$ CI.
     - Hệ số đường dẫn chuẩn hóa:
       $$\beta_{mk} = B_{mk} \cdot \frac{s_{X_{mk}}}{s_{Y_m}}$$
     - Hệ số xác định $R_m^2$ và phương sai sai số $\psi_{mm} = \text{Var}(\epsilon_m) = s_{Y_m}^2 (1 - R_m^2)$.
  2. **Phân rã Tác động Nhân quả (Direct, Indirect & Total Effects):**
     - **Tác động trực tiếp:** $\beta_{\text{direct}} = \beta_{Y \leftarrow X}$.
     - **Tác động gián tiếp:** Tích các hệ số dọc theo tất cả các đường đi đơn trong đồ thị DAG có độ dài $\ge 2$:
       $$B_{\text{indirect}} = \prod_{(u, v) \in \text{path}} B_{v \leftarrow u}$$
       Kiểm định ý nghĩa thống kê gián tiếp qua phương pháp Delta / Sobel mở rộng:
       $$SE_{\text{indirect}} = |B_{\text{indirect}}| \cdot \sqrt{\sum_{(u, v)} \left(\frac{SE(B_{uv})}{B_{uv}}\right)^2}, \quad z = \frac{B_{\text{indirect}}}{SE_{\text{indirect}}}$$
     - **Tác động tổng thể:** $B_{\text{total}} = B_{\text{direct}} + \sum B_{\text{indirect}}$.
  3. **Đại số Ma trận RAM & Chỉ số Phù hợp Toàn thể (Global Goodness-of-Fit Indices):**
     Ma trận hiệp phương sai lý thuyết theo công thức Reticular Action Model:
     $$\Sigma(\theta) = (I - A)^{-1} \Psi (I - A)^{-T}$$
     - Thống kê Chi-square $\chi^2$ với bậc tự do $df = \frac{P(P+1)}{2} - K_{\text{parameters}}$ và $p$-value.
     - **CFI (Comparative Fit Index $\ge 0.95$):** $1 - \frac{\max(\chi^2 - df, 0)}{\max(\chi_0^2 - df_0, \chi^2 - df, 0)}$.
     - **TLI (Tucker-Lewis Index $\ge 0.95$):** Non-Normed Fit Index (NNFI).
     - **RMSEA ($\le 0.06$):** $\sqrt{\max\left(0, \frac{\chi^2 - df}{(N-1)df}\right)}$ kèm khoảng tin cậy $90\%$ CI.
     - **SRMR ($\le 0.08$):** Căn bậc hai trung bình thặng dư chuẩn hóa (Hu & Bentler, 1999).
  4. **Sơ đồ Đường dẫn Vector SVG (Structural Path Diagram):**
     Tự động phân lớp cấu trúc (Exogenous, Mediators, Endogenous Outcomes), vẽ các hộp biến quan sát với nhãn hiển thị và huy hiệu $R^2$, các đường cong Bezier có mũi tên định hướng, nhãn hệ số chuẩn hóa $\beta$ kèm dấu hoa thị ý nghĩa thống kê ($^{***}, ^{**}, ^{*}$).
  5. **Đoạn Thuyết minh Chuẩn APA 7th Edition:**
     Tự động tổng hợp báo cáo học thuật chuẩn mực, giải thích cỡ mẫu $N$, các chỉ số phù hợp mô hình, các đường dẫn có ý nghĩa thống kê, kết quả kiểm định trung gian và mức độ giải thích phương sai của từng biến nội sinh.
- **Niêm phong kiểm toán:** Tự động ghi nhận `SEM_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.

## 50. Competing Risks & Shared Frailty Survival Engine

- **Mục đích:** Phân tích sống sót đa trạng thái cho dữ liệu bỏ dở khảo sát trực địa và online với các nguyên nhân kết thúc loại trừ lẫn nhau (Bỏ cuộc giữa chừng, Hết hạn ngạch quota, Loại trừ do gian lận tốc độ/honeypot) và bóc tách tính không đồng nhất chưa quan sát (Unobserved Heterogeneity) giữa các cụm điều tra viên / thiết bị (**Fine & Gray, 1999**; **Hougaard, 2000**; **Wienke, 2010**; **Putter et al., 2007**; **Self & Liang, 1987**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/competing-risks`
- **Payload (`CompetingRisksAnalysisRequest`):**
  ```json
  {
    "cluster_question_id": "string (UUID câu hỏi phân nhóm Điều tra viên / Thiết bị / Chi nhánh, tùy chọn)",
    "event_question_id": "string (UUID câu hỏi phân loại nguyên nhân kết thúc, tùy chọn)",
    "time_milestones": [60.0, 180.0, 300.0, 600.0],
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Hàm Tích lũy Biến cố Phi tham số (Cumulative Incidence Function - CIF Aalen-Johansen):**
     Với mỗi nguyên nhân cạnh tranh $k \in \{1, \dots, K\}$ tại các mốc thời gian $t_j$:
     $$\hat{I}_k(t_j) = \hat{I}_k(t_{j-1}) + S(t_{j-1}) \frac{d_{jk}}{n_j}$$
     Trong đó $S(t_{j-1}) = \prod_{l < j} (1 - d_l / n_l)$ là xác suất duy trì không gặp bất kỳ biến cố cạnh tranh nào.
  2. **Lượng hóa Sai lệch Thổi phồng của Kaplan-Meier Cổ điển (Naive KM Overestimation Bias):**
     Kaplan-Meier chuẩn xem các nguyên nhân khác như kiểm duyệt độc lập (independent censoring), vi phạm định lý Fine & Gray (1999) và thổi phồng nguy cơ:
     $$\text{Bias}_{\text{Naive KM}}(t) = (1 - \hat{S}_{\text{KM, naive}}(t)) - \hat{I}_k(t) \ge 0$$
     Hệ thống tự động tính toán mức độ thổi phồng (ví dụ: +12.4% tại mốc 180s) để cảnh báo nhà nghiên cứu.
  3. **Mô hình Suy yếu Chung Gamma (Shared Gamma Frailty Model):**
     Mô hình hóa tỷ lệ nguy cơ rủi ro bỏ dở cho đối tượng $j$ thuộc cụm $i$ (điều tra viên $i$):
     $$h_{ij}(t) = w_i h_0(t)$$
     với $w_i \sim \text{Gamma}(1/\theta, 1/\theta)$ có kỳ vọng 1 và phương sai $\theta = \text{Var}(w_i)$.
     - Ước lượng Bayes Thực nghiệm (Empirical Bayes):
       $$\hat{w}_i = \frac{1/\theta + D_i}{1/\theta + E_i}$$
       $\hat{w}_i > 1.25$ nhận diện các điều tra viên hoặc thiết bị có rủi ro người trả lời bỏ cuộc cao bất thường.
     - Kiểm định Tỉ số Hợp lý (Likelihood Ratio Test - LRT) với phân phối hỗn hợp Self & Liang (1987) $0.5 \chi_0^2 + 0.5 \chi_1^2$ đánh giá $H_0: \theta = 0$.
  4. **Đồ thị Vector SVG Đa đường cong CIF:**
     Vẽ biểu đồ hàm bậc thang nhiều màu biểu diễn xác suất tích lũy $I_k(t)$ theo thời lượng khảo sát (0 - 600s), kèm các vạch mốc thời gian Milestone và bảng chú giải màu sắc trực quan.
  5. **Đoạn Thuyết minh Chuẩn APA 7th Edition:**
     Tự động biên soạn báo cáo chuẩn mực nêu rõ cỡ mẫu $N$, tỷ lệ CIF từng nguyên nhân, độ lệch thổi phồng của ước lượng cổ điển, phương sai suy yếu $\theta$, thống kê LRT và giá trị $p$.
- **Niêm phong kiểm toán:** Tự động ghi nhận `COMPETING_RISKS_EVALUATED` vào chuỗi sổ cái SHA-256.

## 51. Item Response Theory (IRT) 3PL & 4PL Models & Adaptive Testing Engine

- **Mục đích:** Mô hình hóa xác suất phản hồi tâm lý học và giáo dục nâng cao có tính đến yếu tố đoán mò may rủi ($c_i$) và sự đãng trí / bất cẩn ($d_i$), đánh giá Hàm thông tin bài test (Test Information Function - TIF), sai số chuẩn đo lường có điều kiện, và mô phỏng trắc nghiệm thích ứng máy tính (Computerized Adaptive Testing - CAT) (**Birnbaum, 1968**; **Lord, 1980**; **Barton & Lord, 1981**; **Magis, 2013**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/irt-4pl`
- **Payload (`IRT4PLAnalysisRequest`):**
  ```json
  {
    "question_ids": ["UUID_câu_hỏi_1", "UUID_câu_hỏi_2", "UUID_câu_hỏi_3"],
    "model_type": "4pl" | "3pl",
    "binarization_threshold": 3.0,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Mô hình Xác suất 4PL Logistic:**
     $$P_i(\theta) = c_i + (d_i - c_i) \frac{1}{1 + \exp\left(-D a_i (\theta - b_i)\right)}$$
     - $a_i > 0$: Độ phân biệt câu hỏi (Discrimination).
     - $b_i \in [-3.5, 3.5]$: Độ khó câu hỏi (Difficulty).
     - $c_i \in [0, 0.45]$: Tham số đoán mò tiệm cận dưới (Pseudo-guessing).
     - $d_i \in [0.55, 1.0]$: Tham số bất cẩn/trượt tiệm cận trên (Inattention / Upper asymptote). Trong mô hình 3PL, $d_i \equiv 1.0$.
     - Hằng số co dãn logistic $D = 1.702$.
  2. **Hàm Thông tin Câu hỏi (IIF) & Bài test (TIF - Magis 2013):**
     $$I_i(\theta) = \frac{(P_i'(\theta))^2}{P_i(\theta) (1 - P_i(\theta))} = D^2 a_i^2 (d_i - c_i)^2 \frac{[P_i^*(\theta)]^2 [1 - P_i^*(\theta)]^2}{P_i(\theta) [1 - P_i(\theta)]}$$
     Hàm thông tin toàn bài:
     $$\text{TIF}(\theta) = \sum_{i=1}^M I_i(\theta)$$
     Sai số chuẩn đo lường (Standard Error of Measurement):
     $$\text{SE}(\theta) = \frac{1}{\sqrt{\text{TIF}(\theta)}}$$
     Độ tin cậy có điều kiện (Conditional Reliability): $R(\theta) = 1 - \frac{1}{\text{TIF}(\theta)}$.
  3. **Mô phỏng Trắc nghiệm Thích ứng Máy tính (CAT Simulation):**
     Lựa chọn tuần tự các câu hỏi tối đa hóa thông tin Fisher tại năng lực ước lượng sơ bộ hiện tại $\hat{\theta}_s$, cập nhật điểm năng lực và ghi nhận sự giảm dần của sai số $\text{SE}(\theta)$ qua từng bước kiểm tra.
  4. **Đồ thị Vector SVG Đường cong Đặc trưng ICC & TIF:**
     Biểu diễn trực quan các đường cong ICC cho từng câu hỏi với bảng chú giải màu sắc, các ngưỡng $\theta$ và đường cong phân bố lượng thông tin.
  5. **Đoạn Thuyết minh Chuẩn APA 7th Edition:**
     Tự động biên soạn báo cáo chuẩn mực nêu rõ các tham số $a, b, c, d$, đỉnh thông tin $\theta_{\text{peak}}$, sai số chuẩn nhỏ nhất $\text{SE}_{\min}$, và vùng đo lường đạt độ tin cậy tối ưu.
- **Niêm phong kiểm toán:** Tự động ghi nhận `IRT_4PL_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.

## 52. Propensity Score Weighting (IPW) & Doubly Robust Estimation (AIPW) Causal Engine

- **Mục đích:** Ước lượng tác động can thiệp nhân quả thuần túy (Causal Treatment Effects: ATE, ATT, Overlap ATO, Stabilized) từ dữ liệu khảo sát và nghiên cứu quan sát bằng cách khử nhiễu thiên lệch chọn lọc (Selection Bias) và biến gây nhiễu quan sát được (Confounders) qua phương pháp Trọng số Xác suất Nghịch đảo và Hồi quy Vững Kép (**Rosenbaum & Rubin, 1983**; **Robins et al., 1994**; **Lunceford & Davidian, 2004**; **Austin & Stuart, 2015**; **Bang & Robins, 2005**; **Li et al., 2018**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/ipw`
- **Payload (`IPWAnalysisRequest`):**
  ```json
  {
    "treatment_question_id": "UUID_câu_hỏi_can_thiệp_D",
    "outcome_question_id": "UUID_câu_hỏi_kết_quả_Y",
    "covariate_question_ids": ["UUID_đồng_biến_X1", "UUID_đồng_biến_X2"],
    "treatment_value": "1" | "true" | "treated",
    "weight_scheme": "ate" | "att" | "overlap" | "stabilized",
    "trim_weights": true,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Mô hình Điểm Xu Hướng Logistic (Propensity Score IRLS):**
     $$e_i = P(D_i = 1 \mid \mathbf{X}_i) = \frac{1}{1 + \exp\left(-\mathbf{X}_i \boldsymbol{\beta}\right)}$$
     Khớp bằng thuật toán Bình phương Tối thiểu Trọng số Lặp (IRLS) kèm điều chuẩn Ridge $\lambda = 10^{-4}$ và giới hạn cắt tiệm cận $[0.01, 0.99]$.
  2. **Các Lược đồ Gán Trọng số IPW (Weight Schemes):**
     - **ATE (Average Treatment Effect):** $w_i = \frac{D_i}{e_i} + \frac{1 - D_i}{1 - e_i}$.
     - **ATT (Treatment Effect on Treated):** $w_i = D_i + (1 - D_i) \frac{e_i}{1 - e_i}$.
     - **Overlap Weights (Li et al., 2018 - ATO):** $w_i = D_i (1 - e_i) + (1 - D_i) e_i$, triệt tiêu hoàn toàn sự mất ổn định do các giá trị $e_i$ cực trị gần 0 hoặc 1.
     - **Stabilized IPTW (Hernán & Robins, 2006):** $w_i = D_i \frac{\bar{p}}{e_i} + (1 - D_i) \frac{1 - \bar{p}}{1 - e_i}$.
     - Cắt tỉa trọng số ngoại lai (Weight Trimming) tại phân vị 1% và 99%.
  3. **Ước lượng Trọng số Nghịch đảo Chuẩn hóa Hajek (Horvitz-Thompson biến thể chuẩn):**
     $$\hat{\tau}_{\text{IPW}} = \frac{\sum_{i=1}^N w_i D_i Y_i}{\sum_{i=1}^N w_i D_i} - \frac{\sum_{i=1}^N w_i (1 - D_i) Y_i}{\sum_{i=1}^N w_i (1 - D_i)}$$
     Sai số chuẩn theo khai triển tiệm cận phi Lunceford & Davidian (2004).
  4. **Ước lượng Vững Kép (Doubly Robust / Augmented IPW - AIPW):**
     Khớp mô hình hồi quy kết quả $m_1(\mathbf{X})$ và $m_0(\mathbf{X})$.
     $$\Gamma_{i1} = m_1(\mathbf{X}_i) + \frac{D_i (Y_i - m_1(\mathbf{X}_i))}{e_i}, \quad \Gamma_{i0} = m_0(\mathbf{X}_i) + \frac{(1 - D_i) (Y_i - m_0(\mathbf{X}_i))}{1 - e_i}$$
     $$\hat{\tau}_{\text{DR}} = \frac{1}{N} \sum_{i=1}^N (\Gamma_{i1} - \Gamma_{i0})$$
     Đảm bảo tính vững nếu một trong hai mô hình (Propensity Score HOẶC Outcome Regression) được đặc tả chính xác (Robins et al., 1994; Bang & Robins, 2005).
  5. **Kiểm định Cân bằng Đồng biến (Covariate Balance Diagnostics & Love Plot):**
     Tính Chênh lệch Trung bình Chuẩn hóa Tuyệt đối (Absolute Standardized Mean Difference - ASMD) trước và sau gán trọng số:
     $$\text{ASMD}_{\text{raw}} = \frac{|\bar{X}_{1} - \bar{X}_{0}|}{s_{\text{pooled}}}, \quad \text{ASMD}_{\text{weighted}} = \frac{|\bar{X}_{1, w} - \bar{X}_{0, w}|}{s_{\text{pooled}}}$$
     Ngưỡng chuẩn vàng: $\text{ASMD} \le 0.10$ (Austin & Stuart, 2015).
  6. **Đồ họa Vector SVG Love Plot & Báo cáo APA 7th Edition:**
     Tự động tạo đồ thị Love Plot so sánh ASMD trước/sau với vạch đỏ giới hạn chuẩn 0.10, và đoạn văn báo cáo học thuật APA 7th đầy đủ.
- **Niêm phong kiểm toán:** Tự động ghi nhận `IPW_DOUBLY_ROBUST_EVALUATED` vào chuỗi sổ cái SHA-256.

## 53. Generalized Additive Models (GAM) & Natural Spline Regression Engine

- **Mục đích:** Mô hình hóa và kiểm định thống kê các mối quan hệ phi tuyến tính phức tạp giữa biến dự báo $X$ và biến kết quả $Y$ (ví dụ: đường cong phản hồi liều lượng Dose-Response, điểm bão hòa mệt mỏi theo thời lượng khảo sát, quy luật hiệu suất giảm dần) bằng cách sử dụng cơ sở Natural Cubic Spline có phạt độ gồ ghề (Roughness Regularization) và kiểm định $F$ phi tuyến tính (**Hastie & Tibshirani, 1990**; **Wood, 2017**; **Green & Silverman, 1994**; **de Boor, 1978**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/gam`
- **Payload (`GAMSplineAnalysisRequest`):**
  ```json
  {
    "predictor_question_id": "UUID_câu_hỏi_dự_báo_X",
    "outcome_question_id": "UUID_câu_hỏi_kết_quả_Y",
    "n_knots": 5,
    "smoothing_penalty": 1.0,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Hàm Cơ sở Natural Cubic Spline (Hastie et al., 2009):**
     Với $K$ mốc Knots $k_1 < k_2 < \dots < k_K$ đặt tại các phân vị phân bố của $X$:
     $$d_k(x) = \frac{(x - k_k)_+^3 - (x - k_K)_+^3}{k_K - k_k}$$
     $$N_1(x) = x, \quad N_{k+1}(x) = d_k(x) - d_{K-1}(x) \quad (k = 1, \dots, K-2)$$
     Bảo đảm đường cong bậc 3 trơn liên tục tại các khoảng giữa và suy biến về đường thẳng tuyến tính ngoài biên ($x < k_1$ hoặc $x > k_K$).
  2. **Bậc Tự do Hiệu dụng (Effective Degrees of Freedom - EDF) & Điểm GCV:**
     Khớp bằng bình phương tối thiểu có phạt: $(B^T B + \Omega) \hat{\boldsymbol{\beta}} = B^T \mathbf{y}$ với $\Omega$ phạt các hệ số phi tuyến.
     $$\text{EDF} = \text{tr}\left((B^T B + \Omega)^{-1} B^T B\right)$$
     - $\text{EDF} \approx 2$: Quan hệ gần như tuyến tính thuần túy.
     - $\text{EDF} > 2.2$: Tồn tại độ cong uốn lượn phi tuyến rõ rệt.
     - **GCV Score (Generalized Cross-Validation; Wood, 2017):**
       $$\text{GCV} = \frac{\frac{1}{N} \text{RSS}}{(1 - \text{EDF}/N)^2}$$
  3. **Kiểm định Giả thuyết Phi tuyến tính (Non-linearity F-test):**
     So sánh phần dư của mô hình tuyến tính chuẩn $\text{RSS}_{\text{linear}}$ (df = 2) với mô hình GAM $\text{RSS}_{\text{gam}}$ (df = EDF):
     $$F = \frac{(\text{RSS}_{\text{linear}} - \text{RSS}_{\text{gam}}) / (\text{EDF} - 2)}{\text{RSS}_{\text{gam}} / (N - \text{EDF})}, \quad p = 1 - F_{\text{cdf}}(F; \text{EDF} - 2, N - \text{EDF})$$
     Nếu $p < .05$, bác bỏ giả định tuyến tính và xác nhận tồn tại cấu trúc phi tuyến có ý nghĩa thống kê.
  4. **Nhận diện Điểm Uốn & Ngưỡng Bão hòa (Turning Points / Local Extrema):**
     Đánh giá đạo hàm số $f'(x)$ trên lưới 100 điểm, tự động gắn nhãn các điểm cực đại (đỉnh trần bão hòa) hoặc cực tiểu (đáy phản hồi).
  5. **Đồ họa Vector SVG Đường cong Trơn kèm Dải băng Tin cậy 95% CI:**
     Vẽ đường cong trơn $f(x)$, dải băng bóng mờ 95% CI $\hat{y} \pm 1.96 \cdot \text{SE}(x)$, các điểm quan sát thực tế và các vạch mốc knots.
  6. **Đoạn Thuyết minh Chuẩn APA 7th Edition:**
     Tự động biên soạn báo cáo chuẩn mực nêu rõ cỡ mẫu $N$, EDF, GCV, hệ số $R^2_{\text{GAM}}$ so với $R^2_{\text{lin}}$, thống kê kiểm định $F$, và tọa độ các điểm uốn quan trọng.
- **Niêm phong kiểm toán:** Tự động ghi nhận `GAM_SPLINE_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.

## 54. Quantile Regression & Conditional Distributional Effects Engine

- **Mục đích:** Bóc tách và kiểm định tác động không đồng nhất của biến can thiệp/dự báo trên từng phân vị khác nhau của biến kết quả ($\tau \in [0.05, 0.95]$, ví dụ: nhóm điểm thấp $\tau = 0.10$, trung vị $\tau = 0.50$, nhóm xuất sắc $\tau = 0.90$), kháng lại triệt để ảnh hưởng của các ngoại lai nặng đuôi (heavy tails) và độ lệch phân bố (skewness) mà hồi quy trung bình OLS không thể nắm bắt (**Koenker & Bassett, 1978**; **Koenker, 2005**; **Angrist & Pischke, 2009**; **Portnoy & Koenker, 1997**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/quantile-regression`
- **Payload (`QuantileRegressionRequest`):**
  ```json
  {
    "predictor_question_id": "UUID_câu_hỏi_dự_báo_X",
    "outcome_question_id": "UUID_câu_hỏi_kết_quả_Y",
    "covariate_question_ids": ["UUID_đồng_biến_kiểm_soát_C1"],
    "quantiles": [0.10, 0.25, 0.50, 0.75, 0.90],
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Hàm Mất Mát Pinball Loss (Check Function):**
     $$\rho_\tau(u) = u \cdot (\tau - \mathbf{1}(u < 0))$$
     Ước lượng nghiệm tối ưu $\hat{\boldsymbol{\beta}}(\tau) = \arg\min_{\boldsymbol{\beta}} \sum_{i=1}^N \rho_\tau(y_i - \mathbf{x}_i \boldsymbol{\beta})$ thông qua thuật toán Huber-Smoothed Iteratively Reweighted Least Squares (IRLS; Koenker, 2005).
  2. **Ma trận Hiệp phương sai Tiệm cận Sandwich Koenker (2005):**
     $$\text{Cov}(\hat{\boldsymbol{\beta}}(\tau)) = \frac{\tau (1 - \tau)}{N} \left(\mathbf{X}^T \mathbf{F}_0 \mathbf{X}\right)^{-1} \left(\mathbf{X}^T \mathbf{X}\right) \left(\mathbf{X}^T \mathbf{F}_0 \mathbf{X}\right)^{-1}$$
     với mật độ phần dư tại 0 được ước lượng theo hàm Kernel dải thông tối ưu Hall & Sheather (1988).
  3. **Hệ số Xác định Giả Pseudo $R^1(\tau)$ (Koenker & Machado, 1999):**
     $$R^1(\tau) = 1 - \frac{\sum \rho_\tau(y_i - \mathbf{x}_i \hat{\boldsymbol{\beta}}(\tau))}{\sum \rho_\tau(y_i - \hat{q}_\tau)}$$
     Lượng hóa tỷ lệ suy giảm tổn thất Pinball Loss so với mô hình chỉ có hằng số.
  4. **Kiểm định Sự Không Đồng Nhất Phân Vị (Interquantile Difference Test):**
     Kiểm định giả thuyết vô hiệu $H_0: \beta(\tau_{\text{high}}) = \beta(\tau_{\text{low}})$ (tác động đồng nhất trên toàn phổ phân bố):
     $$z = \frac{\hat{\beta}(\tau_{\text{high}}) - \hat{\beta}(\tau_{\text{low}})}{\sqrt{\text{SE}^2(\tau_{\text{high}}) + \text{SE}^2(\tau_{\text{low}})}}, \quad p = 2 \cdot (1 - \Phi(|z|))$$
     Nếu $p < .05$, xác nhận tác động có tính phân hóa không đồng nhất có ý nghĩa thống kê.
  5. **Đồ họa Vector SVG Koenker Process Plot:**
     Tự động tạo đồ thị quỹ đạo hệ số $\beta(\tau)$ với dải băng tin cậy 95% CI màu tím, đối sánh trực tiếp với đường nằm ngang nét đứt màu đỏ của OLS Mean và vùng tin cậy OLS xám mờ.
  6. **Đoạn Thuyết minh Chuẩn APA 7th Edition:**
     Tự động biên soạn báo cáo học thuật chuẩn mực so sánh hệ số góc trung bình OLS với các phân vị thấp $\tau=0.10$, trung vị $\tau=0.50$, phân vị cao $\tau=0.90$, và kết luận kiểm định sự không đồng nhất.
- **Niêm phong kiểm toán:** Tự động ghi nhận `QUANTILE_REGRESSION_EVALUATED` vào chuỗi sổ cái SHA-256.

## 55. Generalizability Theory (G-Theory: G-Study & D-Study) Engine

- **Mục đích:** Phân rã cấu trúc sai số đo lường khảo sát đa chiều thành các nguồn phương sai độc lập (Cá thể $p$, Câu hỏi $i$, Người đánh giá $r$, Tương tác $pi,e$) thay vì gộp chung như Cronbach's Alpha trong CTT, đồng thời thực hiện nghiên cứu quyết định D-Study nhằm tối ưu hóa số lượng câu hỏi và điều tra viên đạt độ tin cậy mong muốn (**Cronbach et al., 1972**; **Brennan, 2001**; **Shavelson & Webb, 1991**; **Webb et al., 2006**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/g-theory`
- **Payload (`GTheoryAnalysisRequest`):**
  ```json
  {
    "item_question_ids": ["UUID_câu_hỏi_1", "UUID_câu_hỏi_2", "UUID_câu_hỏi_3"],
    "rater_question_id": "UUID_câu_hỏi_phân_loại_điều_tra_viên (tùy chọn)",
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Nghiên cứu Khái quát hóa G-Study (ANOVA Variance Decomposition):**
     Với thiết kế chéo $p \times i$ (Persons $\times$ Items):
     $$X_{pi} = \mu + \nu_p + \nu_i + \nu_{pi,e}$$
     - Phương sai chân trị đối tượng đo lường (Universe Score Variance): $\sigma_p^2 = \frac{\text{MS}_p - \text{MS}_{pi,e}}{n_i}$.
     - Phương sai câu hỏi: $\sigma_i^2 = \frac{\text{MS}_i - \text{MS}_{pi,e}}{n_p}$.
     - Phương sai sai số tương tác và ngẫu nhiên: $\sigma_{pi,e}^2 = \text{MS}_{pi,e}$.
  2. **Nghiên cứu Quyết định D-Study (Decision Study):**
     Với số lượng câu hỏi giả định $n_i'$:
     - **Phương sai sai số tương đối (Relative Error Variance):**
       $$\sigma_{\delta}^2 = \frac{\sigma_{pi,e}^2}{n_i'}, \quad \text{SEM}_{\text{rel}} = \sqrt{\sigma_{\delta}^2}$$
     - **Phương sai sai số tuyệt đối (Absolute Error Variance):**
       $$\sigma_{\Delta}^2 = \frac{\sigma_i^2}{n_i'} + \frac{\sigma_{pi,e}^2}{n_i'}, \quad \text{SEM}_{\text{abs}} = \sqrt{\sigma_{\Delta}^2}$$
  3. **Hệ số Khái quát hóa (G-Coefficient $E\rho^2$) & Hệ số Đáng tin cậy (Phi Coefficient $\Phi$):**
     - **Quyết định Chuẩn mực Tương đối (Norm-referenced Decisions):**
       $$E\rho^2 = \frac{\sigma_p^2}{\sigma_p^2 + \sigma_{\delta}^2}$$
     - **Quyết định Tiêu chí Tuyệt đối (Criterion-referenced Decisions):**
       $$\Phi = \frac{\sigma_p^2}{\sigma_p^2 + \sigma_{\Delta}^2}$$
     - Ngưỡng chuẩn vàng: $E\rho^2 \ge 0.80$ và $\Phi \ge 0.80$.
  4. **Kịch bản Dự phóng Tối ưu hóa D-Study:**
     Mô phỏng tự động sự biến thiên của $E\rho^2$ và $\Phi$ khi thay đổi số câu hỏi $n_i'$ từ $n_i/2$ đến $2n_i$, giúp nhà nghiên cứu xác định quy mô khảo sát tiết kiệm chi phí nhất mà vẫn đảm bảo độ tin cậy.
  5. **Đồ họa Kép Vector SVG:**
     Tích hợp trực quan: Biểu đồ thanh xếp chồng phân rã phương sai G-Study + Đường cong D-Study đối sánh ngưỡng 0.80.
  6. **Đoạn Thuyết minh Chuẩn APA 7th Edition:**
     Tự động biên soạn báo cáo học thuật chuẩn mực theo Brennan (2001), nêu rõ phương sai từng thành phần, hệ số $E\rho^2$ tương đối và chỉ số $\Phi$ tuyệt đối.
- **Niêm phong kiểm toán:** Tự động ghi nhận `G_THEORY_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 56. Sharp Regression Discontinuity Design (RDD) & Local Polynomial Causal Engine

- **Mục đích:** Đánh giá hiệu quả tác động nhân quả cục bộ (Local Average Treatment Effect - LATE) tại ngưỡng chính sách/điểm cắt định trước ($c$) khi can thiệp được kích hoạt nghiêm ngặt ($D_i = \mathbf{1}\{X_i \ge c\}$), giải quyết triệt để nội sinh và thiên lệch chọn mẫu mà không cần thử nghiệm ngẫu nhiên kiểm soát (RCT) (**Thistlethwaite & Campbell, 1960**; **Hahn, Todd & van der Klaauw, 2001**; **Imbens & Lemieux, 2008**; **Imbens & Kalyanaraman, 2012**; **Calonico, Cattaneo & Titiunik, 2014**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/rdd`
- **Payload (`RDDAnalysisRequest`):**
  ```json
  {
    "running_question_id": "UUID_câu_hỏi_biến_chỉ_định_X",
    "outcome_question_id": "UUID_câu_hỏi_biến_kết_quả_Y",
    "cutoff": 50.0,
    "bandwidth": null,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Hồi quy Tuyến tính Cục bộ Hai Phía (Local Linear Kernel Regression):**
     - Hạt nhân tam giác (Triangular Kernel): $K(u) = (1 - |u|) \cdot \mathbf{1}\{|u| \le 1\}$ với $u = \frac{X_i - c}{h}$, gán trọng số tối ưu cho các quan sát nằm sát ngưỡng cắt.
     - Ước lượng độc lập cận trái ($X_i < c$) và cận phải ($X_i \ge c$) bằng hồi quy OLS gia quyền (WLS):
       $$\min_{\alpha_l, \beta_l} \sum_{i: X_i < c} K\left(\frac{X_i - c}{h}\right) \left[Y_i - \alpha_l - \beta_l (X_i - c)\right]^2$$
       $$\min_{\alpha_r, \beta_r} \sum_{i: X_i \ge c} K\left(\frac{X_i - c}{h}\right) \left[Y_i - \alpha_r - \beta_r (X_i - c)\right]^2$$
  2. **Ước lượng Tác động Nhân quả Cục bộ (Sharp RDD LATE Jump):**
     $$\hat{\tau}_{\text{RDD}} = \hat{\alpha}_r - \hat{\alpha}_l = \lim_{x \downarrow c} \mathbb{E}[Y \mid X=x] - \lim_{x \uparrow c} \mathbb{E}[Y \mid X=x]$$
  3. **Lựa chọn Độ rộng Cửa sổ Tối ưu theo Imbens-Kalyanaraman (2012):**
     - Tự động tính toán độ rộng dải băng $h_{\text{opt}} = C_K \cdot \left(\frac{2 \sigma^2(c)}{f(c) (m''(c))^2}\right)^{1/5} N^{-1/5}$ nhằm tối thiểu hóa sai số toàn phương trung bình (MSE).
     - Cho phép ghi đè băng thông thủ công khi nhà nghiên cứu cần kiểm tra độ nhạy (Sensitivity / Bandwidth robustness analysis).
  4. **Sai số Chuẩn Mạnh và Khoảng Tin cậy 95% CI:**
     - Tính sai số chuẩn vững trước phương sai sai số thay đổi (Heteroskedasticity-robust standard error):
       $$\text{SE}(\hat{\tau}) = \sqrt{\widehat{\text{Var}}(\hat{\alpha}_r) + \widehat{\text{Var}}(\hat{\alpha}_l)}$$
     - Tính giá trị $z$-statistic và $p$-value hai phía chuẩn mực.
  5. **Kiểm định Thao túng Phân phối Mật độ McCrary (2008):**
     - Chia dải băng thành các ô nhỏ để so sánh mật độ quan sát bên trái và bên phải ngưỡng cắt:
       $$\theta_{\text{McCrary}} = \ln(\hat{f}_r) - \ln(\hat{f}_l)$$
     - Cảnh báo vi phạm giả định liên tục nếu $p < 0.05$ (nghi vấn đối tượng tự chọn hoặc điều tra viên gian lận làm biến dạng phân bố quanh ngưỡng).
  6. **Phân nhóm Dữ liệu & Trực Quan Hóa Vector SVG (RDD Binned Scatter Plot):**
     - Gom nhóm theo các phân khoảng (bins) hai bên điểm cắt, biểu diễn giá trị trung bình từng ô bằng các điểm chấm scatter.
     - Vẽ hai đường hồi quy tuyến tính cục bộ kèm dải băng tin cậy 95% ribbon, đường đứt nét thẳng đứng đánh dấu ngưỡng $c$, và mũi tên chỉ thị bước nhảy gián đoạn $\hat{\tau}_{\text{RDD}}$.
  7. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động sinh văn bản báo cáo khoa học chi tiết: quy mô mẫu hiệu dụng trong dải băng ($N_{\text{eff}}$), băng thông tối ưu $h$, giá trị nhảy $\hat{\tau}$, sai số chuẩn SE, $z$-score, $p$-value, 95% CI, và kết quả kiểm định thao túng McCrary.
- **Niêm phong kiểm toán:** Tự động ghi nhận `RDD_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 57. Synthetic Control Method (SCM) & Comparative Policy Evaluation Engine

- **Mục đích:** Đánh giá định lượng tác động can thiệp chính sách hoặc sự kiện can thiệp cục bộ tại một đơn vị/khu vực cụ thể trên dữ liệu khảo sát lặp/chuỗi thời gian bằng cách xây dựng một đơn vị "đối chứng tổng hợp" (synthetic counterfactual) thông qua tổ hợp lồi tối ưu từ các đơn vị đối chứng chưa can thiệp ($W \ge 0, \sum W_j = 1$), kèm kiểm định hoán vị không gian (In-Space Placebo Permutation Test) để tính toán $p$-value thực nghiệm chính xác mà không đòi hỏi giả định phân phối chuẩn (**Abadie & Gardeazabal, 2003**; **Abadie, Diamond & Hainmueller, 2010**; **Abadie, 2021**; **Doudchenko & Imbens, 2016**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/synthetic-control`
- **Payload (`SyntheticControlAnalysisRequest`):**
  ```json
  {
    "unit_question_id": "UUID_câu_hỏi_đơn_vị_khu_vực",
    "period_question_id": "UUID_câu_hỏi_kỳ_chuỗi_thời_gian",
    "outcome_question_id": "UUID_câu_hỏi_biến_kết_quả_Y",
    "treated_unit": "Tên_hoặc_mã_đơn_vị_can_thiệp",
    "treatment_period": "Thời_điểm_bắt_đầu_can_thiệp_T0",
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Quy hoạch Phi tuyến Có Ràng buộc (Constrained Convex Optimization):**
     - Tìm vector trọng số $W^* = (w_2, \dots, w_{J+1})'$ thỏa mãn $w_j \ge 0$ và $\sum_{j=2}^{J+1} w_j = 1$ để cực tiểu hóa khoảng cách giữa đặc trưng tiền can thiệp của đơn vị can thiệp ($X_1$) và nhóm đối chứng tổng hợp ($X_0 W$):
       $$\min_{W} (X_1 - X_0 W)' V (X_1 - X_0 W) \quad \text{s.t. } w_j \ge 0, \sum w_j = 1$$
     - Ma trận trọng số $V$ chuẩn hóa thang đo theo phương sai mẫu nhằm đảm bảo tính bất biến thứ nguyên.
  2. **Đánh giá Quỹ đạo Đối chứng & Tác động Trung bình Can thiệp (ATT):**
     - Quỹ đạo phản thực nghiệm (Synthetic counterfactual series): $\hat{Y}_{1t} = \sum_{j=2}^{J+1} w_j^* Y_{jt}$ với mọi $t = 1, \dots, T$.
     - Tác động tại từng thời điểm $t > T_0$: $\hat{\alpha}_{1t} = Y_{1t} - \hat{Y}_{1t}$.
     - Tác động trung bình sau can thiệp (ATT): $\hat{\tau}_{\text{SCM}} = \frac{1}{T - T_0} \sum_{t=T_0+1}^T \hat{\alpha}_{1t}$.
  3. **Chỉ số Sai số Dự báo Toàn phương Trung bình (RMSPE):**
     - Sai số tiền can thiệp (Pre-intervention fit):
       $$\text{RMSPE}_{\text{pre}} = \sqrt{\frac{1}{T_0} \sum_{t=1}^{T_0} (Y_{1t} - \hat{Y}_{1t})^2}$$
     - Sai số hậu can thiệp (Post-intervention prediction error):
       $$\text{RMSPE}_{\text{post}} = \sqrt{\frac{1}{T - T_0} \sum_{t=T_0+1}^{T} (Y_{1t} - \hat{Y}_{1t})^2}$$
     - Tỷ số $\text{RMSPE Ratio} = \frac{\text{RMSPE}_{\text{post}}}{\text{RMSPE}_{\text{pre}}}$.
  4. **Kiểm định Hoán vị Không gian Placebo (In-Space Placebo Permutation Inference):**
     - Lần lượt gán giả định từng đơn vị đối chứng $j \in \{2, \dots, J+1\}$ là đơn vị can thiệp và giải bài toán SCM với pool đối chứng gồm các đơn vị còn lại (Abadie et al., 2010).
     - Tính tỷ số RMSPE ratio của từng đơn vị placebo.
     - Giá trị $p$-value thực nghiệm chính xác (Empirical $p$-value):
       $$p = \frac{\sum_{j=1}^{J+1} \mathbf{1}\left\{ \text{Ratio}_j \ge \text{Ratio}_{\text{treated}} \right\}}{J + 1}$$
     - Nếu $p < 0.05$, bác bỏ giả thuyết vô hiệu và kết luận tác động can thiệp có ý nghĩa thống kê cao.
  5. **Trực quan hóa Đồ họa Kép Vector SVG (Dual-Panel Trajectory & Gap Plot):**
     - Bảng trên: Đường diễn tiến Thực tế vs Đối chứng Tổng hợp kèm đường đứt nét đánh dấu kỳ can thiệp $T_0$.
     - Bảng dưới: Đường khoảng cách tác động (Gap) của đơn vị can thiệp nổi bật trên nền các đường placebo mờ của toàn bộ nhóm đối chứng.
  6. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động sinh văn bản báo cáo khoa học chi tiết: quy mô pool đối chứng ($J$), danh sách các đơn vị đóng góp trọng số lớn nhất kèm tỷ lệ %, chỉ số $\text{RMSPE}_{\text{pre}}$, tác động $\hat{\tau}_{\text{SCM}}$, $\text{RMSPE}_{\text{post}}$, tỷ số RMSPE ratio, và kết quả kiểm định giả dược $p$-value.
- **Niêm phong kiểm toán:** Tự động ghi nhận `SYNTHETIC_CONTROL_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 58. Small Area Estimation (SAE) & Fay-Herriot Empirical Bayes Engine

- **Mục đích:** Khắc phục triệt để hiện tượng phương sai lấy mẫu lớn và khoảng tin cậy quá rộng do cỡ mẫu nhỏ ($n_m < 30$) tại các tiểu vùng, khu vực địa lý, phòng ban hoặc phân khúc khách hàng bằng cách "vay mượn sức mạnh thống kê" (Borrowing Strength) xuyên khu vực thông qua mô hình phân cấp Bayes thực nghiệm EBLUP (**Fay & Herriot, 1979**; **Prasad & Rao, 1990**; **Pfeffermann, 2013**; **Rao & Molina, 2015**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/small-area-estimation`
- **Payload (`SmallAreaEstimationRequest`):**
  ```json
  {
    "area_question_id": "UUID_câu_hỏi_phân_loại_tiểu_vùng",
    "outcome_question_id": "UUID_câu_hỏi_biến_kết_quả_Y",
    "auxiliary_question_ids": ["UUID_biến_hỗ_trợ_1", "UUID_biến_hỗ_trợ_2"],
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Mô hình Hai Cấp Độ Khu vực (Two-Level Area-Level Hierarchical Model):**
     - Mô hình lấy mẫu (Sampling Model):
       $$y_m = \theta_m + e_m, \quad e_m \overset{\text{ind}}{\sim} \mathcal{N}(0, D_m)$$
       với $y_m$ là ước lượng khảo sát trực tiếp (Direct survey mean), và $D_m = s_m^2 / n_m$ là phương sai lấy mẫu thiết kế.
     - Mô hình liên kết tổng hợp (Linking Model):
       $$\theta_m = x_m' \beta + v_m, \quad v_m \overset{\text{iid}}{\sim} \mathcal{N}(0, \sigma_v^2)$$
       với $x_m$ là vector các biến hỗ trợ cấp tiểu vùng, và $\sigma_v^2$ là phương sai giữa các tiểu vùng chưa giải thích được.
  2. **Ước lượng Phương sai Mô hình $\hat{\sigma}_v^2$ & Hệ số Hồi quy GLS $\hat{\beta}$:**
     - Ước lượng $\sigma_v^2$ bằng thuật toán Fisher-Scoring / Phương pháp mô-men Fay-Herriot lặp:
       $$\sum_{m=1}^M \frac{(y_m - x_m' \tilde{\beta}(\sigma_v^2))^2}{\sigma_v^2 + D_m} = M - p$$
       với ràng buộc $\hat{\sigma}_v^2 \ge 0$.
     - Ước lượng hệ số hồi quy bằng Bình phương Tối thiểu Tổng quát (GLS):
       $$\hat{\beta} = \left(\sum_{m=1}^M \frac{x_m x_m'}{\hat{\sigma}_v^2 + D_m}\right)^{-1} \sum_{m=1}^M \frac{x_m y_m}{\hat{\sigma}_v^2 + D_m}$$
  3. **Hệ số Co rút (Shrinkage Factor $\gamma_m$) & Ước lượng Tuyến tính Không chệch Tốt nhất EBLUP:**
     $$\gamma_m = \frac{\hat{\sigma}_v^2}{\hat{\sigma}_v^2 + D_m} \in [0, 1]$$
     $$\hat{\theta}_m^{\text{EB}} = \gamma_m y_m + (1 - \gamma_m) x_m' \hat{\beta}$$
     - Tiểu vùng có cỡ mẫu lớn ($D_m \to 0$): $\gamma_m \to 1$ (tin tưởng gần như tuyệt đối vào dữ liệu trực tiếp).
     - Tiểu vùng có cỡ mẫu quá nhỏ ($D_m \to \infty$): $\gamma_m \to 0$ (vay mượn sức mạnh từ mô hình hồi quy toàn thể $x_m' \hat{\beta}$).
  4. **Sai số Toàn phương Trung bình Hiệu chỉnh Bậc hai Prasad & Rao (1990):**
     $$\text{MSE}(\hat{\theta}_m^{\text{EB}}) \approx g_{1m}(\hat{\sigma}_v^2) + g_{2m}(\hat{\sigma}_v^2) + 2 g_{3m}(\hat{\sigma}_v^2)$$
     - $g_{1m} = \gamma_m D_m$: sai số do phương sai ngẫu nhiên trong vùng.
     - $g_{2m} = (1 - \gamma_m)^2 x_m' (X' V^{-1} X)^{-1} x_m$: sai số do bất định khi ước lượng $\beta$.
     - $g_{3m} = \frac{D_m^2}{(\hat{\sigma}_v^2 + D_m)^3} \overline{\text{Var}}(\hat{\sigma}_v^2)$: sai số do bất định khi ước lượng $\sigma_v^2$.
     - Mức tăng hiệu quả thống kê (Efficiency Gain):
       $$\text{Efficiency Gain}_m = \left(1 - \frac{\sqrt{\text{MSE}_m}}{\sqrt{D_m}}\right) \times 100\%$$
  5. **Trực quan hóa Biểu đồ Co rút Rừng (Vector SVG Shrinkage Forest Plot):**
     - Biểu diễn đồng thời điểm ước lượng trực tiếp ($y_m \pm 1.96 \sqrt{D_m}$) và điểm co rút EBLUP ($\hat{\theta}_m^{\text{EB}} \pm 1.96 \sqrt{\text{MSE}_m}$) kèm đường mũi tên đứt nét thể hiện xu hướng co rút và mức độ thu hẹp khoảng tin cậy.
  6. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động sinh báo cáo khoa học chi tiết: số lượng tiểu vùng ($M$), phương sai $\hat{\sigma}_v^2$, hệ số co rút trung bình $\bar{\gamma}$, tỷ lệ tăng hiệu quả bình quân, và bảng hồi quy GLS.
- **Niêm phong kiểm toán:** Tự động ghi nhận `SMALL_AREA_ESTIMATION_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 59. Dynamic Event-Study & Staggered Difference-in-Differences Engine

- **Mục đích:** Phân tích cấu trúc tác động động lực học theo chuỗi thời gian của can thiệp chính sách hoặc sự kiện triển khai theo đợt (Staggered Rollout) với mốc chuẩn hóa cơ sở $k = -1$, kiểm định đồng thời tính hợp lệ của giả định xu hướng song song tiền can thiệp (Pre-Trends Wald Test) và đánh giá tác động tức thời lẫn tích lũy dài hạn (**Hausman & Rapson, 2018**; **Sun & Abraham, 2021**; **Callaway & Sant'Anna, 2021**; **Roth et al., 2023**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/event-study`
- **Payload (`EventStudyAnalysisRequest`):**
  ```json
  {
    "unit_question_id": "UUID_câu_hỏi_đơn_vị_chi_nhánh",
    "time_question_id": "UUID_câu_hỏi_mốc_thời_gian_kỳ",
    "outcome_question_id": "UUID_câu_hỏi_biến_kết_quả_Y",
    "event_time_question_id": "UUID_câu_hỏi_thời_điểm_bắt_đầu (tùy chọn cho staggered rollout)",
    "treated_units": ["Tên_đơn_vị_1", "Tên_đơn_vị_2"],
    "global_event_time": 3,
    "max_leads": 5,
    "max_lags": 5,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Mô hình Hồi quy Cố định Hai Chiều (Two-Way Fixed Effects Dynamic Specification):**
     $$Y_{it} = \alpha_i + \lambda_t + \sum_{k = -K, k \ne -1}^L \mu_k \cdot \mathbf{1}\{t - E_i = k\} + \epsilon_{it}$$
     - $k = t - E_i$: thời gian tương đối so với thời điểm can thiệp $E_i$.
     - Kỳ cơ sở liền trước $k = -1$ được chuẩn hóa cố định bằng $0$ ($\mu_{-1} \equiv 0$) để xác lập mốc so sánh chuẩn tắc theo khuyến nghị của Roth et al. (2023).
  2. **Ma trận Hiệp phương sai Bánh kẹp Vững Cụm (Cluster-Robust Sandwich Covariance):**
     $$\text{Cov}(\hat{\beta}) = (X'X)^{-1} \left(\sum_{i} X_i' e_i e_i' X_i\right) (X'X)^{-1}$$
     Đảm bảo sai số chuẩn vững trước tự tương quan chuỗi thời gian nội tại của từng đối tượng khảo sát và phương sai sai số thay đổi.
  3. **Kiểm định Đồng thời Xu hướng Song song Tiền Sự kiện (Pre-Trends Wald Test):**
     - Giả thuyết vô hiệu: $H_0: \mu_k = 0 \quad \forall k < -1$.
     - Thống kê kiểm định Wald $\chi^2$:
       $$W = \hat{\mu}_{\text{leads}}' \left[\text{Cov}(\hat{\mu}_{\text{leads}})\right]^{-1} \hat{\mu}_{\text{leads}} \sim \chi^2(\text{df})$$
     - Nếu $p \ge 0.05$: Giả định xu hướng song song được xác nhận vững chắc, loại trừ hiện tượng xu hướng tự nhiên từ trước gây hiểu lầm tác động chính sách.
  4. **Hồ sơ Động lực Tác động Hậu Can thiệp (Post-Treatment Dynamics):**
     - Tác động trung bình sau can thiệp: $\bar{\mu}_{\text{post}} = \frac{1}{L + 1} \sum_{k = 0}^L \mu_k$.
     - Tác động tích lũy (Cumulative effect): $\sum_{k = 0}^L \mu_k$.
  5. **Trực quan hóa Đồ họa Vector SVG (Dynamic Event-Study Leads & Lags Ribbon):**
     - Biểu diễn đồng thời đường ước lượng hệ số $\mu_k$, dải băng mờ tin cậy 95% Ribbon, thanh sai số chuẩn error bars, vạch đứt nét màu hổ phách phân tách tại thời điểm can thiệp $k = 0$, và đường chuẩn cơ sở $k = -1$.
  6. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động sinh báo cáo khoa học chi tiết: kết quả kiểm định Wald xu hướng song song, tác động động thái qua từng mốc tương đối, tác động trung bình $\bar{\mu}_{\text{post}}$, và tác động tích lũy.
- **Niêm phong kiểm toán:** Tự động ghi nhận `EVENT_STUDY_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 60. Bayesian Structural Time Series (BSTS) & Causal Impact Engine

- **Mục đích:** Đánh giá định lượng tác động nhân quả của một can thiệp chính sách hoặc chiến dịch truyền thông lên biến kết quả chuỗi thời gian khảo sát thông qua mô hình không gian trạng thái Bayes (Bayesian State-Space Models) và thuật toán Lọc Kalman (Kalman Filter / Smoother), dựng chuỗi quỹ đạo đối thực tế phản nghiệm (counterfactual trajectory) kèm dải bất định hậu nghiệm 95% Bayesian Credible Intervals mà không đòi hỏi nhóm đối chứng song song hoàn hảo (**Brodersen, Gallusser, Koehler, Remy & Scott, 2015**; **Harvey, 1989**; **Durbin & Koopman, 2012**; **Scott & Varian, 2014**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/bsts-causal-impact`
- **Payload (`BSTSCausalImpactRequest`):**
  ```json
  {
    "time_question_id": "UUID_câu_hỏi_mốc_thời_gian_kỳ",
    "outcome_question_id": "UUID_câu_hỏi_biến_kết_quả_Y",
    "intervention_time": "2024-Q3 hoặc 10 (mốc bắt đầu can thiệp)",
    "covariate_question_ids": ["UUID_chuỗi_kiểm_soát_X1", "UUID_chuỗi_kiểm_soát_X2"],
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Mô hình Không gian Trạng thái Cấp độ Cục bộ (Local Level State-Space Model):**
     $$\text{Phương trình quan sát: } y_t = \mu_t + \mathbf{x}_t \boldsymbol{\beta} + \epsilon_t, \quad \epsilon_t \sim \mathcal{N}(0, \sigma_\epsilon^2)$$
     $$\text{Phương trình trạng thái: } \mu_{t+1} = \mu_t + \eta_t, \quad \eta_t \sim \mathcal{N}(0, \sigma_\eta^2)$$
     - $\mu_t$: Mức cơ sở tiềm ẩn (latent local level) biến động ngẫu nhiên theo bước ngẫu nhiên (random walk).
     - $\mathbf{x}_t \boldsymbol{\beta}$: Thành phần hồi quy đồng biến ngoại sinh không chịu tác động của sự kiện.
     - $\sigma_\epsilon^2$: Phương sai nhiễu đo lường (observation variance).
     - $\sigma_\eta^2$: Phương sai nhiễu dịch chuyển trạng thái (system / state innovation variance).
  2. **Thuật toán Lọc Kalman Thuận & Dịch chuyển Ngược (Kalman Filter & State Smoother):**
     - Dự báo trạng thái: $a_{t|t-1} = a_{t-1|t-1}, \quad P_{t|t-1} = P_{t-1|t-1} + \sigma_\eta^2$.
     - Sai số đổi mới: $v_t = y_t - a_{t|t-1} - \mathbf{x}_t \boldsymbol{\beta}, \quad F_t = P_{t|t-1} + \sigma_\epsilon^2$.
     - Hệ số khuếch đại Kalman (Kalman Gain): $K_t = P_{t|t-1} / F_t$.
     - Cập nhật hậu nghiệm: $a_{t|t} = a_{t|t-1} + K_t v_t, \quad P_{t|t} = P_{t|t-1} (1 - K_t)$.
  3. **Ước lượng Quỹ đạo Phản thực tế Hậu can thiệp (Counterfactual Inference):**
     - Khóa thông số lọc trạng thái tại kỳ tiền can thiệp $t \le T_0$ và phóng chiếu chuỗi giả định $\hat{y}_t = a_{t|T_0} + \mathbf{x}_t \boldsymbol{\beta}$ với sai số phương sai mở rộng dần $P_{t|T_0} + \sigma_\epsilon^2$ cho mọi $t > T_0$.
     - Khoảng tin cậy 95% Bayesian Credible Interval: $[\hat{y}_t - 1.96 \sqrt{\text{Var}_t}, \hat{y}_t + 1.96 \sqrt{\text{Var}_t}]$.
  4. **Chỉ số Tác động Điểm, Tích lũy & Tương đối (Pointwise & Cumulative Effects):**
     - Tác động điểm tại kỳ $t$: $\delta_t = y_t - \hat{y}_t$.
     - Tác động điểm bình quân: $\bar{\delta}_{\text{post}} = \frac{1}{T - T_0} \sum_{t = T_0 + 1}^T \delta_t$.
     - Tác động tích lũy (Cumulative causal effect): $\Delta_{\text{cum}} = \sum_{t = T_0 + 1}^T \delta_t$.
     - Tỷ lệ tác động tương đối: $\Delta_{\text{rel}} = \frac{\Delta_{\text{cum}}}{\sum_{t=T_0+1}^T \hat{y}_t} \times 100\%$.
  5. **Xác suất Hậu nghiệm & Giá trị $p$-value Đuôi Bayes (Posterior Tail Area Probability):**
     - Ước lượng xác suất tác động ngẫu nhiên qua diện tích đuôi chuẩn:
       $$p = 2 \cdot \left(1 - \Phi\left(\frac{|\bar{\delta}_{\text{post}}|}{\text{SE}_{\bar{\delta}}}\right)\right)$$
     - Nếu $p < 0.05$: Khẳng định can thiệp tạo ra bước chuyển biến nhân quả có ý nghĩa thống kê cao.
  6. **Trực quan hóa Đồ thị Động học 3 Tầng Vector SVG (Tri-Panel Causal Trajectory Plot):**
     - Tầng 1: Chuỗi Thực tế $Y_t$ vs Đối thực tế $\hat{Y}_t$ kẹp dải băng mờ Credible Interval 95% và vạch đứt nét can thiệp $T_0$.
     - Tầng 2: Chuỗi tác động điểm thời gian (Pointwise Impact $\delta_t$) dao động quanh đường cơ sở 0.
     - Tầng 3: Chuỗi tác động tích lũy dồn dập (Cumulative Impact) theo thời gian.
  7. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực khoa học theo Brodersen et al. (2015): nêu rõ số kỳ tiền và hậu can thiệp, giá trị thực tế bình quân $\bar{Y}_{\text{post}}$, giá trị phản thực tế $\hat{Y}_{\text{post}}$, tác động điểm $\bar{\delta}$, tác động tích lũy $\Delta_{\text{cum}}$, tỷ lệ % tương đối, và xác suất đuôi hậu nghiệm $p$.
- **Niêm phong kiểm toán:** Tự động ghi nhận `BSTS_CAUSAL_IMPACT_EVALUATED` vào chuỗi sổ cái SHA-256.















---

## 61. Doubly Robust Augmented Inverse Probability Weighting (AIPW) & CATE Engine

- **Mục đích:** Ước lượng tác động can thiệp trung bình (Average Treatment Effect - ATE) và phân tích tính không đồng nhất của tác động can thiệp theo từng phân khúc khách hàng / nhân khẩu học (Conditional Average Treatment Effects - CATE) trên dữ liệu khảo sát quan sát không ngẫu nhiên (non-randomized observational surveys), kết hợp đồng thời mô hình xác suất khuynh hướng (Propensity Score Model $\hat{e}(X)$) và mô hình hồi quy kết quả (Outcome Regression Model $\hat{\mu}(W, X)$) để đạt được **tính kép vững (Double Robustness)**: ước lượng hội tụ không chệch và tiệm cận hiệu quả nếu **ít nhất một trong hai mô hình** được chỉ định đúng (**Robins, Rotnitzky & Zhao, 1994**; **Chernozhukov et al., 2018**; **Athey & Wager, 2019**; **Crump et al., 2009**; **Kennedy, 2023**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/aipw-cate`
- **Payload (`AIPWCATERequest`):**
  ```json
  {
    "treatment_question_id": "UUID_câu_hỏi_can_thiệp_W",
    "outcome_question_id": "UUID_câu_hỏi_biến_kết_quả_Y",
    "confounder_question_ids": ["UUID_đồng_biến_X1", "UUID_đồng_biến_X2"],
    "subgroup_question_id": "UUID_câu_hỏi_phân_khúc_nhóm (tùy chọn cho CATE)",
    "treatment_value": "Nhãn gán can thiệp W=1 (tùy chọn, mặc định 1/true/yes/có)",
    "trim_alpha": 0.05,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Mô hình Hồi quy Logistic Xác suất Khuynh hướng (Propensity Score Estimation):**
     $$\hat{e}_i = \mathbb{P}(W_i = 1 \mid \mathbf{X}_i) = \frac{1}{1 + \exp(-\mathbf{X}_i \hat{\boldsymbol{\gamma}})}$$
     - Tối ưu hóa hợp lý cực đại có điều chuẩn L2 ($\lambda = 10^{-4}$) qua thuật toán L-BFGS-B để triệt tiêu hiện tượng phân tách hoàn hảo (quasi-complete separation).
  2. **Cắt lọc Vùng Hỗ trợ Chung Biên Tối ưu theo Crump et al. (2009):**
     - Loại bỏ các quan sát có xác suất khuynh hướng cực đoan: $\hat{e}_i \notin [\alpha, 1 - \alpha]$ (mặc định $\alpha = 0.05$) để kiểm soát phương sai tiệm cận của trọng số nghịch đảo.
  3. **Mô hình Hồi quy Kết quả Riêng biệt (Outcome Regression Models):**
     - Nhóm Can thiệp ($W=1$): $\hat{\mu}_1(\mathbf{X}) = \mathbf{X} \hat{\boldsymbol{\beta}}_1$ (Ridge regression).
     - Nhóm Đối chứng ($W=0$): $\hat{\mu}_0(\mathbf{X}) = \mathbf{X} \hat{\boldsymbol{\beta}}_0$ (Ridge regression).
  4. **Điểm số Kép Vững Phản nghiệm (Doubly Robust Pseudo-Outcomes $\hat{\Gamma}_i$):**
     $$\hat{\Gamma}_i = \hat{\mu}_1(\mathbf{X}_i) - \hat{\mu}_0(\mathbf{X}_i) + \frac{W_i (Y_i - \hat{\mu}_1(\mathbf{X}_i))}{\hat{e}_i} - \frac{(1 - W_i)(Y_i - \hat{\mu}_0(\mathbf{X}_i))}{1 - \hat{e}_i}$$
  5. **Ước lượng Tác động Trung bình Can thiệp (AIPW ATE) & Sai số Chuẩn Sandwich:**
     $$\hat{\tau}_{\text{AIPW}} = \frac{1}{N_{\text{eff}}} \sum_{i=1}^{N_{\text{eff}}} \hat{\Gamma}_i$$
     $$\widehat{\text{Var}}(\hat{\tau}_{\text{AIPW}}) = \frac{1}{N_{\text{eff}} (N_{\text{eff}} - 1)} \sum_{i=1}^{N_{\text{eff}}} (\hat{\Gamma}_i - \hat{\tau}_{\text{AIPW}})^2$$
     $$\text{SE} = \sqrt{\widehat{\text{Var}}(\hat{\tau}_{\text{AIPW}})}, \quad z = \frac{\hat{\tau}_{\text{AIPW}}}{\text{SE}}, \quad p = 2 \cdot (1 - \Phi(|z|))$$
     $$\text{CI}_{95\%} = [\hat{\tau}_{\text{AIPW}} - 1.96 \cdot \text{SE}, \hat{\tau}_{\text{AIPW}} + 1.96 \cdot \text{SE}]$$
  6. **Phân tích Không đồng nhất Phân khúc (Subgroup CATE Heterogeneity):**
     - Ước lượng tác động riêng cho từng phân khúc $g$: $\hat{\tau}_g = \frac{1}{N_g} \sum_{i \in g} \hat{\Gamma}_i$ kèm sai số chuẩn $\text{SE}_g$ và khoảng tin cậy 95% CI.
     - Kiểm định Omnibus ANOVA trên điểm số $\hat{\Gamma}_i$ ($F$-statistic, $p$-value) để chứng minh xem sự phân hóa hiệu ứng giữa các nhóm có ý nghĩa thống kê hay chỉ do biến thiên ngẫu nhiên.
  7. **Trực quan hóa Đồ thị Động học Kép Vector SVG (Dual-Panel Overlap & Forest Plot):**
     - Panel A: Phân bố mật độ xác suất khuynh hướng $\hat{e}(\mathbf{X})$ (Histogram so sánh Treated vs Control và vạch đỏ cắt lọc Crump $\alpha$).
     - Panel B: Biểu đồ Rừng (Forest Plot) hiệu ứng CATE từng phân khúc với thanh sai số 95% CI đối sánh trực tiếp với đường chuẩn AIPW ATE toàn thể.
  8. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực khoa học theo Robins et al. (1994) và Chernozhukov et al. (2018): nêu rõ cỡ mẫu $N$, số mẫu cắt lọc, tác động $\hat{\tau}_{\text{AIPW}}$, SE, $z$-score, $p$-value, chênh lệch ngây thơ (Naive Difference), độ lệch chọn lọc ước tính (Selection Bias), và kết quả kiểm định không đồng nhất phân khúc.
- **Niêm phong kiểm toán:** Tự động ghi nhận `AIPW_CATE_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 62. Instrumental Variables Two-Stage Least Squares (2SLS) & Weak Instrument Diagnostics Engine

- **Mục đích:** Xử lý và triệt tiêu triệt để hiện tượng thiên lệch nội sinh (Endogeneity Bias), thiên lệch do biến bị bỏ sót (Omitted Variable Bias), đồng thời tính (Simultaneity) và sai số đo lường (Measurement Error) của biến giải thích quan sát trong khảo sát thông qua phương pháp Biến Công cụ Bình phương Tối thiểu Hai Giai đoạn (2SLS), đồng thời cung cấp đầy đủ hệ thống chẩn đoán biến công cụ yếu theo chuẩn mực Stock & Yogo (2005), kiểm định tính nội sinh Wu-Hausman (1978), và kiểm định ràng buộc nhận diện thừa Sargan-Hansen (1982) (**Wright, 1928**; **Angrist & Imbens, 1995**; **Staiger & Stock, 1997**; **Stock & Yogo, 2005**; **Hausman, 1978**; **Sargan, 1958**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/iv-2sls`
- **Payload (`IV2SLSRequest`):**
  ```json
  {
    "outcome_question_id": "UUID_câu_hỏi_kết_quả_Y",
    "endogenous_question_id": "UUID_câu_hỏi_dự_báo_nội_sinh_X",
    "instrument_question_ids": ["UUID_biến_công_cụ_Z1", "UUID_biến_công_cụ_Z2"],
    "control_question_ids": ["UUID_kiểm_soát_ngoại_sinh_W1"],
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Hồi quy Giai đoạn 1 (First-Stage Regression):**
     $$\mathbf{X} = \mathbf{Z}_{\text{full}} \boldsymbol{\gamma} + \mathbf{v}$$
     - $\mathbf{Z}_{\text{full}} = [\mathbf{1}, \mathbf{W}, \mathbf{Z}]$: ma trận gồm hằng số, các biến kiểm soát ngoại sinh $\mathbf{W}$, và các biến công cụ ngoại sinh loại trừ $\mathbf{Z}$.
     - Giá trị dự báo khớp giai đoạn 1: $\hat{\mathbf{X}} = \mathbf{Z}_{\text{full}} \hat{\boldsymbol{\gamma}}$.
  2. **Chẩn đoán Biến Công cụ Yếu (Weak Instrument Diagnostics - Staiger & Stock 1997; Stock & Yogo 2005):**
     - Thống kê $F$ giai đoạn một kiểm định $H_0: \boldsymbol{\gamma}_{\mathbf{Z}} = \mathbf{0}$:
       $$F = \frac{(\text{RSS}_{\text{restr}} - \text{RSS}_{\text{unrestr}}) / L}{\text{RSS}_{\text{unrestr}} / (N - K)}$$
     - **Quy tắc Staiger & Stock (1997):** Nếu $F < 10.0$, biến công cụ bị coi là yếu (weak instrument), tiềm ẩn rủi ro thiên lệch đáng kể cho ước lượng 2SLS.
     - **Ngưỡng tới hạn Stock & Yogo (2005):** Đối chiếu với các giá trị tới hạn cho độ lệch tương đối 10% và 15% (ví dụ $F_{\text{crit}} = 16.38, 8.96$ với $L=1$).
  3. **Ước lượng Cấu trúc Giai đoạn 2 (Second-Stage 2SLS Structural Estimation):**
     - Hồi quy $\mathbf{Y}$ theo ma trận thiết kế chứa $\hat{\mathbf{X}}$ thay vì $\mathbf{X}$ thô:
       $$\hat{\boldsymbol{\beta}}_{\text{2SLS}} = (\hat{\mathbf{X}}^*{'}\hat{\mathbf{X}}^*)^{-1} \hat{\mathbf{X}}^*{'} \mathbf{Y}$$
     - **Hiệu chỉnh Ma trận Hiệp phương sai Asymptotic:**
       Phần dư cấu trúc thực sự phải được tính trên $\mathbf{X}$ gốc: $e_i^* = Y_i - \mathbf{X}_i^* \hat{\boldsymbol{\beta}}_{\text{2SLS}}$.
       $$\widehat{\text{Var}}(\hat{\boldsymbol{\beta}}_{\text{2SLS}}) = \hat{\sigma}^2 (\hat{\mathbf{X}}^*{'}\hat{\mathbf{X}}^*)^{-1}, \quad \hat{\sigma}^2 = \frac{1}{N - K} \sum_{i=1}^N (e_i^*)^2$$
  4. **Kiểm định Tính Nội sinh Wu-Hausman (Wu 1973, Hausman 1978):**
     - Thêm phần dư giai đoạn một $\hat{v}_i$ vào phương trình cấu trúc và kiểm định hệ số $\delta$:
       $$Y_i = \mathbf{W}_i \boldsymbol{\beta}_0 + X_i \beta_1 + \hat{v}_i \delta + u_i$$
     - Nếu $p < 0.05$, bác bỏ tính ngoại sinh của $X$, xác nhận 2SLS là cần thiết và OLS bị chệch.
  5. **Kiểm định Ràng buộc Nhận diện Thừa Sargan-Hansen (Sargan 1958, Hansen 1982):**
     - Khi số công cụ $L > 1$ (overidentified): hồi quy phần dư $e^*$ theo toàn bộ $\mathbf{Z}_{\text{full}}$:
       $$J = N \cdot R^2 \sim \chi^2(L - 1)$$
     - Nếu $p \ge 0.05$, hệ biến công cụ thỏa mãn giả định loại trừ (uncorrelated with error).
  6. **Trực quan hóa Đồ thị Động học Kép Vector SVG (Dual-Panel First-Stage & Forest Plot):**
     - Panel A: Đồ thị tán xạ giai đoạn 1 ($Z \to X$) kèm đường xu thế và hộp đồng hồ đo Thống kê $F$ First-Stage so sánh trực quan với ngưỡng chuẩn Staiger-Stock 10.0 và Stock-Yogo.
     - Panel B: Biểu đồ Rừng (Forest Plot) đối sánh trực diện hệ số cấu trúc không chệch 2SLS vs hệ số thiên lệch OLS với khoảng tin cậy 95% CI.
  7. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực khoa học theo Angrist & Imbens (1995) và Stock & Yogo (2005): nêu rõ số biến công cụ $L$, thống kê First-stage $F$, hệ số $\hat{\beta}_{\text{2SLS}}$, SE, $z$-score, $p$-value, hệ số OLS, độ lệch nội sinh, và kết quả kiểm định Wu-Hausman / Sargan $J$.
- **Niêm phong kiểm toán:** Tự động ghi nhận `TWO_STAGE_LEAST_SQUARES_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 63. Bifactor Psychometric Modeling & Omega Hierarchical Engine

- **Mục đích:** Phân rã cấu trúc phương sai của thang đo đa chiều thành một nhân tố chung duy nhất ($G$ - General Factor) bao quát toàn bộ các mục hỏi và các nhân tố nhóm cụ thể ($S_1, \dots, S_K$ - Group/Subscale Factors) hoàn toàn trực giao ($G \perp S_k$, $S_k \perp S_m$), giải quyết dứt điểm câu hỏi học thuật kinh điển: **"Thang đo có đủ tính đơn chiều thực chất (essential unidimensionality) để sử dụng một điểm số tổng hợp (composite sum score) duy nhất hay bắt buộc phải báo cáo từng tiểu thang đo riêng lẻ?"** (**Schmid & Leiman, 1957**; **Reise, 2012**; **Rodriguez, Reise & Haviland, 2016**; **McDonald, 1999**; **Gibbons et al., 2007**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/bifactor`
- **Payload (`BifactorAnalysisRequest`):**
  ```json
  {
    "subscales": [
      {
        "subscale_name": "Cognitive Worry",
        "question_ids": ["UUID_câu_hỏi_1", "UUID_câu_hỏi_2", "UUID_câu_hỏi_3"]
      },
      {
        "subscale_name": "Somatic Anxiety",
        "question_ids": ["UUID_câu_hỏi_4", "UUID_câu_hỏi_5", "UUID_câu_hỏi_6"]
      }
    ],
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Biến đổi Schmid-Leiman Trực giao (Schmid-Leiman Orthogonal Transformation):**
     - Trích xuất tải trọng bậc một cục bộ trong từng tiểu thang đo: $\mathbf{A} = [a_{ik}]$.
     - Phân tích nhân tố bậc hai trên ma trận tương quan giữa các tiểu thang đo $\mathbf{\Phi}$ thu được vector tải trọng bậc hai $\boldsymbol{\gamma} = (\gamma_1, \dots, \gamma_K)'$.
     - Tải trọng nhân tố chung $G$: $\lambda_{i0} = a_{ik} \cdot \gamma_k$.
     - Tải trọng tiểu thang đo đặc thù $S_k$: $\lambda_{ik} = a_{ik} \cdot \sqrt{1 - \gamma_k^2}$.
     - Phương sai sai số đặc trưng (Uniqueness): $u_i^2 = 1 - \lambda_{i0}^2 - \lambda_{ik}^2$.
  2. **Hệ số Độ tin cậy Toàn thể & Omega Phân cấp (Omega Hierarchical $\omega_h$):**
     - **Omega Total ($\omega_{\text{total}}$):** Tỷ lệ phương sai của tổng điểm do tất cả các nhân tố chung và nhóm giải thích:
       $$\omega_{\text{total}} = \frac{(\sum \lambda_{i0})^2 + \sum_k (\sum_{i \in k} \lambda_{ik})^2}{\text{Var}(\text{Total})}$$
     - **Omega Hierarchical ($\omega_h$):** Tỷ lệ phương sai của tổng điểm do duy nhất Nhân tố chung $G$ giải thích:
       $$\omega_h = \frac{(\sum \lambda_{i0})^2}{\text{Var}(\text{Total})}$$
     - **Ngưỡng chuẩn vàng (Rodriguez et al., 2016):** Nếu $\omega_h \ge 0.80$, phần lớn phương sai tin cậy phản ánh một biến tiềm ẩn đơn nhất, cho phép hợp nhất điểm tổng hợp (composite score) an toàn mà không làm méo mó bản chất tâm trắc học.
  3. **Hệ số Omega Phân cấp của Từng Tiểu thang đo ($\omega_{hs}$ - Subscale Viability):**
     $$\omega_{hs, k} = \frac{(\sum_{i \in k} \lambda_{ik})^2}{\text{Var}(\text{Subscale } k)}$$
     - Đánh giá xem tiểu thang đo có giữ được phương sai tin cậy độc lập sau khi đã bóc tách ảnh hưởng áp đảo của $G$. Nếu $\omega_{hs} < 0.50$, tiểu thang đo mất giá trị chẩn đoán riêng rẽ.
  4. **Tỷ lệ Phương sai Chung được Giải thích (Explained Common Variance - ECV):**
     $$\text{ECV} = \frac{\sum_i \lambda_{i0}^2}{\sum_i \lambda_{i0}^2 + \sum_k \sum_{i \in k} \lambda_{ik}^2}$$
     - Nếu $\text{ECV} \ge 0.60$ - $0.70$, khẳng định thang đo là đơn chiều thực chất (essentially unidimensional).
  5. **Tỷ lệ Tương quan Không Bị Ô nhiễm (Percent of Uncontaminated Correlations - PUC):**
     - Tỷ lệ các cặp tương quan giữa các mục thuộc các tiểu thang đo khác nhau so với tổng số cặp tương quan.
  6. **Chỉ số Cấp độ Mục hỏi I-ECV (Item-level Explained Common Variance):**
     $$I\text{-ECV}_i = \frac{\lambda_{i0}^2}{\lambda_{i0}^2 + \lambda_{ik}^2}$$
     - Nếu $I\text{-ECV}_i \ge 0.80$: Mục hỏi được phân loại là **Mục Trụ cột Nhân tố Chung (General Factor Anchor Item)**.
  7. **Trực quan hóa Đồ thị Cấu trúc Không gian Vector SVG (Bifactor Path Diagram):**
     - Nút tròn trung tâm nhân tố chung $G$ (màu tím) phát tán mũi tên liên kết đến toàn bộ các câu hỏi.
     - Các nút tròn tiểu thang đo $S_1, S_2, \dots$ (màu ngọc bích / lục bảo) chỉ liên kết đến các câu hỏi thuộc phân nhóm kèm tải trọng $\lambda_{ik}$.
  8. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực khoa học theo Reise (2012) và Rodriguez et al. (2016): nêu rõ cỡ mẫu $N$, số mục hỏi $P$, số tiểu thang $K$, $\omega_{\text{total}}$, $\omega_h$, ECV, PUC, khuyến nghị sử dụng điểm tổng hợp duy nhất vs báo cáo tiểu thang đo, và đánh giá tính độc lập của từng tiểu thang đo ($\omega_{hs}$).
- **Niêm phong kiểm toán:** Tự động ghi nhận `BIFACTOR_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 64. Panel Vector Autoregression (Panel VAR) & Dynamic Granger Causality Engine

- **Mục đích:** Mô hình hóa các quan hệ động học tương tác nội sinh đa chiều theo thời gian giữa các biến số khảo sát lặp (repeated multi-wave panel surveys) đồng thời kiểm soát triệt để các hiệu ứng cố định cá thể không quan sát được (unobserved individual fixed effects), kiểm định quan hệ nhân quả động Granger (Panel Granger Causality Wald Tests), và mô phỏng tác động lan tỏa của các cú sốc qua hàm phản ứng đẩy trực giao (Orthogonalized Impulse Response Functions - OIRF) kèm phân rã phương sai sai số dự báo (FEVD) (**Holtz-Eakin, Newey & Rosen, 1988**; **Arellano & Bover, 1995**; **Blundell & Bond, 1998**; **Abrigo & Love, 2016**; **Granger, 1969**; **Sims, 1980**).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/panel-var`
- **Payload (`PanelVARRequest`):**
  ```json
  {
    "unit_question_id": "UUID_câu_hỏi_đơn_vị_bảng_i",
    "time_question_id": "UUID_câu_hỏi_mốc_thời_gian_kỳ_t",
    "var1_question_id": "UUID_biến_nội_sinh_Y1",
    "var2_question_id": "UUID_biến_nội_sinh_Y2",
    "lags": 1,
    "irf_horizons": 6,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Đặc tả Mô hình PVAR(p) Hệ phương trình Động:**
     $$\mathbf{Y}_{it} = \sum_{l=1}^p \mathbf{A}_l \mathbf{Y}_{i, t-l} + \mathbf{u}_i + \boldsymbol{\epsilon}_{it}$$
     - $\mathbf{Y}_{it} = (Y_{1, it}, Y_{2, it})'$: vector 2 biến khảo sát nội sinh tại đơn vị $i$ và thời điểm $t$.
     - $\mathbf{u}_i$: vector hiệu ứng cố định cá thể (individual fixed effects).
     - $\mathbf{A}_l$: ma trận hệ số tự hồi quy bậc trễ $l$.
  2. **Biến đổi Trực giao Helmert Tiền tuyến (Forward Orthogonal Deviations; Arellano & Bover, 1995):**
     - Loại bỏ hiệu ứng $\mathbf{u}_i$ mà không tạo ra thiên lệch Nickell (1981) bằng cách trừ đi trung bình của các quan sát trong tương lai:
       $$y_{it}^* = c_t \left(y_{it} - \frac{1}{T - t} \sum_{s = t + 1}^T y_{is}\right), \quad c_t = \sqrt{\frac{T - t}{T - t + 1}}$$
     - Bảo toàn tính trực giao của các phần dư sai số ngẫu nhiên, cho phép ước lượng OLS / GMM nhất quán và hiệu quả.
  3. **Điều kiện Ổn định Hệ thống Động lực (Dynamic Stability Condition):**
     - Kiểm tra các giá trị riêng của ma trận đồng hành (companion matrix): $|\lambda_m| < 1 \quad \forall m$.
     - Nếu $|\lambda|_{\max} < 1$, hệ thống PVAR là dừng (stationary and stable), đảm bảo các hàm phản ứng đẩy OIRF suy giảm dần về 0 theo thời gian.
  4. **Kiểm định Nhân quả Granger Dữ liệu Bảng (Panel Granger Causality Wald Tests):**
     - Kiểm định giả thuyết vô hiệu $H_0: A_{12, l} = 0 \quad \forall l$ ($Y_2$ không gây ra $Y_1$ theo nghĩa Granger).
     - Kiểm định giả thuyết vô hiệu $H_0: A_{21, l} = 0 \quad \forall l$ ($Y_1$ không gây ra $Y_2$ theo nghĩa Granger).
     - Tính thống kê Wald $\chi^2(\text{df})$ và $p$-value: phân loại chính xác quan hệ thành: nhân quả một chiều ($Y_1 \to Y_2$ hoặc $Y_2 \to Y_1$), tương tác phản hồi hai chiều ($Y_1 \leftrightarrow Y_2$), hoặc độc lập động học.
  5. **Hàm Phản ứng Đẩy Trực giao Cholesky (Orthogonalized Impulse Response Functions - OIRF):**
     - Phân rã Cholesky ma trận hiệp phương sai phần dư $\boldsymbol{\Sigma}_\epsilon = \mathbf{P} \mathbf{P}'$.
     - Quỹ đạo phản ứng qua các bước chân trời $h = 0, \dots, H$: $\boldsymbol{\Psi}_h = \mathbf{\Phi}_h \mathbf{P}$.
  6. **Phân rã Phương sai Sai số Dự báo (Forecast Error Variance Decomposition - FEVD):**
     - Định lượng chính xác tỷ lệ phần trăm biến thiên phương sai của từng biến số được giải thích bởi các cú sốc nội tại so với cú sốc lan truyền từ biến còn lại tại các mốc chân trời dự báo.
  7. **Trực quan hóa Đồ thị Động học Kép Vector SVG (Dual-Panel OIRF & Granger Network):**
     - Panel A: Đồ thị hàm phản ứng đẩy OIRF thể hiện tác động của cú sốc 1 độ lệch chuẩn lan truyền qua $h$ kỳ tương lai.
     - Panel B: Sơ đồ mạng lưới nhân quả Granger có hướng với độ dày mũi tên và màu sắc phản ánh giá trị thống kê Wald $\chi^2$ và mức ý nghĩa thống kê $p$.
  8. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực khoa học theo Holtz-Eakin et al. (1988) và Abrigo & Love (2016): kiểm tra điều kiện ổn định $|\lambda|_{\max}$, hệ số tự hồi quy tự thân và biến chéo, thống kê kiểm định Wald $\chi^2$ nhân quả Granger, kết luận cấu trúc tương tác, và kết quả FEVD.
- **Niêm phong kiểm toán:** Tự động ghi nhận `PANEL_VAR_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 65. Latent Growth Curve Modeling (LGCM) Engine

- **Mục đích:** Mô hình hóa các quỹ đạo tăng trưởng cá nhân theo thời gian trong các cuộc khảo sát lặp nhiều đợt (multi-wave panel surveys, $T \ge 3$) dựa trên mô hình phương trình cấu trúc (SEM / Growth Curves) (**Meredith & Tisak, 1990**; **Bollen & Curran, 2006**; **Preacher et al., 2008**; **Duncan & Duncan, 2004**). Phân rã biến thiên thành hai biến tiềm ẩn: Mức khởi điểm ban đầu (Latent Intercept $\eta_0$) và Tốc độ gia tốc tăng trưởng (Latent Slope $\eta_1$). Đo lường sự không đồng nhất cá thể (individual heterogeneity), tương quan hiệp phương sai $\text{Cov}(\eta_0, \eta_1)$ (kiểm định hiệu ứng trần ceiling vs hiệu ứng tích lũy Matthew), đánh giá độ phù hợp cấu trúc (CFI, TLI, RMSEA, $\chi^2$), và vẽ đồ thị quỹ đạo cá nhân (spaghetti plot) cùng dải tin cậy kỳ vọng dân số 95%.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/latent-growth`
- **Payload (`LatentGrowthRequest`):**
  ```json
  {
    "wave_question_ids": ["UUID_dot_1", "UUID_dot_2", "UUID_dot_3", "UUID_dot_4"],
    "time_scores": [0.0, 1.0, 2.0, 3.0],
    "wave_labels": ["Tháng 1", "Tháng 3", "Tháng 6", "Tháng 12"],
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Đặc tả Mô hình Tuyến tính Tiềm ẩn (Linear Latent Basis):**
     $$\mathbf{y}_i = \boldsymbol{\Lambda} \boldsymbol{\eta}_i + \boldsymbol{\epsilon}_i, \quad \boldsymbol{\Lambda} = \begin{bmatrix} 1 & \lambda_{11} \\ 1 & \lambda_{21} \\ \vdots & \vdots \\ 1 & \lambda_{T1} \end{bmatrix}$$
     - $\boldsymbol{\eta}_i = [\eta_{0i}, \eta_{1i}]'$: Vector điểm tiềm ẩn cá nhân của Hệ số chặn (Intercept) và Độ dốc (Slope).
     - $\lambda_{t1} = t$ (thời gian chuẩn hóa: $0, 1, 2, \dots, T-1$).
  2. **Ước lượng Kỳ vọng Dân số (Latent Population Means):**
     $$\boldsymbol{\mu}_\eta = (\boldsymbol{\Lambda}' \boldsymbol{\Lambda})^{-1} \boldsymbol{\Lambda}' \bar{\mathbf{y}}$$
     - $\mu_{\text{intercept}}$: Mức độ điểm số trung bình của toàn dân số tại điểm xuất phát ban đầu ($t=0$).
     - $\mu_{\text{slope}}$: Tốc độ gia tăng/suy giảm trung bình kỳ vọng trên mỗi đơn vị thời gian.
     - Sai số chuẩn vững và thống kê kiểm định giả thuyết $z = \mu / \text{SE}(\mu)$, $p$-value.
  3. **Ma trận Hiệp phương sai Tiềm ẩn $\boldsymbol{\Psi}$ (Latent Factor Covariance):**
     $$\boldsymbol{\Psi} = \begin{bmatrix} \psi_{00} & \psi_{01} \\ \psi_{01} & \psi_{11} \end{bmatrix} = \text{Cov}(\boldsymbol{\eta})$$
     - $\psi_{00} = \text{Var}(\eta_0)$: Mức độ biến thiên cá thể tại điểm xuất phát (nếu $\psi_{00} > 0$: người tham gia khởi đầu ở các mức độ rất khác nhau).
     - $\psi_{11} = \text{Var}(\eta_1)$: Mức độ không đồng nhất cá thể về tốc độ tăng trưởng (nếu $\psi_{11} > 0$: có người tiến bộ nhanh, có người đi ngang hoặc thụt lùi).
     - $r_{01} = \frac{\psi_{01}}{\sqrt{\psi_{00} \psi_{11}}}$: Hệ số tương quan giữa điểm ban đầu và tốc độ phát triển:
       - $r_{01} < -0.20$: **Hiệu ứng Trần / Bù trừ (Ceiling Effect)**: Người khởi đầu thấp hơn có xu hướng tiến bộ nhanh hơn, khoảng cách dần thu hẹp.
       - $r_{01} > +0.20$: **Hiệu ứng Matthew / Lợi thế Tích lũy (Matthew Effect)**: Người đã có nền tảng cao hơn tiếp tục gia tăng nhanh hơn, gia tăng bất bình đẳng.
       - $-0.20 \le r_{01} \le +0.20$: Tốc độ phát triển độc lập với vị thế ban đầu.
  4. **Các Chỉ số Độ Phù hợp Cấu trúc Mô hình (SEM Goodness-of-Fit Indices):**
     - Ma trận hiệp phương sai ngụ ý mô hình: $\boldsymbol{\Sigma}(\boldsymbol{\theta}) = \boldsymbol{\Lambda} \boldsymbol{\Psi} \boldsymbol{\Lambda}' + \boldsymbol{\Theta}_\epsilon$.
     - Thống kê Khớp Chi-Square: $\chi^2 = (N - 1) F_{\text{ML}}$.
     - Bậc tự do mô hình: $\text{df} = \frac{T(T+1)}{2} + T - 5$.
     - **CFI (Comparative Fit Index)** và **TLI (Tucker-Lewis Index)**: Ngưỡng chuẩn mực $\ge 0.90$ (Tốt nếu $\ge 0.95$).
     - **RMSEA (Root Mean Square Error of Approximation)**: Ngưỡng chuẩn mực $\le 0.08$ (Tốt nếu $\le 0.05$).
  5. **Trực quan hóa Đồ thị Không gian Vector SVG Kép:**
     - Đồ thị spaghetti plot: Các đường mảnh biểu diễn quỹ đạo tăng trưởng thực nghiệm của từng cá nhân trong mẫu.
     - Đường cong xu thế dân số nổi bật kèm dải ruy băng mờ thể hiện khoảng tin cậy 95% ($[\mu_t - 1.96 \text{SE}, \mu_t + 1.96 \text{SE}]$).
     - Bảng thẻ viền nổi hiển thị trực quan các tham số $\mu_0, \mu_1, \psi_{00}, \psi_{11}, r_{01}$.
  6. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực khoa học theo Meredith & Tisak (1990) và Bollen & Curran (2006): nêu rõ cỡ mẫu $N$, số đợt sóng $T$, điểm trung bình và sai số chuẩn $\mu_{\text{intercept}}$ và $\mu_{\text{slope}}$, phương sai $\psi_{00}$ và $\psi_{11}$, hệ số tương quan $r_{01}$ kèm diễn giải bản chất động lực (bù trừ vs tích lũy), và toàn bộ các chỉ số độ phù hợp mô hình $\chi^2(\text{df}), p, \text{CFI}, \text{RMSEA}$.
- **Niêm phong kiểm toán:** Tự động ghi nhận `LATENT_GROWTH_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 66. Quantile Treatment Effects (QTE) & Distributional Treatment Effects Engine

- **Mục đích:** Đánh giá tác động nhân quả không đồng nhất của chính sách hoặc can thiệp trên toàn bộ phổ phân phối của biến kết quả (distributional causal inference) thay vì chỉ xem xét tác động lên trung bình mẫu ($ATE = \mathbb{E}[Y(1) - Y(0)]$) (**Firpo, 2007**; **Koenker & Bassett, 1978**; **Abadie, Angrist & Imbens, 2002**; **Chernozhukov, Fernandez-Val & Melly, 2013**). Phân tích hiệu ứng lượng vị $QTE(\tau) = q_1(\tau) - q_0(\tau)$ qua các mốc phân vị $\tau \in \{0.10, 0.20, \dots, 0.90\}$, cân bằng các biến nhiễu bằng trọng số nghịch đảo xu hướng (IPW), ước lượng sai số chuẩn tiệm cận bằng ước lượng mật độ hạt nhân Gaussian (Silverman bandwidth), kiểm định giả thuyết tác động hằng số (Constant Treatment Effect), và lượng hóa sự dịch chuyển bất bình đẳng qua $\Delta \text{IQR} = QTE(0.75) - QTE(0.25)$ và $\Delta (90-10) = QTE(0.90) - QTE(0.10)$.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/qte`
- **Payload (`QTERequest`):**
  ```json
  {
    "outcome_question_id": "UUID_câu_hỏi_biến_kết_quả_Y",
    "treatment_question_id": "UUID_câu_hỏi_biến_can_thiệp_D",
    "covariate_question_ids": ["UUID_biến_nhiễu_X1", "UUID_biến_nhiễu_X2"],
    "quantiles": [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90],
    "alpha_trim": 0.05,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Định nghĩa Hiệu ứng Lượng vị Can thiệp (Quantile Treatment Effects):**
     $$QTE(\tau) = Q_{Y(1)}(\tau) - Q_{Y(0)}(\tau) = \inf\{y: F_{Y(1)}(y) \ge \tau\} - \inf\{y: F_{Y(0)}(y) \ge \tau\}$$
  2. **Ước lượng Bán tham số Không phụ thuộc Mô hình (Firpo, 2007):**
     - Ước lượng xác suất xu hướng (Propensity Score) $\hat{e}(X) = P(D = 1 | X)$ qua hồi quy Logistic chính quy hóa $L_2$.
     - Áp dụng cắt gọt biên vi phạm cận trên/dưới: $\alpha \le \hat{e}(X) \le 1 - \alpha$.
     - Tính trọng số IPW chuẩn hóa cho từng nhóm:
       $$w_1(X) = \frac{D}{\hat{e}(X)}, \quad w_0(X) = \frac{1 - D}{1 - \hat{e}(X)}$$
     - Tính lượng vị đối chứng $q_0(\tau)$ và lượng vị can thiệp $q_1(\tau)$ trên phân phối tích lũy có trọng số.
  3. **Ước lượng Phương sai Tiệm cận & Kiểm định Giả thuyết (Asymptotic Variance):**
     $$\text{Var}(QTE(\tau)) = \frac{\tau(1 - \tau)}{N_1 \hat{f}_1(q_1(\tau))^2} + \frac{\tau(1 - \tau)}{N_0 \hat{f}_0(q_0(\tau))^2}$$
     - Hàm mật độ xác suất $\hat{f}_1$ và $\hat{f}_0$ được ước lượng thông qua hạt nhân Gaussian với độ rộng dải Silverman: $h = 1.06 \hat{\sigma} N^{-0.2}$.
     - Thống kê kiểm định $z = QTE(\tau) / \text{SE}(QTE(\tau))$, giá trị $p$, và khoảng tin cậy 95%: $[QTE(\tau) - 1.96 \text{SE}, QTE(\tau) + 1.96 \text{SE}]$.
  4. **Lượng hóa Tác động đến Bất bình đẳng & Hình dạng Phân phối:**
     - **Hiệu ứng Độ giãn Khoảng liên tứ phân vị (Interquartile Range Shift):**
       $$\Delta \text{IQR} = QTE(0.75) - QTE(0.25)$$
       - Nếu $\Delta \text{IQR} < 0$: **Thu hẹp bất bình đẳng (Compensatory / Compressive Effect)** (Người ở phân vị thấp được hưởng lợi nhiều hơn từ chính sách).
       - Nếu $\Delta \text{IQR} > 0$: **Gia tăng bất bình đẳng (Matthew Effect / Dispersive Effect)** (Người ở phân vị cao được hưởng lợi vượt trội).
       - Nếu $\Delta \text{IQR} \approx 0$: **Tác động song song (Uniform / Parallel Shift)**.
     - **Chênh lệch Khoảng cách Đuôi Phân phối:**
       $$\Delta(90-10) = QTE(0.90) - QTE(0.10)$$
     - **Kiểm định Phân hóa Tác động (Constant Treatment Effect Test):** So sánh độ lệch cực đại giữa $QTE(\tau)$ và $ATE$.
  5. **Trực quan hóa Đồ thị Không gian Vector SVG Kép (Dual-Panel QTE & Counterfactual CDFs):**
     - Panel A: Đường cong quỹ đạo QTE qua các phân vị $\tau \in [0.10, 0.90]$ với ruy băng dải tin cậy 95% phủ bóng và đường đứt nét tham chiếu ngang ATE.
     - Panel B: Đường cong hàm phân phối tích lũy đối chứng thực tế $F_{Y(1)}(y)$ (màu xanh lá) và $F_{Y(0)}(y)$ (màu hồng viền đứt) thể hiện trực quan khoảng cách dịch chuyển ngang tại từng mốc xác suất tích lũy.
  6. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực theo Firpo (2007) và Chernozhukov et al. (2013): quy mô mẫu $N, N_1, N_0$, giá trị ATE so sánh với Median QTE(0.50), giá trị chi tiết của các mốc lượng vị tiêu biểu (q = 0.10, 0.50, 0.90) kèm SE, z, p-value, và kết luận phân phối về xu thế bất bình đẳng (thu hẹp vs phân hóa).
- **Niêm phong kiểm toán:** Tự động ghi nhận `QUANTILE_TREATMENT_EFFECTS_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 67. Causal DAG & Structure Learning Engine (PC Algorithm)

- **Mục đích:** Tự động suy diễn cấu trúc đồ thị nhân quả có hướng (Directed Acyclic Graphs - DAG / CPDAG) từ dữ liệu khảo sát quan sát đa biến (**Spirtes, Glymour & Scheines, 2000**; **Pearl, 2009**; **Kalisch & Bühlmann, 2007**; **Meek, 1995**). Giải quyết triệt để hạn chế của các mạng lưới tương quan vô hướng (như EBICglasso) bằng cách định hướng luồng tác động nhân quả trực tiếp ($X \to Y$), loại bỏ liên kết giả mạo qua kiểm định độc lập có điều kiện Fisher $z$, nhận diện các cấu trúc v-structure / colliders ($X \to Z \leftarrow Y$), áp dụng các quy tắc suy diễn Meek để bảo đảm tính phi chu trình (acyclicity), và phân loại toàn diện thứ bậc nhân quả: Động lực gốc thượng nguồn (Root Causes), Biến trung gian (Mediators), và Điểm hấp thụ kết quả hạ nguồn (Terminal Sinks).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/causal-dag`
- **Payload (`CausalDAGRequest`):**
  ```json
  {
    "question_ids": ["UUID_câu_hỏi_1", "UUID_câu_hỏi_2", "UUID_câu_hỏi_3", "UUID_câu_hỏi_4"],
    "alpha": 0.05,
    "max_cond_size": 2,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Thuật toán PC Giai đoạn 1 (Skeleton Discovery):**
     - Bắt đầu từ đồ thị vô hướng đầy đủ $G_0 = (V, E)$ kết nối tất cả các cặp biến khảo sát.
     - Kiểm định độc lập có điều kiện $X \perp Y \mid \mathbf{S}$ với kích thước tập điều kiện tăng dần $d = 0, 1, \dots, d_{\max}$.
     - Tính hệ số tương quan riêng phần qua nghịch đảo ma trận hiệp phương sai con:
       $$r_{XY \mid \mathbf{S}} = -\frac{P_{12}}{\sqrt{P_{11} P_{22}}}, \quad \mathbf{P} = \boldsymbol{\Sigma}_{XY\mathbf{S}}^{-1}$$
     - Áp dụng phép biến đổi Fisher $z$:
       $$z = \frac{1}{2} \ln\left(\frac{1 + r}{1 - r}\right), \quad \sigma_z = \frac{1}{\sqrt{N - |\mathbf{S}| - 3}}$$
     - Nếu $p$-value $> \alpha$: xóa cạnh $(X, Y)$ và lưu trữ tập tách rời $\text{SepSet}(X, Y) = \mathbf{S}$.
  2. **Thuật toán PC Giai đoạn 2 (Collider Orientation - V-structures):**
     - Đối với mọi bộ ba không che chắn $X - Z - Y$ (trong đó $X$ và $Y$ không liền kề):
     - Nếu $Z \notin \text{SepSet}(X, Y)$: định hướng $X \to Z \leftarrow Y$ (v-structure / collider).
  3. **Thuật toán PC Giai đoạn 3 (Meek Orientation Rules):**
     - **Quy tắc 1 (Tránh tạo collider mới):** Nếu $X \to Y$ và $Y - Z$, đồng thời $X, Z$ không liền kề $\Rightarrow$ định hướng $Y \to Z$.
     - **Quy tắc 2 (Tránh tạo chu trình):** Nếu $X \to Z \to Y$ và $X - Y$ $\Rightarrow$ định hướng $X \to Y$.
     - **Quy tắc 3 (Quy tắc bổ sung Meek):** Định hướng các liên kết vô hướng còn lại sao cho đồ thị duy trì tính DAG / CPDAG hợp lệ.
  4. **Phân tích Thứ bậc Nhân quả & Vai trò Mạng lưới (Causal Hierarchy Analysis):**
     - Bậc vào (In-degree): Số lượng mũi tên nhân quả hướng vào biến (mức độ chịu chi phối).
     - Bậc ra (Out-degree): Số lượng mũi tên nhân quả phát xuất từ biến (sức mạnh chi phối).
     - **Nguyên nhân gốc (Root Causes / Exogenous Drivers):** Bậc ra $> 0$, Bậc vào $= 0$. Đây là các đòn bẩy can thiệp tối ưu nhất.
     - **Biến trung gian (Mediators / Transmission Nodes):** Bậc vào $> 0$, Bậc ra $> 0$.
     - **Kết quả hạ nguồn (Terminal Sinks / Outcomes):** Bậc vào $> 0$, Bậc ra $= 0$.
  5. **Trực quan hóa Đồ thị Không gian Vector SVG:**
     - Sơ đồ cấu trúc mạng lưới với các nút tròn phân màu sắc trực quan theo vai trò nhân quả: Ngọc lục bảo (Root Driver), Xanh da trời (Mediator), Vàng hổ phách (Terminal Sink).
     - Mũi tên định hướng vector với độ dày nét tương ứng độ lớn tương quan riêng phần.
  6. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực theo Spirtes et al. (2000) và Pearl (2009): quy mô mẫu $N$, số biến $P$, ngưỡng $\alpha$, số liên kết có hướng vs vô hướng, danh sách cụ thể các đòn bẩy thượng nguồn, mắt xích trung gian, và khuyến nghị can thiệp chính sách.
- **Niêm phong kiểm toán:** Tự động ghi nhận `CAUSAL_DAG_DISCOVERY_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 68. Marginal Structural Models (MSM) & Time-Varying Confounding Engine

- **Mục đích:** Ước lượng tác động nhân quả không thiên lệch trong các nghiên cứu khảo sát theo dõi dọc đa đợt (longitudinal multi-wave panel studies, $T \ge 2$) khi xuất hiện hiện tượng nhiễu biến thiên theo thời gian (time-varying confounding) và tương tác phản hồi giữa can thiệp và biến nhiễu ($A_{t-1} \to L_t \to A_t \to Y$) (**Robins, Hernán & Brumback, 2000**; **Hernán & Robins, 2024**; **Robins, 1986**; **Cole & Hernán, 2008**). Khắc phục hoàn toàn sự thất bại của các phương pháp hồi quy cổ điển và Fixed Effects (vốn gây ra thiên lệch chia tầng collider bias và chặn đứng các chuỗi tác động gián tiếp của can thiệp quá khứ) thông qua trọng số ổn định nghịch đảo xác suất xu hướng (Stabilized IPTW), so sánh độ chệch với mô hình OLS ngây thơ, và ước lượng sai số chuẩn vững dạng bánh kẹp sandwich Huber-White.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/msm-iptw`
- **Payload (`MSMAnalysisRequest`):**
  ```json
  {
    "treatment_question_ids": ["UUID_can_thiep_dot_1", "UUID_can_thiep_dot_2", "UUID_can_thiep_dot_3"],
    "confounder_question_ids": ["UUID_bien_nhieu_dot_1", "UUID_bien_nhieu_dot_2", "UUID_bien_nhieu_dot_3"],
    "outcome_question_id": "UUID_ket_qua_dich_cuoi_cung_Y",
    "wave_labels": ["Đợt 1", "Đợt 2", "Đợt 3"],
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Đặc tả Mô hình Cấu trúc Biên (Marginal Structural Model):**
     $$\mathbb{E}[Y^{\bar{a}}] = \beta_0 + \beta_1 \operatorname{Cum}(\bar{a}), \quad \operatorname{Cum}(\bar{a}) = \sum_{t=1}^T a_t$$
     - $\beta_1$: Hiệu ứng nhân quả biên trung bình trên mỗi đợt can thiệp tích lũy qua thời gian.
  2. **Ước lượng Trọng số Ổn định Tích lũy (Stabilized IPTW; Robins et al., 2000):**
     $$SW_i = \prod_{t=1}^T \frac{P(A_t = a_{it} \mid \bar{A}_{t-1} = \bar{a}_{i, t-1})}{P(A_t = a_{it} \mid \bar{A}_{t-1} = \bar{a}_{i, t-1}, \bar{L}_t = \bar{l}_{it})}$$
     - Tử số (Numerator Model): Hồi quy logistic xác suất can thiệp chỉ điều kiện trên lịch sử can thiệp quá khứ.
     - Mẫu số (Denominator Model): Hồi quy logistic xác suất can thiệp điều kiện trên cả lịch sử can thiệp và toàn bộ quá trình biến thiên của các biến nhiễu thời gian $\bar{L}_t$.
     - Trọng số ổn định tạo ra một tổng thể giả lập (pseudo-population) trong đó $A_t$ không còn bị nhiễu bởi $L_t$, đồng thời giữ phương sai ở mức tối thiểu so với trọng số không ổn định (Unstabilized Weights).
  3. **Chẩn đoán Phân phối Trọng số & Cắt gọt Cận biên (Weight Diagnostics & Truncation):**
     - Đánh giá $\operatorname{Mean}(SW) \approx 1.0$ (chỉ báo tính đúng đắn của mô hình xác suất xu hướng và giả định khả thi dương positivity).
     - Cắt gọt trọng số ở bách phân vị 1% và 99% để triệt tiêu các quan sát cực đoan làm nổ phương sai (Cole & Hernán, 2008).
  4. **Ước lượng Tham số & Sai số Chuẩn Vững Sandwich:**
     - Ước lượng hồi quy tuyến tính có trọng số $SW_i$ của $Y$ theo $\operatorname{Cum}(\bar{a})$.
     - Ma trận hiệp phương sai vững Huber-White Sandwich:
       $$\operatorname{Var}(\hat{\boldsymbol{\beta}}) = (\mathbf{X}' \mathbf{W} \mathbf{X})^{-1} \left[\sum_{i=1}^N w_i^2 e_i^2 \mathbf{x}_i \mathbf{x}_i'\right] (\mathbf{X}' \mathbf{W} \mathbf{X})^{-1}$$
     - Thống kê $z = \hat{\beta}_1 / \operatorname{SE}(\hat{\beta}_1)$, giá trị $p$, và khoảng tin cậy 95%: $[\hat{\beta}_1 - 1.96 \operatorname{SE}, \hat{\beta}_1 + 1.96 \operatorname{SE}]$.
  5. **Định lượng Thiên lệch Hồi quy Ngây thơ (Confounding Bias Analysis):**
     $$\operatorname{Bias}\% = \frac{\beta_{\text{Naive OLS}} - \beta_{\text{MSM}}}{|\beta_{\text{MSM}}|} \times 100\%$$
     - Phân loại trực quan: Nhiễu thổi phồng (Positive Confounding) vs Nhiễu che mờ (Negative Confounding / Suppression).
  6. **Trực quan hóa Đồ thị Không gian Vector SVG Kép (Dual-Panel SW & Trajectory):**
     - Panel A: Biểu đồ cột phân phối tần số của các trọng số ổn định $SW_i$ so với vạch chuẩn $SW = 1.0$.
     - Panel B: Đường dốc đáp ứng liều lượng tích lũy so sánh giữa mô hình nhân quả MSM (màu xanh ngọc lục bảo) và hồi quy ngây thơ OLS (đường đứt nét màu hồng viền).
  7. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực theo Robins et al. (2000) và Hernán & Robins (2024): quy mô mẫu $N$, số đợt sóng $T$, kiểm tra trung bình trọng số $\operatorname{Mean}(SW)$, hệ số nhân quả $\beta_{\text{MSM}}$ kèm SE, z, p-value, 95% CI, so sánh đối chuẩn với $\beta_{\text{Naive OLS}}$, và kết luận khoa học về thiên lệch thời gian.
- **Niêm phong kiểm toán:** Tự động ghi nhận `MARGINAL_STRUCTURAL_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 69. Generalized Estimating Equations (GEE) & Population-Averaged Longitudinal Engine

- **Mục đích:** Mô hình hóa tác động dân số trung bình (Population-Averaged Effects) trên các bộ dữ liệu khảo sát lặp dọc (longitudinal repeat-measures surveys) có tương quan nội cụm/cá nhân qua thời gian (**Liang & Zeger, 1986**; **Zeger, Liang & Albert, 1988**; **Diggle et al., 2002**; **Pan, 2001**; **Hardin & Hilbe, 2003**). Cung cấp phương pháp tiếp cận bán tham số chuẩn mực thay thế cho mô hình hiệu ứng ngẫu nhiên (GLMM/HLM), bảo đảm tính nhất quán tiệm cận của ước lượng $\boldsymbol{\beta}$ ngay cả khi cấu trúc ma trận tương quan làm việc (Working Correlation Matrix) bị chỉ định sai lệch, thông qua ma trận hiệp phương sai sai số chuẩn vững Sandwich Huber-White, hỗ trợ các họ phân phối Gaussian và Binomial, và tính tiêu chí thông tin bán hợp lý QIC (Quasi-likelihood Information Criterion) để lựa chọn cấu trúc tương quan tối ưu.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/gee`
- **Payload (`GEEAnalysisRequest`):**
  ```json
  {
    "cluster_question_id": "UUID_câu_hỏi_mã_đối_tượng_cụm",
    "time_question_id": "UUID_câu_hỏi_mốc_thời_gian_làn_sóng",
    "outcome_question_id": "UUID_câu_hỏi_biến_phụ_thuộc_Y",
    "predictor_question_ids": ["UUID_biến_dự_báo_X1", "UUID_biến_dự_báo_X2"],
    "family": "gaussian" | "binomial",
    "corstr": "exchangeable" | "ar1" | "independent",
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Hệ Phương trình Ước lượng Bán tham số (Quasi-Score Equations; Liang & Zeger, 1986):**
     $$\mathbf{U}(\boldsymbol{\beta}) = \sum_{i=1}^N \mathbf{D}_i' \mathbf{V}_i^{-1} (\mathbf{y}_i - \boldsymbol{\mu}_i) = \mathbf{0}$$
     - $\boldsymbol{\mu}_i = g^{-1}(\mathbf{X}_i \boldsymbol{\beta})$: Kỳ vọng có điều kiện dân số trung bình.
     - $\mathbf{D}_i = \frac{\partial \boldsymbol{\mu}_i}{\partial \boldsymbol{\beta}} = \mathbf{A}_i \mathbf{X}_i$ đối với hàm liên kết chính tắc (canonical link).
     - $\mathbf{A}_i = \operatorname{diag}(V(\mu_{it}))$: Ma trận phương sai biên ($V(\mu) = 1$ cho Gaussian, $V(\mu) = \mu(1 - \mu)$ cho Binomial).
  2. **Ma trận Hiệp phương sai Làm việc (Working Covariance Matrix $\mathbf{V}_i$):**
     $$\mathbf{V}_i = \phi \mathbf{A}_i^{1/2} \mathbf{R}_i(\alpha) \mathbf{A}_i^{1/2}$$
     - $\phi$: Hệ số tán xạ (dispersion parameter), ước lượng qua bình phương phần dư Pearson: $\hat{\phi} = \frac{1}{M - K} \sum_{i, t} e_{it}^2$.
     - $\mathbf{R}_i(\alpha)$: Ma trận tương quan làm việc kích thước $n_i \times n_i$:
       - **Exchangeable (Đồng nhất):** $\operatorname{Corr}(Y_{it}, Y_{is}) = \alpha \quad \forall t \neq s$.
       - **Autoregressive AR(1):** $\operatorname{Corr}(Y_{it}, Y_{is}) = \alpha^{|t - s|}$.
       - **Independent (Độc lập):** $\mathbf{R}_i = \mathbf{I}$.
  3. **Ước lượng Sai số Chuẩn Vững Bánh kẹp (Huber-White Sandwich Covariance):**
     $$\mathbf{V}_{\text{robust}} = \mathbf{M}_0^{-1} \mathbf{M}_1 \mathbf{M}_0^{-1}$$
     - $\mathbf{M}_0 = \sum_{i=1}^N \mathbf{D}_i' \mathbf{V}_i^{-1} \mathbf{D}_i$ (Ma trận thông tin mô hình mẫu).
     - $\mathbf{M}_1 = \sum_{i=1}^N \mathbf{D}_i' \mathbf{V}_i^{-1} (\mathbf{y}_i - \boldsymbol{\mu}_i) (\mathbf{y}_i - \boldsymbol{\mu}_i)' \mathbf{V}_i^{-1} \mathbf{D}_i$ (Ma trận hiệp phương sai ngoại vi thực nghiệm).
     - $\operatorname{SE}_{\text{robust}} = \sqrt{\operatorname{diag}(\mathbf{V}_{\text{robust}})}$: Bất biến vững chắc trước sai sót trong giả định tương quan $\mathbf{R}(\alpha)$.
  4. **Tiêu chí Lựa chọn Cấu trúc Tương quan QIC (Pan, 2001):**
     $$\operatorname{QIC} = -2 Q(\hat{\boldsymbol{\beta}}; \mathbf{I}) + 2 \operatorname{trace}(\mathbf{\Omega}_I^{-1} \mathbf{V}_{\text{robust}})$$
     - Cung cấp thước đo khoa học khách quan để chọn lựa giữa các cấu trúc Exchangeable vs AR(1) (giá trị QIC thấp hơn phản ánh cấu trúc tương quan sát thực hơn).
  5. **Trực quan hóa Đồ thị Không gian Vector SVG Kép (Dual-Panel Heatmap & Forest Plot):**
     - Panel A: Bản đồ nhiệt ma trận tương quan làm việc $\mathbf{R}(\hat{\alpha})$ thể hiện mức độ tương quan đo lường nội cụm.
     - Panel B: Đồ thị rừng (Forest plot) các hệ số hồi quy dân số trung bình kèm khoảng tin cậy 95% tính theo sai số chuẩn Sandwich Huber-White.
  6. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực theo Liang & Zeger (1986) và Diggle et al. (2002): nêu rõ số đối tượng $N$, số lượt quan sát $M$, họ phân phối, cấu trúc tương quan và tham số $\hat{\alpha}$, hệ số tán xạ $\hat{\phi}$, tiêu chí QIC, bảng các hệ số $\beta$ kèm robust SE, z-score, p-value, và khoảng tin cậy 95%.
- **Niêm phong kiểm toán:** Tự động ghi nhận `GEE_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 70. Exact Permutation & Randomization Inference Engine (Fisher's Sharp Null)

- **Mục đích:** Kiểm định ý nghĩa thống kê và suy luận nhân quả phân phối mẫu hữu hạn hoàn toàn phi tham số dựa trên Giả thuyết Không Sắc nét của Fisher (**Fisher, 1935**; **Rosenbaum, 2002**; **Ernst, 2004**; **Ho & Imai, 2006**; **Imbens & Rubin, 2015**). Khác với giả thuyết không yếu của Neyman ($H_0: \mathbb{E}[Y(1)] = \mathbb{E}[Y(0)]$), giả thuyết không sắc nét giả định $Y_i(1) = Y_i(0) \ \forall i$ (can thiệp không gây ra bất kỳ hiệu ứng nào trên từng cá thể riêng biệt). Dưới giả thuyết này, toàn bộ dữ liệu phản thực được xác định chính xác tuyệt đối, cho phép thiết lập phân phối xác suất hoán vị chính xác (Exact Permutation Distribution) trên không gian $B$ lần hoán vị ngẫu nhiên mà không đòi hỏi bất kỳ giả định tiệm cận chuẩn hay phương sai đồng nhất nào. Hỗ trợ tính toán hiệu số trung bình, hiệu số trung vị, thống kê thứ bậc Wilcoxon Rank Sum, ước lượng độ dịch chuyển vị trí Hodges-Lehmann ($\hat{\Delta}$) cùng khoảng tin cậy chính xác 95%, và so sánh đối chuẩn trực tiếp với kiểm định $t$ Welch tiệm cận cổ điển.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/randomization-inference`
- **Payload (`RandomizationInferenceRequest`):**
  ```json
  {
    "outcome_question_id": "UUID_câu_hỏi_biến_kết_quả_liên_tục_Y",
    "treatment_question_id": "UUID_câu_hỏi_biến_can_thiệp_nhị_phân_D",
    "num_permutations": 2000,
    "alternative": "two-sided" | "greater" | "less",
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Nguyên lý Hoán vị Dưới Giả thuyết Sắc nét (Fisher's Sharp Null Hypothesis):**
     $$H_0: Y_i(1) = Y_i(0) = Y_i^{\text{obs}} \quad \forall i \in \{1, \dots, N\}$$
     - Cơ chế ngẫu nhiên hóa (Random Assignment Mechanism) tạo ra phân phối lấy mẫu chính xác cho bất kỳ hàm thống kê kiểm định $T(\mathbf{D}, \mathbf{Y})$.
     - Mỗi hoán vị $\mathbf{d}^{(b)} \in \Omega$ là một phép phân bổ ngẫu nhiên lại nhãn can thiệp giữ nguyên số lượng $N_1$ và $N_0$.
  2. **Các Thống kê Kiểm định Phân phối Hoán vị (Exact Test Statistics):**
     - **Hiệu số Trung bình (Difference in Means):**
       $$T_{\text{mean}}(\mathbf{d}, \mathbf{y}) = \frac{1}{N_1} \sum_{i: d_i = 1} y_i - \frac{1}{N_0} \sum_{i: d_i = 0} y_i$$
     - **Hiệu số Trung vị (Difference in Medians):**
       $$T_{\text{median}}(\mathbf{d}, \mathbf{y}) = \operatorname{Median}(y \mid d = 1) - \operatorname{Median}(y \mid d = 0)$$
     - **Thống kê Thứ bậc Wilcoxon Rank Sum ($W$):**
       $$W(\mathbf{d}, \mathbf{y}) = \sum_{i: d_i = 1} \operatorname{Rank}(y_i)$$
  3. **Tính toán Exact P-Value (Phần mềm mẫu Monte Carlo Permutation):**
     $$p_{\text{exact}} = \frac{1 + \sum_{b=1}^B \mathbb{I}(|T^{(b)}| \ge |T^{\text{obs}}|)}{1 + B}$$
     - Áp dụng hiệu chỉnh mẫu hữu hạn chuẩn xác (Davison & Hinkley, 1997) bảo đảm $p$-value không bao giờ bị đánh giá 0 giả mạo khi $B$ hữu hạn.
  4. **Ước lượng Vị trí Hodges-Lehmann & Khoảng Tin cậy Chính xác 95%:**
     - Ước lượng điểm: $\hat{\Delta}_{\text{HL}} = \operatorname{Median}(\{y_{1, j} - y_{0, k} \mid 1 \le j \le N_1, 1 \le k \le N_0\})$.
     - Khoảng tin cậy 95% chính xác nghịch đảo kiểm định hoán vị: tìm ngưỡng bách phân vị $k_{\alpha/2}$ và $k_{1 - \alpha/2}$ trên phân phối của các hiệu cặp đôi pairwise differences (Hodges & Lehmann, 1963).
  5. **So sánh Đối chuẩn Tiệm cận Welch's $t$-test:**
     - Tính toán $t$-statistic và $p$-value từ kiểm định $t$ hai mẫu không đồng nhất phương sai (Welch, 1947) để đo lường độ lệch giữa suy luận tiệm cận chuẩn và suy luận chính xác phân phối mẫu nhỏ/lệch phân phối.
  6. **Trực quan hóa Đồ thị Không gian Vector SVG Kép (Permutation Histogram & Null Distribution):**
     - Panel A: Biểu đồ cột phân phối tần số thực nghiệm $T^{(b)}$ dưới $H_0$, đường thẳng nét liền màu ngọc lục bảo đánh dấu $T^{\text{obs}}$ thực tế và đường nét đứt đối xứng đánh dấu ngưỡng bác bỏ $\alpha = 0.05$.
     - Panel B: Đường cong hàm phân phối tích lũy thực nghiệm (ECDF) của các sai khác cặp Hodges-Lehmann với dải ranh giới 95% CI.
  7. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực khoa học theo Fisher (1935) và Rosenbaum (2002): nêu rõ cỡ mẫu can thiệp $N_1$ và đối chứng $N_0$, số lượng hoán vị $B$, thống kê quan sát $T^{\text{obs}}$, giá trị $p_{\text{exact}}$ kèm kết luận bác bỏ/chấp nhận $H_0$, thống kê Wilcoxon Rank Sum $W$, ước lượng điểm Hodges-Lehmann $\hat{\Delta}$ cùng khoảng tin cậy 95%, và so sánh với kiểm định tiệm cận Welch.
- **Niêm phong kiểm toán:** Tự động ghi nhận `RANDOMIZATION_INFERENCE_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 71. Extreme Value Theory (EVT) & Survey Tail Risk Modeling Engine

- **Mục đích:** Mô hình hóa các quan sát cực đoan ở vùng đuôi phân phối (Tail Risk & Outlier Science) theo phương pháp Peaks-Over-Threshold (POT) và Phân phối Pareto Tổng quát (Generalized Pareto Distribution - GPD) (**Pickands, 1975**; **Balkema & de Haan, 1974**; **Davison & Smith, 1990**; **McNeil & Frey, 2000**; **Coles, 2001**). Cho phép phát hiện các rủi ro hoạt động nghiêm trọng tiềm ẩn trong dữ liệu khảo sát (thời gian làm bài chậm đột biến, khiếu nại tài chính cực đại, mức độ bất mãn dữ dội) mà các chỉ số trung bình và độ lệch chuẩn Gaussian truyền thống hoàn toàn che khuất. Ước lượng chuẩn xác tham số hình dạng đuôi $\xi$ (Tail Index), tham số tỷ lệ $\sigma$, phân loại hành vi rủi ro đuôi (Fréchet / Gumbel / Weibull), tính toán các chỉ số quản trị rủi ro định lượng Value-at-Risk ($\text{VaR}_p$) và Kỳ vọng Tổn thất Đuôi (Expected Shortfall $\text{ES}_p$ / CVaR), kiểm định độ phù hợp Kolmogorov-Smirnov, và trực quan hóa Đồ thị Kỳ vọng Vượt trội (Mean Excess Plot) cùng Đường cong Sống sót Đuôi (Tail Survival Function).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/extreme-value`
- **Payload (`EVTAnalysisRequest`):**
  ```json
  {
    "metric_question_id": "UUID_câu_hỏi_biến_đo_lường_hoặc_rủi_ro_Y",
    "threshold_percentile": 0.90,
    "custom_threshold": null,
    "alpha_levels": [0.95, 0.99, 0.995],
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Định lý Pickands-Balkema-de Haan (1974, 1975):**
     Với ngưỡng $u$ đủ lớn, phân phối có điều kiện của các phần dư vượt ngưỡng $Y = X - u \mid X > u$ hội tụ tiệm cận về Phân phối Pareto Tổng quát (GPD):
     $$G_{\xi, \sigma}(y) = 1 - \left(1 + \frac{\xi y}{\sigma}\right)^{-1/\xi} \quad (y > 0, 1 + \xi y / \sigma > 0)$$
  2. **Phân loại Đặc tính Rủi ro Đuôi (Tail Classification):**
     - **$\xi > 0$ (Họ Fréchet / Đuôi Nặng Fat-Tail):** Suy giảm theo hàm lũy thừa (polynomial decay). Rủi ro xuất hiện các điểm cực đoan thảm khốc cao hơn nhiều so với phân phối chuẩn.
     - **$\xi = 0$ (Họ Gumbel / Đuôi Hàm Mũ Exponential):** $G_{0, \sigma}(y) = 1 - \exp(-y / \sigma)$. Rủi ro cực đoan suy giảm tương tự phân phối chuẩn hoặc phân phối mũ.
     - **$\xi < 0$ (Họ Weibull / Đuôi Chặn Trên Bounded Support):** Có giới hạn vật lý trên tại $u - \sigma / \xi$.
  3. **Ước lượng Tham số & Sai số Chuẩn Tiệm cận (MLE):**
     - Tối ưu hóa hàm log-likelihood hoặc phương pháp mô-men trọng số xác suất (PWM).
     - Sai số chuẩn tiệm cận (Davison & Smith, 1990): $\operatorname{SE}(\hat{\xi}) \approx \frac{|1 + \hat{\xi}|}{\sqrt{N_u}}$, $\operatorname{SE}(\hat{\sigma}) \approx \hat{\sigma} \sqrt{\frac{2(1 + \hat{\xi})}{N_u}}$.
  4. **Định lượng Giá trị Chịu Rủi ro (VaR) & Kỳ vọng Tổn thất Đuôi (Expected Shortfall):**
     $$\operatorname{VaR}_p = u + \frac{\sigma}{\xi} \left( \left(\frac{N}{N_u} (1 - p)\right)^{-\xi} - 1 \right)$$
     $$\operatorname{ES}_p = \frac{\operatorname{VaR}_p + \sigma - \xi u}{1 - \xi} \quad (\text{với } \xi < 1.0)$$
  5. **Kiểm định Độ phù hợp Kolmogorov-Smirnov & Biểu đồ Kỳ vọng Vượt trội (Mean Excess Plot):**
     - Đánh giá $e(u) = \mathbb{E}[X - u \mid X > u]$ trên một lưới ngưỡng tăng dần. Độ dốc dương khẳng định hành vi đuôi nặng ($\xi > 0$).
     - Kiểm định KS trên các phần dư vượt ngưỡng để bảo đảm mô hình GPD không vi phạm giả thiết phân phối thực nghiệm.
  6. **Trực quan hóa Đồ thị Không gian Vector SVG Kép (Dual-Panel EVT):**
     - Panel A: Đồ thị Kỳ vọng Vượt trội (Mean Excess Plot) thể hiện tính tuyến tính của $e(u)$ cùng vạch đánh dấu ngưỡng lựa chọn $u$.
     - Panel B: Đường cong hàm sống sót đuôi $S(x)$ trên thang logarit cùng các đường nét đứt định vị $\operatorname{VaR}_{95\%}$ và $\operatorname{VaR}_{99\%}$.
  7. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực khoa học: quy mô mẫu $N$, ngưỡng $u$, số lượng quan sát vượt ngưỡng $N_u$, xác suất vượt ngưỡng $\zeta_u$, hệ số $\xi$ và $\sigma$ kèm sai số chuẩn, kết quả kiểm định Kolmogorov-Smirnov, bảng chỉ số rủi ro $\operatorname{VaR}_p$ và $\operatorname{ES}_p$, cùng khuyến nghị quản trị rủi ro đuôi.
- **Niêm phong kiểm toán:** Tự động ghi nhận `EXTREME_VALUE_ANALYSIS_EVALUATED` vào chuỗi sổ cái SHA-256.

---

## 72. Joint Modeling (JM) of Longitudinal Trajectories & Panel Attrition Engine

- **Mục đích:** Mô hình hóa đồng thời (Joint Modeling) quỹ đạo tăng trưởng tiềm ẩn đo lường lặp qua thời gian và nguy cơ rời bỏ khảo sát/thất thoát mẫu (panel drop-off / attrition) (**Wulfsohn & Tsiatis, 1997**; **Henderson, Diggle & Dobson, 2000**; **Tsiatis & Davidian, 2004**; **Rizopoulos, 2010, 2012**). Khắc phục triệt để nghịch lý thiên lệch sống sót (Survivorship Bias) và giả định sai lầm về thất thoát ngẫu nhiên (MAR): khi những người trả lời có điểm số tâm lý/kinh tế suy giảm có xu hướng bỏ cuộc cao hơn, các mô hình hồi quy hỗn hợp tuyến tính (LMM/HLM) thông thường sẽ tạo ra quỹ đạo tăng trưởng giả mạo lạc quan. Phân tích ước lượng hàm liên kết đồng thời qua tham số liên kết $\alpha$ (Association parameter), tỷ số nguy cơ rời bỏ Hazard Ratio ($\text{HR} = \exp(\alpha)$), kiểm định tính khuyết có thông tin (Non-ignorable Attrition Test), dự báo động xác suất duy trì khảo sát (Dynamic Survival Predictions), và trực quan hóa Đồ thị Không gian Vector SVG kép.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/joint-model`
- **Payload (`JointModelAnalysisRequest`):**
  ```json
  {
    "subject_question_id": "UUID_câu_hỏi_mã_đối_tượng_ID",
    "time_question_id": "UUID_câu_hỏi_mốc_thời_gian_làn_sóng_T",
    "outcome_question_id": "UUID_câu_hỏi_biến_đo_lường_dọc_Y",
    "event_question_id": "UUID_chỉ_báo_bỏ_cuộc_tùy_chọn",
    "event_time_question_id": "UUID_thời_điểm_bỏ_cuộc_tùy_chọn",
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Phân mô hình Dọc Tuyến tính Hỗn hợp (Longitudinal LMM Submodel):**
     $$y_i(t) = m_i(t) + \epsilon_i(t) = (\beta_0 + b_{0i}) + (\beta_1 + b_{1i}) t + \epsilon_i(t)$$
     - $m_i(t)$: Quỹ đạo tiềm ẩn thực sự không có sai số đo lường.
     - $\mathbf{b}_i = [b_{0i}, b_{1i}]' \sim \mathcal{N}(\mathbf{0}, \boldsymbol{\Sigma}_b)$: Hiệu ứng ngẫu nhiên chặn và dốc cá thể.
     - $\epsilon_i(t) \sim \mathcal{N}(0, \sigma_\epsilon^2)$: Sai số đo lường độc lập.
  2. **Phân mô hình Sống sót & Nguy cơ Rời bỏ (Relative Risk Survival Submodel):**
     $$h_i(t) = h_0(t) \exp\left( \alpha m_i(t) \right)$$
     - $h_0(t)$: Hàm nguy cơ cơ sở (ước lượng phi tham số Breslow).
     - $\alpha$: Tham số liên kết (Association parameter) lượng hóa tác động trực tiếp của mức điểm tiềm ẩn $m_i(t)$ lên log-hazard rời bỏ khảo sát.
     - $\text{HR} = \exp(\alpha)$: Tỷ số nguy cơ thất thoát mẫu trên mỗi 1 đơn vị tăng của biến dọc.
  3. **Kiểm định Hao hụt Mẫu Phi ngẫu nhiên (Non-ignorable Attrition Wald Test):**
     - Giả thuyết $H_0: \alpha = 0$: Cơ chế thất thoát mẫu độc lập với điểm số dọc (Missing at Random - MAR hợp lệ).
     - Bác bỏ $H_0$ ($p < .05$): Khẳng định thất thoát mẫu mang tính thông tin / phi ngẫu nhiên (Non-ignorable Attrition). Joint Model là bắt buộc để tránh thiên lệch sống sót.
  4. **Dự báo Xác suất Duy trì Động (Dynamic Individualized Predictions; Rizopoulos 2011):**
     - Cho đối tượng có lịch sử điểm số đo lường đến làn sóng $t$, dự báo xác suất tiếp tục duy trì đến làn sóng tương lai $u > t$:
       $$\pi_i(u \mid t) = P(T_i > u \mid T_i > t, \mathcal{Y}_i(t)) = \exp\left( - \int_t^u h_0(s) \exp(\alpha m_i(s)) ds \right)$$
  5. **Trực quan hóa Đồ thị Không gian Vector SVG Kép (Dual-Panel JM):**
     - Panel A: Đồ thị Spaghetti quỹ đạo cá thể $y_i(t)$ (phân biệt màu xanh cho đối tượng duy trì và nét đứt đỏ cho đối tượng bỏ cuộc) lồng ghép đường quỹ đạo trung bình $\beta_0 + \beta_1 t$.
     - Panel B: Họ đường cong duy trì khảo sát $S(t)$ theo thời gian đối chiếu giữa nhóm điểm cao (+1 SD), điểm trung bình và điểm thấp (-1 SD).
  6. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực: quy mô $N$, số lượt đo lặp, số ca bỏ cuộc và kiểm duyệt, các hệ số cố định $\beta_0, \beta_1$, độ lệch chuẩn ngẫu nhiên $\sigma_{b0}, \sigma_{b1}, \sigma_\epsilon$, tham số $\alpha$, SE, z, p-value, HR kèm 95% CI, và chẩn đoán cơ chế khuyết dữ liệu.
- **Niêm phong kiểm toán:** Tự động ghi nhận `JOINT_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 73. Conformal Prediction & Distribution-Free Risk Intervals Engine

- **Mục đích:** Định lượng bất định và thiết lập khoảng dự báo rủi ro tự do phân phối (Distribution-Free Predictive Inference) với cam kết bao phủ hữu hạn mẫu nghiêm ngặt $P(Y_{n+1} \in \hat{C}(X_{n+1})) \ge 1 - \alpha$ (**Vovk, Gammerman & Shafer, 2005**; **Shafer & Vovk, 2008**; **Lei, G'Sell, Rinaldo, Tibshirani & Wasserman, 2018**; **Angelopoulos & Bates, 2023**; **Romano, Patterson & Candès, 2019**). Khắc phục triệt để điểm yếu chí tử của các mô hình hồi quy OLS và Machine Learning cổ điển: khi dữ liệu khảo sát (CSAT, Likert 1-5, NPS 0-10) phân phối lệch (skewed), đa đỉnh (multimodal), nặng đuôi (heavy-tailed) hoặc có phương sai thay đổi (heteroscedastic), các khoảng tin cậy Gauss $\hat{y} \pm 1.96 \hat{\sigma}$ bị suy giảm độ bao phủ nghiêm trọng (thực tế chỉ đạt 70-85% dù danh nghĩa là 95%), dẫn tới đánh giá sai lầm về rủi ro. Conformal Prediction bảo đảm tính hợp lệ cận biên chính xác trên mẫu hữu hạn mà không đòi hỏi bất kỳ giả định tham số nào về phân phối của dữ liệu.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/conformal-prediction`
- **Payload (`ConformalPredictionAnalysisRequest`):**
  ```json
  {
    "target_question_id": "UUID_câu_hỏi_mục_tiêu_Y",
    "feature_question_ids": ["UUID_đặc_trưng_X1", "UUID_đặc_trưng_X2"],
    "alpha": 0.05,
    "method": "split_conformal" | "locally_weighted",
    "calib_fraction": 0.30,
    "test_fraction": 0.20,
    "clamp_min": 1.0,
    "clamp_max": 5.0,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Phân vùng Mẫu Độc lập (Inductive / Split Conformal Partitioning):**
     Phân chia tập quan sát $N$ thành 3 tập dữ liệu độc lập:
     - Tập Huấn luyện $\mathcal{D}_{\text{train}}$: Dùng để khớp hàm kỳ vọng có điều kiện $\hat{\mu}(x)$ (Ridge OLS hoặc mô hình phi tham số).
     - Tập Hiệu chuẩn $\mathcal{D}_{\text{cal}}$ quy mô $n_{\text{cal}}$: Dùng để tính toán các điểm số không tương đồng (Non-conformity scores).
     - Tập Đánh giá $\mathcal{D}_{\text{test}}$ quy mô $n_{\text{test}}$: Dùng để kiểm chứng độc lập độ bao phủ thực nghiệm out-of-sample và độ rộng khoảng dự báo.
  2. **Hàm Điểm số Không tương đồng (Non-Conformity Scoring Functions):**
     - **Split Conformal Tiêu chuẩn:** $R_i = |y_i - \hat{\mu}(x_i)|$.
     - **Locally-Weighted Conformal (Thích ứng Phương sai Dị biệt):** $R_i = \frac{|y_i - \hat{\mu}(x_i)|}{\hat{\sigma}(x_i) + \epsilon}$, với $\hat{\sigma}(x)$ là mô hình ước lượng quy mô phần dư cục bộ, giúp dải dự báo co giãn linh hoạt theo mật độ bất định của từng vùng đặc trưng.
  3. **Phân vị Hiệu chuẩn với Hiệu chỉnh Hữu hạn Mẫu (Finite-Sample Quantile Calibration):**
     $$\hat{q}_{1-\alpha} = \text{Quantile}\left( \min\left(1.0, \frac{\lceil (n_{\text{cal}} + 1)(1 - \alpha) \rceil}{n_{\text{cal}}}\right), \{R_i\}_{i \in \mathcal{D}_{\text{cal}}} \right)$$
     Bảo đảm định lý Vovk et al. (2005):
     $$1 - \alpha \le P\left(Y_{n+1} \in \hat{C}(X_{n+1})\right) \le 1 - \alpha + \frac{1}{n_{\text{cal}} + 1}$$
  4. **Thiết lập Dải Dự báo Conformal & Ràng buộc Miền Giá trị (Clamping):**
     $$\hat{C}(x) = [\max(y_{\min}, \hat{\mu}(x) - \hat{q}_{1-\alpha} \hat{s}(x)), \; \min(y_{\max}, \hat{\mu}(x) + \hat{q}_{1-\alpha} \hat{s}(x))]$$
  5. **Bảng Chuẩn hóa Đa mức Độ bao phủ (Reliability Calibration Schedule):**
     Đánh giá đồng thời trên lưới $\alpha \in [0.01, 0.40]$, so sánh trực tiếp đường cong độ bao phủ thực nghiệm của Conformal Prediction với mô hình Gaussian cổ điển.
  6. **Trực quan hóa Đồ thị Không gian Vector SVG Kép (Dual-Panel Conformal Diagram):**
     - Panel A: Đồ thị Chuẩn hóa Độ bao phủ (Reliability Diagram) so sánh đường Conformal (xanh lục bám sát đường chéo 45 độ kỳ vọng) với đường Gaussian (đỏ lệch chuẩn).
     - Panel B: Dải băng dự báo Conformal kèm các điểm dữ liệu thực tế ngoài mẫu sắp xếp theo thứ tự kỳ vọng tăng dần, hiển thị trực quan các điểm đạt chuẩn và điểm ngoại lai rủi ro.
  7. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực: phân vùng mẫu $(N_{\text{train}}, N_{\text{cal}}, N_{\text{test}})$, ngưỡng phân vị $\hat{q}_{1-\alpha}$, độ bao phủ thực nghiệm out-of-sample đối chiếu danh nghĩa, so sánh độ rộng khoảng $W_{\text{conf}}$ vs $W_{\text{gauss}}$, và khuyến nghị quản trị rủi ro khảo sát.
- **Niêm phong kiểm toán:** Tự động ghi nhận `CONFORMAL_PREDICTION_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 74. Multilevel Structural Equation Modeling (MSEM 1-1-1 Mediation) Engine

- **Mục đích:** Bóc tách và kiểm định mô hình phương trình cấu trúc đa cấp lồng ghép (Multilevel SEM) cho dữ liệu khảo sát có cấu trúc phân cụm (học sinh trong trường học, nhân viên trong phòng ban/chi nhánh, khách hàng trong cụm địa lý) (**Preacher, Zyphur & Zhang, 2010**; **Muthén, 1994**; **Asparouhov & Muthén, 2008**; **Preacher, Zhang & Zyphur, 2011**; **Zhang, Zyphur & Preacher, 2009**). Khắc phục triệt để nghịch lý sai lệch gộp (Conflation Bias) của mô hình hồi quy tuyến tính phân bậc (HLM) cổ điển: khi biến tiền đề $X$, biến trung gian $M$ và biến kết quả $Y$ đều được thu thập ở cấp độ cá nhân (mô hình 1-1-1), HLM gộp lẫn tác động cá nhân vi mô (Within-cluster) với tác động bối cảnh vĩ mô (Between-cluster), dẫn đến sai lầm loại I nghiêm trọng. MSEM thực hiện phân rã trực giao ma trận hiệp phương sai tổng thể thành hai thành phần độc lập: $\boldsymbol{\Sigma}_{\text{Total}} = \boldsymbol{\Sigma}_{\text{Within}} + \boldsymbol{\Sigma}_{\text{Between}}$, ước lượng các hệ số hồi quy $a, b, c'$ riêng biệt cho từng tầng, kiểm định gián tiếp Monte Carlo đối xứng, và kiểm định chênh lệch $(ab_B - ab_W)$ để bảo đảm kết luận khoa học vững chắc.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/msem`
- **Payload (`MSEMAnalysisRequest`):**
  ```json
  {
    "cluster_question_id": "UUID_câu_hỏi_phân_cụm_ClusterID",
    "x_question_id": "UUID_câu_hỏi_tiền_đề_X",
    "m_question_id": "UUID_câu_hỏi_trung_gian_M",
    "y_question_id": "UUID_câu_hỏi_kết_quả_Y",
    "n_mc_sims": 2000,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Phân rã Ma trận Hiệp phương sai Đa cấp (Orthogonal Variance-Covariance Decomposition):**
     Với mỗi quan sát cá thể $i$ trong cụm $j$:
     $$\mathbf{y}_{ij} = \boldsymbol{\mu} + \boldsymbol{\eta}_{B, j} + \boldsymbol{\eta}_{W, ij}$$
     - $\boldsymbol{\eta}_{W, ij} = \mathbf{y}_{ij} - \bar{\mathbf{y}}_{\cdot j}$: Thành phần lệch tâm cụm đại diện cho biến thiên vi mô nội bộ (Within-cluster).
     - $\boldsymbol{\eta}_{B, j} = \bar{\mathbf{y}}_{\cdot j} - \boldsymbol{\mu}$: Thành phần trung bình cụm đại diện cho biến thiên vĩ mô bối cảnh (Between-cluster).
  2. **Hệ số Tương quan Nội cụm (Intraclass Correlation Coefficient - ICC(1)):**
     $$\text{ICC}(1) = \frac{\sigma_B^2}{\sigma_B^2 + \sigma_W^2}$$
     Lượng hóa tỷ lệ phương sai của $X, M, Y$ bắt nguồn từ sự khác biệt giữa các cụm. Khi $\text{ICC} \ge 0.10$, việc sử dụng MSEM là bắt buộc.
  3. **Phân mô hình Cấp độ 1 (Level 1: Within-Cluster Process):**
     $$M_{W, ij} = a_W X_{W, ij} + e_{M, W, ij}$$
     $$Y_{W, ij} = b_W M_{W, ij} + c'_W X_{W, ij} + e_{Y, W, ij}$$
     - Tác động gián tiếp vi mô: $ab_W = a_W \times b_W$.
     - Tác động tổng thể vi mô: $c_W = ab_W + c'_W$.
  4. **Phân mô hình Cấp độ 2 (Level 2: Between-Cluster Process):**
     $$M_{B, j} = a_B X_{B, j} + e_{M, B, j}$$
     $$Y_{B, j} = b_B M_{B, j} + c'_B X_{B, j} + e_{Y, B, j}$$
     - Tác động gián tiếp vĩ mô bối cảnh: $ab_B = a_B \times b_B$.
  5. **Mô phỏng Phân vị Monte Carlo cho Tác động Gián tiếp (Preacher & Selig, 2012):**
     Tạo $K = 2000$ mẫu phân bố chuẩn đa biến cho $(a^*, b^*)$, tính tích số $a^* b^*$ và trích xuất khoảng tin cậy phân vị bất đối xứng 95% Monte Carlo CI:
     $$\text{CI}_{95\%} = [\text{Percentile}_{2.5\%}(a^* b^*), \; \text{Percentile}_{97.5\%}(a^* b^*)]$$
  6. **Kiểm định Thiên lệch Gộp (Conflation Test; Zhang, Zyphur & Preacher, 2009):**
     $$\Delta_{ab} = ab_B - ab_W$$
     Nếu khoảng tin cậy 95% của $\Delta_{ab}$ không chứa giá trị 0, bác bỏ giả định đồng nhất và khẳng định sự tồn tại của Conflation Bias: cơ chế tâm lý ở cấp cá nhân khác biệt có ý nghĩa so với cơ chế tổ chức ở cấp nhóm.
  7. **Chỉ số Độ phù hợp Mô hình (Model Fit):**
     - Comparative Fit Index (CFI) $\ge 0.95$.
     - Root Mean Square Error of Approximation (RMSEA) $\le 0.06$.
     - Standardized Root Mean Square Residual ($\text{SRMR}_{\text{Within}}$, $\text{SRMR}_{\text{Between}}$) $\le 0.08$.
  8. **Trực quan hóa Đồ thị Không gian Vector SVG Kép (Dual-Panel MSEM):**
     - Panel A: Sơ đồ đường dẫn cấu trúc đa tầng (Multilevel Path Diagram) trực quan hóa đồng thời cấu trúc Level 1 và Level 2 với các hệ số chuẩn hóa $a, b, c'$, dải đo và độ lệch chuẩn.
     - Panel B: Đường cong hàm mật độ phân bố Monte Carlo của tác động gián tiếp Within vs Between kèm vạch tham chiếu vô hiệu 0 và các thanh lỗi 95% CI.
  9. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực khoa học: cỡ mẫu $N$, số cụm $J$, kích thước cụm trung bình, bộ 3 chỉ số ICC, hệ số đường dẫn vi mô $a_W, b_W, c'_W$, vĩ mô $a_B, b_B, c'_B$, khoảng tin cậy Monte Carlo, kết quả kiểm định Conflation Bias, và khuyến nghị chính sách khảo sát.
- **Niêm phong kiểm toán:** Tự động ghi nhận `MSEM_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 75. Targeted Maximum Likelihood Estimation (TMLE) Causal Inference Engine

- **Mục đích:** Ước lượng tác động can thiệp trung bình (Average Treatment Effect - ATE) bán tham số bền vững kép (Doubly Robust) và đạt cận dưới phương sai hiệu quả Cramér-Rao bán tham số cho các chính sách, thử nghiệm hoặc can thiệp khảo sát (**van der Laan & Rubin, 2006**; **van der Laan & Rose, 2011**; **Gruber & van der Laan, 2012**; **Schuler & Rose, 2017**; **Luque-Fernandez et al., 2018**). Khắc phục triệt để hạn chế cốt tử của hai trường phái kinh điển: mô hình hồi quy tham số G-computation (dễ bị chệch nghiêm trọng khi phương trình kỳ vọng kết quả bị xác định sai) và mô hình nghịch đảo xác suất xu hướng IPW (dễ bị bùng nổ phương sai và bất ổn định khi điểm xu hướng gần 0 hoặc 1). TMLE hoạt động như một ước lượng thế chuẩn tắc (Substitution Estimator), sử dụng bước dao động mục tiêu thông qua biến phụ trợ thông minh (Clever Covariate) để trực tiếp triệt tiêu thành phần chệch bậc nhất, giải phương trình hàm ảnh hưởng tối ưu (Efficient Influence Curve - EIC: $\frac{1}{n} \sum D^*(O_i) = 0$).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/tmle`
- **Payload (`TMLEAnalysisRequest`):**
  ```json
  {
    "treatment_question_id": "UUID_câu_hỏi_can_thiệp_nhị_phân_A",
    "outcome_question_id": "UUID_câu_hỏi_kết_quả_Y",
    "covariate_question_ids": ["UUID_nhiễu_W1", "UUID_nhiễu_W2"],
    "gbound": 0.025,
    "target_treatment_val": "1",
    "control_treatment_val": "0",
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Chuẩn hóa Miền Giá trị & Mô hình Khởi tạo (Initial Estimators):**
     - Đưa biến kết quả $Y$ liên tục về đoạn $[0, 1]$ qua phép biến đổi vị tự $Y^* = \frac{Y - y_{\min}}{y_{\max} - y_{\min}}$ để bảo đảm tính ổn định của hàm liên kết logit.
     - Khớp mô hình điểm xu hướng can thiệp $g(W) = P(A=1 \mid W)$ bằng hồi quy Logistic chính quy hóa. Áp dụng ngưỡng cắt xén biên $g \in [\text{gbound}, 1 - \text{gbound}]$ để thỏa mãn giả định tích cực (Positivity / Common Support).
     - Khớp mô hình kỳ vọng kết quả khởi tạo $\bar{Q}^0(A, W) = \mathbb{E}[Y \mid A, W]$. Trích xuất dự báo tiềm năng ban đầu $\bar{Q}^0(1, W_i)$ và $\bar{Q}^0(0, W_i)$.
  2. **Thiết lập Biến Phụ trợ Thông minh (Clever Covariate Construction):**
     $$H^*(A_i, W_i) = \frac{A_i}{g(W_i)} - \frac{1 - A_i}{1 - g(W_i)}$$
     $$H^*(1, W_i) = \frac{1}{g(W_i)}, \quad H^*(0, W_i) = -\frac{1}{1 - g(W_i)}$$
  3. **Bước Dao động Tối ưu Hóa Mục tiêu (Targeting Step via MLE Offset):**
     Thiết lập phân mô hình tham số đơn biến với độ dịch $\text{logit}(\bar{Q}^0)$:
     $$\text{logit}\left( \bar{Q}^*_\epsilon(A, W) \right) = \text{logit}\left( \bar{Q}^0(A, W) \right) + \epsilon H^*(A, W)$$
     Ước lượng tham số dao động $\hat{\epsilon}$ bằng phương pháp hợp lý cực đại (MLE) tối thiểu hóa mất mát entropy chéo:
     $$\hat{\epsilon} = \arg\min_\epsilon - \frac{1}{n} \sum_{i=1}^n \left( Y_i \log \bar{Q}^*_\epsilon(A_i, W_i) + (1 - Y_i) \log(1 - \bar{Q}^*_\epsilon(A_i, W_i)) \right)$$
  4. **Cập nhật Dự báo Phản thực tế & Điểm Ước lượng TMLE ATE:**
     $$\bar{Q}^*(1, W_i) = \text{expit}\left( \text{logit}(\bar{Q}^0(1, W_i)) + \hat{\epsilon} H^*(1, W_i) \right)$$
     $$\bar{Q}^*(0, W_i) = \text{expit}\left( \text{logit}(\bar{Q}^0(0, W_i)) + \hat{\epsilon} H^*(0, W_i) \right)$$
     $$\hat{\psi}_{\text{TMLE}} = (y_{\max} - y_{\min}) \times \frac{1}{n} \sum_{i=1}^n \left( \bar{Q}^*(1, W_i) - \bar{Q}^*(0, W_i) \right)$$
  5. **Suy diễn Thống kê Dựa trên Hàm Ảnh hưởng Tối ưu (Efficient Influence Curve Inference):**
     Hàm ảnh hưởng tối ưu tiệm cận cho từng quan sát:
     $$D^*(O_i) = H^*(A_i, W_i) \left( Y_i - \bar{Q}^*(A_i, W_i) \right) + \bar{Q}^*(1, W_i) - \bar{Q}^*(0, W_i) - \hat{\psi}_{\text{TMLE}}$$
     Phương sai tiệm cận và sai số chuẩn:
     $$\hat{\sigma}^2_{\text{TMLE}} = \frac{1}{n} \sum_{i=1}^n \left( D^*(O_i) \right)^2, \quad \operatorname{SE}(\hat{\psi}_{\text{TMLE}}) = \frac{\hat{\sigma}_{\text{TMLE}}}{\sqrt{n}}$$
     Khoảng tin cậy 95% Wald CI: $\hat{\psi}_{\text{TMLE}} \pm 1.96 \cdot \operatorname{SE}(\hat{\psi}_{\text{TMLE}})$.
  6. **Bảng Đối chiếu Đa Ước lượng Nhân quả:**
     So sánh trực diện: Hiệu số thô không hiệu chỉnh (Unadjusted Difference in Means), hồi quy tham số G-Computation, mô hình IPW Hajek chuẩn hóa, và mô hình bán tham số mục tiêu TMLE.
  7. **Trực quan hóa Đồ thị Không gian Vector SVG Kép (Dual-Panel TMLE):**
     - Panel A: Đồ thị Gương Mật độ Điểm Xu hướng (Mirror Overlap Histogram) đánh giá giả định Positivity giữa nhóm Can thiệp $A=1$ và nhóm Đối chứng $A=0$.
     - Panel B: Biểu đồ Rừng Đối chiếu (Forest Plot) minh họa sự hội tụ và biên độ sai số của 4 phương pháp ước lượng kèm vạch tham chiếu vô hiệu 0.
  8. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực khoa học: cỡ mẫu $N$, số lượng can thiệp/đối chứng, phạm vi điểm xu hướng, tham số $\epsilon$, điểm ATE TMLE, sai số chuẩn EIC, thống kê $z$, giá trị $p$, khoảng tin cậy 95% CI, và đánh giá tác động chính sách can thiệp.
- **Niêm phong kiểm toán:** Tự động ghi nhận `TMLE_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 76. Synthetic Difference-in-Differences (SDID) Panel Econometrics Engine

- **Mục đích:** Ước lượng tác động can thiệp trung bình trên nhóm can thiệp (Average Treatment Effect on the Treated - ATT) cho dữ liệu bảng/chuỗi thời gian theo dõi khảo sát (Panel Data) (**Arkhangelsky, Athey, Hirshberg, Imbens, & Wager, AER 2021**; **Abadie, 2021**; **Callaway & Sant'Anna, 2021**; **Clarke et al., 2023**). Khắc phục đồng thời hai điểm yếu cơ bản của phương pháp Khác biệt kép (DiD) và Đối chứng Tổng hợp (SCM):
  1. DiD cổ điển đòi hỏi **Giả định Xu hướng Song song (Parallel Trends Assumption)** khắt khe; khi nhóm can thiệp có thành phần khác biệt với nhóm đối chứng, xu hướng trước can thiệp không song song và DiD bị chệch nghiêm trọng.
  2. SCM cổ điển (Abadie et al., 2010) cố gắng khớp điểm giá trị tuyệt đối trước can thiệp nhưng không cho phép độ dịch hằng số chặn (intercept shift), dẫn đến việc không thể tìm được nghiệm tổng hợp lồi khi nhóm can thiệp có mức độ cơ bản cao hơn toàn bộ nhóm đối chứng.
  SDID tổng hòa xuất sắc hai phương pháp: áp dụng **trọng số đơn vị $\hat{\omega}_i$** để làm cho quỹ đạo của đối chứng tổng hợp song song hoàn hảo với nhóm can thiệp (cho phép độ dịch chặn), đồng thời áp dụng **trọng số thời gian $\hat{\lambda}_t$** để cân bằng mức độ thời gian trước và sau can thiệp, triệt tiêu hoàn toàn thiên lệch biến động theo thời gian.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/sdid`
- **Payload (`SDIDAnalysisRequest`):**
  ```json
  {
    "unit_question_id": "UUID_câu_hỏi_đơn_vị_UnitID",
    "time_question_id": "UUID_câu_hỏi_mốc_thời_gian_TimeWave",
    "outcome_question_id": "UUID_câu_hỏi_biến_kết_quả_Y",
    "treated_units": ["Region_1", "Region_2"],
    "treatment_start_time": 3,
    "n_placebo_reps": 200,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Tối ưu hóa Trọng số Đơn vị Đối chứng $\boldsymbol{\omega}$ (Unit Weights with Regularization; Arkhangelsky et al., 2021):**
     $$\min_{\omega_0, \boldsymbol{\omega}} \sum_{t=1}^{T_{\text{pre}}} \left( \omega_0 + \sum_{i \in \text{control}} \omega_i Y_{it} - \frac{1}{N_{\text{tr}}} \sum_{i \in \text{treated}} Y_{it} \right)^2 + \zeta^2 T_{\text{pre}} \|\boldsymbol{\omega}\|_2^2$$
     với ràng buộc $\omega_i \ge 0, \sum \omega_i = 1$, và tham số phạt $\zeta^2$ được định chuẩn theo phương sai sai phân bậc 1 của nhóm đối chứng.
  2. **Tối ưu hóa Trọng số Thời gian Tiền Can thiệp $\boldsymbol{\lambda}$ (Time Weights):**
     $$\min_{\lambda_0, \boldsymbol{\lambda}} \sum_{i \in \text{control}} \left( \lambda_0 + \sum_{t=1}^{T_{\text{pre}}} \lambda_t Y_{it} - \frac{1}{T_{\text{post}}} \sum_{t \in \text{post}} Y_{it} \right)^2$$
     với ràng buộc $\lambda_t \ge 0, \sum \lambda_t = 1$. Trọng số thời gian gán mức ưu tiên cao hơn cho các kỳ tiền can thiệp có tính chất vĩ mô tương đồng nhất với kỳ hậu can thiệp.
  3. **Ước lượng Tác động Can thiệp SDID Trọng số Kép (Double-Weighted Estimator):**
     $$\hat{\tau}^{\text{sdid}} = \left( \bar{Y}_{\text{tr}, \text{post}} - \sum_{i \in \text{co}} \hat{\omega}_i \bar{Y}_{i, \text{post}} \right) - \left( \sum_{t \in \text{pre}} \hat{\lambda}_t \bar{Y}_{\text{tr}, t} - \sum_{i \in \text{co}} \hat{\omega}_i \sum_{t \in \text{pre}} \hat{\lambda}_t Y_{it} \right)$$
  4. **Suy diễn Thống kê Giả dược / Hoán vị Đơn vị Đối chứng (Placebo In-Space Permutation Inference):**
     Tiến hành hoán vị gán tuần tự từng đơn vị đối chứng làm đơn vị giả can thiệp, tính toán phân phối tác động giả dược $\hat{\tau}^{\text{placebo}}$ để ước lượng sai số chuẩn $SE(\hat{\tau}^{\text{sdid}})$ và giá trị $p$-value hai phía chính xác.
  5. **Bảng Đối chiếu Đa Mô hình:**
     So sánh trực diện: Ước lượng DiD cổ điển không trọng số $\hat{\tau}^{\text{did}}$, mô hình Đối chứng Tổng hợp chuẩn $\hat{\tau}^{\text{scm}}$, và mô hình SDID trọng số kép $\hat{\tau}^{\text{sdid}}$.
  6. **Trực quan hóa Đồ thị Không gian Vector SVG Kép (Dual-Panel SDID):**
     - Panel A: Đồ thị Quỹ đạo Động (Trajectory Curves) biểu diễn diễn biến qua thời gian của Nhóm Can thiệp thực tế, Nhóm Đối chứng Tổng hợp thô, và Đường Đối chứng Tổng hợp Hiệu chỉnh Song song (Parallel Synthetic Trend) kèm vạch phân cách thời điểm can thiệp và khoảng cách hiệu ứng nhân quả $\hat{\tau}$.
     - Panel B: Biểu đồ Thanh kẹo mút (Lollipop Chart) thể hiện phân bổ trọng số đóng góp của các đơn vị đối chứng tiêu biểu $(\hat{\omega}_i)$ và thanh so sánh 3 mô hình DiD - SCM - SDID.
  7. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực khoa học: số đơn vị can thiệp và đối chứng, số mốc tiền và hậu can thiệp, điểm ước lượng $\hat{\tau}^{\text{sdid}}$, sai số chuẩn $SE$, giá trị $p$, khoảng tin cậy 95% CI, danh sách các đơn vị đối chứng đóng góp trọng số lớn nhất, và hàm ý chính sách kinh tế lượng.
- **Niêm phong kiểm toán:** Tự động ghi nhận `SDID_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 77. Generalized Causal Forest (GRF) Non-Parametric Heterogeneity Engine

- **Mục đích:** Ước lượng tác động can thiệp không đồng nhất ở cấp độ từng cá thể người phản hồi (Conditional Average Treatment Effect - CATE $\hat{\tau}(X_i) = \mathbb{E}[Y_i(1) - Y_i(0) \mid X_i]$) và xác định các đặc trưng nhân khẩu/tâm lý đóng vai trò điều tiết then chốt dựa trên lý thuyết Rừng Cây Nhân Quả Suy Rộng (Generalized Random Forests - GRF) (**Athey, Tibshirani & Wager, Ann. Statist. 2019**; **Wager & Athey, JASA 2018**; **Chernozhukov et al., 2018**; **Athey & Imbens, PNAS 2016**).
  1. Khắc phục hạn chế của các mô hình tương tác tuyến tính cổ điển (Linear OLS Interactions): Trong OLS, nhà nghiên cứu phải giả định trước dạng hàm tương tác bậc 1 hoặc bậc 2 ($X_1 \times T$). Khi không gian đặc trưng khảo sát lớn ($p > 10$), việc dò tìm thủ công dẫn đến khai thác dữ liệu quá mức (p-hacking) và bỏ sót các hiệu ứng phi tuyến tính phức tạp.
  2. Áp dụng kỹ thuật **Cây Nhân Quả Trung Thực (Honest Causal Trees)**: Mẫu ngẫu nhiên được chia đôi độc lập: tập phân nhánh $J_{\text{tr}}$ chỉ dùng để xác định các nhát cắt tối ưu hóa phương sai hiệu ứng can thiệp, trong khi tập ước lượng $J_{\text{est}}$ được dùng độc lập để gán giá trị trung bình $\bar{Y}_1 - \bar{Y}_0$ tại từng lá cây. Cơ chế phân ly này triệt tiêu hoàn toàn hiện tượng thiên lệch tối ưu hóa quá mức (overfitting bias) và bảo đảm phân phối tiệm cận Gaussian chuẩn tắc cho từng dự báo $\hat{\tau}(X_i)$.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/causal-forest`
- **Payload (`CausalForestAnalysisRequest`):**
  ```json
  {
    "treatment_question_id": "UUID_câu_hỏi_can_thiệp_W",
    "outcome_question_id": "UUID_câu_hỏi_kết_quả_Y",
    "feature_question_ids": ["UUID_đặc_trưng_1", "UUID_đặc_trưng_2", "UUID_đặc_trưng_3"],
    "n_trees": 40,
    "min_leaf_size": 5,
    "target_treatment_val": 1,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Thuật toán Phân nhánh Cây Nhân quả Tối ưu (Causal Tree Splitting Criterion):**
     Với mỗi nút $P$, tiêu chuẩn phân nhánh tìm kiếm điểm cắt $(j^*, c^*)$ tối đa hóa phương sai của hiệu ứng can thiệp dự kiến giữa hai lá con $L$ và $R$:
     $$\Delta(L, R) = \frac{N_L N_R}{N_P} \left( \hat{\tau}_L - \hat{\tau}_R \right)^2, \quad \hat{\tau}_k = \bar{Y}_{1, k} - \bar{Y}_{0, k}$$
     đồng thời kiểm soát điều kiện kích thước lá tối thiểu $N_{\text{leaf}} \ge \text{min\_leaf\_size}$ và có đủ cả quan sát can thiệp lẫn đối chứng trong mỗi lá.
  2. **Ước lượng Trung thực Không Thiên lệch (Honest Estimation & Ensemble Averaging):**
     Hợp nhất dự báo trên $B$ cây ngẫu nhiên được tái lấy mẫu có hoàn lại (subsampling bootstrap):
     $$\hat{\tau}(x) = \frac{1}{B} \sum_{b=1}^B \hat{\tau}_b(x)$$
     Tác động can thiệp trung bình dân số (ATE): $\hat{\tau}_{\text{ATE}} = \frac{1}{n} \sum_{i=1}^n \hat{\tau}(X_i)$.
  3. **Độ Quan trọng của Biến Số (Variable Importance Ranking):**
     Định lượng mức độ đóng góp của từng biến hiệp biến $X_j$ vào việc tạo ra tính không đồng nhất của tác động can thiệp:
     $$\text{VI}(X_j) = \sum_{b=1}^B \sum_{k \in \text{Splits}_b} \mathbb{I}(\text{SplitVar}(k) = j) \cdot 2^{-\text{depth}(k)}$$
     Chuẩn hóa về tỷ lệ phần trăm tương đối $\text{RelVI}_j = \frac{\text{VI}_j}{\sum_m \text{VI}_m} \times 100\%$.
  4. **Kiểm định Thống kê Tính Không Đồng Nhất (Omnibus Test for Heterogeneity):**
     Ước lượng phương sai của hiệu ứng cá thể $\widehat{\text{Var}}(\tau(X)) = \frac{1}{n-1} \sum_{i=1}^n (\hat{\tau}(X_i) - \hat{\tau}_{\text{ATE}})^2$.
     Tính toán tỷ số phương sai và giá trị $p$-value tiệm cận phân phối $\chi^2$ để kết luận xem tác động chính sách có thực sự khác biệt có ý nghĩa thống kê giữa các phân khúc dân số hay thuần túy là đồng nhất.
  5. **Bảng Phân bổ Tần suất CATE Bins:**
     Chia phân phối CATE thành các khoảng đều nhau, thống kê số lượng quan sát và tỷ lệ % cá thể phản hồi có tác động dương ($\hat{\tau} > 0$) so với tác động âm ($\hat{\tau} < 0$).
  6. **Trực quan hóa Đồ thị Không gian Vector SVG Kép (Dual-Panel Causal Forest):**
     - Panel A: Biểu đồ Histogram phân phối tần suất của hiệu ứng can thiệp cá thể $\hat{\tau}(X_i)$ với vạch trung bình ATE và dải phân cách tác động dương/âm.
     - Panel B: Biểu đồ Thanh ngang Tầm quan trọng của Hiệp biến (Variable Importance Bar Chart) thể hiện xếp hạng các yếu tố nhân khẩu/tâm lý phân hóa tác động mạnh mẽ nhất.
  7. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực khoa học: số cây ensemble $B$, cỡ mẫu $N$, số lượng quan sát nhóm can thiệp và đối chứng, hiệu ứng trung bình $\hat{\tau}_{\text{ATE}}$, sai số chuẩn $SE$, khoảng tin cậy 95% CI, kết quả kiểm định tính không đồng nhất Omnibus $p$-value, tỷ lệ phần trăm cá thể nhận được tác động dương, và danh sách các đặc trưng điều tiết quan trọng nhất.
- **Niêm phong kiểm toán:** Tự động ghi nhận `CAUSAL_FOREST_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 78. Causal Mediation Analysis with Sensitivity Analysis for Unmeasured Confounding Engine

- **Mục đích:** Phân rã tác động nhân quả toàn phần (Total Effect $\tau$) thành Hiệu ứng Can thiệp Trung gian Trung bình (Average Causal Mediation Effect - ACME $\delta$) và Hiệu ứng Can thiệp Trực tiếp Trung bình (Average Direct Effect - ADE $\zeta$), đồng thời tiến hành kiểm định độ nhạy chính xác đối với sự vi phạm Giả định Tuần tự Bỏ qua (Sequential Ignorability Assumption) do các biến nhiễu không quan sát (Unmeasured Omitted Confounders) (**Imai, Keele, & Tingley, Psychol. Methods 2010**; **Imai, Keele, & Yamamoto, Statist. Sci. 2010**; **Tingley et al., JSS 2014**; **VanderWeele, 2015**).
  1. Khắc phục hạn chế sinh tử của các mô hình trung gian cổ điển Baron & Kenny (1986) và Preacher & Hayes (2008): Các phương pháp truyền thống mặc định giả định không có biến nhiễu tiềm ẩn đồng thời tác động lên biến trung gian $M$ và biến kết quả $Y$ ($e_M \perp e_Y$). Khi có một yếu tố thứ ba chưa thu thập (ví dụ: động lực nội tại, năng lực tiềm ẩn, yếu tố môi trường), sai số của hai phương trình sẽ tương quan với nhau: $\rho = \text{Corr}(e_M, e_Y) \ne 0$, khiến ước lượng ACME bị thiên lệch nghiêm trọng và có thể đảo ngược dấu.
  2. Áp dụng Khung Phân tích Độ nhạy Bán tham số Imai et al. (2010): Thiết lập tham số độ nhạy $\rho \in (-1, 1)$ đại diện cho mức độ tương quan sai số sinh ra bởi biến nhiễu tiềm ẩn; tính toán nghiệm giải tích chính xác của ngưỡng triệt tiêu $\tilde{\rho}$ tại đó hiệu ứng trung gian bị suy giảm hoàn toàn về 0 ($\delta(\tilde{\rho}) = 0$), định lượng tỷ lệ phương sai giải thích tối thiểu $R^{*2}_M R^{*2}_Y = \tilde{\rho}^2$ mà biến nhiễu phải chiếm giữ để phá vỡ kết luận nghiên cứu.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/causal-mediation-sensitivity`
- **Payload (`CausalMediationSensitivityRequest`):**
  ```json
  {
    "treatment_question_id": "UUID_câu_hỏi_can_thiệp_T",
    "mediator_question_id": "UUID_câu_hỏi_trung_gian_M",
    "outcome_question_id": "UUID_câu_hỏi_kết_quả_Y",
    "covariate_question_ids": ["UUID_hiệp_biến_1", "UUID_hiệp_biến_2"],
    "target_treatment_val": 1,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Hệ Phương trình Cấu trúc Tuyến tính (Structural Linear Equations):**
     $$M_i = \alpha_0 + \alpha_T T_i + \mathbf{X}_i' \boldsymbol{\alpha}_X + e_{Mi}, \quad e_{Mi} \sim \mathcal{N}(0, \sigma_M^2)$$
     $$Y_i = \beta_0 + \beta_T T_i + \beta_M M_i + \mathbf{X}_i' \boldsymbol{\beta}_X + e_{Yi}, \quad e_{Yi} \sim \mathcal{N}(0, \sigma_Y^2)$$
     với hiệp phương sai sai số $\text{Cov}(e_M, e_Y) = \rho \sigma_M \sigma_Y$.
  2. **Ước lượng Cơ sở Dưới Giả định Tuần tự Bỏ qua (Baseline $\rho = 0$):**
     - ACME: $\hat{\delta} = \hat{\alpha}_T \hat{\beta}_M$.
     - ADE: $\hat{\zeta} = \hat{\beta}_T$.
     - Total Effect: $\hat{\tau} = \hat{\delta} + \hat{\zeta}$.
     - Sai số chuẩn vững và khoảng tin cậy 95% CI theo phương pháp Sobel Delta Method:
       $$\operatorname{SE}(\hat{\delta}) = \sqrt{\hat{\alpha}_T^2 \operatorname{SE}(\hat{\beta}_M)^2 + \hat{\beta}_M^2 \operatorname{SE}(\hat{\alpha}_T)^2}$$
     - Tỷ lệ trung gian hòa: $\hat{\nu} = \hat{\delta} / \hat{\tau}$.
  3. **Hàm Độ nhạy Giải tích ACME $\delta(\rho)$ (Analytical Sensitivity Function):**
     Với bất kỳ giá trị tương quan nhiễu tiềm ẩn $\rho \in (-0.95, 0.95)$:
     $$\delta(\rho) = \hat{\alpha}_T \left( \hat{\beta}_M - \rho \frac{\sigma_Y}{\sigma_M \sqrt{1 - \rho^2}} \right)$$
     Tính toán sai số chuẩn và khoảng tin cậy tiệm cận $95\%$ CI dọc theo lưới $\rho \in [-0.8, +0.8]$.
  4. **Nghiệm Giải tích Đóng của Ngưỡng Triệt tiêu $\tilde{\rho}$ (Closed-Form Threshold):**
     $$\tilde{\rho} = \frac{\hat{\beta}_M \sigma_M}{\sqrt{\sigma_Y^2 + \hat{\beta}_M^2 \sigma_M^2}}$$
     - Nếu $|\tilde{\rho}| \ge 0.35$: Phân loại `HIGHLY_ROBUST` (Vững chắc cao trước nhiễu tiềm ẩn).
     - Nếu $0.15 \le |\tilde{\rho}| < 0.35$: Phân loại `MODERATELY_ROBUST` (Vững chắc trung bình).
     - Nếu $|\tilde{\rho}| < 0.15$: Phân loại `FRAGILE_TO_CONFOUNDING` (Nhạy cảm cao với nhiễu tiềm ẩn, dễ bị tổn thương).
  5. **Tích Hệ số Xác định Bán phần (Coefficient of Determination Product):**
     $$R^{*2}_M R^{*2}_Y = \tilde{\rho}^2$$
     Đo lường tích tỷ lệ phương sai dư thừa của $M$ và $Y$ mà một biến nhiễu chưa quan sát phải đồng thời giải thích được để đưa hiệu ứng trung gian về 0.
  6. **Trực quan hóa Đồ thị Không gian Vector SVG Kép (Dual-Panel Causal Mediation):**
     - Panel A: Sơ đồ Đường Nhân Quả (Causal Path Diagram) thể hiện các nhánh $a (T \to M)$, $b (M \to Y)$, $c' (T \to Y)$, kèm cung cong đứt nét màu đỏ minh họa tương quan sai số $\rho = \text{Corr}(e_M, e_Y)$.
     - Panel B: Đồ thị Đường cong Độ nhạy ACME $\delta(\rho)$ với dải ruy băng mờ biểu diễn khoảng tin cậy 95% CI, đường tham chiếu vô hiệu $\delta = 0$, điểm gốc $\rho = 0$, và vạch đánh dấu ngưỡng triệt tiêu $\tilde{\rho}$.
  7. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực khoa học theo Imai et al. (2010): số quan sát nhóm can thiệp và đối chứng, hệ số và sai số chuẩn các nhánh $a, b, c'$, giá trị hiệu ứng trung gian ACME $\delta$ và trực tiếp ADE $\zeta$, tỷ lệ hòa giải $\nu$, ngưỡng tương quan sai số triệt tiêu $\tilde{\rho}$, tích $R^{*2}$, và phân hạng mức độ vững chắc phương pháp luận.
- **Niêm phong kiểm toán:** Tự động ghi nhận `CAUSAL_MEDIATION_SENSITIVITY_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 79. Dynamic Time Warping (DTW) Longitudinal Trajectory Clustering Engine

- **Mục đích:** Khám phá và phân tách các phân khúc đối tượng người tham gia khảo sát theo hình thái biến thiên quỹ đạo thời gian dọc (Multi-Wave Longitudinal Panel Data) bằng thuật toán Đồng chỉnh Thời gian Động (Dynamic Time Warping - DTW) kết hợp K-Medoids / PAM (**Sakoe & Chiba, IEEE Trans. ASSP 1978**; **Keogh & Ratanamahatana, KAIS 2005**; **Petitjean, Ketterlin, & Gançarski, Pattern Recognit. 2011**; **Aghabozorgi, Shirkhorshidi, & Wah, Inf. Syst. 2015**).
  1. Khắc phục sự thất bại của khoảng cách Euclidean trong phân cụm chuỗi thời gian: Khoảng cách Euclidean thông thường ($d_E = \sqrt{\sum (x_t - y_t)^2}$) so sánh cứng nhắc các điểm cùng mốc thời gian $t$. Khi hai nhóm người phản hồi có cùng mẫu hình hành vi (ví dụ: bùng nổ quan tâm rồi bão hòa) nhưng một nhóm phản ứng trễ hơn nhóm kia 1-2 đợt sóng (phase shift / time lag), khoảng cách Euclidean sẽ coi hai quỹ đạo này hoàn toàn xa lạ và phân loại nhầm thành hai cụm khác nhau.
  2. Áp dụng Thuật toán DTW với Ràng buộc Dải Sakoe-Chiba: Cho phép co giãn phi tuyến tính trục thời gian để tìm kiếm đường đi uốn lượn tối ưu (optimal warping path) căn chỉnh các đặc tính hình học tương đồng nhất giữa hai chuỗi phản hồi dọc, đồng thời kiểm soát độ lệch tối đa bằng bán kính cửa sổ dải Sakoe-Chiba $r$ để triệt tiêu các biến dạng phi thực tế.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/dtw-clustering`
- **Payload (`DTWClusteringRequest`):**
  ```json
  {
    "time_series_question_ids": ["UUID_đợt_1", "UUID_đợt_2", "UUID_đợt_3", "UUID_đợt_4"],
    "time_labels": ["Quý 1", "Quý 2", "Quý 3", "Quý 4"],
    "n_clusters": 3,
    "window_radius": 1,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Quy hoạch Động Ma trận Chi phí Tích lũy DTW (Cumulative Cost Matrix Recurrence):**
     Với hai chuỗi thời gian cá nhân $\mathbf{X} = (x_1, \dots, x_T)$ và $\mathbf{Y} = (y_1, \dots, y_T)$:
     $$C(i, j) = (x_i - y_j)^2 + \min\left( C(i-1, j), C(i, j-1), C(i-1, j-1) \right)$$
     với điều kiện biên $C(0, 0) = 0, C(i, 0) = C(0, j) = \infty$, và ràng buộc dải Sakoe-Chiba $|i - j| \le r$.
     Khoảng cách DTW chính xác: $D_{\text{DTW}}(\mathbf{X}, \mathbf{Y}) = \sqrt{C(T, T)}$.
  2. **Thuật toán Phân cụm K-Medoids / PAM trên Không gian DTW:**
     Khởi tạo các điểm trung tâm medoids theo xác suất bình phương khoảng cách (k-means++ distance-weighted probability); lặp tối ưu hóa phân cụm bằng cách gán từng quan sát về medoid gần nhất theo khoảng cách DTW và cập nhật lại medoid là phần tử có tổng khoảng cách nội cụm cực tiểu.
  3. **Ước lượng Quỹ đạo Trung tâm Trung bình (Barycenter Averaging - DBA; Petitjean et al. 2011):**
     Tính toán chuỗi vector tọa độ trung bình đại diện cho trung tâm hình thái của từng cụm qua các mốc thời gian $T_1, \dots, T_m$.
  4. **Phân loại Hình thái Quỹ đạo Chuẩn mực (Trajectory Archetype Classification):**
     Tự động định danh bản chất động lực của từng cụm dựa trên hệ số độ dốc và biên độ cực trị:
     - *Tăng trưởng liên tục (Progressive Growth / Upward Surge)*
     - *Suy giảm lũy tiến (Progressive Decline / Wear-Off)*
     - *Đỉnh sớm rồi thoái trào (Early Peak & Fade / Transient Surge)*
     - *Chạm đáy rồi phục hồi (V-Shaped Dip & Recovery)*
     - *Ổn định đi ngang (Stable Baseline / Plateau)*
  5. **Đánh giá Chất lượng Phân cụm Silhouette Coefficient DTW:**
     Tính toán hệ số Silhouette cá nhân $s_i = \frac{b_i - a_i}{\max(a_i, b_i)}$ dựa trên khoảng cách phi tuyến DTW để đánh giá độ tách biệt giữa các cụm (ngưỡng đạt yêu cầu: $S \ge 0.35$).
  6. **Trực quan hóa Đồ thị Không gian Vector SVG Kép (Dual-Panel DTW Trajectory):**
     - Panel A: Đồ thị Spaghetti biểu diễn toàn bộ các quỹ đạo cá nhân được phân màu theo cụm dưới dạng các đường mảnh trong suốt, làm nổi bật đường trung tâm Barycenter đậm nét kèm các điểm nút đánh dấu giá trị trung bình từng mốc.
     - Panel B: Thẻ phân bổ tỷ lệ phần trăm cơ cấu từng cụm, số lượng quan sát $n$, độ phân tán nội cụm DTW, và phân loại hình thái quỹ đạo.
  7. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực khoa học theo Sakoe & Chiba (1978) và Petitjean et al. (2011): cỡ mẫu $N$, số đợt sóng $T$, số cụm $k$, hệ số Silhouette $S$, cơ cấu tỷ lệ và đặc tính động lực của từng hình thái quỹ đạo, và hàm ý nghiên cứu hành vi người tiêu dùng/nhân khẩu học.
- **Niêm phong kiểm toán:** Tự động ghi nhận `DTW_TRAJECTORY_CLUSTERING_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 80. Causal Interaction Trees & Honest Subgroup Identification Engine

- **Mục đích:** Tự động khám phá các phân khúc đối tượng phản hồi đặc thù (Treatment Effect Subgroup Discovery) và nhận diện các nhóm hưởng lợi vượt trội (Extreme Positive Responders) hoặc bị phản tác dụng (Adverse Backfire Responders) bằng Cây Tương Tác Nhân Quả Phân Chia Mẫu Trung Thực (**Athey & Imbens, PNAS 2016**; **Su et al., JMLR 2009**; **Wager & Athey, JASA 2018**; **Lipkovich et al., Stat. Med. 2017**).
  1. Khắc phục điểm yếu chí tử của mô hình hồi quy tương tác tuyến tính cổ điển ($T \times X$): Các phương pháp truyền thống yêu cầu nhà nghiên cứu tự lựa chọn điểm cắt phân nhóm (dichotomization) một cách chủ quan, dễ dẫn đến hiện tượng khai thác dữ liệu quá mức (data snooping / p-hacking), không thể tự động phát hiện các quy tắc phân nhánh đa chiều phi tuyến tính (ví dụ: `Độ tuổi ≤ 35 VÀ Thu nhập > 20 triệu VÀ Niềm tin số cao`).
  2. Áp dụng Thuật toán Phân nhánh Cây Nhân Quả Trung Thực (Honest Sample Splitting): Chia ngẫu nhiên mẫu thành hai tập độc lập:
     - Tập cấu trúc $J_{\text{tr}}$: Chỉ dùng để tìm kiếm các nhát cắt $(j^*, c^*)$ tối đa hóa phương sai hiệu ứng can thiệp giữa hai lá con $\Delta(L, R)$.
     - Tập ước lượng $J_{\text{est}}$: Được dùng độc lập hoàn toàn để gán giá trị trung bình $\hat{\tau}_k = \bar{Y}_{1, k} - \bar{Y}_{0, k}$, sai số chuẩn vững và khoảng tin cậy 95% CI cho từng lá. Cơ chế này loại bỏ hoàn toàn thiên lệch lạc quan (overoptimism bias) và đảm bảo các kiểm định giả thuyết tiệm cận Gaussian chuẩn tắc.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/causal-tree`
- **Payload (`CausalTreeSubgroupRequest`):**
  ```json
  {
    "treatment_question_id": "UUID_câu_hỏi_can_thiệp_T",
    "outcome_question_id": "UUID_câu_hỏi_kết_quả_Y",
    "feature_question_ids": ["UUID_đặc_trưng_1", "UUID_đặc_trưng_2", "UUID_đặc_trưng_3"],
    "max_depth": 3,
    "min_leaf_size": 5,
    "target_treatment_val": 1,
    "scope": "all" | "verified_clean"
  }
  ```
- **Cơ chế tính toán & Quy chuẩn phương pháp luận:**
  1. **Tiêu chuẩn Tối ưu Phân nhánh Cây Tương tác (Heterogeneity Splitting Criterion):**
     Với mỗi nút cha $P$, thuật toán duyệt qua toàn bộ các biến đặc trưng $X_j$ và các ngưỡng cắt phân vị $c$ để tối đa hóa phương sai phân hóa hiệu ứng can thiệp:
     $$\Delta(L, R) = \frac{N_L N_R}{N_P} \left( \hat{\tau}_L - \hat{\tau}_R \right)^2$$
     với ràng buộc kích thước lá tối thiểu $N_{\text{leaf}} \ge \text{min\_leaf\_size}$ cho cả nhóm can thiệp và đối chứng trong mỗi nhánh.
  2. **Ước lượng Trung thực Phân khúc (Honest Subgroup Effect Estimation):**
     Tại mỗi lá kết thúc $k$ trên tập $J_{\text{est}}$:
     $$\hat{\tau}_k = \frac{1}{N_{1, k}} \sum_{i \in k, T_i=1} Y_i - \frac{1}{N_{0, k}} \sum_{i \in k, T_i=0} Y_i$$
     $$\operatorname{SE}(\hat{\tau}_k) = \sqrt{\frac{s_{1, k}^2}{N_{1, k}} + \frac{s_{0, k}^2}{N_{0, k}}}, \quad z_k = \frac{\hat{\tau}_k}{\operatorname{SE}(\hat{\tau}_k)}, \quad p_k = 2(1 - \Phi(|z_k|))$$
  3. **Hệ Thống Phân Loại Phân Khúc Đối Tượng Tự Động (Subgroup Taxonomy):**
     - `STRONG_POSITIVE_RESPONDERS`: $\hat{\tau}_k > 0, p_k < 0.05$ (Nhóm hưởng lợi vượt trội có ý nghĩa thống kê cao).
     - `ADVERSE_BACKFIRE_RESPONDERS`: $\hat{\tau}_k < 0, p_k < 0.05$ (Nhóm bị phản tác dụng / tác động tiêu cực nguy hiểm cần cảnh báo).
     - `MODERATE_POSITIVE`: $\hat{\tau}_k > 0, p_k \ge 0.05$ (Nhóm có xu hướng tích cực nhẹ).
     - `MODERATE_NEGATIVE`: $\hat{\tau}_k < 0, p_k \ge 0.05$ (Nhóm có xu hướng suy giảm nhẹ).
     - `NEUTRAL_NO_EFFECT`: $\hat{\tau}_k \approx 0$ (Nhóm trung tính không đổi).
  4. **Trực quan hóa Đồ thị Không gian Vector SVG Kép (Dual-Panel Causal Tree):**
     - Panel A: Sơ đồ Cây Quyết định Phân nhánh (Decision Tree Flowchart) thể hiện các nút điều kiện rẽ nhánh và các lá phân khúc được viền màu theo hiệu ứng can thiệp $\hat{\tau}_k$.
     - Panel B: Biểu đồ Rừng Đối chiếu Phân khúc (Forest Plot) minh họa các điểm ước lượng $\hat{\tau}_k$ kèm thanh sai số khoảng tin cậy 95% CI và đường tham chiếu vô hiệu 0.
  5. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn báo cáo chuẩn mực khoa học theo Athey & Imbens (2016): quy mô tập cấu trúc và tập ước lượng, hiệu ứng trung bình toàn mẫu ATE, số phân khúc được nhận diện, mô tả chi tiết quy tắc điều kiện của nhóm hưởng lợi nhiều nhất và nhóm bị tác động bất lợi nhất, cùng giá trị $\hat{\tau}$, SE, 95% CI, và $p$-value.
- **Niêm phong kiểm toán:** Tự động ghi nhận `CAUSAL_TREE_SUBGROUPS_EVALUATED` vào chuỗi sổ cái SHA-256.


### 81. Multiple Testing Correction & False Discovery Rate (FDR Matrix) Engine (Benjamini & Hochberg 1995, Storey 2002)

- **Mục tiêu khoa học:** Khắc phục triệt để vấn đề kiểm định lặp (Multiple Hypothesis Testing) và lạm phát sai lầm loại I (Family-Wise Error Rate inflation) khi phân tích hàng chục, hàng trăm cặp biến hoặc giả thuyết tương quan đồng thời trong các bảng khảo sát quy mô lớn.
- **Cơ sở phương pháp luận:**
  1. **Benjamini-Hochberg (BH) Step-Up Procedure (1995):** Sắp xếp tăng dần các $p$-value $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$. Tìm rank lớn nhất $k$ thỏa mãn $p_{(k)} \le \frac{k}{m} Q$, và bác bỏ toàn bộ các giả thuyết $H_{(1)}, \dots, H_{(k)}$. Giá trị điều chỉnh $q$-value: $q_{BH(i)} = \min_{j \ge i} \left\{ \frac{m}{j} p_{(j)} \right\}$.
  2. **Benjamini-Yekutieli (BY) Arbitrary Dependence Control (2001):** Hiệu chỉnh dưới cấu trúc phụ thuộc bất kỳ giữa các biến khảo sát với hệ số điều hòa $c(m) = \sum_{j=1}^m \frac{1}{j}$: $q_{BY(i)} = \min_{j \ge i} \left\{ \frac{m \cdot c(m)}{j} p_{(j)} \right\}$.
  3. **Bonferroni Conservative Family-Wise Error Rate (FWER):** Ngưỡng hiệu chỉnh cực đoan $\alpha / m$ để đối chiếu mức độ bảo thủ và xác định những phát hiện vững chắc tuyệt đối.
  4. **Ước lượng Tỷ lệ Giả thuyết Vô hiệu Thực tế $\hat{\pi}_0$ (Storey 2002):** Ước lượng $\hat{\pi}_0(\lambda = 0.5) = \frac{\#\{p_i > 0.5\}}{m(1 - 0.5)}$ để đánh giá tỷ lệ tín hiệu thật trên dữ liệu.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/multiple-testing-fdr`
- **Request Body (`MultipleTestingFDRRequest`):**
  - `question_ids`: Danh sách ID các câu hỏi định lượng để tự động tính toán toàn bộ ma trận tương quan Pearson cặp $\frac{k(k-1)}{2}$ và kiểm định FDR.
  - `custom_p_values`: Danh sách giá trị $p$-value tùy chọn nhập thủ công từ các mô hình hồi quy / kiểm định bên ngoài.
  - `custom_labels`: Danh sách nhãn giả thuyết tương ứng với `custom_p_values`.
  - `fdr_q`: Mức ý nghĩa mục tiêu FDR $Q$ (mặc định: `0.05`, phạm vi: `0.01` - `0.20`).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`MultipleTestingFDROut`):**
  - `status`: `"success"` hoặc `"error"`.
  - `sample_diagnostics`:
    - `total_hypotheses_m`: Tổng số giả thuyết kiểm định đồng thời.
    - `fdr_target_q`: Mức ý nghĩa mục tiêu FDR $Q$.
    - `estimated_pi_0_null_proportion`: Tỷ lệ giả thuyết vô hiệu $\hat{\pi}_0$.
    - `raw_significant_count`: Số phát hiện thô ($p < Q$).
    - `bh_fdr_significant_count`: Số phát hiện có ý nghĩa thực thụ được bảo toàn bởi Benjamini-Hochberg FDR.
    - `by_fdr_significant_count`: Số phát hiện vượt qua kiểm soát phụ thuộc Benjamini-Yekutieli.
    - `bonferroni_significant_count`: Số phát hiện vượt qua kiểm định Bonferroni cực đoan.
    - `rescued_by_bh_count`: Số phát hiện thực thụ được giải cứu khỏi sự bảo thủ triệt tiêu của Bonferroni.
    - `filtered_false_positives_count`: Số giả thuyết dương tính giả do kiểm định lặp đã được sàng lọc loại trừ.
  - `corrections`: Danh sách kết quả chi tiết từng giả thuyết theo thứ tự xếp hạng rank tăng dần:
    - `rank`: Thứ hạng $i \in [1, m]$.
    - `hypothesis`: Nhãn giả thuyết hoặc cặp câu hỏi tương quan.
    - `raw_p_value`: $p$-value thô ban đầu.
    - `bh_critical_value`: Ngưỡng cắt BH tại rank $i$: $\frac{i}{m} Q$.
    - `bh_q_value`: Giá trị $q$-value Benjamini-Hochberg điều chỉnh.
    - `by_adjusted_p`: Giá trị $p$-value Benjamini-Yekutieli điều chỉnh.
    - `bonferroni_p`: Giá trị $p$-value Bonferroni điều chỉnh ($\min(1, m \cdot p)$).
    - `is_significant_bh`: Boolean đạt ý nghĩa thống kê theo BH ($q_{BH} \le Q$).
    - `is_significant_bonferroni`: Boolean đạt ý nghĩa theo Bonferroni ($p_{Bonf} < Q$).
    - `decision_status`: Phân loại kết luận:
      - `SURVIVES_BONFERRONI`: Vững chắc tuyệt đối (vượt qua cả Bonferroni).
      - `DISCOVERED_BH_FDR`: Ý nghĩa thực thụ (được bảo toàn bởi FDR).
      - `FILTERED_FALSE_POSITIVE`: Dương tính giả đã lọc (loại trừ sai lầm Type I).
      - `NON_SIGNIFICANT`: Không có ý nghĩa thống kê.
    - `decision_badge`: Nhãn hiển thị giao diện tiếng Việt mô tả trực quan.
  - `svg_chart`: Mã nguồn biểu đồ vector SVG kép trực quan hóa:
    - Panel A: Đồ thị Rank-Order P-Value Curve đối chiếu đường chéo ngưỡng Benjamini-Hochberg $\frac{i}{m} Q$ và đường ngang Bonferroni $\frac{Q}{m}$.
    - Panel B: Biểu đồ thanh đối chiếu số lượng phát hiện qua 4 tầng kiểm soát: Raw vs BH FDR vs BY FDR vs Bonferroni.
  - `apa_narrative`: Đoạn thuyết minh học thuật định dạng chuẩn APA 7th Edition tóm tắt đầy đủ các chỉ số thống kê, tỷ lệ $\hat{\pi}_0$, số phát hiện được bảo toàn và số dương tính giả đã loại trừ.
- **Niêm phong kiểm toán:** Tự động ghi nhận sự kiện `MULTIPLE_TESTING_FDR_CORRECTED` vào chuỗi sổ cái SHA-256.


### 82. Bayesian Structural Equation Modeling (BSEM) Engine with MCMC Gibbs Sampling & Prior Sensitivity (Muthén & Asparouhov 2012, Gelman et al. 2013)

- **Mục tiêu khoa học:** Khắc phục nút thắt nhận diện và bác bỏ mô hình sai lầm của SEM cổ điển (Maximum Likelihood SEM) khi áp đặt các ràng buộc zero cứng nhắc trên hệ số tải chéo và hiệp phương sai phần dư. BSEM thay thế các số 0 cứng nhắc bằng phân phối tiên nghiệm co rút thông tin nhỏ $\lambda_{\text{cross}} \sim \mathcal{N}(0, \sigma_0^2)$, cho phép sai lệch nhỏ phản ánh thực tế dữ liệu xã hội học & tâm lý học mà không cần dò tìm chỉ số điều chỉnh (modification indices) hậu nghiệm mang tính bóp méo.
- **Cơ sở phương pháp luận:**
  1. **Mô hình Đo lường & Co rút Tiên nghiệm Nhỏ (Muthén & Asparouhov 2012):**
     $$y_{ij} = \sum_{k=1}^K \lambda_{jk} \eta_{ik} + \epsilon_{ij}, \quad \epsilon_{ij} \sim \mathcal{N}(0, \theta_j)$$
     Chỉ báo chính $k^*$: $\lambda_{j, k^*} \sim \mathcal{N}(1.0, 1.0)$ (diffuse).
     Tải chéo $k \ne k^*$: $\lambda_{j, k} \sim \mathcal{N}(0, \sigma_0^2)$ với $\sigma_0 \in [0.005, 0.10]$ (shrinkage informative prior).
     Phương sai phần dư: $\theta_j \sim \text{Inverse-Gamma}(1.0, 1.0)$.
  2. **Thuật toán MCMC Gibbs Sampling & Data Augmentation:**
     Lấy mẫu đan xen các biến tiềm ẩn $\eta_i \sim \mathcal{N}(\mu_\eta, \Sigma_\eta)$, hệ số tải $\Lambda$ qua hồi quy Bayes liên hợp, phương sai sai số $\Theta \sim \text{Inv-Gamma}$, và hệ số hồi quy cấu trúc $\gamma \sim \mathcal{N}(\mu_\gamma, \Sigma_\gamma)$.
  3. **Chẩn đoán Hội tụ Chuỗi Bayes (Gelman et al. 2013):**
     - Chỉ số Gelman-Rubin $\hat{R}$ giữa các chuỗi MCMC song song: $\hat{R} = \sqrt{\frac{\hat{V}}{W}} \le 1.10$.
     - Kích thước mẫu hiệu dụng Effective Sample Size (ESS) sau khi khử tự tương quan.
     - Sai số chuẩn Monte Carlo (MCSE): $\text{MCSE} = \frac{\text{Posterior SD}}{\sqrt{\text{ESS}}}$.
  4. **Kiểm định Phù hợp Mô hình Hậu nghiệm PPP (Posterior Predictive Checking):**
     Tính hàm khoảng cách discrepancy $D(y, \theta)$ trên dữ liệu quan sát và $D(y^{\text{rep}}, \theta)$ trên dữ liệu mô phỏng lặp lại:
     $$PPP = \frac{1}{S} \sum_{s=1}^S \mathbb{I}(D(y^{\text{rep}}, \theta^{(s)}) > D(y, \theta^{(s)}))$$
     Mô hình hoàn hảo khi $PPP \approx 0.50$ ($0.20 \le PPP \le 0.80$ xuất sắc; $PPP < 0.05$ bị bác bỏ).
  5. **Phân tích Độ nhạy Tiên nghiệm (van Erp et al. 2018):**
     Đánh giá độ trôi của hệ số cấu trúc $\gamma$ khi biến thiên độ lệch chuẩn tiên nghiệm co rút $\sigma_0 \in \{0.005, 0.01, 0.05, 0.10\}$ để phân loại `HIGHLY_ROBUST_TO_PRIOR`, `MODERATELY_ROBUST`, hoặc `PRIOR_SENSITIVE`.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/bsem`
- **Request Body (`BSEMRequest`):**
  - `measurement_spec`: Ánh xạ tên biến tiềm ẩn (ví dụ: `"F1_Motivation"`, `"F2_Performance"`) tới danh sách ID các câu hỏi chỉ báo chính.
  - `structural_regressions`: Danh sách đường dẫn hồi quy giữa các biến tiềm ẩn, ví dụ: `[{"source": "F1_Motivation", "target": "F2_Performance"}]`.
  - `prior_cross_loading_sd`: Độ lệch chuẩn tiên nghiệm cho tải chéo $\sigma_0$ (mặc định: `0.01`).
  - `n_iterations`: Số lượt lặp Gibbs mỗi chuỗi (mặc định: `800`).
  - `n_burnin`: Số lượt lặp khởi động loại bỏ (mặc định: `300`).
  - `n_chains`: Số chuỗi MCMC song song (mặc định: `2`).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`BSEMOut`):**
  - `status`: `"success"` hoặc `"error"`.
  - `sample_diagnostics`: Thống kê $N, K, P$, số chuỗi, số lượt lặp, $PPP$ fit index, huy hiệu đánh giá phù hợp và độ bền vững tiên nghiệm.
  - `structural_paths`: Danh sách tham số đường dẫn cấu trúc: trung bình hậu nghiệm $\gamma$, SD, khoảng tin cậy 95% Credible Interval, $\hat{R}$, ESS, MCSE, $p_{\text{Bayes}}$, và trạng thái hội tụ.
  - `loadings`: Danh sách hệ số tải nhân tố (cả chỉ báo chính và tải chéo co rút) kèm khoảng tin cậy hậu nghiệm 95%.
  - `prior_sensitivity`: Bảng đối chiếu độ trôi của tham số cấu trúc qua các mức tiên nghiệm $\sigma_0$.
  - `svg_chart`: Mã nguồn biểu đồ vector SVG kép:
    - Panel A: Đồ thị MCMC Gibbs Trace & Đường cong Mật độ Xác suất Hậu nghiệm (Posterior Density).
    - Panel B: Sơ đồ đường dẫn BSEM với các nhân tố tiềm ẩn, chỉ báo chính và mũi tên nét đứt minh họa tải chéo co rút nhỏ.
  - `apa_narrative`: Đoạn thuyết minh học thuật chuẩn mực APA 7th Edition theo Muthén & Asparouhov (2012).
- **Niêm phong kiểm toán:** Tự động ghi nhận `BSEM_EVALUATED` vào chuỗi sổ cái SHA-256.


### 83. Endogeneity Control via Gaussian Copula Estimation Engine (Park & Gupta 2012, Becker et al. 2022)

- **Mục tiêu khoa học:** Khắc phục triệt để vấn đề sai lệch nội sinh (Endogeneity Bias) do biến tiềm ẩn bị bỏ sót (omitted variable bias), sai số đo lường (measurement error) hoặc đồng thời (simultaneity) trong các mô hình khảo sát hành vi & kinh tế lượng mà **không cần tìm kiếm biến công cụ ngoại sinh** (External Instrumental Variables) - vốn là rào cản nan giải hàng đầu trong nghiên cứu thực nghiệm.
- **Cơ sở phương pháp luận:**
  1. **Khái niệm & Sự Tồn tại của Bổ đề Phân phối Phi chuẩn (Park & Gupta 2012):**
     Nếu biến độc lập nội sinh $P$ có phân phối phi chuẩn (Non-normal distribution - đặc trưng phổ biến của thang đo Likert, xếp hạng thứ tự, doanh thu, hành vi), hàm phân phối tích lũy thực nghiệm $\hat{F}_P(P)$ có thể được ánh xạ vào phân phối chuẩn tắc thông qua nghịch đảo hàm Gauss:
     $$C_P = \Phi^{-1}(\hat{F}_P(P))$$
  2. **Mô hình Hồi quy Bổ sung Biến Công cụ Copula:**
     $$Y = \beta_0 + \beta_P P + \sum_{k} \gamma_k X_k + \rho C_P + \nu$$
     - $\beta_P$: Hệ số tác động nhân quả đã được làm sạch và hiệu chỉnh sai lệch nội sinh.
     - $\rho$: Tham số hiệp phương sai copula đo lường mức độ và chiều hướng nội sinh.
  3. **Kiểm định Thống kê Kiểm chứng Nội sinh:**
     - Giả thuyết: $H_0: \rho = 0$ (Ngoại sinh) vs $H_1: \rho \ne 0$ (Nội sinh nghiêm trọng).
     - Thống kê $t_\rho = \frac{\hat{\rho}}{\text{SE}_{\text{boot}}(\hat{\rho})}$. Nếu $p < 0.05$, OLS cổ điển bị chứng minh là sai lệch (biased), và mô hình Gaussian Copula là bắt buộc.
  4. **Kiểm định Điều kiện Tiên quyết Phi Chuẩn (Non-Normality Diagnostics):**
     - Kiểm định Jarque-Bera $JB = \frac{N}{6}(S^2 + K^2/4)$ đối với $P$. Yêu cầu $p_{JB} < 0.05$.
     - Kiểm tra đa cộng tuyến: Variance Inflation Factor (VIF) của số hạng $C_P$ đảm bảo $< 10$ để kiểm soát điều kiện ước lượng.
  5. **Suy diễn Bootstrap Phi Tham số (Bootstrap Standard Errors):**
     Do $C_P$ là biến công cụ được ước lượng từ mẫu, sai số chuẩn của $\beta_P$ và $\rho$ được tính toán qua thuật toán tái chọn mẫu Bootstrap (mặc định $B = 250$ to $400$ resamples) để cung cấp khoảng tin cậy 95% Bootstrap Confidence Intervals không phụ thuộc vào giả định phân phối.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/gaussian-copula`
- **Request Body (`GaussianCopulaRequest`):**
  - `endogenous_question_id`: ID câu hỏi đại diện cho biến độc lập nghi ngờ bị nội sinh $P$.
  - `outcome_question_id`: ID câu hỏi đại diện cho biến kết quả / phụ thuộc $Y$.
  - `control_question_ids`: Danh sách ID các câu hỏi kiểm soát bổ sung $X_k$.
  - `n_bootstraps`: Số lượt tái chọn mẫu Bootstrap (mặc định: `400`).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`GaussianCopulaOut`):**
  - `status`: `"success"` hoặc `"error"`.
  - `sample_diagnostics`: Thống kê mẫu $N$, kiểm định Jarque-Bera ($JB$, $p$, Skewness, Kurtosis), trạng thái thỏa mãn phi chuẩn, VIF của biến công cụ Copula, và kết luận nội sinh (`ENDOGENEITY_CONFIRMED` hoặc `NO_SIGNIFICANT_ENDOGENEITY`).
  - `naive_ols`: Kết quả ước lượng hồi quy OLS ngây thơ (chưa hiệu chỉnh): $\beta_{\text{OLS}}$, SE, $t$-stat, 95% CI, $R^2$.
  - `copula_corrected`: Kết quả ước lượng hiệu chỉnh Gaussian Copula: $\beta_{\text{Copula}}$, Bootstrap SE, 95% Bootstrap CI, tham số $\rho$, SE của $\rho$, $t_\rho$, $p$-value của $\rho$, khoảng cách sai lệch nội sinh $\Delta = \beta_{\text{OLS}} - \beta_{\text{Copula}}$, và tỷ lệ phần trăm sai lệch bias.
  - `svg_chart`: Mã nguồn biểu đồ vector SVG kép:
    - Panel A: Phân phối thực nghiệm phi chuẩn của biến nội sinh $P$ kèm kiểm định Jarque-Bera.
    - Panel B: Biểu đồ Forest Plot so sánh trực quan hiệu ứng OLS Ngây thơ vs Đã Hiệu chỉnh Copula kèm thanh sai lệch nội sinh.
  - `apa_narrative`: Đoạn thuyết minh học thuật định dạng chuẩn APA 7th Edition theo Park & Gupta (2012).
- **Niêm phong kiểm toán:** Tự động ghi nhận `GAUSSIAN_COPULA_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 84. Dynamic Factor Modeling (DFM) with Kalman Filter & RTS State-Space Smoothing

- **Mục tiêu khoa học:** Trích xuất và giải mã quỹ đạo của các biến nhân tố tiềm ẩn vĩ mô/hành vi chuyển động qua các chu kỳ/mốc thời gian khảo sát (Multi-wave Longitudinal / Time-Series Panel Surveys) bằng mô hình Không gian trạng thái (State-Space Model) kết hợp Bộ lọc Kalman chuyển tiếp (Forward Kalman Filter) và Bộ làm mịn lùi Rauch-Tung-Striebel (Backward RTS Smoother) (**Stock & Watson 2002, 2011**; **Durbin & Koopman 2012**; **Harvey 1989**).
- **Cơ sở phương pháp luận:**
  1. **Phương trình Quan sát (Measurement Equation):**
     $$y_t = \Lambda f_t + \epsilon_t, \quad \epsilon_t \sim \mathcal{N}(0, R)$$
     Trong đó $y_t$ là vector $P \times 1$ gồm các chỉ báo câu hỏi khảo sát tại chu kỳ $t$, $\Lambda$ là ma trận hệ số tải nhân tố (Factor Loadings), $f_t$ là biến trạng thái tiềm ẩn bậc 1 ($r=1$), và $R = \text{diag}(\sigma_1^2, \dots, \sigma_P^2)$ là ma trận phương sai sai số đặc trưng (idiosyncratic variance).
  2. **Phương trình Chuyển đổi Trạng thái (Transition Equation - AR(1)):**
     $$f_t = A f_{t-1} + \eta_t, \quad \eta_t \sim \mathcal{N}(0, Q)$$
     Với $A$ là hệ số tự tương quan bậc 1 của nhân tố tiềm ẩn, $Q = \text{Var}(\eta_t)$ là phương sai nhiễu chuyển đổi.
  3. **Bộ lọc Kalman Chuyển tiếp (Forward Kalman Filter):**
     - Dự báo: $f_{t|t-1} = A f_{t-1|t-1}$, $P_{t|t-1} = A P_{t-1|t-1} A^T + Q$
     - Đổi mới (Innovation): $v_t = y_t - \Lambda f_{t|t-1}$, $F_t = \Lambda P_{t|t-1} \Lambda^T + R$
     - Cập nhật trọng số Kalman Gain: $K_t = P_{t|t-1} \Lambda^T F_t^{-1}$
     - Cập nhật trạng thái: $f_{t|t} = f_{t|t-1} + K_t v_t$, $P_{t|t} = (I - K_t \Lambda) P_{t|t-1}$
  4. **Bộ làm mịn Lùi Rauch-Tung-Striebel (Backward RTS Smoother):**
     Tái tạo quỹ đạo tối ưu có điều kiện trên toàn bộ lịch sử thời gian $T$:
     $$J_t = P_{t|t} A^T P_{t+1|t}^{-1}$$
     $$f_{t|T} = f_{t|t} + J_t (f_{t+1|T} - f_{t+1|t})$$
     $$P_{t|T} = P_{t|t} + J_t (P_{t+1|T} - P_{t+1|t}) J_t^T$$
  5. **Phân rã Phương sai & Tỷ lệ Tín hiệu trên Nhiễu (Signal-to-Noise Ratio):**
     Tách bạch phương sai của từng chỉ báo $j$ thành thành phần nhân tố chung (Common Component Variance) và thành phần nhiễu đặc thù (Idiosyncratic Noise Variance), tính toán $R_j^2 = \frac{\lambda_j^2 \text{Var}(f)}{\lambda_j^2 \text{Var}(f) + \sigma_j^2}$.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/dynamic-factor`
- **Request Body (`DynamicFactorModelRequest`):**
  - `indicator_question_ids`: Danh sách UUID của các câu hỏi đo lường qua các chu kỳ.
  - `time_question_id`: UUID của câu hỏi biểu thị chu kỳ/thời điểm (Wave/Period) (tùy chọn; nếu để trống hệ thống tự chia theo thời gian nộp bài `submitted_at`).
  - `num_time_bins`: Số phân đoạn thời gian (mặc định: `10`, tối thiểu 4).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`DynamicFactorModelOut`):**
  - `status`: `"success"` hoặc `"error"`.
  - `summary`: Tổng số quan sát $N$, số mốc thời gian $T$, số chỉ báo $P$, hệ số quán tính nhân tố $A$, phương sai nhiễu $Q$, tỷ lệ giải thích tổng thể của nhân tố tiềm ẩn $R^2$.
  - `trajectories`: Danh sách các điểm thời gian $t = 1 \dots T$ gồm: giá trị nhân tố làm mịn $f_{t|T}$, độ lệch chuẩn làm mịn $SE$, khoảng tin cậy 95% CI $[f_{\text{low}}, f_{\text{high}}]$, và giá trị nhân tố lọc thời gian thực $f_{t|t}$.
  - `factor_loadings`: Danh sách các chỉ báo $j$ gồm: hệ số tải $\lambda_j$, phương sai nhiễu đặc trưng $\sigma_j^2$, tỷ lệ phương sai giải thích $R_j^2$, và tỷ số SNR.
  - `svg_chart`: Biểu đồ vector SVG kép:
    - Panel A: Đồ thị Quỹ đạo Động học Nhân tố Tiềm ẩn (Latent Dynamic Factor Trajectory) với dải băng khoảng tin cậy 95% Confidence Ribbon và đường làm mịn RTS vs đường lọc Kalman.
    - Panel B: Biểu đồ Thanh Xếp chồng Phân rã Phương sai (Stacked Variance Decomposition) minh họa tỷ lệ tín hiệu chung vs nhiễu đặc thù theo từng câu hỏi.
  - `apa_narrative`: Đoạn thuyết minh học thuật định dạng chuẩn APA 7th Edition theo Stock & Watson (2002) và Durbin & Koopman (2012).
- **Niêm phong kiểm toán:** Tự động ghi nhận `DYNAMIC_FACTOR_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 85. Extreme Bound Analysis (EBA) Specification Curve Engine

- **Mục tiêu khoa học:** Kiểm định toàn diện độ nhạy và tính vững chắc của các phát hiện thực nghiệm/kinh tế lượng khảo sát chống lại hiện tượng khai thác dữ liệu có chủ đích (p-hacking / specification searching / data mining) (**Leamer 1983, 1985**; **Sala-i-Martin 1997**; **Christensen & Miguel 2018**).
- **Cơ sở phương pháp luận:**
  1. **Không gian Đặc tả Mô hình Tổ hợp (Combinatorial Model Space):**
     Với một biến độc lập trọng tâm $P$ (Focus variable - chính sách, can thiệp hoặc cấu trúc tâm lý then chốt), một biến phụ thuộc $Y$, một tập biến kiểm soát bắt buộc $D$ (Free variables), và một bể $K$ biến kiểm soát ứng viên $\{Z_1, \dots, Z_K\}$, hệ thống ước lượng toàn bộ $M$ tổ hợp mô hình OLS:
     $$Y = \beta_0 + \beta_P^{(m)} P + \sum_{d \in D} \gamma_d X_d + \sum_{z \in Z^{(m)}} \theta_z Z_z + \epsilon^{(m)}$$
     với $Z^{(m)} \subseteq \{Z_1, \dots, Z_K\}$ có kích thước lên đến $k_{\max}$.
  2. **Tiêu chuẩn Cực trị Nghiêm ngặt của Leamer (1983):**
     Xác định khoảng cực trị mở rộng:
     $$\text{Lower Bound} = \min_{m} \left( \hat{\beta}_P^{(m)} - 1.96 \cdot \text{SE}(\hat{\beta}_P^{(m)}) \right)$$
     $$\text{Upper Bound} = \max_{m} \left( \hat{\beta}_P^{(m)} + 1.96 \cdot \text{SE}(\hat{\beta}_P^{(m)}) \right)$$
     - Nếu $\text{Lower Bound} > 0$: Kết luận `ROBUST_POSITIVE` (Tác động dương vững chắc trên mọi biến cố kiểm soát).
     - Nếu $\text{Upper Bound} < 0$: Kết luận `ROBUST_NEGATIVE` (Tác động âm vững chắc trên mọi biến cố kiểm soát).
     - Nếu khoảng cực trị bao trùm điểm 0: Kết luận `FRAGILE` (Dễ vỡ / Nhạy cảm - tồn tại đặc tả biến kiểm soát làm đảo chiều hoặc triệt tiêu tác động).
  3. **Tiêu chuẩn Phân phối Tích lũy Sala-i-Martin (1997):**
     Khắc phục tính chất quá khắt khe của Leamer bằng cách tích hợp toàn bộ hàm mật độ xác suất của $\hat{\beta}_P$:
     $$\text{CDF}(0) = \max \left( \frac{1}{M}\sum_{m=1}^M \Phi\left(\frac{\hat{\beta}^{(m)}}{\text{SE}^{(m)}}\right), 1 - \frac{1}{M}\sum_{m=1}^M \Phi\left(\frac{\hat{\beta}^{(m)}}{\text{SE}^{(m)}}\right) \right)$$
     và trọng số độ khớp $R^2$:
     $$\text{Weighted CDF}(0) = \max \left( \frac{\sum R^{2(m)} \Phi(\cdot)}{\sum R^{2(m)}}, 1 - \frac{\sum R^{2(m)} \Phi(\cdot)}{\sum R^{2(m)}} \right)$$
     Nếu $\text{CDF}(0) \ge 0.95$, mối quan hệ được xếp loại `ROBUST` (95% khối lượng phân phối tích lũy nằm hoàn toàn về một phía của trục số 0).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/extreme-bounds`
- **Request Body (`ExtremeBoundsAnalysisRequest`):**
  - `focus_question_id`: UUID của câu hỏi độc lập trọng tâm $P$.
  - `outcome_question_id`: UUID của câu hỏi phụ thuộc $Y$.
  - `candidate_question_ids`: Danh sách UUID của các câu hỏi kiểm soát ứng viên $Z_k$.
  - `free_question_ids`: Danh sách UUID của các biến bắt buộc luôn xuất hiện trong mọi mô hình (tùy chọn).
  - `max_controls_per_model`: Giới hạn số biến kiểm soát tối đa trong 1 mô hình (mặc định: `4`).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`ExtremeBoundsAnalysisOut`):**
  - `status`: `"success"` hoặc `"error"`.
  - `summary`: Tổng quan $N$, số mô hình $M$, $\beta_{\text{mean}}$, $\beta_{\text{median}}$, $\beta_{\text{min}}$, $\beta_{\text{max}}$, $\text{SD}(\beta)$, các mốc Leamer bounds, nhãn kết luận Leamer, điểm Sala-i-Martin CDF(0), nhãn kết luận Sala-i-Martin, tỷ lệ mô hình có ý nghĩa $p < 0.05$, các biến kiểm soát tạo ra mô hình cực tiểu và cực đại.
  - `specifications_sample`: Mẫu danh sách các mô hình hồi quy đại diện đã sắp xếp kèm hệ số, SE, $t$, $p$, $R^2$, 95% CI và danh sách biến kiểm soát.
  - `svg_chart`: Biểu đồ vector SVG kép:
    - Panel A: Đường cong Đặc tả Mô hình (Specification Curve) hiển thị các hệ số $\hat{\beta}_P$ kèm dải sai số 95% CI được tô màu theo mức ý nghĩa thống kê.
    - Panel B: Biểu đồ Histogram phân phối tần suất $\beta$ kèm vạch chỉ báo Leamer Extreme Bounds và Widget đo lường Sala-i-Martin CDF(0).
  - `apa_narrative`: Đoạn thuyết minh học thuật định dạng chuẩn APA 7th Edition theo Leamer (1983) và Sala-i-Martin (1997).
- **Niêm phong kiểm toán:** Tự động ghi nhận `EXTREME_BOUNDS_ANALYSIS_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 86. Spatial Econometrics & Moran's I Autoregressive Engine (SAR / SEM)

- **Mục tiêu khoa học:** Khắc phục vi phạm giả định độc lập không gian của định lý Gauss-Markov (Tobler's First Law of Geography) trong các cuộc khảo sát thực địa có tọa độ GPS; kiểm định sự tồn tại của tự tương quan không gian (Global Moran's I), kiểm định chẩn đoán nhân tử Lagrange (Anselin LM Tests), và ước lượng mô hình hồi quy tự hồi quy không gian (Spatial Lag Model - SAR) nhằm phân rã hiệu ứng tác động trực tiếp và lan tỏa không gian (**Anselin 1988**; **LeSage & Pace 2009**; **Kelejian & Prucha 1998**; **Moran 1950**).
- **Cơ sở phương pháp luận:**
  1. **Ma trận Trọng số Không gian Chuẩn hóa Hàng (Row-Standardized Spatial Weights Matrix W):**
     Tính khoảng cách trắc địa đường cong mặt đất Haversine giữa các điểm tọa độ GPS $(\text{lat}_i, \text{lon}_i)$:
     - Nghịch đảo khoảng cách: $w_{ij}^* = \frac{1}{d_{ij}^\alpha}$ ($i \ne j$), $w_{ii}^* = 0$.
     - Hoặc K láng giềng gần nhất (KNN): $w_{ij}^* = 1$ nếu $j \in N_k(i)$.
     - Chuẩn hóa hàng: $w_{ij} = \frac{w_{ij}^*}{\sum_{k} w_{ik}^*}$ đảm bảo $\sum_j w_{ij} = 1$.
  2. **Kiểm định Tự tương quan Không gian Toàn cục Moran's I:**
     $$I = \frac{N}{\sum_i \sum_j w_{ij}} \frac{\sum_i \sum_j w_{ij} (y_i - \bar{y})(y_j - \bar{y})}{\sum_i (y_i - \bar{y})^2}$$
     - Kỳ vọng dưới giả thuyết vô hiệu $H_0$ (phân bổ ngẫu nhiên): $E[I] = -\frac{1}{N - 1}$.
     - Phương sai giải tích $\text{Var}(I)$, kiểm định $z$-score $z = \frac{I - E[I]}{\sqrt{\text{Var}(I)}}$ và giá trị $p$.
     - Phân loại: `SPATIAL_CLUSTERING_POSITIVE` (tập trung thành chùm không gian), `SPATIAL_DISPERSION_NEGATIVE` (phân tán không gian), hoặc `RANDOM_SPATIAL_DISTRIBUTION`.
  3. **Kiểm định Chẩn đoán Nhân tử Lagrange Anselin (1988):**
     - $LM_{\text{Lag}}$ kiểm định hiện tượng trễ không gian (Spatial Lag).
     - $LM_{\text{Error}}$ kiểm định hiện tượng sai số không gian (Spatial Error).
     - Định hướng nhà nghiên cứu lựa chọn mô hình tối ưu: Classical OLS, Spatial Lag (SAR), hay Spatial Error (SEM).
  4. **Ước lượng Mô hình Tự hồi quy Không gian (SAR) qua Spatial 2SLS (Kelejian & Prucha 1998):**
     $$Y = \rho W Y + X \beta + \epsilon$$
     với biến nội sinh không gian $W Y$ được công cụ hóa bằng không gian công cụ bậc cao $[X, W X, W^2 X]$.
  5. **Phân rã Hiệu ứng Tác động LeSage & Pace (2009):**
     Ma trận hệ số nhân không gian $(I - \hat{\rho} W)^{-1}$:
     - Tác động Trực tiếp (Direct Impact): Mức độ thay đổi của $Y_i$ khi biến $X_{ik}$ tại chính địa bàn $i$ thay đổi.
     - Tác động Gián tiếp / Lan tỏa Không gian (Spatial Spillover Impact): Mức độ thay đổi của $Y_i$ do tác động lan truyền từ các địa bàn láng giềng $j \ne i$.
     - Tổng tác động (Total Impact): $\text{Direct} + \text{Indirect} = \frac{\beta_k}{1 - \hat{\rho}}$.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/spatial-econometrics`
- **Request Body (`SpatialEconometricsRequest`):**
  - `outcome_question_id`: UUID của câu hỏi phụ thuộc $Y$.
  - `covariate_question_ids`: Danh sách UUID các câu hỏi độc lập $X_k$.
  - `lat_field`: Trường chứa vĩ độ (mặc định trích xuất từ `client_metadata.latitude`).
  - `lon_field`: Trường chứa kinh độ (mặc định trích xuất từ `client_metadata.longitude`).
  - `weights_type`: `"inverse_distance"` hoặc `"knn"`.
  - `knn_k`: Số láng giềng nếu chọn KNN (mặc định: `5`).
  - `distance_power`: Số mũ khoảng cách $\alpha$ (mặc định: `1.0`).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`SpatialEconometricsOut`):**
  - `status`: `"success"` hoặc `"error"`.
  - `morans_i`: Chỉ số $I$, $E[I]$, phương sai, $SE$, $z$-score, $p$-value, phân loại, giải thích và số lượng điểm theo 4 góc phần tư: High-High, Low-Low, High-Low, Low-High.
  - `lm_diagnostics`: Thống kê $LM_{\text{Lag}}$, $LM_{\text{Error}}$, $p$-values và mô hình khuyến nghị.
  - `baseline_ols`: Kết quả OLS truyền thống để đối chiếu.
  - `spatial_lag_model`: Tham số lan tỏa không gian $\rho$, $SE$, $z$, $p$, $R^2$, và bảng phân rã hiệu ứng LeSage & Pace (Direct, Spillover, Total, Spillover Ratio) cho từng biến giải thích.
  - `svg_chart`: Biểu đồ vector SVG kép:
    - Panel A: Biểu đồ Phân tán Moran (Moran Scatterplot $W Y$ vs $Y$) với 4 góc phần tư và đường dốc hồi quy Moran's $I$.
    - Panel B: Biểu đồ Thanh nhóm Phân rã Hiệu ứng (Direct vs Spillover Impacts Decomposition) cho từng biến giải thích.
  - `apa_narrative`: Đoạn thuyết minh học thuật định dạng chuẩn APA 7th Edition theo Anselin (1988) và LeSage & Pace (2009).
- **Niêm phong kiểm toán:** Tự động ghi nhận `SPATIAL_ECONOMETRICS_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 87. Instrumental Variable Quantile Regression (IV-QR) Engine

- **Mục tiêu khoa học:** Ước lượng tác động nhân quả phi tuyến phân vị (Quantile Treatment Effects) của một biến can thiệp/chính sách bị nghi ngờ nội sinh (Endogenous Treatment $D$) lên toàn bộ phổ phân phối của biến kết quả $Y$, sử dụng biến công cụ $Z$ theo phương pháp Nghịch đảo Hồi quy Phân vị (Inverse Quantile Regression - IQR) và khoảng tin cậy đảo ngược hàm mục tiêu Wald (**Chernozhukov & Hansen 2005, 2006, 2008**; **Chernozhukov, Hansen, & Jansson 2009**).
- **Cơ sở phương pháp luận:**
  1. **Hạn chế của Mô hình Cổ điển (2SLS & QR tiêu chuẩn):**
     - Mô hình 2SLS thông thường chỉ ước lượng hiệu ứng trung bình cục bộ (Local Average Treatment Effect - LATE), hoàn toàn che giấu hiện tượng chính sách có thể mang lại lợi ích rất lớn cho nhóm yếu thế (phân vị thấp $\tau = 0.10, 0.25$) nhưng không có tác dụng hoặc gây phản tác dụng ở nhóm phân vị cao ($\tau = 0.75, 0.90$).
     - Ngược lại, Hồi quy Phân vị Tiêu chuẩn (Koenker & Bassett 1978) đòi hỏi giả định ngoại sinh; khi người trả lời tự chọn lọc tham gia can thiệp ($D$ tương quan với yếu tố tiềm ẩn $U$), QR tiêu chuẩn bị chệch nghiêm trọng.
  2. **Thuật toán Nghịch đảo Hồi quy Phân vị (Inverse Quantile Regression - IQR):**
     Với mỗi phân vị $\tau \in \{0.10, 0.25, 0.50, 0.75, 0.90\}$:
     - Quét lưới các giá trị tham số can thiệp tiềm năng $\alpha \in [\alpha_{\min}, \alpha_{\max}]$.
     - Tại mỗi điểm $\alpha$, tạo biến kết quả tịnh tiến $Y^*(\alpha) = Y - \alpha D$.
     - Chạy hồi quy phân vị có trọng số của $Y^*(\alpha)$ trên $[1, X, Z]$:
       $$\min_{\beta, \gamma} \sum_{i=1}^n \rho_\tau \left( Y_i^*(\alpha) - \beta_0 - X_i \beta - \gamma Z_i \right)$$
       với hàm mất mát $\rho_\tau(u) = u (\tau - \mathbb{I}(u < 0))$.
     - Dưới tham số nhân quả thực $\alpha^*(\tau)$, biến công cụ ngoại sinh $Z$ không được phép có năng lực dự báo thặng dư $Y^* - X \beta$ (tức là $\gamma(\alpha^*) = 0$).
     - Ước lượng điểm: $\hat{\alpha}(\tau) = \arg\min_{\alpha} W_n(\alpha)$ với thống kê Wald $W_n(\alpha) = \frac{\hat{\gamma}(\alpha)^2}{\text{Var}(\hat{\gamma}(\alpha))}$.
  3. **Khoảng Tin Cậy Đảo Ngược Chernozhukov-Hansen (Dual-Inversion Confidence Intervals):**
     Không phụ thuộc vào tiệm cận của vi phân bậc hai, khoảng tin cậy 95% là tập hợp tất cả các giá trị $\alpha$ thỏa mãn điều kiện chấp nhận giả thuyết $H_0: \gamma(\alpha) = 0$:
     $$\text{CI}_{1-\eta}(\tau) = \{ \alpha : W_n(\alpha) \le \chi^2_{1, 1-\eta} \} \quad (\chi^2_{1, 0.95} = 3.841)$$
     Khoảng tin cậy này có tính chất vững đối với biến công cụ yếu (Weak-instrument robust).
  4. **Kiểm định Cấu trúc Phân hóa Phân vị (Quantile Treatment Heterogeneity Test):**
     Đo lường độ choãi hiệu ứng giữa tầng phân vị cao và tầng phân vị thấp: $\hat{\Delta}_{90-10} = \hat{\alpha}(0.90) - \hat{\alpha}(0.10)$. Nếu $|\hat{\Delta}_{90-10}|$ lớn, xác nhận chính sách có hiệu lực bất đối xứng.
  5. **Đo lường Khoảng cách Sai lệch Nội sinh (Endogeneity Bias Gap):**
     Lượng hóa độ chênh lệch $\Delta(\tau) = \hat{\alpha}_{\text{QR}}(\tau) - \hat{\alpha}_{\text{IV-QR}}(\tau)$ cho từng phân vị để chỉ ra mức độ thổi phồng hoặc hạ thấp hiệu ứng khi không dùng biến công cụ.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/iv-quantile-regression`
- **Request Body (`IVQuantileRegressionRequest`):**
  - `outcome_question_id`: UUID của câu hỏi kết quả $Y$.
  - `treatment_question_id`: UUID của câu hỏi can thiệp nội sinh $D$.
  - `instrument_question_id`: UUID của câu hỏi biến công cụ ngoại sinh $Z$.
  - `covariate_question_ids`: Danh sách UUID các biến kiểm soát ngoại sinh $X_k$ (tùy chọn).
  - `quantiles`: Danh sách phân vị cần đánh giá (mặc định: `[0.10, 0.25, 0.50, 0.75, 0.90]`).
  - `grid_points`: Số điểm chia lưới tìm kiếm $\alpha$ (mặc định: `80`).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`IVQuantileRegressionOut`):**
  - `status`: `"success"` hoặc `"error"`.
  - `summary`: Cỡ mẫu $N$, đánh giá độ mạnh biến công cụ (F-stat tầng 1, cảnh báo biến yếu nếu $F < 10$), hệ số OLS ngây thơ, hệ số 2SLS LATE trung bình, độ lệch phân vị $\Delta_{90-10}$, cờ dị biệt hóa phân vị, và giá trị tới hạn $\chi^2(1) = 3.841$.
  - `quantile_estimates`: Danh sách kết quả theo từng phân vị $\tau$:
    - `quantile`: Mức phân vị $\tau$.
    - `iv_qr_estimate`: Hiệu ứng nhân quả IV-QR $\hat{\alpha}(\tau)$.
    - `ci_lower` & `ci_upper`: Khoảng tin cậy đảo ngược 95% CI.
    - `is_significant`: Trạng thái có ý nghĩa thống kê ($0 \notin \text{CI}$).
    - `exogenous_qr_estimate` & `exogenous_qr_se`: Ước lượng QR ngây thơ để đối chiếu.
    - `endogeneity_bias_gap`: Khoảng cách sai lệch nội sinh $\Delta$.
    - `min_wald_stat`: Giá trị cực tiểu của thống kê Wald $W_n$.
  - `svg_chart`: Biểu đồ vector SVG kép:
    - Panel A: Đồ thị Quỹ đạo Tác động Phân vị (IV-QR Trajectory Curve) với dải băng tin cậy đảo ngược 95% CI đối chiếu đường 2SLS LATE và đường OLS.
    - Panel B: Đường cong Hàm Mục tiêu Wald $W_n(\alpha)$ tại trung vị $(\tau = 0.50)$ kèm vạch cắt $\chi^2(1) = 3.841$ và điểm cực tiểu $\alpha^*$.
  - `apa_narrative`: Đoạn thuyết minh học thuật định dạng chuẩn APA 7th Edition theo Chernozhukov & Hansen (2005, 2008).
- **Niêm phong kiểm toán:** Tự động ghi nhận `IV_QUANTILE_REGRESSION_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 88. Choice-Based Conjoint (CBC) Analysis with Hierarchical Bayes (HB) Engine

- **Mục tiêu khoa học:** Mô hình hóa các quyết định đánh đổi đa thuộc tính (Multi-attribute trade-off choice decisions) và ước lượng phân phối tiện ích từng phần ở cấp độ cá thể người tham gia khảo sát (Individual-level random coefficient part-worth utilities $\beta_i$) thông qua thuật toán MCMC Bayes Phân tầng (Hierarchical Bayes MCMC; **Rossi, Allenby & McCulloch 2005**; **Allenby & Rossi 1998**; **McFadden 1974**; **Green & Srinivasan 1990**).
- **Cơ sở phương pháp luận:**
  1. **Hạn chế của Mô hình Hồi quy Conjoint Cổ điển (Aggregate MNL / OLS):**
     - Mô hình Multinomial Logit tổng gộp giả định toàn bộ người trả lời có cùng một hàm sở thích (Homogeneous preferences), vi phạm tiên đề độc lập của các phương án không liên quan (IIA - Independence of Irrelevant Alternatives; Luce 1959, McFadden 1974).
     - Trong thực tế khảo sát thị trường và chính sách công, sở thích người tiêu dùng/công dân luôn có sự dị biệt hóa mạnh mẽ (Preference heterogeneity).
  2. **Cấu trúc Mô hình Hai Tầng Bayes Phân tầng (Two-Level Hierarchical Bayes):**
     - **Tầng trên (Upper-Level Model - Dân số):**
       $$\beta_i \sim \mathcal{N}(\mu, \Sigma)$$
       - $\mu \in \mathbb{R}^K$: Vector tiện ích trung bình của toàn thể dân số.
       - $\Sigma \in \mathbb{R}^{K \times K}$: Ma trận hiệp phương sai đo lường mức độ biến thiên sở thích cá thể và tương quan chéo giữa các thuộc tính.
       - Tiên nghiệm liên hợp (Conjugate Priors): $\mu \sim \mathcal{N}(0, 10 I)$, $\Sigma^{-1} \sim \text{Wishart}(K + 2, I)$.
     - **Tầng dưới (Lower-Level Model - Lựa chọn Cá thể):**
       Dưới Lý thuyết Tiện ích Ngẫu nhiên (Random Utility Model - RUM), xác suất cá nhân $i$ chọn hồ sơ $j$ trong tập nhiệm vụ $t$ tuân theo phân phối Multinomial Logit:
       $$P(y_{it} = j) = \frac{\exp(X_{jt} \beta_i)}{\sum_{k=1}^{J_t} \exp(X_{kt} \beta_i)}$$
  3. **Thuật toán Lấy mẫu MCMC Hỗn hợp (Hybrid Gibbs / Metropolis-Hastings):**
     - Bước 1: Cập nhật từng vector hệ số cá nhân $\beta_i$ bằng bước bước nhảy ngẫu nhiên Metropolis-Hastings (Random-Walk MH) với độ lệch chuẩn đề xuất thích ứng $\sigma_{\text{prop}}$ duy trì tỷ lệ chấp nhận tối ưu ~25-35%.
     - Bước 2: Cập nhật kỳ vọng dân số $\mu | \{\beta_i\}, \Sigma \sim \mathcal{N}\left(\bar{\beta}, \frac{1}{N}\Sigma\right)$ qua phân phối chuẩn liên hợp Gibbs.
     - Bước 3: Cập nhật ma trận hiệp phương sai $\Sigma | \{\beta_i\}, \mu \sim \text{Inv-Wishart}\left(N + \nu_0, S_0 + \sum_i (\beta_i - \mu)(\beta_i - \mu)'\right)$ qua phân phối Inverse-Wishart liên hợp Gibbs.
     - Trích xuất trung bình hậu nghiệm $\hat{\mu}$, $\hat{\beta}_i$ và khoảng tin cậy Bayes 95% (95% Bayesian Credible Intervals - BCI) từ các lượt rút sau giai đoạn burn-in.
  4. **Chuẩn hóa Mã hóa Hiệu ứng (Effects Coding Zero-Centered Contrasts):**
     Với mỗi thuộc tính có $L_a$ mức độ, mức cơ sở thứ $L_a$ được tính bằng:
     $$\beta_{a, L_a} = - \sum_{l=1}^{L_a - 1} \beta_{a, l} \implies \sum_{l=1}^{L_a} \beta_{a, l} = 0$$
     Đảm bảo mức tiện ích trung bình của từng thuộc tính luôn bằng 0, giúp việc so sánh trực quan và chuẩn hóa hoàn toàn giữa các thuộc tính.
  5. **Độ Quan Trọng Tương Đối của Thuộc Tính (Attribute Relative Importance %):**
     - Tại cấp độ từng cá nhân $i$, độ biến thiên phạm vi tiện ích của thuộc tính $a$:
       $$R_{i, a} = \max_l \beta_{i, a, l} - \min_l \beta_{i, a, l}$$
     - Tỷ trọng quan trọng: $I_{i, a} = \frac{R_{i, a}}{\sum_{a'} R_{i, a'}} \times 100\%$.
     - Tính trung bình dân số $\bar{I}_a$ và độ lệch chuẩn $\text{SD}(I_a)$ phản ánh mức độ nhất trí của mẫu khảo sát.
  6. **Định Giá Sẵn Sàng Chi Trả (Willingness to Pay - WTP):**
     - Nếu một thuộc tính là giá (với các mức số học), hệ số nhạy cảm giá $\alpha_{\text{price}} = \frac{\Delta \text{Utility}}{\Delta \text{Price}} < 0$.
     - Mức thặng dư sẵn sàng chi trả cho mức thuộc tính $l$ so với mức tham chiếu cơ sở:
       $$\text{WTP}(a, l) = - \frac{\beta_{a, l} - \beta_{a, \text{base}}}{\alpha_{\text{price}}}$$
  7. **Mô Phỏng Thị Phần Lựa Chọn Cạnh Tranh (Choice Share Market Simulator):**
     Cho tập hợp $M$ cấu hình sản phẩm giả định $C = \{c_1, \dots, c_M\}$, mô phỏng xác suất thị phần theo quy tắc Logit Share of Preference:
     $$\text{Share}_m = \frac{100\%}{N} \sum_{i=1}^N \frac{\exp(X_{c_m} \beta_i)}{\sum_{m'=1}^M \exp(X_{c_{m'}} \beta_i)}$$
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/conjoint-hb`
- **Request Body (`ConjointHBAnalysisRequest`):**
  - `attributes_config`: Bản đồ ánh xạ tên thuộc tính -> danh sách các mức độ (e.g. `{"Thương hiệu": ["A", "B"], "Giá": ["100", "200"]}`).
  - `tasks_data`: Danh sách các lựa chọn/đánh giá hồ sơ đã thu thập (tùy chọn; nếu để trống hệ thống sẽ tự động ghép nối từ các câu hỏi khảo sát).
  - `price_attribute`: Tên thuộc tính giá để tính WTP (tùy chọn).
  - `simulation_scenarios`: Danh sách các hồ sơ giả định để mô phỏng thị phần (tùy chọn).
  - `n_draws`: Tổng số lượt rút chuỗi MCMC (mặc định: `500`).
  - `burn_in`: Số lượt rút loại bỏ ban đầu (mặc định: `150`).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`ConjointHBAnalysisOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"CHOICE_BASED_CONJOINT_HIERARCHICAL_BAYES"`.
  - `diagnostics`: Cỡ mẫu cá thể $N$, tổng số quan sát $T$, tỷ lệ dự đoán đúng lựa chọn (Hit Rate %), hệ số giả $R^2$ McFadden, tỷ lệ chấp nhận chuỗi MCMC %, Log-Likelihood, RMSE.
  - `attribute_importance`: Danh sách xếp hạng tỷ trọng thuộc tính (%, SD %).
  - `part_worth_utilities`: Chi tiết tiện ích từng phần $\hat{\mu}$, dải tin cậy 95% BCI $[L, U]$, cờ tham chiếu zero-sum cho toàn bộ các mức độ.
  - `willingness_to_pay`: Hệ số biên của giá $\alpha_{\text{price}}$, dải giá và bảng ước lượng WTP bằng tiền tệ cho từng thuộc tính.
  - `market_simulations`: Bảng phân bổ thị phần lựa chọn (%) dự đoán cho từng cấu hình kịch bản đối đầu.
  - `svg_visualization`: Biểu đồ vector SVG kép (Panel A: Thanh ngang tỷ trọng thuộc tính; Panel B: Phổ tiện ích từng phần kèm thanh sai số tin cậy 95% BCI).
  - `apa_narrative`: Thuyết minh học thuật hoàn chỉnh chuẩn APA 7th Edition theo Rossi et al. (2005) và McFadden (1974).
- **Niêm phong kiểm toán:** Tự động ghi nhận `CONJOINT_HB_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 89. Fractional Response Regression (QMLE) Engine

- **Mục tiêu khoa học:** Mô hình hóa biến kết quả khảo sát là các tỷ lệ, phần trăm, chỉ số bị chặn nghiêm ngặt trong khoảng đơn vị $y \in [0, 1]$ (hoặc $0\% - 100\%$) có chứa các điểm khối xác suất cực trị tại biên 0 và 1 (boundary mass points), thông qua phương pháp Chuẩn Cực đại Hợp lý Bernoulli (Bernoulli Quasi-Maximum Likelihood Estimation - QMLE; **Papke & Wooldridge 1996, 2008**; **Gourieroux, Monfort & Trognon 1984**; **Wooldridge 2010**).
- **Cơ sở phương pháp luận:**
  1. **Hạn chế Nghiêm Trọng của OLS và Biến đổi Log-Odds Cổ điển:**
     - Mô hình OLS tuyến tính giả định hiệu ứng biên không đổi và không có cơ chế chặn biên, dẫn đến các giá trị dự báo phi thực tế ($\hat{y} < 0$ hoặc $\hat{y} > 1$), đồng thời vi phạm giả định phương sai không đổi do $\text{Var}(y|X)$ buộc phải triệt tiêu về 0 khi $E[y|X] \to 0$ hoặc $1$.
     - Biến đổi Log-Odds $\ln(y / (1 - y))$ hoàn toàn không xác định khi $y = 0$ hoặc $y = 1$. Việc cộng một hằng số nhỏ tùy tiện $\epsilon$ tạo ra độ lệch ước lượng không kiểm soát được.
     - Mô hình Tobit/Censoring không phù hợp vì biến tỷ lệ không phải là biến tiềm ẩn bị cắt cụt do quan sát; giá trị 0 và 1 là các lựa chọn thực tế hoàn toàn hợp lệ.
  2. **Cơ chế Kỳ vọng Có Điều kiện và Bernoulli QMLE:**
     Mô hình hóa hàm kỳ vọng có điều kiện:
     $$E[y_i | X_i] = G(X_i \beta)$$
     với hàm liên kết $G(\cdot)$ là hàm phân phối tích lũy:
     - **Fractional Logit:** $G(z) = \frac{1}{1 + \exp(-z)}$
     - **Fractional Probit:** $G(z) = \Phi(z)$
     - **Complementary Log-Log (cloglog):** $G(z) = 1 - \exp(-\exp(z))$ (phù hợp khi phân phối tỷ lệ lệch bất đối xứng ở vùng cực trị).
     Tối đa hóa hàm Quasi-Log-Likelihood Bernoulli:
     $$\ln L(\beta) = \sum_{i=1}^N \left[ y_i \ln(G(X_i \beta)) + (1 - y_i) \ln(1 - G(X_i \beta)) \right]$$
     Định lý Gourieroux et al. (1984) và Papke & Wooldridge (1996) chứng minh rằng ước lượng $\hat{\beta}$ là **nhất quán và phân phối chuẩn tiệm cận** miễn là hàm kỳ vọng có điều kiện $E[y|X] = G(X\beta)$ được chỉ định đúng, bất kể phân phối thực của $y$ là liên tục, rời rạc hay hỗn hợp.
  3. **Ma trận Hiệp Phương Sai Sandwich Huber-White Vững:**
     $$\text{Var}(\hat{\beta}) = \mathbf{A}^{-1} \mathbf{B} \mathbf{A}^{-1}$$
     với ma trận Hessian thông tin $\mathbf{A} = \sum_{i=1}^N \frac{g(X_i \beta)^2}{G(X_i \beta)(1 - G(X_i \beta))} X_i X_i'$ và ma trận tích ngoài gradients $\mathbf{B} = \sum_{i=1}^N \frac{(y_i - G(X_i \beta))^2 g(X_i \beta)^2}{[G(X_i \beta)(1 - G(X_i \beta))]^2} X_i X_i'$. Đảm bảo sai số chuẩn và kiểm định $z$ hoàn toàn vững trước hiện tượng phương sai thay đổi (heteroscedasticity).
  4. **Hiệu Ứng Biên Trung Bình (Average Marginal Effects - AME):**
     Do mô hình là phi tuyến, hệ số $\beta_j$ không phản ánh trực tiếp sự thay đổi của $y$. Hệ thống tính toán chính xác:
     - Hiệu ứng Biên Trung bình (AME): $\text{AME}_j = \frac{1}{N} \sum_{i=1}^N g(X_i \hat{\beta}) \hat{\beta}_j$ kèm sai số chuẩn Delta-method.
     - Hiệu ứng Biên tại Giá trị Trung bình (MEM): $\text{MEM}_j = g(\bar{X} \hat{\beta}) \hat{\beta}_j$.
  5. **Chẩn Đoán Dạng Hàm Ramsey RESET & Kiểm Tra Vi Phạm OLS:**
     - Kiểm định Ramsey RESET cho mô hình Fractional Response kiểm tra xem các lũy thừa của giá trị dự báo $(\hat{G}^2, \hat{G}^3)$ có cải thiện Quasi-Likelihood hay không ($p > 0.05$: dạng hàm phi tuyến được chỉ định hoàn hảo).
     - Định lượng trực tiếp số lượng quan sát mà OLS ngây thơ dự báo vượt ngoài khoảng $[0, 1]$, chứng minh tính ưu việt của Fractional QMLE.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/fractional-response`
- **Request Body (`FractionalResponseRequest`):**
  - `outcome_question_id`: UUID của câu hỏi kết quả tỷ lệ $Y \in [0, 1]$ hoặc phần trăm.
  - `covariate_question_ids`: Danh sách UUID các biến giải thích $X_k$.
  - `link`: `"logit"` (mặc định), `"probit"`, hoặc `"cloglog"`.
  - `scale_from_percentage`: `true` để tự động chia 100 nếu dữ liệu nằm trong thang $[0, 100]$.
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`FractionalResponseOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"FRACTIONAL_RESPONSE_QMLE"`.
  - `diagnostics`: Cỡ mẫu $N$, số lượng điểm mass point tại 0, số lượng điểm mass point tại 1, Quasi-Log-Likelihood, hệ số giả $R^2$ McFadden, số lượng vi phạm ngoài biên của OLS, thống kê và p-value kiểm định RESET.
  - `coefficients`: Bảng chi tiết từng biến: Hệ số $\hat{\beta}$, Robust SE, $z$-stat, $p$-value, khoảng tin cậy 95% CI, Hiệu ứng Biên Trung bình (AME) kèm AME SE, và Hiệu ứng Biên tại Trung bình (MEM).
  - `svg_visualization`: Biểu đồ vector SVG kép (Panel A: Đường phản hồi bão hòa phi tuyến $E[y|X]$ vs đường thẳng OLS vi phạm biên; Panel B: Forest plot các hiệu ứng biên AME kèm dải tin cậy 95% CI).
  - `apa_narrative`: Đoạn thuyết minh học thuật định dạng chuẩn APA 7th Edition theo Papke & Wooldridge (1996, 2008).
- **Niêm phong kiểm toán:** Tự động ghi nhận `FRACTIONAL_RESPONSE_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 90. Multidimensional Item Response Theory (MIRT) Engine

- **Mục tiêu khoa học:** Mô hình hóa các bài kiểm tra, thang đo khảo sát tâm lý học và hành vi đa chiều (Multidimensional latent traits $\boldsymbol{\theta}_i \in \mathbb{R}^D$) khi các câu hỏi khảo sát đồng thời đo lường nhiều chiều năng lực (e.g., Tư duy Phân tích, Khả năng Ngôn ngữ, Nhận thức Không gian) thông qua mô hình bù trừ M2PL (Compensatory Multidimensional 2PL; **Reckase 2009**; **Reckase & McKinley 1991**; **Bock & Aitkin 1981**; **Samejima 1969**).
- **Cơ sở phương pháp luận:**
  1. **Khắc phục Giả định Đơn Chiều Vi phạm (Unidimensionality Failure):**
     - Các mô hình IRT đơn chiều (1PL, 2PL, 3PL, Rasch) đưa ra giả định ngặt nghèo rằng toàn bộ các mục hỏi chỉ đo lường duy nhất 1 nhân tố tiềm ẩn $\theta$. Khi dữ liệu khảo sát thực tế có cấu trúc đa chiều, thông số phân biệt $a_j$ bị thổi phồng nghiêm trọng và hàm thông tin kiểm tra TIF bị sai lệch.
     - Mô hình MIRT bù trừ M2PL mở rộng không gian năng lực lên $D$ chiều:
       $$P(Y_{ij} = 1 | \boldsymbol{\theta}_i) = \frac{\exp\left(\mathbf{a}_j' \boldsymbol{\theta}_i + d_j\right)}{1 + \exp\left(\mathbf{a}_j' \boldsymbol{\theta}_i + d_j\right)}$$
       với $\mathbf{a}_j = (a_{j1}, \dots, a_{jD})'$ là vector độ dốc phân biệt đa chiều và $d_j$ là hệ số chặn (intercept).
  2. **Chỉ Số Phân Biệt Đa Chiều (Multidimensional Discrimination Index - MDISC):**
     $$\text{MDISC}_j = \|\mathbf{a}_j\|_2 = \sqrt{\sum_{d=1}^D a_{jd}^2}$$
     Biểu thị năng lực phân biệt tối đa của câu hỏi $j$ trong không gian đa chiều $\boldsymbol{\theta}$. Phân loại theo thang Reckase: Rất Cao ($\ge 1.70$), Cao ($1.35 - 1.70$), Trung Bình ($0.65 - 1.35$), Thấp ($< 0.65$).
  3. **Góc Đo Lường Chỉ Hướng Tối Ưu (Direction of Best Measurement):**
     Vector góc chỉ hướng $\boldsymbol{\alpha}_j = (\alpha_{j1}, \dots, \alpha_{jD})$ trong không gian $\boldsymbol{\theta}$:
     $$\cos(\alpha_{jd}) = \frac{a_{jd}}{\text{MDISC}_j} \implies \alpha_{jd} = \arccos\left(\frac{a_{jd}}{\text{MDISC}_j}\right) \times \frac{180^\circ}{\pi}$$
     Chỉ ra hướng trực giao mà tại đó câu hỏi cung cấp thông tin kiểm tra cực đại.
  4. **Độ Khó Đa Chiều (Multidimensional Item Difficulty - MID):**
     $$\text{MID}_j = - \frac{d_j}{\text{MDISC}_j}$$
     Biểu thị khoảng cách Euclid từ gốc tọa độ không gian tiềm ẩn $(\mathbf{0})$ đến điểm có độ dốc cực đại của bề mặt phản hồi câu hỏi (Item Response Surface).
  5. **Thuật toán Ước lượng Hợp Lý Cực Đại Biên MMLE-EM:**
     Sử dụng thuật toán EM (Bock & Aitkin 1981) kết hợp lưới cầu phương đa chiều Gauss-Hermite $Q = K^D$.
     - Bước E: Tính kỳ vọng số lượng người trả lời $r_{jq}$ và tổng mật độ $N_q$ tại từng nút cầu phương dựa trên phân phối hậu nghiệm $P(\boldsymbol{\theta}_q | \mathbf{Y}_i)$.
     - Bước M: Tối ưu hóa hàm hợp lý có điều kiện cho từng mục hỏi bằng L-BFGS-B.
  6. **Ước Lượng Điểm Năng Lực Tiềm Ẩn Cá Nhân (EAP Trait Scoring):**
     $$\hat{\boldsymbol{\theta}}_i = \sum_{q=1}^Q \boldsymbol{\theta}_q P(\boldsymbol{\theta}_q | \mathbf{Y}_i)$$
     Đồng thời tính ma trận tương quan thực nghiệm giữa các chiều tiềm ẩn $r(\theta_{d1}, \theta_{d2})$.
  7. **Chẩn Đoán Độ Khớp Mục Hỏi (Item Fit S-χ² & RMSEA):**
     Ước lượng chỉ số Orlando-Thissen (2000) và Item RMSEA: giá trị $\text{RMSEA} < 0.08$ khẳng định mục hỏi hoàn toàn khớp với không gian tiềm ẩn đa chiều.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/mirt`
- **Request Body (`MIRTAnalysisRequest`):**
  - `item_question_ids`: Danh sách UUID các câu hỏi khảo sát cần phân tích (tối thiểu 3 câu hỏi).
  - `n_dimensions`: Số chiều tiềm ẩn $D$ (mặc định: `2`, hỗ trợ 2 hoặc 3 chiều).
  - `dimension_names`: Tên tùy chỉnh cho từng chiều năng lực (tùy chọn).
  - `max_em_iter`: Số vòng lặp tối đa của thuật toán EM (mặc định: `40`).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`MIRTAnalysisOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"MULTIDIMENSIONAL_IRT_2PL"`.
  - `diagnostics`: Cỡ mẫu $N$, số mục hỏi $J$, số chiều $D$, số lượt lặp EM, Log-Likelihood, AIC, BIC, điểm trung bình năng lực EAP và ma trận tương quan giữa các chiều.
  - `item_parameters`: Bảng chi tiết từng câu hỏi: Intercept $d_j$, Slopes $\mathbf{a}_j$, Chỉ số phân biệt đa chiều MDISC, Phân loại MDISC, Độ khó đa chiều MID, Góc chỉ hướng $\boldsymbol{\alpha}_j^\circ$, Item RMSEA và đánh giá độ khớp.
  - `svg_visualization`: Biểu đồ vector SVG kép:
    - Panel A: Không gian Vector Thuộc tính (Item Vector Plot) trong hệ tọa độ $\theta_1 - \theta_2$ với các mũi tên vector chỉ hướng và độ dài phản ánh MDISC.
    - Panel B: Biểu đồ thanh ngang phân bổ MDISC và MID kèm dải phân loại năng lực.
  - `apa_narrative`: Đoạn thuyết minh học thuật định dạng chuẩn APA 7th Edition theo Reckase (2009).
- **Niêm phong kiểm toán:** Tự động ghi nhận `MIRT_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 91. Heckman Two-Step Sample Selection Model Engine

- **Mục tiêu khoa học:** Khắc phục và khử triệt để sai lệch chọn mẫu phi ngẫu nhiên (Non-random sample selection bias), thiên lệch tự chọn lọc (Self-selection bias), và mất dấu quan sát trong khảo sát (Survey attrition / Non-response) đối với các biến kết quả chỉ quan sát được có điều kiện (e.g., mức thu nhập tự nguyện khai báo, sự hài lòng của nhóm tiếp tục tham gia khảo sát) dựa trên phương pháp hai bước kinh điển đạt giải Nobel Kinh tế năm 2000 (**Heckman 1979**; **Greene 1981**; **Wooldridge 2010**; **Bushway et al. 2007**).
- **Cơ sở phương pháp luận:**
  1. **Bản Chất Sai Lệch Chọn Mẫu (Sample Selection as a Specification Error):**
     - Xét phương trình kết quả: $Y_i = X_i \beta + \epsilon_i$, nhưng $Y_i$ chỉ được quan sát khi cá nhân quyết định tham gia/trả lời ($S_i = 1$).
     - Phương trình chọn lọc: $S_i^* = Z_i \gamma + u_i$, trong đó $S_i = 1$ khi $S_i^* > 0$.
     - Khi các yếu tố tiềm ẩn không quan sát được ảnh hưởng đồng thời đến việc tham gia và kết quả ($\text{Corr}(u_i, \epsilon_i) = \rho \ne 0$), ước lượng OLS thông thường trên mẫu quan sát ($S_i = 1$) sẽ bị chệch nghiêm trọng do:
       $$E[Y_i | X_i, S_i = 1] = X_i \beta + E[\epsilon_i | u_i > - Z_i \gamma] = X_i \beta + \rho \sigma_\epsilon \lambda_i(Z_i \gamma)$$
  2. **Tỷ Số Nghịch Đảo Mills (Inverse Mills Ratio - IMR $\lambda$):**
     - Tại Bước 1: Ước lượng mô hình Probit xác suất chọn mẫu trên toàn bộ mẫu khảo sát $N$ (bao gồm cả quan sát $S=1$ và $S=0$):
       $$P(S_i = 1 | Z_i) = \Phi(Z_i \gamma)$$
     - Tính toán tỷ số rủi ro chọn mẫu (hazard rate of selection):
       $$\lambda_i = \frac{\phi(Z_i \hat{\gamma})}{\Phi(Z_i \hat{\gamma})}$$
       với $\phi(\cdot)$ là hàm mật độ xác suất chuẩn và $\Phi(\cdot)$ là hàm phân phối tích lũy chuẩn tắc.
  3. **Hồi Quy Mở Rộng Bước 2 & Khử Thiên Lệch:**
     - Trên mẫu quan sát được ($N_1$), hồi quy OLS phương trình bổ sung:
       $$Y_i = X_i \beta + \beta_\lambda \lambda_i + \nu_i$$
       trong đó hệ số của nghịch đảo Mills là $\beta_\lambda = \rho \sigma_\epsilon$.
  4. **Hiệu Chỉnh Ma Trận Hiệp Phương Sai Asymptotic Heckman-Greene:**
     - Sai số chuẩn OLS thông thường ở Bước 2 không hợp lệ vì $\lambda_i$ là biến ước lượng và phần dư $\nu_i$ bị phương sai thay đổi điều kiện: $\text{Var}(\nu_i | Z_i, S_i=1) = \sigma_\epsilon^2 (1 - \rho^2 \delta_i)$ với $\delta_i = \lambda_i(\lambda_i + Z_i \hat{\gamma})$.
     - Hệ thống áp dụng hiệu chỉnh ma trận Greene (1981):
       $$\mathbf{V}_{\text{Greene}} = \hat{\sigma}_\epsilon^2 (\mathbf{X}_*'\mathbf{X}_*)^{-1} \left[ \mathbf{X}_*' (\mathbf{I} - \hat{\rho}^2 \boldsymbol{\Delta}) \mathbf{X}_* \right] (\mathbf{X}_*'\mathbf{X}_*)^{-1}$$
  5. **Kiểm Định Chẩn Đoán Thiên Lệch Chọn Mẫu (Selection Bias Test):**
     - Kiểm định giả thuyết vô hiệu $H_0: \beta_\lambda = 0$ (hoặc $\rho = 0$) thông qua thống kê kiểm định $t = \hat{\beta}_\lambda / \text{SE}(\hat{\beta}_\lambda)$.
     - Nếu $p < 0.05$: Khẳng định sự tồn tại của sai lệch chọn mẫu có ý nghĩa thống kê; Naive OLS bị chệch và việc áp dụng hiệu chỉnh Heckman là bắt buộc.
     - Lượng hóa Khoảng cách Sai lệch Chọn mẫu (Selection Bias Gap) cho từng biến: $\Delta_j = \hat{\beta}_{j, \text{OLS}} - \hat{\beta}_{j, \text{Heckman}}$.
  6. **Ràng Buộc Loại Trừ (Exclusion Restriction Requirement):**
     - Kiểm tra sự hiện diện của biến công cụ $Z_{\text{excl}}$ (ảnh hưởng đến quyết định tham gia nhưng không tác động trực tiếp đến kết quả $Y$) để tránh hiện tượng đa cộng tuyến giữa $\lambda$ và $X$.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/heckman-selection`
- **Request Body (`HeckmanSelectionRequest`):**
  - `outcome_question_id`: UUID của câu hỏi kết quả $Y$ (bị khuyết hoặc quan sát có điều kiện).
  - `selection_indicator_question_id`: UUID của câu hỏi chỉ báo tham gia $S \in \{0, 1\}$ (tùy chọn; nếu không cung cấp, hệ thống tự động suy diễn theo trạng thái trả lời của $Y$).
  - `outcome_covariate_question_ids`: Danh sách UUID các biến giải thích $X$ trong phương trình kết quả.
  - `exclusion_restriction_question_ids`: Danh sách UUID các biến công cụ ngoại sinh $Z_{\text{excl}}$ chỉ xuất hiện trong phương trình chọn lọc (tùy chọn).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`HeckmanSelectionOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"HECKMAN_TWO_STEP_SELECTION"`.
  - `diagnostics`: Tổng mẫu $N$, số quan sát được chọn $N_1$, số quan sát bị kiểm duyệt $N_0$, tỷ lệ chọn %, hệ số IMR $\beta_\lambda$, sai số chuẩn, thống kê $t$, $p$-value kiểm định sai lệch, hệ số tương quan $\rho$, độ lệch chuẩn sai số $\sigma_\epsilon$, và cờ cảnh báo chọn mẫu.
  - `coefficients_comparison`: Bảng đối chiếu song song giữa Naive OLS và Heckman đã hiệu chỉnh: Hệ số OLS, Sai số OLS, Hệ số Heckman, Sai số chuẩn vững Greene, $z$-stat, $p$-value, khoảng tin cậy 95% CI và khoảng lệch thiên lệch $\Delta$.
  - `svg_visualization`: Biểu đồ vector SVG kép (Panel A: Đường cong tỷ số nghịch đảo Mills $\lambda(p)$ kèm mật độ phân bổ rug plot; Panel B: Forest plot đối chiếu Naive OLS vs Heckman kèm dải tin cậy 95% CI).
  - `apa_narrative`: Đoạn thuyết minh học thuật định dạng chuẩn APA 7th Edition theo Heckman (1979) và Greene (1981).
- **Niêm phong kiểm toán:** Tự động ghi nhận `HECKMAN_SELECTION_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 92. Stochastic Frontier Analysis (SFA) & Technical Efficiency Engine

- **Mục tiêu khoa học:** Đánh giá và đo lường độ hiệu quả kỹ thuật (Technical Efficiency - TE) của các đơn vị quan sát (doanh nghiệp, trường học, bệnh viện, trang trại, hoặc cá nhân trong khảo sát) so với biên sản xuất tối đa lý thuyết (Production Frontier) bằng phương pháp biên ngẫu nhiên dựa trên lý thuyết kinh tế lượng vi mô sản xuất (**Aigner, Lovell & Schmidt 1977**; **Meeusen & van Den Broeck 1977**; **Jondrow, Lovell, Materov & Schmidt - JLMS 1982**; **Kumbhakar & Lovell 2000**; **Greene 2008**).
- **Cơ sở phương pháp luận:**
  1. **Cấu Trúc Sai Số Hỗn Hợp (Composed Error Structure):**
     - Mô hình biên sản xuất chuẩn tắc:
       $$\ln Y_i = \beta_0 + \sum_{k=1}^K \beta_k \ln X_{ik} + \epsilon_i$$
     - Sai số $\epsilon_i$ được phân rã thành hai thành phần độc lập:
       $$\epsilon_i = v_i - u_i$$
       - $v_i \sim \mathcal{N}(0, \sigma_v^2)$: Nhiễu ngẫu nhiên thuần túy hai chiều (thời tiết, biến động vĩ mô, sai số đo lường khảo sát).
       - $u_i \sim \text{Half-Normal}(0, \sigma_u^2)$ với $u_i \ge 0$: Độ kém hiệu quả kỹ thuật phi âm (technical inefficiency), kéo sản lượng thực tế nằm dưới đường biên tối ưu.
  2. **Ước Lượng Hợp Lý Cực Đại (Maximum Likelihood Estimation - MLE):**
     - Tham số hóa theo Battese & Corra (1977): $\sigma^2 = \sigma_u^2 + \sigma_v^2$ và $\lambda = \sigma_u / \sigma_v$.
     - Hàm mật độ xác suất biên của sai số hỗn hợp $\epsilon$:
       $$f(\epsilon) = \frac{2}{\sigma} \phi\left(\frac{\epsilon}{\sigma}\right) \Phi\left(-\frac{\lambda \epsilon}{\sigma}\right)$$
     - Log-Likelihood cực đại hóa theo thuật toán L-BFGS-B:
       $$\ln L(\boldsymbol{\beta}, \sigma, \lambda) = \frac{N}{2} \ln\left(\frac{2}{\pi}\right) - N \ln \sigma + \sum_{i=1}^N \ln \Phi\left(-\frac{\lambda \epsilon_i}{\sigma}\right) - \frac{1}{2\sigma^2} \sum_{i=1}^N \epsilon_i^2$$
     - Tỷ lệ phương sai do kém hiệu quả: $\gamma = \sigma_u^2 / \sigma^2 \in [0, 1]$.
  3. **Ước Lượng Điểm Kém Hiệu Quả Cá Thể JLMS (1982):**
     - Phân phối điều kiện của $u_i$ khi đã biết phần dư $\epsilon_i$:
       $$u_i | \epsilon_i \sim \mathcal{N}^+(\mu_{*i}, \sigma_*^2)$$
       với $\mu_{*i} = -\epsilon_i \sigma_u^2 / \sigma^2$ và $\sigma_*^2 = \sigma_u^2 \sigma_v^2 / \sigma^2$.
     - Kỳ vọng điều kiện (JLMS point estimator):
       $$\hat{u}_i = E[u_i | \epsilon_i] = \mu_{*i} + \sigma_* \left[ \frac{\phi(\mu_{*i}/\sigma_*)}{\Phi(\mu_{*i}/\sigma_*)} \right]$$
     - Điểm Hiệu Quả Kỹ Thuật (Technical Efficiency score):
       $$\text{TE}_i = \exp(-\hat{u}_i) \in (0, 100\%]$$
       (Đơn vị đạt $\text{TE} = 100\%$ là đơn vị hoàn toàn tối ưu công nghệ nằm ngay trên đường biên).
  4. **Kiểm Định Thống Kê & Chẩn Đoán:**
     - **Kiểm định tỷ số hợp lý (Likelihood Ratio Test) về sự hiện diện của kém hiệu quả kỹ thuật:**
       $H_0: \lambda = 0$ (hoặc $\sigma_u = 0$, mô hình rút về OLS thuần túy) vs $H_1: \lambda > 0$. Thống kê $\text{LR} = 2 (\ln L_{\text{SFA}} - \ln L_{\text{OLS}})$. Phân phối tiệm cận dưới giả thuyết vô hiệu là phân phối hỗn hợp $\frac{1}{2}\chi^2_0 + \frac{1}{2}\chi^2_1$ (Kodde & Palm 1986).
     - **Kiểm định độ lệch phần dư OLS (Waldman 1982 Skewness Test):** Phần dư OLS phải có độ lệch âm (negative skewness $m_3 < 0$) thì mô hình biên sản xuất $(v - u)$ mới có ý nghĩa kinh tế lượng.
     - **Quy mô sản xuất (Returns to Scale - RTS):** Tổng các hệ số co giãn $\text{RTS} = \sum_{k=1}^K \beta_k$. Phân loại thành Tăng theo quy mô ($\text{IRS} > 1.02$), Quy mô không đổi ($\text{CRS} \in [0.98, 1.02]$), hoặc Giảm theo quy mô ($\text{DRS} < 0.98$).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/stochastic-frontier`
- **Request Body (`StochasticFrontierRequest`):**
  - `output_question_id`: UUID của câu hỏi sản lượng / doanh thu / điểm số đầu ra $Y$.
  - `input_question_ids`: Danh sách UUID các câu hỏi nguồn lực đầu vào $X_k$ (vốn, lao động, nguyên vật liệu...).
  - `log_transform`: `true` cho dạng hàm Cobb-Douglas log-log $\ln Y = \beta_0 + \sum \beta_k \ln X_k$, hoặc `false` cho hàm tuyến tính.
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`StochasticFrontierOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"STOCHASTIC_FRONTIER_ANALYSIS"`.
  - `diagnostics`: Cỡ mẫu $N$, số biến đầu vào $K$, hội tụ MLE, SFA LL, OLS LL, thống kê kiểm định LR, $p$-value kiểm định kém hiệu quả, $\sigma_{\text{total}}$, $\sigma_u$, $\sigma_v$, tỷ số $\lambda$, tỷ trọng phương sai $\gamma$, độ lệch phần dư OLS, tổng co giãn quy mô RTS, phán quyết RTS, hiệu quả kỹ thuật trung bình %, trung vị %, min %, max %, độ lệch chuẩn %.
  - `coefficients`: Danh sách hệ số biên sản xuất $\beta_k$, độ co giãn elasticity, sai số chuẩn Hessian vững, thống kê $t$, $p$-value, khoảng tin cậy 95% CI.
  - `inefficiency_summary`: Tóm tắt phân bổ tứ phân vị của điểm hiệu quả kỹ thuật (Q25, Median, Q75).
  - `individual_efficiency_sample`: Mẫu điểm hiệu quả kỹ thuật từng cá thể: số thứ tự quan sát, độ kém hiệu quả $\hat{u}_i$, điểm hiệu quả kỹ thuật $\text{TE}_i\%$.
  - `svg_visualization`: Biểu đồ SVG trực quan hóa kép:
    - Panel A: Đường cong biên sản xuất tối ưu (Stochastic Frontier Curve) so sánh với đám mây điểm quan sát và đường hồi quy OLS.
    - Panel B: Biểu đồ cột phân bố tần suất điểm hiệu quả kỹ thuật JLMS $\text{TE}_i$ kèm đường đánh dấu trung vị.
  - `apa_narrative`: Đoạn thuyết minh học thuật định dạng chuẩn APA 7th Edition theo Aigner et al. (1977) và JLMS (1982).
- **Niêm phong kiểm toán:** Tự động ghi nhận `STOCHASTIC_FRONTIER_ANALYSIS_EXECUTED` vào chuỗi sổ cái SHA-256.


---

## 93. Zero-Inflated Count Regression Models (ZIP & ZINB) Engine

- **Mục tiêu khoa học:** Mô hình hóa các biến số đếm khảo sát (e.g., số lần đi khám bác sĩ, số khiếu nại dịch vụ khách hàng, số ngày nghỉ việc, số sự cố hỏng hóc thiết bị, số lần bị quấy rối) có hiện tượng tích tụ điểm 0 vượt mức (Excess Zeros) vượt quá khả năng dung nạp của các phân phối Poisson hoặc Âm nhị thức tiêu chuẩn (**Lambert 1992**; **Greene 1994**; **Vuong 1989**; **Long 1997**).
- **Cơ sở phương pháp luận:**
  1. **Cơ Chế Hỗn Hợp Hữu Hạn Hai Trạng Thái (Finite Mixture Model):**
     - **Trạng thái Đột biến Không (Structural Zero):** Một bộ phận cá thể có xác suất bằng 0 tuyệt đối và không tham gia vào quá trình đếm (e.g., người không có bảo hiểm y tế không bao giờ đến bệnh viện tư nhân). Xác suất $p_i$ được mô hình hóa qua hàm liên kết Logit:
       $$p_i = \frac{1}{1 + \exp(-\mathbf{Z}_i \boldsymbol{\gamma})}$$
     - **Trạng thái Phân phối Đếm (Count Distribution):** Với xác suất $(1 - p_i)$, cá thể tham gia vào quá trình đếm có kỳ vọng $\mu_i = \exp(\mathbf{X}_i \boldsymbol{\beta})$.
  2. **Hàm Mật Độ Hỗn Hợp:**
     - Khi $Y_i = 0$: Xác suất quan sát điểm 0 là tổng hợp của hai nguồn:
       $$P(Y_i = 0) = p_i + (1 - p_i) P_{\text{count}}(0 | \mu_i)$$
     - Khi $Y_i = y_i > 0$: Điểm số đếm dương chỉ xuất phát từ trạng thái đếm:
       $$P(Y_i = y_i) = (1 - p_i) P_{\text{count}}(y_i | \mu_i)$$
  3. **Hai Phân Phối Đếm Hỗ Trợ:**
     - **Zero-Inflated Poisson (ZIP; Lambert 1992):** $P_{\text{count}}(y | \mu) = \frac{\exp(-\mu) \mu^y}{y!}$.
     - **Zero-Inflated Negative Binomial (ZINB; Greene 1994):** Dung nạp hiện tượng phân tán quá mức (Overdispersion $\text{Var}(Y) > E[Y]$) thông qua tham số phân tán $\alpha = 1/r$:
       $$P_{\text{count}}(y | \mu, \alpha) = \frac{\Gamma(y + 1/\alpha)}{\Gamma(y + 1)\Gamma(1/\alpha)} \left(\frac{1/\alpha}{1/\alpha + \mu}\right)^{1/\alpha} \left(\frac{\mu}{1/\alpha + \mu}\right)^y$$
  4. **Kiểm Định Phi Lồng Ghép Vuong (Vuong 1989 Non-Nested Test):**
     - Đặt $m_i = \ln f_{\text{ZI}}(Y_i) - \ln f_{\text{Standard}}(Y_i)$.
     - Thống kê kiểm định:
       $$V = \frac{\sqrt{N} \bar{m}}{s_m} \xrightarrow{d} \mathcal{N}(0, 1)$$
     - Phán quyết:
       - Nếu $V > +1.96$: Mô hình Zero-Inflated vượt trội vượt bậc có ý nghĩa thống kê ($p < 0.05$) so với mô hình đếm thông thường.
       - Nếu $V < -1.96$: Mô hình đếm thông thường đủ chuẩn.
       - Nếu $|V| \le 1.96$: Kiểm định không phân định dứt khoát.
  5. **Hệ Số Tỷ Lệ Tần Suất Biến Cố (Incidence Rate Ratio - IRR):**
     - Đối với phương trình đếm: $\text{IRR}_j = \exp(\beta_j)$ biểu thị tỷ lệ gia tăng số lần biến cố khi biến độc lập $X_j$ tăng 1 đơn vị.
     - Đối với phương trình đột biến không: $\text{OR}_j = \exp(\gamma_j)$ biểu thị tỷ số tỷ lệ cược (Odds Ratio) thuộc nhóm luôn bằng 0.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/zero-inflated`
- **Request Body (`ZeroInflatedRequest`):**
  - `count_question_id`: UUID của câu hỏi biến số đếm không âm $Y \ge 0$.
  - `covariate_question_ids`: Danh sách UUID các biến giải thích quá trình đếm $X$.
  - `inflation_covariate_question_ids`: Danh sách UUID các biến dự báo đột biến không $Z$ (tùy chọn, mặc định sử dụng $X$).
  - `model_type`: `"ZIP"` (Poisson) hoặc `"ZINB"` (Negative Binomial).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`ZeroInflatedOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"ZERO_INFLATED_ZIP"` hoặc `"ZERO_INFLATED_ZINB"`.
  - `diagnostics`: Cỡ mẫu $N$, số lượng và tỷ lệ % điểm 0, trung bình và phương sai mẫu, tỷ số phân tán $\text{Var}/M$, hội tụ MLE, Log-Likelihood ZI vs Poisson chuẩn, AIC/BIC, thống kê kiểm định Vuong $z$, $p$-value Vuong, phán quyết Vuong, tham số phân tán $\alpha$ (nếu ZINB).
  - `count_model_coefficients`: Bảng hệ số phương trình đếm: $\beta$, IRR, SE, $z$-stat, $p$-value, 95% CI của $\beta$, 95% CI của IRR.
  - `inflation_model_coefficients`: Bảng hệ số phương trình đột biến không: $\gamma$, Odds Ratio OR, SE, $z$-stat, $p$-value, 95% CI.
  - `frequency_distribution`: Bảng đối chiếu tần suất thực tế vs dự báo cho từng mức đếm $0, 1, 2, \dots$ kèm chênh lệch phần dư.
  - `svg_visualization`: Biểu đồ SVG kép:
    - Panel A: Biểu đồ cột so sánh phân bổ tần suất thực tế vs dự báo (đột biến tại điểm 0).
    - Panel B: Forest plot các hệ số hồi quy đếm $\beta$ kèm dải tin cậy 95% CI.
  - `apa_narrative`: Đoạn thuyết minh học thuật định dạng chuẩn APA 7th Edition theo Lambert (1992) và Vuong (1989).
- **Niêm phong kiểm toán:** Tự động ghi nhận `ZERO_INFLATED_MODEL_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 94. Latent Moderated Structural Equations (LMS / QML) Engine

- **Mục tiêu khoa học:** Đánh giá và kiểm định tác động điều tiết phi tuyến giữa các biến tiềm ẩn liên tục (Latent Continuous Interaction: $\xi_1 \times \xi_2 \to \eta$) trong mô hình phương trình cấu trúc (SEM), khắc phục triệt để hiện tượng sai lệch suy giảm nghiêm trọng (Attenuation Bias) của kích thước hiệu ứng tương tác do sai số đo lường gây ra trong hồi quy điểm quan sát truyền thống (**Klein & Moosbrugger 2000**; **Klein & Muthén 2007**; **Marsh, Wen & Hau 2004**; **Muthén 2002**; **Aiken & West 1991**).
- **Cơ sở phương pháp luận:**
  1. **Khuyết Tật Nghiêm Trọng Của Hồi Quy Điểm Tổng Hợp Quan Sát (Attenuation Bias):**
     - Khi nhân hai điểm số quan sát có chứa sai số đo lường ($X_1 = \xi_1 + \delta_1$ và $X_2 = \xi_2 + \delta_2$), sai số của số hạng tích $X_1 X_2$ tăng theo cấp số nhân:
       $$\text{Rel}(X_1 X_2) \approx \text{Rel}(X_1) \cdot \text{Rel}(X_2)$$
     - Độ tin cậy của số hạng tương tác suy sụp xuống chỉ còn ~0.40 - 0.60, khiến hệ số tương tác quan sát bị suy giảm tới 50% - 70% so với bản chất thực tế, gây ra tỷ lệ lỗi loại II (Type II Error - bỏ sót tương tác thực tế) đặc biệt nghiêm trọng trong khoa học hành vi và kinh tế lượng.
  2. **Mô Hình LMS / QML (Latent Moderated Structural Equations):**
     - Phương trình đo lường cho các nhân tố tiềm ẩn:
       $$\mathbf{x}_1 = \boldsymbol{\Lambda}_{x1} \xi_1 + \boldsymbol{\delta}_1, \quad \mathbf{x}_2 = \boldsymbol{\Lambda}_{x2} \xi_2 + \boldsymbol{\delta}_2, \quad \mathbf{y} = \boldsymbol{\Lambda}_y \eta + \boldsymbol{\epsilon}$$
     - Phương trình cấu trúc tiềm ẩn có tương tác:
       $$\eta = \alpha_0 + \gamma_1 \xi_1 + \gamma_2 \xi_2 + \gamma_3 (\xi_1 \xi_2) + \zeta$$
       trong đó:
       - $\gamma_1$: Tác động chính của biến độc lập tiềm ẩn $\xi_1$.
       - $\gamma_2$: Tác động chính của biến điều tiết tiềm ẩn $\xi_2$.
       - $\gamma_3$: **Hệ số tương tác tiềm ẩn LMS**, hoàn toàn sạch bóng sai số đo lường!
       - $\zeta \sim \mathcal{N}(0, \psi)$: Phần dư cấu trúc.
  3. **Thuật Toán Chuẩn Hợp Lý Cực Đại QML (Quasi-Maximum Likelihood; Klein & Muthén 2007):**
     - Tối ưu hóa phân phối điều kiện của biến tiềm ẩn tích $(\xi_1 \xi_2)$ mà không cần tạo hàng loạt biến chỉ báo tích nhân tạo (product indicators), đảm bảo tính vững tiệm cận (asymptotic consistency) và tính hiệu quả tiệm cận.
     - Sai số chuẩn vững được tính toán qua ma trận thông tin Hessian số học đảo.
  4. **Phân Tích Độ Dốc Đơn Giản (Simple Slopes Probing; Aiken & West 1991):**
     - Đạo hàm riêng tác động biên của $\xi_1$ lên $\eta$:
       $$\frac{\partial \eta}{\partial \xi_1} = \gamma_1 + \gamma_3 \xi_2$$
     - Ước lượng độ dốc điều kiện và kiểm định ý nghĩa thống kê $t$/$z$ tại ba mốc chuẩn hóa của biến điều tiết $\xi_2$:
       - Mức thấp (Low Moderator): $\xi_2 = -1\text{SD}$ ($-1.0$).
       - Mức trung bình (Mean Moderator): $\xi_2 = 0\text{SD}$ ($0.0$).
       - Mức cao (High Moderator): $\xi_2 = +1\text{SD}$ ($+1.0$).
  5. **Ngưỡng Ý Nghĩa Johnson-Neyman (Johnson-Neyman Cutoffs):**
     - Giải phương trình bậc hai xác định chính xác các giá trị ngưỡng của $\xi_2$ mà tại đó tác động của $\xi_1$ chuyển giao giữa có ý nghĩa thống kê ($p < 0.05$) và không có ý nghĩa thống kê.
  6. **Định Lượng Kích Thước Hiệu Ứng Cohen's $f^2$ & Khoảng Trống Attenuation:**
     - Cohen's $f^2 = \frac{\Delta R^2}{1 - R^2_{\text{LMS}}}$ (Nhỏ: $f^2 \ge 0.02$, Vừa: $f^2 \ge 0.15$, Lớn: $f^2 \ge 0.35$).
     - Định lượng phần trăm kích thước hiệu ứng được phục hồi: $\text{Attenuation Gap} = \frac{|\gamma_3 - \gamma_{\text{obs}}|}{|\gamma_3|} \times 100\%$.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/latent-moderation`
- **Request Body (`LatentModerationRequest`):**
  - `predictor_item_ids`: Danh sách UUID các câu hỏi chỉ báo nhân tố độc lập $\xi_1$.
  - `moderator_item_ids`: Danh sách UUID các câu hỏi chỉ báo nhân tố điều tiết $\xi_2$.
  - `outcome_item_ids`: Danh sách UUID các câu hỏi chỉ báo nhân tố kết quả $\eta$.
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`LatentModerationOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"LATENT_MODERATED_STRUCTURAL_EQUATIONS_LMS"`.
  - `diagnostics`: Cỡ mẫu $N$, hội tụ MLE, hệ số $R^2$ cấu trúc, Cohen's $f^2$, phân loại hiệu ứng, % phục hồi suy giảm Attenuation, hệ số tương tác Naive OLS $\gamma_{\text{obs}}$, hệ số tương tác tiềm ẩn $\gamma_3$, độ tin cậy Cronbach's $\alpha$ của $\xi_1, \xi_2, \eta$, tương quan tiềm ẩn $\text{Corr}(\xi_1, \xi_2)$, cờ ý nghĩa điều tiết, và các ngưỡng cắt Johnson-Neyman.
  - `coefficients`: Bảng chi tiết các tham số $\gamma_1, \gamma_2, \gamma_3$: Ước lượng, SE, $z$-stat, $p$-value, khoảng tin cậy 95% CI.
  - `simple_slopes`: Bảng phân tích độ dốc đơn giản tại $-1\text{SD}$, Mean, $+1\text{SD}$: Giá trị độ dốc, SE, $z$-stat, $p$-value, 95% CI, kết luận ý nghĩa.
  - `svg_visualization`: Biểu đồ SVG kép:
    - Panel A: Phối cảnh 3D đẳng cự (Isometric 3D Wireframe Surface) của bề mặt phản hồi tiềm ẩn $\hat{\eta}(\xi_1, \xi_2)$.
    - Panel B: Đồ thị phân tích độ dốc đơn giản (Simple Slopes Probing Plot) với ba đường hồi quy màu phân biệt (Xanh biển: $-1\text{SD}$, Xám: Mean, Lục bảo: $+1\text{SD}$) kèm các vạch phân cách ngưỡng Johnson-Neyman.
  - `apa_narrative`: Đoạn thuyết minh học thuật định dạng chuẩn APA 7th Edition theo Klein & Moosbrugger (2000) và Marsh et al. (2004).
- **Niêm phong kiểm toán:** Tự động ghi nhận `LATENT_MODERATION_LMS_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 95. Endogenous Switching Regression (ESR - FIML) Engine

- **Mục tiêu khoa học:** Đánh giá tác động nhân quả phản thực tế (Causal Counterfactual Impact) và kiểm soát triệt để sai lệch tự chọn lọc hai chiều (Two-regime endogenous self-selection bias) khi quyết định tham gia/áp dụng can thiệp là nội sinh và không đồng nhất (**Maddala 1983**; **Lokshin & Sajaia 2004**; **Lee 1978**; **Heckman 1979**).
- **Cơ sở phương pháp luận:**
  1. **Hệ Phương Trình Đồng Thời Chế Độ (Simultaneous Switching System):**
     - **Phương trình chọn lọc Probit (Selection Equation):**
       $$I_i^* = \mathbf{Z}_i \boldsymbol{\gamma} + u_i, \quad I_i = 1 \text{ if } I_i^* > 0, \quad 0 \text{ otherwise}$$
     - **Phương trình kết quả Chế độ 1 (Can thiệp / Áp dụng, $I_i = 1$):**
       $$Y_{1i} = \mathbf{X}_i \boldsymbol{\beta}_1 + \epsilon_{1i}$$
     - **Phương trình kết quả Chế độ 0 (Đối chứng / Không áp dụng, $I_i = 0$):**
       $$Y_{0i} = \mathbf{X}_i \boldsymbol{\beta}_0 + \epsilon_{0i}$$
  2. **Cấu Trúc Tương Quan Sai Số Ba Biến (Trivariate Normal Error Structure):**
     - $(\epsilon_{1i}, \epsilon_{0i}, u_i)' \sim \mathcal{N}_3(\mathbf{0}, \boldsymbol{\Omega})$ với:
       $$\boldsymbol{\Omega} = \begin{pmatrix} \sigma_1^2 & \cdot & \sigma_{1u} \\ \cdot & \sigma_0^2 & \sigma_{0u} \\ \sigma_{1u} & \sigma_{0u} & 1 \end{pmatrix}$$
     - Hệ số tương quan chọn lọc:
       $$\rho_1 = \text{Corr}(\epsilon_{1}, u) = \frac{\sigma_{1u}}{\sigma_1}, \quad \rho_0 = \text{Corr}(\epsilon_{0}, u) = \frac{\sigma_{0u}}{\sigma_0}$$
     - Nếu $\rho_1 \ne 0$ hoặc $\rho_0 \ne 0$, OLS ước lượng trên từng nhóm sẽ bị chệch nghiêm trọng do bỏ sót biến $\lambda_1, \lambda_0$.
  3. **Ước Lượng Hợp Lý Cực Đại Toàn Phần FIML (Full Information Maximum Likelihood):**
     - Hàm log-likelihood kết hợp cả ba phương trình:
       $$\ln L = \sum_{i: I_i = 1} \left[ \ln \phi\left(\frac{Y_{1i} - \mathbf{X}_i \boldsymbol{\beta}_1}{\sigma_1}\right) - \ln \sigma_1 + \ln \Phi\left(\frac{\mathbf{Z}_i \boldsymbol{\gamma} + \rho_1 (Y_{1i} - \mathbf{X}_i \boldsymbol{\beta}_1)/\sigma_1}{\sqrt{1 - \rho_1^2}}\right) \right] + \sum_{i: I_i = 0} \left[ \ln \phi\left(\frac{Y_{0i} - \mathbf{X}_i \boldsymbol{\beta}_0}{\sigma_0}\right) - \ln \sigma_0 + \ln \left(1 - \Phi\left(\frac{\mathbf{Z}_i \boldsymbol{\gamma} + \rho_0 (Y_{0i} - \mathbf{X}_i \boldsymbol{\beta}_0)/\sigma_0}{\sqrt{1 - \rho_0^2}}\right)\right) \right]$$
     - Tối ưu hóa bằng L-BFGS-B tham số hóa qua $r_j = \text{atanh}(\rho_j)$ đảm bảo tính ổn định số học và chặn nghiệm $|\rho_j| < 1$.
     - Kiểm định tỷ số hợp lý LR test tính độc lập của các phương trình: $H_0: \rho_1 = \rho_0 = 0$.
  4. **Phân Rã Nhân Quả Phản Thực Tế (Causal Counterfactual Decomposition):**
     - Tỷ số nghịch đảo Mills: $\lambda_{1i} = \frac{\phi(\mathbf{Z}_i \boldsymbol{\gamma})}{\Phi(\mathbf{Z}_i \boldsymbol{\gamma})}$; $\lambda_{0i} = -\frac{\phi(\mathbf{Z}_i \boldsymbol{\gamma})}{1 - \Phi(\mathbf{Z}_i \boldsymbol{\gamma})}$.
     - **Hiệu ứng xử lý trung bình đối với nhóm can thiệp (ATT):**
       $$E[Y_{1i} | I_i = 1] = \mathbf{X}_i \boldsymbol{\beta}_1 + \sigma_1 \rho_1 \lambda_{1i}$$
       $$E[Y_{0i} | I_i = 1] = \mathbf{X}_i \boldsymbol{\beta}_0 + \sigma_0 \rho_0 \lambda_{1i} \quad \text{(Phản thực tế)}$$
       $$\text{ATT} = E[Y_{1i} | I_i = 1] - E[Y_{0i} | I_i = 1] = \mathbf{X}_i (\boldsymbol{\beta}_1 - \boldsymbol{\beta}_0) + (\sigma_1 \rho_1 - \sigma_0 \rho_0) \lambda_{1i}$$
     - **Hiệu ứng xử lý trung bình đối với nhóm đối chứng (ATU):**
       $$E[Y_{0i} | I_i = 0] = \mathbf{X}_i \boldsymbol{\beta}_0 + \sigma_0 \rho_0 \lambda_{0i}$$
       $$E[Y_{1i} | I_i = 0] = \mathbf{X}_i \boldsymbol{\beta}_1 + \sigma_1 \rho_1 \lambda_{0i} \quad \text{(Phản thực tế)}$$
       $$\text{ATU} = E[Y_{1i} | I_i = 0] - E[Y_{0i} | I_i = 0] = \mathbf{X}_i (\boldsymbol{\beta}_1 - \boldsymbol{\beta}_0) + (\sigma_1 \rho_1 - \sigma_0 \rho_0) \lambda_{0i}$$
     - **Tính không đồng nhất chuyển đổi (Transitional Heterogeneity):** $\text{TH} = \text{ATT} - \text{ATU}$.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/endogenous-switching`
- **Request Body (`EndogenousSwitchingRequest`):**
  - `treatment_question_id`: UUID của câu hỏi phân loại can thiệp nhị phân $I \in \{0, 1\}$.
  - `outcome_question_id`: UUID của câu hỏi kết quả liên tục $Y$.
  - `covariate_question_ids`: Danh sách UUID các biến giải thích trong phương trình kết quả $X$.
  - `instrument_question_ids`: Danh sách UUID các biến công cụ loại trừ $Z$ (chỉ xuất hiện trong phương trình chọn lọc, tùy chọn).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`EndogenousSwitchingOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"ENDOGENOUS_SWITCHING_REGRESSION_FIML"`.
  - `diagnostics`: Tổng mẫu $N$, số lượng và tỷ lệ % từng chế độ, hội tụ FIML, Log-Likelihood, thống kê kiểm định LR tính độc lập $\chi^2(2)$, $p$-value kiểm định chọn lọc nội sinh, $\rho_1, \rho_0, \sigma_1, \sigma_0$, ATT, ATU, Transitional Heterogeneity (TH), Base Heterogeneity ($BH_1, BH_0$).
  - `treatment_effects`: Bảng chi tiết ATT, ATU: Ước lượng hiệu ứng, SE, $t$-stat, $p$-value, khoảng tin cậy 95% CI.
  - `coefficients`: Bảng đối chiếu hệ số hai chế độ: $\beta_1$ (Regime 1), SE, $p$, $\beta_0$ (Regime 0), SE, $p$, chênh lệch hệ số $(\beta_1 - \beta_0)$.
  - `svg_visualization`: Biểu đồ SVG kép:
    - Panel A: Biểu đồ cột so sánh kết quả thực tế vs phản thực tế cho nhóm Can thiệp (ATT) và nhóm Đối chứng (ATU).
    - Panel B: Forest plot so sánh hệ số theo chế độ ($\beta_1$ xanh lục vs $\beta_0$ xanh lam) kèm dải tin cậy 95% CI.
  - `apa_narrative`: Đoạn thuyết minh học thuật định dạng chuẩn APA 7th Edition theo Maddala (1983) và Lokshin & Sajaia (2004).
- **Niêm phong kiểm toán:** Tự động ghi nhận `ENDOGENOUS_SWITCHING_REGRESSION_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 96. Động Cơ Phân Tích Điểm Xu Hướng Khái Quát & Hàm Liều Lượng - Đáp Ứng (Generalized Propensity Score GPS & Dose-Response Analysis - Hirano & Imbens 2004)

- **Cơ sở khoa học:** Khi biến can thiệp/chính sách trong khảo sát là một đại lượng liên tục (Continuous Treatment Regime, ví dụ: số giờ tham gia đào tạo, chi phí đầu tư công nghệ, liều lượng hỗ trợ tài chính, thời lượng sử dụng nền tảng), các phương pháp đối sánh điểm xu hướng nhị phân truyền thống (Binary PSM hay IPTW) không thể áp dụng được hoặc buộc phải chia nhóm tùy tiện làm mất thông tin và gây thiên lệch. Hirano & Imbens (2004) mở rộng lý thuyết điểm xu hướng của Rosenbaum & Rubin (1983) sang trường hợp can thiệp liên tục bằng Điểm Xu Hướng Khái Quát (Generalized Propensity Score - GPS).
- **Phương pháp luận kinh tế lượng:**
  1. **Mô Hình Can Thiệp Liên Tục & Mật Độ Xu Hướng Khái Quát:**
     - Giả định can thiệp liên tục có phân phối chuẩn có điều kiện: $T_i | \mathbf{X}_i \sim \mathcal{N}(\mathbf{X}_i \boldsymbol{\beta}, \sigma^2)$.
     - Điểm xu hướng khái quát $R_i = r(T_i, \mathbf{X}_i)$ là giá trị mật độ xác suất điều kiện:
       $$R_i = \frac{1}{\sqrt{2\pi \sigma^2}} \exp\left( -\frac{(T_i - \mathbf{X}_i \boldsymbol{\beta})^2}{2\sigma^2} \right)$$
  2. **Mô Hình Hồi Quy Kết Quả Điều Kiện Linh Hoạt:**
     - Ước lượng hàm hồi quy kết quả theo liều lượng can thiệp $T$ và điểm xu hướng $R$ (kèm các thành phần bậc hai hoặc tương tác):
       $$E[Y_i | T_i, R_i] = \alpha_0 + \alpha_1 T_i + \alpha_2 T_i^2 + \alpha_3 R_i + \alpha_4 R_i^2 + \alpha_5 (T_i \cdot R_i)$$
  3. **Hàm Liều Lượng - Đáp Ứng Trung Bình (Average Dose-Response Function - ADRF):**
     - Bằng cách lấy tích phân (trung bình hóa) trên toàn bộ phân phối của các biến kiểm soát trong quần thể mẫu:
       $$\mu(t) = E[Y(t)] = \frac{1}{N} \sum_{i=1}^N \left[ \hat{\alpha}_0 + \hat{\alpha}_1 t + \hat{\alpha}_2 t^2 + \hat{\alpha}_3 \hat{r}(t, \mathbf{X}_i) + \hat{\alpha}_4 \hat{r}(t, \mathbf{X}_i)^2 + \hat{\alpha}_5 (t \cdot \hat{r}(t, \mathbf{X}_i)) \right]$$
  4. **Hàm Hiệu Ứng Biên Can Thiệp (Marginal Treatment Effect Function - MTEF):**
     - Đạo hàm bậc nhất của đường cong đáp ứng theo liều lượng:
       $$\theta(t) = \frac{d\mu(t)}{dt}$$
     - Xác định điểm liều lượng tối ưu $t^*$ (Optimal Dosage Peak) tại đó $\theta(t^*) = 0$, phân tách rõ vùng lợi ích cận biên dương tăng trưởng và vùng bão hòa hoặc suy giảm lợi ích.
  5. **Dải Tin Cậy Chuẩn Hóa Bằng Bootstrap / Delta Method:**
     - Tính sai số chuẩn và khoảng tin cậy 95% CI dọc theo toàn bộ lưới liều lượng đánh giá $t \in [t_{\min}, t_{\max}]$.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/gps-dose-response`
- **Request Body (`GPSDoseResponseRequest`):**
  - `treatment_question_id`: UUID của câu hỏi can thiệp liên tục $T$.
  - `outcome_question_id`: UUID của câu hỏi kết quả liên tục $Y$.
  - `covariate_question_ids`: Danh sách UUID các biến kiểm soát nền $\mathbf{X}$.
  - `grid_points`: Số điểm lưới đánh giá liều lượng trên miền giá trị (mặc định 50, tối đa 200).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`GPSDoseResponseOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"GENERALIZED_PROPENSITY_SCORE_DOSE_RESPONSE"`.
  - `diagnostics`: Tổng mẫu $N$, R-squared phương trình can thiệp và phương trình kết quả, độ lệch chuẩn dư can thiệp $\sigma$, điểm liều lượng tối ưu $t^*$, đáp ứng cực đại $\mu(t^*)$, hiệu ứng biên trung bình $\bar{\theta}$.
  - `treatment_equation`: Bảng hệ số phương trình điểm xu hướng $\beta_j$, SE, $t$-stat, $p$-value.
  - `outcome_equation`: Bảng hệ số phương trình kết quả có điều kiện $\alpha_j$, SE, $t$-stat, $p$-value.
  - `dose_response_curve`: Mảng các điểm lưới liều lượng $t$, giá trị đáp ứng $\mu(t)$, dải tin cậy dưới/trên 95% CI, và hiệu ứng biên $\theta(t)$.
  - `svg_visualization`: Biểu đồ SVG kép:
    - Panel A: Đường cong hàm Liều Lượng - Đáp Ứng Trung Bình $\mu(t)$ (màu chàm Indigo) với dải bóng tin cậy 95% CI và vạch chỉ điểm liều lượng tối ưu $t^*$.
    - Panel B: Đường cong hàm Hiệu Ứng Can Thiệp Cận Biên $\theta(t) = d\mu/dt$ (màu ngọc lam Teal) kèm đường mốc tham chiếu không hiệu ứng ($y = 0$).
  - `apa_narrative`: Báo cáo học thuật chi tiết định dạng chuẩn APA 7th Edition theo lý thuyết Hirano & Imbens (2004).
- **Niêm phong kiểm toán:** Tự động ghi nhận `GPS_DOSE_RESPONSE_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 97. Động Cơ Khám Phá Cấu Trúc Đồ Thị Nhân Quả Khảo Sát (Causal Discovery DAG - LiNGAM & ANM)

- **Cơ sở khoa học:** Trong nghiên cứu khảo sát định lượng, việc xác lập chiều hướng quan hệ nhân quả (Causal Direction) thường vấp phải rào cản tương đương Markov (Markov Equivalence Class) trong các mô hình tuyến tính phân phối chuẩn (Gaussian), khiến không thể phân biệt giữa $X \to Y$ và $Y \to X$ nếu chỉ dựa trên ma trận hiệp phương sai cắt ngang. Tuy nhiên, dữ liệu khảo sát thực tế (thang đo Likert, điểm số độ tin cậy, thời lượng, v.v.) hầu như luôn có tính chất phi chuẩn (Non-Gaussian) thể hiện qua độ lệch (Skewness) hoặc độ nhọn (Kurtosis). Shimizu et al. (2006, 2011) đã chứng minh định lý định danh cơ bản: Trong mô hình đồ thị có hướng không chu trình tuyến tính (LiNGAM) với các biến nhiễu liên tục độc lập và có phân phối phi chuẩn, toàn bộ cấu trúc DAG, thứ tự topo nhân quả và ma trận trọng số kết nối $\mathbf{B}$ là **hoàn toàn có thể định danh duy nhất (strictly and uniquely identifiable)**.
- **Phương pháp luận toán học:**
  1. **Mô Hình Tuyến Tính Phi Gauss Không Chu Trình (LiNGAM):**
     $$x_i = \sum_{j \in \text{Parents}(i)} b_{ij} x_j + e_i \iff \mathbf{X} = \mathbf{B} \mathbf{X} + \mathbf{e} = (\mathbf{I} - \mathbf{B})^{-1} \mathbf{e}$$
     với $e_i$ là các thành phần nhiễu độc lập lẫn nhau và có tối đa 1 thành phần có phân phối chuẩn.
  2. **Tách Thành Phần Độc Lập Bằng FastICA & Xác Định Thứ Tự Topo:**
     - Chuẩn hóa và làm trắng dữ liệu (Whitening via SVD): $\tilde{\mathbf{X}} = \mathbf{V} \mathbf{D}^{-1/2} \mathbf{V}^T \mathbf{X}$.
     - Tối ưu hóa FastICA với hàm tương phản $g(u) = \tanh(u)$ để tìm ma trận tách nhiễu $\mathbf{W} = \mathbf{A}^{-1}$.
     - Thuật toán hoán vị hàng/cột của $\mathbf{W}$ để tìm thứ tự topo nhân quả (Topological Causal Ordering) sao cho ma trận trọng số $\mathbf{B}$ có dạng tam giác dưới nghiêm ngặt (Strictly Lower Triangular).
  3. **Ước Lượng Trọng Số Đường Dẫn & Ma Trận Tổng Hiệu Ứng (Total Causal Effects):**
     - Hồi quy OLS theo từng biến trên tập hợp tiền tố các biến nguyên nhân trong thứ tự topo.
     - Áp dụng ngưỡng tỉa cạnh (Prune Threshold) $\tau$ và loại bỏ các cạnh không có ý nghĩa thống kê ($p \ge 0.05$).
     - Tính toán ma trận tổng hiệu ứng tích lũy: $\mathbf{T} = (\mathbf{I} - \mathbf{B})^{-1} - \mathbf{I}$.
  4. **Kiểm Định Độc Lập Phần Dư Bằng Mô Hình Nhiễu Cộng Tính (ANM - Hoyer et al. 2009):**
     - Với mỗi cạnh có hướng $X \to Y$, kiểm định tính độc lập giữa phần dư $\hat{e}_Y$ và biến nguyên nhân $X$ bằng hệ số tương quan hạng Spearman và thống kê độc lập phi tuyến. Nếu $\hat{e}_Y \perp\!\!\perp X$ được thỏa mãn, chiều nhân quả từ $X$ đến $Y$ được xác thực hoàn toàn và loại trừ quan hệ đảo chiều $Y \to X$.
  5. **Kiểm Tra Điều Kiện Tiền Đề Phi Gauss (Non-Gaussianity Profiling):**
     - Đánh giá Skewness, Excess Kurtosis và kiểm định chuẩn hóa đa biến D'Agostino-Pearson omnibus test ($K^2$) cho từng biến khảo sát để xác nhận điều kiện tiên quyết của định lý Shimizu et al. (2006).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/causal-discovery`
- **Request Body (`CausalDiscoveryRequest`):**
  - `variable_question_ids`: Danh sách UUID các câu hỏi khảo sát tham gia đồ thị nhân quả ($p \ge 2$).
  - `prune_threshold`: Ngưỡng loại bỏ trọng số đường dẫn nhỏ (mặc định $0.05$).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`CausalDiscoveryOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"CAUSAL_DISCOVERY_LINGAM_ANM"`.
  - `diagnostics`: Tổng mẫu $N$, số biến $p$, trạng thái hội tụ FastICA, số biến phi Gauss thỏa mãn điều kiện định danh, tổng số cạnh có hướng phát hiện, ngưỡng tỉa cạnh.
  - `causal_order`: Danh sách tên các biến theo thứ tự topo nhân quả xác lập ($X_{\text{root}} \to \dots \to X_{\text{sink}}$).
  - `directed_edges`: Danh sách các cạnh nhân quả có hướng: Biến nguyên nhân `from`, Biến hệ quả `to`, Hệ số trực tiếp `path_coefficient` $\beta$, Tổng hiệu ứng nhân quả `total_effect`, `t_statistic`, `p_value`, cờ ý nghĩa `is_significant`.
  - `non_gaussianity_tests`: Bảng đánh giá phân phối phi Gauss: Tên biến, Skewness, Excess Kurtosis, Thống kê Omnibus $K^2$, $p$-value, Cờ đạt chuẩn định danh `is_non_gaussian`.
  - `anm_diagnostics`: Bảng kiểm định mô hình cộng tính: Tên cạnh, Tương quan phần dư - nguyên nhân $\rho$, $p$-value độc lập, Cờ độc lập `anm_noise_independent`.
  - `adjacency_matrix`: Ma trận kề trọng số $\mathbf{B}$ cỡ $p \times p$.
  - `total_effects_matrix`: Ma trận tổng hiệu ứng $\mathbf{T}$ cỡ $p \times p$.
  - `svg_visualization`: Biểu đồ SVG kép:
    - Panel A: Đồ thị có hướng DAG trực quan với các nút tròn đại diện biến, mũi tên cong có hướng (xanh lục: tác động dương, đỏ: tác động âm) kèm nhãn hệ số trực tiếp.
    - Panel B: Biểu đồ thanh đo lường mức độ phi chuẩn $|Ku| + |Sk|$ của các biến kèm nhãn trạng thái đạt chuẩn định danh (Identifiable).
  - `apa_narrative`: Thuyết minh học thuật định dạng chuẩn APA 7th Edition theo lý thuyết Shimizu et al. (2006) và Hoyer et al. (2009).
- **Niêm phong kiểm toán:** Tự động ghi nhận `CAUSAL_DISCOVERY_DAG_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 98. Động Cơ Cây Hồi Quy Cộng Tính Bayes (BART Causal Inference & Heterogeneity)

- **Cơ sở khoa học:** Trong đánh giá tác động can thiệp hoặc chính sách khảo sát, giả định hiệu ứng can thiệp đồng nhất (Constant Treatment Effect) đối với toàn bộ quần thể là một giả định phi thực tế. Đồng thời, các mô hình hồi quy tuyến tính tham số truyền thống ($T \times X$) đòi hỏi nhà nghiên cứu phải xác định trước dạng hàm tương tác cụ thể, dễ dẫn đến sai lệch dạng hàm nghiêm trọng (Functional Form Misspecification). Chipman, George & McCulloch (2010), Jennifer L. Hill (2011), và P. Richard Hahn et al. (2020 - Bayesian Causal Forests) đã phát triển Cây Hồi Quy Cộng Tính Bayes (BART) - một mô hình học máy phi tham số Bayesian cho phép tự động nắm bắt các cấu trúc phi tuyến phức tạp và các tương tác bậc cao, đồng thời kiểm soát chặt chẽ hiện tượng quá khớp (Overfitting) bằng các tiên nghiệm co ngót Bayes (Bayesian Regularizing Shrinkage Priors).
- **Phương pháp luận toán học:**
  1. **Mô Hình Tập Hợp Tổng Các Cây Hồi Quy (Sum-of-Trees Ensemble):**
     $$Y_i = \sum_{m=1}^M g(\mathbf{X}_i, T_i; \mathcal{T}_m, \mathcal{M}_m) + \epsilon_i, \quad \epsilon_i \sim \mathcal{N}(0, \sigma^2)$$
     trong đó mỗi cây $\mathcal{T}_m$ là một cây quyết định nông (thường có độ sâu 2–3 tầng) và $\mathcal{M}_m = \{\mu_{m1}, \dots, \mu_{mb_m}\}$ là tập hợp các tham số tại các nút lá.
  2. **Tiên Nghiệm Co Ngót Bayes (Regularizing Shrinkage Priors):**
     - Xác suất phân nhánh tại độ sâu $d$: $p(\text{split}) = \alpha (1 + d)^{-\beta}$ (với $\alpha = 0.95, \beta = 2$) áp đặt hình phạt nặng đối với các cây sâu, biến mỗi cây thành một "bộ học yếu" (Weak Learner).
     - Tiên nghiệm tham số lá: $\mu_{mj} \sim \mathcal{N}(0, \sigma_\mu^2)$ với $\sigma_\mu = \frac{y_{\max} - y_{\min}}{2 k \sqrt{M}}$ ($k = 2$) kéo trung bình lá về 0, đảm bảo hiệu ứng được phân bổ đều trên toàn bộ $M$ cây.
     - Tiên nghiệm phương sai nhiễu: $\sigma^2 \sim \text{Inv-}\chi^2(\nu, \lambda)$.
  3. **Ước Lượng Hiệu Ứng Can Thiệp Phản Thực Tế (Counterfactual Potential Outcomes):**
     - Dự báo giá trị phản thực tế có điều kiện:
       $$\hat{Y}_i(1) = \sum_{m=1}^M g(\mathbf{X}_i, 1; \mathcal{T}_m, \mathcal{M}_m), \quad \hat{Y}_i(0) = \sum_{m=1}^M g(\mathbf{X}_i, 0; \mathcal{T}_m, \mathcal{M}_m)$$
     - **Hiệu ứng can thiệp cá thể (Individual Treatment Effect - ITE):** $\tau_i = \hat{Y}_i(1) - \hat{Y}_i(0)$.
     - **Hiệu ứng can thiệp trung bình mẫu (Average Treatment Effect - ATE):** $\text{ATE} = \frac{1}{N} \sum_{i=1}^N \tau_i$.
     - **Hiệu ứng can thiệp trung bình trên nhóm tiếp nhận (ATT):** $\text{ATT} = \frac{1}{N_1} \sum_{i: T_i=1} \tau_i$.
     - **Hiệu ứng can thiệp trung bình trên nhóm đối chứng (ATU):** $\text{ATU} = \frac{1}{N_0} \sum_{i: T_i=0} \tau_i$.
  4. **Kiểm Định Tính Không Đồng Nhất Hiệu Ứng (Treatment Effect Heterogeneity Test):**
     - Tính toán độ lệch chuẩn hậu nghiệm của hiệu ứng cá thể: $\text{SD}(\tau) = \sqrt{\text{Var}(\tau_i)}$.
     - Nếu cận dưới khoảng tin cậy hậu nghiệm 95% Bayesian Credible Interval của $\text{SD}(\tau)$ cách biệt có ý nghĩa so với 0, khẳng định hiệu ứng can thiệp phân hóa đáng kể giữa các đáp viên.
  5. **Xác Định Biến Điều Tiết Hàng Đầu & Phân Rã CATE (Conditional Average Treatment Effect):**
     - Đếm tần suất biến được chọn làm quy tắc phân nhánh (Variable Importance / Split Counts) qua toàn bộ tập hợp cây.
     - Phân rã hiệu ứng CATE theo từng phân nhóm của biến điều tiết chủ đạo (ví dụ: Nhóm Thấp $\le$ Trung vị vs Nhóm Cao $>$ Trung vị) kèm khoảng tin cậy 95% CrI.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/bart-causal`
- **Request Body (`BARTCausalRequest`):**
  - `treatment_question_id`: UUID của câu hỏi can thiệp nhị phân $T \in \{0, 1\}$.
  - `outcome_question_id`: UUID của câu hỏi kết quả liên tục $Y$.
  - `covariate_question_ids`: Danh sách UUID các biến kiểm soát/điều tiết nền $\mathbf{X}$.
  - `n_trees`: Số lượng cây quyết định trong tập hợp (mặc định 50, từ 10 đến 100).
  - `n_samples`: Số mẫu lấy ngẫu nhiên hậu nghiệm MCMC (mặc định 200, từ 50 đến 500).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`BARTCausalOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"BAYESIAN_ADDITIVE_REGRESSION_TREES_CAUSAL"`.
  - `diagnostics`: Tổng mẫu $N$, số mẫu nhóm can thiệp $N_1$ và đối chứng $N_0$, số biến kiểm soát $k$, số cây $M$, số mẫu hậu nghiệm, cờ phát hiện không đồng nhất `has_significant_heterogeneity`.
  - `treatment_effects`: Bảng các chỉ số tác động can thiệp ATE, ATT, ATU (Ước lượng, Sai số chuẩn SE, Khoảng tin cậy hậu nghiệm 95% Bayesian Credible Interval [Lower, Upper], $p$-value).
  - `ite_distribution`: Bảng phân phối hiệu ứng cá thể: Phân vị p05, p25, median, p75, p95, độ phân tán $\text{SD}(\tau)$ kèm dải tin cậy 95% CrI.
  - `variable_importance`: Bảng xếp hạng mức độ ảnh hưởng điều tiết của các biến nền: Tên biến, Số lần phân nhánh, Tỷ lệ ảnh hưởng tương đối %, Cờ điều tiết chính `is_primary_moderator`.
  - `subgroup_cate`: Bảng phân rã CATE theo phân nhóm con của biến điều tiết chính (Tên biến, Phân nhóm Thấp/Cao, Số đáp viên, Ước lượng CATE, SE, 95% CrI).
  - `svg_visualization`: Biểu đồ SVG kép:
    - Panel A: Đường cong thác nước xếp hạng hiệu ứng cá thể (Sorted ITE Waterfall) $\tau_i$ kèm dải bóng tin cậy hậu nghiệm 95% Bayesian Credible Band (xanh lam Sky) và đường mốc ATE (xanh lục Emerald).
    - Panel B: Biểu đồ thanh ngang xếp hạng tầm quan trọng của các biến điều tiết (Variable Importance) kèm nhãn phân loại Primary/Secondary.
  - `apa_narrative`: Báo cáo học thuật chi tiết định dạng chuẩn APA 7th Edition theo lý thuyết Chipman et al. (2010) và Jennifer L. Hill (2011).
- **Niêm phong kiểm toán:** Tự động ghi nhận `BART_CAUSAL_HETEROGENEITY_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 99. Động Cơ Phân Tích Kết Hợp & Lựa Chọn Rời Rạc (Conjoint Analysis & Discrete Choice Experiment DCE - McFadden 1974; Train 2009)

- **Cơ sở khoa học:** Khi khảo sát định lượng nhu cầu thị trường, sự đánh đổi chính sách hoặc định giá sản phẩm mới, việc hỏi trực tiếp độ quan trọng của từng tính năng thường bị sai lệch trần (Ceiling Effect - người trả lời đều chấm điểm tối đa cho mọi tính năng). Thử nghiệm Lựa chọn Rời rạc (Discrete Choice Experiment - DCE) và Phân tích Kết hợp Dựa trên Lựa chọn (Choice-Based Conjoint - CBC) buộc đáp viên phải thực hiện đánh đổi thực tế giữa các hồ sơ sản phẩm/dịch vụ đa thuộc tính. Daniel McFadden (Giải Nobel Kinh tế 1974) và Kenneth E. Train (2009) đã thiết lập nền tảng toán học dựa trên Lý Thuyết Tối Đa Hóa Lợi Ích Ngẫu Nhiên (Random Utility Maximization - RUM).
- **Phương pháp luận kinh tế lượng:**
  1. **Mô Hình Lợi Ích Ngẫu Nhiên (Random Utility Model - RUM):**
     $$U_{nij} = V_{nij} + \epsilon_{nij} = \beta_0 + \sum_{k=1}^K \beta_k X_{nijk} + \epsilon_{nij}$$
     trong đó $V_{nij}$ là thành phần lợi ích xác định quan sát được và $\epsilon_{nij}$ là sai số ngẫu nhiên độc lập tuân theo phân phối giá trị cực trị Gumbel (Extreme Value Type I).
  2. **Xác Suất Lựa Chọn Logit Đa Thức (Multinomial / Conditional Logit):**
     $$P_{nij} = \frac{\exp(\mathbf{x}_{nij}' \boldsymbol{\beta})}{\sum_{j' \in \mathcal{C}_n} \exp(\mathbf{x}_{nij'}' \boldsymbol{\beta})}$$
     - Ước lượng tham số $\boldsymbol{\beta}$ bằng phương pháp Hợp lý cực đại chuẩn hóa (Regularized L-BFGS-B Maximum Likelihood).
     - Ma trận thông tin Fisher nghịch đảo để trích xuất sai số chuẩn tiệm cận vững và kiểm định giả thuyết $z$-test / $t$-test.
  3. **Độ Hữu Dụng Từng Phần & Tầm Quan Trọng Tương Đối (Part-Worth Utilities & Attribute Importance):**
     - Mỗi hệ số $\beta_k$ biểu diễn độ hữu dụng từng phần (Part-Worth Utility) gắn liền với một đơn vị thuộc tính.
     - Phạm vi biến thiên hữu dụng của thuộc tính $a$: $\text{Range}_a = |\beta_a| \times (X_{a,\max} - X_{a,\min})$.
     - Tỷ lệ tầm quan trọng tương đối (% Relative Attribute Importance):
       $$W_a = \frac{\text{Range}_a}{\sum_{a'=1}^K \text{Range}_{a'}} \times 100\%$$
  4. **Định Giá Sẵn Sàng Chi Trả Biên (Marginal Willingness-To-Pay - WTP):**
     - Khi một trong các thuộc tính là biến giá cả/chi phí ($X_{\text{Price}}$ với hệ số $\beta_{\text{Price}} < 0$):
       $$\text{WTP}_k = -\frac{\beta_k}{\beta_{\text{Price}}}$$
     - Sai số chuẩn của WTP được tính toán chính xác bằng phương pháp Delta Method:
       $$\text{Var}(\text{WTP}_k) \approx \frac{1}{\beta_{\text{Price}}^2} \text{Var}(\beta_k) + \frac{\beta_k^2}{\beta_{\text{Price}}^4} \text{Var}(\beta_{\text{Price}})$$
       cho phép xây dựng khoảng tin cậy 95% CI cho giá trị định giá của từng tính năng bằng đơn vị tiền tệ thực tế.
  5. **Chỉ Số Phù Hợp Mô Hình (Model Fit Diagnostics):**
     - McFadden's Pseudo-$R^2 = 1 - \frac{\ln L}{\ln L_0}$ (với giá trị $> 0.20$ biểu thị mô hình tốt và $> 0.40$ biểu thị mô hình xuất sắc theo thang đo McFadden).
     - Kiểm định tỷ số hợp lý Likelihood Ratio Test: $\text{LR} = 2(\ln L - \ln L_0) \sim \chi^2(K)$.
     - Tiêu chuẩn thông tin Akaike (AIC) và Bayesian (BIC).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/conjoint-choice`
- **Request Body (`ConjointChoiceRequest`):**
  - `choice_question_id`: UUID của câu hỏi chỉ báo lựa chọn ($1 = \text{Chọn}, 0 = \text{Bỏ qua/Không chọn}$).
  - `attribute_question_ids`: Danh sách UUID các câu hỏi thuộc tính cấu thành sản phẩm ($K \ge 1$).
  - `price_question_id`: UUID của câu hỏi giá cả/chi phí (tùy chọn, để kích hoạt định giá WTP).
  - `price_unit`: Đơn vị tiền tệ (mặc định `"mil VND"`).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`ConjointChoiceOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"CONJOINT_DISCRETE_CHOICE_MNL"`.
  - `diagnostics`: Tổng mẫu lựa chọn $N$, số lựa chọn được chọn $N_{\text{chosen}}$ và bỏ qua $N_{\text{rejected}}$, số thuộc tính $K$, McFadden's Pseudo-$R^2$, Log-Likelihood mô hình và Null, kiểm định LR Chi-square, $p$-value, AIC, BIC, trạng thái hội tụ.
  - `part_worth_utilities`: Bảng độ hữu dụng từng phần: Tên thuộc tính, Hệ số hữu dụng $\beta$, Sai số chuẩn SE, $t$-stat, $p$-value, Khoảng tin cậy 95% CI, Khoảng biến thiên hữu dụng Range, Tầm quan trọng tương đối `relative_importance_pct` (%), Cờ có ý nghĩa thống kê `is_significant`.
  - `willingness_to_pay`: Bảng sẵn sàng chi trả: Tên thuộc tính, Giá trị ước lượng WTP, Sai số chuẩn Delta, Khoảng tin cậy 95% CI [Lower, Upper], Đơn vị tiền tệ `unit`.
  - `svg_visualization`: Biểu đồ SVG kép:
    - Panel A: Biểu đồ thanh đo lường Tầm quan trọng tương đối (%) của các thuộc tính với dải màu gradient tím/lam.
    - Panel B: Forest plot biểu diễn định giá sẵn sàng chi trả WTP với điểm ước lượng tròn và thanh khoảng tin cậy 95% CI (màu xanh ngọc Emerald).
  - `apa_narrative`: Thuyết minh học thuật định dạng chuẩn APA 7th Edition theo lý thuyết McFadden (1974) và Train (2009).
- **Niêm phong kiểm toán:** Tự động ghi nhận `CONJOINT_CHOICE_MNL_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 100. Động Cơ Kiểm Định Bất Biến Đo Lường Đa Nhóm & Khác Biệt Điểm Tiềm Ẩn (MG-SEM Invariance & Latent Means - Meredith 1993; Byrne 2013)

- **Cơ sở khoa học:** Trong nghiên cứu khảo sát so sánh giữa các nhóm nhân khẩu học, vùng địa lý, văn hóa, hoặc các nhóm thử nghiệm (ví dụ: Nam vs Nữ, Miền Bắc vs Miền Nam, Doanh nghiệp Tư nhân vs Nhà nước, Nhóm Can thiệp vs Đối chứng), việc so sánh trực tiếp điểm số trung bình quan sát (Sum Scores / Composite Means) mà không chứng minh được tính bất biến đo lường (Measurement Invariance) là một sai lầm phương pháp luận phổ biến và nguy hiểm. Nếu các nhóm hiểu hoặc phản hồi câu hỏi khảo sát theo các chuẩn mực khác nhau (tồn tại Thiên lệch câu hỏi DIF hoặc không đồng nhất điểm chặn indicator), sự khác biệt điểm quan sát thực chất chỉ phản ánh thiên lệch đo lường chứ không phải sự khác biệt thực tế về bản chất khái niệm tiềm ẩn (Latent Trait).
- **Phương pháp luận kinh tế lượng & tâm trắc học:**
  1. **Cấp Bậc Kiểm Định Bất Biến Đo Lường (Measurement Invariance Hierarchy - Meredith 1993; Vandenberg & Lance 2000):**
     - **Cấp độ 1: Bất biến cấu hình (Configural Invariance):** Cùng một cấu trúc nhân tố đo lường CFA được thiết lập trên tất cả các nhóm (cùng số lượng nhân tố và cùng các biến quan sát tải lên cùng nhân tố).
     - **Cấp độ 2: Bất biến metric / yếu (Metric / Weak Invariance - Equal Factor Loadings $\boldsymbol{\Lambda}_1 = \boldsymbol{\Lambda}_2$):** Các hệ số tải nhân tố bằng nhau giữa các nhóm. Đảm bảo đáp viên ở các nhóm khác nhau hiệu chuẩn thang đo (Scale Calibration) như nhau. Đây là điều kiện tiên quyết bắt buộc để so sánh hiệp phương sai, tương quan và các hệ số đường dẫn cấu trúc (Structural Path Coefficients).
     - **Cấp độ 3: Bất biến scalar / mạnh (Scalar / Strong Invariance - Equal Indicator Intercepts $\boldsymbol{\tau}_1 = \boldsymbol{\tau}_2$):** Các điểm chặn của biến chỉ báo bằng nhau giữa các nhóm. Đảm bảo khi mức độ khái niệm tiềm ẩn bằng 0, giá trị kỳ vọng của các câu hỏi khảo sát là như nhau ở mọi nhóm. **Đây là điều kiện tiên quyết BẮT BUỘC để có thể so sánh Điểm Trung Bình Khái Niệm Tiềm Ẩn (Latent Means) mà không bị thiên lệch.**
     - **Cấp độ 4: Bất biến nghiêm ngặt / phần dư (Strict / Residual Invariance - Equal Error Variances $\boldsymbol{\Theta}_1 = \boldsymbol{\Theta}_2$):** Phương sai sai số đo lường của các câu hỏi bằng nhau giữa các nhóm.
  2. **Tiêu Chuẩn Đánh Giá Bất Biến Lồng Nhau (Nested Model Comparisons):**
     - Kiểm định Chi-square chênh lệch: $\Delta \chi^2(\Delta \text{df}) = \chi^2_{\text{constrained}} - \chi^2_{\text{unconstrained}}$.
     - Tiêu chuẩn thực nghiệm Cheung & Rensvold (2002): Khi kích thước mẫu lớn, $\Delta \chi^2$ thường quá nhạy cảm. Tiêu chuẩn $|\Delta \text{CFI}| \le 0.010$ và $\Delta \text{RMSEA} \le 0.015$ được áp dụng để xác nhận tính bất biến được duy trì.
  3. **Ước Lượng Chênh Lệch Điểm Số Tiềm Ẩn (Latent Means Analysis - Byrne 2013):**
     - Điểm trung bình tiềm ẩn của nhóm mốc (Reference Group) được cố định bằng 0: $\alpha_{\text{ref}} = 0$.
     - Điểm trung bình tiềm ẩn của nhóm so sánh (Comparison Group) $\alpha_{\text{comp}}$ được ước lượng tự do cùng với sai số chuẩn SE, thống kê $z$-statistic, $p$-value, khoảng tin cậy 95% CI.
     - **Kích thước hiệu ứng chuẩn hóa Cohen's $d$ cho biến tiềm ẩn:**
       $$d = \frac{\hat{\alpha}_{\text{comp}} - \hat{\alpha}_{\text{ref}}}{\sigma_{\text{latent, pooled}}}$$
       với phân loại định lượng: $|d| \ge 0.2$ (Hiệu ứng nhỏ), $|d| \ge 0.5$ (Hiệu ứng vừa), $|d| \ge 0.8$ (Hiệu ứng lớn).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/mgsem-invariance`
- **Request Body (`MGSEMInvarianceRequest`):**
  - `group_question_id`: UUID của câu hỏi phân nhóm khảo sát (ví dụ: Vùng miền, Giới tính, Nhóm tuổi, v.v.).
  - `indicator_question_ids`: Danh sách UUID các câu hỏi chỉ báo thang đo tiềm ẩn ($m \ge 2$).
  - `reference_group`: Tên hoặc nhãn nhóm làm mốc chuẩn $\alpha = 0$ (tùy chọn, mặc định tự chọn nhóm đầu).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`MGSEMInvarianceOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"MULTI_GROUP_SEM_INVARIANCE"`.
  - `diagnostics`: Tổng mẫu $N_{\text{total}}$, số mẫu từng nhóm $N_1, N_2$, tên nhóm, số chỉ báo $m$, các cờ hỗ trợ bất biến `metric_supported`, `scalar_supported`, `strict_supported`.
  - `invariance_hierarchy`: Bảng 4 bước kiểm định cấp bậc lồng nhau (Configural, Metric, Scalar, Strict) gồm: $\chi^2$, df, $p$-value, CFI, RMSEA, SRMR, $\Delta \chi^2$, $\Delta \text{df}$, $\Delta p$, $\Delta \text{CFI}$, và nhãn trạng thái đánh giá `status`.
  - `latent_means_comparison`: Bảng kết quả so sánh biến tiềm ẩn: Nhóm mốc, Nhóm so sánh, Điểm mốc $\alpha_{\text{ref}} = 0$, Ước lượng chênh lệch $\Delta \alpha$, Sai số chuẩn SE, $z$-stat, $p$-value, Khoảng tin cậy 95% CI [Lower, Upper], Kích thước hiệu ứng Cohen's $d$, cờ ý nghĩa `is_significant`, cờ hợp lệ so sánh `is_valid_comparison` (dựa trên Scalar Invariance).
  - `indicator_parameters`: Bảng chi tiết từng câu hỏi: Hệ số tải nhân tố nhóm 1 ($\lambda_1$), nhóm 2 ($\lambda_2$), chênh lệch tải $|\Delta \lambda|$, Điểm chặn nhóm 1 ($\tau_1$), nhóm 2 ($\tau_2$), chênh lệch chặn $|\Delta \tau|$, cờ bất biến câu hỏi `is_scalar_invariant`.
  - `svg_visualization`: Biểu đồ SVG kép:
    - Panel A: Forest plot đối chiếu hệ số tải nhân tố giữa Nhóm 1 (xanh dương) và Nhóm 2 (hồng cánh sen) cho từng câu hỏi thang đo.
    - Panel B: Đường cong hàm mật độ xác suất chuẩn của biến tiềm ẩn (Latent Distribution) cho hai nhóm, minh họa trực quan khoảng cách chênh lệch $\Delta \alpha$ và kích thước hiệu ứng Cohen's $d$.
  - `apa_narrative`: Thuyết minh học thuật định dạng chuẩn APA 7th Edition theo lý thuyết Meredith (1993), Steenkamp & Baumgartner (1998) và Byrne (2013).
- **Niêm phong kiểm toán:** Tự động ghi nhận `MGSEM_INVARIANCE_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 101. Động Cơ Mô Hình Cộng Tính Khái Quát & Đường Cong P-Splines Phạt Lồi (Generalized Additive Models GAM & Penalized P-Splines - Hastie & Tibshirani 1990; Wood 2017)

- **Cơ sở khoa học:** Trong phân tích khảo sát thực tế và kinh tế lượng ứng dụng, mối quan hệ giữa biến dự báo (ví dụ: Thu nhập, Mức độ sử dụng, Thời gian tiếp xúc, Điểm số tương tác, Tuổi tác) và biến mục tiêu (Độ hài lòng, Lòng trung thành, Điểm NPS, Hành vi mua lại) hiếm khi tuân theo dạng tuyến tính đơn giản hoặc đa thức cố định. Việc giả định tuyến tính sai lầm dẫn đến hiện tượng chệch mô hình nghiêm trọng (functional form misspecification), trong khi việc lạm dụng hồi quy đa thức bậc cao gây hiện tượng Runge (dao động dữ dội ở hai biên). Generalized Additive Models (GAM) giải quyết triệt để thách thức này bằng cách thay thế các hệ số tuyến tính cố định $\beta X$ bằng các hàm trơn phi tham số $f(X)$ được xấp xỉ qua hệ cơ sở B-splines bậc 3 kết hợp điều chuẩn phạt đạo hàm cấp hai (Penalized Splines / P-Splines).
- **Phương pháp luận kinh tế lượng & thống kê:**
  1. **Biểu Diễn B-Splines Bậc Ba & Ma Trận Phạt Đạo Hàm (Eilers & Marx 1996; Wood 2017):**
     - Hàm trơn phi tuyến được biểu diễn dưới dạng tổ hợp tuyến tính của $K$ hàm cơ sở B-splines bậc ba:
       $$f(x) = \sum_{j=1}^K \beta_j B_j(x)$$
     - Cực tiểu hóa hàm mục tiêu phạt lồi (Penalized Least Squares):
       $$\min_{\boldsymbol{\beta}} \| \mathbf{y} - \mathbf{B}\boldsymbol{\beta} \|^2 + \lambda \boldsymbol{\beta}^T \mathbf{S} \boldsymbol{\beta}$$
       trong đó $\mathbf{S} = \mathbf{D}_2^T \mathbf{D}_2$ là ma trận phạt sai phân cấp hai (xấp xỉ tích phân bình phương đạo hàm cấp hai $\int [f''(x)]^2 dx$), và $\lambda \ge 0$ là tham số làm trơn (smoothing parameter).
     - Nghiệm giải tích đóng thông qua ma trận làm trơn (Hat Matrix):
       $$\hat{\boldsymbol{\beta}} = (\mathbf{B}^T \mathbf{B} + \lambda \mathbf{S})^{-1} \mathbf{B}^T \mathbf{y}, \quad \mathbf{H}_{\lambda} = \mathbf{B} (\mathbf{B}^T \mathbf{B} + \lambda \mathbf{S})^{-1} \mathbf{B}^T$$
  2. **Tối Ưu Hóa Tham Số Làm Trơn $\lambda$ Bằng Tiêu Chuẩn GCV (Generalized Cross-Validation):**
     $$\text{GCV}(\lambda) = \frac{N \cdot \| \mathbf{y} - \hat{\mathbf{y}} \|^2}{(N - \text{EDF})^2}$$
     trong đó $\text{EDF} = \text{tr}(\mathbf{H}_{\lambda})$ là Số Bậc Tự Do Hiệu Dụng (Effective Degrees of Freedom).
  3. **Kiểm Định Giả Thuyết Phi Tuyến Tính (Test of Non-Linearity):**
     - So sánh mô hình GAM phi tuyến với mô hình OLS tuyến tính bị giới hạn $(\text{df} = 1)$ bằng kiểm định $F$-test:
       $$F = \frac{(\text{RSS}_{\text{linear}} - \text{RSS}_{\text{GAM}}) / (\text{EDF} - 1)}{\text{RSS}_{\text{GAM}} / (N - \text{EDF})}$$
     - Nếu $p < 0.05$ và $\text{EDF} > 1.5$: Bác bỏ giả thuyết tuyến tính, xác nhận mối quan hệ phi tuyến thực chất trong dữ liệu khảo sát.
  4. **Dò Tìm Điểm Bão Hòa & Ngưỡng Đảo Chiều (Extrema & Saturation Threshold Detection):**
     - Tính đạo hàm số cấp một $\hat{f}'(x)$.
     - Tìm nghiệm $\hat{f}'(x^*) = 0$ để xác định các Điểm Bão Hòa (Diminishing Return Saturation Point), Điểm Cực Đại (Optimal Tipping Point) hoặc Điểm Đáy Chữ U (U-Shape Inversion Point) có ý nghĩa thực tiễn cho quyết sách quản trị.
  5. **Dải Băng Tin Cậy Bayes 95% (95% Bayesian Confidence Band - Nychka 1988):**
     $$\hat{f}(x) \pm 1.96 \cdot \sqrt{\mathbf{b}(x)^T \mathbf{V}_{\beta} \mathbf{b}(x)}$$
     với ma trận hiệp phương sai hậu nghiệm $\mathbf{V}_{\beta} = \hat{\sigma}^2 (\mathbf{B}^T \mathbf{B} + \lambda \mathbf{S})^{-1}$.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/gam-spline`
- **Request Body (`GAMSplineRequest`):**
  - `predictor_question_id`: UUID của câu hỏi biến dự báo liên tục/thứ bậc $X$ (ví dụ: Mức sử dụng, Thu nhập, Tần suất).
  - `outcome_question_id`: UUID của câu hỏi biến kết quả liên tục $Y$ (ví dụ: Độ hài lòng tổng thể, Điểm NPS, Cam kết).
  - `n_knots`: Số nút cơ sở B-splines (mặc định: 10, giới hạn 5 - 30).
  - `smoothing_penalty`: Tham số phạt $\lambda$ tùy chọn (nếu null, hệ thống tự động tối ưu hóa bằng GCV).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`GAMSplineOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"GAM_PENALIZED_P_SPLINE"`.
  - `diagnostics`: Cỡ mẫu $N$, R-squared hiệu chỉnh ($R^2_{\text{adj}}$), Sai số chuẩn mô hình (Residual SE), Bậc tự do hiệu dụng (EDF), Tham số phạt tối ưu $\lambda_{\text{opt}}$, GCV score, Thống kê $F$, $p$-value kiểm định phi tuyến, Cờ kết luận `is_significantly_nonlinear`, Nhận diện dạng hàm `shape_classification` (Tuyến tính, Lồi, Lõm, Chữ U, Ngưỡng bão hòa S-Curve).
  - `turning_points`: Danh sách các điểm cực trị/ngưỡng bão hòa $(x^*, y^*, \text{type})$ kèm ý nghĩa quyết sách.
  - `fitted_curve`: Bảng lưới 100 điểm dự báo $(x, \hat{f}(x), \text{CI}_{\text{lower}}, \text{CI}_{\text{upper}}, f'(x))$ phục vụ vẽ biểu đồ và mô phỏng What-If.
  - `svg_visualization`: Biểu đồ SVG kép:
    - Panel A: Đường cong hàm trơn phi tuyến GAM P-Splines (xanh dương ngọc) bao bọc bởi dải băng tin cậy Bayes 95% (xanh lơ mờ) và các điểm phân tán dữ liệu khảo sát, có đánh dấu điểm ngưỡng cực trị/bão hòa (đỏ).
    - Panel B: Đồ thị hàm đạo hàm bậc một $\hat{f}'(x)$ (cam san hô) đối chiếu với trục 0, thể hiện tốc độ tăng trưởng biên và biên độ tác động cận biên (Marginal Return).
  - `apa_narrative`: Thuyết minh học thuật định dạng chuẩn APA 7th Edition theo lý thuyết Hastie & Tibshirani (1990) và Wood (2017).
- **Niêm phong kiểm toán:** Tự động ghi nhận `GAM_SPLINE_ESTIMATED` vào chuỗi sổ cái SHA-256.


---

## 102. Động Cơ Phân Tích Hồ Sơ Tiềm Ẩn & Mô Hình Hỗn Hợp Gauss Đa Biến (Latent Profile Analysis LPA & Gaussian Mixture Models - McLachlan & Peel 2000; Collins & Lanza 2010)

- **Cơ sở khoa học:** Trong phân tích hành vi đáp viên và phân đoạn thị trường/khách hàng từ khảo sát, các phương pháp phân cụm kinh điển (như K-means hoặc Phân cụm thứ bậc Hierarchical Clustering) bộc lộ nhiều khiếm khuyết mang tính hệ thống: phụ thuộc vào khoảng cách hình học tùy tiện (Euclidean), giả định cụm hình cầu có kích thước phương sai bằng nhau, không dựa trên nền tảng suy diễn thống kê xác suất, và không tính toán được xác suất sai số phân loại của từng cá nhân. Latent Profile Analysis (LPA) là phương pháp tiếp cận hướng cá thể (Person-Centered Approach) dựa trên mô hình hỗn hợp hữu hạn (Finite Mixture Modeling) dành cho các biến chỉ báo khảo sát liên tục (thang đo Likert, điểm số cấu trúc, chỉ số tương tác). LPA giả định rằng quần thể đáp viên là sự pha trộn của $K$ phân đoạn tiềm ẩn (Latent Profiles) chưa quan sát được, mỗi phân đoạn sở hữu vector kỳ vọng trung bình $\boldsymbol{\mu}_k$ và ma trận hiệp phương sai $\boldsymbol{\Sigma}_k$ riêng biệt.
- **Phương pháp luận kinh tế lượng & tâm trắc học:**
  1. **Hàm Mật Độ Hỗn Hợp & Thuật Toán EM (McLachlan & Peel 2000; Dempster et al. 1977):**
     - Hàm mật độ xác suất của vector quan sát $\mathbf{y}_i = (y_{i1}, \dots, y_{ip})^T$:
       $$f(\mathbf{y}_i | \boldsymbol{\theta}) = \sum_{k=1}^K \pi_k \phi(\mathbf{y}_i; \boldsymbol{\mu}_k, \boldsymbol{\Sigma}_k)$$
       với $\pi_k$ là tỷ lệ phân bố tiên nghiệm ($\sum \pi_k = 1$), và $\phi(\cdot)$ là hàm mật độ chuẩn đa biến.
     - **Bước E (Expectation):** Ước lượng xác suất hậu nghiệm (Responsibility) đáp viên $i$ thuộc về hồ sơ $k$:
       $$\gamma_{ik} = P(C_i = k | \mathbf{y}_i) = \frac{\pi_k \phi(\mathbf{y}_i; \boldsymbol{\mu}_k, \boldsymbol{\Sigma}_k)}{\sum_{j=1}^K \pi_j \phi(\mathbf{y}_i; \boldsymbol{\mu}_j, \boldsymbol{\Sigma}_j)}$$
       áp dụng kỹ thuật ổn định số Log-Sum-Exp nhằm triệt tiêu hiện tượng tràn số thực dưới (underflow).
     - **Bước M (Maximization):** Cập nhật ước lượng tỷ lệ tiên nghiệm $\hat{\pi}_k = \frac{1}{N} \sum_{i=1}^N \gamma_{ik}$, vector trung bình $\hat{\boldsymbol{\mu}}_k = \frac{\sum \gamma_{ik} \mathbf{y}_i}{\sum \gamma_{ik}}$, và ma trận phương sai đường chéo $\hat{\sigma}_{kj}^2 = \frac{\sum \gamma_{ik} (y_{ij} - \hat{\mu}_{kj})^2}{\sum \gamma_{ik}}$ kèm điều chuẩn chống suy biến kỳ dị phương sai $\sigma_{kj}^2 \ge 10^{-4} s_j^2$.
  2. **Tiêu Chuẩn Lựa Chọn Số Lượng Hồ Sơ Tối Ưu (Class Enumeration - Nylund et al. 2007):**
     - Đánh giá đa mô hình đồng thời từ $K = 2$ đến $K = 5$ lớp tiềm ẩn.
     - Tiêu chuẩn thông tin: Bayesian Information Criterion (BIC), Sample-Size Adjusted BIC (SABIC - Sclove 1987), và Akaike Information Criterion (AIC).
     - Ưu tiên mô hình cực tiểu hóa BIC và SABIC đồng thời đảm bảo cỡ mẫu của mỗi phân đoạn tối thiểu $\ge 5\%$ tổng mẫu.
  3. **Đánh Giá Độ Sắc Nét & Phân Tách Phân Loại (Classification Quality & Entropy):**
     - **Chỉ số Entropy tương đối (Celeux & Soromenho 1996; Ramaswamy et al. 1993):**
       $$\text{Entropy} = 1 - \frac{\sum_{i=1}^N \sum_{k=1}^K -\gamma_{ik} \ln(\gamma_{ik})}{N \ln(K)}$$
       với $\text{Entropy} \in [0, 1]$. Giá trị $\text{Entropy} \ge 0.80$ minh chứng độ phân tách hồ sơ vượt trội sắc nét, hạn chế tối đa sai số gán nhầm đối tượng (Clark & Muthén 2009).
     - **Xác suất hậu nghiệm trung bình theo phân đoạn gán nhãn (Average Posterior Probability - AvePP):**
       $$\text{AvePP}_k = \frac{1}{N_k} \sum_{i \in \text{Profile}_k} \gamma_{ik}$$
       Quy chuẩn thực nghiệm Nagin (2005) yêu cầu $\text{AvePP}_k \ge 0.70$ trên mọi lớp tiềm ẩn.
  4. **Chuẩn Hóa Điểm Số & Nhận Diện Typology Chân Dung Đối Tượng:**
     - Tính toán điểm chuẩn hóa $z$-score cho từng biến chỉ báo trong từng hồ sơ: $z_{kj} = (\hat{\mu}_{kj} - \bar{y}_j) / s_j$.
     - Tự động gán nhãn chân dung đối tượng (Typology Persona) dựa trên hình thái vector $z$-score (ví dụ: "High-Trust Advocates", "Disengaged Detractors", "Pragmatic Middle", "Selective Focus").
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/latent-profile`
- **Request Body (`LatentProfileRequest`):**
  - `indicator_question_ids`: Danh sách UUID các câu hỏi chỉ báo liên tục/thứ bậc ($P \ge 2$).
  - `n_profiles`: Số lượng hồ sơ $K$ cần ước lượng (tùy chọn, nếu bỏ trống hệ thống tự động dò tìm $K$ tối ưu dựa trên BIC và Entropy).
  - `max_profiles`: Số lượng hồ sơ tối đa để so sánh trong bảng liệt kê (mặc định: 4, tối đa: 5).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`LatentProfileOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"LATENT_PROFILE_ANALYSIS_GMM"`.
  - `diagnostics`: Cỡ mẫu $N$, số chỉ báo $P$, số lớp tối ưu $K$, Log-Likelihood, AIC, BIC, SABIC, Entropy, cờ phân tách sắc nét `is_well_separated`, cấp độ phân tách `separation_quality`.
  - `model_comparison`: Bảng liệt kê so sánh các mô hình $K=2..K_{\max}$ gồm: Log-Likelihood, Số tham số $M$, AIC, BIC, SABIC, Entropy, Tỷ lệ lớp nhỏ nhất (%).
  - `profiles`: Danh sách hồ sơ tiềm ẩn: Mã hồ sơ `profile_id`, Nhãn chân dung `name`, Quy mô $N_k$, Tỷ lệ phần trăm $\%_k$, Xác suất hậu nghiệm TB `average_posterior_prob`, Thống kê chỉ báo (Trung bình $\hat{\mu}$, Độ lệch chuẩn $\hat{\sigma}$, Điểm chuẩn hóa $z$-score).
  - `svg_visualization`: Biểu đồ SVG kép:
    - Panel A: Đồ thị quỹ đạo điểm chuẩn hóa hồ sơ (Latent Profile Plot) với các đường gãy khúc màu sắc tương phản rực rỡ, các điểm nút tròn phát sáng và trục tham chiếu mốc $0.0z$.
    - Panel B: Thước đo chỉ số Entropy (High/Moderate/Low) kèm biểu đồ thanh ngang phân bổ tỷ lệ phần trăm từng hồ sơ và xác suất AvePP.
  - `apa_narrative`: Thuyết minh học thuật định dạng chuẩn APA 7th Edition theo lý thuyết McLachlan & Peel (2000), Nylund et al. (2007) và Collins & Lanza (2010).
- **Niêm phong kiểm toán:** Tự động ghi nhận `LATENT_PROFILE_ANALYSIS_ESTIMATED` vào chuỗi sổ cái SHA-256.


---

## 103. Động Cơ Phân Tích Động Lực Trọng Yếu & Hồi Quy Giá Trị Shapley (Shapley Value Regression & Key Driver Analysis KDA - Lipovetsky & Conklin 2001; Lundberg & Lee 2017)

- **Cơ sở khoa học:** Trong nghiên cứu thị trường, trải nghiệm khách hàng (Customer Experience - CX) và đánh giá chất lượng sản phẩm dịch vụ từ khảo sát số, việc xác định chính xác thuộc tính nào (ví dụ: Tốc độ xử lý, Độ ổn định, Sự hỗ trợ khách hàng, Mức giá hợp lý, Bảo mật dữ liệu) đóng vai trò quyết định chi phối sự hài lòng chung (CSAT), điểm đo lường mức độ quảng bá (NPS), lòng trung thành (Loyalty) hay hành vi tiếp tục sử dụng là mục tiêu chiến lược cốt lõi. Tuy nhiên, các tiêu chí đánh giá trong khảo sát luôn có tương quan nội tại rất cao ($r > 0.60 - 0.85$), dẫn đến hiện tượng đa cộng tuyến nghiêm trọng (Multicollinearity). Hồi quy tuyến tính OLS kinh điển khi đó sẽ sinh ra các hệ số $\beta$ bị méo mó (VIF phóng đại, dấu hệ số bị đảo ngược phi lý, không thể phân rã phần trăm đóng góp của từng tiêu chí vào tổng phương sai $R^2$). Hồi quy Giá trị Shapley (Shapley Value Regression / Game-Theoretic Decomposition) giải quyết trọn vẹn thách thức này bằng cách ứng dụng Lý thuyết Trò chơi Hợp tác (Cooperative Game Theory) của nhà toán học đoạt giải Nobel Lloyd Shapley (1953) vào phân rã kinh tế lượng (Lipovetsky & Conklin 2001; Lundberg & Lee 2017).
- **Phương pháp luận kinh tế lượng & lý thuyết trò chơi:**
  1. **Định Nghĩa Hàm Giá Trị Liên Minh & Đóng Góp Cận Biên (Coalitional Value Function):**
     - Cho tập hợp $P$ biến dự báo động lực $\mathcal{F} = \{X_1, \dots, X_P\}$ và biến kết quả mục tiêu $Y$.
     - Hàm giá trị liên minh $v(S)$ của một tập hợp con $S \subseteq \mathcal{F}$ được định nghĩa là hệ số xác định $R^2(S)$ của mô hình hồi quy OLS khi dự báo $Y$ chỉ bằng các biến trong $S$.
     - Đóng góp cận biên của biến $X_j$ vào liên minh $S$ (với $j \notin S$):
       $$\Delta R^2(S \cup \{j\}) = R^2(S \cup \{j\}) - R^2(S)$$
  2. **Công Thức Trọng Số Shapley Phân Rã Toàn Diện $2^P$ Mô Hình Phụ (Lipovetsky & Conklin 2001):**
     $$\phi_j = \sum_{S \subseteq \mathcal{F} \setminus \{j\}} \frac{|S|! (P - |S| - 1)!}{P!} \left( R^2(S \cup \{j\}) - R^2(S) \right)$$
     - **Tiên đề Hiệu quả Hoàn hảo (Axiom of Efficiency):**
       $$\sum_{j=1}^P \phi_j = R^2_{\text{full}}$$
       Tổng tất cả các giá trị Shapley $\phi_j$ bằng chính xác $100\%$ hệ số xác định bội $R^2$ của mô hình hồi quy đầy đủ, không bỏ sót và không tính trùng lặp bất kỳ phần phương sai nào.
     - **Tiên đề Không âm & Đối xứng (Non-negativity & Symmetry):** Đảm bảo không xảy ra hiện tượng hệ số âm giả tạo do đa cộng tuyến giữa các biến khảo sát có tương quan dương với biến kết quả.
  3. **Tỷ Trọng Tầm Quan Trọng Tương Đối (Relative Importance Share $W_j\%$):**
     $$W_j = \frac{\phi_j}{\sum_{k=1}^P \phi_k} \times 100\% = \frac{\phi_j}{R^2_{\text{full}}} \times 100\%$$
     Tổng tỷ trọng của toàn bộ các thuộc tính động lực luôn đạt chính xác $100.0\%$.
  4. **Ma Trận Quyết Định Ưu Tiên Hành Động (Importance-Performance Analysis - IPA Matrix; Martilla & James 1977):**
     - Kết hợp **Tầm Quan Trọng Tương Đối ($W_j\%$)** trên trục hoành $X$ với **Điểm Đánh Giá Thực Tế Trung Bình ($\bar{X}_j$)** trên trục tung $Y$, phân chia không gian thành 4 góc phần tư chiến lược thông qua ngưỡng trung vị (Median Thresholds):
       - **Góc Phần Tư 1 (High Importance, Low Performance):** *"Concentrate Here" (Ưu tiên Cải thiện Khẩn cấp)* — Yếu tố tác động then chốt nhưng hiệu năng kém; là điểm nghẽn nghiêm trọng nhất cần tập trung nguồn lực khắc phục ngay.
       - **Góc Phần Tư 2 (High Importance, High Performance):** *"Keep Up the Good Work" (Duy trì Phát huy Tối đa)* — Trọng điểm lợi thế cạnh tranh cốt lõi.
       - **Góc Phần Tư 3 (Low Importance, Low Performance):** *"Low Priority" (Thứ yếu / Đầu tư Thấp)* — Yếu tố ít ảnh hưởng và điểm số thấp; không cần phân bổ nhiều ngân sách.
       - **Góc Phần Tư 4 (Low Importance, High Performance):** *"Possible Overkill" (Tránh Lãng phí Tài nguyên)* — Yếu tố ít ảnh hưởng nhưng lại được đầu tư quá mức; cần cân nhắc tái phân bổ nguồn lực sang Vùng 1.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/shapley-drivers`
- **Request Body (`ShapleyDriverRequest`):**
  - `driver_question_ids`: Danh sách UUID các câu hỏi thuộc tính động lực ($P \ge 2$).
  - `outcome_question_id`: UUID của câu hỏi biến kết quả tổng thể (CSAT, NPS, Điểm trung thành, Ý định mua lại).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`ShapleyDriverOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"SHAPLEY_VALUE_KEY_DRIVER_ANALYSIS"`.
  - `diagnostics`: Cỡ mẫu $N$, số lượng động lực $P$, hệ số $R^2$ mô hình đầy đủ, tổng đóng góp Shapley $\sum \phi_j$, sai số hiệu quả $\epsilon_{\text{gap}}$, chỉ số VIF lớn nhất, cờ đa cộng tuyến `has_multicollinearity`, ngưỡng trung vị tầm quan trọng và hiệu năng.
  - `drivers`: Danh sách xếp hạng động lực: Thứ hạng, Tên thuộc tính, Đóng góp cận biên Shapley $\Delta R^2$, Tỷ trọng tầm quan trọng ($W\%$), Điểm đánh giá TB, Độ lệch chuẩn, Hệ số tương quan Pearson, Chỉ số phóng đại phương sai VIF, Phân vùng chiến lược IPA (`strategic_quadrant`), Nhãn phân vùng (`strategic_label`), và Mức độ cấp bách hành động (`action_urgency`).
  - `svg_visualization`: Biểu đồ SVG kép:
    - Panel A: Biểu đồ thanh ngang phân cấp Tầm quan trọng tương đối Shapley ($W\%$) với mã màu theo phân tầng chiến lược (Xanh ngọc Emerald: Hàng đầu $\ge 25\%$, Xanh lơ Cyan: Trung bình, Xám phiến: Thứ yếu).
    - Panel B: Ma trận Quyết định Chiến lược IPA 4 góc phần tư với các đường phân vị đứt nét, nhãn chìm đánh dấu từng vùng và các điểm dữ liệu tròn phát sáng có nhãn tên thuộc tính.
  - `apa_narrative`: Thuyết minh học thuật định dạng chuẩn APA 7th Edition theo lý thuyết Shapley (1953), Martilla & James (1977) và Lipovetsky & Conklin (2001).
- **Niêm phong kiểm toán:** Tự động ghi nhận `SHAPLEY_KEY_DRIVERS_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 104. Động Cơ Mô Hình Lựa Chọn Xếp Hạng Plackett-Luce (Plackett-Luce Choice Model & Rank-Ordered Logit - Luce 1959; Plackett 1975; Hunter 2004 MM)

- **Cơ sở khoa học:** Trong các khảo sát ưu tiên tính năng sản phẩm, bình chọn thương hiệu, xếp hạng ứng viên hay thứ bậc chính sách công, câu hỏi dạng xếp hạng (Rank-Ordering Questions) hoặc thang điểm đánh giá đa thuộc tính là định dạng thu thập dữ liệu phổ biến nhất. Tuy nhiên, cách thức phân tích truyền thống (tính điểm trung bình thứ hạng Mean Rank 1.2 vs 2.4) bộc lộ sai lầm phương pháp luận nghiêm trọng: giả định khoảng cách giữa các bậc xếp hạng là đều nhau (khoảng cách giữa hạng 1 và 2 không hề tương đương khoảng cách giữa hạng 3 và 4), vi phạm bản chất phi tuyến của sự lựa chọn con người, và không thể suy diễn xác suất một phương án sẽ đánh bại phương án khác khi đặt trong đối đầu trực diện. Mô hình Lựa chọn Xác suất Plackett-Luce (Luce 1959; Plackett 1975; Beggs, Cardell & Hausman 1981) giải quyết triệt để bài toán này bằng cách mô hình hóa quá trình xếp hạng như một chuỗi các quyết định lựa chọn đa thức liên tiếp (Sequence of Multinomial Choices) tuân thủ Tiên đề Lựa chọn Luce (Choice Axiom).
- **Phương pháp luận kinh tế lượng & tối ưu hóa MM:**
  1. **Hàm Hợp Lý Hoán Vị Plackett-Luce (Permutation Likelihood):**
     - Cho tập hợp $M$ phương án $\{1, \dots, M\}$. Mỗi đáp viên $i$ tạo ra một hoán vị thứ bậc $\mathbf{r}_i = (r_{i1}, r_{i2}, \dots, r_{iM})$, trong đó $r_{i1}$ là phương án xếp hạng 1, $r_{i2}$ xếp hạng 2,...
     - Xác suất quan sát hoán vị $\mathbf{r}_i$ phụ thuộc vào vector tham số giá trị tiềm ẩn (Latent Worth) $\mathbf{w} = (w_1, \dots, w_M)^T$ với điều kiện chuẩn hóa $\sum_{j=1}^M w_j = 1$ và $w_j > 0$:
       $$P(\mathbf{r}_i | \mathbf{w}) = \prod_{m=1}^{M-1} \frac{w_{r_{im}}}{\sum_{k=m}^M w_{r_{ik}}} = \prod_{m=1}^{M-1} \frac{\exp(\gamma_{r_{im}})}{\sum_{k=m}^M \exp(\gamma_{r_{ik}})}$$
       trong đó $\gamma_j = \ln(w_j)$ là độ hữu dụng log-worth.
  2. **Thuật Toán Minorization-Maximization (Hunter 2004 MM Algorithm):**
     - Tránh hoàn toàn sự bất ổn định của Newton-Raphson khi số lượng phương án lớn. Thuật toán MM của David R. Hunter (2004) đảm bảo tính hội tụ đơn điệu toàn cục đến nghiệm cực đại hợp lý (MLE) duy nhất:
       $$w_j^{(t+1)} = c_j \left[ \sum_{i=1}^N \sum_{m=1}^{M-1} \frac{\mathbb{I}(j \in \{r_{im}, \dots, r_{iM}\})}{\sum_{k=m}^M w_{r_{ik}}^{(t)}} \right]^{-1}$$
       với $c_j$ là tổng số lần phương án $j$ được chọn trước ít nhất một phương án khác còn lại trong tập hợp.
     - Chuẩn hóa lại ở mỗi bước: $\mathbf{w}^{(t+1)} \leftarrow \mathbf{w}^{(t+1)} / \sum w_k^{(t+1)}$ cho đến khi $\|\mathbf{w}^{(t+1)} - \mathbf{w}^{(t)}\|_{\infty} < 10^{-7}$.
  3. **Sai Số Chuẩn & Khoảng Tin Cậy 95% CI (Asymptotic Standard Errors):**
     - Trích xuất ma trận thông tin Fisher quan sát bằng cách tính nghịch đảo ma trận Hessian số học của hàm log-likelihood đối với $M-1$ tham số tự do:
       $$\text{SE}(\gamma_j) = \sqrt{(-\mathbf{H}^{-1})_{jj}}$$
     - Thống kê kiểm định Wald $z = \hat{\gamma}_j / \text{SE}(\gamma_j)$ và giá trị $p$-value hai phía.
     - Khoảng tin cậy 95% CI cho tỷ trọng phần trăm tiềm ẩn $w_j\%$.
  4. **Ma Trận Xác Suất Thắng Đối Đầu Trực Diện (Pairwise Head-to-Head Win Probability Matrix):**
     - Theo Tiên đề Độc lập với các Phương án Không liên quan (IIA) của Luce (1959), xác suất phương án $j$ được ưu tiên hơn phương án $k$ khi so sánh trực diện hai lựa chọn là:
       $$P(j \succ k) = \frac{w_j}{w_j + w_k} = \frac{\exp(\gamma_j)}{\exp(\gamma_j) + \exp(\gamma_k)}$$
     - Thiết lập ma trận nhiệt đối đầu kích thước $M \times M$ phản ánh xác suất từ 0% đến 100%.
  5. **Đánh Giá Độ Phù Hợp Mô Hình (Model Goodness-of-Fit):**
     - Log-Likelihood mô hình đầy đủ $\ln L$.
     - Null Log-Likelihood (giả thuyết vô hiệu mọi phương án đều có giá trị bằng nhau $w_j = 1/M$): $\ln L_0 = -N \sum_{m=1}^{M-1} \ln(M - m + 1) = -N \ln(M!)$.
     - Hệ số xác định McFadden Pseudo-$R^2 = 1 - (\ln L / \ln L_0)$.
     - Kiểm định Tỷ số Hợp lý Likelihood Ratio $\text{LR} = 2(\ln L - \ln L_0) \sim \chi^2(M - 1)$.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/plackett-luce`
- **Request Body (`PlackettLuceRequest`):**
  - `ranking_question_id`: UUID của câu hỏi xếp hạng thứ tự chuyên biệt (tùy chọn).
  - `item_question_ids`: Danh sách UUID các câu hỏi đánh giá thuộc tính liên tục/thang đo rating (tùy chọn; hệ thống tự động suy diễn thứ bậc xếp hạng cho từng đáp viên dựa trên điểm số).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`PlackettLuceOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"PLACKETT_LUCE_RANK_ORDERED_LOGIT"`.
  - `diagnostics`: Cỡ mẫu $N$, số lượng phương án $M$, Log-Likelihood $\ln L$, Null Log-Likelihood $\ln L_0$, McFadden Pseudo-$R^2$, Thống kê LR Chi-square, Bậc tự do $\text{df} = M - 1$, $p$-value, Cờ hội tụ thuật toán `converged`.
  - `items`: Danh sách xếp hạng phương án: Thứ hạng, Tên phương án, Trọng số tiềm ẩn $w_j$, Tỷ trọng phần trăm tiềm ẩn ($w\%$), Hữu dụng Log-Worth $\gamma_j$, Sai số chuẩn SE, Thống kê $z$, Giá trị $p$, Khoảng tin cậy 95% CI [Lower, Upper].
  - `pairwise_win_matrix`: Ma trận đối đầu $M \times M$ chứa các xác suất thắng $P(\text{Row} \succ \text{Col})$.
  - `item_labels`: Danh sách nhãn phương án tương ứng với các hàng/cột ma trận.
  - `svg_visualization`: Biểu đồ SVG kép:
    - Panel A: Biểu đồ thanh ngang Latent Worth Share ($w\%$) với mã màu tương phản rực rỡ và giá trị phần trăm sắc nét.
    - Panel B: Ma trận nhiệt đối đầu trực diện $M \times M$ (Head-to-Head Win Probability Heatmap) với thang màu trực quan (Xanh lục đậm: Ưu thế áp đảo $> 70\%$, Xanh lục: $> 55\%$, Xám: Cân bằng $\approx 50\%$, Đỏ: Yếu thế $< 45\%$).
  - `apa_narrative`: Thuyết minh học thuật định dạng chuẩn APA 7th Edition theo lý thuyết Luce (1959), Beggs et al. (1981) và Hunter (2004).
- **Niêm phong kiểm toán:** Tự động ghi nhận `PLACKETT_LUCE_RANKING_CHOICE_EVALUATED` vào chuỗi sổ cái SHA-256.


---

## 105. Động Cơ Đo Lường Khoảng Cách Cực Đại MaxDiff (MaxDiff Best-Worst Scaling Case 1 - Finn & Louviere 1992; Marley & Louviere 2005)

- **Cơ sở khoa học:** Trong khảo sát thị trường, đánh giá mức độ hấp dẫn của tính năng sản phẩm hoặc ưu tiên phân bổ ngân sách, các câu hỏi đánh giá theo thang đo Likert truyền thống (1-5 sao, thang điểm 1-10) thường xuyên đối mặt với hiện tượng "thiên lệch thang đo" (Scale Usage Bias) và "hiệu ứng trần" (Ceiling Effects) — người trả lời có xu hướng đánh giá mọi phương án là "rất quan trọng" hoặc "hài lòng 5 sao", khiến việc nhận diện ưu tiên thực chất trở nên bất khả thi. MaxDiff (Maximum Difference Scaling / Best-Worst Scaling Case 1 - Finn & Louviere 1992; Marley & Louviere 2005) giải quyết triệt để hạn chế này bằng cách trình bày các tập hợp con gồm $K$ phương án và buộc đáp viên phải đưa ra sự đánh đổi dứt khoát: chọn chính xác 1 phương án Tốt nhất / Quan trọng nhất (Best) và 1 phương án Kém nhất / Ít quan trọng nhất (Worst). Phương pháp này tạo ra thước đo mức độ ưu tiên dạng thang tỷ lệ (Ratio-Scale) chuẩn mực học thuật, loại bỏ hoàn toàn các phong cách trả lời thiên lệch cá nhân hay văn hóa.
- **Phương pháp luận kinh tế lượng & lý thuyết lựa chọn ngẫu nhiên:**
  1. **Mô Hình Lựa Chọn Cực Đại Khác Biệt (MaxDiff Random Utility Model):**
     - Cho tập hợp phương án $S \subseteq \{1, \dots, M\}$ hiển thị trong một nhiệm vụ. Đáp viên chọn phương án $B \in S$ làm Best và phương án $W \in S$ làm Worst ($B \neq W$).
     - Giả định đáp viên tối đa hóa độ chênh lệch hữu dụng giữa Best và Worst ($U_B - U_W$). Theo mô hình phân phối Gumbel (Marley & Louviere 2005), xác suất chọn cặp $(B, W)$ từ tập hợp $S$ là:
       $$P(B, W | S) = \frac{\exp(\beta_B - \beta_W)}{\sum_{j \in S} \sum_{k \in S, j \neq k} \exp(\beta_j - \beta_k)}$$
     - Điều kiện nhận dạng (Identification Constraint): Cố định tổng các độ hữu dụng bằng 0: $\sum_{j=1}^M \beta_j = 0$.
  2. **Ước Lượng Hợp Lý Cực Đại Đa Thức (Multinomial Logit MLE; Orme 2009):**
     - Tối đa hóa hàm Log-Likelihood tổng thể trên toàn bộ $T$ nhiệm vụ đánh đổi bằng thuật toán L-BFGS-B:
       $$\ln L(\boldsymbol{\beta}) = \sum_{t=1}^T \left[ (\beta_{B_t} - \beta_{W_t}) - \ln\left( \sum_{j \in S_t} \sum_{k \in S_t, j \neq k} \exp(\beta_j - \beta_k) \right) \right]$$
     - Trích xuất ma trận thông tin Fisher quan sát thông qua Hessian số học để tính sai số chuẩn tiệm cận $\text{SE}(\beta_j)$, thống kê Wald $z = \hat{\beta}_j / \text{SE}(\beta_j)$, và giá trị $p$-value hai phía.
  3. **Thị Phần Ưu Tiên Chuẩn Hóa Dạng Thang Tỷ Lệ (Rescaled Preference Share $P_j\%$):**
     $$P_j = \frac{\exp(\beta_j)}{\sum_{k=1}^M \exp(\beta_k)} \times 100\%$$
     - Tính chất Thang Tỷ Lệ (Ratio-Scale): Tổng thị phần ưu tiên bằng chính xác $100.0\%$. Một phương án đạt $20\%$ có nghĩa là được người dùng mong muốn và lựa chọn nhiều gấp đúng 2 lần so với phương án đạt $10\%$.
  4. **Phân Tích Đếm Tần Suất Cơ Sở (First-Order Counting Analysis):**
     $$\text{Counting Score}_j = \frac{B_j - W_j}{A_j}$$
     trong đó $B_j$ là số lần được chọn Best, $W_j$ là số lần được chọn Worst, và $A_j$ là số lần xuất hiện của phương án $j$.
  5. **Lưới Phân Bổ Đánh Đổi Best vs Worst (Trade-Off Scatter Grid):**
     - Trục hoành $X$: Tỷ lệ được chọn Best ($\% B$).
     - Trục tung $Y$: Tỷ lệ được chọn Worst ($\% W$).
     - Phân định 4 vùng chiến lược:
       - **Ưu tiên Tuyệt đối (Universally Desired):** High Best, Low Worst (Góc dưới bên phải) — Thuộc tính được đa số thị trường khao khát; rủi ro từ chối cực thấp.
       - **Bị Từ chối (Consensus Rejection):** Low Best, High Worst (Góc trên bên trái) — Thuộc tính bị loại trừ rộng rãi; không nên đầu tư.
       - **Phân cực Tranh cãi (Polarizing / Divisive):** High Best, High Worst (Góc trên bên phải) — Nhóm khách hàng này cực kỳ thích nhưng nhóm khác lại cực kỳ ghét; phù hợp cho chiến lược ngách (Niche Segmentation).
       - **Trung lập / Thờ ơ (Indifferent / Low Salience):** Low Best, Low Worst (Góc dưới bên trái) — Thuộc tính không gây ấn tượng mạnh, ít tác động đến quyết định chung.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/maxdiff`
- **Request Body (`MaxDiffRequest`):**
  - `best_question_id`: UUID của câu hỏi chọn phương án Tốt nhất / Quan trọng nhất (tùy chọn).
  - `worst_question_id`: UUID của câu hỏi chọn phương án Kém nhất / Ít quan trọng nhất (tùy chọn).
  - `item_question_ids`: Danh sách UUID các câu hỏi đánh giá thuộc tính đa tiêu chí ($M \ge 3$; hệ thống tự động suy diễn cặp Best-Worst dựa trên giá trị cực đại và cực tiểu của từng đáp viên).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`MaxDiffOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"MAXDIFF_BEST_WORST_SCALING"`.
  - `diagnostics`: Số nhiệm vụ đánh đổi $T$, số phương án $M$, Log-Likelihood $\ln L$, Null Log-Likelihood $\ln L_0$, McFadden Pseudo-$R^2$, cờ hội tụ thuật toán `converged`.
  - `items`: Danh sách xếp hạng thuộc tính: Thứ hạng, Tên thuộc tính, Điểm hữu dụng thô $\beta_j$, Sai số chuẩn SE, Thống kê Wald $z$, Giá trị $p$, Thị phần ưu tiên chuẩn hóa ($P\%$), Số lần chọn Best, Số lần chọn Worst, Số lần xuất hiện, Tỷ lệ chọn Best ($\% B$), Tỷ lệ chọn Worst ($\% W$), Điểm đếm cơ sở $(B-W)/A$.
  - `svg_visualization`: Biểu đồ SVG kép:
    - Panel A: Biểu đồ thanh ngang Rescaled Preference Share ($P\%$) với mã màu phân cấp chiến lược (Xanh ngọc Emerald: Tier 1 $\ge 20\%$, Xanh lơ Cyan: Tier 2, Xám phiến: Tier 3).
    - Panel B: Lưới phân bổ đánh đổi Best vs Worst (Scatter Grid) với đường phân vị thập tự, đánh dấu 4 vùng chiến lược (Ưu tiên Tuyệt đối, Bị Từ chối, Phân cực Tranh cãi, Trung lập) và các điểm dữ liệu tròn phát sáng có nhãn tên thuộc tính.
  - `apa_narrative`: Thuyết minh học thuật định dạng chuẩn APA 7th Edition theo lý thuyết Finn & Louviere (1992), Marley & Louviere (2005) và Orme (2009).
- **Niêm phong kiểm toán:** Tự động ghi nhận `MAXDIFF_BEST_WORST_SCALING_EVALUATED` vào chuỗi sổ cái SHA-256.


### 106. Học Cấu Trúc Mạng Bayes Gaussian & Không Gian Độc Lập Markov Blanket (Gaussian Bayesian Network DAG Structure Learning - Heckerman 1995; Scutari 2010; Pearl 1988)
- **Nền tảng lý thuyết:**
  1. **Định Lý Phân Rã Mạng Bayes Gaussian (Gaussian Bayesian Network Factorization):**
     Hàm mật độ xác suất liên hiệp của tập $P$ biến ngẫu nhiên liên tục $\mathbf{X} = \{X_1, X_2, \dots, X_P\}$ được phân rã thành tích của các hàm mật độ có điều kiện cục bộ theo cấu trúc đồ thị có hướng không chu trình (Directed Acyclic Graph - DAG) $\mathcal{G}$:
     $$f(\mathbf{x}) = \prod_{j=1}^P f(x_j \mid \text{Pa}(X_j))$$
     trong đó $\text{Pa}(X_j)$ là tập hợp các nút cha trực tiếp (direct parents) của $X_j$ trong đồ thị $\mathcal{G}$. Đối với mạng Bayes Gaussian, mỗi biến $X_j$ tuân theo mô hình hồi quy tuyến tính cục bộ:
     $$X_j = \mu_j + \sum_{X_k \in \text{Pa}(X_j)} \beta_{jk} (X_k - \mu_k) + \epsilon_j, \quad \epsilon_j \sim \mathcal{N}(0, \sigma_j^2)$$
  2. **Tối Ưu Hóa Hàm Điểm BIC Bằng Thuật Toán Leo Đồi (Score-Based Hill-Climbing BIC Optimization):**
     - Đánh giá chất lượng của từng cấu trúc DAG ứng viên thông qua hàm điểm Tiêu chuẩn Thông tin Bayes (Bayesian Information Criterion - BIC; Schwarz 1978):
       $$\text{BIC}(\mathcal{G}) = \sum_{j=1}^P \left[ -\frac{N}{2} \ln(2\pi \hat{\sigma}_j^2) - \frac{N}{2} \right] - \frac{d}{2} \ln(N)$$
       trong đó $N$ là kích thước mẫu hợp lệ, $\hat{\sigma}_j^2$ là phương sai phần dư hồi quy của $X_j$ theo $\text{Pa}(X_j)$, và $d = \sum_{j=1}^P (1 + |\text{Pa}(X_j)|)$ là tổng số tham số độc lập của mô hình.
     - Khởi tạo từ đồ thị rỗng ($\mathcal{G}_0$). Tại mỗi bước lặp, thuật toán duyệt qua toàn bộ không gian biến đổi đồ thị cục bộ: thêm cạnh ($X_i \to X_j$), đảo ngược cạnh ($X_j \to X_i$), hoặc xóa cạnh ($X_i \to X_j$).
     - Áp dụng thuật toán sắp xếp tô-pô Kahn (Kahn 1962) để kiểm tra tính phi chu trình (Cycle Prevention) trong thời gian $O(V + E)$, đảm bảo đồ thị luôn là một DAG hợp lệ.
     - Thuật toán kết thúc khi không còn phép biến đổi nào làm tăng điểm BIC ($\Delta \text{BIC} \le 0$).
  3. **Ước Lượng Hệ Số Tác Động Chuẩn Hóa (Standardized Path Coefficients $\beta_{jk}^*$):**
     $$\beta_{jk}^* = \hat{\beta}_{jk} \cdot \frac{s_k}{s_j}$$
     biểu thị mức độ thay đổi theo độ lệch chuẩn của biến đích khi biến nguồn tăng thêm 1 độ lệch chuẩn, kiểm soát toàn bộ các nút cha đồng thời khác.
  4. **Phân Loại Vai Trò Tô-pô Đồ Thị (Topological Node Roles):**
     - **Nguyên nhân Gốc (Root Cause Node):** $\text{In-Degree} = 0, \text{Out-Degree} > 0$ — Biến số đầu vào độc lập, khởi phát chuỗi tác động trong hệ thống.
     - **Biến Trung gian / Điều phối (Mediator Node):** $\text{In-Degree} > 0, \text{Out-Degree} > 0$ — Chuyển tiếp và phân phối xung lực từ các biến gốc đến các biến kết quả.
     - **Biến Đích / Hấp thụ (Target Sink Node):** $\text{In-Degree} > 0, \text{Out-Degree} = 0$ — Kết quả cuối cùng bị tác động bởi toàn bộ hệ thống; không phát sinh hiệu ứng thứ cấp.
     - **Biến Độc lập (Isolated Node):** $\text{In-Degree} = 0, \text{Out-Degree} = 0$ — Không có tương quan phụ thuộc trực tiếp với các biến còn lại.
  5. **Xác Định Không Gian Markov Blanket (Markov Blanket Extraction; Pearl 1988):**
     $$\text{MB}(X) = \text{Pa}(X) \cup \text{Ch}(X) \cup \text{Sp}(X)$$
     trong đó $\text{Ch}(X)$ là tập hợp các nút con trực tiếp, và $\text{Sp}(X) = \{Z \in \text{Pa}(Y) \mid Y \in \text{Ch}(X), Z \neq X\}$ là tập hợp các "vợ/chồng" (co-parents/spouses).
     - **Tính chất Độc lập Có điều kiện (Conditional Independence):** Khi đã biết trước toàn bộ giá trị của các biến trong $\text{MB}(X)$, biến $X$ hoàn toàn độc lập có điều kiện với tất cả các biến còn lại trong toàn bộ mạng lưới khảo sát. Đây chính là tập hợp biến số can thiệp tối thiểu (minimal sufficient conditioning set) trong phân tích chính sách và tối ưu hóa trải nghiệm khách hàng.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/bayesian-network`
- **Request Body (`BayesianNetworkRequest`):**
  - `question_ids`: Danh sách UUID các câu hỏi thang đo số tham gia vào mạng lưới ($P \ge 2$).
  - `max_parents`: Số nút cha tối đa cho mỗi biến (Mặc định 3; giới hạn 1-5 nhằm tránh overfitting).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`BayesianNetworkOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"GAUSSIAN_BAYESIAN_NETWORK_DAG"`.
  - `diagnostics`: Kích thước mẫu $N$, số nút $P$, số cạnh có hướng, mật độ mạng (Graph Density), điểm BIC tối ưu, điểm BIC đồ thị rỗng, mức độ cải thiện điểm BIC ($\Delta \text{BIC}$ gain), và cờ phi chu trình `is_acyclic`.
  - `nodes`: Danh sách các nút: ID, nhãn tên, vai trò tô-pô, bậc vào (In-Degree), bậc ra (Out-Degree), danh sách biến cha, danh sách biến con, danh sách Markov Blanket.
  - `edges`: Danh sách các cạnh có hướng: Nút nguồn, nút đích, hệ số tác động chuẩn hóa $\beta$, phân loại quan hệ (Strong/Moderate Positive, Strong/Moderate Negative).
  - `svg_visualization`: Biểu đồ SVG kép:
    - Panel A: Đồ thị mạng có hướng (Directed DAG Network Layout) với các nút phát sáng theo vai trò tô-pô (Xanh ngọc cho Root Cause, Xanh lam cho Mediator, Hổ phách cho Target Sink) và mũi tên chỉ hướng với hệ số $\beta$.
    - Panel B: Bảng ma trận không gian Markov Blanket (Markov Blanket Matrix Table) trực quan hóa tập can thiệp độc lập có điều kiện.
  - `apa_narrative`: Thuyết minh học thuật định dạng chuẩn APA 7th Edition theo lý thuyết Heckerman (1995), Scutari (2010) và Pearl (1988).
- **Niêm phong kiểm toán:** Tự động ghi nhận `BAYESIAN_NETWORK_DAG_ESTIMATED` vào chuỗi sổ cái SHA-256.


### 107. Động Cơ Kiểm Định Vượt Trội Ngẫu Nhiên & Bất Bình Đẳng Phân Phối (Stochastic Dominance & Distributional Inequality Engine - Hadar & Russell 1969; Davidson & Duclos 2000; Barrett & Donald 2003)
- **Nền tảng lý thuyết:**
  1. **Định Lý Vượt Trội Ngẫu Nhiên Bậc 1 (First-Order Stochastic Dominance - FSD; Hadar & Russell 1969; Quirk & Saposnik 1962):**
     Cho hai phân phối tích lũy $F_A(y)$ và $F_B(y)$ trên miền giá trị $y \in [\underline{y}, \bar{y}]$ của thang đo khảo sát. Phân phối $A$ vượt trội ngẫu nhiên bậc 1 so với $B$ ($A \succeq_1 B$) khi và chỉ khi:
     $$F_A(y) \le F_B(y) \quad \forall y \in [\underline{y}, \bar{y}]$$
     với ít nhất một giá trị $y$ thỏa mãn bất đẳng thức ngặt.
     - **Ý nghĩa Kinh tế & Hành vi (Economic Interpretation):** Mọi cá nhân tối đa hóa hữu dụng kỳ vọng với hàm hữu dụng không giảm bất kỳ ($u'(y) \ge 0$, tức luôn mong muốn điểm đánh giá/chất lượng cao hơn) đều ưa thích phân phối $A$ hơn $B$:
       $$\mathbb{E}_A[u(Y)] \ge \mathbb{E}_B[u(Y)] \quad \forall u \in \mathcal{U}_1 = \{u: u' \ge 0\}$$
  2. **Định Lý Vượt Trội Ngẫu Nhiên Bậc 2 (Second-Order Stochastic Dominance - SSD; Rothschild & Stiglitz 1970):**
     Định nghĩa hàm diện tích tích lũy phần thiếu hụt:
     $$D_A^{(2)}(y) = \int_{\underline{y}}^y F_A(t) dt, \quad D_B^{(2)}(y) = \int_{\underline{y}}^y F_B(t) dt$$
     Phân phối $A$ vượt trội ngẫu nhiên bậc 2 so với $B$ ($A \succeq_2 B$) khi và chỉ khi:
     $$D_A^{(2)}(y) \le D_B^{(2)}(y) \quad \forall y \in [\underline{y}, \bar{y}]$$
     - **Tiêu chuẩn Né Tránh Rủi Ro (Risk Aversion Criterion):** Ngay cả khi hai phân phối có giá trị trung bình xấp xỉ nhau hoặc các đường CDF cắt nhau cục bộ, mọi người ra quyết định né tránh rủi ro ($u'(y) \ge 0$ và $u''(y) \le 0$) đều ưu tiên $A$ hơn $B$. $A$ mang lại sự an toàn cao hơn với rủi ro đuôi thấp (downside risk) nhỏ hơn đáng kể.
  3. **Định Lý Đường Cong Lorenz Khái Quát (Generalized Lorenz Dominance; Shorrocks 1983):**
     $$A \succeq_2 B \iff GL_A(p) \ge GL_B(p) \quad \forall p \in [0, 1]$$
     trong đó $GL(p) = \mu L(p)$ là đường cong Lorenz tổng quát kết hợp cả mức trung bình và mức độ bất bình đẳng (hệ số Gini).
  4. **Thống Kê Kiểm Định Cận Biên Kolmogorov-Smirnov & Davidson-Duclos (2000):**
     - Đánh giá khoảng cách phân phối cực đại hai phía:
       $$D_1^+ = \sup_{y} [F_B(y) - F_A(y)], \quad D_1^- = \sup_{y} [F_A(y) - F_B(y)]$$
     - Kiểm định hai mẫu Kolmogorov-Smirnov hai phía $D = \max(D_1^+, D_1^-)$ với giá trị $p$-value tiệm cận.
     - Lưới đánh giá $K$ điểm ngưỡng $y_1 < y_2 < \dots < y_K$ trên miền hỗ trợ chung của hai nhóm.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/stochastic-dominance`
- **Request Body (`StochasticDominanceRequest`):**
  - `outcome_question_id`: UUID của câu hỏi đo lường kết quả thang đo số (Likert, rating, điểm số).
  - `group_question_id`: UUID của câu hỏi phân nhóm (Phân khúc khách hàng, giới tính, vùng miền, hoặc can thiệp chính sách).
  - `group_a_value`: Giá trị định danh nhóm A (tùy chọn, hệ thống tự động suy diễn 2 nhóm phổ biến nhất nếu để trống).
  - `group_b_value`: Giá trị định danh nhóm B (tùy chọn).
  - `group_a_label`: Tên nhãn hiển thị trực quan cho Nhóm A.
  - `group_b_label`: Tên nhãn hiển thị trực quan cho Nhóm B.
  - `n_grid_points`: Số điểm lưới phân giải (Mặc định 50, dải 20-100).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`StochasticDominanceOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"STOCHASTIC_DOMINANCE_DAVIDSON_DUCLOS_2000"`.
  - `diagnostics`: Quy mô mẫu $N_A$ và $N_B$, Điểm trung bình Mean, Trung vị Median, Độ lệch chuẩn SD, Hệ số bất bình đẳng Gini của từng nhóm, Thống kê Kolmogorov-Smirnov $D$ và $p$-value, Kết luận vượt trội bậc 1 (FSD), bậc 2 (SSD), và bậc 3 (TSD).
  - `grid_thresholds`: Danh sách các điểm ngưỡng: Ngưỡng $y$, $F_A(y)$, $F_B(y)$, chênh lệch FSD $F_B - F_A$, diện tích tích phân $D_A^{(2)}$, $D_B^{(2)}$, và chênh lệch SSD $D_B^{(2)} - D_A^{(2)}$.
  - `svg_visualization`: Biểu đồ SVG kép:
    - Panel A: Hai đường cong hàm phân phối tích lũy CDF $F_A(y)$ (Xanh ngọc Emerald phát sáng) vs $F_B(y)$ (Tím Indigo) với đường nét đứt vàng cam đánh dấu khoảng cách vượt trội cực đại (Max Dominance Gap).
    - Panel B: Đường cong chênh lệch tích phân bậc 2 $\Delta D^{(2)}(y) = D_B^{(2)}(y) - D_A^{(2)}(y)$ với vùng bóng tô chuyển sắc màu xanh lục biểu thị miền thống trị né tránh rủi ro.
  - `apa_narrative`: Thuyết minh học thuật định dạng chuẩn APA 7th Edition theo lý thuyết Hadar & Russell (1969), Davidson & Duclos (2000), và Barrett & Donald (2003).
- **Niêm phong kiểm toán:** Tự động ghi nhận `STOCHASTIC_DOMINANCE_EVALUATED` vào chuỗi sổ cái SHA-256.

### 108. Động Cơ Ước Lượng Cận Manski & Xác Định Bán Phần Không Tham Số (Manski Non-Parametric Partial Identification & Worst-Case Bounds Engine - Manski 1990, 1995, 2003; Manski & Pepper 2000; Imbens & Manski 2004)
- **Nền tảng lý thuyết:**
  1. **Vấn Đề Cơ Bản của Suy Diễn Nhân Quả & Dữ Liệu Khuyết (Fundamental Problem of Causal Inference & Missing Data; Manski 1990):**
     Xét hiệu ứng can thiệp trung bình $ATE = \mathbb{E}[Y(1) - Y(0)]$. Trong các cuộc khảo sát thực tế, người trả lời thường bỏ qua câu hỏi nhạy cảm hoặc bỏ dở khảo sát (attrition / non-response), dẫn đến cơ chế khuyết không ngẫu nhiên (Not Missing At Random - NMAR).
     Các phương pháp truyền thống (hồi quy OLS, ghép cặp PSM, nội suy Mean/MICE) đều phải dựa vào giả định MAR bất khả kiểm chứng ($Y \perp R \mid X$). Nếu giả định này vi phạm, ước lượng điểm ngây thơ $\text{Naive } ATE = \mathbb{E}[Y \mid D=1, R=1] - \mathbb{E}[Y \mid D=0, R=1]$ sẽ bị chệch nghiêm trọng.
  2. **Phân Cấp Xác Định Bán Phần 4 Bậc (4-Tier Identification Hierarchy):**
     - **Bậc 1: Cận Tồi Tệ Nhất Không Giả Định (Worst-Case / No-Assumption Bounds; Manski 1990):**
       Giả sử biến kết quả bị chặn trong miền hữu hạn $Y \in [y_{\min}, y_{\max}]$. Với xác suất phản hồi $P(R=1 \mid D=d) = p_d$:
       $$\mathbb{E}[Y(d)] \in [p_d \mathbb{E}[Y \mid D=d, R=1] + (1 - p_d) y_{\min}, \; p_d \mathbb{E}[Y \mid D=d, R=1] + (1 - p_d) y_{\max}]$$
       Hiệu ứng can thiệp $ATE = \mathbb{E}[Y(1)] - \mathbb{E}[Y(0)]$ được chặn bởi:
       $$LB_{\text{worst}} = \mathbb{E}[Y(1)]_{\min} - \mathbb{E}[Y(0)]_{\max}, \quad UB_{\text{worst}} = \mathbb{E}[Y(1)]_{\max} - \mathbb{E}[Y(0)]_{\min}$$
     - **Bậc 2: Tiên Đề Lựa Chọn Điều Trị Đơn Điệu (Monotone Treatment Selection - MTS; Manski & Pepper 2000):**
       Giả định nhóm tự nguyện tham gia can thiệp có giá trị tiềm năng trung bình không thấp hơn nhóm đối chứng: $\mathbb{E}[Y(d) \mid D=1] \ge \mathbb{E}[Y(d) \mid D=0]$.
       Hệ quả: $ATE \le \mathbb{E}[Y \mid D=1] - \mathbb{E}[Y \mid D=0]$, thu hẹp cận trên xuống bằng Naive ATE:
       $$[LB_{\text{worst}}, \; \text{Naive } ATE]$$
     - **Bậc 3: Tiên Đề Đáp Ứng Đơn Điệu (Monotone Treatment Response - MTR; Manski 1997):**
       Giả định can thiệp chính sách chỉ mang lại tác động tích cực hoặc trung tính lên từng cá thể: $Y_i(1) \ge Y_i(0) \implies ATE \ge 0$.
       Hệ quả: Cận dưới được nâng lên $\max(0, LB_{\text{worst}})$:
       $$[\max(0, LB_{\text{worst}}), \; UB_{\text{worst}}]$$
     - **Bậc 4: Cận Hợp Nhất MTS + MTR (Joint Bounds; Manski & Pepper 2000):**
       Kết hợp đồng thời hai tiên đề MTS và MTR:
       $$ATE \in [0, \; \min(UB_{\text{worst}}, \text{Naive } ATE)]$$
  3. **Khoảng Tin Cậy Đồng Nhất Imbens & Manski (2004):**
     Khoảng tin cậy cho tham số được xác định bán phần $\theta \in [\theta_L, \theta_U]$ giải phương trình chuẩn hóa với bậc tin cậy $1 - \alpha$:
     $$\Phi\left(c_\alpha + \frac{\sqrt{N}(\hat{\theta}_U - \hat{\theta}_L)}{\max(\hat{\sigma}_L, \hat{\sigma}_U)}\right) - \Phi(-c_\alpha) = 1 - \alpha$$
     Được giải chính xác bằng phương pháp chia đôi (Bisection Search), tạo ra khoảng $CI_{1-\alpha} = [\hat{\theta}_L - c_\alpha \frac{\hat{\sigma}_L}{\sqrt{N}}, \; \hat{\theta}_U + c_\alpha \frac{\hat{\sigma}_U}{\sqrt{N}}]$.
  4. **Điểm Gãy Dấu (Sign Breakdown Point Analysis; Horowitz & Manski 2000):**
     Mô phỏng quỹ đạo biên dưới $[LB(p), UB(p)]$ khi tỷ lệ mất mẫu $p$ quét từ $0\%$ đến $50\%$. Điểm gãy dấu $p^*$ là ngưỡng tỷ lệ mất mẫu tối đa mà tại đó dấu của hiệu ứng can thiệp ($LB(p) > 0$) vẫn được khẳng định chắc chắn.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/manski-bounds`
- **Request Body (`ManskiBoundsRequest`):**
  - `outcome_question_id`: UUID của câu hỏi đo lường kết quả $Y$.
  - `treatment_question_id`: UUID của câu hỏi can thiệp $D$ (phân loại nhóm 1 vs 0).
  - `response_indicator_question_id`: UUID của câu hỏi chỉ thị phản hồi $R$ (tùy chọn, hệ thống tự động phát hiện câu trả lời khuyết).
  - `support_min`: Cận dưới lý thuyết $y_{\min}$ (tùy chọn, tự động tính từ min mẫu).
  - `support_max`: Cận trên lý thuyết $y_{\max}$ (tùy chọn, tự động tính từ max mẫu).
  - `confidence_level`: Mức tin cậy (Mặc định 0.95).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`ManskiBoundsOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"MANSKI_PARTIAL_IDENTIFICATION_BOUNDS_2000"`.
  - `diagnostics`: Quy mô mẫu tổng $N$, $N_{\text{treated}}$, $N_{\text{control}}$, số quan sát non-missing, tỷ lệ khuyết mẫu $p$, Naive ATE, các cận dưới/trên Worst-Case, MTS, MTR, Joint MTS+MTR, khoảng tin cậy Imbens-Manski 95%, Điểm gãy dấu (Breakdown Rate), cờ xác định dấu (`is_sign_identified`).
  - `tiers`: Danh sách 4 bậc phân cấp xác định (Tên bậc, Cận dưới, Cận trên, Độ rộng biên).
  - `sensitivity_grid`: 15 điểm quét tỷ lệ mất mẫu $p \in [0, 0.50]$ với cận trên và cận dưới tương ứng.
  - `svg_visualization`: Đồ thị SVG khoa học kép:
    - Panel A: Các thanh ngang phân cấp biên Manski (Worst-Case, MTS, MTR, Joint) và vạch đỏ ngắt quãng chỉ Naive ATE.
    - Panel B: Đồ thị diện tích chuyển sắc biểu diễn đường ống phong bì xác định (Envelope $[LB(p), UB(p)]$) và vòng tròn vàng đánh dấu Điểm gãy dấu (Sign Breakdown Point).
  - `apa_narrative`: Thuyết minh học thuật định dạng chuẩn APA 7th Edition theo lý thuyết Manski (1990, 2000) và Imbens & Manski (2004).
- **Niêm phong kiểm toán:** Tự động ghi nhận `MANSKI_BOUNDS_EVALUATED` vào chuỗi sổ cái SHA-256.

### 109. Động Cơ Chế Độ Can Thiệp Động Đa Giai Đoạn & Q-Learning Tối Ưu Hóa Chính Sách Thích Ứng (Dynamic Treatment Regimes (DTR) & Sequential Q-Learning Decision Engine - Murphy 2003; Robins 2004; Schulte et al. 2014)
- **Nền tảng lý thuyết:**
  1. **Quy Trình Quyết Định Chuỗi Thích Ứng Cá Nhân Hóa (Sequential Adaptive Decisions in Longitudinal Campaigns; Murphy 2003):**
     Trong các chiến dịch khảo sát kéo dài, nghiên cứu can thiệp xã hội, hay chương trình giữ chân người dùng nhiều giai đoạn, các can thiệp không diễn ra đồng thời một lần mà phân bổ nối tiếp:
     - Giai đoạn 1 (Stage 1): Can thiệp ban đầu $A_1 \in \{0, 1\}$ dựa trên đặc điểm nền tảng $H_1 = (1, X_1)$.
     - Giai đoạn chuyển tiếp (Interim State): Đo lường sự thay đổi hành vi/tiến độ $X_2$ (ví dụ: mức độ tương tác giữa kỳ, độ trễ phản hồi, hoặc điểm số hài lòng sơ bộ). Lịch sử giai đoạn 2 trở thành $H_2 = (1, X_1, A_1, X_2)$.
     - Giai đoạn 2 (Stage 2): Can thiệp thích ứng tiếp theo $A_2 \in \{0, 1\}$ dựa trên toàn bộ lịch sử $H_2$.
     - Kết quả cuối kỳ (Terminal Outcome): $Y$ đo lường tại thời điểm hoàn tất (chỉ số tin cậy số, lòng trung thành, hay hiệu quả chính sách dài hạn).
     Một Chế Độ Can Thiệp Động (Dynamic Treatment Regime - DTR) là một chuỗi quy tắc quyết định $d = (d_1, d_2)$ trong đó $d_1: \mathcal{H}_1 \to \mathcal{A}_1$ và $d_2: \mathcal{H}_2 \to \mathcal{A}_2$.
  2. **Thuật Toán Q-Learning Quy Nạp Ngược (Backward Induction; Watkins 1989; Murphy 2003; Schulte et al. 2014):**
     - **Bước 1: Hồi quy Hàm Q Giai đoạn 2 ($Q_2$-function):**
       $$Q_2(H_2, A_2; \beta_2) = \mathbb{E}[Y \mid H_2, A_2] = H_2^\top \gamma_2 + A_2 (\beta_{21} + \theta_{21} X_2)$$
       Quy tắc quyết định tối ưu giai đoạn 2:
       $$d_2^*(H_2) = \arg\max_{a_2 \in \{0, 1\}} Q_2(H_2, a_2) = \mathbb{I}(\beta_{21} + \theta_{21} X_2 > 0)$$
       Ngưỡng thích ứng giai đoạn 2: $X_2^* = -\beta_{21} / \theta_{21}$.
       Giá trị tiềm năng phản thực tối ưu cho giai đoạn 1 (Pseudo-Outcome):
       $$\tilde{Y}_1 = \max_{a_2 \in \{0, 1\}} Q_2(H_2, a_2)$$
     - **Bước 2: Hồi quy Hàm Q Giai đoạn 1 ($Q_1$-function):**
       Hồi quy biến kết quả ảo $\tilde{Y}_1$ lên lịch sử ban đầu $H_1$ và hành động $A_1$:
       $$Q_1(H_1, A_1; \beta_1) = \mathbb{E}[\tilde{Y}_1 \mid H_1, A_1] = H_1^\top \gamma_1 + A_1 (\beta_{11} + \theta_{11} X_1)$$
       Quy tắc quyết định tối ưu giai đoạn 1:
       $$d_1^*(H_1) = \arg\max_{a_1 \in \{0, 1\}} Q_1(H_1, a_1) = \mathbb{I}(\beta_{11} + \theta_{11} X_1 > 0)$$
       Ngưỡng phân bổ ban đầu: $X_1^* = -\beta_{11} / \theta_{11}$.
  3. **Ước Lượng Giá Trị Kỳ Vọng Của Chính Sách (Policy Value $V(d)$) & Thặng Dư Giá Trị ($\Delta V^*$):**
     - Giá trị của chính sách thích ứng tối ưu:
       $$\hat{V}(d^*) = \frac{1}{N} \sum_{i=1}^N \max_{a_1} Q_1(H_{1i}, a_1)$$
     - So sánh đối chứng với các chính sách tĩnh truyền thống:
       - Luôn can thiệp cả hai kỳ: $\hat{V}(1, 1) = \frac{1}{N} \sum Q_1(H_{1i}, 1)$.
       - Không can thiệp cả hai kỳ: $\hat{V}(0, 0) = \frac{1}{N} \sum Q_1(H_{1i}, 0)$.
       - Trung bình quan sát thực tế: $\hat{V}_{\text{obs}} = \frac{1}{N} \sum Y_i$.
     - Mức thặng dư giá trị chính sách: $\Delta V^* = \hat{V}(d^*) - \hat{V}(0, 0)$.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/dynamic-treatment-regimes`
- **Request Body (`DynamicTreatmentRegimesRequest`):**
  - `outcome_question_id`: UUID câu hỏi đo lường kết quả cuối kỳ $Y$.
  - `stage1_action_question_id`: UUID câu hỏi hành động can thiệp $A_1$ (nhị phân 1 vs 0).
  - `stage2_action_question_id`: UUID câu hỏi hành động can thiệp $A_2$ (nhị phân 1 vs 0).
  - `baseline_covariate_question_id`: UUID biến đo lường nền tảng $X_1$ (điều chỉnh Stage 1).
  - `interim_state_question_id`: UUID biến trạng thái giữa kỳ $X_2$ (điều chỉnh Stage 2).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`DynamicTreatmentRegimesOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"DYNAMIC_TREATMENT_REGIMES_Q_LEARNING_2003"`.
  - `diagnostics`: Quy mô mẫu hợp lệ $N$, Giá trị chính sách tối ưu $V(d^*)$, $V(1,1)$, $V(0,0)$, $V_{\text{obs}}$, Thặng dư giá trị chính sách $\Delta V^*$, Tỷ lệ phần trăm thặng dư $\Delta V^*\%$, Tỷ lệ can thiệp khuyến nghị ở Stage 1 và Stage 2, Ngưỡng quyết định $X_1^*$ và $X_2^*$.
  - `stage1_model`: Hệ số chặn Intercept, Main $X_1$, Main $A_1$, Hệ số tương tác $A_1 \times X_1$, Sai số chuẩn SE, Thống kê $t$-stat, $p$-value, $R^2$.
  - `stage2_model`: Hệ số chặn Intercept, Main $X_1$, Main $A_1$, Main $X_2$, Main $A_2$, Hệ số tương tác $A_2 \times X_2$, Sai số chuẩn SE, Thống kê $t$-stat, $p$-value, $R^2$.
  - `svg_visualization`: Đồ thị SVG khoa học kép:
    - Panel A: Sơ đồ Cây Quyết Định Thích Ứng (DTR Flowchart Tree) nối từ nút gốc Stage 1 $X_1$ sang hai nhánh $A_1$, qua trạng thái giữa kỳ $X_2$, rẽ nhánh Stage 2 $A_2$, và hội tụ tại 4 điểm payoff cuối cùng.
    - Panel B: Biểu đồ thanh ngang so sánh Giá trị Kỳ vọng Chính sách ($V(d^*)$ xanh ngọc Emerald nổi bật vs $V(1,1)$ Indigo, $V_{\text{obs}}$ Sky Blue, và $V(0,0)$ Slate) kèm hộp nổi bật $\Delta V^*$.
  - `apa_narrative`: Thuyết minh học thuật định dạng chuẩn APA 7th Edition theo lý thuyết Murphy (2003), Robins (2004), và Schulte et al. (2014).
- **Niêm phong kiểm toán:** Tự động ghi nhận `DYNAMIC_TREATMENT_REGIMES_EVALUATED` vào chuỗi sổ cái SHA-256.

### 110. Động Cơ Mô Hình Rasch Hỗn Hợp Hữu Hạn & IRT Phân Lớp Tiềm Ẩn (Finite Mixture Rasch Models (FMRM) & Latent Class IRT Engine - Rost 1990; von Davier & Rost 2007; Glas 2010)
- **Nền tảng lý thuyết:**
  1. **Vấn Đề Không Đồng Nhất Tiềm Ẩn trong Đo Lường Tâm Lý Học (Unobserved Heterogeneity in Psychometrics; Rost 1990):**
     Các mô hình Rasch truyền thống (1PL) giả định toàn bộ mẫu đáp viên thuộc về một tổng thể đơn nhất với tập tham số độ khó câu hỏi $\beta_i$ không đổi. Tuy nhiên, trong khảo sát thực tế, đáp viên thường chia thành các phân lớp tiềm ẩn (Latent Classes $g \in \{1, \dots, G\}$) với các phong cách phản hồi khác biệt:
     - Nhóm Đánh giá Khắt khe (Critical Evaluators): Độ khó của toàn bộ các câu hỏi chất lượng cao hơn đáng kể.
     - Nhóm Dễ dãi / Đồng thuận cao (Acquiescent Evaluators): Xu hướng đánh giá cao, độ khó thấp.
     - Nhóm Ưu tiên Thuộc tính Chuyên biệt (Dimension-Specific Evaluators): Giao diện kỹ thuật hay chính sách giá có độ khó tương đối phân hóa sâu sắc so với nhóm còn lại (Differential Item Functioning - DIF nội sinh).
  2. **Mô Hình Rasch Hỗn Hợp Hữu Hạn (FMRM Formulation):**
     Cho $X_{vi} \in \{0, 1\}$ là phản hồi nhị phân của người $v$ đối với câu hỏi $i$ ($i = 1, \dots, I$). Xác suất phản hồi có điều kiện theo phân lớp tiềm ẩn $g$:
     $$P(X_{vi} = 1 \mid \theta_v, g) = \frac{\exp(\theta_v - \beta_{ig})}{1 + \exp(\theta_v - \beta_{ig})}$$
     với điều kiện nhận dạng chuẩn định tâm tham số trong từng phân lớp: $\sum_{i=1}^I \beta_{ig} = 0$.
     Xác suất hợp lý hỗn hợp của toàn bộ vector câu trả lời $\mathbf{x}_v$:
     $$P(\mathbf{x}_v) = \sum_{g=1}^G \pi_g P(\mathbf{x}_v \mid g)$$
     trong đó $\pi_g > 0$ và $\sum_{g=1}^G \pi_g = 1$ là tỷ trọng thành phần hỗn hợp (Mixing Proportions).
  3. **Thuật Toán Kỳ Vọng - Cực Đại Hóa (Expectation-Maximization - EM):**
     - **Bước E (Expectation Step):** Tính toán xác suất hậu nghiệm thuộc phân lớp $g$ cho từng đáp viên:
       $$\hat{\tau}_{vg} = P(g \mid \mathbf{x}_v) = \frac{\pi_g P(\mathbf{x}_v \mid g)}{\sum_{k=1}^G \pi_k P(\mathbf{x}_v \mid k)}$$
     - **Bước M (Maximization Step):** Cập nhật tỷ trọng phân lớp $\hat{\pi}_g = \frac{1}{N} \sum_{v=1}^N \hat{\tau}_{vg}$ và giải hệ phương trình Rasch trọng số cập nhật tham số độ khó $\beta_{ig}$ sao cho bảo toàn $\sum_i \beta_{ig} = 0$.
     - Lặp cho đến khi hàm hợp lý logarit hội tụ $|\Delta \ln L| < 10^{-4}$.
  4. **Tiêu Chuẩn Lựa Chọn Mô Hình & Chỉ Số Phân Tách Entropy:**
     - Tiêu chuẩn Thông tin: $AIC = -2 \ln L + 2K$, $BIC = -2 \ln L + K \ln N$, $aBIC = -2 \ln L + K \ln((N+2)/24)$ với số bậc tự do $K = (G - 1) + G(I - 1)$.
     - Chỉ số Phân tách Entropy Chuẩn hóa:
       $$E = 1 - \frac{\sum_{v=1}^N \sum_{g=1}^G -\hat{\tau}_{vg} \ln \hat{\tau}_{vg}}{N \ln G} \in [0, 1]$$
       $E \ge 0.80$ biểu thị chất lượng phân tách xuất sắc; $E \ge 0.60$ biểu thị chất lượng phân lớp tốt.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/finite-mixture-rasch`
- **Request Body (`FiniteMixtureRaschRequest`):**
  - `question_ids`: Danh sách UUID các câu hỏi thang đo khảo sát (tối thiểu 3 câu hỏi).
  - `n_classes`: Số lượng phân lớp tiềm ẩn cần phân rã (Mặc định 2, dải 2-4).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`FiniteMixtureRaschOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"FINITE_MIXTURE_RASCH_ROST_1990"`.
  - `diagnostics`: Quy mô mẫu hợp lệ $N$, số câu hỏi $I$, số phân lớp $G$, Hợp lý cực đại log-likelihood, AIC, BIC, aBIC, Chỉ số Entropy, Cờ chất lượng phân tách (`is_well_separated`), Câu hỏi có độ phân hóa mạnh nhất (`top_shifted_item`) và biên độ dịch chuyển cực đại $\Delta \beta_{\max}$.
  - `class_proportions`: Danh sách tỷ trọng phần trăm từng phân lớp $\pi_g\%$.
  - `items_parameters`: Bảng tham số độ khó câu hỏi theo từng phân lớp ($\beta_{i1}, \beta_{i2}, \dots$) và độ dịch chuyển cực đại $\Delta \beta_i$.
  - `svg_visualization`: Đồ thị SVG khoa học kép:
    - Panel A: Biểu đồ đường quỹ đạo độ khó câu hỏi qua các phân lớp tiềm ẩn (Item Difficulty Profiles $\beta_{ig}$) phân biệt bằng các đường phát sáng màu sắc khác nhau.
    - Panel B: Biểu đồ thanh tỷ trọng phân lớp và hộp đo chỉ số Entropy phân tách.
  - `apa_narrative`: Thuyết minh học thuật định dạng chuẩn APA 7th Edition theo lý thuyết Rost (1990) và von Davier & Rost (2007).
- **Niêm phong kiểm toán:** Tự động ghi nhận `FINITE_MIXTURE_RASCH_EVALUATED` vào chuỗi sổ cái SHA-256.

### 111. Động Cơ Học Máy Khử Thiên Lệch Hai Bước Ước Lượng Tác Động Nhân Quả (Double / Debiased Machine Learning (DML) for Causal Inference Engine - Chernozhukov et al. 2018; Robinson 1988)
- **Nền tảng lý thuyết:**
  1. **Vấn Đề Thiên Lệch Chính Quy Hóa trong Học Máy Nhân Quả (Regularization Bias in Causal Machine Learning; Chernozhukov et al. 2018):**
     Khi ước lượng hiệu ứng can thiệp nhân quả $\theta_0$ của một chính sách / tính năng khảo sát $D$ lên kết quả $Y$ trong bối cảnh có nhiều biến kiểm soát gây nhiễu chiều cao $X \in \mathbb{R}^p$ (Mô hình Bán tham số Tuyến tính từng phần Partially Linear Regression - PLR):
     $$Y = D \theta_0 + g_0(X) + U, \quad \mathbb{E}[U \mid D, X] = 0$$
     $$D = m_0(X) + V, \quad \mathbb{E}[V \mid X] = 0$$
     Nếu trực tiếp cắm (plug-in) các mô hình học máy chính quy hóa (Lasso, Ridge, Random Forest, Gradient Boosting) để ước lượng hàm phụ trợ $g_0(X) = \mathbb{E}[Y \mid X]$ và đưa vào OLS, sai số làm mịn / co tham số (regularization bias) sẽ làm sai lệch ước lượng $\hat{\theta}$, phá hủy tính hội tụ $\sqrt{N}$-consistent và khiến khoảng tin cậy tiệm cận thất bại nghiêm trọng.
  2. **Hai Trụ Cột Đột Phá Của Chernozhukov et al. (2018):**
     - **Trụ Cột 1: Điểm Trực Giao Neyman (Neyman Orthogonal Scores; Robinson 1988):**
       Thiết lập điều kiện mô-men $\psi(W; \theta, \eta)$ thỏa mãn đạo hàm Gateaux theo các hàm phụ trợ $\eta = (g, m)$ triệt tiêu tại giá trị thực:
       $$\partial_\eta \mathbb{E}[\psi(W; \theta_0, \eta_0)] = 0$$
       Hàm điểm trực giao thặng dư Robinson (1988):
       $$\psi(W; \theta, g, m) = (Y - g(X) - \theta (D - m(X))) (D - m(X))$$
       Đưa đến công thức ước lượng DML giải tích đóng:
       $$\hat{\theta}_{\text{DML}} = \frac{\sum_{i=1}^N (D_i - \hat{m}(X_i)) (Y_i - \hat{g}(X_i))}{\sum_{i=1}^N (D_i - \hat{m}(X_i))^2}$$
     - **Trụ Cột 2: Phân Mẫu Chéo Ngoài Mẫu (K-Fold Cross-Fitting):**
       Chia ngẫu nhiên tập dữ liệu thành $K$ phần (ví dụ $K = 5$). Với mỗi phần $k$, các hàm phụ trợ $\hat{g}_{-k}$ và $\hat{m}_{-k}$ được huấn luyện trên $K-1$ phần còn lại, sau đó dự báo thặng dư trên phần $k$. Điều này triệt tiêu hoàn toàn hiện tượng overfitting và bảo đảm phân phối chuẩn tiệm cận:
       $$\sqrt{N} (\hat{\theta}_{\text{DML}} - \theta_0) \xrightarrow{d} \mathcal{N}\left(0, \frac{\mathbb{E}[\psi^2]}{(\mathbb{E}[(D - m(X))^2])^2}\right)$$
       ngay cả khi các mô hình học máy phi tham số $g, m$ chỉ hội tụ ở tốc độ chậm $N^{-1/4}$.
  3. **Phân Tích So Sánh Khử Thiên Lệch (Debiasing Decomposition):**
     So sánh trực diện $\hat{\theta}_{\text{DML}}$ với hồi quy OLS ngây thơ $\hat{\theta}_{\text{naive}}$ (chưa kiểm soát trực giao) để đo lường định lượng mức độ thiên lệch gây nhiễu (Confounding Bias $\Delta = \hat{\theta}_{\text{naive}} - \hat{\theta}_{\text{DML}}$) đã được làm sạch khỏi ước lượng chính sách.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/double-machine-learning`
- **Request Body (`DoubleMachineLearningRequest`):**
  - `outcome_question_id`: UUID câu hỏi đo lường kết quả $Y$.
  - `treatment_question_id`: UUID câu hỏi can thiệp $D$ (nhị phân 1 vs 0 hoặc liên tục).
  - `covariate_question_ids`: Danh sách UUID các biến kiểm soát $X_1, \dots, X_p$.
  - `n_folds`: Số lượng folds cross-fitting (Mặc định 5, dải 2-10).
  - `alpha_penalty`: Hệ số phạt chính quy hóa L2 Ridge (Mặc định 1.0).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`DoubleMachineLearningOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"DOUBLE_MACHINE_LEARNING_CHERNOZHUKOV_2018"`.
  - `diagnostics`: Quy mô mẫu hợp lệ $N$, số biến kiểm soát $P$, số folds $K$, Ước lượng tác động DML $\hat{\theta}_{\text{DML}}$, Sai số chuẩn SE, Thống kê $z$-statistic, $p$-value, Khoảng tin cậy 95% CI, Hệ số OLS ngây thơ $\hat{\theta}_{\text{naive}}$, Mức thiên lệch gây nhiễu được triệt tiêu, $R^2(Y \mid X)$ và $R^2(D \mid X)$ của các mô hình học máy phụ trợ, Cờ ý nghĩa thống kê (`is_statistically_significant`).
  - `confounding_covariates`: Bảng xếp hạng các biến gây nhiễu mạnh nhất theo tích số tương quan với $Y$ và $D$.
  - `svg_visualization`: Đồ thị SVG khoa học kép:
    - Panel A: Đám mây thặng dư trực giao Robinson $(Y - \hat{g}(X))$ vs $(D - \hat{m}(X))$ với đường dốc hồi quy DML $\hat{\theta}_{\text{DML}}$ màu xanh ngọc Emerald phát sáng.
    - Panel B: Biểu đồ Forest Plot so sánh khoảng tin cậy 95% của $\hat{\theta}_{\text{DML}}$ vs $\hat{\theta}_{\text{naive}}$ kèm hộp làm nổi bật độ chệch được loại bỏ.
  - `apa_narrative`: Thuyết minh học thuật định dạng chuẩn APA 7th Edition theo lý thuyết Chernozhukov et al. (2018) và Robinson (1988).
- **Niêm phong kiểm toán:** Tự động ghi nhận `DOUBLE_MACHINE_LEARNING_EVALUATED` vào chuỗi sổ cái SHA-256.

### 112. Regression Kink Design (RKD) Engine (Card, Lee, Pei, & Weber 2015; Dong 2018)
- **Lý thuyết nền tảng:**
  1. **Nhận diện Nhân quả tại Điểm Gãy Độ Dốc (Causal Derivative Identification):**
     - Thiết kế Đứt đoạn Hồi quy truyền thống (Sharp / Fuzzy RDD) đòi hỏi một bước nhảy cấp số (discontinuity in levels) tại điểm ngưỡng $c$ ($\Delta D(c) \neq 0$). Tuy nhiên trong thực tiễn khảo sát chính sách kinh tế - xã hội (thuế suất lũy tiến theo bậc thu nhập, chính sách trợ cấp xã hội giảm dần theo thang đo, các chương trình hỗ trợ học phí hoặc bảo hiểm y tế), can thiệp không làm thay đổi gián đoạn cấp độ mà chỉ làm thay đổi tỷ lệ thay đổi (độ dốc / marginal slope):
       $$\lim_{x \downarrow c} D(x) = \lim_{x \uparrow c} D(x) = D(c)$$
     - Tại ngưỡng $c$, RDD truyền thống gặp mẫu số bằng 0 ($0 / 0$) và thất bại hoàn toàn.
     - Card, Lee, Pei, & Weber (2015) và Dong (2018) đã chứng minh rằng đạo hàm hiệu ứng xử lý biên (Marginal Treatment Effect Derivative $\tau_{\text{RKD}}$) được nhận diện phi tham số qua tỷ số giữa độ gãy dốc của hàm kết quả và hàm can thiệp:
       $$\tau_{\text{RKD}} = \frac{\lim_{x \downarrow c} \frac{d\mathbb{E}[Y \mid X=x]}{dx} - \lim_{x \uparrow c} \frac{d\mathbb{E}[Y \mid X=x]}{dx}}{\lim_{x \downarrow c} \frac{d\mathbb{E}[D \mid X=x]}{dx} - \lim_{x \uparrow c} \frac{d\mathbb{E}[D \mid X=x]}{dx}} = \frac{\Delta \beta_Y}{\Delta \beta_D}$$
       Đối với Sharp RKD (khi độ gãy của can thiệp đã biết, e.g. $\Delta \beta_D = k = 1.0$), $\tau_{\text{RKD}} = \Delta \beta_Y / k$. Đối với Fuzzy RKD, $\Delta \beta_D$ được ước lượng đồng thời qua hồi quy biến công cụ bán thực nghiệm.
  2. **Thuật Toán Cốt Lõi Trong Engine:**
     - **Ước lượng Hồi quy Đa thức Cục bộ (Local Polynomial Spline Regression):** Ước lượng spline liên tục tại ngưỡng $c$ với hàm trọng số nhân tam giác (triangular kernel $K(u) = (1 - |u|) \mathbf{1}(|u| \le 1)$) trong dải băng thông $[c - h, c + h]$. Hỗ trợ cả bậc 1 (Local Linear Spline) và bậc 2 (Local Quadratic Spline) theo khuyến nghị của Gelman & Imbens (2019).
     - **Băng thông Thích ứng Đạo hàm (Silverman ROT Bandwidth for First Derivatives):** Tự động lựa chọn băng thông tối ưu giải tích thích ứng riêng cho bài toán ước lượng độ dốc bậc 1: $h = C \cdot \sigma_X \cdot N^{-1/(2p + 3)}$.
     - **Kiểm định Mật độ Trơn McCrary (2008):** Chia dữ liệu thành các bin nhỏ đối xứng hai bên ngưỡng $c$ và kiểm tra tính liên tục của hàm mật độ xác suất biến gán chạy $f_X(c)$. Kiểm định này giúp loại trừ giả thuyết đối tượng khảo sát tự lựa chọn hoặc thao túng có chọn lọc vị trí của mình quanh ngưỡng gãy.
     - **Đồ thị SVG Kép Bán Thực Nghiệm:**
       - Panel A: Đồ thị spline gãy cục bộ kèm dải tin cậy 95% và các điểm gom phân tán (Local Binned Scatter) phân biệt màu sắc hai bên ngưỡng.
       - Panel B: Biểu đồ kiểm định mật độ trơn McCrary (2008) trực quan hóa tần suất quan sát và đường tiệm cận mật độ xác suất.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/regression-kink`
- **Request Body (`RegressionKinkRequest`):**
  - `outcome_question_id`: UUID câu hỏi đo lường biến kết quả $Y$.
  - `running_question_id`: UUID câu hỏi đo lường biến gán chạy $X$.
  - `cutoff`: Điểm ngưỡng gãy $c$ của chính sách.
  - `treatment_question_id`: UUID biến can thiệp thực tế $D$ (Tùy chọn, để trống cho Sharp RKD, cung cấp cho Fuzzy RKD).
  - `bandwidth`: Băng thông $h$ cục bộ (Tùy chọn, tự động tính bằng Silverman ROT nếu bỏ trống).
  - `polynomial_order`: Bậc đa thức cục bộ (1: Tuyến tính, 2: Bậc hai).
  - `known_kink_slope`: Độ thay đổi độ dốc chính sách đã biết đối với Sharp RKD (Mặc định 1.0).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`RegressionKinkOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"REGRESSION_KINK_DESIGN_CARD_2015"`.
  - `diagnostics`: Quy mô mẫu tổng thể, Mẫu hiệu dụng trong băng thông, Ngưỡng $c$, Băng thông $h$, Ước lượng đạo hàm hiệu ứng $\hat{\tau}_{\text{RKD}}$, Sai số chuẩn SE, Thống kê $t$, $p$-value, Khoảng tin cậy 95% CI, Độ gãy dốc Outcome $\Delta \beta_Y$, Độ dốc bên trái $\beta_1^-$, Độ dốc bên phải $\beta_1^+$, Giá trị mức chặn tại ngưỡng, $p$-value kiểm định McCrary, Cờ kiểm định mật độ trơn (`is_density_smooth`), Cờ ý nghĩa thống kê (`is_statistically_significant`).
  - `binned_scatter`: Danh sách các bin gom cục bộ (tâm bin, trung bình $X$, trung bình $Y$, số lượng quan sát, phía ngưỡng `left`/`right`).
  - `svg_visualization`: Đồ thị SVG khoa học kép minh họa điểm gãy bán thực nghiệm và mật độ trơn McCrary.
  - `apa_narrative`: Thuyết minh học thuật chuẩn APA 7th Edition giải thích kết quả hồi quy RKD, kiểm định độ trơn mật độ và độ co giãn chính sách biên.
- **Niêm phong kiểm toán:** Tự động ghi nhận `REGRESSION_KINK_EVALUATED` vào chuỗi sổ cái SHA-256.

### 113. Staggered Difference-in-Differences & Group-Time Average Treatment Effects Engine (Callaway & Sant'Anna 2021; Goodman-Bacon 2021; Sun & Abraham 2021)
- **Lý thuyết nền tảng:**
  1. **Khuyết tật của Hồi quy Hai Chiều Cố Định (Two-Way Fixed Effects - TWFE) khi Can Thiệp Phân Tầng Thời Gian:**
     - Trong các nghiên cứu khảo sát dọc / bảng (panel surveys) nơi các đơn vị khảo sát (doanh nghiệp, chi nhánh, trường học, tỉnh thành) tiếp cận hoặc triển khai chính sách tại các thời điểm khác nhau (staggered adoption cohorts $g \in \{g_1, g_2, \dots\}$), phương pháp truyền thống thường chạy mô hình hồi quy TWFE:
       $$Y_{it} = \alpha_i + \lambda_t + \beta^{\text{TWFE}} D_{it} + \varepsilon_{it}$$
     - **Goodman-Bacon (2021)** đã chứng minh định lý phân rã toán học quan trọng: $\beta^{\text{TWFE}}$ là bình quân gia quyền của tất cả các phép so sánh $2 \times 2$ DiD trong mẫu. Khi hiệu ứng can thiệp biến thiên theo thời gian (dynamic / heterogeneous treatment effects $\theta(t - g)$), các đơn vị can thiệp sớm (already treated) bị đưa vào làm "nhóm đối chứng" cho các đơn vị can thiệp muộn hơn, dẫn đến **trọng số âm (negative weights)**. Hậu quả là $\beta^{\text{TWFE}}$ có thể mang dấu âm ngay cả khi hiệu ứng can thiệp thực tế của từng đơn vị đều dương!
  2. **Trụ Cột Phương Pháp Luận Callaway & Sant'Anna (2021) & Sun & Abraham (2021):**
     - **Đại lượng Ước Lượng Nhóm - Thời điểm $ATT(g, t)$:**
       $$ATT(g, t) = \mathbb{E}[Y_t(g) - Y_t(0) \mid G_g = 1]$$
       với $G_g = 1$ là chỉ số đơn vị được can thiệp lần đầu tại mốc $g$, và $t$ là mốc quan sát.
       Ước lượng phi tham số không chệch bằng cách chỉ so sánh với nhóm chưa từng can thiệp (never-treated $C$) hoặc nhóm chưa can thiệp tại thời điểm $t$ (not-yet-treated):
       $$\widehat{ATT}(g, t) = (\bar{Y}_{g, t} - \bar{Y}_{g, g-1}) - (\bar{Y}_{C, t} - \bar{Y}_{C, g-1})$$
     - **Nghiên cứu Biến cố Động (Dynamic Event Study Aggregation $ATT(e)$):**
       Tổng hợp các hiệu ứng theo khoảng thời gian biến cố $e = t - g \in \{-K, \dots, +M\}$:
       $$ATT_{\text{es}}(e) = \sum_g w(g, e) \cdot ATT(g, g + e)$$
       Cho phép kiểm định trực tiếp tính hợp lệ của giả định xu hướng song song trước can thiệp (Pre-Trends Parallel Assumption, $e < 0$) thông qua thống kê Wald $\chi^2$.
     - **Ước lượng Tác động Gộp Toàn cục (Overall Summary ATT $\hat{\tau}_{\text{CS}}$):**
       Trung bình gia quyền quy mô mẫu của các $ATT(g, t)$ hậu can thiệp, bảo đảm không bị ô nhiễm bởi trọng số âm.
     - **Phân tích Phân rã Goodman-Bacon (2021):**
       Tự động tính toán tỷ lệ trọng số âm tiềm ẩn và đo lường khoảng cách sai lệch (Bias Gap $\Delta = \hat{\tau}_{\text{CS}} - \beta^{\text{TWFE}}$) so với mô hình TWFE OLS cổ điển.
     - **Đồ thị SVG Kép Khoa Học:**
       - Panel A: Đồ thị nghiên cứu biến cố động $ATT(e)$ với dải tin cậy 95%, phân định rõ tiền can thiệp (kiểm định xu hướng song song) và hậu can thiệp (quỹ đạo động của chính sách).
       - Panel B: Đồ thị phân tán phân rã Goodman-Bacon trực quan hóa các ước lượng $2 \times 2$ so với tỷ trọng phân rã, đối chiếu trực diện giữa đường chuẩn $\hat{\tau}_{\text{CS}}$ và $\beta^{\text{TWFE}}$.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/staggered-did`
- **Request Body (`StaggeredDIDRequest`):**
  - `outcome_question_id`: UUID câu hỏi đo lường kết quả $Y$.
  - `unit_question_id`: UUID biến định danh đơn vị quan sát (doanh nghiệp, đối tượng, chi nhánh).
  - `time_question_id`: UUID biến đo lường đợt / mốc thời gian khảo sát $T$.
  - `treatment_timing_question_id`: UUID biến xác định mốc thời gian bắt đầu can thiệp $G$ (0 nếu chưa bao giờ can thiệp).
  - `anticipation_periods`: Số kỳ dự báo trước tác động (Mặc định 0).
  - `control_group_type`: Nhóm đối chứng so sánh (`"never_treated"` hoặc `"not_yet_treated"`).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`StaggeredDIDOut`):**
  - `status`: `"SUCCESS"`, `"INSUFFICIENT_SAMPLE"`, `"INSUFFICIENT_TIME_PERIODS"`, hoặc `"NO_TREATED_UNITS"`.
  - `model_type`: `"STAGGERED_DID_CALLAWAY_SANTANNA_2021"`.
  - `diagnostics`: Quy mô mẫu quan sát, số đơn vị, số mốc thời gian, số đoàn hệ, số đơn vị thuần đối chứng, Ước lượng gộp $\hat{\tau}_{\text{CS}}$, Sai số chuẩn SE, $p$-value, Khoảng tin cậy 95% CI, Kiểm định xu hướng song song (Wald $\chi^2$ và $p$-value), Cờ thỏa mãn song song (`parallel_trends_supported`), Hệ số OLS TWFE ngây thơ $\beta^{\text{TWFE}}$, Độ lệch thiên lệch $\Delta$, Tỷ lệ trọng số âm (`pct_negative_weights`).
  - `group_time_effects`: Bảng chi tiết toàn bộ các ước lượng $ATT(g, t)$ kèm SE, $t$, $p$-value và quy mô mẫu treated/control.
  - `event_study_effects`: Bảng nghiên cứu biến cố động $ATT(e)$ tổng hợp theo thời gian tương đối $e = t - g$.
  - `bacon_decomposition`: Kết quả phân rã Goodman-Bacon phân tách thành các cặp so sánh $2 \times 2$ DiD và tỷ trọng đóng góp.
  - `svg_visualization`: Đồ thị SVG khoa học kép trực quan hóa quỹ đạo biến cố động và phân tán trọng số Bacon.
  - `apa_narrative`: Thuyết minh học thuật chuẩn APA 7th Edition giải thích kết quả Callaway-Sant'Anna, kiểm định xu hướng song song và so sánh với TWFE.
- **Niêm phong kiểm toán:** Tự động ghi nhận `STAGGERED_DID_EVALUATED` vào chuỗi sổ cái SHA-256.

### 114. Matrix Completion for Causal Panel Data with Nuclear Norm Regularization (Athey, Bayati, Doudchenko, Imbens, & Khosravi 2021)
- **Lý thuyết nền tảng:**
  1. **Suy diễn Nhân quả Dữ liệu Bảng Dưới Dạng Bài Toán Khuyết Dữ liệu (Causal Inference as Missing Data Imputation):**
     - Xét ma trận kết quả dữ liệu bảng / khảo sát dọc kích thước $N \times T$ ($N$ đơn vị khảo sát quan sát qua $T$ mốc thời gian). Với mỗi ô $(i, t)$, ký hiệu $W_{it} \in \{0, 1\}$ là chỉ báo can thiệp. Giá trị quan sát thực tế là:
       $$Y_{it} = W_{it} Y_{it}(1) + (1 - W_{it}) Y_{it}(0)$$
     - Dưới góc nhìn chuẩn tắc của Rubin (1974) và Athey et al. (2021), suy diễn nhân quả bản chất là bài toán khuyết dữ liệu: đối với mọi ô được can thiệp $(i, t)$ nơi $W_{it} = 1$, giá trị đối chứng phản sự kiện $Y_{it}(0)$ là **chưa quan sát được (missing)**.
  2. **Chính quy hóa Chuẩn Hạt nhân & Phục dựng Hạng Thấp (Nuclear Norm Regularization):**
     - Khác với TWFE (áp đặt cấu trúc cộng rank-2 $\alpha_i + \beta_t$) hoặc Synthetic Control (yêu cầu đối chứng bất biến), Athey et al. (2021) thiết lập mô hình ma trận phản sự kiện $L = Y(0)$ thông qua chương trình tối ưu hóa lồi:
       $$\min_{L \in \mathbb{R}^{N \times T}} \left\{ \frac{1}{|\mathcal{O}|} \sum_{(i, t) \in \mathcal{O}} (Y_{it} - L_{it})^2 + \lambda \|L\|_* \right\}$$
       trong đó $\mathcal{O} = \{(i, t) : W_{it} = 0\}$ là tập hợp các ô đối chứng đã quan sát, và $\|L\|_* = \sum_k \sigma_k(L)$ là chuẩn hạt nhân (tổng các giá trị kỳ dị của $L$, bao lồi chặt nhất của hàm hạng ma trận $\operatorname{rank}(L)$).
  3. **Thuật toán Soft-Impute SVT (Mazumder, Hastie, & Tibshirani 2010):**
     - Lặp lại bước tính SVD trên ma trận $Z^{(k)} = P_{\mathcal{O}}(Y) + P_{\mathcal{O}}^\perp(L^{(k)})$ và áp dụng toán tử thu nhỏ giá trị kỳ dị mềm (soft-thresholding operator $\mathcal{S}_\lambda(\sigma) = \max(0, \sigma - \lambda)$).
     - Hội tụ tiệm cận về ma trận phản sự kiện không chệch $\hat{L} = \hat{Y}(0)$.
  4. **Ước lượng Hiệu ứng Can thiệp Cục bộ và Toàn cục:**
     - Tác động can thiệp tại từng ô cụ thể: $\hat{\tau}_{it} = Y_{it} - \hat{L}_{it}$.
     - Hiệu ứng trung bình trên nhóm can thiệp (Overall ATT):
       $$\hat{\tau}_{\text{MC}} = \frac{1}{|\mathcal{T}|} \sum_{(i, t) \in \mathcal{T}} (Y_{it} - \hat{L}_{it})$$
  5. **Đồ thị SVG Kép Khoa Học:**
     - Panel A: Bản đồ nhiệt ma trận $N \times T$ phân định trực quan các ô đối chứng đã quan sát (xanh dương) và các ô can thiệp được phục dựng phản sự kiện (xanh ngọc Emerald).
     - Panel B: Biểu đồ Scree Plot phân rã phổ giá trị kỳ dị và đường ngưỡng thu nhỏ $\lambda$.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/matrix-completion-causal`
- **Request Body (`MatrixCompletionCausalRequest`):**
  - `outcome_question_id`: UUID câu hỏi đo lường kết quả $Y$.
  - `unit_question_id`: UUID biến định danh đơn vị quan sát $U$.
  - `time_question_id`: UUID biến đo lường đợt / mốc thời gian $T$.
  - `treatment_question_id`: UUID biến chỉ báo can thiệp $W$ (1: Can thiệp, 0: Đối chứng).
  - `lambda_penalty`: Hệ số phạt chuẩn hạt nhân $\lambda$ (Tùy chọn, tự động tối ưu hóa SVT nếu bỏ trống).
  - `max_rank`: Hạng ma trận tối đa cho phép (Mặc định 5).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`MatrixCompletionCausalOut`):**
  - `status`: `"SUCCESS"`, `"INSUFFICIENT_SAMPLE"`, `"INSUFFICIENT_DIMENSIONS"`, `"NO_TREATED_CELLS"`, hoặc `"INSUFFICIENT_CONTROLS"`.
  - `model_type`: `"CAUSAL_MATRIX_COMPLETION_ATHEY_2021"`.
  - `diagnostics`: Kích thước $N \times T$, tổng số ô, số ô can thiệp được phục dựng, số ô đối chứng, hệ số phạt $\lambda$, số vòng lặp hội tụ, hạng hiệu dụng $r$, sai số RMSE khớp ô đối chứng, Ước lượng gộp ATT $\hat{\tau}_{\text{MC}}$, Sai số chuẩn SE, $p$-value, 95% CI, tỷ trọng phương sai nhân tố hàng đầu.
  - `cell_treatment_effects`: Danh sách chi tiết từng ô can thiệp (mã đơn vị, mốc thời gian, $Y(1)$ quan sát, $Y(0)$ phục dựng, hiệu ứng $\hat{\tau}_{it}$).
  - `singular_value_spectrum`: Bảng phổ các giá trị kỳ dị và tỷ lệ phương sai giải thích.
  - `svg_visualization`: Đồ thị SVG khoa học kép bản đồ nhiệt ma trận và biểu đồ Scree Plot.
  - `apa_narrative`: Thuyết minh học thuật chuẩn APA 7th Edition giải thích kết quả hoàn thiện ma trận và hiệu ứng can thiệp.
- **Niêm phong kiểm toán:** Tự động ghi nhận `MATRIX_COMPLETION_CAUSAL_EVALUATED` vào chuỗi sổ cái SHA-256.

### 115. Synthetic Difference-in-Differences (SDID) Advanced Engine (Arkhangelsky, Athey, Hirshberg, Imbens, & Wager 2021; Doudchenko & Imbens 2016)
- **Lý thuyết nền tảng:**
  1. **Hạn chế của DiD truyền thống và Synthetic Control cổ điển:**
     - DiD truyền thống (Ashenfelter & Card 1985) dựa vào giả định xu hướng song song nghiêm ngặt (Parallel Trends Assumption). Nếu đơn vị can thiệp và nhóm đối chứng có xu hướng thời gian trước can thiệp khác nhau, DiD sẽ ước lượng chệch nghiêm trọng.
     - Synthetic Control cổ điển (Abadie, Diamond, & Hainmueller 2010) giải quyết bài toán bằng cách tìm tổ hợp lồi các đơn vị đối chứng $\omega$ để mô phỏng chính xác đơn vị can thiệp, nhưng SC không cho phép dịch chuyển mức nền (level shift) $\omega_0$ và không gán trọng số tối ưu cho các mốc thời gian $\lambda_t$.
  2. **Ước lượng Kép Vững SDID (Double-Robust Synthetic DiD):**
     - Arkhangelsky et al. (2021) kết hợp trọn vẹn hai phương pháp thông qua ước lượng:
       $$\hat{\tau}_{\text{SDID}} = (\bar{Y}_{\text{tr}, \text{post}} - \sum_{t=1}^{T_{\text{pre}}} \hat{\lambda}_t \bar{Y}_{\text{tr}, t}) - \sum_{i=1}^{N_{\text{co}}} \hat{\omega}_i (Y_{i, \text{post}} - \sum_{t=1}^{T_{\text{pre}}} \hat{\lambda}_t Y_{it})$$
       tương đương với việc tìm hệ số $\tau$ trong hồi quy WLS hai chiều:
       $$\min_{\tau, \mu, \alpha, \beta} \sum_{i=1}^N \sum_{t=1}^T (Y_{it} - \mu - \alpha_i - \beta_t - W_{it} \tau)^2 \hat{\Omega}_i \hat{\Lambda}_t$$
  3. **Tối ưu hóa Trọng số Đơn vị có Phạt L2 ($\hat{\omega}$ & $\zeta$):**
     - Tối ưu hóa lồi có ràng buộc với phạt điều hòa L2 phân tán (SLSQP Quadratic Programming):
       $$\min_{\omega_0, \omega} \sum_{t=1}^{T_{\text{pre}}} \left( \omega_0 + \sum_{i \in \text{co}} \omega_i Y_{it} - \bar{Y}_{\text{tr}, t} \right)^2 + \zeta^2 T_{\text{pre}} \|\omega\|_2^2$$
       ràng buộc: $\sum_{i \in \text{co}} \omega_i = 1, \omega_i \ge 0$.
       Hệ số phạt $\zeta$ được tự động tính toán dựa trên độ phân tán sai phân thời gian $\Delta_{it} = Y_{i, t+1} - Y_{it}$.
  4. **Tối ưu hóa Trọng số Thời gian ($\hat{\lambda}$):**
     - Căn chỉnh xu hướng thời gian trước can thiệp để mô phỏng chính xác giai đoạn hậu can thiệp của nhóm đối chứng:
       $$\min_{\lambda_0, \lambda} \sum_{i \in \text{co}} \left( \lambda_0 + \sum_{t=1}^{T_{\text{pre}}} \lambda_t Y_{it} - \bar{Y}_{i, \text{post}} \right)^2$$
       ràng buộc: $\sum_{t=1}^{T_{\text{pre}}} \lambda_t = 1, \lambda_t \ge 0$.
  5. **Sai số Chuẩn và So sánh Trực diện (Placebo/Jackknife & Bias Gap):**
     - Ước lượng sai số chuẩn SE và khoảng tin cậy 95% CI.
     - So sánh đối chiếu trực diện giữa $\hat{\tau}_{\text{SDID}}$, $\hat{\tau}_{\text{DiD}}$ và $\hat{\tau}_{\text{SC}}$, định lượng chính xác độ lệch thiên lệch DiD ($\Delta = \hat{\tau}_{\text{SDID}} - \hat{\tau}_{\text{DiD}}$).
  6. **Đồ thị SVG Kép Khoa Học:**
     - Panel A: Quỹ đạo chuỗi thời gian so sánh giữa Can thiệp thực tế $Y(1)$, Phản sự kiện $\text{SDID } \hat{Y}(0)$, Synthetic Control chuẩn và Đối chứng thô unweighted.
     - Panel B: Biểu đồ thanh ngang phân bổ tỷ lệ trọng số đơn vị $\hat{\omega}_i$ của nhóm donor pool.
  7. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn theo chuẩn mực Arkhangelsky et al. (2021) và Doudchenko & Imbens (2016).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/sdid-advanced`
- **Request Body (`SDIDAdvancedRequest`):**
  - `outcome_question_id`: UUID câu hỏi đo lường kết quả $Y$.
  - `unit_question_id`: UUID biến định danh đơn vị quan sát $U$.
  - `time_question_id`: UUID biến đo lường đợt / mốc thời gian $T$.
  - `treatment_question_id`: UUID biến chỉ báo can thiệp $W$ (1: Can thiệp, 0: Đối chứng).
  - `zeta_regularization`: Hệ số phạt điều hòa L2 phân tán $\zeta$ (Tùy chọn).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`SDIDAdvancedOut`):**
  - `status`: `"SUCCESS"`, `"INSUFFICIENT_SAMPLE"`, `"INSUFFICIENT_UNITS"`, `"INSUFFICIENT_TIME_PERIODS"`, hoặc `"NO_TREATED_OR_CONTROL_UNITS"`.
  - `model_type`: `"SYNTHETIC_DIFFERENCE_IN_DIFFERENCES_ARKHANGELSKY_2021"`.
  - `diagnostics`: Số đơn vị $N$, số can thiệp $N_{\text{tr}}$, số đối chứng $N_{\text{co}}$, số mốc thời gian $T$, số kỳ tiền can thiệp $T_{\text{pre}}$, số kỳ hậu can thiệp $T_{\text{post}}$, hệ số phạt $\zeta$, độ dịch chuyển mức nền $\omega_0$, ước lượng tác động $\hat{\tau}_{\text{SDID}}$, sai số chuẩn SE, $z$-statistic, $p$-value, khoảng tin cậy 95% CI, cờ ý nghĩa thống kê, ước lượng DiD truyền thống $\hat{\tau}_{\text{DiD}}$, ước lượng SC truyền thống $\hat{\tau}_{\text{SC}}$, độ lệch thiên lệch DiD $\Delta$.
  - `unit_weights`: Danh sách tỷ lệ và giá trị trọng số đơn vị $\hat{\omega}_i$ cho từng đơn vị đối chứng.
  - `time_weights`: Danh sách tỷ lệ và giá trị trọng số thời gian $\hat{\lambda}_t$ cho các kỳ tiền can thiệp.
  - `trajectories`: Bảng chi tiết từng mốc thời gian so sánh giá trị can thiệp thực tế, đối chứng thô, synthetic control chuẩn và phản sự kiện SDID.
  - `svg_visualization`: Đồ thị SVG khoa học kép quỹ đạo chuỗi thời gian và phân bổ trọng số đơn vị đối chứng.
  - `apa_narrative`: Thuyết minh học thuật chuẩn APA 7th Edition phân tích tác động chính sách và so sánh với DiD / SC cổ điển.
- **Niêm phong kiểm toán:** Tự động ghi nhận `SDID_ADVANCED_EVALUATED` vào chuỗi sổ cái SHA-256.

### 116. Causal Panel Factor Models with Interactive Fixed Effects & Cross-Sectional Dependence (Bai 2009; Gobillon & Magnac 2016)
- **Lý thuyết nền tảng:**
  1. **Hạn chế của mô hình Two-Way Fixed Effects (TWFE) khi có phụ thuộc chéo:**
     - Mô hình OLS hai chiều TWFE giả định các yếu tố nhiễu không quan sát được có dạng cộng tách rời: $\alpha_i + \lambda_t$.
     - Trong thực tế khảo sát kinh tế - xã hội, các cú sốc vĩ mô (lạm phát, đổi mới công nghệ, khủng hoảng chuỗi cung ứng) tác động đến từng đối tượng khảo sát với độ nhạy khác nhau (heterogeneous factor loadings $\boldsymbol{\gamma}_i^\top \mathbf{f}_t$), tạo ra hiện tượng phụ thuộc chéo (Cross-Sectional Dependence). Khi việc áp dụng chính sách có tương quan với các hệ số tải này, TWFE bị chệch nghiêm trọng.
  2. **Đặc tả Mô hình Interactive Fixed Effects (Bai 2009):**
     $$Y_{it} = \tau D_{it} + \alpha_i + \lambda_t + \boldsymbol{\gamma}_i^\top \mathbf{f}_t + \varepsilon_{it}$$
     - $\mathbf{f}_t \in \mathbb{R}^r$: Vector $r$ nhân tố tiềm ẩn chung biến thiên theo thời gian (chuỗi thời gian của cú sốc vĩ mô).
     - $\boldsymbol{\gamma}_i \in \mathbb{R}^r$: Vector hệ số tải nhân tố đặc trưng cho từng đơn vị (độ nhạy cá thể đối với cú sốc).
     - $\tau$: Tác động can thiệp trung bình trên nhóm can thiệp (ATT).
  3. **Thuật toán Bình phương Tối thiểu Luân phiên (Alternating Least Squares - ALS):**
     - Khử trung bình và ước lượng lặp kết hợp phân rã SVD trên phần dư (Gobillon & Magnac 2016 Section 3):
       $Y^*_{it} = Y_{it} - \tau D_{it}$.
       $\tilde{Y}^* = Y^* - \alpha - \lambda + \bar{Y}$.
       SVD: $\tilde{Y}^* \approx \boldsymbol{\Gamma} \mathbf{F}^\top$ với điều kiện chuẩn hóa $\frac{1}{T} \mathbf{F}^\top \mathbf{F} = \mathbf{I}_r$.
       Cập nhật $\tau$: $\tau^{(k+1)} = \frac{\sum D_{it} (Y_{it} - \hat{Y}_{it}(0))}{\sum D_{it}^2}$.
       Lặp cho tới khi $\tau$ hội tụ sai số tuyệt đối $< 10^{-5}$.
  4. **Tiêu chuẩn Thông tin Chọn Số Nhân tố Tối ưu Bai & Ng (2002):**
     $$\text{IC}_{p1}(k) = \ln(V(k, \mathbf{F})) + k \left( \frac{N + T}{NT} \right) \ln\left( \frac{NT}{N + T} \right)$$
     Tự động lựa chọn chiều nhân tố tối ưu $r^*$ tối thiểu hóa sai số phương sai kết hợp hàm phạt chiều dữ liệu bảng.
  5. **Kiểm định Phụ thuộc Chéo Pesaran (2004, 2021) CD Test:**
     $$CD = \sqrt{\frac{2T}{N(N-1)}} \sum_{i=1}^{N-1} \sum_{j=i+1}^N \hat{\rho}_{ij} \sim \mathcal{N}(0, 1)$$
     Kiểm tra mức độ tự tương quan không gian còn sót lại trên phần dư $\hat{\varepsilon}_{it}$, chứng minh IFE đã triệt tiêu triệt để phụ thuộc chéo.
  6. **Đồ thị SVG Kép Khoa Học:**
     - Panel A: Biểu đồ Scree Plot phân rã phổ giá trị riêng (Eigenvalues) và đường ngưỡng lựa chọn $r^*$ theo tiêu chuẩn Bai-Ng.
     - Panel B: Quỹ đạo động của các nhân tố tiềm ẩn chung $\mathbf{f}_t$ qua các mốc thời gian khảo sát.
  7. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn theo chuẩn mực Bai (2009) và Gobillon & Magnac (2016).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/interactive-fixed-effects`
- **Request Body (`InteractiveFixedEffectsRequest`):**
  - `outcome_question_id`: UUID câu hỏi đo lường kết quả $Y$.
  - `unit_question_id`: UUID biến định danh đơn vị quan sát $U$.
  - `time_question_id`: UUID biến đo lường đợt / mốc thời gian $T$.
  - `treatment_question_id`: UUID biến chỉ báo can thiệp $W$ (1: Can thiệp, 0: Đối chứng).
  - `num_factors`: Số lượng nhân tố tiềm ẩn chỉ định thủ công (Tùy chọn, mặc định tự động theo Bai-Ng IC).
  - `max_factors`: Số nhân tố tối đa quét kiểm định (Mặc định 4).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`InteractiveFixedEffectsOut`):**
  - `status`: `"SUCCESS"`, `"INSUFFICIENT_SAMPLE"`, `"INSUFFICIENT_UNITS"`, `"INSUFFICIENT_TIME_PERIODS"`, `"NO_TREATED_CELLS"`, hoặc `"INSUFFICIENT_CONTROLS"`.
  - `model_type`: `"INTERACTIVE_FIXED_EFFECTS_BAI_2009"`.
  - `diagnostics`: Số đơn vị $N$, số mốc thời gian $T$, số ô can thiệp, số ô đối chứng, số nhân tố tối ưu $r^*$, tỷ lệ phương sai giải thích (%), ước lượng tác động $\hat{\tau}_{\text{IFE}}$, sai số chuẩn SE Jackknife, $z$-statistic, $p$-value, khoảng tin cậy 95% CI, cờ ý nghĩa thống kê, ước lượng TWFE so sánh $\beta^{\text{TWFE}}$, độ lệch thiên lệch nhân tố Factor Bias Gap $\Delta$, thống kê Pesaran CD và $p$-value, cờ triệt tiêu phụ thuộc chéo.
  - `latent_factors`: Danh sách các chuỗi nhân tố tiềm ẩn trích xuất được kèm tỷ trọng phương sai giải thích.
  - `scree_spectrum`: Phổ các giá trị riêng và cờ lựa chọn của từng nhân tố.
  - `cell_effects`: Danh sách chi tiết từng ô can thiệp (mã đơn vị, kỳ thời gian, $Y(1)$ quan sát, $Y(0)$ phục dựng phản sự kiện, hiệu ứng can thiệp).
  - `svg_visualization`: Đồ thị SVG khoa học kép Scree Plot và quỹ đạo động các nhân tố.
  - `apa_narrative`: Thuyết minh học thuật chuẩn APA 7th Edition giải thích kết quả IFE và đối chiếu TWFE.
- **Niêm phong kiểm toán:** Tự động ghi nhận `INTERACTIVE_FIXED_EFFECTS_EVALUATED` vào chuỗi sổ cái SHA-256.

### 117. Multiple Sequential Mediators & Path-Specific Causal Mediation Engine (VanderWeele 2014; Steen, Loeys, Moerkerke, & Vansteelandt 2012; Imai & Yamamoto 2013)
- **Lý thuyết nền tảng:**
  1. **Hạn chế của mô hình đơn trung gian (Single-Mediator Models):**
     - Mô hình trung gian đơn tuyến cổ điển (Baron & Kenny 1986; Sobel 1982) chỉ xét duy nhất một biến trung gian độc lập $X \to M \to Y$.
     - Trong các hiện tượng xã hội, hành vi và tổ chức phức tạp, cơ chế tác động thường vận hành qua chuỗi các biến trung gian liên hoàn (Sequential Mediators) hoặc song song (Parallel Mediators), trong đó trung gian sớm $M_1$ tác động trực tiếp lên trung gian muộn $M_2$ ($X \to M_1 \to M_2 \to Y$).
     - Việc bỏ qua liên kết giữa các biến trung gian gây ra sai lệch trầm trọng (Mediator-Mediator Confounding).
  2. **Phân rã Tác động Causal Đa biến Tuần tự (VanderWeele 2014):**
     - Dưới khung kết quả tiềm năng (Counterfactual / Potential Outcomes Framework), tổng tác động (Total Effect - TE) được phân rã chặt chẽ thành:
       $$\text{TE} = \text{PDE} + \text{NIE}_{M_1} + \text{NIE}_{M_2} + \text{NIE}_{\text{Seq}}$$
       - **Tác động trực tiếp thuần (Pure Direct Effect - PDE):** Tác động độc lập của $X$ lên $Y$ khi cố định tất cả các biến trung gian ở mức đối chứng tự nhiên: $\mathbb{E}[Y(1, M_1(0), M_2(0, M_1(0))) - Y(0, M_1(0), M_2(0, M_1(0)))]$.
       - **Tác động gián tiếp đặc thù qua $M_1$ ($\text{NIE}_{M_1}$):** Kênh $X \to M_1 \to Y$.
       - **Tác động gián tiếp đặc thù qua $M_2$ ($\text{NIE}_{M_2}$):** Kênh $X \to M_2 \to Y$.
       - **Tác động gián tiếp chuỗi tuần tự ($\text{NIE}_{\text{Seq}}$):** Kênh liên hoàn $X \to M_1 \to M_2 \to Y$.
       - **Tổng tác động gián tiếp (Total Indirect Effect - TIE):** $\text{TIE} = \text{NIE}_{M_1} + \text{NIE}_{M_2} + \text{NIE}_{\text{Seq}}$.
  3. **Ước lượng Sai số Chuẩn và Khoảng tin cậy Bootstrap:**
     - Sử dụng phân phối tái chọn không tham số Bootstrap (mặc định 500 lần) để ước lượng sai số chuẩn và khoảng tin cậy 95% Percentile CI cho toàn bộ các tác động phi tuyến tính.
  4. **Tỷ lệ Trung gian (Proportion Mediated - PM):**
     - Tính toán tỷ lệ phần trăm đóng góp của từng kênh trung gian và tổng tác động gián tiếp so với tổng tác động: $\text{PM} = \frac{\text{TIE}}{\text{TE}} \times 100\%$.
  5. **Đồ thị SVG Kép Khoa Học:**
     - Panel A: Sơ đồ mạng DAG đường dẫn cấu trúc thể hiện các hệ số đường dẫn $a_1, a_2, d_{21}, b_1, b_2, c'$ cùng mức ý nghĩa thống kê.
     - Panel B: Biểu đồ Forest Plot trực quan hóa các ước lượng điểm và khoảng tin cậy 95% CI của TE, PDE, TIE và từng kênh trung gian cụ thể.
  6. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn theo chuẩn mực VanderWeele (2014) và Steen et al. (2012).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/multiple-mediators`
- **Request Body (`MultipleMediatorsRequest`):**
  - `treatment_question_id`: UUID câu hỏi can thiệp $X$.
  - `mediator1_question_id`: UUID câu hỏi trung gian thứ nhất $M_1$.
  - `mediator2_question_id`: UUID câu hỏi trung gian thứ hai $M_2$.
  - `outcome_question_id`: UUID câu hỏi kết quả $Y$.
  - `covariate_question_ids`: Danh sách UUID các biến kiểm soát ngoại sinh (Tùy chọn).
  - `n_bootstraps`: Số lần tái chọn mẫu Bootstrap (Mặc định 500).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`MultipleMediatorsOut`):**
  - `status`: `"SUCCESS"`, `"INSUFFICIENT_SAMPLE"`, hoặc `"ZERO_VARIANCE"`.
  - `model_type`: `"MULTIPLE_SEQUENTIAL_MEDIATORS_VANDERWEELE_2014"`.
  - `diagnostics`: Cỡ mẫu $N$, số mẫu bootstrap, Tổng tác động (TE), Tác động trực tiếp thuần (PDE), Tổng tác động gián tiếp (TIE), Tác động qua M1 ($\text{NIE}_{M_1}$), Tác động qua M2 ($\text{NIE}_{M_2}$), Tác động chuỗi tuần tự ($\text{NIE}_{\text{Seq}}$), Tỷ lệ trung gian tổng (%), Tỷ lệ qua từng kênh (%), Cờ phân loại trung gian toàn phần (Full Mediation) hay một phần (Partial Mediation).
  - `path_coefficients`: Bảng chi tiết toàn bộ các hệ số đường dẫn ($a_1, a_2, d_{21}, b_1, b_2, c'$) kèm sai số chuẩn SE và $p$-value.
  - `effects_summary`: Bảng phân rã chi tiết 6 loại tác động kèm ước lượng, SE, $z$, $p$-value, 95% CI và tỷ trọng (%).
  - `svg_visualization`: Đồ thị SVG khoa học kép sơ đồ mạng DAG và biểu đồ Forest Plot.
  - `apa_narrative`: Thuyết minh học thuật chuẩn APA 7th Edition phân tích cơ chế trung gian và kết luận khoa học.
- **Niêm phong kiểm toán:** Tự động ghi nhận `MULTIPLE_MEDIATORS_EVALUATED` vào chuỗi sổ cái SHA-256.

### 118. Doubly Robust Policy Learning & Optimal Treatment Regimes Engine (Athey & Wager 2021; Dudík, Langford, & Li 2011)
- **Lý thuyết nền tảng:**
  1. **Bài toán Học Chính sách Phân bổ Cá thể hóa (Optimal Individualized Policy Learning):**
     - Thay vì chỉ đo lường tác động trung bình (ATE) hoặc tác động không đồng nhất (CATE), mục tiêu thực tiễn của người quản lý hoặc nhà hoạch định chính sách là tìm ra quy tắc quyết định tối ưu $\pi^*(X) \in \{0, 1\}$ phân bổ can thiệp cho từng khách thể dựa trên đặc tính $X$ nhằm tối đa hóa tổng phúc lợi xã hội / kỳ vọng giá trị kết quả:
       $$Q(\pi) = \mathbb{E}[Y(\pi(X))]$$
  2. **Biến đổi Điểm AIPW (Doubly Robust Pseudo-Outcomes):**
     - Athey & Wager (2021) và Dudík et al. (2011) biến đổi bài toán tối ưu hóa phúc lợi thành bài toán phân loại có trọng số chi phí (Cost-Weighted Classification) sử dụng điểm AIPW:
       $$\Gamma_i = \hat{\mu}_1(X_i) - \hat{\mu}_0(X_i) + \frac{W_i (Y_i - \hat{\mu}_1(X_i))}{\hat{e}(X_i)} - \frac{(1 - W_i)(Y_i - \hat{\mu}_0(X_i))}{1 - \hat{e}(X_i)}$$
       $$\min_{\pi \in \Pi} \frac{1}{n} \sum_{i=1}^n |\Gamma_i| \cdot \mathbb{I}\left( \operatorname{sign}(\Gamma_i) \neq 2\pi(X_i) - 1 \right)$$
     - Điểm $\Gamma_i$ có tính chất kép vững: chỉ cần mô hình propensity score $\hat{e}(X)$ HOẶC mô hình hàm hồi quy kết quả $\hat{\mu}_w(X)$ được đặc tả đúng, điểm $\Gamma_i$ là ước lượng không chệch của lợi ích can thiệp cá thể $\tau(X_i) = Y_i(1) - Y_i(0)$.
  3. **Quy tắc Quyết định Tối ưu và Ngưỡng Phân tầng:**
     - Quy tắc tối ưu: $\pi^*(X) = \mathbb{I}(\Gamma_i > 0)$.
     - Phân bổ can thiệp cho mọi đối tượng có điểm phúc lợi thuần dương $\Gamma_i > 0$.
  4. **So sánh Đối chiếu 4 Chế độ Chính sách & Thặng dư Phúc lợi Thuần (Net Welfare Gain):**
     - $V(\pi^*)$: Phúc lợi kỳ vọng dưới chính sách tối ưu cá thể hóa.
     - $V(\mathbf{1})$: Phúc lợi khi can thiệp đại trà 100% mẫu khảo sát (Treat All).
     - $V(\mathbf{0})$: Phúc lợi khi không can thiệp (Treat None).
     - $V(W)$: Phúc lợi của hiện trạng phân bổ thực tế trong mẫu khảo sát.
     - Thặng dư phúc lợi thuần: $\Delta V = V(\pi^*) - \max(V(\mathbf{1}), V(\mathbf{0}))$.
     - Kiểm định giả thuyết Bootstrap (one-sided test) cho thấy chính sách tối ưu có tạo ra sự cải thiện phúc lợi vượt trội có ý nghĩa thống kê hay không.
  5. **Đồ thị SVG Kép Khoa Học:**
     - Panel A: Đồ thị phân tán điểm AIPW $\Gamma_i$ theo đặc tính phân tầng chính, hiển thị rõ đường ngưỡng quyết định chính sách $\Gamma = 0$ và vùng can thiệp (xanh ngọc Emerald).
     - Panel B: Biểu đồ cột so sánh phúc lợi dân số qua 4 chế độ chính sách (Tối ưu $\pi^*$, Treat All, Treat None, và Hiện trạng $W$).
  6. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn theo chuẩn mực Athey & Wager (2021) và Dudík et al. (2011).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/policy-learning`
- **Request Body (`PolicyLearningRequest`):**
  - `outcome_question_id`: UUID câu hỏi đo lường kết quả $Y$.
  - `treatment_question_id`: UUID biến chỉ báo can thiệp $W$.
  - `covariate_question_ids`: Danh sách UUID các biến đặc tính cá thể dùng phân tầng chính sách $X$.
  - `primary_feature_idx`: Vị trí chỉ mục của biến đặc tính chính hiển thị trên trục hoành (Mặc định 0).
  - `n_bootstraps`: Số lần tái chọn mẫu Bootstrap (Mặc định 300).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`PolicyLearningOut`):**
  - `status`: `"SUCCESS"`, `"INSUFFICIENT_SAMPLE"`, hoặc `"INSUFFICIENT_VARIATION"`.
  - `model_type`: `"DOUBLY_ROBUST_POLICY_LEARNING_ATHEY_WAGER_2021"`.
  - `diagnostics`: Cỡ mẫu $N$, số quan sát can thiệp/đối chứng, Tỷ lệ phần trăm và số lượng đối tượng được khuyến nghị can thiệp theo chính sách tối ưu $\pi^*$, Giá trị phúc lợi kỳ vọng của từng chế độ ($V(\pi^*), V(\mathbf{1}), V(\mathbf{0}), V(W)$), Thặng dư phúc lợi thuần $\Delta V$, Sai số chuẩn Bootstrap SE, $z$-statistic, $p$-value, khoảng tin cậy 95% CI, Cờ ý nghĩa thống kê của thặng dư chính sách.
  - `regimes_comparison`: Bảng so sánh chi tiết 4 chế độ chính sách kèm phúc lợi kỳ vọng, tỷ lệ can thiệp và mô tả nguyên tắc.
  - `sample_allocations`: Danh sách phân bổ chi tiết cho từng cá thể trong mẫu (mã đối tượng, giá trị đặc tính, can thiệp thực tế, điểm AIPW $\Gamma_i$, quyết định tối ưu $\pi^*$ và trạng thái khuyến nghị).
  - `svg_visualization`: Đồ thị SVG khoa học kép điểm AIPW & so sánh phúc lợi chế độ chính sách.
  - `apa_narrative`: Thuyết minh học thuật chuẩn APA 7th Edition phân tích tính tối ưu và thặng dư phúc lợi xã hội.
- **Niêm phong kiểm toán:** Tự động ghi nhận `POLICY_LEARNING_EVALUATED` vào chuỗi sổ cái SHA-256.


### 119. RDD with Local Randomization for Discrete Running Variables (Cattaneo, Frandsen, & Titiunik 2015 JCA)

- **Mục đích & Cơ sở Khoa học:**
  1. **Hạn chế của RDD tiệm cận liên tục đối với Biến Chạy Rời rạc (Discrete Running Variables):**
     - Trong thực tế khảo sát kinh tế lượng và khoa học xã hội, biến chạy (running / forcing variable $X$) thường có tính chất rời rạc với số điểm tập trung giá trị (mass points) hữu hạn (ví dụ: tuổi theo năm nguyên, số năm thâm niên, điểm thi trắc nghiệm nguyên 1-100, số lượng nhân viên).
     - Khi số điểm mass points hữu hạn hoặc biến chạy rời rạc, các phương pháp hồi quy đa thức cục bộ tiệm cận liên tục (Hahn et al. 2001; Calonico, Cattaneo, & Titiunik 2014) không thể thu hẹp băng thông $h \to 0$ về ngưỡng $c$, dẫn đến chệch do xấp xỉ hàm đa thức và suy diễn thống kê quy ước bị sai lệch.
  2. **Khung Suy diễn Ngẫu nhiên Cục bộ (Local Randomization Framework - Cattaneo, Frandsen, & Titiunik 2015):**
     - Cattaneo et al. (2015) thiết lập khung phân tích giả định tồn tại một cửa sổ hẹp $W^* = [c - w, c + w]$ xung quanh ngưỡng phân định $c$, trong đó cơ chế gán can thiệp cận ngưỡng có tính chất ngẫu nhiên hoàn toàn như một thí nghiệm đối chứng ngẫu nhiên (RCT):
       $$W_i \perp (Y_i(1), Y_i(0)) \mid X_i \in W^*$$
     - Lựa chọn cửa sổ $W^*$ dựa trên kiểm định cân bằng hiệp biến tiền can thiệp (Covariate Balance Tests) sử dụng thống kê sai khác trung bình hoặc Kolmogorov-Smirnov.
  3. **Kiểm định Hoán vị Chính xác Mẫu Hữu hạn (Exact Finite-Sample Permutation Test):**
     - Dưới giả thuyết không Fisher sắc nét (Sharp Null Hypothesis $H_0: Y_i(1) = Y_i(0)$ với mọi $i \in W^*$), phân phối mẫu của hiệu số trung bình $\hat{\tau}_{\text{diff}} = \bar{Y}_{1, W} - \bar{Y}_{0, W}$ hoặc hiệu số trung vị $\hat{\tau}_{\text{median}}$ được mô phỏng chính xác qua phép hoán vị ngẫu nhiên (Monte Carlo permutation with $B$ resamples).
     - Cho phép suy diễn thống kê hợp lệ với mẫu hữu hạn mà không cần giả định phân phối tiệm cận chuẩn.
  4. **Đối chiếu So sánh với RDD Đa thức Cục bộ (Local Polynomial RDD Benchmark):**
     - Đối chiếu kết quả hiệu số trung bình ngẫu nhiên cục bộ với mô hình hồi quy đa thức bậc 1 (Local Linear) trong cửa sổ nhằm đánh giá độ bền vững trước xu hướng dốc (slope drift) của biến chạy rời rạc.
  5. **Đồ thị SVG Kép Khoa học:**
     - Panel A: Đồ thị phân phối các điểm khối lượng (mass points) của biến chạy rời rạc quanh ngưỡng $c$, phân định rõ nhóm đối chứng và can thiệp trong cửa sổ $W^*$.
     - Panel B: Phân phối hoán vị chính xác (Exact Permutation Null Distribution) cùng vị trí của thống kê quan sát thực tế $\hat{\tau}_{\text{obs}}$ và vùng bác bỏ kiểm định hai phía.
  6. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn theo chuẩn mực Cattaneo, Frandsen, & Titiunik (2015 JCA).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/rdd-local-randomization`
- **Request Body (`RDDLocalRandomizationRequest`):**
  - `outcome_question_id`: UUID câu hỏi đo lường kết quả $Y$.
  - `running_question_id`: UUID biến chạy rời rạc $X$.
  - `cutoff`: Ngưỡng phân định can thiệp $c$ (Mặc định 50.0).
  - `window_half_width`: Bán độ rộng cửa sổ ngẫu nhiên cục bộ $w$ (Mặc định 2.0, kiểm tra khoảng $[c-w, c+w]$).
  - `covariate_question_ids`: Danh sách UUID các biến hiệp biến kiểm tra cân bằng (Tùy chọn).
  - `n_permutations`: Số lần hoán vị ngẫu nhiên mẫu hữu hạn (Mặc định 500).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`RDDLocalRandomizationOut`):**
  - `status`: `"SUCCESS"`, `"INSUFFICIENT_SAMPLE"`, hoặc `"NO_WINDOW_VARIATION"`.
  - `model_type`: `"RDD_LOCAL_RANDOMIZATION_CATTANEO_2015"`.
  - `diagnostics`: Cỡ mẫu tổng $N$, số quan sát trong cửa sổ $N_W$, số quan sát can thiệp/đối chứng trong cửa sổ, số lượng điểm mass points bên trái/phải ngưỡng, Ước lượng hiệu số trung bình ngẫu nhiên cục bộ $\hat{\tau}_{\text{LR}}$, p-value hoán vị chính xác (Exact Permutation p-value), Hiệu số trung vị, Ước lượng đối chiếu RDD đa thức bậc 1 (Local Linear RDD estimate & p-value), Kết quả kiểm định cân bằng hiệp biến.
  - `mass_points`: Bảng tổng hợp các điểm giá trị rời rạc của biến chạy kèm cỡ mẫu, giá trị kết quả trung bình và trạng thái can thiệp.
  - `svg_visualization`: Đồ thị SVG khoa học kép phân phối điểm khối lượng và phân phối hoán vị giả thuyết không.
  - `apa_narrative`: Thuyết minh học thuật chuẩn APA 7th Edition theo Cattaneo, Frandsen, & Titiunik (2015).
- **Niêm phong kiểm toán:** Tự động ghi nhận `RDD_LOCAL_RANDOMIZATION_EVALUATED` vào chuỗi sổ cái SHA-256.


### 120. Dynamic Panel System & Difference GMM (Arellano-Bond 1991, Blundell-Bond 1998, Windmeijer 2005)

- **Mục đích & Cơ sở Khoa học:**
  1. **Thiên lệch Nickell trong Dữ liệu Bảng Động (Nickell 1981 Dynamic Panel Bias):**
     - Khi nghiên cứu dữ liệu bảng dọc (Longitudinal Panel Survey) qua nhiều đợt sóng thời gian ($t = 1, \dots, T$), mô hình chứa biến trễ phụ thuộc $Y_{i,t-1}$:
       $$Y_{i,t} = \alpha Y_{i,t-1} + \beta' X_{i,t} + \eta_i + \varepsilon_{i,t}$$
     - Ước lượng OLS bị chệch dương nghiêm trọng do biến trễ $Y_{i,t-1}$ tương quan dương với hiệu ứng cố định cá nhân $\eta_i$ ($\mathbb{E}[Y_{i,t-1}\eta_i] > 0 \implies \hat{\alpha}_{\text{OLS}} > \alpha$).
     - Ngược lại, ước lượng Within-Groups / Fixed Effects biến đổi khử trung bình cũng bị chệch âm với quy mô $\mathcal{O}(1/T)$ (Nickell 1981) do biến trễ khử trung bình $(Y_{i,t-1} - \bar{Y}_{i,-1})$ tương quan âm với sai số ngẫu nhiên khử trung bình $(\varepsilon_{i,t} - \bar{\varepsilon}_i)$ ($\hat{\alpha}_{\text{FE}} < \alpha$).
  2. **Ước lượng GMM Sai phân (Difference GMM - Arellano & Bond 1991):**
     - Loại bỏ hiệu ứng cố định cá nhân $\eta_i$ bằng phép lấy sai phân bậc nhất:
       $$\Delta Y_{i,t} = \alpha \Delta Y_{i,t-1} + \beta' \Delta X_{i,t} + \Delta \varepsilon_{i,t}$$
     - Sử dụng các biến cấp độ trễ từ $t-2$ trở về trước $(Y_{i,t-2}, Y_{i,t-3}, \dots)$ làm biến công cụ hợp lệ cho $\Delta Y_{i,t-1}$, thỏa mãn điều kiện trực giao $\mathbb{E}[Y_{i,t-s} \Delta \varepsilon_{i,t}] = 0$ với mọi $s \ge 2$.
  3. **Ước lượng GMM Hệ thống (System GMM - Blundell & Bond 1998):**
     - Khi chuỗi thời gian có độ dai dẳng cao ($\alpha \to 1$) hoặc tỷ lệ phương sai $\sigma_{\eta}^2 / \sigma_{\varepsilon}^2$ lớn, các công cụ sai phân trở nên yếu (weak instruments).
     - System GMM xếp chồng hệ phương trình sai phân bậc nhất và phương trình cấp độ ban đầu, bổ sung các công cụ sai phân trễ $\Delta Y_{i,t-1}$ cho phương trình cấp độ dưới giả định điều kiện ban đầu chuẩn hóa $\mathbb{E}[\Delta Y_{i,2} \eta_i] = 0$.
  4. **Hiệu chỉnh Sai số Mẫu Hữu hạn Windmeijer (2005) & Kiểm soát Số lượng Biến Công cụ:**
     - Ước lượng Two-Step GMM sử dụng ma trận trọng số tối ưu ước lượng từ phần dư bước một khiến sai số chuẩn quy ước bị đánh giá thấp nghiêm trọng trong mẫu hữu hạn. Hệ thống triển khai ma trận hiệu chỉnh $D$ theo Windmeijer (2005) để khôi phục độ tin cậy của kiểm định giả thuyết $z$ và khoảng tin cậy 95%.
     - Giới hạn độ trễ công cụ tối đa (`max_instrument_lags`) nhằm ngăn ngừa hiện tượng bùng nổ biến công cụ (instrument proliferation; Roodman 2009), hạn chế làm suy yếu kiểm định Hansen $J$.
  5. **Bộ Kiểm định Chẩn đoán Đặc tả Toàn diện:**
     - **Nickell Bounds Check:** Kiểm chứng xem ước lượng GMM có nằm trong khoảng kinh tế lượng hợp lệ $\hat{\alpha}_{\text{FE}} \le \hat{\alpha}_{\text{GMM}} \le \hat{\alpha}_{\text{OLS}}$ hay không.
     - **Arellano-Bond AR(1) & AR(2) Tests:** Kiểm định tự tương quan trong phần dư sai phân bậc nhất $\Delta \varepsilon_{i,t}$. Kỳ vọng $AR(1)$ có ý nghĩa thống kê ($p < .05$) do cấu trúc sai phân, và $AR(2)$ không có ý nghĩa thống kê ($p > .05$) để bảo đảm biến công cụ trễ bậc 2 không tương quan với sai số.
     - **Hansen $J$-Test:** Kiểm định tính ngoại sinh tổng thể của tập hợp biến công cụ vượt mức (overidentifying restrictions; $H_0$: các công cụ là hợp lệ, kỳ vọng $p > .05$).
  6. **Đồ thị SVG Kép Khoa học:**
     - Panel A: Forest Plot biểu diễn giới hạn Nickell bounds ($\hat{\alpha}_{\text{FE}}$, $\hat{\alpha}_{\text{GMM}}$, $\hat{\alpha}_{\text{OLS}}$) kèm khoảng tin cậy 95% và vạch giới hạn lý thuyết.
     - Panel B: Thẻ chẩn đoán kết quả kiểm định Arellano-Bond $AR(1)$, $AR(2)$ và Hansen $J$ với trạng thái PASS/FAIL trực quan.
  7. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn theo chuẩn mực kinh tế lượng Arellano & Bond (1991), Blundell & Bond (1998) và Windmeijer (2005).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/dynamic-panel-gmm`
- **Request Body (`DynamicPanelGMMRequest`):**
  - `unit_id_question_id`: UUID câu hỏi định danh đơn vị (Unit ID).
  - `time_question_id`: UUID câu hỏi đợt khảo sát / thời gian (Wave / Time).
  - `outcome_question_id`: UUID câu hỏi đo lường biến kết quả $Y$.
  - `covariate_question_ids`: Danh sách UUID các biến giải thích kiểm soát ngoại sinh $X$ (Tùy chọn).
  - `method`: `"system"` (Mặc định) hoặc `"difference"`.
  - `two_step`: `true` (Mặc định) hoặc `false`.
  - `windmeijer_correction`: `true` (Mặc định) hoặc `false`.
  - `max_instrument_lags`: Số độ trễ công cụ tối đa (Mặc định 3).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`DynamicPanelGMMOut`):**
  - `status`: `"SUCCESS"` hoặc `"INSUFFICIENT_SAMPLE"`.
  - `model_type`: `"DYNAMIC_PANEL_SYSTEM_GMM"` hoặc `"DYNAMIC_PANEL_DIFFERENCE_GMM"`.
  - `diagnostics`: Cỡ mẫu đơn vị bảng $N$, tổng quan sát $NT$, số đợt sóng thời gian $T$, số lượng biến công cụ, hệ số tự hồi quy $\hat{\alpha}_{\text{GMM}}$ kèm sai số chuẩn, cận trên OLS $\hat{\alpha}_{\text{OLS}}$, cận dưới Fixed Effects $\hat{\alpha}_{\text{FE}}$, kết quả kiểm tra Nickell bounds, thống kê kiểm định $AR(1)$, $AR(2)$ và Hansen $J$ kèm p-values.
  - `parameters`: Bảng chi tiết ước lượng tham số, sai số chuẩn hiệu chỉnh Windmeijer, z-statistic, p-value, khoảng tin cậy 95% và cờ ý nghĩa thống kê.
  - `svg_visualization`: Đồ thị SVG khoa học kép Nickell Bounds Forest Plot & Specification Test Scorecard.
  - `apa_narrative`: Đoạn thuyết minh học thuật chuẩn APA 7th Edition theo Blundell & Bond (1998) và Windmeijer (2005).
- **Niêm phong kiểm toán:** Tự động ghi nhận `DYNAMIC_PANEL_GMM_EVALUATED` vào chuỗi sổ cái SHA-256.


### 121. Weak-Instrument Robust Inference (Anderson-Rubin 1949, Moreira 2003 CLR, Montiel Olea & Pflueger 2013)

- **Mục đích & Cơ sở Khoa học:**
  1. **Khủng hoảng Công cụ Yếu trong Nghiên cứu Khảo sát & Kinh tế lượng (Weak Instruments Crisis):**
     - Trong các nghiên cứu khảo sát có biến can thiệp nội sinh (Endogenous Regressor $Y$), các biến công cụ ngoại sinh loại trừ $Z$ (ví dụ: khoảng cách địa lý, số xổ số, tháng sinh, chính sách trợ cấp ngẫu nhiên) thường có mối tương quan yếu với $Y$ ($\Pi \approx 0$).
     - Khi công cụ yếu ($F < 10$ theo quy tắc kinh nghiệm Nelson & Startz 1990; Staiger & Stock 1997; Stock & Yogo 2005), suy diễn thống kê chuẩn dựa trên ước lượng Two-Stage Least Squares (2SLS) bị sụp đổ hoàn toàn:
       - Ước lượng điểm 2SLS bị kéo lệch mạnh về phía ước lượng OLS.
       - Thống kê kiểm định Wald $t$-statistic không còn hội tụ về phân phối chuẩn $\mathcal{N}(0, 1)$, khiến tỷ lệ bác bỏ sai lầm (rejection rate) vượt quá 50% ngay cả ở mức ý nghĩa danh định $\alpha = 0.05$.
       - Khoảng tin cậy Wald quy ước $[b - 1.96 SE, b + 1.96 SE]$ có xác suất bao phủ thực tế cực thấp (chỉ 20% - 40%), dẫn đến các kết luận sai lầm về hiệu quả chính sách.
  2. **Đảo nghiệm Phương trình Bậc hai Chính xác Mẫu Hữu hạn Anderson-Rubin (Anderson & Rubin 1949):**
     - Dưới giả thuyết không $H_0: \beta = \beta_0$, phần dư cấu trúc $u(\beta_0) = \tilde{y} - \beta_0 \tilde{Y}$ hoàn toàn độc lập với các công cụ ngoại sinh $\tilde{Z}$.
     - Thống kê kiểm định Anderson-Rubin:
       $$AR(\beta_0) = \frac{u(\beta_0)' P_Z u(\beta_0) / k_z}{u(\beta_0)' M_Z u(\beta_0) / (N - k_x - k_z)} \sim F(k_z, N - k_x - k_z)$$
     - Thống kê $AR(\beta_0)$ tuân theo phân phối $F$ **chính xác trong mẫu hữu hạn mà không phụ thuộc vào độ mạnh của biến công cụ $\Pi$**, ngay cả khi công cụ hoàn toàn không định danh ($\Pi = 0$).
     - Tập tin cậy 95% Anderson-Rubin thu được bằng cách giải bất đẳng thức bậc hai $A \beta_0^2 + B \beta_0 + C \le 0$:
       - Khi công cụ đủ mạnh ($A > 0, \Delta \ge 0$): Tạo ra khoảng tin cậy hữu hạn $[r_1, r_2]$.
       - Khi công cụ yếu ($A < 0, \Delta \ge 0$): Tạo ra tập hợp tin cậy không bị chặn dạng hợp của hai nửa đường thẳng $(-\infty, r_1] \cup [r_2, \infty)$, phản ánh trung thực rằng dữ liệu không thể bác bỏ các giá trị hiệu ứng cực lớn.
       - Khi hoàn toàn không định danh: Bao phủ toàn bộ trục số thực $(-\infty, \infty)$.
  3. **Kiểm định Tỷ số Hợp lý Có điều kiện Moreira (Conditional Likelihood Ratio - Moreira 2003 Econometrica):**
     - Moreira (2003) phân rã dữ liệu thành hai thống kê đủ: $S(\beta_0)$ (đo lường độ lệch khỏi giả thuyết không) và $T(\beta_0)$ (đo lường độ mạnh thực tế của biến công cụ).
     - Thống kê CLR:
       $$CLR(\beta_0) = \frac{1}{2} \left[ S'S - T'T + \sqrt{(S'S - T'T)^2 + 4(S'T)^2} \right]$$
     - Andrews, Moreira, & Stock (2006 Econometrica) chứng minh toán học rằng kiểm định CLR là kiểm định mạnh nhất bất biến đồng đều (Uniformly Most Powerful Invariant - UMPI).
     - Khi công cụ rất mạnh ($T'T \to \infty$), $CLR$ tiệm cận kiểm định Lagrange Multiplier $K \sim \chi^2(1)$. Khi công cụ rất yếu ($T'T \to 0$), $CLR$ hội tụ về kiểm định Anderson-Rubin $AR \sim \chi^2(k_z)$.
  4. **Thống kê Hiệu quả Montiel Olea & Pflueger (2013 JBES Effective F-Statistic):**
     - Khắc phục giới hạn của quy tắc Stock & Yogo (2005) vốn chỉ đúng khi sai số đồng phương sai (homoskedastic).
     - Dưới sai số dị phương sai hoặc tự tương quan, $F_{\text{eff}} = \frac{\hat{\Pi}' (Z'Z) \hat{\Pi}}{\text{tr}(\text{meat}(Z'Z)^{-1})}$ so sánh với ngưỡng tới hạn khắt khe 23.11 (để độ chệch không vượt quá 10% ngưỡng chuẩn).
  5. **Đồ thị SVG Kép Khoa học:**
     - Panel A: Đồ thị hàm mục tiêu đảo nghiệm kiểm định (Test Inversion Curves) biểu diễn các đường cong $AR(\beta_0)$, $CLR(\beta_0)$, $K(\beta_0)$ qua lưới giá trị ứng viên $\beta_0$ cùng ngưỡng bác bỏ 95%.
     - Panel B: Biểu đồ Forest Plot so sánh trực quan các khoảng tin cậy 95%: Moreira CLR CI, Anderson-Rubin AR CI, Standard 2SLS Wald CI (cảnh báo méo kích thước), và OLS Benchmark.
  6. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn theo chuẩn mực kinh tế lượng Anderson & Rubin (1949), Moreira (2003), Andrews et al. (2006) và Montiel Olea & Pflueger (2013).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/weak-iv-robust`
- **Request Body (`WeakIVRobustRequest`):**
  - `outcome_question_id`: UUID câu hỏi đo lường kết quả phụ thuộc $Y$.
  - `endogenous_question_id`: UUID câu hỏi can thiệp nội sinh $Y_{\text{endog}}$.
  - `instrument_question_ids`: Danh sách UUID các câu hỏi biến công cụ loại trừ $Z$ ($\ge 1$).
  - `covariate_question_ids`: Danh sách UUID các biến hiệp biến kiểm soát ngoại sinh $X$ (Tùy chọn).
  - `alpha_level`: Mức ý nghĩa thống kê (Mặc định 0.05).
  - `grid_points`: Số điểm lưới tìm nghiệm Moreira CLR (Mặc định 120).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`WeakIVRobustOut`):**
  - `status`: `"SUCCESS"`, `"INSUFFICIENT_SAMPLE"`, hoặc `"ERROR"`.
  - `model_type`: `"WEAK_IV_ROBUST_MOREIRA_CLR_AR"`.
  - `diagnostics`: Cỡ mẫu $N$, số lượng công cụ $k_z$, First-stage $F$, Montiel Olea-Pflueger Effective $F$, Phân loại độ mạnh công cụ (`STRONG_IDENTIFICATION`, `MODERATE_IDENTIFICATION`, `WEAK_IDENTIFICATION`, `SEVERELY_WEAK_OR_UNIDENTIFIED`), Thống kê kiểm định Anderson-Rubin cho giả thuyết không vô hiệu $H_0: \beta=0$.
  - `estimates`: Điểm ước lượng 2SLS $\hat{\beta}_{\text{2SLS}}$ kèm sai số chuẩn và Wald CI 95%, Điểm ước lượng OLS, Loại tập tin cậy Anderson-Rubin (`BOUNDED_INTERVAL`, `DISJOINT_UNBOUNDED`, `ENTIRE_REAL_LINE`), Khoảng tin cậy chính xác Anderson-Rubin 95%, Khoảng tin cậy Moreira CLR 95%, Khoảng tin cậy Kleibergen K 95%.
  - `svg_visualization`: Đồ thị SVG khoa học kép Test Inversion Curves & Robust Forest Plot.
  - `apa_narrative`: Đoạn thuyết minh học thuật chuẩn APA 7th Edition.
- **Niêm phong kiểm toán:** Tự động ghi nhận `WEAK_IV_ROBUST_EVALUATED` vào chuỗi sổ cái SHA-256.


### 122. Sequential Causal Mediation & Path-Specific Decomposition (Hayes Model 6, Imai & Yamamoto 2013)

- **Mục đích & Cơ sở Khoa học:**
  1. **Hạn chế của Mô hình Trung gian Song song (Parallel Mediation Flaw):**
     - Trong các nghiên cứu hành vi và chính sách, các biến trung gian thường không hoạt động độc lập mà diễn ra theo chuỗi tuần tự thời gian: can thiệp $T$ tác động lên trung gian cấp 1 $M_1$ (ví dụ: nhận thức về sự minh bạch), $M_1$ tác động lên trung gian cấp 2 $M_2$ (ví dụ: niềm tin thể chế), và $M_2$ dẫn tới kết quả $Y$ (ví dụ: sẵn sàng chia sẻ dữ liệu).
     - Mô hình trung gian song song (Preacher & Hayes 2008) giả định $M_1 \perp M_2 \mid T, X$. Khi $M_1 \to M_2$, mô hình song song bị chệch nghiêm trọng do bỏ sót yếu tố gây nhiễu trung gian bị ảnh hưởng bởi can thiệp (treatment-induced mediator-outcome confounding; VanderWeele et al. 2014).
  2. **Phân rã Đường dẫn Causal 4 Thành phần Riêng biệt (Path-Specific Decomposition):**
     - Mô hình cấu trúc Hayes Model 6 (Imai & Yamamoto 2013 JRSS-B):
       $$M_{1, i} = \alpha_1 + a_1 T_i + \gamma_1' X_i + \varepsilon_{1, i}$$
       $$M_{2, i} = \alpha_2 + a_2 T_i + d_{21} M_{1, i} + \gamma_2' X_i + \varepsilon_{2, i}$$
       $$Y_i = \alpha_y + c' T_i + b_1 M_{1, i} + b_2 M_{2, i} + \gamma_y' X_i + \varepsilon_{y, i}$$
     - Tổng hiệu ứng can thiệp $TE = c$ được phân rã thành:
       - **Hiệu ứng Trực tiếp (Direct Effect - DE):** $c'$ (tác động của $T$ lên $Y$ không qua bất kỳ trung gian nào).
       - **Đường dẫn Đơn lập 1 (Specific Indirect Path 1):** $a_1 \times b_1$ ($T \to M_1 \to Y$ độc lập).
       - **Đường dẫn Đơn lập 2 (Specific Indirect Path 2):** $a_2 \times b_2$ ($T \to M_2 \to Y$ độc lập).
       - **Đường dẫn Tuần tự (Sequential Indirect Path):** $a_1 \times d_{21} \times b_2$ ($T \to M_1 \to M_2 \to Y$ phản ánh cơ chế chuỗi xích thực thụ).
       - **Tổng Hiệu ứng Gián tiếp (Total Indirect Effect):** $IE_{\text{total}} = a_1 b_1 + a_2 b_2 + a_1 d_{21} b_2$.
       - Đảm bảo tính nhất quán đại số tuyệt đối: $TE \equiv DE + IE_{\text{total}}$.
  3. **Suy diễn Thống kê Phân vị Bootstrap Phi Tham số (Non-parametric Percentile Bootstrap):**
     - Do tích của các hệ số hồi quy $(a_1 d_{21} b_2)$ không có phân phối chuẩn ngay cả trong mẫu lớn, phương pháp kiểm định Sobel truyền thống có độ chệch lớn và lực kiểm định yếu.
     - Hệ thống thực hiện tái chọn mẫu bootstrap phi tham số $B$ lần lặp (mặc định 500-1000) để thiết lập khoảng tin cậy phân vị 95% chính xác cho từng đường dẫn causal.
  4. **Tỷ lệ Hòa giải và Tác động Chính sách:**
     - Tính toán tỷ lệ trung gian tổng $P_{\text{total}} = IE_{\text{total}} / TE$ và tỷ lệ đường dẫn tuần tự $P_{\text{seq}} = IE_{\text{seq}} / TE$ giúp các nhà nghiên cứu xác định chính xác nút thắt can thiệp hành vi có hiệu quả cao nhất.
  5. **Đồ thị SVG Kép Khoa học:**
     - Panel A: Sơ đồ đường dẫn DAG cấu trúc chuẩn mực với các hệ số đường dẫn $(a_1, a_2, d_{21}, b_1, b_2, c')$, mũi tên định hướng và liên kết chuỗi nổi bật màu Indigo.
     - Panel B: Biểu đồ Forest Plot so sánh các đường dẫn gián tiếp và trực tiếp kèm khoảng tin cậy phân vị bootstrap 95% và nhãn ý nghĩa thống kê.
  6. **Đoạn Thuyết minh Học thuật Chuẩn APA 7th Edition:**
     - Tự động biên soạn theo chuẩn mực kinh tế lượng và tâm lý học Hayes (2017) và Imai & Yamamoto (2013).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/sequential-mediation`
- **Request Body (`SequentialMediationRequest`):**
  - `treatment_question_id`: UUID câu hỏi đo lường biến can thiệp $T$.
  - `mediator1_question_id`: UUID câu hỏi biến trung gian cấp 1 $M_1$.
  - `mediator2_question_id`: UUID câu hỏi biến trung gian cấp 2 $M_2$.
  - `outcome_question_id`: UUID câu hỏi đo lường kết quả $Y$.
  - `covariate_question_ids`: Danh sách UUID các biến kiểm soát ngoại sinh $X$ (Tùy chọn).
  - `n_bootstraps`: Số lần tái chọn mẫu bootstrap (Mặc định 500).
  - `alpha_level`: Mức ý nghĩa thống kê (Mặc định 0.05).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`SequentialMediationOut`):**
  - `status`: `"SUCCESS"`, `"INSUFFICIENT_SAMPLE"`, hoặc `"ERROR"`.
  - `model_type`: `"SEQUENTIAL_CAUSAL_MEDIATION_HAYES_6"`.
  - `sample_size`: Cỡ mẫu phân tích $N$.
  - `bootstrap_replications`: Số lần lặp bootstrap hợp lệ.
  - `effects`: Chi tiết ước lượng điểm, sai số chuẩn bootstrap, khoảng tin cậy 95% và cờ ý nghĩa cho: `direct_effect`, `indirect_path1_m1`, `indirect_path2_m2`, `indirect_sequential_m1_m2`, `indirect_total`, `total_effect`.
  - `proportions`: Tỷ lệ trung gian tổng (`proportion_mediated_total`) và tỷ lệ đường dẫn tuần tự (`proportion_mediated_sequential`).
  - `regression_equations`: Hệ số hồi quy OLS và hệ số xác định $R^2$ cho 3 phương trình cấu trúc của $M_1$, $M_2$, $Y$.
  - `svg_visualization`: Đồ thị SVG khoa học kép Structural Path DAG & Bootstrap Forest Plot.
  - `apa_narrative`: Thuyết minh học thuật chuẩn APA 7th Edition theo Hayes Model 6.
- **Niêm phong kiểm toán:** Tự động ghi nhận `SEQUENTIAL_MEDIATION_EVALUATED` vào chuỗi sổ cái SHA-256.

### 123. Post-Double-Selection Lasso Engine for High-Dimensional Confounders (Belloni, Chernozhukov, & Hansen 2014 Restud)
- **Mục tiêu:** Cung cấp động cơ ước lượng hiệu ứng nhân quả $D \to Y$ trong bối cảnh khảo sát nhiều chiều ($p \gg N$ hoặc số lượng biến kiểm soát tiềm năng rất lớn: nhân khẩu học chi tiết, hành vi kỹ thuật số, tương tác chéo). Giải quyết triệt để vấn đề chệch lựa chọn biến (variable selection bias) và hiện tượng sụp đổ suy diễn thống kê (inferential breakdown) của Lasso tiêu chuẩn một bước bằng cách thực hiện chọn lọc kép trực giao Neyman (Neyman Orthogonal Post-Double-Selection).
- **Nguyên lý Toán học & Cấu trúc:**
  1. **Khuyết tật của Lasso thông thường:** Khi áp dụng Lasso trực tiếp lên phương trình kết quả $Y = \alpha_0 + \alpha D + X'\beta + \varepsilon$, bất kỳ biến kiểm soát $X_j$ nào có tương quan mạnh với biến can thiệp $D$ nhưng có tương quan trung bình/yếu với kết quả $Y$ (hệ số $O(1/\sqrt{N})$) sẽ bị Lasso triệt tiêu về 0. Sự bỏ sót biến này gây chệch hệ số can thiệp $\hat{\alpha}$ cỡ $O(1)$ ngay cả khi cỡ mẫu $N \to \infty$.
  2. **Quy trình Lựa chọn Kép (Belloni et al. 2014):**
     - **Bước 1 (Lựa chọn dự báo kết quả):** Chạy Lasso phạt $L_1$ từ kết quả $Y$ lên toàn bộ tập covariates $X$:
       $$\hat{\beta} = \arg\min_\beta \frac{1}{2N} \|Y - X\beta\|_2^2 + \lambda_y \sum_{j=1}^p \|\beta_j\|_1$$
       Thu thập tập chỉ số biến kiểm soát được chọn: $I_1 = \{j: \hat{\beta}_j \neq 0\}$.
     - **Bước 2 (Lựa chọn dự báo can thiệp):** Chạy Lasso phạt $L_1$ từ biến can thiệp $D$ lên toàn bộ tập covariates $X$:
       $$\hat{\gamma} = \arg\min_\gamma \frac{1}{2N} \|D - X\gamma\|_2^2 + \lambda_d \sum_{j=1}^p \|\gamma_j\|_1$$
       Thu thập tập chỉ số biến kiểm soát được chọn: $I_2 = \{j: \hat{\gamma}_j \neq 0\}$.
     - **Bước 3 (Hợp nhất và Ước lượng Post-OLS Trực giao):** Lấy hợp tập biến $I_{\text{union}} = I_1 \cup I_2$. Ước lượng OLS không bị phạt trên mô hình:
       $$Y_i = \alpha D_i + X_{i, I_{\text{union}}}' \beta_{I_{\text{union}}} + \varepsilon_i$$
       Đảm bảo tính trực giao Neyman (Neyman Orthogonality), cho phép phân phối chuẩn tiệm cận chuẩn hóa $\sqrt{N}(\hat{\alpha} - \alpha) \stackrel{d}{\to} \mathcal{N}(0, V)$ với sai số chuẩn vững phương sai thay đổi White/Huber-White HC1.
  3. **Lựa chọn Tham số Phạt Tối ưu (Penalization Tuning):**
     - Hỗ trợ cả hai chế độ:
       - **K-Fold Cross-Validation (K-Fold CV):** Lựa chọn $\lambda$ qua 5-Fold CV giảm thiểu sai số dự báo ngoài mẫu.
       - **Lý thuyết Tiệm cận Belloni (Theory-Driven Rigorous Penalty):** $\lambda_{\text{theory}} = 1.1 \times 2 \hat{\sigma} \sqrt{2 \ln(2p / \alpha_c)} / \sqrt{N}$, bảo toàn sparsity tiệm cận.
  4. **Chỉ số Chẩn đoán Trực giao & Đồ thị SVG Khoa học:**
     - Tỷ lệ co cụm (Sparsity ratio) $|I_{\text{union}}| / p$.
     - Ma trận phân loại biến: Được chọn bởi cả $Y$ và $D$, chỉ bởi $Y$, chỉ bởi $D$, hoặc bị loại bỏ.
     - Forest Plot SVG so sánh trực quan ước lượng Post-Double-Selection OLS vs Naive OLS (toàn bộ $X$) vs Simple OLS (không có $X$), minh họa sai số và sự bảo toàn tính vững.
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/post-double-selection-lasso`
- **Request Body (`PostDoubleSelectionLassoRequest`):**
  - `treatment_question_id`: UUID biến can thiệp/điều trị $D$.
  - `outcome_question_id`: UUID biến kết quả khảo sát $Y$.
  - `candidate_covariate_ids`: Danh sách UUID các biến kiểm soát tiềm năng $X$ (nhiều chiều).
  - `alpha_level`: Mức ý nghĩa thống kê (Mặc định 0.05).
  - `penalty_selection`: Phương pháp chọn $\lambda$ (`"cv"` hoặc `"theory"`).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`PostDoubleSelectionLassoOut`):**
  - `status`: `"SUCCESS"`, `"INSUFFICIENT_SAMPLE"`, hoặc `"ERROR"`.
  - `model_type`: `"POST_DOUBLE_SELECTION_LASSO_BELLONI_2014"`.
  - `sample_size`: Cỡ mẫu phân tích $N$.
  - `num_candidates`: Số lượng biến kiểm soát ứng viên $p$.
  - `num_selected_union`: Số biến kiểm soát được chọn vào mô hình cuối $|I_{\text{union}}|$.
  - `selected_controls`: Danh sách chi tiết từng biến được chọn (tên, nguồn chọn: $Y$, $D$, hoặc cả hai, hệ số hồi quy).
  - `estimates`: Ước lượng hệ số can thiệp của 3 mô hình (Post-Double-Selection, Naive full controls, Simple no controls) với SE vững HC1, t-stat, p-value, 95% CI.
  - `diagnostics`: $\lambda_y$, $\lambda_d$, $R^2$, F-stat, sparsity ratio.
  - `svg_visualization`: Đồ thị SVG so sánh Forest Plot ước lượng can thiệp và phân bổ biến chọn lọc.
  - `apa_narrative`: Báo cáo học thuật chuẩn mực APA 7th Edition theo Belloni et al. (2014).
- **Niêm phong kiểm toán:** Ghi nhận `POST_DOUBLE_SELECTION_LASSO_EVALUATED` vào chuỗi sổ cái SHA-256.

### 124. Instrumental Variable Local Average Response Function (LARF; Abadie 2003 Econometrica)
- **Mục tiêu:** Nhận diện và ước lượng hàm phản ứng nhân quả bán tham số cho các kết quả khảo sát phi tuyến hoặc bị chặn (nhị phân $Y \in \{0, 1\}$, điểm hài lòng bị chặn $Y \in [0, 1]$, hoặc tỷ lệ phần trăm) dưới điều kiện biến can thiệp nội sinh $D \in \{0, 1\}$ có biến công cụ $Z \in \{0, 1\}$ mà không bị ép buộc vào các giả định tuyến tính sai lệch của 2SLS (vốn sinh ra giá trị dự báo vượt khỏi $[0, 1]$).
- **Nguyên lý Toán học & Cấu trúc:**
  1. **Định lý Nhận diện Trọng số Abadie Kappa (Abadie 2003 Econometrica):**
     - Dưới giả định tính độc lập của công cụ $Z \perp (Y(1), Y(0), D(1), D(0)) \mid X$ và tính đơn điệu (Monotonicity / No-Defiers: $P(D(1) \ge D(0) \mid X) = 1$ theo Imbens & Angrist 1994), kỳ vọng của bất kỳ hàm đo lường được nào $g(Y, D, X)$ trên phân nhóm người tuân thủ (Compliers: $D(1) > D(0)$) được xác định bằng:
       $$E[g(Y, D, X) \mid D(1) > D(0)] = \frac{E[\kappa \cdot g(Y, D, X)]}{P(D(1) > D(0))}$$
     - Hàm trọng số Abadie $\kappa$ được định nghĩa:
       $$\kappa = 1 - \frac{D(1 - Z)}{1 - P(Z=1 \mid X)} - \frac{(1 - D)Z}{P(Z=1 \mid X)}$$
     - Xác suất tuân thủ trong quần thể khảo sát: $P(\text{Compliers}) = E[\kappa]$.
  2. **Ước lượng Hàm Phản ứng Cục bộ (Local Average Response Function - LARF):**
     - Xác suất công cụ $e(X) = P(Z=1 \mid X)$ được ước lượng thông qua hồi quy Logistic với chuẩn hóa L2.
     - Hàm phản ứng được tối ưu hóa có trọng số $\kappa$:
       $$\hat{\theta} = \arg\min_\theta \sum_{i=1}^N \kappa_i \ell(Y_i, \mu(D_i, X_i; \theta))$$
       Trong đó $\mu(D, X; \theta)$ là hàm liên kết Logit $\Lambda(D, X; \theta)$ hoặc Linear $D\alpha + X'\beta$.
     - Hiệu ứng can thiệp trung bình cục bộ trên nhóm tuân thủ (LATE on Compliers):
       $$\text{LATE} = \frac{\sum_{i=1}^N \kappa_i [\mu(1, X_i; \hat{\theta}) - \mu(0, X_i; \hat{\theta})]}{\sum_{i=1}^N \kappa_i}$$
  3. **Xử lý Trọng số Âm & Cỡ Mẫu Hữu Hiệu (Frölich 2007):**
     - Do phương sai mẫu trong $\hat{e}(X)$, trọng số $\kappa_i$ có thể rơi vào vùng âm. Hệ thống hỗ trợ chế độ cắt trọng số $\kappa_i^+ = \max(0, \kappa_i)$ và báo cáo tỷ lệ trọng số âm $\%(\kappa < 0)$ cùng cỡ mẫu hữu hiệu Kish $N_{\text{eff}} = (\sum \kappa_i)^2 / \sum \kappa_i^2$.
  4. **Suy diễn Thống kê Bootstrap Phi Tham số (Non-parametric Bootstrap):**
     - Thực hiện tái chọn mẫu bootstrap $B$ lần (tái ước lượng đồng thời cả hàm xu hướng công cụ $\hat{e}(X)$ và mô hình kết quả $\hat{\theta}$) để cung cấp sai số chuẩn vững và khoảng tin cậy 95% chính xác.
  5. **Đồ thị SVG Kép Khoa học:**
     - Panel A: Forest Plot so sánh LATE (LARF Compliers) vs ITT ($Z \to Y$) vs Naive Association ($D \to Y$).
     - Panel B: Phân bố mật độ trọng số Abadie Kappa với vùng phân tách $\kappa \ge 0$ và $\kappa < 0$.
  6. **Báo cáo Học thuật APA 7th Edition:** Tự động biên soạn theo chuẩn Abadie (2003) và Imbens & Angrist (1994).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/larf`
- **Request Body (`LARFRequest`):**
  - `outcome_question_id`: UUID biến kết quả khảo sát $Y$.
  - `treatment_question_id`: UUID biến can thiệp nhị phân nội sinh $D$.
  - `instrument_question_id`: UUID biến công cụ ngoại sinh $Z$.
  - `covariate_question_ids`: Danh sách UUID các biến kiểm soát tiền can thiệp $X$.
  - `model_type`: `"logit"` (mặc định) hoặc `"linear"`.
  - `alpha_level`: Mức ý nghĩa thống kê (Mặc định 0.05).
  - `n_bootstraps`: Số lần tái chọn mẫu bootstrap (Mặc định 300).
  - `trim_negative`: Boolean tùy chọn cắt trọng số âm về 0.
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`LARFOut`):**
  - `status`: `"SUCCESS"`, `"INSUFFICIENT_SAMPLE"`, hoặc `"ERROR"`.
  - `model_type`: `"LARF_LOGIT_ABADIE_2003"` hoặc `"LARF_LINEAR_ABADIE_2003"`.
  - `sample_size`: Cỡ mẫu phân tích $N$.
  - `effective_sample_size`: Cỡ mẫu hữu hiệu $N_{\text{eff}}$.
  - `complier_probability`: Tỷ lệ tuân thủ ước tính $P(\text{Compliers}) = E[\kappa]$ kèm sai số chuẩn `complier_probability_se`.
  - `pct_negative_weights`: Tỷ lệ phần trăm mẫu mang trọng số $\kappa < 0$.
  - `potential_outcomes_compliers`: Kỳ vọng phản ứng tiềm năng $E[Y(1) \mid c]$ và $E[Y(0) \mid c]$.
  - `effects`: Chi tiết ước lượng, SE bootstrap, z-statistic, p-value, 95% CI cho: `late` (Compliers), `naive`, `itt`.
  - `model_coefficients`: Danh sách hệ số mô hình hồi quy.
  - `svg_visualization`: Đồ thị SVG trực quan hóa kép Forest Plot & Phân bổ Kappa.
  - `apa_narrative`: Báo cáo học thuật chuẩn mực APA 7th Edition.
- **Niêm phong kiểm toán:** Ghi nhận `LARF_EVALUATED` vào chuỗi sổ cái SHA-256.

### 125. Marginal Treatment Effects (MTE) & Local Instrumental Variables (LIV) Engine (Heckman & Vytlacil 1999, 2005 Econometrica)
- **Mục tiêu:** Cung cấp động cơ kinh tế lượng cấu trúc Nobel giải quyết toàn diện bài toán bất đồng nhất hiệu ứng can thiệp (heterogeneous treatment effects) và tự lựa chọn (Roy selection). Nhận diện đường cong phản ứng can thiệp cận biên $\Delta^{\text{MTE}}(u_D)$ liên tục theo mức độ kháng cự không quan sát được $U_D \in (0, 1)$, từ đó tích phân thống nhất toàn bộ các tham số chính sách kinh tế lượng: ATE, ATT, ATU, LATE, và PRTE.
- **Nguyên lý Toán học & Cấu trúc:**
  1. **Mô hình Roy Tổng quát (Generalized Roy Model):**
     - Kết quả tiềm năng: $Y(1) = \mu_1(X) + U_1$, $Y(0) = \mu_0(X) + U_0$.
     - Phương trình lựa chọn ngưỡng: $D = \mathbf{1}\{ P(Z) \ge U_D \}$, trong đó $P(Z) = \Pr(D=1 \mid Z)$ là điểm xu hướng (propensity score), và $U_D \sim \text{Uniform}(0, 1)$ đại diện cho sức cản vô hình đối với việc tham gia điều trị (unobserved resistance to treatment).
     - Kết quả quan sát: $Y = D Y(1) + (1 - D) Y(0)$.
  2. **Định lý Nhận diện Biến công cụ Cục bộ (Local Instrumental Variables - LIV; Heckman & Vytlacil 1999):**
     - Dưới điều kiện độc lập của công cụ $Z \perp (U_0, U_1, U_D) \mid X$:
       $$E[Y \mid X = x, P(Z) = p] = E[Y(0) \mid X = x] + \int_0^p \Delta^{\text{MTE}}(x, u) \, du$$
     - Theo Định lý cơ bản của Giải tích (Fundamental Theorem of Calculus):
       $$\Delta^{\text{MTE}}(x, u) = \left. \frac{\partial E[Y \mid X = x, P(Z) = p]}{\partial p} \right|_{p = u}$$
       Đạo hàm của kỳ vọng có điều kiện theo propensity score chính là Hiệu ứng Can thiệp Cận biên tại mức kháng cự $u_D = p$!
  3. **Ước lượng Bán tham số Đa thức (Carneiro, Heckman, & Vytlacil 2011 AER; Brinch et al. 2017 JPE):**
     - Ước lượng $P(Z, X)$ qua mô hình Probit, xác lập vùng hỗ trợ chung (common support $[p_{\min}, p_{\max}]$).
     - Ước lượng mô hình kết quả linh hoạt: $E[Y \mid X, P] = X'\beta + \sum_{k=1}^K \gamma_k P^k$.
     - Tính toán giải tích đường cong: $\Delta^{\text{MTE}}(\bar{X}, u) = \sum_{k=1}^K k \cdot \gamma_k u^{k-1}$.
  4. **Tích phân Thống nhất các Tham số Chính sách (Unified Policy Parameters):**
     - **ATE (Average Treatment Effect):** $\int_0^1 \text{MTE}(u) \, du$ (Trọng số đồng đều $w(u) = 1$).
     - **ATT (Effect on the Treated):** $\int_0^1 \text{MTE}(u) \cdot w_{\text{ATT}}(u) \, du$, với $w_{\text{ATT}}(u) = \frac{\Pr(P > u)}{E[P]}$.
     - **ATU (Effect on the Untreated):** $\int_0^1 \text{MTE}(u) \cdot w_{\text{ATU}}(u) \, du$, với $w_{\text{ATU}}(u) = \frac{\Pr(P \le u)}{1 - E[P]}$.
     - **LATE (Local Average Treatment Effect):** $\frac{1}{p_{75} - p_{25}} \int_{p_{25}}^{p_{75}} \text{MTE}(u) \, du$.
     - **PRTE (Policy-Relevant Treatment Effect):** Tác động của chính sách mở rộng trợ cấp/khuyến khích làm dịch chuyển phân phối $P \to P^*$:
       $$\text{PRTE} = \int_0^1 \text{MTE}(u) \cdot \frac{F_P(u) - F_{P^*}(u)}{E[P^*] - E[P]} \, du$$
  5. **Chẩn đoán Lựa chọn Roy (Roy Selection Sorting Diagnosis):**
     - Đánh giá độ dốc đường cong MTE: Nếu dốc âm ($d\text{MTE}/du_D < 0$), cá nhân có kháng cự thấp (hăng hái tham gia) đạt hiệu quả cao nhất (Positive selection on gains / Roy sorting). Nếu dốc dương, xảy ra Negative selection.
  6. **Đồ thị SVG Kép Khoa học:**
     - Panel A: Đường cong MTE $\Delta^{\text{MTE}}(u_D)$ kèm dải tin cậy Bootstrap 95%, đường tham chiếu Null (0.0), ATE và ATT.
     - Panel B: Đường cong hàm trọng số $w_{\text{ATT}}(u)$ vs $w_{\text{ATU}}(u)$ minh họa nguồn gốc sai lệch tự lựa chọn.
  7. **Báo cáo Học thuật Chuẩn APA 7th Edition:** Tự động biên soạn theo Heckman & Vytlacil (2005).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/mte`
- **Request Body (`MTERequest`):**
  - `outcome_question_id`: UUID biến kết quả khảo sát $Y$.
  - `treatment_question_id`: UUID biến can thiệp nhị phân nội sinh $D$.
  - `instrument_question_ids`: Danh sách UUID các biến công cụ ngoại sinh $Z_1, Z_2, \dots$.
  - `covariate_question_ids`: Danh sách UUID các biến kiểm soát tiền can thiệp $X$.
  - `poly_degree`: Bậc đa thức bán tham số (Mặc định 3: Cubic).
  - `alpha_level`: Mức ý nghĩa thống kê (Mặc định 0.05).
  - `n_bootstraps`: Số lần tái chọn mẫu bootstrap (Mặc định 300).
  - `policy_shift_pct`: Tỷ lệ phần trăm dịch chuyển chính sách cho PRTE (Mặc định 0.15: +15%).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`MTEOut`):**
  - `status`: `"SUCCESS"`, `"INSUFFICIENT_SAMPLE"`, hoặc `"ERROR"`.
  - `model_type`: `"MARGINAL_TREATMENT_EFFECTS_HECKMAN_VYTLACIL_2005"`.
  - `sample_size`: Cỡ mẫu phân tích $N$.
  - `bootstrap_replications`: Số lần lặp bootstrap $B$.
  - `polynomial_degree`: Bậc đa thức đã khớp $K$.
  - `common_support`: Ngưỡng hỗ trợ chung $[p_{\min}, p_{\max}]$.
  - `selection_sorting_pattern`: Phân loại quy luật lựa chọn Roy (Positive / Negative / Homogeneous).
  - `mte_slope`: Độ dốc đường cong MTE.
  - `parameters`: Chi tiết ước lượng, SE bootstrap, z-statistic, p-value, 95% CI cho: `ate`, `att`, `atu`, `late`, `prte`.
  - `mte_curve`: Danh sách 50 điểm tọa độ trên đường cong $(u_D, \text{MTE}, \text{SE}, \text{CI}_{\text{low}}, \text{CI}_{\text{high}}, w_{\text{ATT}}, w_{\text{ATU}})$.
  - `svg_visualization`: Đồ thị SVG trực quan hóa kép đường cong MTE và trọng số chính sách.
  - `apa_narrative`: Báo cáo học thuật chuẩn mực APA 7th Edition theo Heckman & Vytlacil (2005).
- **Niêm phong kiểm toán:** Ghi nhận `MTE_EVALUATED` vào chuỗi sổ cái SHA-256.

### 126. Non-random Survey Attrition & Selection Bounds Engine (Lee Bounds; Lee 2009 Restud)
- **Mục tiêu:** Cung cấp động cơ xác lập cận phi tham số sắc nét (sharp non-parametric bounds) bảo vệ suy diễn nhân quả trước hiện tượng hao hụt mẫu không ngẫu nhiên (non-random attrition), mất liên lạc theo dõi (loss to follow-up), hoặc từ chối báo cáo chọn lọc (selective reporting) trong các khảo sát theo chiều dọc, nghiên cứu thử nghiệm can thiệp hoặc bảng lặp lại.
- **Nguyên lý Toán học & Cấu trúc:**
  1. **Hạn chế của Phân tích Hoàn tất Mẫu (Naive Complete-Case Analysis):** Khi tỷ lệ phản hồi giữa nhóm can thiệp và đối chứng chênh lệch ($P(R=1 \mid T=1) \neq P(R=1 \mid T=0)$), việc chỉ phân tích những người hoàn thành khảo sát sẽ tạo ra chệch lựa chọn thành phần (compositional selection bias), làm sai lệch dấu và độ lớn của hiệu ứng thực tế.
  2. **Định lý Cận Sắc nét Lee (Lee 2009 Review of Economic Studies):**
     - Dưới giả định tính đơn điệu (Monotonicity: can thiệp chỉ thúc đẩy phản hồi theo một hướng, $R_i(1) \ge R_i(0)$ đối với mọi cá nhân), tỷ lệ phản hồi thặng dư trong nhóm có tỷ lệ phản hồi cao hơn là:
       $$q = \frac{|P(R=1 \mid T=1) - P(R=1 \mid T=0)|}{\max(P(R=1 \mid T=1), P(R=1 \mid T=0))}$$
     - Cắt tỉa (trimming) tỷ lệ $q$ ở hai đầu phân phối kết quả $Y$ của nhóm có độ phản hồi cao:
       - **Cận Dưới ($\Delta_{LB}$):** Cắt bỏ $q$ phân vị cao nhất của $Y$ (kịch bản bảo thủ nhất khi người phản hồi thêm đều có điểm số cao vượt trội).
       - **Cận Trên ($\Delta_{UB}$):** Cắt bỏ $q$ phân vị thấp nhất của $Y$ (kịch bản thuận lợi nhất khi người phản hồi thêm đều có điểm số thấp).
       Khoảng $[\Delta_{LB}, \Delta_{UB}]$ đại diện cho cận sắc nét tuyệt đối của hiệu ứng can thiệp đối với phân nhóm luôn luôn phản hồi ("always-reporters").
  3. **Thắt chặt Cận qua Phân tầng Biến kiểm soát (Covariate-Tightened Lee Bounds):**
     - Khi có sẵn các biến nhân khẩu học hoặc tiền can thiệp $X$, tỷ lệ cắt gọt $q(x)$ được tính toán trong từng tầng phân vị $x$, và các cận phân tầng được tích hợp có trọng số theo quy mô mẫu:
       $$\Delta_{LB}^{\text{tight}} = \sum_x w(x) \Delta_{LB}(x), \quad \Delta_{UB}^{\text{tight}} = \sum_x w(x) \Delta_{UB}(x)$$
       giúp thu hẹp đáng kể khoảng bất định $[\Delta_{LB}, \Delta_{UB}]$.
  4. **Suy diễn Thống kê Imbens-Manski (2004 Econometrica) / Stoye (2009):**
     - Do tham số được nhận diện theo khoảng (partially identified), việc áp dụng sai số chuẩn $1.96 \times SE$ ở cả hai đầu sẽ tạo ra độ bao phủ bảo thủ quá mức. Hệ thống tính toán giá trị tới hạn chính xác $c_\alpha$ thỏa mãn:
       $$\Phi\left( c_\alpha + \frac{\hat{\Delta}_{UB} - \hat{\Delta}_{LB}}{\max(\hat{SE}_{LB}, \hat{SE}_{UB})} \right) - \Phi(-c_\alpha) = 1 - \alpha$$
       cung cấp khoảng tin cậy 95% chuẩn xác nhất $\text{CI}_{95\%} = [\hat{\Delta}_{LB} - c_\alpha \hat{SE}_{LB}, \, \hat{\Delta}_{UB} + c_\alpha \hat{SE}_{UB}]$.
  5. **Đồ thị SVG Kép Khoa học:**
     - Panel A: Forest Plot so sánh Naive OLS vs Sharp Unconditional Lee Bounds vs Tightened Bounds kèm dải tin cậy Imbens-Manski 95% và đường tham chiếu Null (0.0).
     - Panel B: Biểu đồ thanh tỷ lệ duy trì mẫu (Treated Retention vs Control Retention) và tỷ lệ cắt gọt thặng dư $q$.
  6. **Báo cáo Học thuật Chuẩn APA 7th Edition:** Tự động biên soạn theo chuẩn Lee (2009) và Horowitz & Manski (2000).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/lee-bounds`
- **Request Body (`LeeBoundsRequest`):**
  - `outcome_question_id`: UUID biến kết quả theo dõi $Y$.
  - `treatment_question_id`: UUID biến can thiệp nhị phân $T$.
  - `response_question_id`: UUID biến chỉ báo phản hồi $R$ (Tùy chọn; tự động nhận diện giá trị thiếu nếu bỏ trống).
  - `covariate_question_ids`: Danh sách UUID các biến kiểm soát tiền can thiệp để thắt chặt cận $X$.
  - `alpha_level`: Mức ý nghĩa thống kê (Mặc định 0.05).
  - `n_bootstraps`: Số lần tái chọn mẫu bootstrap (Mặc định 300).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`LeeBoundsOut`):**
  - `status`: `"SUCCESS"`, `"INSUFFICIENT_SAMPLE"`, hoặc `"ERROR"`.
  - `model_type`: `"LEE_BOUNDS_RESTUD_2009"`.
  - `sample_size`: Tổng cỡ mẫu phân tích $N$.
  - `observed_sample_size`: Số lượng đối tượng có dữ liệu kết quả quan sát được.
  - `response_rates`: Tỷ lệ phản hồi nhóm can thiệp, nhóm đối chứng, độ chênh lệch, tỷ lệ cắt gọt $q$, nhóm bị cắt tỉa.
  - `bounds`: Chi tiết cận không điều kiện (`lower_bound`, `upper_bound`, SE, Imbens-Manski CI, cờ `excludes_zero`) và cận thắt chặt bằng biến kiểm soát.
  - `naive_complete_case`: Ước lượng ngây thơ bỏ qua hao hụt kèm SE và CI.
  - `svg_visualization`: Đồ thị SVG trực quan hóa kép Forest Plot & Tỷ lệ hao hụt.
  - `apa_narrative`: Thuyết minh học thuật chuẩn mực APA 7th Edition theo Lee (2009).
- **Niêm phong kiểm toán:** Ghi nhận `LEE_BOUNDS_EVALUATED` vào chuỗi sổ cái SHA-256.

### 127. Surrogate Index & Long-Term Causal Evaluation Engine (Athey, Chetty, Imbens, & Kang 2019 Econometrica)
- **Mục tiêu:** Giải quyết triệt để vấn đề độ trễ thời gian (Horizon Gap) trong nghiên cứu khảo sát và đánh giá can thiệp: kết quả dài hạn $Y$ (như thu nhập 5 năm, lòng trung thành thương hiệu dài hạn, sức khỏe mãn tính) chỉ quan sát được sau nhiều năm, trong khi quyết định can thiệp cần phản hồi nhanh chóng. Động cơ kết hợp mẫu khảo sát thử nghiệm ngắn hạn (có can thiệp $W$ và các biến đại diện $S$) với mẫu theo dõi quan sát (có $S$ và kết quả dài hạn $Y$) để dự phóng chính xác hiệu ứng nhân quả dài hạn $\tau_Y$.
- **Nguyên lý Toán học & Cấu trúc:**
  1. **Điều kiện Đại diện Prentice-Athey (Surrogacy Condition; Prentice 1989; Athey et al. 2019):**
     - Giả định cốt lõi: $Y \perp W \mid (S, X)$.
     - Sau khi kiểm soát tập biến đại diện ngắn hạn $S = (S_1, \dots, S_K)$ và các đặc điểm nền $X$, biến can thiệp $W$ không mang thêm bất kỳ thông tin nào về kết quả dài hạn $Y$. Toàn bộ hiệu ứng dài hạn được trung gian hoàn toàn qua vectơ $S$.
  2. **Xây dựng Chỉ số Đại diện (Surrogate Index $r(S, X)$):**
     - Ước lượng hàm kỳ vọng có điều kiện $r(s, x) \equiv E[Y \mid S=s, X=x]$ trên tập dữ liệu quan sát/theo dõi thông qua mô hình hồi quy phạt Ridge (L2 regularization):
       $$\hat{\beta} = \arg\min_\beta \sum_{i \in \text{Obs}} (Y_i - \beta_0 - S_i'\beta_S - X_i'\beta_X)^2 + \lambda \|\beta\|_2^2$$
  3. **Nhận diện Hiệu ứng Can thiệp Dài hạn (Long-Term Treatment Effect $\tau_Y$):**
     - Đánh giá chỉ số đại diện $\hat{r}(S_i, X_i)$ cho từng đối tượng trong mẫu thử nghiệm:
       $$\hat{\tau}_Y = \frac{1}{N_{1, \text{exp}}} \sum_{i \in \text{Exp}: W_i=1} \hat{r}(S_i, X_i) - \frac{1}{N_{0, \text{exp}}} \sum_{i \in \text{Exp}: W_i=0} \hat{r}(S_i, X_i)$$
  4. **Kiểm định Chẩn đoán Điều kiện Đại diện (Prentice Direct Effect Test):**
     - Khi mẫu quan sát có ghi nhận can thiệp, hệ thống kiểm định giả thuyết $H_0: \gamma = 0$ trong $Y = \alpha_0 + \gamma W + S'\beta + X'\delta + \varepsilon$. Nếu $p < 0.05$, cảnh báo nguy cơ vi phạm điều kiện đại diện do can thiệp có tác động trực tiếp ngoài các biến $S$.
  5. **Suy diễn Thống kê Bootstrap Hai Mẫu (Two-Sample Bootstrap):**
     - Tái chọn mẫu đồng thời cả tập dữ liệu quan sát (nhiễu ước lượng tham số $\beta$) và tập thử nghiệm (phương sai mẫu ngẫu nhiên) để cung cấp sai số chuẩn $\hat{SE}$ và khoảng tin cậy 95% chuẩn xác.
  6. **Đồ thị SVG Kép Khoa học:**
     - Panel A: Forest Plot so sánh hiệu ứng dài hạn $\tau_Y$ với tác động trên từng biến đại diện ngắn hạn $S_k$.
     - Panel B: Biểu đồ thanh ngang thể hiện trọng số đóng góp của từng biến đại diện trong chỉ số $r(S, X)$.
  7. **Báo cáo Học thuật Chuẩn APA 7th Edition:** Tự động biên soạn theo chuẩn Athey et al. (2019).
- **Endpoint:** `POST /api/surveys/{survey_id}/analytics/surrogate-index`
- **Request Body (`SurrogateIndexRequest`):**
  - `treatment_question_id`: UUID biến can thiệp thử nghiệm $W$.
  - `surrogate_question_ids`: Danh sách UUID các câu hỏi đại diện ngắn hạn $S_1, S_2, \dots$.
  - `longterm_outcome_question_id`: UUID biến kết quả dài hạn $Y$.
  - `covariate_question_ids`: Danh sách UUID các biến kiểm soát nền $X$.
  - `sample_indicator_question_id`: UUID biến chỉ báo mẫu (Tùy chọn: 1 = thử nghiệm, 0 = quan sát).
  - `alpha_level`: Mức ý nghĩa thống kê (Mặc định 0.05).
  - `n_bootstraps`: Số lần tái chọn mẫu bootstrap hai mẫu (Mặc định 300).
  - `ridge_lambda`: Hệ số phạt Ridge L2 (Mặc định 1.0).
  - `scope`: `"all"` hoặc `"verified_clean"`.
- **Response (`SurrogateIndexOut`):**
  - `status`: `"SUCCESS"`, `"INSUFFICIENT_SAMPLE"`, hoặc `"ERROR"`.
  - `model_type`: `"SURROGATE_INDEX_ATHEY_CHETTY_IMBENS_2019"`.
  - `sample_sizes`: Quy mô mẫu thử nghiệm ($N_{\text{exp}}$), mẫu theo dõi ($N_{\text{obs}}$), tổng mẫu.
  - `surrogate_index_fit`: Hệ số xác định $R^2$ của chỉ số đại diện trên mẫu quan sát.
  - `longterm_treatment_effect`: Ước lượng $\tau_Y$, SE bootstrap hai mẫu, z-statistic, p-value, 95% CI.
  - `surrogate_decomposition`: Tác động ngắn hạn của $W$ lên từng $S_k$ và trọng số tương ứng trong $r(S, X)$.
  - `surrogacy_validation`: Đánh giá rủi ro vi phạm điều kiện đại diện (Prentice direct effect p-value).
  - `svg_visualization`: Đồ thị SVG trực quan hóa kép Forest Plot & Trọng số đại diện.
  - `apa_narrative`: Thuyết minh học thuật chuẩn mực APA 7th Edition theo Athey et al. (2019).
- **Niêm phong kiểm toán:** Ghi nhận `SURROGATE_INDEX_EVALUATED` vào chuỗi sổ cái SHA-256.


### 128. Conformal Counterfactual Risk Inference Engine (Chernozhukov, Wüthrich, & Zhu 2021 JASA; Lei & Candès 2021 JASA)
- **Mục tiêu:** Khắc phục triệt để hạn chế của suy diễn nhân quả truyền thống (chỉ cung cấp ước lượng điểm ATE hoặc CATE mà không phản ánh độ bất định hay rủi ro cá thể; giả định ngặt nghèo về phân phối chuẩn/tuyến tính). Động cơ xây dựng các khoảng dự báo phản thực nghiệm chính xác hữu hạn không phụ thuộc phân phối (Distribution-Free, Finite-Sample Valid Conformal Prediction Intervals) cho từng cá thể: $Y_i(1) \in \hat{C}_1(X_i)$, $Y_i(0) \in \hat{C}_0(X_i)$, và hiệu ứng can thiệp cá thể $Y_i(1) - Y_i(0) \in \hat{C}_\tau(X_i)$, đồng thời lượng hóa rủi ro tổn hại (Downside Harm Risk) và phân định chính sách triển khai an toàn.
- **Nguyên lý Toán học & Cấu trúc:**
  1. **Hiệu chỉnh Dịch chuyển Phối biến (Covariate Shift Conformal Calibration; Tibshirani et al. 2019; Lei & Candès 2021):**
     - Trong nghiên cứu quan sát, phân bố $X \mid W=1$ khác với $X \mid W=0$.
     - Khi dự báo $Y(1)$ cho nhóm chứng ($W=0$), các điểm hiệu chuẩn lấy từ nhóm can thiệp ($W=1$). Trọng số tỉ số mật độ likelihood ratio:
       $$w_i^{(1)} \propto \frac{1 - e(X_i)}{e(X_i)}$$
     - Ngược lại, khi dự báo $Y(0)$ cho nhóm can thiệp ($W=1$):
       $$w_i^{(0)} \propto \frac{e(X_i)}{1 - e(X_i)}$$
       với $e(X) = P(W=1 \mid X)$ là điểm số xu hướng (propensity score).
  2. **Điểm Không Phù Hợp & Phân Vị Conformal Trọng Số (Weighted Conformal Quantiles):**
     - Trên tập hiệu chuẩn $\mathcal{D}_{w, \text{cal}}$, tính điểm số phần dư $R_i^{(w)} = |Y_i - \hat{\mu}_w(X_i)|$.
     - Ngưỡng cắt non-conformity $\hat{Q}_{w}$ được xác định bằng phân vị theo trọng số tại mức $1 - \alpha/2$ (hiệu chỉnh Bonferroni nhằm bảo đảm bao phủ đồng thời $1 - \alpha$):
       $$\sum_{i \in \text{cal}} p_i \mathbb{I}(R_i^{(w)} \le \hat{Q}_{w}) \ge 1 - \alpha/2$$
  3. **Khoảng Hiệu Ứng Can Thiệp Cá Thể (Individual Treatment Effect Interval $\hat{C}_\tau(X)$):**
     $$\hat{C}_\tau(X_i) = [\tau_{i, \text{lower}}, \tau_{i, \text{upper}}] = [\hat{\mu}_1(X_i) - \hat{\mu}_0(X_i) - (\hat{Q}_1 + \hat{Q}_0), \hat{\mu}_1(X_i) - \hat{\mu}_0(X_i) + (\hat{Q}_1 + \hat{Q}_0)]$$
     - Định lý Lei & Candès (2021) bảo đảm xác suất bao phủ $P(Y_i(1) - Y_i(0) \in \hat{C}_\tau(X_i)) \ge 1 - \alpha$ trong mọi cỡ mẫu hữu hạn $N$, không cần giả định phân phối sai số hay mô hình hàm đúng.
  4. **Hồ Sơ Rủi Ro Tổn Hại (Downside Harm Risk Profiling & CVaR):**
     - Đánh dấu cá thể có rủi ro tổn hại nếu $\tau_{i, \text{lower}} < 0$ (mặc dù ATE có thể dương).
     - Phân loại 4 nhóm chính sách:
       - *Strict Benefit* ($\tau_{\text{lower}} > 0$): Triển khai ưu tiên (ROLLOUT).
       - *Strict Harm* ($\tau_{\text{upper}} < 0$): Chống chỉ định (CONTRAINDICATED).
       - *Downside Risk Present* ($\tau_{\text{lower}} \le 0 \le \tau_{\text{upper}}$): Cần rào chắn an toàn (SAFEGUARDS).
       - *Ambiguous*: Giám sát thông thường (MONITOR).
     - Đo lường mức rủi ro đuôi tệ nhất qua Conditional Value-at-Risk (CVaR 5% Expected Shortfall).
- **API Endpoint:** `POST /api/surveys/{survey_id}/analytics/conformal-counterfactual`
  - **Payload:** `ConformalCounterfactualRequest` (`outcome_question_id`, `treatment_question_id`, `covariate_question_ids`, `miscoverage_alpha`, `calibration_ratio`, `use_propensity_weighting`, `subgroup_question_id`, `scope`).
  - **Response:** `ConformalCounterfactualOut` (`status`, `overall_summary`, `calibration_diagnostics`, `subgroup_risk_profiles`, `individual_predictions_sample`, `svg_visualization`, `apa_narrative`).
- **Niêm phong kiểm toán:** Ghi nhận `CONFORMAL_COUNTERFACTUAL_EVALUATED` vào chuỗi sổ cái SHA-256.


### 129. Causal Sensitivity Analysis & Omitted Variable Bias Contour Engine (Cinelli & Hazlett 2020 JRSS-B)
- **Mục tiêu:** Giải quyết câu hỏi phản biện nghiêm ngặt nhất trong nghiên cứu quan sát và phân tích khảo sát thực nghiệm: "Liệu một biến ẩn gây nhiễu chưa quan sát (Unobserved Confounder $Z$) có thể giải thích hoàn toàn và làm sụp đổ hiệu ứng nhân quả được ước lượng không?". Động cơ cung cấp công thức lượng hóa độ chệch dạng đóng phân bố tự do (distribution-free closed-form bias formulas), tính toán Giá trị Bền vững (Robustness Value $RV_q$, $RV_\alpha$), đối chuẩn với các biến kiểm soát quan sát được ($1\times, 2\times, 3\times$ multipliers), và vẽ bản đồ đẳng mức độ nhạy (Sensitivity Contours).
- **Nguyên lý Toán học & Cấu trúc:**
  1. **Đồng nhất thức Độ chệch Biến bỏ sót qua $R^2$ Riêng phần (Cinelli & Hazlett 2020):**
     - Mô hình đầy đủ: $Y = \tau D + X \beta + \gamma Z + \varepsilon$.
     - Mô hình giới hạn hồi quy: $Y = \hat{\tau}_{\text{rest}} D + X \hat{\beta}_{\text{rest}} + \hat{e}$ với bậc tự do phần dư $df = n - k - 1$ và sai số chuẩn $\widehat{\text{SE}}(\hat{\tau}_{\text{rest}})$.
     - Gọi $R^2_{Y \sim Z \mid D, X}$ là tỷ lệ phương sai phần dư của $Y$ được giải thích bởi $Z$ (sau khi kiểm soát $D, X$), và $R^2_{D \sim Z \mid X}$ là tỷ lệ phương sai của $D$ được giải thích bởi $Z$ (sau khi kiểm soát $X$).
     - Độ chệch chính xác:
       $$\text{Bias}(\hat{\tau}) = \widehat{\text{SE}}(\hat{\tau}_{\text{rest}}) \sqrt{df} \sqrt{\frac{R^2_{Y \sim Z \mid D, X} \cdot R^2_{D \sim Z \mid X}}{1 - R^2_{D \sim Z \mid X}}}$$
  2. **Ước lượng Hiệu chỉnh & Sai số Chuẩn Hiệu chỉnh:**
     $$\hat{\tau}(R^2_{Y \sim Z \mid D, X}, R^2_{D \sim Z \mid X}) = \hat{\tau}_{\text{rest}} - \text{sign}(\hat{\tau}_{\text{rest}}) \times \text{Bias}$$
     $$\widehat{\text{SE}}_{\text{adj}} = \widehat{\text{SE}}(\hat{\tau}_{\text{rest}}) \sqrt{\frac{1 - R^2_{Y \sim Z \mid D, X}}{1 - R^2_{D \sim Z \mid X}} \frac{df}{df - 1}}$$
  3. **Giá trị Bền vững Điểm (Robustness Value $RV_q$):**
     - Sức mạnh liên kết tối thiểu mà một biến ẩn cần đạt được đồng thời với cả can thiệp $D$ và kết quả $Y$ ($R^2_{D \sim Z \mid X} = R^2_{Y \sim Z \mid D, X} = RV_q$) để làm giảm ước lượng hiệu ứng đi $100q\%$ (mặc định $q = 1.0$, triệt tiêu hoàn toàn hiệu ứng về 0):
       $$RV_q = \frac{1}{2} \left( \sqrt{f_q^4 + 4 f_q^2} - f_q^2 \right), \quad f_q = \frac{q |t_{\text{rest}}|}{\sqrt{df}}$$
  4. **Giá trị Bền vững Ý nghĩa Thống kê ($RV_\alpha$):**
     - Sức mạnh tối thiểu cần có để đưa khoảng tin cậy $1 - \alpha$ chạm mức 0 (mất ý nghĩa thống kê $p > \alpha$):
       $$RV_\alpha = \frac{1}{2} \left( \sqrt{f_\alpha^4 + 4 f_\alpha^2} - f_\alpha^2 \right), \quad f_\alpha = \frac{|t_{\text{rest}}| - t_{\text{crit}}}{\sqrt{df}}$$
  5. **Đối chuẩn Biến Quan sát (Covariate Benchmarking & Multipliers):**
     - Đo lường $R^2_{D \sim X_j \mid X_{-j}}$ và $R^2_{Y \sim X_j \mid D, X_{-j}}$ cho từng biến kiểm soát nền $X_j$.
     - Thử nghiệm độ bền vững trước các giả định biến ẩn có sức mạnh gấp $1\times, 2\times, 3\times$ các biến quan sát mạnh nhất.
- **API Endpoint:** `POST /api/surveys/{survey_id}/analytics/causal-sensitivity-bias`
  - **Payload:** `CausalSensitivityBiasRequest` (`outcome_question_id`, `treatment_question_id`, `covariate_question_ids`, `q_reduction`, `alpha_level`, `benchmark_question_ids`, `benchmark_multipliers`, `scope`).
  - **Response:** `CausalSensitivityBiasOut` (`status`, `overall_summary`, `covariate_benchmarks`, `benchmark_scenarios`, `svg_visualization`, `apa_narrative`).
- **Niêm phong kiểm toán:** Ghi nhận `CAUSAL_SENSITIVITY_BIAS_EVALUATED` vào chuỗi sổ cái SHA-256.


### 130. Bayesian Causal Forest (BCF) & Heterogeneous Treatment Effects Engine (Hahn, Murray, & Carver 2020 Bayesian Analysis; Hill 2011 JCGS)
- **Mục tiêu:** Giải quyết triệt để khuyết tật "Regularization-Induced Confounding (RIC)" trong các mô hình học máy cây nhân quả truyền thống (BART, Causal Forests). Khi hàm tiên lượng nền $Y(0)$ có liên hệ mạnh với xác suất gán can thiệp qua điểm số xu hướng propensity score $\pi(X)$, các tiên nghiệm co ngót thông thường sẽ ép cả hiệu ứng tiên lượng và hiệu ứng can thiệp về 0, gây ra độ chệch nghiêm trọng không biến mất ngay cả khi $N \to \infty$. Động cơ phân tách tường minh mô hình thành hàm tiên lượng $\mu(X, \hat{\pi}(X))$ và hàm điều hòa can thiệp $\tau(X)$, cung cấp toàn bộ phân phối hậu nghiệm cho CATE, khoảng tin cậy Bayes (Credible Intervals), phân rã phương sai và phát hiện phân nhóm mục tiêu tối ưu.
- **Nguyên lý Toán học & Cấu trúc:**
  1. **Đặc tả Mô hình BCF (Hahn, Murray, & Carver 2020):**
     $$Y_i = \mu(X_i, \hat{\pi}(X_i)) + \tau(X_i) W_i + \varepsilon_i, \quad \varepsilon_i \sim \mathcal{N}(0, \sigma^2)$$
     - $\hat{\pi}(X_i) = P(W_i = 1 \mid X_i)$: Ước lượng điểm số xu hướng được đưa trực tiếp vào hàm tiên lượng nền $\mu$, trực giao hóa hiệu ứng can thiệp khỏi tương quan gây nhiễu.
     - $\tau(X_i)$: Hàm điều hòa hiệu ứng can thiệp cá thể (CATE) với tiên nghiệm co ngót tập trung trực tiếp vào mức độ không đồng nhất.
  2. **Lấy mẫu Hậu nghiệm Bayes (Bayesian Posterior Draws):**
     - Sinh $B$ mẫu hậu nghiệm $\tau^{(b)}(X_i)$ để ước lượng:
       - Trung bình hậu nghiệm CATE: $\hat{\tau}(X_i) = \frac{1}{B} \sum_{b=1}^B \tau^{(b)}(X_i)$.
       - Khoảng tin cậy hậu nghiệm 95% Credible Interval: $[\tau_{i, 0.025}, \tau_{i, 0.975}]$.
       - Xác suất hiệu ứng có lợi: $P(\tau(X_i) > 0 \mid \text{Data})$.
  3. **Phân rã Phương sai Bayes (Bayesian Variance Decomposition):**
     - Xác định tỷ lệ phần trăm biến thiên của biến kết quả $Y$ cấu thành từ:
       $$\text{Var}(Y) \approx \text{Var}(\hat{\mu}) + \text{Var}(\hat{\tau} \cdot W) + \sigma^2$$
       (Phần trăm Tiên lượng nền vs Phần trăm Can thiệp vs Phần trăm Nhiễu dư).
  4. **Phát hiện Phân đoạn Mục tiêu Tối ưu (Optimal Sub-population Discovery):**
     - Phân vùng cá thể theo các thuộc tính $X$ có tương quan mạnh nhất với biến thiên $\tau(X)$, phân bổ 3 nhóm hành động chính sách: `HIGH_PRIORITY`, `TARGETED`, `CONTRAINDICATED`.
- **API Endpoint:** `POST /api/surveys/{survey_id}/analytics/bcf`
  - **Payload:** `BCFRequest` (`outcome_question_id`, `treatment_question_id`, `covariate_question_ids`, `n_posterior_draws`, `alpha_ridge`, `scope`).
  - **Response:** `BCFOut` (`status`, `overall_summary`, `subgroups`, `individual_sample`, `svg_visualization`, `apa_narrative`).
- **Niêm phong kiểm toán:** Ghi nhận `BCF_EVALUATED` vào chuỗi sổ cái SHA-256.


### 131. Shift-Share Instrumental Variables & Rotemberg Decomposition Engine (Bartik IV; Goldsmith-Pinkham, Sorkin, & Swift 2020 AER; Borusyak, Hull, & Jaravel 2022 Restud; Adao, Kolesár, & Morales 2019 QJE)
- **Mục tiêu:** Mở rộng khả năng suy diễn nhân quả cho các cuộc khảo sát kinh tế, thị trường lao động và phân tích tổ chức có cấu trúc phơi nhiễm danh mục tỷ trọng (portfolio share exposures $z_{ik}$) trước các cú sốc vĩ mô hoặc chính sách tổng thể ($g_k$). Thay vì xem công cụ Bartik $Z_i = \sum_k z_{ik} g_k$ như một "hộp đen", động cơ thực hiện định lý tương đương của Goldsmith-Pinkham et al. (2020), phân rã ước lượng 2SLS thành tổng có trọng số của các công cụ riêng lẻ từng thành phần với Trọng số Rotemberg ($\hat{\alpha}_k$), ước lượng sai số chuẩn Adao-Kolesár-Morales (AKM 2019) chống tương quan cụm ngẫu nhiên do chia sẻ chung cú sốc, và kiểm định tính đồng nhất ngoại sinh Sargan.
- **Nguyên lý Toán học & Cấu trúc:**
  1. **Thiết lập Công cụ Bartik & Hồi quy 2SLS:**
     $$Z_i = \sum_{k=1}^K z_{ik} g_k$$
     - Giai đoạn 1: $D_i = \gamma_0 + \gamma_1 Z_i + X_i \Gamma + u_i$, kiểm định công cụ yếu qua F-statistic ($F \ge 10$).
     - Giai đoạn 2: $Y_i = \beta_0 + \beta_{\text{2SLS}} \hat{D}_i + X_i \Pi + \varepsilon_i$.
  2. **Định lý Phân rã Trọng số Rotemberg (Goldsmith-Pinkham et al. 2020 AER):**
     $$\hat{\beta}_{\text{2SLS}} = \sum_{k=1}^K \hat{\alpha}_k \hat{\beta}_k, \quad \hat{\alpha}_k = \frac{g_k z_k^T M_X D}{Z^T M_X D}$$
     - $\sum_{k=1}^K \hat{\alpha}_k = 1.0$: Trọng số Rotemberg $\hat{\alpha}_k$ định lượng chính xác tỷ lệ phần trăm sức mạnh nhận diện nhân quả mà ngành/thành phần $k$ đóng góp vào toàn bộ ước lượng.
     - $\hat{\beta}_k = \frac{z_k^T M_X Y}{z_k^T M_X D}$: Ước lượng nhân quả chỉ dựa duy nhất vào tỷ trọng ngành $k$.
     - Chỉ số tập trung Herfindahl-Hirschman (HHI) của các trọng số dương đo lường rủi ro tập trung nhận diện.
  3. **Sai số Chuẩn Chống Tương quan Phơi nhiễm (AKM 2019 QJE):**
     - Sai số chuẩn thông thường (Omitted Cross-Unit Correlation) bị đánh giá thấp nghiêm trọng do các đơn vị có cơ cấu tỷ trọng $z_{ik}$ tương đồng sẽ có phần dư tương quan nhau ngay cả khi ở các địa bàn độc lập.
     - Phương sai AKM: $V_{\text{AKM}} = (Z^T M_X D)^{-2} \sum_{k=1}^K \left( \sum_{i=1}^N z_{ik} \hat{\varepsilon}_i g_k \right)^2$.
  4. **Kiểm định Ngoại sinh & Đồng nhất (Overidentification Test):**
     - Kiểm định Sargan qua các thành phần có $\hat{\alpha}_k > 0$ so sánh độ lệch $(\hat{\beta}_k - \hat{\beta}_{\text{2SLS}})$ nhằm phát hiện sự vi phạm giả định loại trừ ngoại sinh (exclusion restriction).
- **API Endpoint:** `POST /api/surveys/{survey_id}/analytics/shift-share-iv`
  - **Payload:** `ShiftShareIVRequest` (`outcome_question_id`, `treatment_question_id`, `share_question_ids`, `shocks`, `covariate_question_ids`, `alpha_level`, `scope`).
  - **Response:** `ShiftShareIVOut` (`status`, `overall_summary`, `rotemberg_decomposition`, `svg_visualization`, `apa_narrative`).
- **Niêm phong kiểm toán:** Ghi nhận `SHIFT_SHARE_IV_EVALUATED` vào chuỗi sổ cái SHA-256.
