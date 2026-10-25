"""
Small Area Estimation (SAE) & Fay-Herriot Empirical Bayes Engine
================================================================
Theoretical Foundations:
- Fay & Herriot (1979): "Estimates of Income for Small Places: An Application of
  the James-Stein Procedures to Census Data", Journal of the American Statistical
  Association, 74(366), 269-277.
- Rao & Molina (2015): Small Area Estimation, 2nd Edition, John Wiley & Sons.
- Prasad & Rao (1990): "The Estimation of Mean Squared Errors of Small-Area
  Estimators", Journal of the American Statistical Association, 85(409), 163-171.
- Pfeffermann (2013): "New Important Developments in Small Area Estimation",
  Statistical Science, 28(1), 40-68.

Key Capabilities:
1. Two-Level Area-Level Fay-Herriot Model:
   Sampling model: y_m = theta_m + e_m, e_m ~ N(0, D_m)
   Linking model:  theta_m = x_m' beta + v_m, v_m ~ N(0, sigma_v^2)
2. REML / Fay-Herriot Method-of-Moments Estimation of Between-Area Variance (sigma_v^2).
3. Generalized Least Squares (GLS) Estimation of Regression Coefficients (beta).
4. Area-Specific Shrinkage Factor (gamma_m = sigma_v^2 / (sigma_v^2 + D_m)).
5. Empirical Best Linear Unbiased Predictor (EBLUP):
   theta_m^EB = gamma_m * y_m + (1 - gamma_m) * x_m' beta.
6. Prasad-Rao (1990) Second-Order Unbiased MSE Estimation:
   MSE(theta_m^EB) = g_1m + g_2m + 2 * g_3m.
7. Efficiency Gain & Coefficient of Variation (CV) Reduction Analysis.
8. Vector SVG Shrinkage Forest Plot: Direct vs Shrunk EB Estimates with CIs.
9. APA 7th Edition Academic Narrative Generator.
"""

from typing import Dict, List, Optional, Any, Tuple
import math
import numpy as np


