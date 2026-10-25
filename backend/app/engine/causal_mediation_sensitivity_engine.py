"""
DataTrust - Nonparametric Causal Mediation Analysis with Unobserved Confounder Sensitivity Bounds
=================================================================================================
Academic Foundations:
- Imai, K., Keele, L., & Yamamoto, T. (2010). Identification, Inference and Sensitivity
  Analysis for Causal Mediation Effects. Statistical Science, 25(1), 51-71.
- Imai, K., Keele, L., & Tingley, D. (2010). A General Approach to Causal Mediation
  Analysis. Psychological Methods, 15(4), 309-334.
- VanderWeele, T. J. (2015). Explanation in Causal Inference: Methods for Mediation
  and Interaction. Oxford University Press.
"""

from typing import Dict, List, Any, Optional, Tuple
import math
import numpy as np
from scipy import stats


def _fit_linear_model(
    y: np.ndarray,
    X: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float, float, np.ndarray]:
    """Fits OLS with intercept and returns coefs, se, residuals, r2, sigma, cov_beta."""
    n, k = X.shape
    X_design = np.column_stack([np.ones(n), X])
    xtx = X_design.T @ X_design
    ridge = 1e-7 * np.eye(xtx.shape[0])
    cov_unscaled = np.linalg.inv(xtx + ridge)
    beta = cov_unscaled @ (X_design.T @ y)

    y_pred = X_design @ beta
    residuals = y - y_pred
    df_e = max(1, n - (k + 1))
    sigma2 = np.sum(residuals ** 2) / df_e
    sigma = math.sqrt(max(1e-12, sigma2))

    cov_beta = sigma2 * cov_unscaled
    se = np.sqrt(np.maximum(1e-12, np.diag(cov_beta)))

    ss_tot = np.sum((y - np.mean(y)) ** 2)
    ss_res = np.sum(residuals ** 2)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else 0.0

    return beta, se, residuals, r2, sigma, cov_beta


