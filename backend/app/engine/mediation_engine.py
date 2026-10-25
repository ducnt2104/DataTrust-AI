import math
import random
from typing import Dict, Any, List, Optional, Tuple

try:
    from app.engine.regression_engine import RegressionEngine
except ModuleNotFoundError:
    from backend.app.engine.regression_engine import RegressionEngine

class MediationEngine:
    """
    Động cơ Phân tích Tác động Trung gian (Statistical Mediation & Path Analysis Engine)
    Tuân thủ phương pháp luận học thuật:
    - Baron, R. M., & Kenny, D. A. (1986). The moderator-mediator variable distinction in social psychological research.
    - Preacher, K. J., & Hayes, A. F. (2004, 2008). Asymptotic and resampling strategies for assessing and comparing indirect effects in multiple mediator models.
    - Hayes, A. F. (2018). Introduction to Mediation, Moderation, and Conditional Process Analysis (PROCESS Model 4).
    - Sobel, M. E. (1982). Asymptotic intervals for indirect effects in structural equations models.
    - Zhao, X., Lynch, J. G., & Chen, Q. (2010). Reconsidering Baron and Kenny: Myths and truths about mediation.
    - Hair, J. F., Hult, G. T. M., Ringle, C. M., & Sarstedt, M. (2017). Variance Accounted For (VAF) in PLS-SEM.
    """

    @staticmethod
    def _normal_cdf(z: float) -> float:
        """Hàm tích lũy chuẩn tắc phi(z) = 0.5 * (1 + erf(z / sqrt(2)))"""
        return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

    @classmethod
    def _sobel_p_value(cls, z: float) -> float:
        """Tính p-value 2 phía cho thống kê Sobel z"""
        p = 2.0 * (1.0 - cls._normal_cdf(abs(z)))
        return max(0.0, min(1.0, p))

    @classmethod
    def fit_simple_regression(
        cls,
        x: List[float],
        y: List[float]
    ) -> Dict[str, Any]:
        """
        Khớp mô hình hồi quy đơn biến OLS: y = beta_0 + beta_1 * x
        Trả về slope, intercept, standard errors, t-statistics, p-values, R-squared, F-stat.
        """
        n = len(x)
        if n < 3:
            return {"status": "INSUFFICIENT_DATA"}

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        ss_xx = sum((xi - mean_x) ** 2 for xi in x)
        ss_yy = sum((yi - mean_y) ** 2 for yi in y)
        ss_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))

        if ss_xx < 1e-12:
            return {"status": "ZERO_VARIANCE_X"}

        slope = ss_xy / ss_xx
        intercept = mean_y - slope * mean_x

        # Tổng bình phương phần dư (SSE)
        sse = sum((yi - (intercept + slope * xi)) ** 2 for xi, yi in zip(x, y))
        df_e = n - 2
        mse = sse / df_e if df_e > 0 else 0.0
        se_slope = math.sqrt(mse / ss_xx) if ss_xx > 0 and mse >= 0 else 0.0

        t_stat = slope / se_slope if se_slope > 1e-12 else 0.0
        p_val = RegressionEngine._t_p_value_2tailed(t_stat, df_e)

        r_sq = (ss_xy ** 2) / (ss_xx * ss_yy) if (ss_xx * ss_yy) > 1e-12 else 0.0
        f_stat = (r_sq * df_e) / (1.0 - r_sq) if (1.0 - r_sq) > 1e-12 else 0.0
        f_p_val = RegressionEngine._f_p_value(f_stat, 1, df_e)

        # Khoảng tin cậy 95% cho slope
        # Giá trị phân vị Student t xấp xỉ cho 95%
        t_crit = 1.96 if df_e >= 100 else (2.04 if df_e >= 30 else 2.1)
        ci_lower = slope - t_crit * se_slope
        ci_upper = slope + t_crit * se_slope

        # Hệ số chuẩn hóa beta (Standardized Beta)
        sd_x = math.sqrt(ss_xx / (n - 1)) if n > 1 else 1.0
        sd_y = math.sqrt(ss_yy / (n - 1)) if n > 1 else 1.0
        std_beta = slope * (sd_x / sd_y) if sd_y > 1e-12 else slope

        return {
            "status": "OK",
            "n": n,
            "intercept": round(intercept, 4),
            "slope": round(slope, 4),
            "std_beta": round(std_beta, 4),
            "se": round(se_slope, 4),
            "t_stat": round(t_stat, 3),
            "p_value": round(p_val, 5),
            "ci_lower": round(ci_lower, 4),
            "ci_upper": round(ci_upper, 4),
            "r_squared": round(r_sq, 4),
            "f_stat": round(f_stat, 3),
            "f_p_value": round(f_p_val, 5),
            "df": df_e
        }

    @classmethod
    def fit_multiple_regression_2pred(
        cls,
        x1: List[float],
        x2: List[float],
        y: List[float]
    ) -> Dict[str, Any]:
        """
        Khớp mô hình hồi quy đa biến với 2 biến độc lập: y = b0 + b1*x1 + b2*x2
        Sử dụng ma trận OLS qua RegressionEngine.fit_ols.
        """
        n = len(y)
        if n < 4:
            return {"status": "INSUFFICIENT_DATA"}

        X_matrix = [[x1[i], x2[i]] for i in range(n)]
        labels = ["pred_x1", "pred_x2"]
        titles = ["X", "M"]

        fit = RegressionEngine.fit_ols(
            X_matrix=X_matrix,
            y_vector=y,
            predictor_labels=labels,
            predictor_titles=titles,
            dependent_title="Y"
        )
        return fit

    @classmethod
    def run_bootstrap_indirect_effect(
        cls,
        x: List[float],
        m: List[float],
        y: List[float],
        num_samples: int = 1000,
        random_seed: int = 42
    ) -> Dict[str, Any]:
        """
        Ước lượng khoảng tin cậy không tham số Bootstrap (Preacher & Hayes 2004, 2008)
        cho tác động gián tiếp (Indirect Effect = a * b).
        """
        n = len(x)
        if n < 5:
            return {
                "bootstrap_samples": 0,
                "indirect_mean": 0.0,
                "se_boot": 0.0,
                "ci_lower": 0.0,
                "ci_upper": 0.0,
                "is_significant": False
            }

        rng = random.Random(random_seed)
        indirect_effects: List[float] = []

        # Ma trận chuẩn bị sẵn
        indices = list(range(n))

        for _ in range(num_samples):
            boot_idx = [rng.choice(indices) for _ in range(n)]
            bx = [x[i] for i in boot_idx]
            bm = [m[i] for i in boot_idx]
            by = [y[i] for i in boot_idx]

            # 1. Slope a: M ~ X
            mean_bx = sum(bx) / n
            mean_bm = sum(bm) / n
            ss_xx = sum((bxi - mean_bx) ** 2 for bxi in bx)
            ss_xm = sum((bxi - mean_bx) * (bmi - mean_bm) for bxi, bmi in zip(bx, bm))
            if ss_xx < 1e-12:
                continue
            slope_a = ss_xm / ss_xx

            # 2. Slope b: Y ~ X + M
            # Tính OLS b2 (slope của M trong mô hình Y ~ X + M)
            mean_by = sum(by) / n
            ss_mm = sum((bmi - mean_bm) ** 2 for bmi in bm)
            ss_xy = sum((bxi - mean_bx) * (byi - mean_by) for bxi, byi in zip(bx, by))
            ss_my = sum((bmi - mean_bm) * (byi - mean_by) for bmi, byi in zip(bm, by))

            denom = ss_xx * ss_mm - (ss_xm ** 2)
            if abs(denom) < 1e-12:
                continue

            # Hệ số b2 (cho biến M)
            slope_b = (ss_xx * ss_my - ss_xm * ss_xy) / denom
            indirect_effects.append(slope_a * slope_b)

        if not indirect_effects:
            return {
                "bootstrap_samples": 0,
                "indirect_mean": 0.0,
                "se_boot": 0.0,
                "ci_lower": 0.0,
                "ci_upper": 0.0,
                "is_significant": False
            }

        indirect_effects.sort()
        count = len(indirect_effects)
        mean_boot = sum(indirect_effects) / count
        var_boot = sum((val - mean_boot) ** 2 for val in indirect_effects) / (count - 1) if count > 1 else 0.0
        se_boot = math.sqrt(var_boot)

        # Phân vị 2.5% và 97.5% cho khoảng tin cậy 95%
        idx_lower = int(round(0.025 * count))
        idx_upper = int(round(0.975 * count))
        idx_lower = max(0, min(count - 1, idx_lower))
        idx_upper = max(0, min(count - 1, idx_upper))

        ci_lower = indirect_effects[idx_lower]
        ci_upper = indirect_effects[idx_upper]

        # Không chứa số 0 -> có ý nghĩa thống kê ở mức alpha = 0.05
        is_significant = (ci_lower > 0 and ci_upper > 0) or (ci_lower < 0 and ci_upper < 0)

        return {
            "bootstrap_samples": count,
            "indirect_mean": round(mean_boot, 4),
            "se_boot": round(se_boot, 4),
            "ci_lower": round(ci_lower, 4),
            "ci_upper": round(ci_upper, 4),
            "is_significant": is_significant
        }

    @classmethod
    def analyze_mediation(
        cls,
        x_data: List[float],
        m_data: List[float],
        y_data: List[float],
        x_label: str = "Biến độc lập (X)",
        m_label: str = "Biến trung gian (M)",
        y_label: str = "Biến phụ thuộc (Y)",
        bootstrap_samples: int = 1000
    ) -> Dict[str, Any]:
        """
        Thực hiện toàn diện quy trình kiểm định tác động trung gian 4 bước của Baron & Kenny (1986)
        kết hợp kiểm định Sobel (1982), kiểm định Bootstrap Preacher & Hayes (2008), và tính chỉ số VAF (Hair et al., 2017).
        """
        n = len(x_data)
        if n != len(m_data) or n != len(y_data):
            return {
                "status": "ERROR",
                "message": f"Số lượng quan sát không đồng nhất: X={len(x_data)}, M={len(m_data)}, Y={len(y_data)}."
            }

        if n < 10:
            return {
                "status": "ERROR",
                "message": f"Cần tối thiểu N >= 10 quan sát để phân tích tác động trung gian (hiện có N={n})."
            }

        # -------------------------------------------------------------
        # Bước 1: Mô hình tổng thể (Total Effect): Y ~ X (Path c)
        # -------------------------------------------------------------
        fit_c = cls.fit_simple_regression(x_data, y_data)
        if fit_c.get("status") != "OK":
            return {"status": "ERROR", "message": f"Không thể ước lượng Path c: {fit_c.get('status')}"}

        c_coeff = fit_c["slope"]
        c_se = fit_c["se"]
        c_t = fit_c["t_stat"]
        c_p = fit_c["p_value"]
        c_std_beta = fit_c["std_beta"]
        r2_step1 = fit_c["r_squared"]

        # -------------------------------------------------------------
        # Bước 2: Mô hình dự báo trung gian: M ~ X (Path a)
        # -------------------------------------------------------------
        fit_a = cls.fit_simple_regression(x_data, m_data)
        if fit_a.get("status") != "OK":
            return {"status": "ERROR", "message": f"Không thể ước lượng Path a: {fit_a.get('status')}"}

        a_coeff = fit_a["slope"]
        a_se = fit_a["se"]
        a_t = fit_a["t_stat"]
        a_p = fit_a["p_value"]
        a_std_beta = fit_a["std_beta"]
        r2_step2 = fit_a["r_squared"]

        # -------------------------------------------------------------
        # Bước 3 & 4: Mô hình đồng thời: Y ~ X + M (Path c' và Path b)
        # -------------------------------------------------------------
        fit_mult = cls.fit_multiple_regression_2pred(x_data, m_data, y_data)
        if fit_mult.get("status") not in ["OK", "SUCCESS"]:
            return {"status": "ERROR", "message": f"Không thể ước lượng mô hình đa biến Y ~ X + M: {fit_mult.get('message', '')}"}

        coef_dict = {item.get("label", item.get("variable", "")): item for item in fit_mult.get("coefficients", [])}
        coef_x = coef_dict.get("pred_x1", {})
        coef_m = coef_dict.get("pred_x2", {})

        c_prime_coeff = coef_x.get("b_unstandardized", coef_x.get("unstandardized_B", 0.0))
        c_prime_se = coef_x.get("std_error", 0.0)
        c_prime_t = coef_x.get("t_stat", 0.0)
        c_prime_p = coef_x.get("p_value", 1.0)
        c_prime_std_beta = coef_x.get("beta_standardized", coef_x.get("standardized_Beta", 0.0))

        b_coeff = coef_m.get("b_unstandardized", coef_m.get("unstandardized_B", 0.0))
        b_se = coef_m.get("std_error", 0.0)
        b_t = coef_m.get("t_stat", 0.0)
        b_p = coef_m.get("p_value", 1.0)
        b_std_beta = coef_m.get("beta_standardized", coef_m.get("standardized_Beta", 0.0))

        r2_step3 = fit_mult.get("model_summary", {}).get("r_squared", 0.0)
        delta_r2 = round(max(0.0, r2_step3 - r2_step1), 4)

        # -------------------------------------------------------------
        # Tính toán Tác động Gián tiếp (Indirect Effect = a * b)
        # -------------------------------------------------------------
        indirect_coeff = round(a_coeff * b_coeff, 4)
        std_indirect_coeff = round(a_std_beta * b_std_beta, 4)

        # -------------------------------------------------------------
        # Kiểm định Sobel Test (1982) & Các biến thể Aroian, Goodman
        # -------------------------------------------------------------
        denom_sobel = math.sqrt((b_coeff ** 2) * (a_se ** 2) + (a_coeff ** 2) * (b_se ** 2)) if (a_se > 0 or b_se > 0) else 0.0
        sobel_z = round(indirect_coeff / denom_sobel, 3) if denom_sobel > 1e-12 else 0.0
        sobel_p = round(cls._sobel_p_value(sobel_z), 5)

        denom_aroian = math.sqrt((b_coeff ** 2) * (a_se ** 2) + (a_coeff ** 2) * (b_se ** 2) + (a_se ** 2) * (b_se ** 2)) if (a_se > 0 or b_se > 0) else 0.0
        aroian_z = round(indirect_coeff / denom_aroian, 3) if denom_aroian > 1e-12 else 0.0
        aroian_p = round(cls._sobel_p_value(aroian_z), 5)

        goodman_val = (b_coeff ** 2) * (a_se ** 2) + (a_coeff ** 2) * (b_se ** 2) - (a_se ** 2) * (b_se ** 2)
        denom_goodman = math.sqrt(max(1e-12, goodman_val)) if goodman_val > 0 else 0.0
        goodman_z = round(indirect_coeff / denom_goodman, 3) if denom_goodman > 1e-12 else 0.0
        goodman_p = round(cls._sobel_p_value(goodman_z), 5)

        # -------------------------------------------------------------
        # Kiểm định Bootstrap 95% Confidence Interval (Hayes 2018)
        # -------------------------------------------------------------
        bootstrap_res = cls.run_bootstrap_indirect_effect(
            x_data, m_data, y_data,
            num_samples=min(2000, max(100, bootstrap_samples))
        )

        # -------------------------------------------------------------
        # Phân loại Tác động Trung gian (Mediation Classification)
        # -------------------------------------------------------------
        # Tiêu chí: Indirect effect có ý nghĩa qua Sobel (p < 0.05) HOẶC Bootstrap CI không chứa 0
        indirect_sig = (sobel_p < 0.05) or bootstrap_res["is_significant"]
        direct_sig = (c_prime_p < 0.05)
        path_a_sig = (a_p < 0.05)
        path_b_sig = (b_p < 0.05)

        # Variance Accounted For (VAF)
        vaf_ratio = (indirect_coeff / c_coeff) if abs(c_coeff) > 1e-12 else 0.0
        vaf_pct = round(max(0.0, min(100.0, vaf_ratio * 100.0)), 2)

        if indirect_sig and path_a_sig and path_b_sig:
            if not direct_sig:
                mediation_type = "FULL_MEDIATION"
                mediation_label_vn = "Trung gian toàn phần (Full / Indirect-Only Mediation)"
                mediation_desc = (
                    f"Biến trung gian '{m_label}' truyền dẫn toàn bộ tác động từ '{x_label}' sang '{y_label}'. "
                    f"Khi có mặt '{m_label}', tác động trực tiếp c' không còn ý nghĩa thống kê (p = {c_prime_p})."
                )
            else:
                product_sign = a_coeff * b_coeff * c_prime_coeff
                if product_sign > 0:
                    mediation_type = "COMPLEMENTARY_PARTIAL_MEDIATION"
                    mediation_label_vn = "Trung gian một phần tương hỗ (Complementary Partial Mediation)"
                    mediation_desc = (
                        f"'{m_label}' đóng vai trò trung gian một phần tương hỗ. Cả tác động gián tiếp (a*b = {indirect_coeff}) "
                        f"và tác động trực tiếp (c' = {c_prime_coeff}) đều có ý nghĩa thống kê và cùng chiều tác động."
                    )
                else:
                    mediation_type = "COMPETITIVE_PARTIAL_MEDIATION"
                    mediation_label_vn = "Trung gian một phần triệt tiêu (Competitive Partial Mediation / Suppressor)"
                    mediation_desc = (
                        f"'{m_label}' đóng vai trò trung gian triệt tiêu (Suppressor). Tác động trực tiếp và gián tiếp có chiều nghịch nhau."
                    )
        elif direct_sig and not indirect_sig:
            mediation_type = "DIRECT_ONLY"
            mediation_label_vn = "Chỉ có tác động trực tiếp (Direct-Only Non-Mediation)"
            mediation_desc = (
                f"'{x_label}' tác động trực tiếp lên '{y_label}' (c' = {c_prime_coeff}, p = {c_prime_p}), "
                f"nhưng không có bằng chứng thống kê về vai trò trung gian của '{m_label}' (Sobel p = {sobel_p})."
            )
        elif not direct_sig and not indirect_sig:
            mediation_type = "NO_EFFECT"
            mediation_label_vn = "Không có tác động (No Effect)"
            mediation_desc = f"Không tìm thấy mối liên hệ có ý nghĩa thống kê giữa '{x_label}', '{m_label}' và '{y_label}'."
        else:
            mediation_type = "INCONCLUSIVE"
            mediation_label_vn = "Tác động chưa hội tụ đủ điều kiện (Inconclusive Mediation)"
            mediation_desc = f"Dữ liệu chưa thỏa mãn đồng thời các giả định của Baron & Kenny (Path a: p={a_p}, Path b: p={b_p})."

        # -------------------------------------------------------------
        # Báo cáo chuẩn học thuật APA 7th Edition
        # -------------------------------------------------------------
        apa_text = (
            f"Kết quả phân tích tác động trung gian (Baron & Kenny, 1986; Hayes, 2018) trên mẫu N = {n} cho thấy:\n"
            f"Tác động tổng thể của {x_label} lên {y_label} có ý nghĩa thống kê (c = {c_coeff}, SE = {c_se}, t = {c_t}, p = {c_p}, R² = {r2_step1}).\n"
            f"Đường dẫn a ({x_label} → {m_label}) đạt mức ý nghĩa (a = {a_coeff}, SE = {a_se}, t = {a_t}, p = {a_p}, R² = {r2_step2}).\n"
            f"Khi kiểm soát {x_label}, đường dẫn b ({m_label} → {y_label}) đạt ý nghĩa (b = {b_coeff}, SE = {b_se}, t = {b_t}, p = {b_p}).\n"
            f"Tác động trực tiếp còn lại của {x_label} lên {y_label} là c' = {c_prime_coeff} (SE = {c_prime_se}, t = {c_prime_t}, p = {c_prime_p}).\n"
            f"Tác động gián tiếp a×b = {indirect_coeff} với kiểm định Sobel z = {sobel_z} (p = {sobel_p}) "
            f"và kiểm định Bootstrap {bootstrap_res['bootstrap_samples']} mẫu: 95% CI [{bootstrap_res['ci_lower']}, {bootstrap_res['ci_upper']}]. "
            f"Chỉ số giải thích phương sai VAF = {vaf_pct}%. Kết luận: Mô hình đạt trạng thái {mediation_label_vn}."
        )

        # -------------------------------------------------------------
        # Cấu trúc trực quan hóa sơ đồ đường dẫn (Path Diagram Model)
        # -------------------------------------------------------------
        def format_sig_stars(p: float) -> str:
            if p < 0.001:
                return "***"
            if p < 0.01:
                return "**"
            if p < 0.05:
                return "*"
            return "ns"

        diagram_nodes = [
            {"id": "X", "label": x_label, "role": "predictor", "x": 80, "y": 240},
            {"id": "M", "label": m_label, "role": "mediator", "x": 260, "y": 80},
            {"id": "Y", "label": y_label, "role": "outcome", "x": 440, "y": 240}
        ]

        diagram_paths = [
            {
                "id": "path_a",
                "source": "X",
                "target": "M",
                "coeff": a_coeff,
                "std_beta": a_std_beta,
                "se": a_se,
                "p_value": a_p,
                "stars": format_sig_stars(a_p),
                "is_significant": path_a_sig,
                "label": f"a = {a_coeff} ({format_sig_stars(a_p)})"
            },
            {
                "id": "path_b",
                "source": "M",
                "target": "Y",
                "coeff": b_coeff,
                "std_beta": b_std_beta,
                "se": b_se,
                "p_value": b_p,
                "stars": format_sig_stars(b_p),
                "is_significant": path_b_sig,
                "label": f"b = {b_coeff} ({format_sig_stars(b_p)})"
            },
            {
                "id": "path_c_prime",
                "source": "X",
                "target": "Y",
                "coeff": c_prime_coeff,
                "std_beta": c_prime_std_beta,
                "se": c_prime_se,
                "p_value": c_prime_p,
                "stars": format_sig_stars(c_prime_p),
                "is_significant": direct_sig,
                "label": f"c' = {c_prime_coeff} ({format_sig_stars(c_prime_p)})"
            },
            {
                "id": "path_c_total",
                "source": "X",
                "target": "Y",
                "coeff": c_coeff,
                "std_beta": c_std_beta,
                "se": c_se,
                "p_value": c_p,
                "stars": format_sig_stars(c_p),
                "is_significant": fit_c["p_value"] < 0.05,
                "label": f"c = {c_coeff} ({format_sig_stars(c_p)})"
            }
        ]

        return {
            "status": "OK",
            "sample_size": n,
            "variables": {
                "x": {"label": x_label},
                "m": {"label": m_label},
                "y": {"label": y_label}
            },
            "steps": [
                {
                    "step": 1,
                    "title": "Mô hình tổng thể: Y ~ X (Path c)",
                    "formula": f"{y_label} = c₀ + c · {x_label}",
                    "r_squared": r2_step1,
                    "f_stat": fit_c["f_stat"],
                    "f_p_value": fit_c["f_p_value"],
                    "coefficient": c_coeff,
                    "std_beta": c_std_beta,
                    "se": c_se,
                    "t_stat": c_t,
                    "p_value": c_p,
                    "ci_95": [fit_c["ci_lower"], fit_c["ci_upper"]],
                    "is_significant": fit_c["p_value"] < 0.05
                },
                {
                    "step": 2,
                    "title": "Mô hình tác động lên trung gian: M ~ X (Path a)",
                    "formula": f"{m_label} = a₀ + a · {x_label}",
                    "r_squared": r2_step2,
                    "f_stat": fit_a["f_stat"],
                    "f_p_value": fit_a["f_p_value"],
                    "coefficient": a_coeff,
                    "std_beta": a_std_beta,
                    "se": a_se,
                    "t_stat": a_t,
                    "p_value": a_p,
                    "ci_95": [fit_a["ci_lower"], fit_a["ci_upper"]],
                    "is_significant": path_a_sig
                },
                {
                    "step": 3,
                    "title": "Mô hình đồng thời: Y ~ X + M (Path c' & Path b)",
                    "formula": f"{y_label} = c'₀ + c' · {x_label} + b · {m_label}",
                    "r_squared": r2_step3,
                    "delta_r_squared": delta_r2,
                    "path_c_prime": {
                        "coefficient": c_prime_coeff,
                        "std_beta": c_prime_std_beta,
                        "se": c_prime_se,
                        "t_stat": c_prime_t,
                        "p_value": c_prime_p,
                        "is_significant": direct_sig
                    },
                    "path_b": {
                        "coefficient": b_coeff,
                        "std_beta": b_std_beta,
                        "se": b_se,
                        "t_stat": b_t,
                        "p_value": b_p,
                        "is_significant": path_b_sig
                    }
                }
            ],
            "effects_summary": {
                "total_effect_c": c_coeff,
                "direct_effect_c_prime": c_prime_coeff,
                "indirect_effect_ab": indirect_coeff,
                "std_indirect_effect_ab": std_indirect_coeff,
                "indirect_to_direct_ratio": round(indirect_coeff / c_prime_coeff, 3) if abs(c_prime_coeff) > 1e-12 else None,
                "vaf_percent": vaf_pct
            },
            "significance_tests": {
                "sobel_test": {
                    "z_stat": sobel_z,
                    "p_value": sobel_p,
                    "is_significant": sobel_p < 0.05
                },
                "aroian_test": {
                    "z_stat": aroian_z,
                    "p_value": aroian_p,
                    "is_significant": aroian_p < 0.05
                },
                "goodman_test": {
                    "z_stat": goodman_z,
                    "p_value": goodman_p,
                    "is_significant": goodman_p < 0.05
                },
                "bootstrap_resampling": bootstrap_res
            },
            "conclusion": {
                "mediation_type": mediation_type,
                "mediation_label_vn": mediation_label_vn,
                "description": mediation_desc,
                "apa_narrative": apa_text
            },
            "diagram": {
                "nodes": diagram_nodes,
                "paths": diagram_paths
            }
        }
