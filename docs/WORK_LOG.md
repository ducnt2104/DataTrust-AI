# DataTrust AI — Engineering Work Log & Progress Checkpoints

## Checkpoint 1: Khởi động & Khám phá Workspace (Giai đoạn A)
- **Thời gian:** 2026-10-22 13:16 - 13:20
- **Hiện trạng ban đầu:** Workspace rỗng. Định nghĩa lại toàn bộ sản phẩm theo chỉ thị tối cao: Link-based Survey Platform + Real Response Collection + Quality Assurance & Fraud Screening Engine.
- **Thực hiện:** Khởi tạo Git repo; khởi tạo React 19 + TypeScript + Vite + Tailwind CSS; cài đặt `lucide-react`, `qrcode`, `recharts`; thiết lập toàn bộ bộ tài liệu kiến trúc kỹ thuật trong `docs/`.

---

## Checkpoint 2: Xây Dựng Backend & DataTrust Quality Engine (Giai đoạn B & E)
- **Thời gian:** 2026-10-22 13:20 - 13:25
- **Thực hiện:**
  1. Xây dựng CSDL SQLite `backend/app/database.py` kích hoạt WAL mode, foreign keys và busy timeout.
  2. Xây dựng Pydantic v2 schemas `backend/app/schemas.py`.
  3. Xây dựng DataTrust Quality Engine `backend/app/engine/quality_engine.py` gồm 7 tầng phân tích (Layer A -> Layer G) với Hamming distance, Shannon entropy, straightlining, logic contradiction và heuristic composite risk score.
  4. Xây dựng AI Survey Assistant `backend/app/engine/ai_assistant.py` với bộ sinh câu hỏi thông minh và kiểm định câu hỏi dẫn dắt / câu hỏi kép.
  5. Xây dựng toàn bộ các tuyến API trong `backend/app/routes/` (`surveys.py`, `public.py`, `responses.py`, `analytics.py`, `export_import.py`, `ai.py`).
  6. Xây dựng bộ test suite `backend/tests/` và chạy qua 100% test cases.

---

## Checkpoint 3: Xây Dựng Giao Diện Người Dùng & Các Luồng Tương Tác (Giai đoạn C, D, F)
- **Thời gian:** 2026-10-22 13:25 - 13:31
- **Thực hiện:**
  1. Xây dựng Typed API Client `frontend/src/api/client.ts`.
  2. Xây dựng Question Renderer `frontend/src/components/QuestionRenderer.tsx` hỗ trợ đầy đủ 12 loại câu hỏi và hiển thị lỗi hợp lệ.
  3. Xây dựng Share Modal `frontend/src/components/ShareModal.tsx` với mã QR động trên Canvas và sao chép link 1 chạm.
  4. Xây dựng Trình tạo khảo sát `frontend/src/pages/SurveyBuilderPage.tsx` tích hợp AI soạn thảo câu hỏi, kiểm định AI, xem trước và xuất bản.
  5. Xây dựng Trang khảo sát công khai `frontend/src/pages/PublicSurveyPage.tsx` tối ưu mobile-first, thanh tiến độ, logic rẽ nhánh động và gửi phản hồi thật.
  6. Xây dựng Bảng điều khiển phân tích `frontend/src/pages/SurveyAnalyticsPage.tsx` lấy dữ liệu thật, kiểm soát ngưỡng mẫu $N < 5$.
  7. Xây dựng Trung tâm rà soát `frontend/src/pages/ResponsesListPage.tsx` & `frontend/src/pages/ResponseDetailPage.tsx` ghi nhận quyết định xác minh của con người.
  8. Xây dựng Trang đối sánh phản hồi `frontend/src/pages/ResponseComparePage.tsx` hiển thị chi tiết câu trùng và khác biệt.
  9. Xây dựng Trung tâm xuất nhập `frontend/src/pages/ExportImportPage.tsx` hỗ trợ 3 phạm vi (Verified Clean, Reviewed, Raw) CSV UTF-8 BOM.
  10. Biên dịch frontend (`npm run build`) thành công 1,977 modules trong 857ms.

---

## Checkpoint 4: Kiểm Thử Toàn Trình (E2E) & Khởi Chạy Dịch Vụ (Giai đoạn G & H)
- **Thời gian:** 2026-10-22 13:31 - 13:33
- **Thực hiện:**
  1. Xây dựng và thực thi bài kiểm thử toàn trình 12 bước `backend/tests/test_full_journey_e2e.py`.
  2. Toàn bộ 9/9 test suites (TEST-01 đến TEST-12) đạt kết quả 100% PASSED.
  3. Khởi chạy Backend FastAPI daemon trên cổng 8000 (`http://127.0.0.1:8000`).
  4. Khởi chạy Frontend Vite dev daemon trên cổng 5173 (`http://127.0.0.1:5173`).
  5. Kiểm tra kết nối end-to-end với HTTP 200 OK trên cả 2 cổng.
  6. Hoàn thiện tài liệu nghiệm thu `docs/TEST_RESULTS.md` và `docs/IMPLEMENTATION_BACKLOG.md`.