def run_causal_mediation_sensitivity(
    records: List[Dict[str, Any]],
    treatment_col: str,
    mediator_col: str,
    outcome_col: str,
    covariate_cols: Optional[List[str]] = None,
    target_treatment_val: Optional[Any] = None,
    simulations: int = 400,
    alpha_level: float = 0.05,
    scope: str = "all",
    **kwargs
) -> Dict[str, Any]:
    """
    Executes Causal Mediation Analysis & Imai-Keele-Yamamoto (2010) Sensitivity Analysis.
    Compatible with both flat dict records and wrapped answers records.
    """
    if covariate_cols is None:
        covariate_cols = []

    # Handle records filtering if wrapped
    filtered_records = records
    if scope == "verified_clean":
        filtered_records = [
            r for r in records
            if not r.get("is_speeding", False)
            and not r.get("is_straightlining", False)
            and not r.get("anomaly_flags")
        ]
        if len(filtered_records) < 20:
            filtered_records = records

    t_list: List[float] = []
    m_list: List[float] = []
    y_list: List[float] = []
    z_list: List[List[float]] = []

    for r in filtered_records:
        ans = r.get("answers", r) # extract inner answers if present, else flat dict
        if (treatment_col not in ans or
            mediator_col not in ans or
            outcome_col not in ans):
            continue

        try:
            t_raw = ans[treatment_col]
            if target_treatment_val is not None:
                t_val = 1.0 if str(t_raw).strip() == str(target_treatment_val).strip() else 0.0
            else:
                t_val = float(t_raw)
            m_val = float(ans[mediator_col])
            y_val = float(ans[outcome_col])
        except (ValueError, TypeError):
            continue

        row_z: List[float] = []
        skip = False
        for zid in covariate_cols:
            if zid not in ans:
                skip = True
                break
            try:
                row_z.append(float(ans[zid]))
            except (ValueError, TypeError):
                skip = True
                break

        if skip:
            continue

        t_list.append(t_val)
        m_list.append(m_val)
        y_list.append(y_val)
        z_list.append(row_z)

    n = len(t_list)
    if n < 20:
        return {
            "status": "INSUFFICIENT_SAMPLE",
            "sample_size": n,
            "message": f"Chỉ có {n} phản hồi hợp lệ (cần tối thiểu 20 phản hồi).",
        }

    t_arr = np.array(t_list, dtype=float)
    m_arr = np.array(m_list, dtype=float)
    y_arr = np.array(y_list, dtype=float)

    # Treatment binary binarization
    unique_t = np.unique(t_arr)
    if len(unique_t) == 2 and set(unique_t).issubset({0.0, 1.0}):
        t_bin = t_arr
    else:
        med_t = float(np.median(t_arr))
        t_bin = (t_arr > med_t).astype(float)

    n_treated = int(np.sum(t_bin == 1.0))
    n_control = int(np.sum(t_bin == 0.0))
    if n_treated < 3 or n_control < 3:
        return {
            "status": "IMBALANCED_TREATMENT",
            "message": f"Nhóm can thiệp phân bố quá lệch (Treated: {n_treated}, Control: {n_control}).",
        }

    num_z = len(covariate_cols)
    z_arr = np.array(z_list, dtype=float) if num_z > 0 else np.empty((n, 0), dtype=float)

    # 1. Mediator Model: M ~ 1 + T + Z
    X_m = np.column_stack([t_bin, z_arr]) if num_z > 0 else t_bin.reshape(-1, 1)
    beta_m, se_m, res_m, r2_m, sigma_m, cov_m = _fit_linear_model(m_arr, X_m)

    # 2. Outcome Model: Y ~ 1 + T + M + Z
    X_y = np.column_stack([t_bin, m_arr, z_arr]) if num_z > 0 else np.column_stack([t_bin, m_arr])
    beta_y, se_y, res_y, r2_y, sigma_y, cov_y = _fit_linear_model(y_arr, X_y)

    path_a = float(beta_m[1])
    se_path_a = float(se_m[1])
    path_b = float(beta_y[2])
    se_path_b = float(se_y[2])
    path_c_prime = float(beta_y[1])
    se_path_c_prime = float(se_y[1])

    # Point estimates under sequential ignorability (rho = 0)
    acme_point = path_a * path_b
    ade_point = path_c_prime
    total_point = acme_point + ade_point
    prop_mediated = (acme_point / total_point * 100.0) if abs(total_point) > 1e-6 else 0.0

    # 3. Quasi-Bayesian Monte Carlo Simulation (King et al. 2000; Imai et al. 2010)
    n_sims = min(max(100, simulations), 800)
    rng = np.random.default_rng(101)

    draws_m = rng.multivariate_normal(beta_m, cov_m, size=n_sims)
    draws_y = rng.multivariate_normal(beta_y, cov_y, size=n_sims)

    sim_acme = draws_m[:, 1] * draws_y[:, 2]
    sim_ade = draws_y[:, 1]
    sim_total = sim_acme + sim_ade

    acme_se = float(np.std(sim_acme))
    ade_se = float(np.std(sim_ade))
    total_se = float(np.std(sim_total))

    z_crit = float(stats.norm.ppf(1.0 - alpha_level / 2.0))
    ci_acme = [float(np.percentile(sim_acme, alpha_level / 2.0 * 100)), float(np.percentile(sim_acme, (1 - alpha_level / 2.0) * 100))]
    ci_ade = [float(np.percentile(sim_ade, alpha_level / 2.0 * 100)), float(np.percentile(sim_ade, (1 - alpha_level / 2.0) * 100))]
    ci_total = [float(np.percentile(sim_total, alpha_level / 2.0 * 100)), float(np.percentile(sim_total, (1 - alpha_level / 2.0) * 100))]

    p_acme = float(2.0 * (1.0 - stats.norm.cdf(abs(acme_point) / max(1e-8, acme_se))))
    p_ade = float(2.0 * (1.0 - stats.norm.cdf(abs(ade_point) / max(1e-8, ade_se))))
    p_total = float(2.0 * (1.0 - stats.norm.cdf(abs(total_point) / max(1e-8, total_se))))

    # 4. Imai-Keele Sensitivity Analysis on Sequential Ignorability (rho in [-0.8, +0.8])
    rho_grid = np.linspace(-0.80, 0.80, 33)
    sensitivity_curve: List[Dict[str, Any]] = []

    for rho_val in rho_grid:
        if abs(rho_val) >= 0.999:
            continue
        factor = (rho_val * sigma_y) / (max(1e-6, sigma_m) * math.sqrt(max(1e-6, 1.0 - rho_val**2)))
        adj_acme = float(path_a * (path_b - factor))
        ci_low = adj_acme - z_crit * acme_se
        ci_high = adj_acme + z_crit * acme_se

        sensitivity_curve.append({
            "rho": round(float(rho_val), 2),
            "acme": round(adj_acme, 4),
            "ci_lower": round(ci_low, 4),
            "ci_upper": round(ci_high, 4),
        })

    # Exact analytic solution for rho at which ACME(rho) = 0:
    denom_rho = sigma_y**2 + (path_b**2) * (sigma_m**2)
    if denom_rho > 1e-12:
        exact_rho_zero = float(np.sign(path_b) * math.sqrt(min(0.99, max(0.0, (path_b**2 * sigma_m**2) / denom_rho))))
    else:
        exact_rho_zero = 0.0

    rho_robustness_label = (
        "Bền vững cao (|ρ₀| ≥ 0.40)"
        if abs(exact_rho_zero) >= 0.40
        else "Bền vững trung bình (0.20 ≤ |ρ₀| < 0.40)"
        if abs(exact_rho_zero) >= 0.20
        else "Dễ bị tổn thương (|ρ₀| < 0.20)"
    )

    # 5. Dual-Panel SVG Visualization
    svg_chart = _render_mediation_svg(
        path_a=path_a,
        path_b=path_b,
        path_c_prime=path_c_prime,
        acme=acme_point,
        ade=ade_point,
        total=total_point,
        prop_med=prop_mediated,
        exact_rho_zero=exact_rho_zero,
        sensitivity_curve=sensitivity_curve,
        p_acme=p_acme,
    )

    # 6. APA Narrative
    is_acme_sig = p_acme < alpha_level
    sig_text = (
        f"có ý nghĩa thống kê (z = {acme_point / max(1e-8, acme_se):.3f}, p = {p_acme:.4f})"
        if is_acme_sig
        else f"không có ý nghĩa thống kê (z = {acme_point / max(1e-8, acme_se):.3f}, p = {p_acme:.4f})"
    )

    apa_narrative = (
        f"Phân tích trung gian nhân quả theo Imai, Keele, and Yamamoto (2010) với {n_sims} lượt mô phỏng Quasi-Bayesian "
        f"(N = {n}, Nhóm Can thiệp = {n_treated}, Đối chứng = {n_control}). "
        f"Average Causal Mediation Effect (ACME / Hiệu ứng trung gian nhân quả) ước tính là delta = {acme_point:.4f} "
        f"(SE = {acme_se:.4f}, 95% CI [{ci_acme[0]:.4f}, {ci_acme[1]:.4f}], p = {p_acme:.4f}), {sig_text}. "
        f"Hiệu ứng trực tiếp (ADE) là zeta = {ade_point:.4f} (SE = {ade_se:.4f}, p = {p_ade:.4f}), "
        f"Tổng hiệu ứng nhân quả là tau = {total_point:.4f} (p = {p_total:.4f}). "
        f"Tỷ lệ hiệu ứng được truyền dẫn qua biến trung gian đạt {prop_mediated:.1f}%. "
        f"Kiểm định độ nhạy với giả định Ignorability Tuần tự xác định ngưỡng tương quan tới hạn rho_0 = {exact_rho_zero:+.3f} "
        f"({rho_robustness_label})."
    )

    return {
        "status": "success",
        "sample_size": n,
        "n_treated": n_treated,
        "n_control": n_control,
        "treatment_field": treatment_col,
        "mediator_field": mediator_col,
        "outcome_field": outcome_col,
        "covariate_fields": covariate_cols,
        "sample_diagnostics": {
            "n_total": n,
            "total_sample": n,
            "n_treated": n_treated,
            "treated_count": n_treated,
            "n_control": n_control,
            "control_count": n_control,
            "mean_mediator": round(float(np.mean(m_arr)), 3),
            "sd_mediator": round(float(np.std(m_arr)), 3),
            "mean_outcome": round(float(np.mean(y_arr)), 3),
            "sd_outcome": round(float(np.std(y_arr)), 3),
            "r_squared_mediator_model": round(r2_m, 4),
            "r_squared_outcome_model": round(r2_y, 4),
        },
        "path_estimates": {
            "path_a": {
                "coefficient": round(path_a, 4),
                "se": round(se_path_a, 4),
                "t_stat": round(path_a / max(1e-8, se_path_a), 3),
                "p_value": round(float(2.0 * (1.0 - stats.t.cdf(abs(path_a / max(1e-8, se_path_a)), df=max(1, n - X_m.shape[1] - 1)))), 4),
            },
            "path_b": {
                "coefficient": round(path_b, 4),
                "se": round(se_path_b, 4),
                "t_stat": round(path_b / max(1e-8, se_path_b), 3),
                "p_value": round(float(2.0 * (1.0 - stats.t.cdf(abs(path_b / max(1e-8, se_path_b)), df=max(1, n - X_y.shape[1] - 1)))), 4),
            },
            "path_c_prime": {
                "coefficient": round(path_c_prime, 4),
                "se": round(se_path_c_prime, 4),
                "t_stat": round(path_c_prime / max(1e-8, se_path_c_prime), 3),
                "p_value": round(float(2.0 * (1.0 - stats.t.cdf(abs(path_c_prime / max(1e-8, se_path_c_prime)), df=max(1, n - X_y.shape[1] - 1)))), 4),
            },
        },
        "path_coefficients": {
            "path_a_treatment_to_mediator": round(path_a, 4),
            "se_a": round(se_path_a, 4),
            "path_b_mediator_to_outcome": round(path_b, 4),
            "se_b": round(se_path_b, 4),
            "path_c_prime_direct": round(path_c_prime, 4),
            "se_c_prime": round(se_path_c_prime, 4),
        },
        "baseline_effects": {
            "acme": round(acme_point, 4),
            "se_acme": round(acme_se, 4),
            "acme_se": round(acme_se, 4),
            "p_value": round(p_acme, 4),
            "acme_p": round(p_acme, 4),
            "ci_95_lower": round(ci_acme[0], 4),
            "ci_95_upper": round(ci_acme[1], 4),
            "acme_ci_95": [round(ci_acme[0], 4), round(ci_acme[1], 4)],
            "z_stat": round(acme_point / max(1e-8, acme_se), 3),
            "ade": round(ade_point, 4),
            "se_ade": round(ade_se, 4),
            "ade_se": round(ade_se, 4),
            "p_ade": round(p_ade, 4),
            "ade_p": round(p_ade, 4),
            "ade_ci_95": [round(ci_ade[0], 4), round(ci_ade[1], 4)],
            "total_effect": round(total_point, 4),
            "total_se": round(total_se, 4),
            "total_p": round(p_total, 4),
            "total_ci_95": [round(ci_total[0], 4), round(ci_total[1], 4)],
            "proportion_mediated": round(prop_mediated / 100.0, 4),
            "is_significant": bool(is_acme_sig),
        },
        "causal_effects": {
            "acme_indirect": {
                "estimate": round(acme_point, 4),
                "se": round(acme_se, 4),
                "p_value": round(p_acme, 4),
                "ci_95": [round(ci_acme[0], 4), round(ci_acme[1], 4)],
                "is_significant": bool(is_acme_sig),
            },
            "ade_direct": {
                "estimate": round(ade_point, 4),
                "se": round(ade_se, 4),
                "p_value": round(p_ade, 4),
                "ci_95": [round(ci_ade[0], 4), round(ci_ade[1], 4)],
            },
            "total_effect": {
                "estimate": round(total_point, 4),
                "se": round(total_se, 4),
                "p_value": round(p_total, 4),
                "ci_95": [round(ci_total[0], 4), round(ci_total[1], 4)],
            },
            "proportion_mediated_pct": round(prop_mediated, 2),
        },
        "sensitivity_analysis": {
            "critical_rho_threshold": round(exact_rho_zero, 4),
            "critical_rho_zero": round(exact_rho_zero, 4),
            "r2_star_product": round(exact_rho_zero**2, 4),
            "robustness_level": rho_robustness_label,
            "robustness_badge": "Bền vững cao" if abs(exact_rho_zero) >= 0.4 else "Trung bình" if abs(exact_rho_zero) >= 0.2 else "Dễ tổn thương",
            "robustness_description": f"Cần nhiễu tiềm ẩn |rho| >= {abs(exact_rho_zero):.2f} để triệt tiêu hiệu ứng trung gian.",
            "sensitivity_curve": sensitivity_curve,
            "sensitivity_grid": sensitivity_curve,
            "curve_points": sensitivity_curve,
        },
        "svg_chart": svg_chart,
        "svg_visualization": svg_chart,
        "apa_narrative": apa_narrative,
    }


