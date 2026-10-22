# DataTrust AI — Product Definition & Functional Specification

## 1. Định Vị Sản Phẩm

**DataTrust AI** là nền tảng trực tuyến toàn diện kết hợp 3 trụ cột:
1. **Survey Builder (Bộ tạo khảo sát chuyên nghiệp):** Hỗ trợ đầy đủ các loại câu hỏi (đóng, mở, thang đo, ma trận, xếp hạng), thiết lập logic rẽ nhánh, ràng buộc hợp lệ và xuất bản thành đường liên kết công khai (Public Survey Link).
2. **Real Response Collection (Thu thập phản hồi thực địa & trực tuyến):** Giao diện điền biểu mẫu tối ưu đa thiết bị (Desktop, Mobile, Tablet), kiểm soát tiến độ, xác thực dữ liệu 2 lớp (Client & Server), ghi nhận thời gian làm bài và lưu trữ chính xác vào cơ sở dữ liệu quan hệ.
3. **Data Quality Assurance & Fraud Screening Engine (Hệ thống phân tích chất lượng dữ liệu & sàng lọc bất thường):** Phát hiện trùng lặp/gần trùng lặp (Hamming distance vector), mẫu đáp án bất thường (Straightlining, Shannon Entropy thấp, lặp ma trận), vi phạm logic chéo (Logic Rule Violation Engine), tốc độ nộp bất thường (Speeding/Spamming), và tính toán điểm rủi ro tổng hợp có giải thích (Composite Explainable Risk Score: 0 - 100).

---

## 2. Các Luồng Nghiệp Vụ Cốt Lõi (Core User Journeys)

### Luồng 1: Người tạo khảo sát (Survey Creator / Researcher)
1. Đăng nhập hoặc truy cập Workspace quản trị.
2. Tạo khảo sát mới (từ đầu hoặc dùng gợi ý AI Survey Assistant).
3. Thiết lập tiêu đề, mô tả, hướng dẫn làm bài và danh sách câu hỏi.
4. Cấu hình thuộc tính câu hỏi: Bắt buộc, loại câu hỏi, tùy chọn đáp án, điều kiện logic rẽ nhánh, giới hạn giá trị.
5. Xem trước (Preview) trên giao diện Desktop và Mobile.
6. Xuất bản khảo sát (Publish): Hệ thống sinh mã định danh / slug công khai duy nhất (`/s/:slug`), tạo mã QR và link chia sẻ.
7. Đóng hoặc tạm dừng nhận phản hồi bất cứ lúc nào.

### Luồng 2: Người tham gia khảo sát (Public Respondent)
1. Nhấp vào đường link khảo sát hoặc quét mã QR từ điện thoại/máy tính.
2. Hệ thống tải schema khảo sát đã xuất bản từ API Backend.
3. Người dùng trả lời tuần tự các câu hỏi; hệ thống hiển thị thanh tiến độ (Progress Bar) và áp dụng logic hiển thị rẽ nhánh theo thời gian thực.
4. Xác thực lỗi trực tiếp nếu thiếu trường bắt buộc hoặc giá trị không hợp lệ.
5. Gửi bài: Backend tiếp nhận, xác minh tính toàn vẹn, ghi nhận `started_at`, `submitted_at`, tính thời gian hoàn thành (`duration_seconds`), lưu câu trả lời và trả về xác nhận thành công.

### Luồng 3: Quản trị chất lượng & Rà soát (Data Quality & Reviewer)
1. Truy cập **Survey Dashboard**: Xem số lượng phản hồi thực tế, tỷ lệ hoàn thành, thời gian trả lời trung bình và phân bố rủi ro.
2. Truy cập **Responses List**: Xem danh sách phản hồi kèm điểm rủi ro, cờ cảnh báo (Flags) và trạng thái xác minh.
3. Mở **Response Detail**: Xem toàn bộ câu trả lời, phân tích chi tiết từng cờ cảnh báo, điểm thành phần (`S_dup`, `S_pat`, `S_logic`, `S_speed`).
4. Sử dụng công cụ **Response Comparison**: Mở hai phản hồi nghi vấn cạnh nhau (Side-by-side) để đối chiếu mức độ tương đồng câu trả lời.
5. Cập nhật quyết định xác minh: Chấp thuận (`VERIFIED_VALID`), Từ chối/Loại bỏ (`VERIFIED_FRAUD`), hoặc Cần xem xét thêm (`UNDER_REVIEW`) kèm ghi chú (Audit notes).
6. Xuất dữ liệu: Lựa chọn xuất tập dữ liệu gốc (Raw), tập dữ liệu đã rà soát (Reviewed) hoặc bộ dữ liệu sạch đã kiểm định (Verified Clean Dataset) dưới định dạng CSV/JSON.

---

## 3. Các Loại Câu Hỏi Hỗ Trợ (Supported Question Types)

1. `short_text`: Trả lời văn bản ngắn (họ tên, email, nghề nghiệp, ...).
2. `long_text`: Trả lời văn bản dài (ý kiến đóng góp, nhận xét tự do).
3. `single_choice`: Chọn một phương án duy nhất (Radio buttons).
4. `multiple_choice`: Chọn nhiều phương án (Checkboxes có giới hạn min/max options).
5. `dropdown`: Danh sách thả xuống.
6. `linear_scale`: Thang điểm tuyến tính (ví dụ 1 - 5, 1 - 10 với nhãn hai đầu).
7. `likert`: Thang đo Likert chuẩn (Hoàn toàn không đồng ý -> Hoàn toàn đồng ý).
8. `matrix`: Ma trận câu hỏi nhiều hàng và nhiều cột.
9. `number`: Giá trị số thực hoặc số nguyên có kiểm tra min/max.
10. `date`: Ngày tháng.
11. `boolean`: Đúng / Sai hoặc Có / Không.
12. `ranking`: Sắp xếp thứ tự ưu tiên các lựa chọn.

---

## 4. Nguyên Tắc Trung Thực Về Dữ Liệu (Zero-Fabrication & Real Data Integrity)
- Tuyệt đối không sinh dữ liệu ảo (fake mock respondents) vào cơ sở dữ liệu hoạt động.
- Khi một khảo sát mới tạo chưa có phản hồi, hiển thị trạng thái Trống (Empty State) với hướng dẫn chia sẻ link.
- Không tính các chỉ số thống kê (P-value, Precision, F1-score) khi số lượng mẫu không đủ hoặc không có nhãn kiểm định đối chứng thực tế.
- Mọi điểm số rủi ro đều được định nghĩa rõ là **Điểm rủi ro heuristic có giải thích (Explainable Heuristic Risk Score)**, không tự phong là "mô hình AI tuyệt đối".
