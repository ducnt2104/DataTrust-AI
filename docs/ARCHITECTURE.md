# DataTrust — Đặc Tả Kiến Trúc Kỹ Thuật (Technical Architecture Specification)
## Phiên Bản Hoàn Thiện: Kiến Trúc Hai Luồng (Dual-Stream Architecture) & Động Cơ Kiểm Định Đa Tầng

**Mã tài liệu:** `DT-ARCH-2026-V2`  
**Ngày cập nhật:** 2026-10-23  

---

## 1. Tổng Quan Kiến Trúc Hệ Thống (System Overview)

DataTrust được xây dựng theo nguyên tắc kiến trúc sạch (**Clean Architecture** & **Modular Monolith**), phân tách ranh giới rõ ràng giữa các tầng trình diễn, dịch vụ nghiệp vụ, xử lý ảnh thị giác máy tính và lưu trữ dữ liệu bền vững.

Hệ thống tích hợp hai luồng thu thập dữ liệu song song (Dual-Stream), cùng đưa dữ liệu về một cấu trúc phản hồi chuẩn hóa và được phân tích bởi cùng một Động cơ Kiểm định Chất lượng Dữ liệu (**Quality Engine**).

```mermaid
graph TD
    subgraph Stream_A [Luồng A: Khảo Sát Kỹ Thuật Số (Digital Survey Platform)]
        A1[Survey Builder / Trình Soạn Thảo] -->|Xuất Bản| A2[Link Công Khai /s/:slug]
        A2 -->|Nộp Trực Tuyến| A3[Client-Side Validation & Telemetry]
        A3 -->|HTTP POST| A4[API Gateway & Rate Limiter]
    end

    subgraph Stream_B [Luồng B: Số Hóa Khảo Sát Giấy (Field Survey Digitization)]
        B1[Bộ Tạo Mẫu In Phiếu Giấy] -->|Sinh QR & Dấu Căn Góc| B2[Bản In Giấy A4 / In Khảo Sát Thực Địa]
        B2 -->|Điều Tra Viên Thu Phiếu & Chụp Ảnh| B3[Tải Ảnh Phiếu Giấy Lên Hệ Thống]
        B3 -->|OpenCV Vision Engine| B4[Nhận Diện 4 Góc -> Nắn Phối Cảnh -> Đọc QR -> Quét OMR]
        B4 -->|Giao Diện Xác Minh Mắt Người| B5[Human-in-the-Loop OMR Correction]
    end

    A4 --> UNIFIED_INGESTION[Bộ Tiếp Nhận Phản Hồi Chuẩn Hóa]
    B5 --> UNIFIED_INGESTION

    subgraph Engine [DataTrust Quality Assurance Engine]
        UNIFIED_INGESTION --> L_A[Tầng A: Schema & Kiểu Dữ Liệu]
        L_A --> L_B[Tầng B: Trùng Lặp 100% & Gần Trùng - Hamming Distance]
        L_B --> L_C[Tầng C: Mẫu Trả Lời Bất Thường - Straightlining & Shannon Entropy]
        L_C --> L_D[Tầng D: Mâu Thuẫn Logic Câu Hỏi Chéo]
        L_D --> L_E[Tầng E: Thời Gian & Tốc Độ Làm Bài - Speeding Anomaly]
        L_E --> L_F[Tầng F: Ngữ Nghĩa Câu Mở & Lặp Văn Bản - Semantic NLP]
        L_F --> L_G[Tầng G: Sàng Lọc Điều Tra Viên & Nhóm Thu Thập]
        L_G --> BENFORD[Tầng Thống Kê: Phân Tích Chữ Số Đầu Định Luật Benford]
    end

    Engine --> DB[(Cơ Sở Dữ Liệu SQLite 3 WAL Mode)]
    
    subgraph Governance [Trung Tâm Quản Trị & Khai Thác Nghiên Cứu]
        DB --> REVIEW[Review Center: Thẩm Định Bằng Chứng & Quyết Định Con Người]
        DB --> ANALYTICS[Analytics Dashboard: Phân Phối Tần Suất & Thống Kê Thực]
        DB --> EXPORT[Export Center: SPSS Syntax, R Dataset, CSV UTF-8 BOM]
        DB --> AUDIT[Audit Report: Báo Cáo Kiểm Toán Chất Lượng & SHA-256 Digest]
    end
```

