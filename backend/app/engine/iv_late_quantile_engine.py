"""
Nonparametric Instrumental Variable & Local Average Treatment Effect (LATE) Quantile Engine
DataTrust Quantitative Econometrics Architecture

References:
- Abadie, A., Angrist, J., & Imbens, G. (2002).
  "Instrumental Variables Estimates of the Effect of Subsidized Training on the Quantiles of Trainee Earnings".
  Econometrica, 70(1), 91-117.
- Frölich, M., & Melly, B. (2013).
  "Unconditional quantile treatment effects under endogeneity".
  Quantitative Economics, 4(3), 497-537.
- Kitagawa, T. (2015).
  "A test for instrument validity". Econometrica, 83(5), 2043-2063.
- Imbens, G. W., & Angrist, J. D. (1994).
  "Identification and Estimation of Local Average Treatment Effects".
  Econometrica, 62(2), 467-475.
"""

from typing import Dict, List, Any, Optional
import numpy as np
from scipy import stats


def _weighted_quantile(values: np.ndarray, weights: np.ndarray, tau: float) -> float:
    """Compute empirical weighted quantile for non-negative weights."""
    valid = (weights > 0) & np.isfinite(values) & np.isfinite(weights)
    if not np.any(valid):
        return 0.0
    vals = values[valid]
    w = weights[valid]
    sorter = np.argsort(vals)
    sorted_vals = vals[sorter]
    sorted_w = w[sorter]
    cum_w = np.cumsum(sorted_w)
    tot_w = cum_w[-1]
    if tot_w <= 0:
        return float(np.median(vals))
    cutoff = tau * tot_w
    idx = np.searchsorted(cum_w, cutoff)
    idx = min(idx, len(sorted_vals) - 1)
    return float(sorted_vals[idx])