---

## Checkpoint 5: Mở Rộng 12 Dạng Câu Hỏi, Khử Flaky DB Tests & Báo Cáo Nghiệm Thu
- **Thời gian:** 2026-10-22 17:22 - 17:30
- **Thực hiện:**
  1. Hoàn thiện hỗ trợ toàn diện dạng câu hỏi `matrix` (ma trận lưới hàng x cột) và `ranking` (xếp hạng thứ tự ưu tiên) từ Builder, Public Renderer, Quality Engine (giải nén ma trận vào straightlining, bảo toàn vector thứ tự ranking) đến Analytics Dashboard (bảng phân bố tần suất 2 chiều và điểm thứ hạng trung bình).
  2. Khắc phục triệt để lỗi TypeScript strict typing trong `QuestionRenderer.tsx` và `SurveyBuilderPage.tsx`. Biên dịch production Vite + TypeScript pass 100%.
  3. Xây dựng bộ kiểm thử mới `test_all_12_question_types.py` kiểm định trọn vẹn 12 loại câu hỏi, chuẩn hóa vector ranking, straightlining trên matrix và analytics aggregation.
  4. Chuẩn hóa môi trường test thông qua `backend/tests/conftest.py`, tự động cô lập và dọn dẹp CSDL test suite tạm thời, chấm dứt hoàn toàn xung đột khóa chính `questions.id`.
  5. Toàn bộ 12 ca kiểm thử tự động trên Pytest vượt qua 100% (12/12 PASSED).
  6. Tạo văn bản báo cáo chiến dịch `docs/CAMPAIGN_CHECKPOINT.md` ghi nhận toàn bộ tiến độ, ma trận tính năng, kết quả kiểm thử và bằng chứng cổng lắng nghe socket.
  7. Xác minh cổng mạng: Backend `http://127.0.0.1:8000/api/health` trả về HTTP 200 `{ "status": "healthy" }`, Frontend `http://127.0.0.1:5173/` trả về HTTP 200.

---

## Checkpoint 6: Triển Khai Stream B (Số Hóa Phiếu Giấy OMR), Layer G ($S_{enum}$) & Benchmark Đối Chứng
- **Thời gian:** 2026-10-23 13:45 - 14:40
- **Thực hiện:**
  1. **Nâng cấp CSDL SQLite:** Bổ sung di trú tự động (migrations) cho các cột `source`, `enumerator_id`, `paper_form_id`, `scan_image_url`, `omr_confidence` trong bảng `responses`, cột `score_enum` trong bảng `quality_assessments`, và bảng mới `paper_templates`.
  2. **Động cơ OMR bằng OpenCV (`backend/app/engine/omr_engine.py`):**
     - Sinh bố cục mẫu phiếu chuẩn A4 có mã QR định danh và 4 dấu căn góc vuông.
     - Phát hiện 4 dấu góc, biến đổi phối cảnh 2D (`warpPerspective`) đưa ảnh về kích thước gốc.
     - Kiểm định chất lượng ảnh đầu vào: Độ nét biến thiên Laplacian (ngưỡng >= 40.0) và độ sáng trung bình.
     - Giải mã QR qua `cv2.QRCodeDetector` để liên kết mẫu khảo sát.
     - Phân tích tỷ lệ lấp đầy điểm ảnh (bubble fill ratio) và độ tin cậy nhận diện.
     - Sinh ảnh lớp phủ trực quan (Visual Overlay) với vòng tròn xanh/đỏ thể hiện các ô tích.
     - Tạo hàm giả lập scan mẫu chuẩn (`generate_synthetic_test_scan`) phục vụ kiểm thử tự động.
  3. **Tầng phân tích Điều tra viên (Layer G - $S_{enum}$):**
     - Đo lường Z-score phương sai câu trả lời ($Z_{var}$), tỷ lệ phản hồi rủi ro cao theo lô và mức độ trùng lặp nội bộ điều tra viên.
     - Tích hợp vào công thức tính điểm rủi ro tổng hợp có tái chuẩn hóa trọng số ($w_1=0.35, w_2=0.25, w_3=0.25, w_4=0.15$).
  4. **Tuyến API & Giao diện người dùng:**
     - Tạo tuyến API `/api/surveys/{id}/paper/template`, `/scan`, `/ingest` và `/api/surveys/{id}/enumerators`.
     - Xây dựng trang `frontend/src/pages/PaperSurveyPage.tsx` gồm 3 tab: Mẫu in A4, Tải ảnh quét & Kiểm tra độ nét, Lớp phủ thị giác và Hiệu chỉnh thủ công kèm ghi nhật ký kiểm toán (Audit Trail).
     - Xây dựng trang `frontend/src/pages/EnumeratorAnalyticsPage.tsx` theo dõi điều tra viên và cảnh báo bất thường.
     - Cập nhật điều hướng, danh sách phản hồi và trang chi tiết phản hồi với nhãn nguồn và điểm $S_{enum}$.
  5. **Bộ dữ liệu kiểm chuẩn đối chứng (Controlled Benchmark):**
     - Triển khai `backend/app/engine/benchmark_suite.py` chạy thực nghiệm Mục II.1 trong hồ sơ Word với $N = 150$ phản hồi.
     - Đạt 100% Precision, 100% Recall, 100% F1, độ trễ trung bình 0.64 ms/phản hồi. Ghi chép tài liệu `docs/BENCHMARK_RESULTS.md` và `docs/DATATRUST_REQUIREMENT_TRACEABILITY.md`.
  6. **Kiểm thử tự động:** Thêm 7 ca kiểm thử mới (tổng cộng 19 tests), toàn bộ 19/19 PASSED.

