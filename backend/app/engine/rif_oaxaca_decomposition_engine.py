"""
DataTrust - Recentered Influence Function (RIF) Regression & Distributional Oaxaca-Blinder Decomposition Engine
Scientific References:
- Firpo, S., Fortin, N. M., & Lemieux, T. (2009). "Unconditional Quantile Regressions." Econometrica, 77(3), 953-973.
- Firpo, S., Fortin, N. M., & Lemieux, T. (2018). "Decomposing Wage Distributions Using Recentered Influence Function Regressions." Econometrics, 6(2), 28.
- Oaxaca, R. (1973). "Male-Female Wage Differentials in Urban Labor Markets." International Economic Review, 14(3), 693-709.
- Blinder, A. S. (1973). "Wage Discrimination: Reduced Form and Structural Estimates." Journal of Human Resources, 8(4), 436-455.
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from scipy import stats


def compute_rif_quantile(y: np.ndarray, tau: float) -> Tuple[float, np.ndarray, float]:
    """
    Computes the Recentered Influence Function (RIF) for the tau-th quantile of y.
    RIF(y; q_tau) = q_tau + (tau - 1(y <= q_tau)) / f_y(q_tau)
    """
    n = len(y)
    q_tau = float(np.percentile(y, tau * 100.0))
    std_y = float(np.std(y, ddof=1)) if n > 1 else 1.0
    iqr_y = float(stats.iqr(y))

    # Silverman's rule of thumb bandwidth
    if iqr_y > 1e-6 and std_y > 1e-6:
        h = 0.9 * min(std_y, iqr_y / 1.34) * (n ** (-0.2))
    elif std_y > 1e-6:
        h = 1.06 * std_y * (n ** (-0.2))
    else:
        h = 0.1
    h = max(h, 1e-4)

    # Gaussian kernel density at q_tau
    u = (y - q_tau) / h
    f_q = float(np.mean(stats.norm.pdf(u)) / h)
    f_q = max(f_q, 1e-6)

    indicator = (y <= q_tau).astype(float)
    rif = q_tau + (tau - indicator) / f_q
    return q_tau, rif, f_q


def run_rif_oaxaca_decomposition(
    records: List[Dict[str, Any]],
    group_col: str,
    outcome_col: str,
    covariate_cols: List[str],
    reference_group_val: Optional[Any] = None,
    target_quantiles: Optional[List[float]] = None,
    num_bootstrap_reps: int = 100,
    alpha_level: float = 0.05
) -> Dict[str, Any]:
    """
    Executes Distributional Oaxaca-Blinder RIF Decomposition across quantiles.
    Decomposes total gap into:
      - Endowment / Composition Effect (Explained)
      - Coefficient / Structure Effect (Unexplained)
    """
    if target_quantiles is None or len(target_quantiles) == 0:
        target_quantiles = [0.10, 0.25, 0.50, 0.75, 0.90]
    target_quantiles = sorted(list(set([round(q, 2) for q in target_quantiles if 0.01 <= q <= 0.99])))

    # 1. Clean records
    valid_rows = []
    for r in records:
        g_raw = r.get(group_col)
        y_raw = r.get(outcome_col)
        if g_raw is None or y_raw is None:
            continue
        try:
            y_val = float(y_raw)
            if np.isnan(y_val) or np.isinf(y_val):
                continue
            
            # Check covariates
            x_vals = []
            valid_x = True
            for c in covariate_cols:
                cv = r.get(c)
                if cv is None:
                    valid_x = False
                    break
                try:
                    xv = float(cv)
                    if np.isnan(xv) or np.isinf(xv):
                        valid_x = False
                        break
                    x_vals.append(xv)
                except (ValueError, TypeError):
                    valid_x = False
                    break
            if not valid_x:
                continue

            valid_rows.append({
                "group": str(g_raw).strip(),
                "outcome": y_val,
                "covariates": x_vals
            })
        except (ValueError, TypeError):
            continue

    if len(valid_rows) < 30:
        return {
            "status": "error",
            "message": f"Số lượng bản ghi hợp lệ ({len(valid_rows)}) quá ít, yêu cầu tối thiểu 30 bản ghi có đầy đủ biến."
        }

    # 2. Identify Group A (Reference) vs Group B (Comparison)
    unique_groups = list(set(r["group"] for r in valid_rows))
    if len(unique_groups) < 2:
        return {
            "status": "error",
            "message": f"Biến phân nhóm chỉ có 1 giá trị ('{unique_groups[0]}'). Cần đúng 2 nhóm để so sánh phân rã."
        }
    
    if reference_group_val is not None and str(reference_group_val).strip() in unique_groups:
        group_A_label = str(reference_group_val).strip()
        remaining = [g for g in unique_groups if g != group_A_label]
        group_B_label = remaining[0]
    else:
        # Default: first group is A, second is B
        # Or if 1 and 0, 1 is A, 0 is B
        if "1" in unique_groups and "0" in unique_groups:
            group_A_label = "1"
            group_B_label = "0"
        else:
            sorted_groups = sorted(unique_groups)
            group_A_label = sorted_groups[0]
            group_B_label = sorted_groups[1]

    rows_A = [r for r in valid_rows if r["group"] == group_A_label]
    rows_B = [r for r in valid_rows if r["group"] == group_B_label]

    if len(rows_A) < 15 or len(rows_B) < 15:
        return {
            "status": "error",
            "message": f"Mỗi nhóm cần tối thiểu 15 quan sát (Nhóm A '{group_A_label}': {len(rows_A)}, Nhóm B '{group_B_label}': {len(rows_B)})."
        }

    N_A = len(rows_A)
    N_B = len(rows_B)
    N_total = N_A + N_B
    K = len(covariate_cols)

    Y_A = np.array([r["outcome"] for r in rows_A])
    Y_B = np.array([r["outcome"] for r in rows_B])

    # Design matrix: prepend intercept column
    X_A = np.column_stack([np.ones(N_A)] + [np.array([r["covariates"][k] for r in rows_A]) for k in range(K)])
    X_B = np.column_stack([np.ones(N_B)] + [np.array([r["covariates"][k] for r in rows_B]) for k in range(K)])

    col_names = ["Intercept"] + list(covariate_cols)

    # 3. Overall Mean Decomposition (Classic Oaxaca-Blinder benchmark)
    mean_A = float(np.mean(Y_A))
    mean_B = float(np.mean(Y_B))
    mean_gap = mean_A - mean_B

    beta_A = np.linalg.lstsq(X_A, Y_A, rcond=None)[0]
    beta_B = np.linalg.lstsq(X_B, Y_B, rcond=None)[0]

    X_bar_A = np.mean(X_A, axis=0)
    X_bar_B = np.mean(X_B, axis=0)

    # Two-fold decomposition:
    # Explained (Endowments): (X_bar_A - X_bar_B) * beta_B
    # Unexplained (Coefficients): X_bar_A * (beta_A - beta_B)
    explained_mean_vec = (X_bar_A - X_bar_B) * beta_B
    unexplained_mean_vec = X_bar_A * (beta_A - beta_B)
    explained_mean_total = float(np.sum(explained_mean_vec))
    unexplained_mean_total = float(np.sum(unexplained_mean_vec))

    # 4. RIF Quantile Decompositions across target quantiles
    quantile_results = []
    # Store median detailed decomposition for KPI display
    median_detailed = None

    for tau in target_quantiles:
        q_A, rif_A, f_A = compute_rif_quantile(Y_A, tau)
        q_B, rif_B, f_B = compute_rif_quantile(Y_B, tau)
        tot_gap = q_A - q_B

        # OLS of RIF on X
        gamma_A = np.linalg.lstsq(X_A, rif_A, rcond=None)[0]
        gamma_B = np.linalg.lstsq(X_B, rif_B, rcond=None)[0]

        exp_vec = (X_bar_A - X_bar_B) * gamma_B
        unexp_vec = X_bar_A * (gamma_A - gamma_B)

        exp_tot = float(np.sum(exp_vec))
        unexp_tot = float(np.sum(unexp_vec))

        exp_pct = float((exp_tot / tot_gap) * 100.0) if abs(tot_gap) > 1e-6 else 0.0
        unexp_pct = float((unexp_tot / tot_gap) * 100.0) if abs(tot_gap) > 1e-6 else 0.0

        detail_items = []
        for idx_c, c_name in enumerate(col_names):
            detail_items.append({
                "variable_name": c_name,
                "mean_group_a": round(float(X_bar_A[idx_c]), 3),
                "mean_group_b": round(float(X_bar_B[idx_c]), 3),
                "mean_diff": round(float(X_bar_A[idx_c] - X_bar_B[idx_c]), 3),
                "explained_effect": round(float(exp_vec[idx_c]), 4),
                "unexplained_effect": round(float(unexp_vec[idx_c]), 4),
                "total_effect": round(float(exp_vec[idx_c] + unexp_vec[idx_c]), 4)
            })

        if abs(tau - 0.50) < 1e-4:
            median_detailed = detail_items

        quantile_results.append({
            "quantile": round(tau, 2),
            "group_a_val": round(q_A, 3),
            "group_b_val": round(q_B, 3),
            "total_gap": round(tot_gap, 4),
            "explained_gap": round(exp_tot, 4),
            "unexplained_gap": round(unexp_tot, 4),
            "explained_pct": round(exp_pct, 1),
            "unexplained_pct": round(unexp_pct, 1),
            "detailed_contributions": detail_items
        })

    if median_detailed is None and len(quantile_results) > 0:
        median_detailed = quantile_results[len(quantile_results) // 2]["detailed_contributions"]

    # 5. Bootstrap Standard Errors for Median Quantile (tau = 0.50)
    B = max(20, min(num_bootstrap_reps, 150))
    boot_gaps = []
    boot_exps = []
    boot_unexps = []
    np.random.seed(987)

    for b in range(B):
        idx_A_b = np.random.choice(N_A, size=N_A, replace=True)
        idx_B_b = np.random.choice(N_B, size=N_B, replace=True)

        Y_A_b, X_A_b = Y_A[idx_A_b], X_A[idx_A_b, :]
        Y_B_b, X_B_b = Y_B[idx_B_b], X_B[idx_B_b, :]

        try:
            q_A_b, rif_A_b, _ = compute_rif_quantile(Y_A_b, 0.50)
            q_B_b, rif_B_b, _ = compute_rif_quantile(Y_B_b, 0.50)
            g_b = q_A_b - q_B_b

            g_A_b = np.linalg.lstsq(X_A_b, rif_A_b, rcond=None)[0]
            g_B_b = np.linalg.lstsq(X_B_b, rif_B_b, rcond=None)[0]

            xb_A_b = np.mean(X_A_b, axis=0)
            xb_B_b = np.mean(X_B_b, axis=0)

            e_b = np.sum((xb_A_b - xb_B_b) * g_B_b)
            u_b = np.sum(xb_A_b * (g_A_b - g_B_b))

            boot_gaps.append(g_b)
            boot_exps.append(e_b)
            boot_unexps.append(u_b)
        except Exception:
            continue

    if len(boot_gaps) > 10:
        se_gap = float(np.std(boot_gaps, ddof=1))
        se_exp = float(np.std(boot_exps, ddof=1))
        se_unexp = float(np.std(boot_unexps, ddof=1))
    else:
        se_gap = 0.1
        se_exp = 0.1
        se_unexp = 0.1

    z_crit = float(stats.norm.ppf(1.0 - alpha_level / 2.0))
    # Median gap metrics
    med_res = [qr for qr in quantile_results if abs(qr["quantile"] - 0.50) < 1e-4]
    med_item = med_res[0] if med_res else quantile_results[len(quantile_results) // 2]
    med_tot = med_item["total_gap"]
    med_exp = med_item["explained_gap"]
    med_unexp = med_item["unexplained_gap"]

    z_unexp = float(med_unexp / se_unexp) if se_unexp > 1e-8 else 0.0
    p_unexp = float(2.0 * (1.0 - stats.norm.cdf(abs(z_unexp))))

    # 6. Glass Ceiling / Sticky Floor Diagnostics
    # Compare gap at 90th percentile vs 10th percentile
    p10_res = [qr for qr in quantile_results if abs(qr["quantile"] - 0.10) < 1e-4]
    p90_res = [qr for qr in quantile_results if abs(qr["quantile"] - 0.90) < 1e-4]
    gap_10 = p10_res[0]["total_gap"] if p10_res else (quantile_results[0]["total_gap"] if quantile_results else 0.0)
    gap_90 = p90_res[0]["total_gap"] if p90_res else (quantile_results[-1]["total_gap"] if quantile_results else 0.0)

    glass_ceiling_diff = round(gap_90 - gap_10, 4)
    if gap_90 > gap_10 * 1.25 and gap_90 > 0:
        ceiling_diagnostic = "Glass Ceiling Effect (Khoảng cách nới rộng mạnh mẽ ở phân vị trên 90th percentile)"
    elif gap_10 > gap_90 * 1.25 and gap_10 > 0:
        ceiling_diagnostic = "Sticky Floor Effect (Khoảng cách tập trung nặng nề ở phân vị đáy 10th percentile)"
    else:
        ceiling_diagnostic = "Uniform Distributional Gap (Khoảng cách tương đối đồng đều xuyên suốt các phân vị)"

    # 7. Dual-Panel SVG Visualization
    svg_viz = generate_rif_svg(
        quantile_results=quantile_results,
        detailed_covariates=median_detailed or [],
        group_A_label=group_A_label,
        group_B_label=group_B_label
    )

    # 8. APA 7th Narrative
    apa_narrative = generate_rif_apa_narrative(
        group_A_label=group_A_label,
        group_B_label=group_B_label,
        n_a=N_A,
        n_b=N_B,
        mean_gap=mean_gap,
        exp_mean=explained_mean_total,
        unexp_mean=unexplained_mean_total,
        med_gap=med_tot,
        med_exp=med_exp,
        med_unexp=med_unexp,
        se_unexp=se_unexp,
        z_unexp=z_unexp,
        p_unexp=p_unexp,
        gap_10=gap_10,
        gap_90=gap_90,
        ceiling_diag=ceiling_diagnostic,
        detailed_covariates=median_detailed or []
    )

    return {
        "status": "success",
        "sample_size": N_total,
        "group_a_label": group_A_label,
        "group_b_label": group_B_label,
        "sample_counts": {
            "group_a_n": N_A,
            "group_b_n": N_B
        },
        "mean_decomposition": {
            "group_a_mean": round(mean_A, 3),
            "group_b_mean": round(mean_B, 3),
            "total_mean_gap": round(mean_gap, 4),
            "explained_endowments": round(explained_mean_total, 4),
            "unexplained_coefficients": round(unexplained_mean_total, 4),
            "explained_pct": round((explained_mean_total / mean_gap * 100.0) if abs(mean_gap) > 1e-6 else 0.0, 1),
            "unexplained_pct": round((unexplained_mean_total / mean_gap * 100.0) if abs(mean_gap) > 1e-6 else 0.0, 1)
        },
        "median_rif_estimates": {
            "total_median_gap": round(med_tot, 4),
            "explained_endowments": round(med_exp, 4),
            "unexplained_coefficients": round(med_unexp, 4),
            "unexplained_se": round(se_unexp, 4),
            "unexplained_ci_95": [round(med_unexp - z_crit * se_unexp, 4), round(med_unexp + z_crit * se_unexp, 4)],
            "unexplained_z_stat": round(z_unexp, 3),
            "unexplained_p_value": round(p_unexp, 5),
            "is_significant": bool(p_unexp < alpha_level),
            "explained_pct": med_item["explained_pct"],
            "unexplained_pct": med_item["unexplained_pct"]
        },
        "glass_ceiling_diagnostics": {
            "gap_p10": round(gap_10, 4),
            "gap_p90": round(gap_90, 4),
            "gap_p90_minus_p10": glass_ceiling_diff,
            "diagnostic_label": ceiling_diagnostic
        },
        "quantile_decomposition_curve": quantile_results,
        "detailed_covariates": median_detailed or [],
        "svg_visualization": svg_viz,
        "apa_narrative": apa_narrative
    }


def generate_rif_svg(
    quantile_results: List[Dict[str, Any]],
    detailed_covariates: List[Dict[str, Any]],
    group_A_label: str,
    group_B_label: str
) -> str:
    """Generates a responsive dual-panel SVG for RIF quantile curve and covariate breakdown."""
    width = 960
    height = 360

    # Panel A: Quantile Gap Curve (x: 50, y: 50, w: 450, h: 240)
    p1_x = 55
    p1_y = 50
    p1_w = 440
    p1_h = 240

    all_gaps = []
    for qr in quantile_results:
        all_gaps.extend([qr["total_gap"], qr["explained_gap"], qr["unexplained_gap"]])
    all_gaps.append(0.0)
    min_y = min(all_gaps)
    max_y = max(all_gaps)
    yrange = max_y - min_y
    if yrange < 1e-4:
        yrange = 1.0
    ypad = yrange * 0.15
    y_min_plot = min_y - ypad
    y_max_plot = max_y + ypad
    plot_h = y_max_plot - y_min_plot

    num_pts = len(quantile_results)
    x_step = p1_w / max(1, num_pts - 1)

    def get_x(idx: int) -> float:
        return p1_x + idx * x_step

    def get_y(val: float) -> float:
        r = (val - y_min_plot) / plot_h
        return p1_y + p1_h - r * p1_h

    tot_pts = []
    exp_pts = []
    unexp_pts = []
    for i, qr in enumerate(quantile_results):
        px = get_x(i)
        tot_pts.append(f"{px:.1f},{get_y(qr['total_gap']):.1f}")
        exp_pts.append(f"{px:.1f},{get_y(qr['explained_gap']):.1f}")
        unexp_pts.append(f"{px:.1f},{get_y(qr['unexplained_gap']):.1f}")

    tot_polyline = " ".join(tot_pts)
    exp_polyline = " ".join(exp_pts)
    unexp_polyline = " ".join(unexp_pts)

    y_zero = get_y(0.0)

    # Panel B: Detailed Covariate Contribution Bar Chart (x: 550, y: 50, w: 360, h: 240)
    p2_x = 560
    p2_y = 50
    p2_w = 340
    p2_h = 240

    cov_items = [c for c in detailed_covariates if c["variable_name"] != "Intercept"]
    if not cov_items:
        cov_items = detailed_covariates[:4]

    max_c_val = max((abs(c["explained_effect"]) + abs(c["unexplained_effect"]) for c in cov_items), default=1.0)
    if max_c_val < 1e-4:
        max_c_val = 1.0

    bars_svg = []
    bar_h = 18
    gap_b = 14
    for idx, c in enumerate(cov_items[:6]):
        by = p2_y + idx * (bar_h + gap_b) + 12
        w_exp = (abs(c["explained_effect"]) / max_c_val) * (p2_w * 0.38)
        w_unexp = (abs(c["unexplained_effect"]) / max_c_val) * (p2_w * 0.38)

        # Truncate variable name
        v_name = c["variable_name"][:12]

        bars_svg.append(f"""
        <g>
          <text x="{p2_x}" y="{by + 13}" font-size="11" font-family="sans-serif" fill="#475569" font-weight="600">{v_name}</text>
          <!-- Explained Bar (Teal) -->
          <rect x="{p2_x + 90}" y="{by}" width="{max(2.0, w_exp):.1f}" height="{bar_h}" rx="3" fill="#0d9488" opacity="0.85" />
          <!-- Unexplained Bar (Rose) -->
          <rect x="{p2_x + 95 + max(2.0, w_exp):.1f}" y="{by}" width="{max(2.0, w_unexp):.1f}" height="{bar_h}" rx="3" fill="#e11d48" opacity="0.85" />
          <text x="{p2_x + 105 + max(2.0, w_exp) + max(2.0, w_unexp):.1f}" y="{by + 13}" font-size="10" font-family="sans-serif" fill="#334155" font-weight="bold">
            {c['total_effect']:+.2f}
          </text>
        </g>
        """)

    bars_markup = "".join(bars_svg)

    svg = f"""<svg viewBox="0 0 {width} {height}" class="w-full h-auto select-none font-sans" xmlns="http://www.w3.org/2000/svg">
  <rect width="{width}" height="{height}" fill="#f8fafc" rx="12" />

  <!-- Panel A: Quantile Decomposition Curve -->
  <g id="panel-curve">
    <text x="{p1_x}" y="30" font-size="13" font-weight="bold" fill="#0f172a">Đường cong Phân rã Chênh lệch Phân vị (RIF Quantiles: {group_A_label} - {group_B_label})</text>
    
    <!-- Zero axis -->
    <line x1="{p1_x}" y1="{y_zero:.1f}" x2="{p1_x + p1_w}" y2="{y_zero:.1f}" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="3,3" />

    <!-- Grid box -->
    <rect x="{p1_x}" y="{p1_y}" width="{p1_w}" height="{p1_h}" fill="none" stroke="#e2e8f0" stroke-width="1" />

    <!-- Unexplained Curve (Rose) -->
    <polyline fill="none" stroke="#e11d48" stroke-width="2.5" stroke-dasharray="4,3" points="{unexp_polyline}" />

    <!-- Explained Curve (Teal) -->
    <polyline fill="none" stroke="#0d9488" stroke-width="2.5" stroke-dasharray="3,3" points="{exp_polyline}" />

    <!-- Total Gap Curve (Indigo Bold) -->
    <polyline fill="none" stroke="#4f46e5" stroke-width="3.5" points="{tot_polyline}" />

    <!-- X Ticks -->
    {''.join([f'<text x="{get_x(i):.1f}" y="{p1_y + p1_h + 18}" font-size="11" text-anchor="middle" fill="#64748b font-weight="600">p{int(qr["quantile"]*100)}</text>' for i, qr in enumerate(quantile_results)])}

    <!-- Panel A Legend -->
    <g transform="translate({p1_x}, {p1_y + p1_h + 38})">
      <line x1="0" y1="0" x2="16" y2="0" stroke="#4f46e5" stroke-width="3" />
      <text x="22" y="4" font-size="11" fill="#1e293b" font-weight="600">Tổng chênh lệch (Total Gap)</text>

      <line x1="170" y1="0" x2="186" y2="0" stroke="#0d9488" stroke-width="2.5" stroke-dasharray="3,3" />
      <text x="192" y="4" font-size="11" fill="#1e293b" font-weight="600">Đặc điểm (Explained)</text>

      <line x1="320" y1="0" x2="336" y2="0" stroke="#e11d48" stroke-width="2.5" stroke-dasharray="4,3" />
      <text x="342" y="4" font-size="11" fill="#1e293b" font-weight="600">Hệ số (Unexplained)</text>
    </g>
  </g>

  <!-- Panel B: Covariate Contribution Bars -->
  <g id="panel-covariates">
    <text x="{p2_x}" y="30" font-size="13" font-weight="bold" fill="#0f172a">Phân rã Đóng góp của Biến (Covariates at Median)</text>
    <line x1="{p2_x}" y1="{p2_y + p2_h}" x2="{p2_x + p2_w}" y2="{p2_y + p2_h}" stroke="#cbd5e1" stroke-width="1" />
    {bars_markup}
    <!-- Panel B Legend -->
    <g transform="translate({p2_x}, {p2_y + p2_h + 15})">
      <rect x="0" y="-4" width="12" height="12" rx="2" fill="#0d9488" />
      <text x="16" y="6" font-size="11" fill="#475569">Explained (Đặc điểm)</text>

      <rect x="150" y="-4" width="12" height="12" rx="2" fill="#e11d48" />
      <text x="166" y="6" font-size="11" fill="#475569">Unexplained (Định giá)</text>
    </g>
  </g>
