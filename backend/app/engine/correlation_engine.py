import math
from typing import Dict, Any, List, Optional, Tuple

class CorrelationEngine:
    """
    Động cơ Phân tích Tương quan Đôi (Bivariate Correlation Analysis Engine)
    hỗ trợ hệ số tương quan Pearson r (tham số), Spearman rho (phi tham số dựa trên thứ bậc),
    kiểm định ý nghĩa thống kê 2 phía (Two-Tailed Student's t p-value),
    khoảng tin cậy 95% chuyển đổi Fisher z, và sàng lọc nguy cơ đa cộng tuyến (Multicollinearity Screening).

    Cơ sở phương pháp luận học thuật:
    - Pearson, K. (1895). Notes on regression and inheritance in the case of two parents.
    - Spearman, C. (1904). The proof and measurement of association between two things.
    - Fisher, R. A. (1915). Frequency distribution of the values of the correlation coefficient.
    - Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences.
    - Tabachnick, B. G., & Fidell, L. S. (2019). Using Multivariate Statistics (7th ed.).
    """

    @staticmethod
    def _betainc(a: float, b: float, x: float) -> float:
        """Hàm Beta không đầy đủ chính quy hóa I_x(a, b) dùng thuật toán liên phân số Lentz"""
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0

        if x > (a + 1.0) / (a + b + 2.0):
            return 1.0 - CorrelationEngine._betainc(b, a, 1.0 - x)

        log_beta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
        front = math.exp(math.log(x) * a + math.log(1.0 - x) * b - log_beta) / a

        tiny = 1e-30
        c = 1.0
        d = 1.0 - (a + b) * x / (a + 1.0)
        if abs(d) < tiny:
            d = tiny
        d = 1.0 / d
        f = d

        for m in range(1, 100):
            m2 = 2 * m
            num_even = (m * (b - m) * x) / ((a + m2 - 1.0) * (a + m2))
            d = 1.0 + num_even * d
            if abs(d) < tiny:
                d = tiny
            c = 1.0 + num_even / c
            if abs(c) < tiny:
                c = tiny
            d = 1.0 / d
            f *= (d * c)

            num_odd = -((a + m) * (a + b + m) * x) / ((a + m2) * (a + m2 + 1.0))
            d = 1.0 + num_odd * d
            if abs(d) < tiny:
                d = tiny
            c = 1.0 + num_odd / c
            if abs(c) < tiny:
                c = tiny
            d = 1.0 / d
            del_val = d * c
            f *= del_val

            if abs(del_val - 1.0) < 1e-12:
                break

        return max(0.0, min(1.0, front * f))

    @classmethod
    def _t_p_value_2tailed(cls, t_stat: float, df: float) -> float:
        """Tính p-value 2-tailed cho phân phối Student's t"""
        if df <= 0:
            return 1.0
        t_abs = abs(t_stat)
        if t_abs < 1e-12:
            return 1.0
        x = df / (df + t_abs * t_abs)
        p = cls._betainc(df / 2.0, 0.5, x)
        return max(0.0, min(1.0, p))

    @staticmethod
    def _compute_ranks(values: List[float]) -> List[float]:
        """
        Gán thứ bậc thập phân chuẩn hóa (Fractional Ranks) cho mảng giá trị,
        xử lý chính xác các giá trị trùng lặp (ties) theo trung bình thứ bậc.
        """
        n = len(values)
        indexed = sorted(enumerate(values), key=lambda x: x[1])
        ranks = [0.0] * n

        i = 0
        while i < n:
            j = i
            while j < n - 1 and abs(indexed[j + 1][1] - indexed[j][1]) < 1e-12:
                j += 1
            avg_rank = (i + 1 + j + 1) / 2.0
            for k in range(i, j + 1):
                ranks[indexed[k][0]] = avg_rank
            i = j + 1

        return ranks

    @classmethod
    def compute_pearson_r(cls, x: List[float], y: List[float]) -> Tuple[float, float, float, float]:
        """
        Tính hệ số tương quan Pearson r, p-value 2 phía, và khoảng tin cậy 95% (Fisher z).
        Trả về: (r, p_value, ci_lower, ci_upper)
        """
        n = len(x)
        if n < 3:
            return 0.0, 1.0, -1.0, 1.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        ss_xx = sum((xi - mean_x) ** 2 for xi in x)
        ss_yy = sum((yi - mean_y) ** 2 for yi in y)
        ss_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))

        if ss_xx < 1e-12 or ss_yy < 1e-12:
            return 0.0, 1.0, 0.0, 0.0

        r = ss_xy / math.sqrt(ss_xx * ss_yy)
        r = max(-1.0, min(1.0, r))

        # Thống kê t cho p-value
        df = n - 2
        if abs(abs(r) - 1.0) < 1e-9:
            p_val = 0.0
        else:
            denom = math.sqrt(max(1e-12, (1.0 - r * r) / df))
            t_stat = r / denom
            p_val = cls._t_p_value_2tailed(t_stat, float(df))

        # Khoảng tin cậy 95% qua chuyển đổi Fisher z
        r_clamped = max(-0.99999, min(0.99999, r))
        z = 0.5 * math.log((1.0 + r_clamped) / (1.0 - r_clamped))
        se_z = 1.0 / math.sqrt(n - 3) if n > 3 else 0.5
        z_low = z - 1.96 * se_z
        z_up = z + 1.96 * se_z

        ci_low = (math.exp(2.0 * z_low) - 1.0) / (math.exp(2.0 * z_low) + 1.0)
        ci_up = (math.exp(2.0 * z_up) - 1.0) / (math.exp(2.0 * z_up) + 1.0)

        return r, p_val, max(-1.0, min(1.0, ci_low)), max(-1.0, min(1.0, ci_up))

    @classmethod
    def compute_spearman_rho(cls, x: List[float], y: List[float]) -> Tuple[float, float, float, float]:
        """
        Tính hệ số tương quan hạng Spearman rho và p-value 2 phía.
        Trả về: (rho, p_value, ci_lower, ci_upper)
        """
        n = len(x)
        if n < 3:
            return 0.0, 1.0, -1.0, 1.0

        ranks_x = cls._compute_ranks(x)
        ranks_y = cls._compute_ranks(y)

        # Pearson trên các hạng là Spearman chính xác kể cả khi có ties
        return cls.compute_pearson_r(ranks_x, ranks_y)

    @staticmethod
    def _interpret_strength(abs_r: float) -> str:
        """Phân loại độ mạnh tương quan theo thang chuẩn Evans (1996) & Cohen (1988)"""
        if abs_r < 0.20:
            return "Rất yếu (Very Weak)"
        elif abs_r < 0.40:
            return "Yếu (Weak)"
        elif abs_r < 0.60:
            return "Trung bình (Moderate)"
        elif abs_r < 0.80:
            return "Mạnh (Strong)"
        else:
            return "Rất mạnh (Very Strong)"

    @classmethod
    def analyze_correlation_matrix(
        cls,
        variables_data: Dict[str, Dict[str, Any]],
        method: str = "pearson"
    ) -> Dict[str, Any]:
        """
        Phân tích Ma trận Tương quan Đôi hoàn chỉnh giữa các biến thang đo định lượng.
        variables_data: {
            "var_id": {
                "title": "Tiêu đề câu hỏi",
                "label": "Tên biến (VAR001...)",
                "values": [val1, val2, ...]
            }
        }
        """
        var_keys = list(variables_data.keys())
        k = len(var_keys)

        if k < 2:
            return {
                "status": "INSUFFICIENT_VARIABLES",
                "message": "Cần tối thiểu 2 biến thang đo định lượng để xây dựng ma trận tương quan."
            }

        # Tìm các quan sát hợp lệ chung trên toàn bộ các biến (listwise deletion)
        # Hoặc ghép cặp từng đôi (pairwise deletion). Trong khoa học, pairwise tối ưu cỡ mẫu hơn.
        var_summaries = []
        for v_id in var_keys:
            raw_vals = [float(v) for v in variables_data[v_id].get("values", []) if v is not None and str(v).strip() != ""]
            n_v = len(raw_vals)
            m_v = sum(raw_vals) / n_v if n_v > 0 else 0.0
            std_v = math.sqrt(sum((x - m_v)**2 for x in raw_vals) / (n_v - 1)) if n_v > 1 else 0.0
            var_summaries.append({
                "id": v_id,
                "title": variables_data[v_id].get("title", v_id),
                "label": variables_data[v_id].get("label", v_id),
                "n": n_v,
                "mean": round(m_v, 3),
                "std": round(std_v, 3)
            })

        matrix = []
        high_correlations = []
        multicollinearity_warnings = []

        total_pairs = 0
        significant_pairs_05 = 0

        for i in range(k):
            row_items = []
            v1_id = var_keys[i]
            v1_vals = variables_data[v1_id].get("values", [])

            for j in range(k):
                v2_id = var_keys[j]
                v2_vals = variables_data[v2_id].get("values", [])

                if i == j:
                    row_items.append({
                        "var1_id": v1_id,
                        "var2_id": v2_id,
                        "correlation": 1.0,
                        "p_value": 0.0,
                        "is_significant_05": True,
                        "is_significant_01": True,
                        "is_significant_001": True,
                        "ci_95_lower": 1.0,
                        "ci_95_upper": 1.0,
                        "strength": "Hoàn hảo (Perfect)",
                        "direction": "Đồng biến (Positive)"
                    })
                    continue

                # Lọc các cặp quan sát cùng hợp lệ
                paired_x = []
                paired_y = []
                for x_val, y_val in zip(v1_vals, v2_vals):
                    if x_val is not None and y_val is not None:
                        try:
                            paired_x.append(float(x_val))
                            paired_y.append(float(y_val))
                        except (ValueError, TypeError):
                            continue

                n_pair = len(paired_x)
                if n_pair < 3:
                    row_items.append({
                        "var1_id": v1_id,
                        "var2_id": v2_id,
                        "correlation": 0.0,
                        "p_value": 1.0,
                        "is_significant_05": False,
                        "is_significant_01": False,
                        "is_significant_001": False,
                        "ci_95_lower": -1.0,
                        "ci_95_upper": 1.0,
                        "strength": "Không đủ dữ liệu",
                        "direction": "Trung lập"
                    })
                    continue

                if method == "spearman":
                    r_val, p_val, ci_low, ci_up = cls.compute_spearman_rho(paired_x, paired_y)
                else:
                    r_val, p_val, ci_low, ci_up = cls.compute_pearson_r(paired_x, paired_y)

                abs_r = abs(r_val)
                strength_desc = cls._interpret_strength(abs_r)
                direction = "Đồng biến (Positive)" if r_val > 0 else ("Nghịch biến (Negative)" if r_val < 0 else "Không tương quan")

                is_sig_05 = p_val < 0.05
                is_sig_01 = p_val < 0.01
                is_sig_001 = p_val < 0.001

                cell_data = {
                    "var1_id": v1_id,
                    "var2_id": v2_id,
                    "correlation": round(r_val, 3),
                    "p_value": round(p_val, 4),
                    "is_significant_05": is_sig_05,
                    "is_significant_01": is_sig_01,
                    "is_significant_001": is_sig_001,
                    "ci_95_lower": round(ci_low, 3),
                    "ci_95_upper": round(ci_up, 3),
                    "strength": strength_desc,
                    "direction": direction
                }
                row_items.append(cell_data)

                # Thu thập thông tin cho nửa ma trận trên (i < j)
                if i < j:
                    total_pairs += 1
                    if is_sig_05:
                        significant_pairs_05 += 1

                    pair_summary = {
                        "var1_id": v1_id,
                        "var1_title": variables_data[v1_id].get("title", v1_id),
                        "var2_id": v2_id,
                        "var2_title": variables_data[v2_id].get("title", v2_id),
                        "correlation": round(r_val, 3),
                        "p_value": round(p_val, 4),
                        "ci_95_lower": round(ci_low, 3),
                        "ci_95_upper": round(ci_up, 3),
                        "strength": strength_desc,
                        "direction": direction,
                        "n": n_pair
                    }

                    if abs_r >= 0.50:
                        high_correlations.append(pair_summary)

                    # Cảnh báo đa cộng tuyến nghiêm trọng (Tabachnick & Fidell, 2019)
                    if abs_r >= 0.85:
                        multicollinearity_warnings.append({
                            **pair_summary,
                            "warning": (
                                f"Hệ số tương quan |r| = {abs_r:.2f} >= 0.85 biểu thị nguy cơ đa cộng tuyến rất cao (Multicollinearity). "
                                f"Cân nhắc gộp biến hoặc loại bớt một trong hai biến khi chạy hồi quy đa biến."
                            )
                        })

            matrix.append(row_items)

        # Sắp xếp các cặp tương quan cao theo trị tuyệt đối giảm dần
        high_correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        # 5. Diễn giải APA 7th Edition
        method_name = "Pearson (r)" if method == "pearson" else "Spearman (rho)"
        strongest_pair = high_correlations[0] if high_correlations else None

        if strongest_pair:
            p_txt = "< .001" if strongest_pair["p_value"] < 0.001 else f"= {strongest_pair['p_value']:.3f}"
            strongest_text = (
                f"Mối tương quan mạnh nhất được ghi nhận giữa '{strongest_pair['var1_title']}' và "
                f"'{strongest_pair['var2_title']}', {method_name[0].lower()} = {strongest_pair['correlation']:.2f}, "
                f"p {p_txt}, 95% CI [{strongest_pair['ci_95_lower']:.2f}, {strongest_pair['ci_95_upper']:.2f}]."
            )
        else:
            strongest_text = "Không ghi nhận cặp biến nào có tương quan đạt mức mạnh (|r| >= .50)."

        sig_pct = (significant_pairs_05 / total_pairs * 100.0) if total_pairs > 0 else 0.0

        if multicollinearity_warnings:
            collin_text = (
                f"Lưu ý học thuật: Phát hiện {len(multicollinearity_warnings)} cặp biến có tương quan rất cao (|r| >= .85), "
                f"cần kiểm định VIF (Variance Inflation Factor) trước khi xây dựng mô hình hồi quy OLS/SEM."
            )
        else:
            collin_text = "Tất cả các cặp biến đều duy trì tương quan dưới ngưỡng đa cộng tuyến nghiêm trọng (|r| < .85), phù hợp để tiến hành các phân tích đa biến tiếp theo."

        apa_narrative = (
            f"Phân tích tương quan đôi {method_name} được tiến hành giữa K = {k} thang đo định lượng. "
            f"Trong tổng số {total_pairs} cặp tương quan được khảo sát, có {significant_pairs_05} cặp "
            f"({sig_pct:.1f}%) đạt ý nghĩa thống kê ở mức alpha = .05. "
            f"{strongest_text} "
            f"{collin_text}"
        )

        return {
            "status": "SUCCESS",
            "method": method,
            "variables_count": k,
            "total_pairs_count": total_pairs,
            "significant_pairs_count": significant_pairs_05,
            "variables": var_summaries,
            "matrix": matrix,
            "high_correlations": high_correlations,
            "multicollinearity_warnings": multicollinearity_warnings,
            "apa_interpretation": apa_narrative
        }