---

## Checkpoint 7: Hoàn Thiện Đối Sánh Song Song & Nâng Cấp Xuất Nhập Dữ Liệu Đa Nguồn
- **Thời gian:** 2026-10-23 14:45 - 14:55
- **Thực hiện:**
  1. **Nâng cấp API So sánh Đối chiếu (`/api/surveys/{id}/responses/compare/side-by-side`):**
     - Trả về chi tiết metadata của cả 2 phản hồi (`resp1_meta` và `resp2_meta`), bao gồm nhãn nguồn (`online_form`, `paper_scan`, `csv_import`), mã điều tra viên, thời lượng, mức rủi ro và trạng thái thẩm định.
  2. **Tái thiết kế Giao diện Đối sánh (`ResponseComparePage.tsx`):**
     - Bổ sung thẻ tóm tắt đối chiếu trực quan với tỷ lệ Hamming Similarity.
     - Hiển thị đầy đủ thông tin nguồn, điều tra viên và thời gian của từng phản hồi.
     - Bộ lọc tương tác 3 chế độ: Tất cả câu hỏi, Chỉ câu khác biệt, Chỉ câu trùng khớp.
     - Tô màu đánh dấu trực quan rõ ràng giữa các câu trả lời trùng và khác.
  3. **Nâng cấp Trung tâm Xuất & Nhập (`ExportImportPage.tsx`):**
     - Bổ sung bộ chọn kênh nguồn xuất (Tất cả, Trực tuyến, Phiếu giấy OMR, Tệp CSV).
     - Tích hợp thông điệp hướng dẫn và giải thích quy trình bảo toàn tính toàn vẹn khi nhập dữ liệu CSV ngoại tuyến.
  4. **Kiểm thử xác minh:**
     - Chạy lại toàn bộ 19/19 tests trong `pytest`: 100% PASSED trong 2.88s.
     - Biên dịch production Frontend `npm run build`: 1,979 modules transformed thành công với 0 lỗi.

---

