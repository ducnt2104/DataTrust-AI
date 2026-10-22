# DataTrust AI — Quality Engine & Fraud Screening Algorithms

Hệ thống phân tích chất lượng của DataTrust AI phân biệt rõ ràng giữa **Phản hồi thực tế**, **Đặc trưng tính toán bằng thuật toán tất định (Deterministic Algorithms)**, **Điểm rủi ro gợi ý (Heuristic Risk Score)** và **Quyết định xác minh của con người (Human Decision)**. Điểm rủi ro cao **không được coi là bằng chứng tuyệt đối về gian lận**, mà là tín hiệu để ưu tiên rà soát.

---

## 1. Công Thức Điểm Rủi Ro Tổng Hợp (Composite Heuristic Risk Score)

Điểm rủi ro tổng hợp $R \in [0, 100]$ được tính toán từ các thành phần chuẩn hóa:

$$R = \min\left(100, \sum_{i \in \text{Signals}} w_i \cdot S_i + \text{BonusPenalties}\right)$$

Trong đó các tín hiệu thành phần $S_i \in [0, 100]$ bao gồm:
1. $S_{\text{dup}}$: Tín hiệu trùng lặp hoặc gần trùng lặp câu trả lời (Trọng số mặc định: $w_{\text{dup}} = 0.35$).
2. $S_{\text{pat}}$: Tín hiệu mẫu đáp án bất thường / Straightlining / Entropy thấp (Trọng số mặc định: $w_{\text{pat}} = 0.25$).
3. $S_{\text{logic}}$: Tín hiệu vi phạm quy tắc logic câu hỏi chéo (Trọng số mặc định: $w_{\text{logic}} = 0.25$).
4. $S_{\text{speed}}$: Tín hiệu nộp bài siêu tốc / spam thời gian (Trọng số mặc định: $w_{\text{speed}} = 0.15$).

Nếu một khảo sát không có các câu hỏi thuộc nhóm tương ứng (ví dụ: không có câu hỏi thang đo Likert), trọng số sẽ được tái chuẩn hóa tự động để đảm bảo tổng trọng số luôn bằng 1.0.

### Phân loại mức độ rủi ro (Risk Levels):
- **Thấp (Low):** $0 \le R < 40$ — Dữ liệu tự nhiên, không phát hiện dấu hiệu bất thường.
- **Trung bình (Medium):** $40 \le R < 70$ — Có một số dấu hiệu trùng lặp nhẹ hoặc tốc độ nhanh, khuyến nghị xem xét.
- **Cao (High):** $70 \le R \le 100$ — Đạt nhiều cờ cảnh báo nghiêm trọng (Ví dụ: Trùng lặp hoàn toàn với phản hồi trước + vi phạm logic rõ rệt), ưu tiên xác minh hàng đầu.

---

## 2. Chi Tiết Các Tầng Phân Tích (Analysis Layers)

### 2.1. Layer A — Kiểm Tra Tính Toàn Vẹn Tức Thời (Immediate Validation)
- Kiểm tra các trường bắt buộc (`is_required = true`) không được để trống hoặc `null`.
- Kiểm tra kiểu dữ liệu số nằm trong khoảng `[min_val, max_val]`.
- Kiểm tra số lượng lựa chọn nhiều phương án (`multiple_choice`) không vượt quá số lượng cho phép.

### 2.2. Layer B — Trùng Lặp & Gần Trùng Lặp (Hamming Distance Vectorization)
- Với mỗi phản hồi, trích xuất vector câu trả lời đóng $V = (a_1, a_2, \dots, a_k)$ theo thứ tự câu hỏi đã chuẩn hóa.
- So sánh cặp vector $(V_A, V_B)$ giữa phản hồi mới và tất cả phản hồi trước đó của cùng một khảo sát:
  $$\text{Similarity}(V_A, V_B) = 1 - \frac{\text{HammingDistance}(V_A, V_B)}{k}$$
- Nếu $\text{Similarity} = 1.0$: Gắn cờ `FLAG_EXACT_DUPLICATE` ($S_{\text{dup}} = 100$).
- Nếu $0.85 \le \text{Similarity} < 1.0$: Gắn cờ `FLAG_NEAR_DUPLICATE` ($S_{\text{dup}} = \text{Similarity} \times 90$).
- Cung cấp ID của phản hồi tương đồng cao nhất (`closest_match_response_id`) để phục vụ đối chiếu trực quan trong Review Center.

### 2.3. Layer C — Mẫu Đáp Án Bất Thường (Straightlining & Shannon Entropy)
- **Straightlining:** Người trả lời chọn cùng 1 phương án (ví dụ toàn chọn 5 hoặc toàn chọn 3) trên chuỗi câu hỏi thang đo Likert hoặc ma trận.
  $$\text{StraightlineRatio} = \frac{\max_{v} \text{Count}(v)}{N_{\text{scale}}}$$
  Nếu $\text{StraightlineRatio} \ge 0.85$ với $N_{\text{scale}} \ge 5$, gắn cờ `FLAG_STRAIGHTLINING` ($S_{\text{pat}} \ge 80$).
- **Shannon Entropy:** Đo lường độ đa dạng thông tin của các lựa chọn:
  $$H = -\sum_{i=1}^{M} p_i \log_2(p_i)$$
  Nếu $H$ thấp bất thường ($H < 0.5$ với $M \ge 4$), gắn cờ `FLAG_LOW_ENTROPY`.

### 2.4. Layer D — Vi Phạm Logic Chéo (Cross-Question Consistency)
- Thực thi danh sách quy tắc điều kiện logic, ví dụ:
  - Nếu `Q_has_vehicle == "Không"`, nhưng `Q_vehicle_type != null`: Gắn cờ `FLAG_LOGIC_CONTRADICTION` ($S_{\text{logic}} = 85$).
  - Nếu `Q_age < 18` nhưng `Q_job == "Đã nghỉ hưu"`: Gắn cờ `FLAG_LOGIC_CONTRADICTION`.

### 2.5. Layer E — Thời Gian Hoàn Thành & Tần Suất Nộp (Speed & Frequency)
- Tính ngưỡng thời gian làm bài tối thiểu hợp lý:
  $$T_{\text{min}} = N_{\text{questions}} \times 2.5 \text{ giây}$$
- Nếu $\text{duration\_seconds} < T_{\text{min}}$: Gắn cờ `FLAG_SPEEDING` (người trả lời bấm qua loa mà không kịp đọc câu hỏi).

### 2.6. Layer F — Phân Tích Câu Trả Lời Mở (Text Repetition & Semantic)
- Phát hiện các câu trả lời ngắn lặp lại ký tự vô nghĩa (ví dụ: "asdfghjk", ".....", "111111").
- Phát hiện câu trả lời văn bản trùng lặp nguyên văn giữa nhiều phản hồi khác nhau.

---

## 3. Điều Kiện Dữ Liệu Thiếu (Sample Size Guards)
- Nếu một khảo sát có $N < 5$ phản hồi:
  - Hiển thị rõ thông báo: **"Cỡ mẫu chưa đủ ($N < 5$) để đưa ra các kết luận thống kê tổng thể"**.
  - Không vẽ biểu đồ sai lệch hay suy diễn giả định khi chưa đủ cơ sở thực nghiệm.
