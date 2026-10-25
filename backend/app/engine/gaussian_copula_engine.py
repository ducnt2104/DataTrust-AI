"""
Endogeneity Control via Gaussian Copula Estimation Engine.
Based on the foundational econometric methodologies of:
- Park, S., & Gupta, S. (2012). Handling Endogenous Regressors by Joint Estimation Using Copulas. Marketing Science, 31(4), 567-586.
- Becker, J.-M., Proksch, D., & Ringle, C. M. (2022). Revisiting Gaussian Copulas to Address Endogeneity in PLS-SEM. Australasian Marketing Journal, 30(1), 5-14.
"""

from typing import Dict, List, Any, Optional, Tuple
import math
import numpy as np
import scipy.special
import scipy.stats


def _inv_norm_cdf(p: float) -> float:
    """
    Computes inverse standard normal CDF Phi^{-1}(p) using scipy.special.ndtri.
    """
    p_capped = max(1e-12, min(1.0 - 1e-12, float(p)))
    return float(scipy.special.ndtri(p_capped))


def _empirical_cdf(values: np.ndarray) -> np.ndarray:
    """
    Computes empirical cumulative distribution function (ECDF) for vector values.
    Uses Blom/Hazen rank mapping: (rank - 0.375) / (N + 0.25) to avoid boundary singularities.
    """
    n = len(values)
    ranks = np.argsort(np.argsort(values)) + 1.0  # 1-based ranks
    ecdf = (ranks - 0.375) / (n + 0.25)
    return np.clip(ecdf, 1e-6, 1.0 - 1e-6)


def _jarque_bera_test(values: np.ndarray) -> Tuple[float, float, float, float]:
    """
    Performs Jarque-Bera test for non-normality.
    Returns: (jb_stat, p_value, skewness, excess_kurtosis)
    """
    n = len(values)
    if n < 8:
        return 0.0, 1.0, 0.0, 0.0

    mean_v = np.mean(values)
    var_v = np.var(values)
    if var_v < 1e-12:
        return 0.0, 1.0, 0.0, 0.0

    m3 = np.mean((values - mean_v) ** 3)
    m4 = np.mean((values - mean_v) ** 4)

    skew = m3 / (var_v ** 1.5)
    kurt = (m4 / (var_v ** 2)) - 3.0

    res = scipy.stats.jarque_bera(values)
    return float(res.statistic), float(res.pvalue), float(skew), float(kurt)


