# DATATRUST AI — CAMPAIGN CHECKPOINT REPORT
**Campaign ID:** `DATATRUST-AI-REBUILD-V1`  
**Checkpoint Date:** 2026-10-22  
**Target Architecture:** Python FastAPI (SQLite 3 WAL) + React 18, TypeScript, Vite, Tailwind CSS  
**Engine:** DataTrust Survey Quality Engine (7-Layer Multidimensional Analysis)

---

## 1. TỔNG QUAN CHIẾN DỊCH & BẢN CHẤT SẢN PHẨM

DataTrust AI đã được xây dựng lại hoàn chỉnh từ số 0 theo đúng tôn chỉ sản phẩm:
> **Survey Builder + Real Response Collection + AI-Assisted Data Quality Assurance & Fraud Screening**

Hệ thống cung cấp trải nghiệm quen thuộc, dễ tiếp cận tương tự Google Forms nhưng tích hợp chiều sâu kiểm định chất lượng dữ liệu của Qualtrics/Research Platforms:
1. **Khởi tạo và thiết kế khảo sát:** Hỗ trợ đầy đủ **12 loại câu hỏi**, logic rẽ nhánh có điều kiện, cấu hình bắt buộc và AI Audit câu hỏi (phát hiện câu hỏi định kiến, câu hỏi lồng 2 ý).
2. **Xuất bản & Thu thập dữ liệu thực:** Sinh liên kết công khai định dạng `/s/:slug`, hỗ trợ mã QR, giao diện phản hồi responsive tối ưu cho cả máy tính và thiết bị di động.
3. **Lưu trữ chuẩn CSDL quan hệ:** Toàn bộ phản hồi được ghi nhận vào SQLite với chế độ Write-Ahead Logging (WAL), lưu trữ chính xác thời gian bắt đầu, thời gian gửi, metadata thiết bị và câu trả lời chi tiết. Không dùng mock data hay fake records trong cơ sở dữ liệu vận hành.
4. **DataTrust Quality Engine:** Phân tích 7 tầng độc lập (Layer A đến G) tính toán điểm rủi ro tổng hợp (0 - 100), gán các nhãn cảnh báo (câu trả lời trùng lặp Hamming, straightlining ma trận & likert, entropy Shannon thấp, mâu thuẫn logic rẽ nhánh, làm bài siêu tốc speeding, văn bản vô nghĩa/sao chép).
5. **Khu vực rà soát & Xác minh:** Giao diện so sánh đối chiếu hai phản hồi (side-by-side compare), gắn trạng thái rà soát (`verified_valid`, `verified_fraud`, `needs_review`) và ghi chú quyết định.
6. **Báo cáo thống kê & Xuất dữ liệu:** Báo cáo tần suất, phân bố ma trận, xếp hạng trung bình; cảnh báo kích thước mẫu khi $N < 5$; xuất khẩu dữ liệu nhiều phạm vi (Tất cả, Đã làm sạch, Đã duyệt) sang file CSV chuẩn UTF-8 BOM.

---

## 2. MA TRẬN HỖ TRỢ ĐẦY ĐỦ 12 DẠNG CÂU HỎI

| STT | Mã dạng câu hỏi | Tên hiển thị | Cơ chế nhập liệu (Public/Renderer) | Logic Quality Engine & Analytics |
|:---:|:---|:---|:---|:---|
| 1 | `single_choice` | Trắc nghiệm 1 đáp án | Radio buttons với focus rings | Tần suất lựa chọn, khoảng cách Hamming |
| 2 | `multiple_choice` | Trắc nghiệm nhiều lựa chọn | Checkboxes linh hoạt | Chuẩn hóa sắp xếp tập hợp, tần suất |
| 3 | `short_text` | Trả lời ngắn | Input text 1 dòng | Phát hiện lặp ký tự đơn điệu, trùng lặp |
| 4 | `long_text` | Đoạn văn bản dài | Textarea nhiều dòng tự co giãn | Kiểm tra gibberish text, duplicate cross-response |
| 5 | `number` | Số liệu | Numeric input với min/max | Thống kê Min, Max, Average, Count |
| 6 | `rating` | Đánh giá sao | 5-star interactive picker | Thang đo hài lòng, kiểm tra straightlining |
| 7 | `linear_scale` | Thang điểm tuyến tính | Thang ngang 1 đến N (1-5, 1-10) | Tần suất điểm, entropy Shannon |
| 8 | `dropdown` | Hộp chọn thả xuống | Accessible `<select>` native | Tần suất lựa chọn |
| 9 | `date` | Ngày tháng | HTML5 Date picker format YYYY-MM-DD | Phân bố thời gian |
| 10 | `likert` | Thang đo Likert | 5 mức từ Hoàn toàn không đồng ý đến Hoàn toàn đồng ý | Straightlining detection, Shannon Entropy |
| 11 | `matrix` | Ma trận hàng & cột | Bảng lưới tương tác (Hàng tiêu chí x Cột đánh giá) | Tách hàng vào kiểm định straightlining, bảng tần suất 2 chiều |
| 12 | `ranking` | Xếp hạng thứ tự ưu tiên | Thẻ lựa chọn với nút Move Up / Move Down | Chuẩn hóa vector bảo toàn thứ tự, tính thứ hạng trung bình |

---

## 3. KẾT QUẢ KIỂM THỬ TỰ ĐỘNG TOÀN HỆ THỐNG

### 3.1. Backend Test Suites (Pytest)
Toàn bộ 12 ca kiểm thử tự động đã vượt qua với tỷ lệ thành công 100%:

