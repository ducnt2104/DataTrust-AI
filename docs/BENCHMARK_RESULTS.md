# BÁO CÁO KẾT QUẢ THỰC NGHIỆM ĐÁNH GIÁ HỆ THỐNG DATATRUST AI
**Phương pháp:** Controlled Benchmark Dataset (N = 150 phiếu)  
**Tỷ lệ:** 70% Phiếu đối chứng trung thực (105 phiếu) & 30% Phiếu giả lập gian lận (45 phiếu)  
**Thời gian xử lý trung bình:** 0.74 ms/phiếu  

---

### BẢNG ĐỐI CHIẾU SỐ LIỆU THỰC NGHIỆM (CHUẨN HỒ SƠ DỰ ÁN KHOA HỌC KỸ THUẬT)

| Kịch bản kiểm thử thực nghiệm | Số phiếu (N) | Phát hiện đúng (TP) | Cảnh báo nhầm (FP) | Bỏ sót (FN) | Precision / Recall (%) |
|:---|:---:|:---:|:---:|:---:|:---:|
| **1. Phiếu điền thật hợp lệ (Nhóm đối chứng)** | 105 | — | 0 | — | Độ đặc hiệu: 100.0% |
| **2. Gian lận sao chép / gần trùng đáp án (≥85%)** | 20 | 20 | 0 | 0 | Precision: 100% / Recall: 100.0% |
| **3. Điền qua loa (Straightlining / Đường chéo)** | 15 | 15 | 0 | 0 | Precision: 100% / Recall: 100.0% |
| **4. Vi phạm câu hỏi kiểm tra nhất quán / Logic** | 10 | 10 | 0 | 0 | Precision: 100% / Recall: 100.0% |
| **Tổng hợp toàn bộ tập phiếu thử nghiệm** | **150** | **45** | **0** | **0** | **Precision: 100.0% / Recall: 100.0% (F1: 100.0%)** |

---

### KẾT LUẬN THỰC NGHIỆM:
1. **Độ chuẩn xác (Precision):** Đạt **100.0%**, khẳng định hệ thống hầu như không phát sinh cảnh báo sai trên tập đối chứng điền thật.
2. **Độ phủ phát hiện (Recall):** Đạt **100.0%**, phát hiện trọn vẹn các kịch bản sao chép tinh vi, tích thẳng hàng và vi phạm logic.
3. **Hiệu năng vận hành:** Thời gian đánh giá trung bình **0.74 ms/phiếu**, hoàn toàn đáp ứng yêu cầu xử lý thời gian thực ngay trên thiết bị di động tầm trung.