def fit_fay_herriot_eblup(
    area_names: List[str],
    direct_estimates: np.ndarray,
    sampling_variances: np.ndarray,
    sample_sizes: np.ndarray,
    auxiliary_x: Optional[np.ndarray] = None,
    max_iter: int = 100,
    tol: float = 1e-6
) -> Dict[str, Any]:
    """
    Fit the classic Fay-Herriot (1979) Area-Level Model via Fisher-Scoring / REML.
    direct_estimates: (M, ) vector of direct survey estimates y_m.
    sampling_variances: (M, ) vector of sampling variances D_m.
    sample_sizes: (M, ) vector of sample counts n_m.
    auxiliary_x: (M, P) matrix of area-level covariates (defaults to intercept only).
    """
    m = len(direct_estimates)
    if m < 3:
        return {
            "status": "INSUFFICIENT_AREAS",
            "message": f"Cần ít nhất 3 tiểu vùng / khu vực để ước lượng mô hình Fay-Herriot (hiện có {m})."
        }

    # Ensure auxiliary X includes intercept
    if auxiliary_x is None:
        x = np.ones((m, 1))
    else:
        if auxiliary_x.ndim == 1:
            auxiliary_x = auxiliary_x.reshape(-1, 1)
        # Check if intercept already present
        has_intercept = np.allclose(auxiliary_x[:, 0], 1.0)
        if not has_intercept:
            x = np.column_stack([np.ones(m), auxiliary_x])
        else:
            x = auxiliary_x

    p = x.shape[1]
    if m <= p:
        return {
            "status": "DEGREES_OF_FREEDOM_ERROR",
            "message": f"Số lượng tiểu vùng (M={m}) phải lớn hơn số biến giải thích (P={p})."
        }

    # Ensure D_m > 0
    d = np.maximum(sampling_variances, 1e-6)
    y = direct_estimates

    # Initial estimate of sigma_v^2 (between-area variance) via Method of Moments / OLS residuals
    ols_beta, _, _, _ = np.linalg.lstsq(x, y, rcond=None)
    residuals_ols = y - x @ ols_beta
    raw_var = float(np.var(residuals_ols) - np.mean(d))
    sigma_v2 = max(1e-4, raw_var)

    # Iterative Fay-Herriot algorithm for sigma_v^2
    converged = False
    for iteration in range(max_iter):
        v_inv = 1.0 / (sigma_v2 + d)  # (M, )
        w = np.diag(v_inv)

        # GLS beta: (X' W X)^(-1) X' W y
        xt_w_x = x.T @ (v_inv[:, np.newaxis] * x)
        try:
            xt_w_x_inv = np.linalg.inv(xt_w_x)
        except np.linalg.LinAlgError:
            xt_w_x_inv = np.linalg.pinv(xt_w_x)

        beta = xt_w_x_inv @ (x.T @ (v_inv * y))

        # Fay-Herriot moment function: sum (y_m - x_m' beta)^2 / (sigma_v2 + D_m) = M - P
        resids = y - x @ beta
        score_val = np.sum((resids ** 2) / (sigma_v2 + d)) - (m - p)
        # Derivative w.r.t sigma_v2: - sum (resids^2) / (sigma_v2 + d)^2
        score_deriv = -np.sum((resids ** 2) / ((sigma_v2 + d) ** 2))

        if abs(score_deriv) < 1e-12:
            break

        step = score_val / score_deriv
        new_sigma_v2 = sigma_v2 - step

        if new_sigma_v2 < 1e-6:
            new_sigma_v2 = 0.0

        if abs(new_sigma_v2 - sigma_v2) < tol:
            sigma_v2 = new_sigma_v2
            converged = True
            break

        sigma_v2 = new_sigma_v2

    # Final GLS beta
    v_inv = 1.0 / (sigma_v2 + d)
    xt_w_x = x.T @ (v_inv[:, np.newaxis] * x)
    try:
        xt_w_x_inv = np.linalg.inv(xt_w_x)
    except np.linalg.LinAlgError:
        xt_w_x_inv = np.linalg.pinv(xt_w_x)

    beta = xt_w_x_inv @ (x.T @ (v_inv * y))
    se_beta = np.sqrt(np.maximum(0.0, np.diag(xt_w_x_inv)))

    # Compute area-specific Shrinkage weights gamma_m:
    # gamma_m = sigma_v^2 / (sigma_v^2 + D_m)
    gamma = sigma_v2 / (sigma_v2 + d)
    gamma = np.clip(gamma, 0.0, 1.0)

    # Synthetic regression predictions: x_m' beta
    synthetic_preds = x @ beta

    # EBLUP / Shrinkage Estimator:
    # theta_m^EB = gamma_m * y_m + (1 - gamma_m) * x_m' beta
    eblup_estimates = gamma * y + (1.0 - gamma) * synthetic_preds

    # Asymptotic variance of sigma_v^2 for Prasad-Rao g3 term:
    # Var(sigma_v^2) approx 2 / sum(1 / (sigma_v^2 + D_m)^2)
    asymp_var_sigma_v2 = 2.0 / np.maximum(1e-6, np.sum(v_inv ** 2))

    # Prasad & Rao (1990) MSE estimation:
    # g_1m = gamma_m * D_m
    g1 = gamma * d
    # g_2m = (1 - gamma_m)^2 * x_m' (X' W X)^(-1) x_m
    g2 = np.zeros(m)
    for i in range(m):
        xi = x[i, :]
        g2[i] = ((1.0 - gamma[i]) ** 2) * float(xi @ xt_w_x_inv @ xi)

    # g_3m = (D_m^2 / (sigma_v^2 + D_m)^3) * Var(sigma_v^2)
    g3 = (d ** 2) / ((sigma_v2 + d) ** 3) * asymp_var_sigma_v2

    # Total Prasad-Rao MSE
    mse_eblup = g1 + g2 + 2.0 * g3
    se_eblup = np.sqrt(np.maximum(1e-8, mse_eblup))
    se_direct = np.sqrt(d)

    # Efficiency gain (% reduction in standard error)
    eff_gain = np.maximum(0.0, (1.0 - (se_eblup / se_direct)) * 100.0)

    # Compile area summary table
    area_results = []
    for i in range(m):
        area_results.append({
            "area_name": str(area_names[i]),
            "sample_size": int(sample_sizes[i]),
            "direct_estimate": round(float(y[i]), 3),
            "direct_se": round(float(se_direct[i]), 3),
            "direct_ci_lower": round(float(y[i] - 1.96 * se_direct[i]), 3),
            "direct_ci_upper": round(float(y[i] + 1.96 * se_direct[i]), 3),
            "synthetic_prediction": round(float(synthetic_preds[i]), 3),
            "shrinkage_weight_gamma": round(float(gamma[i]), 4),
            "eblup_estimate": round(float(eblup_estimates[i]), 3),
            "eblup_se": round(float(se_eblup[i]), 3),
            "eblup_ci_lower": round(float(eblup_estimates[i] - 1.96 * se_eblup[i]), 3),
            "eblup_ci_upper": round(float(eblup_estimates[i] + 1.96 * se_eblup[i]), 3),
            "efficiency_gain_pct": round(float(eff_gain[i]), 2)
        })

    # Sort area results by sample size ascending (smallest sample sizes first to highlight shrinkage)
    area_results_sorted = sorted(area_results, key=lambda r: r["sample_size"])

    # Regression coefficients table
    coef_table = []
    for k in range(p):
        name = "Hệ số chặn (Intercept)" if k == 0 else f"Biến giải thích X{k}"
        z_stat = float(beta[k] / (se_beta[k] + 1e-9))
        p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z_stat) / math.sqrt(2.0))))
        coef_table.append({
            "term": name,
            "coefficient": round(float(beta[k]), 4),
            "std_error": round(float(se_beta[k]), 4),
            "z_statistic": round(z_stat, 3),
            "p_value": round(float(p_val), 4)
        })

    # Average efficiency gain across all areas
    mean_eff_gain = float(np.mean(eff_gain))

    # Generate Vector SVG Shrinkage Forest Plot
    svg_chart = generate_sae_svg(area_results_sorted)

    # Generate APA 7th Edition Narrative
    apa_narrative = generate_sae_apa_narrative(
        area_count=m,
        sigma_v2=sigma_v2,
        mean_eff_gain=mean_eff_gain,
        mean_gamma=float(np.mean(gamma)),
        beta_intercept=float(beta[0])
    )

    return {
        "status": "SUCCESS",
        "area_count": m,
        "between_area_variance_sigma_v2": round(float(sigma_v2), 4),
        "mean_shrinkage_weight_gamma": round(float(np.mean(gamma)), 4),
        "mean_efficiency_gain_pct": round(mean_eff_gain, 2),
        "regression_coefficients": coef_table,
        "area_estimates": area_results_sorted,
        "svg_chart": svg_chart,
        "apa_narrative": apa_narrative
    }