# Dual signature compatibility
def run_causal_mediation_sensitivity_analysis(
    records: List[Dict[str, Any]],
    treatment_question_id: str,
    mediator_question_id: str,
    outcome_question_id: str,
    covariate_question_ids: Optional[List[str]] = None,
    simulations: int = 400,
    alpha_level: float = 0.05,
    scope: str = "all",
    **kwargs
) -> Dict[str, Any]:
    return run_causal_mediation_sensitivity(
        records=records,
        treatment_col=treatment_question_id,
        mediator_col=mediator_question_id,
        outcome_col=outcome_question_id,
        covariate_cols=covariate_question_ids,
        simulations=simulations,
        alpha_level=alpha_level,
        scope=scope,
        **kwargs
    )


def _render_mediation_svg(
    path_a: float,
    path_b: float,
    path_c_prime: float,
    acme: float,
    ade: float,
    total: float,
    prop_med: float,
    exact_rho_zero: float,
    sensitivity_curve: List[Dict[str, Any]],
    p_acme: float,
) -> str:
    """Generates responsive dual-panel SVG visualizer."""
    svg_width = 860
    svg_height = 360

    badge_color = "#10b981" if p_acme < 0.05 else "#94a3b8"
    badge_text = f"Significant Mediation (p = {p_acme:.3f})" if p_acme < 0.05 else f"Non-Significant (p = {p_acme:.3f})"

    min_acme_curve = min([pt["ci_lower"] for pt in sensitivity_curve] + [0.0])
    max_acme_curve = max([pt["ci_upper"] for pt in sensitivity_curve] + [0.0])
    span_acme = max(1e-4, max_acme_curve - min_acme_curve)

    def x_rho(r: float) -> float:
        return 490 + ((r - (-0.8)) / 1.6) * 310

    def y_acme(a_val: float) -> float:
        return 290 - ((a_val - min_acme_curve) / span_acme) * 190

    y_zero = y_acme(0.0)
    x_rho_crit = x_rho(exact_rho_zero)

    pts_line = []
    pts_upper = []
    pts_lower = []
    for pt in sensitivity_curve:
        rx = x_rho(pt["rho"])
        ry = y_acme(pt["acme"])
        ry_u = y_acme(pt["ci_upper"])
        ry_l = y_acme(pt["ci_lower"])
        pts_line.append(f"{rx:.1f},{ry:.1f}")
        pts_upper.append(f"{rx:.1f},{ry_u:.1f}")
        pts_lower.append(f"{rx:.1f},{ry_l:.1f}")

    path_curve = "M " + " L ".join(pts_line)
    poly_band = "M " + " L ".join(pts_upper) + " L " + " L ".join(reversed(pts_lower)) + " Z"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <defs>
    <linearGradient id="medBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="{svg_width}" height="{svg_height}" rx="12" fill="url(#medBg)"/>

  <!-- Main Title -->
  <text x="30" y="36" fill="#f8fafc" font-size="16" font-weight="700">Causal Mediation &amp; Confounder Sensitivity Analysis</text>
  <rect x="580" y="20" width="250" height="26" rx="6" fill="{badge_color}" opacity="0.2"/>
  <rect x="580" y="20" width="250" height="26" rx="6" fill="none" stroke="{badge_color}" stroke-width="1.5"/>
  <text x="705" y="37" fill="{badge_color}" font-size="11" font-weight="700" text-anchor="middle">{badge_text}</text>

  <!-- Panel A: Mediation Path Diagram -->
  <rect x="30" y="60" width="410" height="270" rx="8" fill="#1e293b" fill-opacity="0.6" stroke="#334155" stroke-width="1"/>
  <text x="45" y="85" fill="#e2e8f0" font-size="13" font-weight="600">Panel A: Causal Mediation Flow (T → M → Y)</text>

  <!-- Node T -->
  <rect x="60" y="200" width="80" height="40" rx="8" fill="#0369a1" stroke="#38bdf8" stroke-width="1.5"/>
  <text x="100" y="225" fill="#ffffff" font-size="12" font-weight="700" text-anchor="middle">Treatment (T)</text>

  <!-- Node M -->
  <rect x="195" y="110" width="85" height="40" rx="8" fill="#4338ca" stroke="#818cf8" stroke-width="1.5"/>
  <text x="237" y="135" fill="#ffffff" font-size="12" font-weight="700" text-anchor="middle">Mediator (M)</text>

  <!-- Node Y -->
  <rect x="330" y="200" width="80" height="40" rx="8" fill="#047857" stroke="#34d399" stroke-width="1.5"/>
  <text x="370" y="225" fill="#ffffff" font-size="12" font-weight="700" text-anchor="middle">Outcome (Y)</text>

  <!-- Arrow T -> M (path a) -->
  <line x1="125" y1="200" x2="195" y2="140" stroke="#38bdf8" stroke-width="2"/>
  <text x="145" y="160" fill="#38bdf8" font-size="11" font-weight="700">a = {path_a:+.2f}</text>

  <!-- Arrow M -> Y (path b) -->
  <line x1="280" y1="140" x2="345" y2="200" stroke="#818cf8" stroke-width="2"/>
  <text x="325" y="160" fill="#818cf8" font-size="11" font-weight="700">b = {path_b:+.2f}</text>

  <!-- Arrow T -> Y (direct c') -->
  <line x1="140" y1="220" x2="330" y2="220" stroke="#f59e0b" stroke-width="2" stroke-dasharray="4,3"/>
  <text x="235" y="240" fill="#f59e0b" font-size="11" font-weight="700" text-anchor="middle">c' (ADE) = {path_c_prime:+.2f}</text>

  <!-- Mediation Metrics Box -->
  <rect x="50" y="260" width="370" height="55" rx="6" fill="#0f172a" stroke="#334155" stroke-width="1"/>
  <text x="65" y="280" fill="#94a3b8" font-size="11">ACME (Indirect): <tspan fill="#34d399" font-weight="700">{acme:+.3f}</tspan> | Total Effect: <tspan fill="#ffffff" font-weight="700">{total:+.3f}</tspan></text>
  <text x="65" y="300" fill="#94a3b8" font-size="11">Proportion Mediated: <tspan fill="#818cf8" font-weight="700">{prop_med:.1f}%</tspan></text>

  <!-- Panel B: Sensitivity Curve -->
  <rect x="460" y="60" width="370" height="270" rx="8" fill="#1e293b" fill-opacity="0.6" stroke="#334155" stroke-width="1"/>
  <text x="475" y="85" fill="#e2e8f0" font-size="13" font-weight="600">Panel B: Sensitivity Analysis ACME(&rho;) vs &rho;</text>

  <!-- Zero Horizontal Line -->
  <line x1="490" y1="{y_zero:.1f}" x2="800" y2="{y_zero:.1f}" stroke="#64748b" stroke-width="1" stroke-dasharray="4,4"/>
  <text x="805" y="{y_zero + 4:.1f}" fill="#64748b" font-size="10">0.0</text>

  <!-- Axes B -->
  <line x1="490" y1="290" x2="800" y2="290" stroke="#475569" stroke-width="1.5"/>
  <line x1="490" y1="290" x2="490" y2="100" stroke="#475569" stroke-width="1.5"/>
  <text x="645" y="315" fill="#94a3b8" font-size="11" text-anchor="middle">Confounder Correlation (&rho;)</text>
  <text x="475" y="195" fill="#94a3b8" font-size="11" text-anchor="middle" transform="rotate(-90 475 195)">ACME(&rho;)</text>

  <!-- Confidence Band -->
  <path d="{poly_band}" fill="#818cf8" fill-opacity="0.2"/>

  <!-- Sensitivity Curve Line -->
  <path d="{path_curve}" fill="none" stroke="#818cf8" stroke-width="2.5"/>

  <!-- Vertical line for critical rho_zero -->
  <line x1="{x_rho_crit:.1f}" y1="100" x2="{x_rho_crit:.1f}" y2="290" stroke="#ef4444" stroke-width="2" stroke-dasharray="3,3"/>
  <circle cx="{x_rho_crit:.1f}" cy="{y_zero:.1f}" r="5" fill="#ef4444"/>
  <text x="{x_rho_crit:.1f}" y="115" fill="#ef4444" font-size="10" font-weight="700" text-anchor="middle">&rho;₀ = {exact_rho_zero:+.2f}</text>
</svg>"""
    return svg
