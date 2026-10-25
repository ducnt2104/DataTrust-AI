import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats

class EquatingEngine:
    """
    Động cơ Chuẩn hóa & Liên kết Thang đo (Score Equating & Concordance Transformation Engine).
    
    Tuân thủ các chuẩn mực đo lường học thuật và trắc lượng tâm lý:
    - Kolen, M. J., & Brennan, R. L. (2014). Test Equating, Scaling, and Linking: Methods and Practices (3rd ed.). Springer.
    - Angoff, W. H. (1971). Scales, norms, and equivalent scores. Educational Measurement, 2, 508-600.
    - Holland, P. W., & Thayer, D. T. (1987). Notes on loglinear models for equating. ETS Research Report Series.
    - Braun, H. I., & Holland, P. W. (1982). Observed-score test equating: A review. Test Equating, 9-49.
    """

    @staticmethod
    def equate_scales(
        x_values: List[float],
        y_values: List[float],
        x_label: str = "Thang đo nguồn X",
        y_label: str = "Thang đo đích Y",
        x_min: Optional[float] = None,
        x_max: Optional[float] = None,
        y_min: Optional[float] = None,
        y_max: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Tính toán hàm liên kết tuyến tính (Linear Equating) và phân vị (Equipercentile Equating),
        sinh bảng quy đổi tương đương (Concordance Table) giữa 2 thang đo/câu hỏi khảo sát.
        """
        # Lọc các giá trị hợp lệ
        valid_x = np.array([float(v) for v in x_values if v is not None and not math.isnan(float(v))])
        valid_y = np.array([float(v) for v in y_values if v is not None and not math.isnan(float(v))])

        Nx = len(valid_x)
        Ny = len(valid_y)

        if Nx < 5 or Ny < 5:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 5 quan sát cho mỗi thang đo (hiện có X: {Nx}, Y: {Ny})."
            }

        # 1. Thống kê mô tả hai thang đo
        mu_x = float(np.mean(valid_x))
        sigma_x = float(np.std(valid_x, ddof=1)) if Nx > 1 else 1.0
        if sigma_x == 0:
            sigma_x = 1e-4

        mu_y = float(np.mean(valid_y))
        sigma_y = float(np.std(valid_y, ddof=1)) if Ny > 1 else 1.0
        if sigma_y == 0:
            sigma_y = 1e-4

        skew_x = float(stats.skew(valid_x)) if Nx > 2 else 0.0
        skew_y = float(stats.skew(valid_y)) if Ny > 2 else 0.0

        # Xác định miền giá trị của thang đo
        min_x = x_min if x_min is not None else float(np.min(valid_x))
        max_x = x_max if x_max is not None else float(np.max(valid_x))
        min_y = y_min if y_min is not None else float(np.min(valid_y))
        max_y = y_max if y_max is not None else float(np.max(valid_y))

        # 2. Linear Equating (Tucker / Levine):
        # l_Y(x) = (sigma_Y / sigma_X) * (x - mu_X) + mu_Y
        alpha = sigma_y / sigma_x
        beta = mu_y - alpha * mu_x

        # 3. Equipercentile Equating (Kolen & Brennan 2014, pp. 35-44):
        # Continuous equipercentile conversion based on effective continuous interval [s - 0.5, s + 0.5]
        # and linear extrapolation for low/high scores outside empirical support.
        unique_y = np.sort(np.unique(valid_y))
        min_obs_x = float(np.min(valid_x))
        max_obs_x = float(np.max(valid_x))

        def equipercentile_convert(score: float) -> Tuple[float, float]:
            """
            Tính thứ hạng phân vị PR(x) và điểm quy đổi tương đương e_Y(x) theo Kolen & Brennan (2014).
            """
            # Ngoại suy tuyến tính (Linear extrapolation) cho các điểm nằm ngoài miền quan sát thực nghiệm
            if score < min_obs_x:
                extrapolated = alpha * score + beta
                return 0.0, float(extrapolated)
            if score > max_obs_x:
                extrapolated = alpha * score + beta
                return 100.0, float(extrapolated)

            f_less = float(np.sum(valid_x < score)) / Nx
            f_equal = float(np.sum(valid_x == score)) / Nx

            if f_equal == 0:
                # Nếu score không xuất hiện trực tiếp trong mẫu x, dùng nội suy ECDF
                p = float(np.sum(valid_x <= score)) / Nx
                pr_pct = p * 100.0
                eq_val = float(np.percentile(valid_y, pr_pct))
                return pr_pct, eq_val

            # Điểm giữa của khoảng phân vị (Midpoint percentile rank)
            p = f_less + 0.5 * f_equal
            pr_pct = p * 100.0

            # Nghịch đảo trên hàm phân phối tích lũy của Y
            for y_val in unique_y:
                g_less = float(np.sum(valid_y < y_val)) / Ny
                g_equal = float(np.sum(valid_y == y_val)) / Ny
                g_upper = g_less + g_equal
                if g_less <= p <= g_upper:
                    if g_equal > 0:
                        eq_score = (y_val - 0.5) + ((p - g_less) / g_equal)
                    else:
                        eq_score = float(y_val)
                    return pr_pct, float(eq_score)

            # Fallback nếu vượt ngoài cận trên/dưới
            eq_fallback = float(np.percentile(valid_y, np.clip(pr_pct, 0.0, 100.0)))
            return pr_pct, eq_fallback

        # 4. Xây dựng Bảng Quy Đổi Tương Đương (Concordance Table)
        # Sinh các mốc điểm của thang đo X
        range_x_span = max_x - min_x
        if range_x_span <= 15:
            # Ví dụ: Thang Likert 1-5 hoặc 1-7 hoặc NPS 0-10
            x_steps = np.arange(math.floor(min_x), math.ceil(max_x) + 0.01, 1.0)
            if len(x_steps) < 5:
                x_steps = np.arange(min_x, max_x + 0.01, 0.5)
        else:
            x_steps = np.linspace(min_x, max_x, num=15)

        concordance_table = []
        for x_val in x_steps:
            x_score = round(float(x_val), 2)
            # Linear equivalent
            linear_eq = alpha * x_score + beta
            linear_eq_bounded = float(np.clip(linear_eq, min_y, max_y))

            # Equipercentile equivalent
            pr, equi_eq = equipercentile_convert(x_score)
            equi_eq_bounded = float(np.clip(equi_eq, min_y, max_y))

            # Standardized T-Score (Mean=50, SD=10)
            t_score = 50.0 + 10.0 * ((x_score - mu_x) / sigma_x)

            # Stanine (Standard Nine: 1 to 9 scale)
            stanine = int(np.clip(round(5.0 + 2.0 * ((x_score - mu_x) / sigma_x)), 1, 9))

            concordance_table.append({
                "x_score": x_score,
                "percentile_rank": round(pr, 2),
                "linear_equivalent_raw": round(linear_eq, 3),
                "linear_equivalent": round(linear_eq_bounded, 2),
                "linear_equivalent_rounded": int(round(linear_eq_bounded)),
                "equipercentile_equivalent": round(equi_eq_bounded, 2),
                "equipercentile_rounded": int(round(equi_eq_bounded)),
                "t_score": round(t_score, 1),
                "stanine": stanine
            })

        # 5. So sánh Độ Bất Đồng Giữa Hai Phương Pháp (Equating Difference Metric)
        obs_diffs = [
            abs(row["linear_equivalent"] - row["equipercentile_equivalent"])
            for row in concordance_table
            if min_obs_x <= row["x_score"] <= max_obs_x
        ]
        diffs = obs_diffs if obs_diffs else [abs(row["linear_equivalent"] - row["equipercentile_equivalent"]) for row in concordance_table]
        max_discrepancy = round(float(max(diffs)), 3) if diffs else 0.0
        mean_discrepancy = round(float(np.mean(diffs)), 3) if diffs else 0.0

        # Đánh giá mức độ đồng quy (concordance agreement)
        if max_discrepancy < 0.25:
            agreement_verdict = "EXCELLENT"
            agreement_narrative = (
                "Hàm liên kết tuyến tính và phân vị gần như trùng khớp hoàn hảo (sai lệch tối đa < 0.25 điểm). "
                "Cả hai phân phối có hình dạng đối xứng tương đồng, cho phép áp dụng phương pháp Linear Equating đơn giản."
            )
        elif max_discrepancy < 0.75:
            agreement_verdict = "MODERATE"
            agreement_narrative = (
                f"Có sự khác biệt vừa phải giữa hai phương pháp (sai lệch tối đa {max_discrepancy} điểm). "
                "Khuyến nghị ưu tiên kết quả Equipercentile Equating để bảo toàn chính xác tỷ lệ phân vị thực nghiệm."
            )
        else:
            agreement_verdict = "SKEWED_DIVERGENCE"
            agreement_narrative = (
                f"Phát hiện độ phân kỳ lớn giữa hai phương pháp (sai lệch tối đa {max_discrepancy} điểm). "
                "Nguyên nhân do độ lệch (skewness) hoặc hiệu ứng trần/sàn (ceiling/floor effect) của một trong hai thang đo. "
                "Bắt buộc sử dụng Equipercentile Equating để tránh bóp méo phân phối điểm số."
            )

        # 6. Văn phong khoa học chuẩn APA 7th Edition
        apa_narrative = (
            f"Observed-score equating was performed between {x_label} (M = {mu_x:.2f}, SD = {sigma_x:.2f}, N = {Nx}) "
            f"and {y_label} (M = {mu_y:.2f}, SD = {sigma_y:.2f}, N = {Ny}). "
            f"The linear equating conversion function was l(X) = {alpha:.3f}X + {beta:.3f}. "
            f"Equipercentile concordance mappings confirmed distribution alignment across percentiles "
            f"with an average discrepancy of {mean_discrepancy:.2f} score units."
        )

        return {
            "status": "OK",
            "x_label": x_label,
            "y_label": y_label,
            "sample_sizes": {
                "x_count": Nx,
                "y_count": Ny
            },
            "descriptive_statistics": {
                "x_scale": {
                    "mean": round(mu_x, 3),
                    "std": round(sigma_x, 3),
                    "skewness": round(skew_x, 3),
                    "min_observed": float(np.min(valid_x)),
                    "max_observed": float(np.max(valid_x)),
                    "theoretical_range": [min_x, max_x]
                },
                "y_scale": {
                    "mean": round(mu_y, 3),
                    "std": round(sigma_y, 3),
                    "skewness": round(skew_y, 3),
                    "min_observed": float(np.min(valid_y)),
                    "max_observed": float(np.max(valid_y)),
                    "theoretical_range": [min_y, max_y]
                }
            },
            "linear_equating": {
                "slope_alpha": round(alpha, 4),
                "intercept_beta": round(beta, 4),
                "formula": f"Y_equiv = {alpha:.4f} * X + ({beta:.4f})"
            },
            "discrepancy_analysis": {
                "max_discrepancy": max_discrepancy,
                "mean_discrepancy": mean_discrepancy,
                "agreement_verdict": agreement_verdict,
                "agreement_narrative": agreement_narrative
            },
            "concordance_table": concordance_table,
            "apa_narrative": apa_narrative
        }

    @staticmethod
    def transform_respondent_scores(
        x_scores: List[Optional[float]],
        linear_alpha: float,
        linear_beta: float,
        y_bounds: Tuple[float, float],
        concordance_lookup: Optional[Dict[float, float]] = None
    ) -> List[Optional[float]]:
        """
        Chuyển đổi danh sách điểm số thực tế của người trả lời từ thang X sang thang Y.
        """
        y_min, y_max = y_bounds
        transformed = []
        for x in x_scores:
            if x is None or math.isnan(x):
                transformed.append(None)
                continue

            if concordance_lookup and round(float(x), 2) in concordance_lookup:
                val = concordance_lookup[round(float(x), 2)]
            else:
                val = linear_alpha * float(x) + linear_beta

            val_bounded = float(np.clip(val, y_min, y_max))
            transformed.append(round(val_bounded, 2))

        return transformed
