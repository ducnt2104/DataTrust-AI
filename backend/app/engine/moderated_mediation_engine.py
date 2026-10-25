"""
Statistical Moderated Mediation & Conditional Indirect Effects Engine (PROCESS Model 7 - Hayes 2015, 2018).

Cơ sở phương pháp luận học thuật:
- Hayes, A. F. (2015). An index and test of linear moderated mediation.
  Multivariate Behavioral Research, 50(1), 1-22.
- Hayes, A. F. (2018). Introduction to Mediation, Moderation, and Conditional Process Analysis:
  A Regression-Based Approach (2nd ed.). Guilford Press. (PROCESS Model 7).
- Preacher, K. J., Rucker, D. D., & Hayes, A. F. (2007). Addressing moderated mediation hypotheses:
  Theory, methods, and prescriptions. Multivariate Behavioral Research, 42(1), 185-227.
- Edwards, J. R., & Lambert, L. S. (2007). Methods for integrating moderation and mediation:
  A general analytical framework using moderated path analysis. Psychological Methods, 12(1), 1-22.
"""

import math
import random
from typing import Dict, Any, List, Optional, Tuple

try:
    from app.engine.regression_engine import RegressionEngine
except ModuleNotFoundError:
    from backend.app.engine.regression_engine import RegressionEngine