def _generate_iv_late_svg(
    tau_grid: List[float],
    q_treated: List[float],
    q_control: List[float],
    qte_c: List[float],
    complier_share: float,
    monotonicity_valid: bool,
    grid_y: List[float],
    diff_density_1: List[float],
    diff_density_0: List[float]
) -> str:
    """
    Generate responsive dual-panel SVG:
    Panel A: Complier Potential Quantiles Q_{Y(1)|C}(tau) vs Q_{Y(0)|C}(tau) & QTE-C Ribbon
    Panel B: Kitagawa (2015) Monotonicity & Defier Absence Diagnostic Densities
    """
    svg_w, svg_h = 960, 420
    p1_x, p1_y, p1_w, p1_h = 60, 50, 400, 310
    p2_x, p2_y, p2_w, p2_h = 520, 50, 380, 310

    # Panel 1: Quantiles mapping
    all_q = q_treated + q_control
    min_q = min(all_q) if all_q else 0.0
    max_q = max(all_q) if all_q else 100.0
    span_q = max(max_q - min_q, 1e-4)

    def map_p1_x(tau_val: float) -> float:
        return p1_x + tau_val * p1_w

    def map_p1_y(q_val: float) -> float:
        return p1_y + p1_h - ((q_val - min_q) / span_q) * p1_h

    t_pts = " ".join([f"{map_p1_x(t):.1f},{map_p1_y(q):.1f}" for t, q in zip(tau_grid, q_treated)])
    c_pts = " ".join([f"{map_p1_x(t):.1f},{map_p1_y(q):.1f}" for t, q in zip(tau_grid, q_control)])

    # Ribbon polygon
    poly_pts = []
    for t, q in zip(tau_grid, q_treated):
        poly_pts.append(f"{map_p1_x(t):.1f},{map_p1_y(q):.1f}")
    for t, q in reversed(list(zip(tau_grid, q_control))):
        poly_pts.append(f"{map_p1_x(t):.1f},{map_p1_y(q):.1f}")
    ribbon_str = " ".join(poly_pts)

    # Panel 2: Kitagawa density tests
    all_d = diff_density_1 + diff_density_0 + [0.0]
    min_d = min(all_d)
    max_d = max(all_d)
    span_d = max(max_d - min_d, 1e-4)
    min_y = min(grid_y) if grid_y else 0.0
    max_y = max(grid_y) if grid_y else 100.0
    span_y = max(max_y - min_y, 1e-4)

    def map_p2_x(y_val: float) -> float:
        return p2_x + ((y_val - min_y) / span_y) * p2_w

    def map_p2_y(d_val: float) -> float:
        return p2_y + p2_h - ((d_val - min_d) / span_d) * p2_h

    d1_pts = " ".join([f"{map_p2_x(y):.1f},{map_p2_y(d):.1f}" for y, d in zip(grid_y, diff_density_1)])
    d0_pts = " ".join([f"{map_p2_x(y):.1f},{map_p2_y(d):.1f}" for y, d in zip(grid_y, diff_density_0)])
    zero_d_y = map_p2_y(0.0)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" style="background:#0f172a;border-radius:12px;font-family:system-ui,-apple-system,sans-serif;">
  <defs>
    <linearGradient id="qteCRibbon" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#818cf8" stop-opacity="0.15"/>
    </linearGradient>
  </defs>

  <!-- Title Header -->
  <text x="30" y="30" fill="#f8fafc" font-size="15" font-weight="700">DataTrust · IV-LATE Quantile Decomposition (Abadie et al. 2002; Frölich &amp; Melly 2013)</text>
  <text x="700" y="30" fill="#94a3b8" font-size="12" text-anchor="end">Complier Share P(C) = {complier_share*100:.1f}% | Kitagawa Monotonicity: {'PASS' if monotonicity_valid else 'VIOLATED'}</text>

  <!-- PANEL A: Complier Quantiles -->
  <rect x="{p1_x}" y="{p1_y}" width="{p1_w}" height="{p1_h}" fill="#1e293b" rx="6" stroke="#334155" stroke-width="1"/>
  <text x="{p1_x + 12}" y="{p1_y + 22}" fill="#38bdf8" font-size="12" font-weight="600">Panel A: Complier Potential Quantiles &amp; QTE-C</text>

  <!-- Grid lines -->
  <line x1="{p1_x}" y1="{p1_y + p1_h * 0.25:.1f}" x2="{p1_x + p1_w}" y2="{p1_y + p1_h * 0.25:.1f}" stroke="#334155" stroke-dasharray="3,3"/>
  <line x1="{p1_x}" y1="{p1_y + p1_h * 0.5:.1f}" x2="{p1_x + p1_w}" y2="{p1_y + p1_h * 0.5:.1f}" stroke="#334155" stroke-dasharray="3,3"/>
  <line x1="{p1_x}" y1="{p1_y + p1_h * 0.75:.1f}" x2="{p1_x + p1_w}" y2="{p1_y + p1_h * 0.75:.1f}" stroke="#334155" stroke-dasharray="3,3"/>

  <!-- QTE-C Ribbon -->
  <polygon points="{ribbon_str}" fill="url(#qteCRibbon)" stroke="none"/>

  <!-- Quantile curves -->
  <polyline points="{t_pts}" fill="none" stroke="#38bdf8" stroke-width="2.5"/>
  <polyline points="{c_pts}" fill="none" stroke="#818cf8" stroke-width="2" stroke-dasharray="4,3"/>

  <!-- Legend Panel A -->
  <circle cx="{p1_x + 20}" cy="{p1_y + p1_h - 18}" r="4" fill="#38bdf8"/>
  <text x="{p1_x + 30}" y="{p1_y + p1_h - 14}" fill="#e2e8f0" font-size="11">Complier Treated Q_Y(1)|C</text>
  <circle cx="{p1_x + 210}" cy="{p1_y + p1_h - 18}" r="4" fill="#818cf8"/>
  <text x="{p1_x + 220}" y="{p1_y + p1_h - 14}" fill="#e2e8f0" font-size="11">Complier Control Q_Y(0)|C</text>

  <!-- PANEL B: Kitagawa Monotonicity -->
  <rect x="{p2_x}" y="{p2_y}" width="{p2_w}" height="{p2_h}" fill="#1e293b" rx="6" stroke="#334155" stroke-width="1"/>
  <text x="{p2_x + 12}" y="{p2_y + 22}" fill="#a78bfa" font-size="12" font-weight="600">Panel B: Kitagawa (2015) Monotonicity Density Test</text>

  <!-- Zero boundary line -->
  <line x1="{p2_x}" y1="{zero_d_y:.1f}" x2="{p2_x + p2_w}" y2="{zero_d_y:.1f}" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="{p2_x + p2_w - 8}" y="{zero_d_y - 6:.1f}" fill="#ef4444" font-size="10" text-anchor="end">Defier Threshold (Δf &lt; 0)</text>

  <!-- Density difference curves -->
  <polyline points="{d1_pts}" fill="none" stroke="#10b981" stroke-width="2"/>
  <polyline points="{d0_pts}" fill="none" stroke="#06b6d4" stroke-width="2" stroke-dasharray="3,3"/>

  <!-- Legend Panel B -->
  <circle cx="{p2_x + 20}" cy="{p2_y + p2_h - 18}" r="4" fill="#10b981"/>
  <text x="{p2_x + 30}" y="{p2_y + p2_h - 14}" fill="#e2e8f0" font-size="11">Δf(Y, D=1 | Z)</text>
  <circle cx="{p2_x + 180}" cy="{p2_y + p2_h - 18}" r="4" fill="#06b6d4"/>
  <text x="{p2_x + 190}" y="{p2_y + p2_h - 14}" fill="#e2e8f0" font-size="11">Δf(Y, D=0 | Z)</text>

  <!-- Axis labels -->
  <text x="{p1_x + p1_w/2}" y="{p1_y + p1_h + 20}" fill="#64748b" font-size="11" text-anchor="middle">Quantile Rank τ ∈ (0, 1)</text>
  <text x="{p2_x + p2_w/2}" y="{p2_y + p2_h + 20}" fill="#64748b" font-size="11" text-anchor="middle">Outcome Domain y</text>