</svg>"""
    return svg.strip()


def generate_rif_apa_narrative(
    group_A_label: str,
    group_B_label: str,
    n_a: int,
    n_b: int,
    mean_gap: float,
    exp_mean: float,
    unexp_mean: float,
    med_gap: float,
    med_exp: float,
    med_unexp: float,
    se_unexp: float,
    z_unexp: float,
    p_unexp: float,
    gap_10: float,
    gap_90: float,
    ceiling_diag: str,
    detailed_covariates: List[Dict[str, Any]]
) -> str:
    """Formats standard APA 7th scientific report for RIF Oaxaca-Blinder."""
    p_str = "p < .001" if p_unexp < 0.001 else f"p = {p_unexp:.3f}"
    sig_str = "đạt mức ý nghĩa thống kê cao" if p_unexp < 0.01 else ("đạt ý nghĩa thống kê" if p_unexp < 0.05 else "không đạt mức ý nghĩa thống kê quy ước")

    top_covs = [c for c in detailed_covariates if c["variable_name"] != "Intercept"]
    top_covs.sort(key=lambda x: abs(x["total_effect"]), reverse=True)
    cov_summary = ", ".join([f"{c['variable_name']} (Δ = {c['total_effect']:+.3f})" for c in top_covs[:3]])

    exp_pct = (med_exp / med_gap * 100.0) if abs(med_gap) > 1e-6 else 0.0
    unexp_pct = (med_unexp / med_gap * 100.0) if abs(med_gap) > 1e-6 else 0.0

    narrative = (
        f"Phân tích phân rã chênh lệch phân phối bằng phương pháp Recentered Influence Function "
        f"(RIF Oaxaca-Blinder; Firpo, Fortin, & Lemieux, 2009, 2018) giữa Nhóm A ({group_A_label}, N = {n_a}) "
        f"và Nhóm B ({group_B_label}, N = {n_b}) cho thấy: "
        f"Chênh lệch trung bình tổng thể đạt Δ_Mean = {mean_gap:.4f}, trong đó thành phần đặc điểm được giải thích "
        f"(Endowments/Composition) đóng góp {exp_mean:.4f} và thành phần hệ số chưa giải thích (Wage Structure/Coefficients) đóng góp {unexp_mean:.4f}.\n\n"
        f"Tại điểm trung vị (Median, 50th percentile), tổng chênh lệch đạt Δ_Median = {med_gap:.4f}. "
        f"Phương pháp hồi quy RIF bóc tách thành phần đặc điểm giải thích được Δ_X = {med_exp:.4f} ({exp_pct:.1f}% tổng khoảng cách), "
        f"trong khi phần chênh lệch do định giá khác biệt (Unexplained Structure Effect) đạt Δ_S = {med_unexp:.4f} ({unexp_pct:.1f}%), "
        f"với sai số chuẩn Bootstrap SE = {se_unexp:.4f} (z = {z_unexp:.2f}, {p_str}), {sig_str} ở mức α = 0.05.\n\n"
        f"Chẩn đoán hiệu ứng trần kính (Glass Ceiling Diagnostic): Khoảng cách chênh lệch tại phân vị thứ 10 đạt {gap_10:.4f}, "
        f"trong khi tại phân vị thứ 90 đạt {gap_90:.4f} (độ dốc chênh lệch Δ_90-10 = {gap_90 - gap_10:+.4f}), "
        f"chỉ ra hình thái {ceiling_diag}. "
        f"Các biến kiểm soát đóng góp tỷ trọng lớn nhất vào khoảng cách trung vị bao gồm: {cov_summary}."
    )
    return narrative