class ModeratedMediationEngine:
    """
    Động cơ Phân tích Tác động Trung gian bị Điều tiết (Moderated Mediation - PROCESS Model 7).
    Mô hình hóa:
    Stage 1: M = i_M + a1*X + a2*W + a3*(X*W) + e_M  (Giai đoạn 1 bị điều tiết bởi W)
    Stage 2: Y = i_Y + c'*X + b*M + e_Y              (Giai đoạn 2 tác động lên Y)

    Tác động gián tiếp có điều kiện:
    f(W) = (a1 + a3*W) * b

    Chỉ số Trung gian bị Điều tiết (Index of Moderated Mediation - Hayes 2015):
    omega = a3 * b
    """

    @classmethod
    def analyze_moderated_mediation(
        cls,
        x: List[float],
        m: List[float],
        w: List[float],
        y: List[float],
        center_variables: bool = True,
        num_bootstrap: int = 1000,
        random_seed: int = 42,
        x_label: str = "X",
        m_label: str = "M",
        w_label: str = "W",
        y_label: str = "Y"
    ) -> Dict[str, Any]:
        """
        Thực hiện phân tích Moderated Mediation (PROCESS Model 7).
        """
        n = len(y)
        if n < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 10 phản hồi hoàn chỉnh để phân tích Moderated Mediation (hiện có {n})."
            }

        mean_x = sum(x) / n
        mean_m = sum(m) / n
        mean_w = sum(w) / n
        mean_y = sum(y) / n

        var_x = sum((xi - mean_x) ** 2 for xi in x) / (n - 1)
        var_m = sum((mi - mean_m) ** 2 for mi in m) / (n - 1)
        var_w = sum((wi - mean_w) ** 2 for wi in w) / (n - 1)
        var_y = sum((yi - mean_y) ** 2 for yi in y) / (n - 1)

        if var_x < 1e-7 or var_m < 1e-7 or var_w < 1e-7 or var_y < 1e-7:
            return {
                "status": "ZERO_VARIANCE",
                "message": "Một hoặc nhiều biến có phương sai bằng 0 (dữ liệu hằng số)."
            }

        std_x = math.sqrt(var_x)
        std_m = math.sqrt(var_m)
        std_w = math.sqrt(var_w)
        std_y = math.sqrt(var_y)

        # 1. Mean-centering cho X và W trong Stage 1
        if center_variables:
            x_c = [xi - mean_x for xi in x]
            w_c = [wi - mean_w for wi in w]
        else:
            x_c = list(x)
            w_c = list(w)

        xw_inter = [x_c[i] * w_c[i] for i in range(n)]

        # 2. Stage 1: Hồi quy M ~ X + W + X*W
        X_mat_stage1 = [[x_c[i], w_c[i], xw_inter[i]] for i in range(n)]
        fit_stage1 = RegressionEngine.fit_ols(
            X_matrix=X_mat_stage1,
            y_vector=m,
            predictor_labels=["X", "W", "X*W"],
            predictor_titles=[x_label, w_label, f"{x_label} * {w_label}"],
            dependent_title=m_label
        )

        coeffs_s1 = fit_stage1.get("coefficients", [])
        a0 = coeffs_s1[0]["b_unstandardized"] if len(coeffs_s1) > 0 else 0.0
        a1 = coeffs_s1[1]["b_unstandardized"] if len(coeffs_s1) > 1 else 0.0
        a2 = coeffs_s1[2]["b_unstandardized"] if len(coeffs_s1) > 2 else 0.0
        a3 = coeffs_s1[3]["b_unstandardized"] if len(coeffs_s1) > 3 else 0.0

        r2_stage1 = fit_stage1.get("model_summary", {}).get("r_squared", 0.0)
        f_stage1 = fit_stage1.get("anova_table", {}).get("f_statistic", 0.0)
        p_stage1 = fit_stage1.get("anova_table", {}).get("p_value", 1.0)

        # 3. Stage 2: Hồi quy Y ~ X + M
        X_mat_stage2 = [[x[i], m[i]] for i in range(n)]
        fit_stage2 = RegressionEngine.fit_ols(
            X_matrix=X_mat_stage2,
            y_vector=y,
            predictor_labels=["X", "M"],
            predictor_titles=[x_label, m_label],
            dependent_title=y_label
        )

        coeffs_s2 = fit_stage2.get("coefficients", [])
        c0 = coeffs_s2[0]["b_unstandardized"] if len(coeffs_s2) > 0 else 0.0
        c_prime = coeffs_s2[1]["b_unstandardized"] if len(coeffs_s2) > 1 else 0.0
        b = coeffs_s2[2]["b_unstandardized"] if len(coeffs_s2) > 2 else 0.0

        r2_stage2 = fit_stage2.get("model_summary", {}).get("r_squared", 0.0)
        f_stage2 = fit_stage2.get("anova_table", {}).get("f_statistic", 0.0)
        p_stage2 = fit_stage2.get("anova_table", {}).get("p_value", 1.0)

        # 4. Chỉ số Trung gian bị Điều tiết (Index of Moderated Mediation - Hayes 2015)
        # omega = a3 * b
        index_omega = a3 * b

        # 5. Tác động gián tiếp có điều kiện tại 3 mức của W (Pick-a-Point)
        w_levels = [
            {
                "level": "LOW",
                "label": f"Thấp (-1 SD: {mean_w - std_w:.2f})",
                "w_val_c": -std_w if center_variables else mean_w - std_w,
                "w_val_raw": mean_w - std_w
            },
            {
                "level": "MEAN",
                "label": f"Trung bình (Mean: {mean_w:.2f})",
                "w_val_c": 0.0 if center_variables else mean_w,
                "w_val_raw": mean_w
            },
            {
                "level": "HIGH",
                "label": f"Cao (+1 SD: {mean_w + std_w:.2f})",
                "w_val_c": std_w if center_variables else mean_w + std_w,
                "w_val_raw": mean_w + std_w
            }
        ]

        point_effects = []
        for wl in w_levels:
            wc = wl["w_val_c"]
            cond_a = a1 + a3 * wc
            cond_indirect = cond_a * b
            point_effects.append({
                "level": wl["level"],
                "label": wl["label"],
                "w_value": round(wl["w_val_raw"], 3),
                "conditional_a": round(cond_a, 4),
                "b_path": round(b, 4),
                "indirect_effect": round(cond_indirect, 4)
            })

        # 6. Bootstrap Resampling (1000 mẫu) ước lượng khoảng tin cậy 95%
        rng = random.Random(random_seed)
        boot_omegas: List[float] = []
        boot_cond_indirects: Dict[str, List[float]] = {
            "LOW": [],
            "MEAN": [],
            "HIGH": []
        }

        indices = list(range(n))
        for _ in range(num_bootstrap):
            b_idx = [rng.choice(indices) for _ in range(n)]
            bx = [x[i] for i in b_idx]
            bm = [m[i] for i in b_idx]
            bw = [w[i] for i in b_idx]
            by = [y[i] for i in b_idx]

            # Stage 1 bootstrap
            if center_variables:
                bm_x = sum(bx) / n
                bm_w = sum(bw) / n
                bx_c = [xi - bm_x for xi in bx]
                bw_c = [wi - bm_w for wi in bw]
            else:
                bx_c = bx
                bw_c = bw

            bxw = [bx_c[i] * bw_c[i] for i in range(n)]
            bX1 = [[bx_c[i], bw_c[i], bxw[i]] for i in range(n)]
            fit_b1 = RegressionEngine.fit_ols(
                X_matrix=bX1, y_vector=bm,
                predictor_labels=["X", "W", "X*W"],
                predictor_titles=["X", "W", "X*W"],
                dependent_title="M"
            )
            c1 = fit_b1.get("coefficients", [])
            if len(c1) < 4:
                continue
            ba1 = c1[1]["b_unstandardized"]
            ba3 = c1[3]["b_unstandardized"]

            # Stage 2 bootstrap
            bX2 = [[bx[i], bm[i]] for i in range(n)]
            fit_b2 = RegressionEngine.fit_ols(
                X_matrix=bX2, y_vector=by,
                predictor_labels=["X", "M"],
                predictor_titles=["X", "M"],
                dependent_title="Y"
            )
            c2 = fit_b2.get("coefficients", [])
            if len(c2) < 3:
                continue
            bb = c2[2]["b_unstandardized"]

            # Lưu omega
            b_omega = ba3 * bb
            boot_omegas.append(b_omega)

            # Lưu conditional indirect
            for wl in w_levels:
                b_cond_a = ba1 + ba3 * wl["w_val_c"]
                boot_cond_indirects[wl["level"]].append(b_cond_a * bb)

        # Tính toán phân vị 95% CI
        def calc_ci(vals: List[float]) -> Tuple[float, float, float, bool]:
            if not vals:
                return 0.0, 0.0, 0.0, False
            vals.sort()
            mean_v = sum(vals) / len(vals)
            se_v = math.sqrt(sum((v - mean_v) ** 2 for v in vals) / (len(vals) - 1)) if len(vals) > 1 else 0.0
            low_idx = int(0.025 * len(vals))
            high_idx = int(0.975 * len(vals))
            ci_l = vals[min(low_idx, len(vals) - 1)]
            ci_u = vals[min(high_idx, len(vals) - 1)]
            is_sig = (ci_l > 0.0 and ci_u > 0.0) or (ci_l < 0.0 and ci_u < 0.0)
            return round(se_v, 4), round(ci_l, 4), round(ci_u, 4), is_sig

        omega_se, omega_ci_low, omega_ci_up, omega_sig = calc_ci(boot_omegas)

        conditional_results = []
        for pe in point_effects:
            lvl = pe["level"]
            b_vals = boot_cond_indirects[lvl]
            se_val, ci_l, ci_u, sig = calc_ci(b_vals)
            conditional_results.append({
                **pe,
                "bootstrap_se": se_val,
                "boot_ci_95_lower": ci_l,
                "boot_ci_95_upper": ci_u,
                "is_significant": sig
            })

        # 7. Đoạn trích APA 7th Edition
        apa_narrative = (
            f"Phân tích tác động trung gian bị điều tiết (Moderated Mediation Analysis - PROCESS Model 7; Hayes 2018) "
            f"được tiến hành nhằm kiểm định xem tác động gián tiếp của {x_label} lên {y_label} qua biến trung gian {m_label} "
            f"có thay đổi theo các mức độ khác nhau của biến điều tiết {w_label} hay không. "
            f"Dữ liệu ước lượng qua {len(boot_omegas)} mẫu tái lấy mẫu Bootstrap phi tham số (95% CI). "
            f"Chỉ số trung gian bị điều tiết (Index of Moderated Mediation; Hayes 2015) đạt omega = {index_omega:.4f} "
            f"(BootSE = {omega_se:.4f}, 95% BootCI [{omega_ci_low:.4f}, {omega_ci_up:.4f}]). "
            + (
                f"Khoảng tin cậy Bootstrap 95% không bao hàm giá trị 0, xác nhận tác động trung gian bị điều tiết có ý nghĩa thống kê. "
                f"Cụ thể, tác động gián tiếp của {x_label} lên {y_label} qua {m_label} đạt giá trị "
                f"b = {conditional_results[0]['indirect_effect']:.4f} (95% CI [{conditional_results[0]['boot_ci_95_lower']}, {conditional_results[0]['boot_ci_95_upper']}]) khi {w_label} ở mức thấp, "
                f"và tăng lên b = {conditional_results[2]['indirect_effect']:.4f} (95% CI [{conditional_results[2]['boot_ci_95_lower']}, {conditional_results[2]['boot_ci_95_upper']}]) khi {w_label} ở mức cao."
                if omega_sig
                else "Khoảng tin cậy Bootstrap 95% chứa giá trị 0, cho thấy không có bằng chứng thống kê vững chắc về tác động trung gian bị điều tiết."
            )
        )

        return {
            "status": "SUCCESS",
            "sample_size": n,
            "bootstrap_samples_executed": len(boot_omegas),
            "center_variables": center_variables,
            "variables": {
                "independent_x": {"title": x_label, "mean": round(mean_x, 3), "std": round(std_x, 3)},
                "mediator_m": {"title": m_label, "mean": round(mean_m, 3), "std": round(std_m, 3)},
                "moderator_w": {"title": w_label, "mean": round(mean_w, 3), "std": round(std_w, 3)},
                "dependent_y": {"title": y_label, "mean": round(mean_y, 3), "std": round(std_y, 3)}
            },
            "stage1_mediator_model": {
                "formula": f"{m_label} = a0 + a1*{x_label} + a2*{w_label} + a3*({x_label}*{w_label})",
                "r_squared": round(r2_stage1, 4),
                "f_stat": round(f_stage1, 3),
                "p_value": round(p_stage1, 4),
                "coefficients": {
                    "intercept_a0": round(a0, 4),
                    "path_a1_X": round(a1, 4),
                    "path_a2_W": round(a2, 4),
                    "interaction_a3_XW": round(a3, 4)
                }
            },
            "stage2_dependent_model": {
                "formula": f"{y_label} = c0 + c'*({x_label}) + b*({m_label})",
                "r_squared": round(r2_stage2, 4),
                "f_stat": round(f_stage2, 3),
                "p_value": round(p_stage2, 4),
                "coefficients": {
                    "intercept_c0": round(c0, 4),
                    "direct_path_c_prime": round(c_prime, 4),
                    "mediator_path_b": round(b, 4)
                }
            },
            "index_of_moderated_mediation": {
                "index_omega": round(index_omega, 4),
                "bootstrap_se": omega_se,
                "boot_ci_95_lower": omega_ci_low,
                "boot_ci_95_upper": omega_ci_up,
                "is_significant": omega_sig,
                "verdict_badge": "TRUNG GIAN BỊ ĐIỀU TIẾT CÓ Ý NGHĨA" if omega_sig else "KHÔNG BỊ ĐIỀU TIẾT"
            },
            "conditional_indirect_effects": conditional_results,
            "apa_narrative": apa_narrative
        }