---

## 2. Phân Tích Chi Tiết Hai Luồng Thu Thập (Dual-Stream Ingestion)

### 2.1. Luồng A — Khảo Sát Số Hóa Trực Tuyến (Digital Survey Platform)
- **Visual Survey Builder:** Cho phép người tạo khảo sát xây dựng 12 loại câu hỏi, thiết lập logic rẽ nhánh (`logic_rules`), chỉ định câu hỏi bắt buộc, cấu hình tùy chọn điểm và thang đo Likert.
- **Public Survey Portal (`/s/:slug`):** Giao diện tương thích 100% thiết bị di động và máy tính, hỗ trợ tự động hiển thị/ẩn câu hỏi theo thời gian thực (Reactive Dynamic Logic), đo lường thời gian làm bài chính xác (`duration_seconds`).
- **An Toàn Đăng Tải:** Tích hợp bộ đệm chống click đúp chuột trong 3 giây và Sliding-window Rate Limiter (40 requests/phút trên mỗi IP).

### 2.2. Luồng B — Số Hóa Khảo Sát Giấy (Field Survey Digitization)
- **Tạo mẫu in tiêu chuẩn:** Sinh mẫu HTML/CSS có độ phân giải in ấn cao, tự động chèn:
  - 4 dấu định vị căn góc hình vuông (ArUco / Quad Markers) tại 4 góc trang giấy.
  - Mã QR định danh chứa `survey_id` và phiên bản mẫu in (`v1`, `v2`, ...).
  - Lưới ô tích trắc nghiệm (OMR Bubbles) với tọa độ chuẩn hóa $[x_i, y_i, w, h]$.
- **OpenCV Vision Engine:**
  1. *Corner Detection:* Tìm kiếm 4 dấu căn góc bằng thuật toán dò đường bao diện tích và tỷ lệ co giãn aspect ratio.
  2. *Perspective Transform (Homography):* Nắn ảnh phẳng từ ảnh chụp nghiêng của điện thoại thông minh về kích thước chuẩn ($1654 \times 2338$ px tương đương 200 DPI A4).
  3. *QR Code Decoding:* Đọc tự động mã QR trên ảnh để nhận diện khảo sát mà không cần người dùng nhập tay.
  4. *Optical Density Thresholding:* Đánh giá tỷ lệ điểm ảnh tối bên trong từng ô tròn để xác định ô đã được tô mực bút bi hoặc chì ($> 40\%$ pixel đen).
- **Human-in-the-Loop Verification:** Cung cấp màn hình trực quan cho phép điều tra viên đối chiếu ảnh gốc với kết quả bóc tách OMR trước khi phê duyệt lưu vào cơ sở dữ liệu.

---

## 3. Kiến Trúc Động Cơ Kiểm Định Chất Lượng (Quality Engine Layers)

