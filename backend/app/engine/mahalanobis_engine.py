import math
import re
from typing import Dict, Any, List, Optional, Tuple

class MahalanobisEngine:
    """
    Động cơ Phát hiện Điểm Dị biệt Đa biến (Multivariate Outlier Detection Engine)
    sử dụng Khoảng cách Mahalanobis và phân phối Chi-Square.

    Cơ sở phương pháp luận:
    - Mahalanobis, P. C. (1936). On the generalised distance in statistics.
      Proceedings of the National Institute of Sciences of India, 2(1), 49-55.
    - Rousseeuw, P. J., & Van Zomeren, B. C. (1990). Unmasking multivariate
      outliers and leverage points. Journal of the American Statistical Association,
      85(411), 633-639.
    - Tabachnick, B. G., & Fidell, L. S. (2019). Using Multivariate Statistics.
      Pearson (7th Edition).
    - Leys, C., et al. (2018). Detecting multivariate outliers: Use a robust
      variant of Mahalanobis distance. Journal of Experimental Social Psychology.
    """

    @staticmethod
    def _regularized_gamma_lower(a: float, x: float) -> float:
        """
        Khai triển chuỗi hàm Gamma không đầy đủ chính quy hóa P(a, x) = gamma(a, x) / Gamma(a).
        Dùng để tính chính xác CDF của phân phối Chi-Square với bậc tự do p.
        """
        if x <= 0.0:
            return 0.0
        if a <= 0.0:
            return 1.0

        # Khai triển chuỗi Taylor cho x < a + 1
        if x < a + 1.0:
            ap = a
            sum_val = 1.0 / a
            del_val = sum_val
            for _ in range(120):
                ap += 1.0
                del_val *= x / ap
                sum_val += del_val
                if abs(del_val) < abs(sum_val) * 1e-12:
                    break
            log_gamma_a = math.lgamma(a)
            return sum_val * math.exp(-x + a * math.log(x) - log_gamma_a)
        else:
            # Khai triển liên phân số (Continued Fraction) cho x >= a + 1
            b = x + 1.0 - a
            c = 1.0 / 1e-30
            d = 1.0 / b
            h = d
            for i in range(1, 120):
                an = -i * (i - a)
                b += 2.0
                d = an * d + b
                if abs(d) < 1e-30:
                    d = 1e-30
                c = b + an / c
                if abs(c) < 1e-30:
                    c = 1e-30
                d = 1.0 / d
                del_val = d * c
                h *= del_val
                if abs(del_val - 1.0) < 1e-12:
                    break
            log_gamma_a = math.lgamma(a)
            gammcf = math.exp(-x + a * math.log(x) - log_gamma_a) * h
            return 1.0 - gammcf

    @staticmethod
    def _chi2_p_value(chi2: float, df: int) -> float:
        """Tính p-value P(Chi2 >= x) cho bậc tự do df"""
        if chi2 <= 0.0 or df <= 0:
            return 1.0
        cdf = MahalanobisEngine._regularized_gamma_lower(df / 2.0, chi2 / 2.0)
        return max(0.0, min(1.0, 1.0 - cdf))

    @staticmethod
    def _invert_matrix_gauss_jordan(matrix: List[List[float]]) -> Optional[List[List[float]]]:
        """
        Đảo ma trận thực đối xứng n x n bằng phương pháp khử Gauss-Jordan với chọn phần tử trụ (Pivoting).
        Hỗ trợ ma trận kích thước từ 2x2 đến 30x30 với độ chính xác vi phân vi độ.
        """
        n = len(matrix)
        # Tạo ma trận tăng cường [A | I]
        aug = []
        for i in range(n):
            row = [float(x) for x in matrix[i]] + [1.0 if i == j else 0.0 for j in range(n)]
            aug.append(row)

        for col in range(n):
            # Chọn pivot có trị tuyệt đối lớn nhất
            pivot_row = col
            max_val = abs(aug[col][col])
            for r in range(col + 1, n):
                if abs(aug[r][col]) > max_val:
                    max_val = abs(aug[r][col])
                    pivot_row = r

            if max_val < 1e-14:
                return None  # Ma trận suy biến

            # Hoán đổi hàng
            if pivot_row != col:
                aug[col], aug[pivot_row] = aug[pivot_row], aug[col]

            # Chuẩn hóa hàng pivot
            pivot = aug[col][col]
            for c in range(2 * n):
                aug[col][c] /= pivot

            # Khử các hàng khác
            for r in range(n):
                if r != col:
                    factor = aug[r][col]
                    if abs(factor) > 1e-15:
                        for c in range(2 * n):
                            aug[r][c] -= factor * aug[col][c]

        # Tách ma trận nghịch đảo
        inv = []
        for i in range(n):
            inv.append(aug[i][n:])
        return inv

    @staticmethod
    def _parse_numeric_value(val: Any) -> Optional[float]:
        """Trích xuất giá trị số từ câu trả lời (hỗ trợ số thực, chuỗi số, hoặc nhãn '5 - Đồng ý')"""
        if val is None or val == "":
            return None
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip()
        try:
            return float(val_str)
        except ValueError:
            # Thử tìm số ở đầu chuỗi (ví dụ: '5 - Rất hài lòng', '1: Hoàn toàn không đồng ý')
            m = re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\b', val_str)
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    pass
        return None

    @classmethod
    def compute_mahalanobis_distances(
        cls,
        records: List[Dict[str, Any]],
        scale_question_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Tính toán khoảng cách Mahalanobis đa biến cho toàn bộ mẫu phản hồi.

        Input:
        - records: Danh sách bản ghi [{'id': '...', 'answers': {...}, 'duration_seconds': ..., 'risk_score': ...}]
        - scale_question_ids: Danh sách ID các câu hỏi thang đo số/Likert để xây dựng vector đặc trưng.
        """
        p = len(scale_question_ids)
        if p < 2:
            return {
                "status": "INSUFFICIENT_VARIABLES",
                "message": "Cần ít nhất 2 biến thang đo định lượng để phân tích dị biệt đa biến.",
                "total_records": len(records),
                "variable_count": p,
                "outliers": []
            }

        # 1. Trích xuất ma trận dữ liệu số X (N x p)
        valid_records = []
        matrix_X: List[List[float]] = []

        for rec in records:
            ans = rec.get("answers", {})
            vector = []
            valid_vec = True
            for qid in scale_question_ids:
                num_val = cls._parse_numeric_value(ans.get(qid))
                if num_val is None:
                    valid_vec = False
                    break
                vector.append(num_val)

            if valid_vec and len(vector) == p:
                valid_records.append(rec)
                matrix_X.append(vector)

        n = len(matrix_X)
        if n <= p + 1:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cỡ mẫu hợp lệ (N = {n}) phải lớn hơn số biến thang đo (p = {p}) để tính ma trận hiệp phương sai.",
                "total_records": len(records),
                "valid_records_count": n,
                "variable_count": p,
                "outliers": []
            }

        # 2. Tính vector trung bình mẫu mu (1 x p)
        mean_vec = [0.0] * p
        for row in matrix_X:
            for j in range(p):
                mean_vec[j] += row[j]
        mean_vec = [m / n for m in mean_vec]

        # 3. Tính ma trận hiệp phương sai mẫu Sigma (p x p)
        cov_matrix = [[0.0 for _ in range(p)] for _ in range(p)]
        for row in matrix_X:
            diff = [row[j] - mean_vec[j] for j in range(p)]
            for i in range(p):
                for j in range(p):
                    cov_matrix[i][j] += diff[i] * diff[j]

        denom = float(n - 1)
        for i in range(p):
            for j in range(p):
                cov_matrix[i][j] /= denom

        # 4. Hiệu chỉnh Ridge Regularization tránh suy biến (Collinearity Protection)
        trace_val = sum(cov_matrix[i][i] for i in range(p))
        ridge_lambda = max(1e-4, 0.01 * (trace_val / p))
        for i in range(p):
            cov_matrix[i][i] += ridge_lambda

        # 5. Nghịch đảo ma trận hiệp phương sai Sigma^-1
        inv_cov = cls._invert_matrix_gauss_jordan(cov_matrix)
        if not inv_cov:
            return {
                "status": "SINGULAR_MATRIX",
                "message": "Ma trận hiệp phương sai bị suy biến tuyến tính hoàn toàn.",
                "total_records": len(records),
                "variable_count": p,
                "outliers": []
            }

        # 6. Tính khoảng cách Mahalanobis bình phương D^2_M cho từng quan sát
        # D^2_i = (x_i - mu)^T * Sigma^-1 * (x_i - mu)
        results = []
        d2_values = []

        for idx, row in enumerate(matrix_X):
            diff = [row[j] - mean_vec[j] for j in range(p)]
            # Tính (Sigma^-1 * diff)
            inv_diff = [0.0] * p
            for i in range(p):
                for j in range(p):
                    inv_diff[i] += inv_cov[i][j] * diff[j]

            # Tính diff^T * inv_diff
            d2 = sum(diff[i] * inv_diff[i] for i in range(p))
            d2 = max(0.0, d2)
            d = math.sqrt(d2)
            p_val = cls._chi2_p_value(d2, df=p)

            # Phân loại dị biệt đa biến (Tabachnick & Fidell: p < 0.001 hoặc p < 0.01)
            is_extreme = p_val < 0.001
            is_moderate = 0.001 <= p_val < 0.01

            if is_extreme:
                status_tier = "Extreme Anomaly"
            elif is_moderate:
                status_tier = "Moderate Outlier"
            else:
                status_tier = "Normal Multivariate Range"

            orig_rec = valid_records[idx]
            d2_values.append(d2)

            results.append({
                "response_id": orig_rec.get("id", ""),
                "d2_mahalanobis": round(d2, 2),
                "distance_d": round(d, 2),
                "p_value": round(p_val, 6),
                "degrees_of_freedom": p,
                "is_outlier": is_extreme or is_moderate,
                "outlier_tier": status_tier,
                "duration_seconds": orig_rec.get("duration_seconds", 0.0),
                "risk_score": orig_rec.get("risk_score", 0.0),
                "review_status": orig_rec.get("review_status", "unverified"),
                "answers_vector": [round(val, 2) for val in row]
            })

        # 7. Sắp xếp theo khoảng cách D^2 giảm dần
        results.sort(key=lambda x: x["d2_mahalanobis"], reverse=True)

        # 8. Thống kê tổng thể phân phối
        mean_d2 = sum(d2_values) / len(d2_values) if d2_values else 0.0
        sorted_d2 = sorted(d2_values)
        median_d2 = sorted_d2[len(sorted_d2) // 2] if sorted_d2 else 0.0
        max_d2 = sorted_d2[-1] if sorted_d2 else 0.0

        extreme_count = sum(1 for r in results if r["outlier_tier"] == "Extreme Anomaly")
        moderate_count = sum(1 for r in results if r["outlier_tier"] == "Moderate Outlier")
        total_outliers = extreme_count + moderate_count

        # 9. Đoạn diễn giải học thuật APA 7th Edition
        critical_val_001 = round(p + 3.0 * math.sqrt(2 * p), 2)  # Ước lượng ngưỡng kiểm định
        apa_interpretation = (
            f"Kiểm định dị biệt đa biến Mahalanobis được thực hiện trên p = {p} biến thang đo "
            f"(N = {n}). Khoảng cách Mahalanobis bình phương trung bình đạt D² = {round(mean_d2, 2)} "
            f"(Trung vị D² = {round(median_d2, 2)}, Max D² = {round(max_d2, 2)}). "
            f"Dựa trên tiêu chuẩn Tabachnick & Fidell (2019) với phân phối Chi-Square bậc tự do df = {p}, "
            f"hệ thống phát hiện {extreme_count} phản hồi có cấu trúc trả lời dị biệt cực đoan (p < .001) "
            f"và {moderate_count} phản hồi dị biệt vừa phải (p < .01). "
            f"Các mẫu này có tổ hợp câu trả lời dị biệt phi ngẫu nhiên so với tâm phân bố của tổng thể."
        )

        return {
            "status": "SUCCESS",
            "sample_size": n,
            "degrees_of_freedom": p,
            "scale_variables_count": p,
            "scale_variable_ids": scale_question_ids,
            "mean_d2": round(mean_d2, 2),
            "median_d2": round(median_d2, 2),
            "max_d2": round(max_d2, 2),
            "critical_chi2_001": critical_val_001,
            "total_outliers_count": total_outliers,
            "extreme_outliers_count": extreme_count,
            "moderate_outliers_count": moderate_count,
            "outlier_rate_pct": round((total_outliers / n) * 100, 1) if n > 0 else 0.0,
            "apa_interpretation": apa_interpretation,
            "outliers_summary": results[:25],  # Top 25 dị biệt nhất
            "all_records_count": len(results)
        }