```
backend/tests/test_all_12_question_types.py::test_quality_engine_ranking_normalization PASSED
backend/tests/test_all_12_question_types.py::test_quality_engine_matrix_straightlining PASSED
backend/tests/test_all_12_question_types.py::test_all_12_question_types_survey_lifecycle PASSED
backend/tests/test_analytics_and_export.py::test_analytics_and_export_journey PASSED
backend/tests/test_full_journey_e2e.py::test_full_12_step_e2e_journey PASSED
backend/tests/test_public_survey.py::test_public_survey_lifecycle PASSED
backend/tests/test_quality_engine.py::test_exact_duplicate_detection PASSED
backend/tests/test_quality_engine.py::test_straightlining_detection PASSED
backend/tests/test_quality_engine.py::test_speeding_detection PASSED
backend/tests/test_quality_engine.py::test_logic_contradiction_detection PASSED
backend/tests/test_quality_engine.py::test_clean_response_low_risk PASSED
backend/tests/test_surveys_api.py::test_create_and_update_survey PASSED

======================== 12 passed, 1 warning in 1.39s ========================
```

### 3.2. Frontend Build Verification (TypeScript & Vite)
Quá trình build production kiểm tra toàn bộ type system và bundle:
```
vite v8.3.5 building client environment for production...
✓ 1977 modules transformed.
dist/index.html                   0.45 kB │ gzip:   0.29 kB
dist/assets/index-iWtgCRgY.css   47.56 kB │ gzip:   8.42 kB
dist/assets/index-DS8MMhYm.js   368.89 kB │ gzip: 104.08 kB
✓ built in 707ms
```
Không có cảnh báo TypeScript strict (0 errors).

---

## 4. ĐỐI CHIẾU TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA AC-01 ĐẾN AC-12)

| Mã AC | Tiêu chí nghiệm thu | Trạng thái | Bằng chứng kiểm chứng |
|:---:|:---|:---:|:---|
| **AC-01** | Tạo và cấu hình khảo sát (12 dạng câu hỏi, logic rẽ nhánh) | **ĐẠT** | `SurveyBuilderPage.tsx`, `test_surveys_api.py`, `test_all_12_question_types.py` |
| **AC-02** | Xuất bản khảo sát và sinh slug duy nhất | **ĐẠT** | Endpoint `POST /api/surveys/{id}/publish`, `test_public_survey.py` |
| **AC-03** | Mở form công khai theo link `/s/:slug` và QR code | **ĐẠT** | `PublicSurveyPage.tsx`, QR modal hiển thị trực tiếp |
| **AC-04** | Nhận và lưu phản hồi thực vào SQLite WAL | **ĐẠT** | Endpoint `POST /api/public/surveys/{slug}/submit`, `responses` & `response_answers` |
| **AC-05** | Phát hiện trùng lặp Hamming (Exact & High Similarity) | **ĐẠT** | `QualityEngine.test_exact_duplicate_detection`, flag `FLAG_EXACT_DUPLICATE` |
| **AC-06** | Phát hiện mẫu trả lời bất thường (Straightlining, Shannon Entropy) | **ĐẠT** | `test_straightlining_detection`, `test_quality_engine_matrix_straightlining` |
| **AC-07** | Phát hiện vi phạm logic câu hỏi chéo | **ĐẠT** | `test_logic_contradiction_detection`, flag `FLAG_LOGIC_CONTRADICTION` |
| **AC-08** | Phát hiện làm bài siêu tốc (Speeding & Fast Completion) | **ĐẠT** | `test_speeding_detection`, ngưỡng $T < 2.2 \text{s} \times N$ |
| **AC-09** | Tính điểm rủi ro tổng hợp (Composite Risk Score 0-100) | **ĐẠT** | Công thức tái chuẩn hóa trọng số Layer G và quy tắc overriding |
| **AC-10** | Khu vực rà soát, so sánh side-by-side và cập nhật trạng thái | **ĐẠT** | `SurveyResponsesPage.tsx`, `/api/surveys/{id}/responses/compare/side-by-side` |
| **AC-11** | Báo cáo thống kê thời gian thực & Cảnh báo $N < 5$ | **ĐẠT** | `SurveyAnalyticsPage.tsx`, `is_sample_size_sufficient` |
| **AC-12** | Xuất dữ liệu đa phạm vi (Raw, Clean, Verified) sang CSV UTF-8 | **ĐẠT** | `GET /api/surveys/{id}/export`, `test_analytics_and_export.py` |

---

## 5. CAM KẾT VỀ TÍNH TOÀN VẸN DỮ LIỆU & ZERO-MOCK POLICY

1. **Không tạo dữ liệu giả lập trong CSDL chính:** Database `backend/data/datatrust.db` sạch, chỉ lưu trữ các bản ghi phát sinh từ thao tác thực của người dùng hoặc bài test.
2. **Môi trường Test được cô lập hoàn toàn:** Toàn bộ test suite chạy trên CSDL tạm `datatrust_test_suite.db` thông qua `conftest.py`, tự động tạo mới và dọn dẹp sau mỗi lần chạy.
3. **Phân biệt minh bạch giữa Heuristics và AI:**
   - Hệ thống đánh giá chất lượng phản hồi cốt lõi sử dụng các giải thuật toán học tất định (Deterministic Algorithms: Hamming Distance, Shannon Entropy, Tỉ lệ làm bài trên giây, Ma trận chéo logic).
   - Mô-đun AI (`ai_assistant.py`) phụ trách hỗ trợ người thiết kế biểu mẫu (Gợi ý câu hỏi, Audit câu hỏi mớm lời / câu hỏi kép), có cơ chế Fallback thông minh khi không có `GEMINI_API_KEY`.