| Tầng | Tên Tầng | Cơ Chế Toán Học / Thống Kê | Trọng Số Rủi Ro | Hành Động Kích Hoạt |
|---|---|---|:---:|---|
| **Layer A** | Structural Validation | Kiểm tra ràng buộc schema, trường bắt buộc, giá trị số hợp lệ. | - | Chặn nộp (HTTP 422) nếu vi phạm. |
| **Layer B** | Duplicate / Near-Duplicate | Khoảng cách Hamming trên vector đáp án chuẩn hóa ($d_H \le 1$). | 0.85 | Gắn cờ `FLAG_EXACT_DUPLICATE` hoặc `FLAG_NEAR_DUPLICATE`. |
| **Layer C** | Pattern & Straightlining | Độ lệch chuẩn $\sigma = 0$ trên chuỗi Likert liên tiếp; Shannon Entropy $H(X) < 0.5$. | 0.50 | Gắn cờ `FLAG_STRAIGHTLINING` hoặc `FLAG_LOW_ENTROPY`. |
| **Layer D** | Logic Contradiction | Quy tắc phụ thuộc điều kiện câu hỏi chéo ($A \implies \neg B$). | 0.60 | Gắn cờ `FLAG_LOGIC_CONTRADICTION`. |
| **Layer E** | Speeding Anomaly | Ngưỡng thời gian tới hạn: $T_{submit} < N_{questions} \times 2.5\text{s}$. | 0.45 | Gắn cờ `FLAG_EXTREME_SPEEDING`. |
| **Layer F** | Semantic & Repetition | Tần suất trùng lặp chuỗi văn bản mở; lọc chuỗi vô nghĩa (Gibberish). | 0.40 | Gắn cờ `FLAG_TEXT_REPETITION`. |
| **Layer G** | Enumerator Screening | Thống kê phân cụm tỷ lệ gian lận theo `enumerator_id` ($\text{FraudRate} > 40\%$). | 0.35 | Gắn cờ cảnh báo điều tra viên có rủi ro điền khống. |
| **Layer S** | Benford's Law | Kiểm định Chi-Square độ phù hợp phân phối chữ số đầu của biến liên tục: $\chi^2 = \sum \frac{(O_i - E_i)^2}{E_i}$ | Thống kê vĩ mô | Phát hiện hiện tượng bịa đặt số liệu tài chính, thu nhập, thời gian. |

$$\text{Composite Risk Score} = \min\left(1.0, \sum w_k \cdot \mathbb{I}(\text{Flag}_k)\right)$$

$$\text{Risk Level} = \begin{cases} \text{high} & \text{khi Risk} \ge 0.60 \\ \text{medium} & \text{khi } 0.30 \le \text{Risk} < 0.60 \\ \text{low} & \text{khi Risk} < 0.30 \end{cases}$$

---

## 4. Kiến Trúc Dữ Liệu & Tính Toàn Vẹn (Data Persistence)

- **Cơ sở dữ liệu:** SQLite 3 với cấu hình chuyên sâu cho môi trường sản xuất:
  ```sql
  PRAGMA journal_mode = WAL;          -- Ghi nhật ký song song, tăng tốc đọc/ghi
  PRAGMA synchronous = NORMAL;        -- Cân bằng an toàn và tốc độ I/O
  PRAGMA foreign_keys = ON;           -- Ràng buộc toàn vẹn khóa ngoại
  PRAGMA busy_timeout = 5000;         -- Chờ tối đa 5 giây khi có giao dịch đồng thời
  ```
- **Tính Bất Biến (Audit Integrity):** Mỗi khảo sát và bộ phản hồi được tính toán mã băm SHA-256 dựa trên dữ liệu các câu trả lời hợp lệ, đảm bảo không thể chỉnh sửa lén lút sau khi đã nghiệm thu dữ liệu.

---

## 5. Xuất Dữ Liệu Chuẩn Học Thuật (Academic Research Standards)

- **SPSS Export (`.sps`):** Sinh tệp mã lệnh SPSS Syntax định nghĩa tự động `VARIABLE LABELS`, `VALUE LABELS`, và `VARIABLE LEVEL` (Nominal, Ordinal, Scale).
- **R / Python Integration:** Cung cấp tệp Codebook định dạng JSON chuẩn hóa để các nhà nghiên cứu dễ dàng nạp vào Pandas hoặc R data.frame.
- **Multi-Scope CSV Export:** Cho phép xuất theo 3 phạm vi dữ liệu:
  1. `raw_all`: Toàn bộ phản hồi thu thập được.
  2. `reviewed_only`: Các phản hồi đã qua thẩm định của con người.
  3. `verified_clean`: Bộ dữ liệu nghiên cứu sạch đã loại bỏ các phản hồi gian lận (`verified_fraud`).