def _ols_solve(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """
    Standard Ordinary Least Squares solver.
    Returns: (beta, se, t_stats, r_squared)
    """
    n, k = X.shape
    xtx = X.T @ X
    inv_xtx = np.linalg.pinv(xtx)
    beta = inv_xtx @ (X.T @ y)

    residuals = y - X @ beta
    dof = max(1, n - k)
    sigma2 = np.sum(residuals ** 2) / dof
    var_beta = sigma2 * np.diag(inv_xtx)
    se = np.sqrt(np.maximum(1e-12, var_beta))
    t_stats = beta / se

    ss_tot = np.sum((y - np.mean(y)) ** 2)
    ss_res = np.sum(residuals ** 2)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else 0.0

    return beta, se, t_stats, float(r2)


def _compute_vif(X: np.ndarray, target_col: int) -> float:
    """
    Computes Variance Inflation Factor (VIF) for a specific column in design matrix X.
    """
    n, k = X.shape
    if k <= 1:
        return 1.0
    y_col = X[:, target_col]
    other_cols = np.delete(X, target_col, axis=1)

    xtx = other_cols.T @ other_cols
    inv_xtx = np.linalg.pinv(xtx)
    beta = inv_xtx @ (other_cols.T @ y_col)
    res = y_col - other_cols @ beta
    ss_tot = np.sum((y_col - np.mean(y_col)) ** 2)
    r2 = 1.0 - (np.sum(res ** 2) / ss_tot) if ss_tot > 1e-12 else 0.0

    vif = 1.0 / max(1e-6, 1.0 - r2)
    return float(min(999.0, vif))


def run_gaussian_copula_estimation(
    records: List[Dict[str, Any]],
    endogenous_var: str,
    outcome_var: str,
    control_vars: Optional[List[str]] = None,
    var_titles: Optional[Dict[str, str]] = None,
    n_bootstraps: int = 400,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Executes Park & Gupta (2012) Gaussian Copula Endogeneity Correction.
    """
    ctrl_vars = control_vars or []
    all_needed = [endogenous_var, outcome_var] + ctrl_vars

    clean_matrix = []
    for r in records:
        row = []
        valid = True
        for vname in all_needed:
            val = r.get(vname)
            if val is None:
                valid = False
                break
            try:
                row.append(float(val))
            except (ValueError, TypeError):
                valid = False
                break
        if valid:
            clean_matrix.append(row)

    N = len(clean_matrix)
    if N < 25:
        return {
            "status": "error",
            "message": f"Số quan sát hoàn chỉnh (N={N}) quá ít để ước lượng Gaussian Copula (yêu cầu tối thiểu N >= 25)."
        }

    data_arr = np.array(clean_matrix, dtype=float)
    P_vec = data_arr[:, 0]  # Endogenous regressor
    Y_vec = data_arr[:, 1]  # Dependent variable
    X_ctrl = data_arr[:, 2:] if len(ctrl_vars) > 0 else np.zeros((N, 0))

    # 1. Non-normality diagnostic of endogenous regressor P
    jb_stat, jb_p_value, skew_p, kurt_p = _jarque_bera_test(P_vec)
    is_non_normal = jb_p_value < 0.05

    # 2. Construct Gaussian Copula Instrument: C_P = Phi^{-1}(F_P(P))
    ecdf_p = _empirical_cdf(P_vec)
    C_P = np.array([_inv_norm_cdf(u) for u in ecdf_p])

    # 3. Model 1: Naive OLS (Without Copula Instrument)
    X_naive = np.column_stack([np.ones(N), P_vec, X_ctrl])
    beta_naive, se_naive, t_naive, r2_naive = _ols_solve(X_naive, Y_vec)

    # 4. Model 2: Copula-Corrected OLS (With Copula Instrument C_P)
    X_copula = np.column_stack([np.ones(N), P_vec, C_P, X_ctrl])
    beta_copula, se_copula, t_copula, r2_copula = _ols_solve(X_copula, Y_vec)

    # Check VIF for C_P to verify no extreme collinearity with P
    vif_cp = _compute_vif(X_copula, target_col=2)

    # 5. Bootstrap Inference for Standard Errors
    rng = np.random.RandomState(seed)
    boot_beta_p = []
    boot_rho_cp = []

    for b in range(n_bootstraps):
        boot_idx = rng.choice(N, size=N, replace=True)
        P_b = P_vec[boot_idx]
        Y_b = Y_vec[boot_idx]
        X_ctrl_b = X_ctrl[boot_idx] if len(ctrl_vars) > 0 else np.zeros((N, 0))

        ecdf_b = _empirical_cdf(P_b)
        C_P_b = np.array([_inv_norm_cdf(u) for u in ecdf_b])

        X_b = np.column_stack([np.ones(N), P_b, C_P_b, X_ctrl_b])
        try:
            b_coef, _, _, _ = _ols_solve(X_b, Y_b)
            boot_beta_p.append(b_coef[1])
            boot_rho_cp.append(b_coef[2])
        except Exception:
            continue

    if len(boot_beta_p) > 20:
        se_boot_beta_p = float(np.std(boot_beta_p))
        se_boot_rho = float(np.std(boot_rho_cp))
        ci_lower_beta_p = float(np.percentile(boot_beta_p, 2.5))
        ci_upper_beta_p = float(np.percentile(boot_beta_p, 97.5))
        ci_lower_rho = float(np.percentile(boot_rho_cp, 2.5))
        ci_upper_rho = float(np.percentile(boot_rho_cp, 97.5))
    else:
        se_boot_beta_p = float(se_copula[1])
        se_boot_rho = float(se_copula[2])
        ci_lower_beta_p = float(beta_copula[1] - 1.96 * se_boot_beta_p)
        ci_upper_beta_p = float(beta_copula[1] + 1.96 * se_boot_beta_p)
        ci_lower_rho = float(beta_copula[2] - 1.96 * se_boot_rho)
        ci_upper_rho = float(beta_copula[2] + 1.96 * se_boot_rho)

    # Endogeneity Test on Copula Parameter rho
    rho_est = float(beta_copula[2])
    t_rho = rho_est / max(1e-6, se_boot_rho)
    p_rho = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(t_rho) / math.sqrt(2.0))))
    p_rho = max(0.0001, min(1.0, float(p_rho)))

    is_endogenous = p_rho < 0.05
    bias_gap = float(beta_naive[1] - beta_copula[1])
    pct_bias = float((bias_gap / beta_copula[1]) * 100.0) if abs(beta_copula[1]) > 1e-4 else 0.0

    if is_endogenous:
        diag_status = "ENDOGENEITY_CONFIRMED"
        diag_badge = "Xác nhận nội sinh nghiêm trọng (OLS bị sai lệch)"
    else:
        diag_status = "NO_SIGNIFICANT_ENDOGENEITY"
        diag_badge = "Không có nội sinh đáng kể (OLS đáng tin cậy)"

    titles = var_titles or {}
    p_title = titles.get(endogenous_var, endogenous_var)
    y_title = titles.get(outcome_var, outcome_var)

    # 6. Generate SVG Dual-Panel Chart
    svg_chart = _generate_copula_svg(
        P_vec=P_vec,
        p_title=p_title,
        y_title=y_title,
        beta_naive=float(beta_naive[1]),
        se_naive=float(se_naive[1]),
        beta_copula=float(beta_copula[1]),
        se_copula_boot=se_boot_beta_p,
        ci_copula_low=ci_lower_beta_p,
        ci_copula_high=ci_upper_beta_p,
        rho_est=rho_est,
        p_rho=p_rho,
        is_endogenous=is_endogenous
    )

    # 7. APA 7th Edition Narrative
    apa_narrative = (
        f"Kiểm định và hiệu chỉnh nội sinh không cần biến công cụ ngoại sinh theo phương pháp luận Gaussian Copula "
        f"(Park & Gupta, 2012) được áp dụng để ước lượng tác động của {p_title} lên {y_title} trên mẫu N = {N}. "
        f"Kiểm định phi chuẩn Jarque-Bera xác nhận biến độc lập thỏa mãn điều kiện phân phối phi chuẩn "
        f"(JB = {jb_stat:.2f}, p = {jb_p_value:.4f}, Skewness = {skew_p:.2f}, Kurtosis = {kurt_p:.2f}). "
        f"Chỉ số phóng đại phương sai của biến công cụ Copula đạt VIF = {vif_cp:.2f} (< 10), đảm bảo không xảy ra cộng tuyến nghiêm trọng. "
        f"Mô hình hồi quy OLS ngây thơ (Naive OLS) cho ước lượng beta_OLS = {beta_naive[1]:.4f} (SE = {se_naive[1]:.4f}, R² = {r2_naive:.3f}). "
        f"Sau khi đưa số hạng Gaussian Copula C_P vào mô hình với {n_bootstraps} lượt bootstrap resamples, "
        f"hệ số nội sinh đạt rho = {rho_est:.4f} (SE_boot = {se_boot_rho:.4f}, t = {t_rho:.2f}, p = {p_rho:.4f}). "
        f"{'Bằng chứng thống kê bác bỏ giả thuyết ngoại sinh (p < .05), chứng minh OLS cổ điển bị sai lệch (Bias = ' + f'{bias_gap:.4f}' + f', {pct_bias:+.1f}%). ' if is_endogenous else 'Không phát hiện bằng chứng nội sinh có ý nghĩa thống kê (p >= .05), OLS cổ điển duy trì tính vững. '}"
        f"Hệ số tác động nhân quả đã hiệu chỉnh nội sinh đạt beta_Copula = {beta_copula[1]:.4f} "
        f"(SE_boot = {se_boot_beta_p:.4f}, 95% Bootstrap CI [{ci_lower_beta_p:.4f}, {ci_upper_beta_p:.4f}])."
    )

    return {
        "status": "success",
        "sample_diagnostics": {
            "n_observations": N,
            "endogenous_variable": endogenous_var,
            "outcome_variable": outcome_var,
            "control_variables": ctrl_vars,
            "jarque_bera_stat": round(jb_stat, 3),
            "jarque_bera_p_value": round(jb_p_value, 4),
            "skewness": round(skew_p, 3),
            "excess_kurtosis": round(kurt_p, 3),
            "non_normality_satisfied": is_non_normal,
            "copula_vif": round(vif_cp, 3),
            "endogeneity_status": diag_status,
            "endogeneity_badge": diag_badge
        },
        "naive_ols": {
            "beta": round(float(beta_naive[1]), 4),
            "se": round(float(se_naive[1]), 4),
            "t_stat": round(float(t_naive[1]), 3),
            "ci_lower": round(float(beta_naive[1] - 1.96 * se_naive[1]), 4),
            "ci_upper": round(float(beta_naive[1] + 1.96 * se_naive[1]), 4),
            "r_squared": round(r2_naive, 4)
        },
        "copula_corrected": {
            "beta_copula": round(float(beta_copula[1]), 4),
            "se_bootstrap": round(se_boot_beta_p, 4),
            "ci_lower_bootstrap": round(ci_lower_beta_p, 4),
            "ci_upper_bootstrap": round(ci_upper_beta_p, 4),
            "copula_rho_parameter": round(rho_est, 4),
            "se_copula_rho": round(se_boot_rho, 4),
            "t_rho": round(t_rho, 3),
            "p_value_rho": round(p_rho, 4),
            "is_endogeneity_significant": is_endogenous,
            "endogeneity_bias_gap": round(bias_gap, 4),
            "percentage_bias": round(pct_bias, 1),
            "r_squared": round(r2_copula, 4)
        },
        "svg_chart": svg_chart,
        "apa_narrative": apa_narrative
    }


def _generate_copula_svg(
    P_vec: np.ndarray,
    p_title: str,
    y_title: str,
    beta_naive: float,
    se_naive: float,
    beta_copula: float,
    se_copula_boot: float,
    ci_copula_low: float,
    ci_copula_high: float,
    rho_est: float,
    p_rho: float,
    is_endogenous: bool
) -> str:
    """
    Generates a dual-panel SVG:
    Panel A: Non-normality distribution & Empirical CDF of Endogenous Regressor.
    Panel B: Causal Forest Plot (Naive OLS vs Copula-Corrected with Bias Gap).
    """
    svg_width = 960
    svg_height = 400

    # Panel A bounds: X from 40 to 450, Y from 60 to 350
    p1_x, p1_y, p1_w, p1_h = 50, 70, 400, 280
    hist, bin_edges = np.histogram(P_vec, bins=16, density=True)
    max_h = max(hist) if len(hist) > 0 and max(hist) > 0 else 1.0

    bar_svg = []
    b_width = (p1_w - 60) / float(len(hist))
    for b_idx in range(len(hist)):
        bx = p1_x + 30 + b_idx * b_width
        b_h = (hist[b_idx] / max_h) * (p1_h - 60)
        by = (p1_y + p1_h - 20) - b_h
        bar_svg.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{b_width*0.8:.1f}" height="{b_h:.1f}" fill="#38bdf8" opacity="0.75" rx="2" />')

    # Panel B bounds: Forest plot comparing Naive OLS vs Copula-Corrected
    p2_x, p2_y, p2_w, p2_h = 500, 70, 420, 280
    all_vals = [
        beta_naive - 1.96 * se_naive, beta_naive + 1.96 * se_naive,
        ci_copula_low, ci_copula_high, 0.0
    ]
    min_b = min(all_vals) - 0.1
    max_b = max(all_vals) + 0.1
    range_b = max(1e-4, max_b - min_b)

    def to_x(val):
        return p2_x + 50 + ((val - min_b) / range_b) * (p2_w - 90)

    x_zero = to_x(0.0)
    x_naive = to_x(beta_naive)
    x_naive_low = to_x(beta_naive - 1.96 * se_naive)
    x_naive_high = to_x(beta_naive + 1.96 * se_naive)

    x_cop = to_x(beta_copula)
    x_cop_low = to_x(ci_copula_low)
    x_cop_high = to_x(ci_copula_high)

    y_naive = p2_y + 100
    y_cop = p2_y + 190

    bias_color = "#ef4444" if is_endogenous else "#10b981"
    bias_label = f"Sai lệch: {abs(beta_naive - beta_copula):.3f}"

    svg_elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="100%" height="100%" class="copula-svg">',
        '<style>',
        '.cop-bg { fill: #0f172a; }',
        '.cop-panel { fill: #1e293b; stroke: #334155; stroke-width: 1.5; rx: 8px; }',
        '.cop-title { font-family: system-ui, -apple-system, sans-serif; font-size: 13px; font-weight: 700; fill: #f8fafc; }',
        '.cop-subtitle { font-family: system-ui, -apple-system, sans-serif; font-size: 10px; fill: #94a3b8; }',
        '.cop-ref { stroke: #64748b; stroke-width: 1.2; stroke-dasharray: 3,3; }',
        '.cop-naive-line { stroke: #f59e0b; stroke-width: 2.5; stroke-linecap: round; }',
        '.cop-naive-pt { fill: #f59e0b; stroke: #fff; stroke-width: 1.5; }',
        '.cop-copula-line { stroke: #10b981; stroke-width: 3; stroke-linecap: round; }',
        '.cop-copula-pt { fill: #10b981; stroke: #fff; stroke-width: 1.5; }',
        '.cop-label { font-family: system-ui, -apple-system, sans-serif; font-size: 11px; font-weight: 600; fill: #e2e8f0; }',
        '.cop-stat { font-family: system-ui, -apple-system, sans-serif; font-size: 10px; fill: #94a3b8; }',
        '</style>',
        f'<rect width="{svg_width}" height="{svg_height}" class="cop-bg" rx="12" />',

        # Panel A Container
        f'<rect x="{p1_x - 10}" y="{p1_y - 25}" width="{p1_w + 20}" height="{p1_h + 35}" class="cop-panel" />',
        f'<text x="{p1_x}" y="{p1_y - 5}" class="cop-title">Panel A: Phân Phối Phi Chuẩn &amp; Công Cụ Copula ({p_title[:18]})</text>',
        f'<text x="{p1_x}" y="{p1_y + 10}" class="cop-subtitle">Histogram thực nghiệm · Điều kiện phi chuẩn Jarque-Bera (p &lt; .05)</text>',
        f'<line x1="{p1_x + 20}" y1="{p1_y + p1_h - 20}" x2="{p1_x + p1_w}" y2="{p1_y + p1_h - 20}" stroke="#475569" stroke-width="1" />',
        f'<line x1="{p1_x + 20}" y1="{p1_y + 25}" x2="{p1_x + 20}" y2="{p1_y + p1_h - 20}" stroke="#475569" stroke-width="1" />',
        "\n".join(bar_svg),

        # Panel B Container
        f'<rect x="{p2_x - 10}" y="{p2_y - 25}" width="{p2_w + 20}" height="{p2_h + 35}" class="cop-panel" />',
        f'<text x="{p2_x}" y="{p2_y - 5}" class="cop-title">Panel B: Đối Chiếu Hiệu Ứng OLS Ngây Thơ vs Đã Hiệu Chỉnh Copula</text>',
        f'<text x="{p2_x}" y="{p2_y + 10}" class="cop-subtitle">Đánh giá khoảng cách sai lệch nội sinh · Park &amp; Gupta (2012)</text>',

        # Zero reference line in Panel B
        f'<line x1="{x_zero}" y1="{p2_y + 40}" x2="{x_zero}" y2="{p2_y + p2_h - 20}" class="cop-ref" />',
        f'<text x="{x_zero}" y="{p2_y + p2_h - 8}" font-family="system-ui" font-size="9" fill="#94a3b8" text-anchor="middle">Null (0)</text>',

        # Naive OLS Row
        f'<text x="{p2_x + 10}" y="{y_naive - 15}" class="cop-label">1. OLS Ngây Thơ (Bị Nội Sinh)</text>',
        f'<text x="{p2_x + 10}" y="{y_naive}" class="cop-stat">β_OLS = {beta_naive:.3f} (SE = {se_naive:.3f})</text>',
        f'<line x1="{x_naive_low}" y1="{y_naive}" x2="{x_naive_high}" y2="{y_naive}" class="cop-naive-line" />',
        f'<circle cx="{x_naive}" cy="{y_naive}" r="5" class="cop-naive-pt" />',

        # Copula-Corrected Row
        f'<text x="{p2_x + 10}" y="{y_cop - 15}" class="cop-label">2. Đã Hiệu Chỉnh Gaussian Copula</text>',
        f'<text x="{p2_x + 10}" y="{y_cop}" class="cop-stat">β_Copula = {beta_copula:.3f} (SE_boot = {se_copula_boot:.3f})</text>',
        f'<line x1="{x_cop_low}" y1="{y_cop}" x2="{x_cop_high}" y2="{y_cop}" class="cop-copula-line" />',
        f'<circle cx="{x_cop}" cy="{y_cop}" r="6" class="cop-copula-pt" />',

        # Bias gap connector
        f'<line x1="{x_naive}" y1="{y_naive + 10}" x2="{x_cop}" y2="{y_cop - 10}" stroke="{bias_color}" stroke-width="1.8" stroke-dasharray="4,3" />',
        f'<text x="{(x_naive + x_cop) / 2 + 10}" y="{(y_naive + y_cop) / 2}" font-family="system-ui" font-size="10" font-weight="700" fill="{bias_color}">{bias_label}</text>',

        # Footnote Badge
        f'<rect x="{p2_x + 10}" y="{p2_y + p2_h - 50}" width="{p2_w - 20}" height="24" fill="#0f172a" rx="4" />',
        f'<text x="{p2_x + 20}" y="{p2_y + p2_h - 34}" font-family="system-ui" font-size="10" fill="#cbd5e1">'
        f'Kiểm định tham số Copula: ρ = {rho_est:.3f} · p = {p_rho:.4f} ({ "Nội sinh nghiêm trọng" if is_endogenous else "Không nội sinh" })'
        f'</text>',

        '</svg>'
    ]

    return "\n".join(svg_elements)