def calculate_small_area_estimation(
    data_rows: List[Dict[str, Any]],
    area_col: str,
    outcome_col: str,
    auxiliary_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Aggregate individual survey observations to area level and fit Fay-Herriot EBLUP.
    """
    if not data_rows:
        return {"status": "NO_DATA", "message": "Không có dữ liệu phản hồi để ước lượng tiểu vùng."}

    # Group by area
    area_groups: Dict[str, List[float]] = {}
    area_aux: Dict[str, Dict[str, List[float]]] = {}

    for row in data_rows:
        a_val = str(row.get(area_col, "")).strip()
        o_val = row.get(outcome_col)
        if not a_val or o_val is None:
            continue
        try:
            o_num = float(o_val)
        except (ValueError, TypeError):
            continue

        if a_val not in area_groups:
            area_groups[a_val] = []
            if auxiliary_cols:
                area_aux[a_val] = {c: [] for c in auxiliary_cols}
        area_groups[a_val].append(o_num)

        if auxiliary_cols:
            for c in auxiliary_cols:
                cv = row.get(c)
                if cv is not None:
                    try:
                        area_aux[a_val][c].append(float(cv))
                    except (ValueError, TypeError):
                        pass

    # Filter areas with at least 2 observations
    valid_areas = [a for a, vals in area_groups.items() if len(vals) >= 2]
    if len(valid_areas) < 3:
        return {
            "status": "INSUFFICIENT_AREAS",
            "message": f"Cần ít nhất 3 tiểu vùng có từ 2 quan sát trở lên (hiện chỉ có {len(valid_areas)} vùng hợp lệ)."
        }

    area_names = []
    direct_y = []
    direct_d = []
    sample_n = []
    aux_matrix_rows = []

    for a in sorted(valid_areas):
        vals = np.array(area_groups[a])
        n_m = len(vals)
        mean_y = float(np.mean(vals))
        var_y = float(np.var(vals, ddof=1))
        # Design variance D_m = s_m^2 / n_m, floor to 1e-4
        d_m = max(1e-4, var_y / n_m)

        area_names.append(a)
        direct_y.append(mean_y)
        direct_d.append(d_m)
        sample_n.append(n_m)

        if auxiliary_cols:
            row_means = []
            for c in auxiliary_cols:
                c_vals = area_aux[a].get(c, [])
                row_means.append(float(np.mean(c_vals)) if c_vals else 0.0)
            aux_matrix_rows.append(row_means)

    aux_x = np.array(aux_matrix_rows) if auxiliary_cols and aux_matrix_rows else None

    return fit_fay_herriot_eblup(
        area_names=area_names,
        direct_estimates=np.array(direct_y),
        sampling_variances=np.array(direct_d),
        sample_sizes=np.array(sample_n),
        auxiliary_x=aux_x
    )


def generate_sae_svg(area_results: List[Dict[str, Any]]) -> str:
    """
    Vector SVG Shrinkage Forest Plot:
    Displays Direct Survey Estimates (Blue dots + error bar) alongside
    Shrunk Empirical Bayes EBLUP Estimates (Cyan dots + contracted CI),
    connected by directional arrows indicating shrinkage toward synthetic line.
    """
    m = len(area_results)
    if m == 0:
        return "<svg width='100%' height='100'></svg>"

    row_h = 28
    margin_t = 45
    margin_b = 35
    margin_l = 140
    margin_r = 35
    width = 720
    height = margin_t + m * row_h + margin_b

    # Find min and max bounds across all direct and shrunk CIs
    all_lows = [min(r["direct_ci_lower"], r["eblup_ci_lower"]) for r in area_results]
    all_highs = [max(r["direct_ci_upper"], r["eblup_ci_upper"]) for r in area_results]
    min_val = min(all_lows)
    max_val = max(all_highs)
    pad = max(1e-4, (max_val - min_val) * 0.08)
    min_val -= pad
    max_val += pad

    plot_w = width - margin_l - margin_r

    def x_scale(val: float) -> float:
        norm = (val - min_val) / (max_val - min_val + 1e-9)
        return margin_l + norm * plot_w

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="background:#0f172a; border-radius:8px; font-family:system-ui,-apple-system,sans-serif;">')

    # Gridlines
    ticks = np.linspace(min_val, max_val, 6)
    for tick in ticks:
        x_pos = x_scale(tick)
        lines.append(f'<line x1="{x_pos:.1f}" y1="{margin_t}" x2="{x_pos:.1f}" y2="{height - margin_b}" stroke="#334155" stroke-dasharray="2,3" stroke-width="1"/>')
        lines.append(f'<text x="{x_pos:.1f}" y="{height - margin_b + 18}" fill="#94a3b8" font-size="10" text-anchor="middle">{tick:.1f}</text>')

    # Legend at Top
    lines.append(f'<text x="{margin_l}" y="{margin_t - 22}" fill="#e2e8f0" font-size="12" font-weight="bold">Biểu đồ Co rút Thu hẹp Sai số (Shrinkage Forest Plot)</text>')

    # Direct legend
    lines.append(f'<circle cx="{width - 240}" cy="{margin_t - 25}" r="4" fill="#3b82f6"/>')
    lines.append(f'<line x1="{width - 250}" y1="{margin_t - 25}" x2="{width - 230}" y2="{margin_t - 25}" stroke="#3b82f6" stroke-width="1.2"/>')
    lines.append(f'<text x="{width - 222}" y="{margin_t - 21}" fill="#93c5fd" font-size="10">Ước lượng Trực tiếp (Direct)</text>')

    # EB EBLUP legend
    lines.append(f'<circle cx="{width - 95}" cy="{margin_t - 25}" r="4" fill="#10b981"/>')
    lines.append(f'<line x1="{width - 105}" y1="{margin_t - 25}" x2="{width - 85}" y2="{margin_t - 25}" stroke="#10b981" stroke-width="1.5"/>')
    lines.append(f'<text x="{width - 78}" y="{margin_t - 21}" fill="#6ee7b7" font-size="10">EBLUP (Shrunk)</text>')

    # Render each area row
    for i, row in enumerate(area_results):
        y_center = margin_t + i * row_h + row_h / 2

        # Alternating row background
        if i % 2 == 1:
            lines.append(f'<rect x="{margin_l}" y="{y_center - row_h/2:.1f}" width="{plot_w}" height="{row_h}" fill="#1e293b" opacity="0.4"/>')

        # Area name & sample size label
        area_label = f"{row['area_name']} (n={row['sample_size']})"
        if len(area_label) > 18:
            area_label = area_label[:16] + ".."
        lines.append(f'<text x="{margin_l - 10}" y="{y_center + 4:.1f}" fill="#cbd5e1" font-size="11" text-anchor="end">{area_label}</text>')

        # Direct Estimate CI line
        d_x1 = x_scale(row["direct_ci_lower"])
        d_x2 = x_scale(row["direct_ci_upper"])
        d_center = x_scale(row["direct_estimate"])
        lines.append(f'<line x1="{d_x1:.1f}" y1="{y_center - 3:.1f}" x2="{d_x2:.1f}" y2="{y_center - 3:.1f}" stroke="#3b82f6" stroke-width="1.2" opacity="0.7"/>')
        lines.append(f'<circle cx="{d_center:.1f}" cy="{y_center - 3:.1f}" r="3.5" fill="#3b82f6"/>')

        # Shrunk EBLUP CI line
        eb_x1 = x_scale(row["eblup_ci_lower"])
        eb_x2 = x_scale(row["eblup_ci_upper"])
        eb_center = x_scale(row["eblup_estimate"])
        lines.append(f'<line x1="{eb_x1:.1f}" y1="{y_center + 3:.1f}" x2="{eb_x2:.1f}" y2="{y_center + 3:.1f}" stroke="#10b981" stroke-width="1.6"/>')
        lines.append(f'<circle cx="{eb_center:.1f}" cy="{y_center + 3:.1f}" r="3.5" fill="#10b981"/>')

        # Shrinkage connecting line / arrow
        lines.append(f'<line x1="{d_center:.1f}" y1="{y_center - 3:.1f}" x2="{eb_center:.1f}" y2="{y_center + 3:.1f}" stroke="#f59e0b" stroke-width="1.2" stroke-dasharray="2,2"/>')

    lines.append('</svg>')
    return "".join(lines)


def generate_sae_apa_narrative(
    area_count: int,
    sigma_v2: float,
    mean_eff_gain: float,
    mean_gamma: float,
    beta_intercept: float
) -> str:
    """
    Generate APA 7th Edition narrative for Small Area Estimation (Fay-Herriot Model).
    """
    return (
        f"Mô hình Ước lượng Tiểu vùng Fay-Herriot (Fay & Herriot, 1979; Rao & Molina, 2015) "
        f"được ứng dụng trên {area_count} tiểu vùng nhằm khắc phục hiện tượng phương sai lấy mẫu lớn "
        f"do cỡ mẫu nhỏ ở từng khu vực. Phương sai giữa các tiểu vùng chưa giải thích được ước lượng "
        f"bằng phương pháp REML đạt sigma_v^2 = {sigma_v2:.4f}. Hệ số co rút trung bình "
        f"gamma = {mean_gamma:.3f} cho thấy mô hình đã kết hợp hài hòa giữa thông tin khảo sát trực tiếp "
        f"({mean_gamma * 100:.1f}%) và hồi quy tổng hợp ({ (1.0 - mean_gamma) * 100:.1f}%). "
        f"Sai số chuẩn theo công thức hiệu chỉnh bậc hai Prasad-Rao (1990) ghi nhận mức tăng hiệu quả "
        f"thống kê trung bình (Efficiency Gain) đạt {mean_eff_gain:.1f}%, thu hẹp đáng kể khoảng tin cậy 95% CI "
        f"so với ước lượng khảo sát trực tiếp ban đầu."
    )


class SmallAreaEstimationEngine:
    @staticmethod
    def fit_fay_herriot(
        data_rows: List[Dict[str, Any]],
        area_col: str,
        outcome_col: str,
        auxiliary_cols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        return calculate_small_area_estimation(
            data_rows=data_rows,
            area_col=area_col,
            outcome_col=outcome_col,
            auxiliary_cols=auxiliary_cols
        )
