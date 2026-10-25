"""
Causal Mediation Analysis with Sensitivity Analysis for Unmeasured Confounding Engine.
Based on the groundbreaking econometric and statistical methodology by:
- Imai, Keele, & Tingley (2010), "A General Approach to Causal Mediation Analysis", Psychological Methods, 15(4), 309-334.
- Imai, Keele, & Yamamoto (2010), "Identification, Inference and Sensitivity Analysis for Causal Mediation Effects", Statistical Science, 25(1), 51-71.
- Tingley, Yamamoto, Hirose, Keele, & Imai (2014), "mediation: R Package for Causal Mediation Analysis", Journal of Statistical Software, 59(5).
"""

from typing import Dict, List, Any, Optional
import math
import numpy as np


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _ols_fit(X: np.ndarray, y: np.ndarray):
    """
    Fit OLS regression y = X beta + e.
    Returns: beta, se, residuals, sigma_sq, r_sq
    """
    n, p = X.shape
    xtx = X.T @ X
    # Add small ridge if near singular
    if np.linalg.matrix_rank(xtx) < p:
        xtx += 1e-7 * np.eye(p)
    inv_xtx = np.linalg.inv(xtx)
    beta = inv_xtx @ (X.T @ y)
    residuals = y - X @ beta
    dof = max(1, n - p)
    sigma_sq = float(np.sum(residuals ** 2) / dof)
    cov_beta = sigma_sq * inv_xtx
    se = np.sqrt(np.maximum(1e-12, np.diag(cov_beta)))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    ss_res = float(np.sum(residuals ** 2))
    r_sq = float(1.0 - (ss_res / ss_tot)) if ss_tot > 1e-12 else 0.0
    return beta, se, residuals, sigma_sq, r_sq, inv_xtx