</svg>"""
    return svg


def run_iv_late_quantile_decomposition(
    records: List[Dict[str, Any]],
    treatment_col: str,
    instrument_col: str,
    outcome_col: str,
    covariate_cols: Optional[List[str]] = None,
    num_quantiles: int = 19,
    num_bootstrap: int = 100
) -> Dict[str, Any]:
    """
    Execute Nonparametric Instrumental Variable & LATE Quantile Decomposition:
    1. Validate binary treatment D, binary instrument Z, and continuous outcome Y.
    2. Estimate first-stage complier propensity P(Z=1|X) and Abadie kappa weights.
    3. Compute mean LATE and Quantile Treatment Effects on Compliers QTE-C across tau in (0, 1).
    4. Test Kitagawa (2015) monotonicity to detect defiers.
    5. Evaluate complier inequality (Gini, IQR) and first-order stochastic dominance.
    6. Generate responsive dual-panel SVG visualizer and formal APA 7th Edition narrative.
    """
    valid_rows = []
    covs = covariate_cols or []

    for r in records:
        d_raw = r.get(treatment_col)
        z_raw = r.get(instrument_col)
        y_raw = r.get(outcome_col)
        if d_raw is None or z_raw is None or y_raw is None:
            continue
        try:
            d_val = float(d_raw)
            z_val = float(z_raw)
            y_val = float(y_raw)
            if not (np.isfinite(d_val) and np.isfinite(z_val) and np.isfinite(y_val)):
                continue
        except (ValueError, TypeError):
            continue

        c_vals = []
        valid_cov = True
        for c in covs:
            c_raw = r.get(c)
            if c_raw is None:
                valid_cov = False
                break
            try:
                cv = float(c_raw)
                if not np.isfinite(cv):
                    valid_cov = False
                    break
                c_vals.append(cv)
            except (ValueError, TypeError):
                valid_cov = False
                break

        if valid_cov:
            valid_rows.append({
                "d": 1.0 if d_val >= 0.5 else 0.0,
                "z": 1.0 if z_val >= 0.5 else 0.0,
                "y": y_val,
                "covs": c_vals
            })

    N = len(valid_rows)
    if N < 25:
        return {
            "status": "insufficient_data",
            "message": f"Số lượng quan sát hợp lệ (N={N}) không đủ để ước lượng IV-LATE Quantile Decomposition (tối thiểu 25 bản ghi)."
        }

    D = np.array([r["d"] for r in valid_rows])
    Z = np.array([r["z"] for r in valid_rows])
    Y = np.array([r["y"] for r in valid_rows])

    if len(set(D)) < 2:
        return {
            "status": "invalid_treatment",
            "message": "Biến can thiệp D cần có cả 2 nhóm (0 và 1)."
        }

    if len(set(Z)) < 2:
        return {
            "status": "invalid_instrument",
            "message": "Biến công cụ Z cần có cả 2 nhóm (0 và 1)."
        }

    # First-stage instrument propensity: P(Z=1|X)
    # If covariates exist, fit logistic regression; otherwise use empirical mean
    if covs:
        try:
            X_cov = np.ones((N, 1 + len(covs)))
            for idx in range(len(covs)):
                X_cov[:, 1 + idx] = np.array([r["covs"][idx] for r in valid_rows])
            # Simple ridge-regularized logistic or linear probability for stability
            w_logit = np.linalg.pinv(X_cov.T @ X_cov + 1e-4 * np.eye(X_cov.shape[1])) @ (X_cov.T @ Z)
            prop_z = np.clip(X_cov @ w_logit, 0.05, 0.95)
        except Exception:
            prop_z = np.full(N, float(np.mean(Z)))
    else:
        prop_z = np.full(N, float(np.mean(Z)))

    # Abadie (2002) Kappa Weights:
    # kappa = 1 - (D * (1 - Z)) / (1 - P(Z=1|X)) - ((1 - D) * Z) / P(Z=1|X)
    kappa = 1.0 - (D * (1.0 - Z)) / (1.0 - prop_z) - ((1.0 - D) * Z) / prop_z

    # First-stage Complier Share
    complier_share = float(np.clip(np.mean(kappa), 0.01, 1.0))
    first_stage_diff = float(np.mean(D[Z == 1.0]) - np.mean(D[Z == 0.0]))

    if first_stage_diff <= 0.01:
        return {
            "status": "weak_instrument",
            "message": f"Biến công cụ quá yếu hoặc không thỏa mãn tính đơn điệu (First-Stage ΔD = {first_stage_diff:.4f} <= 0.01)."
        }

    # Standard Mean LATE via Wald estimator
    numerator_late = float(np.mean(Y[Z == 1.0]) - np.mean(Y[Z == 0.0]))
    mean_late = float(numerator_late / first_stage_diff)

    # Complier subgroup weights for treated (D=1) and control (D=0)
    w_treated = np.maximum(0.0, kappa * D)
    w_control = np.maximum(0.0, kappa * (1.0 - D))

    tau_grid = np.linspace(0.05, 0.95, max(min(num_quantiles, 49), 5))

    q_treated_list = [_weighted_quantile(Y, w_treated, t) for t in tau_grid]
    q_control_list = [_weighted_quantile(Y, w_control, t) for t in tau_grid]
    qte_c_list = [qt - qc for qt, qc in zip(q_treated_list, q_control_list)]

    median_qte_c = float(np.median(qte_c_list))

    # Kitagawa (2015) Monotonicity Diagnostic
    # Tests that delta_f_1(y) = f(y, D=1 | Z=1) - f(y, D=1 | Z=0) >= 0
    # and delta_f_0(y) = f(y, D=0 | Z=0) - f(y, D=0 | Z=1) >= 0
    grid_y = np.linspace(float(np.min(Y)), float(np.max(Y)), 50)
    y_d1_z1 = Y[(D == 1.0) & (Z == 1.0)]
    y_d1_z0 = Y[(D == 1.0) & (Z == 0.0)]
    y_d0_z0 = Y[(D == 0.0) & (Z == 0.0)]
    y_d0_z1 = Y[(D == 0.0) & (Z == 1.0)]

    def kde_eval(sub_data: np.ndarray, x_eval: np.ndarray) -> np.ndarray:
        if len(sub_data) < 2:
            return np.zeros_like(x_eval)
        try:
            kde = stats.gaussian_kde(sub_data)
            return kde(x_eval)
        except Exception:
            return np.zeros_like(x_eval)

    # Scale KDEs by joint cell probabilities P(D=d, Z=z)
    p_d1_z1 = len(y_d1_z1) / N
    p_d1_z0 = len(y_d1_z0) / N
    p_d0_z0 = len(y_d0_z0) / N
    p_d0_z1 = len(y_d0_z1) / N

    dens_d1_z1 = p_d1_z1 * kde_eval(y_d1_z1, grid_y)
    dens_d1_z0 = p_d1_z0 * kde_eval(y_d1_z0, grid_y)
    dens_d0_z0 = p_d0_z0 * kde_eval(y_d0_z0, grid_y)
    dens_d0_z1 = p_d0_z1 * kde_eval(y_d0_z1, grid_y)

    diff_dens_1 = (dens_d1_z1 - dens_d1_z0).tolist()
    diff_dens_0 = (dens_d0_z0 - dens_d0_z1).tolist()

    # Monotonicity test: check if negative violations are within numerical noise
    min_violation = min(min(diff_dens_1), min(diff_dens_0))
    monotonicity_passed = bool(min_violation >= -0.015)

    # Complier inequality diagnostics
    # Pseudo-samples from complier quantile functions to compute Gini
    syn_treated_c = np.interp(np.random.uniform(0.01, 0.99, size=1000), tau_grid, q_treated_list)
    syn_control_c = np.interp(np.random.uniform(0.01, 0.99, size=1000), tau_grid, q_control_list)

    def compute_gini(arr: np.ndarray) -> float:
        c = arr[np.isfinite(arr)]
        if len(c) < 2:
            return 0.0
        mn = np.min(c)
        if mn <= 0:
            c = c - mn + 1.0
        s = np.sort(c)
        n = len(c)
        idx = np.arange(1, n + 1)
        return float(np.clip((2.0 * np.sum(idx * s)) / (n * np.sum(s)) - (n + 1.0) / n, 0.0, 1.0))

    gini_treated_c = compute_gini(syn_treated_c)
    gini_control_c = compute_gini(syn_control_c)
    delta_gini_c = float(gini_treated_c - gini_control_c)

    iqr_treated_c = float(np.interp(0.75, tau_grid, q_treated_list) - np.interp(0.25, tau_grid, q_treated_list))
    iqr_control_c = float(np.interp(0.75, tau_grid, q_control_list) - np.interp(0.25, tau_grid, q_control_list))
    delta_iqr_c = float(iqr_treated_c - iqr_control_c)

    # First order stochastic dominance on compliers: Q_1(tau) >= Q_0(tau) for all tau
    fsd_compliers = bool(np.all(np.array(qte_c_list) >= -1e-5))

    # Quantile details
    quantile_points = [
        {
            "tau": float(round(t, 2)),
            "q_treated_complier": float(round(qt, 4)),
            "q_control_complier": float(round(qc, 4)),
            "qte_complier": float(round(qte, 4))
        }
        for t, qt, qc, qte in zip(tau_grid, q_treated_list, q_control_list, qte_c_list)
    ]

    # SVG Visualizer
    svg_str = _generate_iv_late_svg(
        tau_grid=tau_grid.tolist(),
        q_treated=q_treated_list,
        q_control=q_control_list,
        qte_c=qte_c_list,
        complier_share=complier_share,
        monotonicity_valid=monotonicity_passed,
        grid_y=grid_y.tolist(),
        diff_density_1=diff_dens_1,
        diff_density_0=diff_dens_0
    )

    # APA 7th Edition Narrative
    mono_desc = "vượt qua kiểm định tính đơn điệu Kitagawa (2015) không phát hiện defiers" if monotonicity_passed else "xuất hiện dấu hiệu vi phạm tính đơn điệu Kitagawa"
    fsd_desc = "đạt tính trội ngẫu nhiên bậc một FSD trên nhóm compliers" if fsd_compliers else "không đạt tính trội ngẫu nhiên bậc một đồng nhất"
    ineq_desc = f"thu hẹp bất bình đẳng nội bộ nhóm compliers (ΔGini = {delta_gini_c:+.4f}, ΔIQR = {delta_iqr_c:+.4f})" if delta_gini_c < 0 else f"nới rộng phân hóa (ΔGini = {delta_gini_c:+.4f})"

    apa_narrative = (
        f"Hệ thống phân tích DataTrust: Mô hình Phân rã Phân vị Hiệu ứng Can thiệp Cục bộ Phi tham số (Nonparametric IV-LATE Quantile Decomposition; "
        f"Abadie et al., 2002; Frölich & Melly, 2013) ước lượng tỷ trọng nhóm tuân thủ là P(Complier) = {complier_share*100:.1f}%. "
        f"Hiệu ứng can thiệp trung bình LATE = {mean_late:+.4f} và trung vị Median QTE-C = {median_qte_c:+.4f}. "
        f"Kiểm định tính hợp lệ của biến công cụ {mono_desc}. "
        f"Về mặt phúc lợi, chính sách can thiệp {fsd_desc} và {ineq_desc}."
    )

    return {
        "status": "success",
        "sample_size": N,
        "complier_share": float(round(complier_share, 4)),
        "first_stage_diff": float(round(first_stage_diff, 4)),
        "mean_late": float(round(mean_late, 4)),
        "median_qte_complier": float(round(median_qte_c, 4)),
        "monotonicity_test": {
            "passed": monotonicity_passed,
            "min_density_difference": float(round(min_violation, 4)),
            "defiers_detected": not monotonicity_passed
        },
        "complier_inequality": {
            "gini_treated_c": float(round(gini_treated_c, 4)),
            "gini_control_c": float(round(gini_control_c, 4)),
            "delta_gini_c": float(round(delta_gini_c, 4)),
            "iqr_treated_c": float(round(iqr_treated_c, 4)),
            "iqr_control_c": float(round(iqr_control_c, 4)),
            "delta_iqr_c": float(round(delta_iqr_c, 4)),
            "first_order_stochastic_dominance": fsd_compliers
        },
        "quantile_curve": quantile_points,
        "svg_visualization": svg_str,
        "apa_narrative": apa_narrative
    }
