"""
Statistical Moderation & Interaction Effects Analysis Engine (PROCESS Model 1 - Hayes 2018).

Cơ sở phương pháp luận học thuật:
- Hayes, A. F. (2018). Introduction to Mediation, Moderation, and Conditional Process Analysis:
  A Regression-Based Approach (2nd ed.). Guilford Press.
- Aiken, L. S., & West, S. G. (1991). Multiple Regression: Testing and Interpreting Interactions.
  Sage Publications.
- Johnson, P. O., & Neyman, J. (1936). Tests of certain linear hypotheses and their application
  to some educational problems. Statistical Research Memoirs, 1, 57-93.
- Bauer, D. J., & Curran, P. J. (2005). Probing interactions in fixed and multilevel regression:
  Inferential and graphical techniques. Multivariate Behavioral Research, 40(3), 373-400.
- Cohen, J., Cohen, P., West, S. G., & Aiken, L. S. (2003). Applied Multiple Regression/Correlation
  Analysis for the Behavioral Sciences. Routledge.
"""

import math
from typing import Dict, Any, List, Optional, Tuple

try:
    from app.engine.regression_engine import RegressionEngine
except ModuleNotFoundError:
    from backend.app.engine.regression_engine import RegressionEngine


class ModerationEngine:
    """
    Động cơ Phân tích Tác động Điều tiết & Hiệu ứng Tương tác (PROCESS Model 1).
    Hỗ trợ:
    1. Chuẩn hóa mean-centering (Aiken & West 1991) triệt tiêu đa cộng tuyến
    2. Kiểm định gia tăng phương sai (Delta R^2 F-test) của số hạng tương tác X * W
    3. Phân tích độ dốc đơn (Simple Slopes / Pick-a-Point: Low, Mean, High Moderator)
    4. Kỹ thuật Johnson-Neyman xác định điểm chuyển tiếp ý nghĩa liên tục
    5. Tọa độ trực quan hóa sơ đồ tương tác 2D
    6. Đoạn trích APA 7th Edition hoàn chỉnh
    """

    @staticmethod
    def _betainc(a: float, b: float, x: float) -> float:
        """Incomplete beta function"""
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0

        lgamma_ab = math.lgamma(a + b)
        lgamma_a = math.lgamma(a)
        lgamma_b = math.lgamma(b)
        front = math.exp(lgamma_ab - lgamma_a - lgamma_b + a * math.log(x) + b * math.log(1.0 - x))

        qab = a + b
        qap = a + 1.0
        qam = a - 1.0
        c = 1.0
        d = 1.0 - qab * x / qap
        tiny = 1e-30
        if abs(d) < tiny:
            d = tiny
        d = 1.0 / d
        f = d

        for m in range(1, 120):
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

            num_odd = -((a + m) * (qab + m) * x) / ((a + m2) * (a + m2 + 1.0))
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

        return max(0.0, min(1.0, front * f / a))

    @classmethod
    def _f_p_value(cls, f_stat: float, df1: float, df2: float) -> float:
        """Tính p-value cho phân phối F"""
        if f_stat <= 0.0 or df1 <= 0.0 or df2 <= 0.0:
            return 1.0
        x = df2 / (df2 + df1 * f_stat)
        p = cls._betainc(df2 / 2.0, df1 / 2.0, x)
        return max(0.0, min(1.0, p))

    @classmethod
    def _t_p_value_2tailed(cls, t_stat: float, df: float) -> float:
        """Tính two-tailed p-value cho Student-t"""
        if df <= 0:
            return 1.0
        t_abs = abs(t_stat)
        if t_abs < 1e-12:
            return 1.0
        x = df / (df + t_abs * t_abs)
        p = cls._betainc(df / 2.0, 0.5, x)
        return max(0.0, min(1.0, p))

    @classmethod
    def _t_critical(cls, df: float, alpha: float = 0.05) -> float:
        """Ước lượng giá trị tới hạn t_crit cho kiểm định 2 phía (mặc định alpha = 0.05)"""
        # Xấp xỉ Hill (1970) cho phân vị t
        if df >= 120:
            return 1.960
        # Bảng xấp xỉ cho df nhỏ
        approx_table = {
            1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
            6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
            12: 2.179, 15: 2.131, 20: 2.086, 25: 2.060, 30: 2.042,
            40: 2.021, 50: 2.009, 60: 2.000, 80: 1.990, 100: 1.984
        }
        for k in sorted(approx_table.keys()):
            if df <= k:
                return approx_table[k]
        return 1.960

    @classmethod
    def analyze_moderation(
        cls,
        x: List[float],
        w: List[float],
        y: List[float],
        center_variables: bool = True,
        x_label: str = "X",
        w_label: str = "W",
        y_label: str = "Y"
    ) -> Dict[str, Any]:
        """
        Thực hiện phân tích điều tiết đầy đủ (PROCESS Model 1):
        Y = b0 + b1*X + b2*W + b3*(X*W)
        """
        n = len(y)
        if n < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 8 phản hồi hoàn chỉnh để phân tích điều tiết (hiện có {n})."
            }

        mean_x = sum(x) / n
        mean_w = sum(w) / n
        mean_y = sum(y) / n

        var_x = sum((xi - mean_x) ** 2 for xi in x) / (n - 1)
        var_w = sum((wi - mean_w) ** 2 for wi in w) / (n - 1)
        var_y = sum((yi - mean_y) ** 2 for yi in y) / (n - 1)

        if var_x < 1e-7 or var_w < 1e-7 or var_y < 1e-7:
            return {
                "status": "ZERO_VARIANCE",
                "message": "Một hoặc nhiều biến có phương sai bằng 0 (dữ liệu hằng số)."
            }

        std_x = math.sqrt(max(1e-12, var_x))
        std_w = math.sqrt(max(1e-12, var_w))
        std_y = math.sqrt(max(1e-12, var_y))

        # 1. Mean-centering
        if center_variables:
            x_centered = [xi - mean_x for xi in x]
            w_centered = [wi - mean_w for wi in w]
        else:
            x_centered = list(x)
            w_centered = list(w)

        xw_interaction = [x_centered[i] * w_centered[i] for i in range(n)]

        # 2. Model 1 (Main Effects Only: Y ~ X + W)
        X_mat1 = [[x_centered[i], w_centered[i]] for i in range(n)]
        fit_m1 = RegressionEngine.fit_ols(
            X_matrix=X_mat1,
            y_vector=y,
            predictor_labels=["X", "W"],
            predictor_titles=[x_label, w_label],
            dependent_title=y_label
        )

        r2_m1 = fit_m1.get("model_summary", {}).get("r_squared", 0.0)

        # 3. Model 2 (Full Model with Interaction: Y ~ X + W + X*W)
        X_mat2 = [[x_centered[i], w_centered[i], xw_interaction[i]] for i in range(n)]
        fit_m2 = RegressionEngine.fit_ols(
            X_matrix=X_mat2,
            y_vector=y,
            predictor_labels=["X", "W", "X*W"],
            predictor_titles=[x_label, w_label, f"{x_label} * {w_label}"],
            dependent_title=y_label
        )

        r2_m2 = fit_m2.get("model_summary", {}).get("r_squared", 0.0)
        df_res = n - 4
        f_m2 = fit_m2.get("anova_table", {}).get("f_statistic", 0.0)
        p_m2 = fit_m2.get("anova_table", {}).get("p_value", 1.0)

        # 4. Kiểm định gia tăng phương sai (Delta R^2)
        delta_r2 = max(0.0, r2_m2 - r2_m1)
        mse_m2 = fit_m2.get("anova_table", {}).get("ms_residual", 1.0)
        if df_res > 0 and (1.0 - r2_m2) > 1e-12:
            f_change = (delta_r2 / 1.0) / ((1.0 - r2_m2) / df_res)
            p_change = cls._f_p_value(f_change, 1.0, float(df_res))
        else:
            f_change = 0.0
            p_change = 1.0

        coeffs_m2 = fit_m2.get("coefficients", [])
        # coeffs_m2: [Const, X, W, X*W]
        b0 = coeffs_m2[0]["b_unstandardized"] if len(coeffs_m2) > 0 else 0.0
        b1 = coeffs_m2[1]["b_unstandardized"] if len(coeffs_m2) > 1 else 0.0
        b2 = coeffs_m2[2]["b_unstandardized"] if len(coeffs_m2) > 2 else 0.0
        b3 = coeffs_m2[3]["b_unstandardized"] if len(coeffs_m2) > 3 else 0.0

        se_b1 = coeffs_m2[1]["std_error"] if len(coeffs_m2) > 1 else 0.1
        se_b3 = coeffs_m2[3]["std_error"] if len(coeffs_m2) > 3 else 0.1
        p_b3 = coeffs_m2[3]["p_value"] if len(coeffs_m2) > 3 else 1.0

        is_moderation_significant = p_b3 < 0.05

        # Trích xuất ma trận hiệp phương sai ước lượng (X'X)^-1 * MSE
        # Để tính chính xác Cov(b1, b3)
        # Thiết lập ma trận thiết kế X_aug (n x 4: 1, X, W, X*W)
        X_aug = [[1.0, x_centered[i], w_centered[i], xw_interaction[i]] for i in range(n)]
        XtX = [[sum(X_aug[r][i] * X_aug[r][j] for r in range(n)) for j in range(4)] for i in range(4)]
        inv_XtX = RegressionEngine._invert_matrix(XtX, ridge=1e-7)
        if inv_XtX:
            cov_b1_b3 = inv_XtX[1][3] * mse_m2
            var_b1 = inv_XtX[1][1] * mse_m2
            var_b3 = inv_XtX[3][3] * mse_m2
        else:
            cov_b1_b3 = 0.0
            var_b1 = se_b1 ** 2
            var_b3 = se_b3 ** 2

        # 5. Phân tích độ dốc đơn (Simple Slopes Analysis / Pick-a-Point)
        # Các mức của W (nếu đã centering thì mean_w = 0, low = -std_w, high = +std_w)
        w_levels = [
            {
                "level": "LOW",
                "label": f"Thấp (-1 SD: {mean_w - std_w:.2f})",
                "w_value_centered": -std_w if center_variables else mean_w - std_w,
                "w_value_raw": mean_w - std_w
            },
            {
                "level": "MEAN",
                "label": f"Trung bình (Mean: {mean_w:.2f})",
                "w_value_centered": 0.0 if center_variables else mean_w,
                "w_value_raw": mean_w
            },
            {
                "level": "HIGH",
                "label": f"Cao (+1 SD: {mean_w + std_w:.2f})",
                "w_value_centered": std_w if center_variables else mean_w + std_w,
                "w_value_raw": mean_w + std_w
            }
        ]

        simple_slopes = []
        for wl in w_levels:
            w_val = wl["w_value_centered"]
            # Slope của X khi W = w_val: b_cond = b1 + b3 * w_val
            slope_cond = b1 + b3 * w_val
            # SE = sqrt(var(b1) + 2*w*cov(b1,b3) + w^2*var(b3))
            se_cond_sq = var_b1 + 2.0 * w_val * cov_b1_b3 + (w_val ** 2) * var_b3
            se_cond = math.sqrt(max(1e-12, se_cond_sq))
            t_cond = slope_cond / se_cond
            p_cond = cls._t_p_value_2tailed(t_cond, float(df_res))
            ci_low = slope_cond - 1.96 * se_cond
            ci_high = slope_cond + 1.96 * se_cond

            simple_slopes.append({
                "level": wl["level"],
                "label": wl["label"],
                "w_value": round(wl["w_value_raw"], 3),
                "slope": round(slope_cond, 4),
                "std_error": round(se_cond, 4),
                "t_stat": round(t_cond, 3),
                "p_value": round(p_cond, 4),
                "ci_95_lower": round(ci_low, 4),
                "ci_95_upper": round(ci_high, 4),
                "is_significant": p_cond < 0.05
            })

        # 6. Kỹ thuật Johnson-Neyman (1936; Bauer & Curran 2005)
        # Giải phương trình bậc 2: A*W^2 + B*W + C = 0
        t_crit = cls._t_critical(float(df_res), 0.05)
        t_crit_sq = t_crit ** 2

        A = (b3 ** 2) - t_crit_sq * var_b3
        B = 2.0 * (b1 * b3 - t_crit_sq * cov_b1_b3)
        C = (b1 ** 2) - t_crit_sq * var_b1

        discriminant = B * B - 4.0 * A * C

        jn_points = []
        jn_within_range = []
        min_w_raw = min(w)
        max_w_raw = max(w)

        if abs(A) > 1e-9 and discriminant >= 0.0:
            sqrt_disc = math.sqrt(discriminant)
            w1_c = (-B - sqrt_disc) / (2.0 * A)
            w2_c = (-B + sqrt_disc) / (2.0 * A)

            w1_raw = w1_c + mean_w if center_variables else w1_c
            w2_raw = w2_c + mean_w if center_variables else w2_c

            for pt in sorted([w1_raw, w2_raw]):
                jn_points.append(round(pt, 3))
                if min_w_raw <= pt <= max_w_raw:
                    jn_within_range.append(round(pt, 3))

        # Tỷ lệ mẫu nằm trong vùng có ý nghĩa
        pct_significant = 100.0
        if len(jn_within_range) == 1:
            pt = jn_within_range[0]
            # Đếm tỷ lệ mẫu có W >= pt hoặc <= pt tùy theo độ dốc
            count_sig = sum(1 for wi in w if wi >= pt) if b3 > 0 else sum(1 for wi in w if wi <= pt)
            pct_significant = (count_sig / n) * 100.0
        elif len(jn_within_range) == 2:
            pt1, pt2 = jn_within_range
            count_sig = sum(1 for wi in w if wi <= pt1 or wi >= pt2)
            pct_significant = (count_sig / n) * 100.0

        # 7. Tọa độ trực quan hóa đồ thị tương tác 2D (Interaction Plot Lines)
        # X tại -1 SD và +1 SD
        x_low_raw = mean_x - std_x
        x_high_raw = mean_x + std_x

        x_low_c = -std_x if center_variables else x_low_raw
        x_high_c = std_x if center_variables else x_high_raw

        plot_lines = []
        for wl in w_levels:
            wc = wl["w_value_centered"]
            # Y_pred = b0 + b1*X + b2*W + b3*(X*W)
            y_pred_low_x = b0 + b1 * x_low_c + b2 * wc + b3 * (x_low_c * wc)
            y_pred_high_x = b0 + b1 * x_high_c + b2 * wc + b3 * (x_high_c * wc)

            plot_lines.append({
                "level": wl["level"],
                "label": wl["label"],
                "point_low_x": {
                    "x": round(x_low_raw, 2),
                    "y_pred": round(y_pred_low_x, 2)
                },
                "point_high_x": {
                    "x": round(x_high_raw, 2),
                    "y_pred": round(y_pred_high_x, 2)
                }
            })

        # 8. Đoạn trích APA 7th Edition
        apa_narrative = (
            f"Phân tích hồi quy điều tiết phân bậc (Hierarchical Moderation Analysis - PROCESS Model 1) "
            f"được tiến hành nhằm đánh giá vai trò điều tiết của {w_label} lên mối quan hệ giữa {x_label} và {y_label}. "
            f"Các biến dự báo đã được chuẩn hóa mean-centering theo khuyến nghị của Aiken & West (1991). "
            f"Kết quả chỉ ra rằng số hạng tương tác giữa {x_label} và {w_label} "
            f"giải thích thêm một phần phương sai có ý nghĩa thống kê của {y_label} "
            f"(Delta R^2 = {delta_r2:.4f}, F(1, {df_res}) = {f_change:.3f}, p = {p_change:.4f}, b = {b3:.4f}, t = {coeffs_m2[3]['t_stat']:.3f}). "
            + (
                f"Phân tích độ dốc đơn (Simple Slopes) chỉ ra rằng tác động của {x_label} lên {y_label} "
                f"có ý nghĩa mạnh nhất khi {w_label} ở mức cao (b = {simple_slopes[2]['slope']:.3f}, p = {simple_slopes[2]['p_value']:.4f}) "
                f"và suy giảm khi {w_label} ở mức thấp (b = {simple_slopes[0]['slope']:.3f}, p = {simple_slopes[0]['p_value']:.4f}). "
                f"Kỹ thuật Johnson-Neyman khẳng định vùng chuyển tiếp ý nghĩa nằm tại W = {jn_within_range} "
                f"với {pct_significant:.1f}% mẫu quan sát thuộc vùng có ý nghĩa thống kê."
                if is_moderation_significant
                else f"Không tìm thấy bằng chứng có ý nghĩa thống kê về vai trò điều tiết của {w_label} (p > .05)."
            )
        )

        return {
            "status": "SUCCESS",
            "sample_size": n,
            "center_variables": center_variables,
            "variables": {
                "independent_x": {"label": "X", "title": x_label, "mean": round(mean_x, 3), "std": round(std_x, 3)},
                "moderator_w": {"label": "W", "title": w_label, "mean": round(mean_w, 3), "std": round(std_w, 3), "range": [round(min_w_raw, 2), round(max_w_raw, 2)]},
                "dependent_y": {"label": "Y", "title": y_label, "mean": round(mean_y, 3), "std": round(std_y, 3)}
            },
            "model_1_main_effects": {
                "r_squared": round(r2_m1, 4),
                "f_stat": round(fit_m1.get("anova_table", {}).get("f_statistic", 0.0), 3),
                "p_value": round(fit_m1.get("anova_table", {}).get("p_value", 1.0), 4)
            },
            "model_2_moderation": {
                "r_squared": round(r2_m2, 4),
                "f_stat": round(f_m2, 3),
                "p_value": round(p_m2, 4),
                "coefficients": fit_m2.get("coefficients", [])
            },
            "moderation_effect": {
                "delta_r_squared": round(delta_r2, 4),
                "delta_f_stat": round(f_change, 3),
                "delta_p_value": round(p_change, 4),
                "interaction_b": round(b3, 4),
                "interaction_se": round(se_b3, 4),
                "interaction_t": round(coeffs_m2[3]["t_stat"] if len(coeffs_m2) > 3 else 0.0, 3),
                "interaction_p": round(p_b3, 4),
                "is_significant": is_moderation_significant,
                "verdict_badge": "ĐIỀU TIẾT CÓ Ý NGHĨA" if is_moderation_significant else "KHÔNG ĐIỀU TIẾT"
            },
            "simple_slopes": simple_slopes,
            "johnson_neyman": {
                "has_solution": len(jn_points) > 0,
                "all_transition_points": jn_points,
                "points_within_observed_range": jn_within_range,
                "observed_moderator_range": [round(min_w_raw, 2), round(max_w_raw, 2)],
                "percent_sample_significant": round(pct_significant, 1),
                "interpretation": (
                    f"Kỹ thuật Johnson-Neyman xác định điểm chuyển tiếp ý nghĩa tại W = {jn_within_range}. "
                    f"Có {pct_significant:.1f}% số quan sát trong mẫu khảo sát nằm trong miền mà tác động của X lên Y đạt ý nghĩa thống kê (p < 0.05)."
                    if jn_within_range
                    else "Không có điểm chuyển tiếp Johnson-Neyman nào rơi vào miền giá trị quan sát của biến điều tiết W."
                )
            },
            "interaction_plot": {
                "x_axis_label": x_label,
                "y_axis_label": y_label,
                "x_range": [round(x_low_raw, 2), round(x_high_raw, 2)],
                "lines": plot_lines
            },
            "apa_narrative": apa_narrative
        }