def run_causal_mediation_sensitivity(
    records: List[Dict[str, Any]],
    treatment_col: str,
    mediator_col: str,
    outcome_col: str,
    covariate_cols: Optional[List[str]] = None,
    target_treatment_val: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Executes Causal Mediation Analysis with unmeasured confounding sensitivity analysis.
    """
    covariates = covariate_cols or []
    valid_rows = []

    for r in records:
        t_raw = r.get(treatment_col)
        m_raw = r.get(mediator_col)
        y_raw = r.get(outcome_col)

        if t_raw is None or m_raw is None or y_raw is None:
            continue

        try:
            m_val = float(m_raw)
            y_val = float(y_raw)
        except (ValueError, TypeError):
            continue

        # Treatment binary coding (0 or 1)
        if target_treatment_val is not None:
            t_val = 1.0 if str(t_raw).strip() == str(target_treatment_val).strip() else 0.0
        else:
            try:
                t_num = float(t_raw)
                t_val = 1.0 if t_num > 0.5 else 0.0
            except (ValueError, TypeError):
                # String comparison
                t_str = str(t_raw).strip().lower()
                t_val = 1.0 if t_str in ["1", "true", "yes", "treatment", "treated"] else 0.0

        # Covariates
        cov_vals = []
        valid_cov = True
        for c in covariates:
            c_raw = r.get(c)
            if c_raw is None:
                valid_cov = False
                break
            try:
                cov_vals.append(float(c_raw))
            except (ValueError, TypeError):
                valid_cov = False
                break

        if not valid_cov:
            continue

        valid_rows.append((t_val, m_val, y_val, cov_vals))

    n_sample = len(valid_rows)
    if n_sample < 20:
        return {
            "status": "error",
            "message": f"Số lượng mẫu hợp lệ sau tiền xử lý (N={n_sample}) không đủ để ước lượng kiểm định độ nhạy trung gian nhân quả (cần tối thiểu N >= 20)."
        }

    T = np.array([row[0] for row in valid_rows], dtype=float)
    M = np.array([row[1] for row in valid_rows], dtype=float)
    Y = np.array([row[2] for row in valid_rows], dtype=float)

    n_treated = int(np.sum(T == 1.0))
    n_control = int(np.sum(T == 0.0))

    if n_treated < 3 or n_control < 3:
        return {
            "status": "error",
            "message": f"Biến can thiệp thiếu phân bổ nhóm hợp lệ (Treated={n_treated}, Control={n_control}; mỗi nhóm cần tối thiểu 3 quan sát)."
        }

    # Covariate matrix
    if len(covariates) > 0:
        C = np.array([row[3] for row in valid_rows], dtype=float)
    else:
        C = np.empty((n_sample, 0), dtype=float)

    # 1. Mediator Model: M = alpha_0 + alpha_T * T + X * alpha_X + e_M
    X_M = np.column_stack([np.ones(n_sample), T, C]) if C.shape[1] > 0 else np.column_stack([np.ones(n_sample), T])
    beta_m_model, se_m_model, e_M, sigma_sq_M, r_sq_M, _ = _ols_fit(X_M, M)

    alpha_T = float(beta_m_model[1])
    se_alpha_T = float(se_m_model[1])
    z_alpha_T = alpha_T / max(1e-9, se_alpha_T)
    p_alpha_T = float(2.0 * (1.0 - _normal_cdf(abs(z_alpha_T))))

    sigma_M = math.sqrt(max(1e-9, sigma_sq_M))

    # 2. Outcome Model: Y = beta_0 + beta_T * T + beta_M * M + X * beta_X + e_Y
    X_Y = np.column_stack([np.ones(n_sample), T, M, C]) if C.shape[1] > 0 else np.column_stack([np.ones(n_sample), T, M])
    beta_y_model, se_y_model, e_Y, sigma_sq_Y, r_sq_Y, _ = _ols_fit(X_Y, Y)

    beta_T = float(beta_y_model[1])      # Direct effect
    se_beta_T = float(se_y_model[1])
    z_beta_T = beta_T / max(1e-9, se_beta_T)
    p_beta_T = float(2.0 * (1.0 - _normal_cdf(abs(z_beta_T))))

    beta_M = float(beta_y_model[2])      # Mediator effect on outcome
    se_beta_M = float(se_y_model[2])
    z_beta_M = beta_M / max(1e-9, se_beta_M)
    p_beta_M = float(2.0 * (1.0 - _normal_cdf(abs(z_beta_M))))

    sigma_Y = math.sqrt(max(1e-9, sigma_sq_Y))

    # 3. Baseline Mediation Parameters (rho = 0, Sequential Ignorability)
    acme_baseline = float(alpha_T * beta_M)
    ade_baseline = float(beta_T)
    total_effect = float(acme_baseline + ade_baseline)

    # Sobel / Delta Method SE for ACME
    se_acme = float(math.sqrt(alpha_T**2 * se_beta_M**2 + beta_M**2 * se_alpha_T**2))
    z_acme = acme_baseline / max(1e-9, se_acme)
    p_acme = float(2.0 * (1.0 - _normal_cdf(abs(z_acme))))
    ci_acme_lower = float(acme_baseline - 1.96 * se_acme)
    ci_acme_upper = float(acme_baseline + 1.96 * se_acme)

    prop_mediated = float(acme_baseline / total_effect) if abs(total_effect) > 1e-6 else 0.0

    # 4. Sensitivity Analysis (Imai, Keele, Tingley 2010):
    # Closed-form exact threshold rho_tilde where delta(rho) = 0:
    # beta_M = rho * sigma_Y / (sigma_M * sqrt(1 - rho^2))
    # => rho_tilde = (beta_M * sigma_M) / sqrt(sigma_Y^2 + beta_M^2 * sigma_M^2)
    denom_threshold = math.sqrt(sigma_Y**2 + (beta_M**2 * sigma_M**2))
    rho_tilde = float((beta_M * sigma_M) / denom_threshold) if denom_threshold > 1e-9 else 0.0
    r2_star_product = float(rho_tilde ** 2)

    # Robustness Classification
    abs_rho = abs(rho_tilde)
    if abs_rho >= 0.35:
        robustness_level = "HIGHLY_ROBUST"
        robustness_badge = "Vững chắc cao trước nhiễu tiềm ẩn"
        robustness_desc = (
            f"Kết luận trung gian rất vững chắc. Tương quan sai số do nhiễu chưa quan sát (|rho|={abs_rho:.3f} >= 0.35) "
            "phải rất lớn mới có thể triệt tiêu hoàn toàn hiệu ứng trung gian nhân quả ACME."
        )
    elif abs_rho >= 0.15:
        robustness_level = "MODERATELY_ROBUST"
        robustness_badge = "Vững chắc trung bình"
        robustness_desc = (
            f"Kết luận trung gian có độ nhạy vừa phải (|rho|={abs_rho:.3f}). "
            "Một yếu tố nhiễu đồng thời giải thích khoảng trung bình biến thiên dư thừa có thể làm đảo chiều kết luận."
        )
    else:
        robustness_level = "FRAGILE_TO_CONFOUNDING"
        robustness_badge = "Nhạy cảm cao với nhiễu tiềm ẩn (Dễ tổn thương)"
        robustness_desc = (
            f"Kết luận trung gian rất nhạy cảm (|rho|={abs_rho:.3f} < 0.15). "
            "Chỉ cần một yếu tố nhiễu thứ ba không quan sát có tương quan nhỏ giữa biến trung gian và kết quả là đủ làm hiệu ứng ACME suy giảm về 0."
        )

    # Sensitivity Curve Grid Evaluation
    rho_grid_points = [-0.8, -0.6, -0.4, -0.2, -0.1, 0.0, 0.1, 0.2, 0.4, 0.6, 0.8]
    sensitivity_curve = []

    for r_val in rho_grid_points:
        if abs(r_val) >= 0.999:
            continue
        # delta(rho) = alpha_T * (beta_M - rho * sigma_Y / (sigma_M * sqrt(1 - rho^2)))
        bias_factor = (r_val * sigma_Y) / (sigma_M * math.sqrt(1.0 - r_val**2))
        acme_rho = float(alpha_T * (beta_M - bias_factor))
        # Variance approximation
        se_rho = float(math.sqrt((beta_M - bias_factor)**2 * se_alpha_T**2 + alpha_T**2 * se_beta_M**2))
        ci_low = float(acme_rho - 1.96 * se_rho)
        ci_high = float(acme_rho + 1.96 * se_rho)
        sensitivity_curve.append({
            "rho": round(r_val, 2),
            "acme": round(acme_rho, 4),
            "se": round(se_rho, 4),
            "ci_lower": round(ci_low, 4),
            "ci_upper": round(ci_high, 4),
            "is_zero_in_ci": bool(ci_low <= 0.0 <= ci_high)
        })

    # 5. Generate Dual-Panel Vector SVG
    svg_chart = _generate_causal_mediation_svg(
        alpha_T=alpha_T,
        se_alpha_T=se_alpha_T,
        p_alpha_T=p_alpha_T,
        beta_M=beta_M,
        se_beta_M=se_beta_M,
        p_beta_M=p_beta_M,
        beta_T=beta_T,
        se_beta_T=se_beta_T,
        p_beta_T=p_beta_T,
        acme_baseline=acme_baseline,
        rho_tilde=rho_tilde,
        sensitivity_curve=sensitivity_curve,
        treatment_name=treatment_col,
        mediator_name=mediator_col,
        outcome_name=outcome_col
    )

    # 6. APA 7th Edition Narrative
    apa_narrative = (
        f"Phân tích trung gian nhân quả và kiểm định độ nhạy theo khung phương pháp luận Imai, Keele, và Tingley (2010) "
        f"được tiến hành trên cỡ mẫu N = {n_sample} người tham gia (Can thiệp: n = {n_treated}, Đối chứng: n = {n_control}). "
        f"Dưới giả định tuần tự bỏ qua (Sequential Ignorability, rho = 0), hiệu ứng trung gian nhân quả trung bình (ACME) "
        f"được ước lượng đạt delta = {acme_baseline:.4f} (SE = {se_acme:.4f}, 95% CI [{ci_acme_lower:.4f}, {ci_acme_upper:.4f}], "
        f"z = {z_acme:.3f}, p = {p_acme:.4f}), đóng góp {prop_mediated * 100:.1f}% vào tổng hiệu ứng can thiệp (Total Effect tau = {total_effect:.4f}). "
        f"Hiệu ứng can thiệp trực tiếp (ADE) ước lượng đạt zeta = {ade_baseline:.4f} (SE = {se_beta_T:.4f}, p = {p_beta_T:.4f}). "
        f"Kiểm định độ nhạy đối với nhiễu tiềm ẩn không quan sát chỉ ra rằng ngưỡng tương quan sai số triệt tiêu hiệu ứng trung gian "
        f"là rho* = {rho_tilde:.4f} (tương đương tích phương sai giải thích dư thừa R*2_M * R*2_Y = {r2_star_product:.4f}). "
        f"Mức độ vững chắc của kết luận nghiên cứu được xếp hạng: {robustness_badge}. {robustness_desc}"
    )

    return {
        "status": "success",
        "treatment_field": treatment_col,
        "mediator_field": mediator_col,
        "outcome_field": outcome_col,
        "covariate_fields": covariates,
        "sample_diagnostics": {
            "n_total": n_sample,
            "n_treated": n_treated,
            "n_control": n_control,
            "mean_mediator": round(float(np.mean(M)), 4),
            "sd_mediator": round(sigma_M, 4),
            "mean_outcome": round(float(np.mean(Y)), 4),
            "sd_outcome": round(sigma_Y, 4),
            "r_squared_mediator_model": round(r_sq_M, 4),
            "r_squared_outcome_model": round(r_sq_Y, 4)
        },
        "path_estimates": {
            "path_a": {
                "coefficient": round(alpha_T, 4),
                "se": round(se_alpha_T, 4),
                "z_stat": round(z_alpha_T, 3),
                "p_value": round(p_alpha_T, 4),
                "is_significant": bool(p_alpha_T < 0.05)
            },
            "path_b": {
                "coefficient": round(beta_M, 4),
                "se": round(se_beta_M, 4),
                "z_stat": round(z_beta_M, 3),
                "p_value": round(p_beta_M, 4),
                "is_significant": bool(p_beta_M < 0.05)
            },
            "path_c_prime": {
                "coefficient": round(beta_T, 4),
                "se": round(se_beta_T, 4),
                "z_stat": round(z_beta_T, 3),
                "p_value": round(p_beta_T, 4),
                "is_significant": bool(p_beta_T < 0.05)
            }
        },
        "baseline_effects": {
            "acme": round(acme_baseline, 4),
            "se_acme": round(se_acme, 4),
            "ci_95_lower": round(ci_acme_lower, 4),
            "ci_95_upper": round(ci_acme_upper, 4),
            "z_stat": round(z_acme, 3),
            "p_value": round(p_acme, 4),
            "is_significant": bool(p_acme < 0.05),
            "ade": round(ade_baseline, 4),
            "se_ade": round(se_beta_T, 4),
            "p_ade": round(p_beta_T, 4),
            "total_effect": round(total_effect, 4),
            "proportion_mediated": round(prop_mediated, 4)
        },
        "sensitivity_analysis": {
            "critical_rho_threshold": round(rho_tilde, 4),
            "r2_star_product": round(r2_star_product, 4),
            "robustness_level": robustness_level,
            "robustness_badge": robustness_badge,
            "robustness_description": robustness_desc,
            "sensitivity_curve": sensitivity_curve
        },
        "svg_chart": svg_chart,
        "apa_narrative": apa_narrative
    }


def _generate_causal_mediation_svg(
    alpha_T: float,
    se_alpha_T: float,
    p_alpha_T: float,
    beta_M: float,
    se_beta_M: float,
    p_beta_M: float,
    beta_T: float,
    se_beta_T: float,
    p_beta_T: float,
    acme_baseline: float,
    rho_tilde: float,
    sensitivity_curve: List[Dict[str, Any]],
    treatment_name: str,
    mediator_name: str,
    outcome_name: str
) -> str:
    """
    Renders high-definition dual-panel vector SVG:
    Panel A: Causal Path Diagram with unobserved confounding correlation arc rho
    Panel B: ACME Sensitivity Contour Plot with 95% CI ribbon and threshold rho*
    """
    width = 840
    height = 370

    # Panel A coordinates
    # T at (80, 250), M at (210, 90), Y at (340, 250)
    tx, ty = 85, 240
    mx, my = 210, 85
    yx, yy = 335, 240

    def sig_stars(p: float) -> str:
        if p < 0.001:
            return "***"
        if p < 0.01:
            return "**"
        if p < 0.05:
            return "*"
        return "ns"

    p_a_str = f"a = {alpha_T:.3f}{sig_stars(p_alpha_T)}"
    p_b_str = f"b = {beta_M:.3f}{sig_stars(p_beta_M)}"
    p_c_str = f"c' = {beta_T:.3f}{sig_stars(p_beta_T)}"

    # Panel B coordinates
    # Box from x=450 to 800, y=60 to 300
    bx0, bx1 = 450, 805
    by0, by1 = 60, 290
    b_width = bx1 - bx0
    b_height = by1 - by0

    # Determine y scale for ACME
    all_y = [pt["ci_lower"] for pt in sensitivity_curve] + [pt["ci_upper"] for pt in sensitivity_curve] + [0.0, acme_baseline]
    min_y = min(all_y)
    max_y = max(all_y)
    # Add padding
    y_range = max(1e-4, max_y - min_y)
    min_y -= 0.1 * y_range
    max_y += 0.1 * y_range
    y_span = max_y - min_y

    def scale_x(rho_val: float) -> float:
        # rho from -0.8 to +0.8
        return bx0 + ((rho_val - (-0.8)) / 1.6) * b_width

    def scale_y(acme_val: float) -> float:
        return by1 - ((acme_val - min_y) / y_span) * b_height

    y_zero = scale_y(0.0)

    # Build polygon for 95% CI ribbon
    pts_upper = []
    pts_lower = []
    pts_line = []

    for pt in sensitivity_curve:
        sx = scale_x(pt["rho"])
        sy_high = scale_y(pt["ci_upper"])
        sy_low = scale_y(pt["ci_lower"])
        sy_mid = scale_y(pt["acme"])
        pts_upper.append(f"{sx:.1f},{sy_high:.1f}")
        pts_lower.insert(0, f"{sx:.1f},{sy_low:.1f}")
        pts_line.append(f"{sx:.1f},{sy_mid:.1f}")

    ribbon_points = " ".join(pts_upper + pts_lower)
    curve_points = " ".join(pts_line)

    # Threshold rho marker
    x_threshold = scale_x(min(0.8, max(-0.8, rho_tilde)))
    x_zero_rho = scale_x(0.0)

    svg_elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="{height}" class="w-full">',
        # Background
        f'<rect width="{width}" height="{height}" fill="#090d16" rx="12" stroke="#1e293b" stroke-width="1.5"/>',

        # Headers
        '<text x="20" y="32" fill="#e2e8f0" font-family="system-ui, sans-serif" font-size="14" font-weight="700">PANEL A: Sơ đồ Đường Nhân Quả & Tương Quan Sai Số (ρ)</text>',
        f'<text x="{bx0}" y="32" fill="#e2e8f0" font-family="system-ui, sans-serif" font-size="14" font-weight="700">PANEL B: Đường Cong Độ Nhạy ACME δ(ρ) (Imai et al. 2010)</text>',

        # Panel A Container & Arrows
        # Path a (T -> M)
        f'<line x1="{tx}" y1="{ty-25}" x2="{mx-25}" y2="{my+20}" stroke="#6366f1" stroke-width="2.5" marker-end="url(#arrow-indigo)"/>',
        f'<rect x="{((tx+mx)/2)-45}" y="{((ty+my)/2)-14}" width="75" height="18" fill="#1e1b4b" rx="4" stroke="#4f46e5" stroke-width="1"/>',
        f'<text x="{((tx+mx)/2)-7}" y="{((ty+my)/2)}" fill="#c7d2fe" font-family="system-ui, sans-serif" font-size="10" font-weight="600" text-anchor="middle">{p_a_str}</text>',

        # Path b (M -> Y)
        f'<line x1="{mx+25}" y1="{my+20}" x2="{yx}" y2="{yy-25}" stroke="#10b981" stroke-width="2.5" marker-end="url(#arrow-emerald)"/>',
        f'<rect x="{((mx+yx)/2)-30}" y="{((my+yy)/2)-14}" width="75" height="18" fill="#064e3b" rx="4" stroke="#059669" stroke-width="1"/>',
        f'<text x="{((mx+yx)/2)+8}" y="{((my+yy)/2)}" fill="#a7f3d0" font-family="system-ui, sans-serif" font-size="10" font-weight="600" text-anchor="middle">{p_b_str}</text>',

        # Direct path c' (T -> Y)
        f'<line x1="{tx+45}" y1="{ty}" x2="{yx-45}" y2="{yy}" stroke="#94a3b8" stroke-width="2" stroke-dasharray="4,3" marker-end="url(#arrow-slate)"/>',
        f'<rect x="{((tx+yx)/2)-35}" y="{ty+12}" width="70" height="18" fill="#1e293b" rx="4" stroke="#475569" stroke-width="1"/>',
        f'<text x="{((tx+yx)/2)}" y="{ty+25}" fill="#cbd5e1" font-family="system-ui, sans-serif" font-size="10" font-weight="600" text-anchor="middle">{p_c_str}</text>',

        # Omitted Confounder Arc between e_M and e_Y
        f'<path d="M {mx+30},{my-5} C {mx+110},{my-20} {yx+30},{yy-80} {yx+25},{yy-25}" fill="none" stroke="#f43f5e" stroke-width="2" stroke-dasharray="5,4"/>',
        f'<rect x="{mx+100}" y="{my+10}" width="95" height="20" fill="#4c0519" rx="4" stroke="#e11d48" stroke-width="1"/>',
        f'<text x="{mx+147}" y="{my+24}" fill="#fda4af" font-family="system-ui, sans-serif" font-size="9.5" font-weight="700" text-anchor="middle">ρ = Corr(e_M, e_Y)</text>',

        # Nodes
        # Node T
        f'<rect x="{tx-50}" y="{ty-20}" width="100" height="40" fill="#1e1e38" rx="8" stroke="#6366f1" stroke-width="2"/>',
        f'<text x="{tx}" y="{ty-3}" fill="#ffffff" font-family="system-ui, sans-serif" font-size="11" font-weight="700" text-anchor="middle">Can Thiệp (T)</text>',
        f'<text x="{tx}" y="{ty+12}" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="9" text-anchor="middle">{treatment_name[:12]}</text>',

        # Node M
        f'<rect x="{mx-50}" y="{my-20}" width="100" height="40" fill="#063529" rx="8" stroke="#10b981" stroke-width="2"/>',
        f'<text x="{mx}" y="{my-3}" fill="#ffffff" font-family="system-ui, sans-serif" font-size="11" font-weight="700" text-anchor="middle">Trung Gian (M)</text>',
        f'<text x="{mx}" y="{my+12}" fill="#6ee7b7" font-family="system-ui, sans-serif" font-size="9" text-anchor="middle">{mediator_name[:12]}</text>',

        # Node Y
        f'<rect x="{yx-50}" y="{yy-20}" width="100" height="40" fill="#1e293b" rx="8" stroke="#38bdf8" stroke-width="2"/>',
        f'<text x="{yx}" y="{yy-3}" fill="#ffffff" font-family="system-ui, sans-serif" font-size="11" font-weight="700" text-anchor="middle">Kết Quả (Y)</text>',
        f'<text x="{yx}" y="{yy+12}" fill="#7dd3fc" font-family="system-ui, sans-serif" font-size="9" text-anchor="middle">{outcome_name[:12]}</text>',

        # ACME Summary Badge in Panel A
        f'<rect x="40" y="305" width="340" height="44" fill="#0f172a" rx="6" stroke="#334155" stroke-width="1"/>',
        f'<text x="50" y="322" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="10">Hiệu ứng gián tiếp chuẩn (ρ = 0):</text>',
        f'<text x="50" y="339" fill="#38bdf8" font-family="system-ui, sans-serif" font-size="12" font-weight="700">ACME δ = {acme_baseline:.4f}</text>',
        f'<text x="210" y="322" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="10">Ngưỡng triệt tiêu nhiễu:</text>',
        f'<text x="210" y="339" fill="#f43f5e" font-family="system-ui, sans-serif" font-size="12" font-weight="700">ρ* = {rho_tilde:.4f}</text>',

        # Panel B: Graph Background & Grid
        f'<rect x="{bx0}" y="{by0}" width="{b_width}" height="{b_height}" fill="#0c1322" rx="6" stroke="#1e293b" stroke-width="1"/>',

        # Zero ACME horizontal line
        f'<line x1="{bx0}" y1="{y_zero}" x2="{bx1}" y2="{y_zero}" stroke="#64748b" stroke-width="1.5" stroke-dasharray="4,3"/>',
        f'<text x="{bx1-5}" y="{y_zero-4}" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="9" text-anchor="end">δ = 0 (Vô hiệu)</text>',

        # Zero Rho vertical line
        f'<line x1="{x_zero_rho}" y1="{by0}" x2="{x_zero_rho}" y2="{by1}" stroke="#475569" stroke-width="1" stroke-dasharray="2,2"/>',
        f'<text x="{x_zero_rho}" y="{by1+14}" fill="#64748b" font-family="system-ui, sans-serif" font-size="9" text-anchor="middle">ρ = 0</text>',

        # 95% Confidence Ribbon
        f'<polygon points="{ribbon_points}" fill="#6366f1" fill-opacity="0.18"/>',

        # Point estimate curve
        f'<polyline points="{curve_points}" fill="none" stroke="#6366f1" stroke-width="2.5"/>',

        # Baseline ACME dot at rho = 0
        f'<circle cx="{x_zero_rho}" cy="{scale_y(acme_baseline)}" r="5" fill="#38bdf8" stroke="#ffffff" stroke-width="1.5"/>',

        # Threshold rho line & marker
        f'<line x1="{x_threshold}" y1="{by0}" x2="{x_threshold}" y2="{by1}" stroke="#f43f5e" stroke-width="2" stroke-dasharray="3,3"/>',
        f'<circle cx="{x_threshold}" cy="{y_zero}" r="6" fill="#f43f5e" stroke="#ffffff" stroke-width="1.5"/>',
        f'<text x="{x_threshold}" y="{by0+16}" fill="#fda4af" font-family="system-ui, sans-serif" font-size="10" font-weight="700" text-anchor="middle">ρ* = {rho_tilde:.3f}</text>',

        # X-axis ticks and labels
        f'<text x="{scale_x(-0.8)}" y="{by1+14}" fill="#64748b" font-family="system-ui, sans-serif" font-size="9" text-anchor="middle">-0.8</text>',
        f'<text x="{scale_x(-0.4)}" y="{by1+14}" fill="#64748b" font-family="system-ui, sans-serif" font-size="9" text-anchor="middle">-0.4</text>',
        f'<text x="{scale_x(0.4)}" y="{by1+14}" fill="#64748b" font-family="system-ui, sans-serif" font-size="9" text-anchor="middle">+0.4</text>',
        f'<text x="{scale_x(0.8)}" y="{by1+14}" fill="#64748b" font-family="system-ui, sans-serif" font-size="9" text-anchor="middle">+0.8</text>',
        f'<text x="{(bx0+bx1)/2}" y="{by1+28}" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="10" text-anchor="middle">Tham số Độ nhạy Tương quan Nhiễu (ρ)</text>',

        # Y-axis label
        f'<text x="{bx0+10}" y="{by0+18}" fill="#cbd5e1" font-family="system-ui, sans-serif" font-size="10" font-weight="600">ACME δ(ρ)</text>',

        # Marker definitions
        '<defs>',
        '<marker id="arrow-indigo" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '<path d="M 0 1 L 8 5 L 0 9 z" fill="#6366f1" />',
        '</marker>',
        '<marker id="arrow-emerald" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '<path d="M 0 1 L 8 5 L 0 9 z" fill="#10b981" />',
        '</marker>',
        '<marker id="arrow-slate" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '<path d="M 0 1 L 8 5 L 0 9 z" fill="#94a3b8" />',
        '</marker>',
        '</defs>',

        '</svg>'
    ]

    return "".join(svg_elements)