## Checkpoint 8: Báo Cáo Kiểm Định Độc Lập, Tuân Thủ Nghị Định 356/2025/NĐ-CP & Kiểm Thử Chịu Tải Cao
- **Thời gian:** 2026-10-23 15:00 - 15:15
- **Thực hiện:**
  1. **Xây dựng Mô-đun Báo cáo Kiểm định Độc lập & Pháp lý (`backend/app/routes/audit_report.py`):**
     - Tuyến API `GET /api/surveys/{id}/audit-report`: Tạo Báo cáo Kiểm định Chất lượng Dữ liệu (Evidence-Based Quality Audit Report) tổng hợp Data Trust Index (DTI), ma trận phân loại rủi ro, phân loại kênh thu thập (Trực tuyến, Phiếu giấy, CSV) và chi tiết 6 nhóm tín hiệu sàng lọc.
     - Tạo mã băm kiểm định SHA-256 (`DT-AUDIT-XXXX`) bảo vệ tính bất biến của báo cáo.
     - Căn cứ pháp lý: Tuyên bố tuân thủ 4 nguyên tắc của Luật Bảo vệ dữ liệu cá nhân 2025 và Nghị định 356/2025/NĐ-CP (Tối thiểu hóa, Giả danh hóa, Mã hóa đường truyền & lưu trữ, Quyền ẩn danh/xóa dữ liệu).
     - Trích dẫn khoa học: Tiêu chuẩn AAPOR (2003), Kennedy et al. (Pew Research Center 2016), Schwanhäuser et al. (2022), Geisen et al.
  2. **Thực thi Quyền Ẩn danh hóa / Xóa dữ liệu PII (`POST /api/surveys/{id}/privacy/anonymize`):**
     - Hỗ trợ ẩn danh hóa tự động metadata client (IP, User-Agent) và che mờ câu trả lời văn bản mở (`[ANONYMIZED_PII]`) sau khi nghiệm thu, lưu vết vào `audit_logs`.
  3. **Giao diện Báo cáo Kiểm định & In ấn (`QualityAuditReportModal.tsx`):**
     - Tích hợp vào `SurveyAnalyticsPage.tsx` với nút "Báo cáo kiểm định độc lập".
     - Chế độ in ấn thân thiện (`window.print()`), ẩn các nút điều khiển, hiển thị chứng nhận trang trọng và phần chữ ký đại diện nghiệm thu.
     - Nút kích hoạt ẩn danh hóa PII trực tiếp trên giao diện.
  4. **Kiểm thử chịu tải cao & thông lượng (Stress Load Test - `test_stress_load.py`):**
     - Nộp dồn dập 100 phản hồi liên tiếp trên SQLite WAL.
     - Kết quả đo lường thực tế: 100/100 thành công (100%), tổng thời gian 1.30s, độ trễ trung bình 12.98 ms/phản hồi, thông lượng 77.1 req/s. 0 database locks.
  5. **Xác minh toàn hệ thống:**
     - Pytest: 12 test suites, 21 tests PASSED 100% trong 3.32s.
     - Frontend build: 1,980 modules transformed, 0 lỗi TypeScript strict trong 649ms.
     - Backend API trên cổng 8000 và Vite trên cổng 5173 hoạt động bình thường.

---

## Checkpoint 9: Kiểm Định Luật Benford Trên Số Liệu & Xuất Từ Điển Cú Pháp SPSS/R (Academic Codebook)
- **Thời gian:** 2026-10-23 15:15 - 15:30
- **Thực hiện:**
  1. **Kiểm định thống kê Luật Benford (First-Digit Test) trên số liệu (`backend/app/engine/quality_engine.py`):**
     - Xây dựng thuật toán kiểm định chữ số đầu tiên theo luật logarit tự nhiên $P(d) = \log_{10}(1 + 1/d)$ nhằm phát hiện số liệu bịa đặt/ngụy tạo trong các câu hỏi số (thu nhập, chi phí, khoảng cách...) theo nghiên cứu của Schräpler & Wagner (2012, AAPOR).
     - Tính thống kê $\chi^2$ với 8 bậc tự do ($df=8$), đánh giá mức ý nghĩa $p < 0.05$ và $p < 0.01$.
     - Tuyến API `GET /api/surveys/{id}/analytics/benford`.
     - Thẻ trực quan hóa phân bố tần suất (`BenfordAnalysisCard.tsx`) tích hợp vào `SurveyAnalyticsPage.tsx`, đối chiếu trực quan cột phần trăm thực tế vs lý thuyết.
  2. **Xuất Từ điển Dữ liệu & Cú pháp SPSS / R (`backend/app/routes/export_import.py`):**
     - Tuyến API `GET /api/surveys/{id}/codebook?format=spss|json`: Tự động phân loại thang đo (Nominal, Ordinal, Scale), trích xuất danh sách biến `VAR001...`, nhãn câu hỏi `VARIABLE LABELS`, nhãn lựa chọn `VALUE LABELS` và quy tắc khuyết thiếu `MISSING VALUES ALL (999)`.
     - Tích hợp khu vực tải file `.sps` và xem JSON Codebook trong `ExportImportPage.tsx`.
  3. **Kiểm thử tự động:**
     - Thêm 2 bài kiểm thử mới trong `backend/tests/test_benford_and_codebook.py` kiểm định tính đúng đắn của Benford trên tập số tự nhiên vs tập số bịa đặt, và kiểm tra tính hợp lệ của cú pháp SPSS.
     - Toàn bộ 23/23 tests trong 13 test suites trên Pytest đạt 100% PASSED trong 3.81s.
     - Biên dịch production Frontend `npm run build`: 1,981 modules transformed thành công với 0 lỗi trong 732ms.
     - Xác minh trạng thái cổng mạng: Backend API Healthy, Frontend Dev Server phản hồi HTTP 200.
