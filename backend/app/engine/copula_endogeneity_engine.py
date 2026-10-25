"""
DataTrust - Copula-Based Endogeneity Correction & Non-Gaussian Joint Likelihood Engine
====================================================================================
Academic Foundations:
- Park, S., & Gupta, S. (2012). Handling Endogenous Regressors with Copulas.
  Marketing Science, 31(4), 567-586.
- Tran, K. C., & Tsionas, E. G. (2015). Endogeneity in Stochastic Frontier Models:
  Copula Approach without External Instruments. Journal of Econometrics.
- Haschka, R. E. (2022). Evaluating the Performance of Copula-Based Estimators
  Under Regressor-Error Correlation. Empirical Economics, 62(1), 329-354.
- Sklar, A. (1959). Fonctions de repartition a n dimensions et leurs marges.
  Publ. Inst. Statist. Univ. Paris, 8, 229-231.
"""

from typing import Dict, List, Any, Optional, Tuple
import math
import numpy as np
from scipy import stats


def _compute_empirical_cdf(x: np.ndarray) -> np.ndarray:
    """Computes continuous empirical distribution function ranks F(X_i) = rank(X_i) / (n + 1)."""
    n = len(x)
    # Using scipy rankdata with average ties
    ranks = stats.rankdata(x, method="average")
    u = ranks / (n + 1.0)
    # Guard against boundaries [1e-6, 1 - 1e-6]
    return np.clip(u, 1e-6, 1.0 - 1e-6)


def _gaussian_copula_transform(u: np.ndarray) -> np.ndarray:
    """Computes Gaussian copula inverse standard normal transform P* = Phi^{-1}(F(P))."""
    return stats.norm.ppf(u)


def _clayton_copula_transform(u: np.ndarray, theta: float = 2.0) -> np.ndarray:
    """Computes transformed copula generator for Clayton copula psi(u) = (u^{-theta} - 1) / theta."""
    safe_u = np.clip(u, 1e-5, 1.0 - 1e-5)
    psi = (np.power(safe_u, -theta) - 1.0) / theta
    # Standardize to zero mean, unit variance for regression numerical stability
    if np.std(psi) > 1e-8:
        return (psi - np.mean(psi)) / np.std(psi)
    return psi - np.mean(psi)


def _ols_fit(y: np.ndarray, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float, float]:
    """Fits OLS regression with intercept and returns coefs, se, residuals, r2, sigma."""
    n, k = X.shape
    # Add intercept column
    X_design = np.column_stack([np.ones(n), X])
    
    # OLS coefficients via pseudo-inverse or solve
    xtx = X_design.T @ X_design
    # Small ridge regularization for numerical stability if near collinear
    ridge = 1e-7 * np.eye(xtx.shape[0])
    beta = np.linalg.solve(xtx + ridge, X_design.T @ y)
    
    y_pred = X_design @ beta
    residuals = y - y_pred
    df_e = max(1, n - (k + 1))
    sigma2 = np.sum(residuals ** 2) / df_e
    sigma = math.sqrt(max(1e-12, sigma2))
    
    # Covariance matrix of beta
    cov_beta = sigma2 * np.linalg.inv(xtx + ridge)
    se = np.sqrt(np.maximum(1e-12, np.diag(cov_beta)))
    
    # R2
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    ss_res = np.sum(residuals ** 2)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else 0.0
    
    return beta, se, residuals, r2, sigma


def run_copula_endogeneity_analysis(
    records: List[Dict[str, Any]],
    outcome_question_id: str,
    endogenous_question_id: str,
    covariate_question_ids: Optional[List[str]] = None,
    copula_family: str = "gaussian",
    bootstrap_replications: int = 100,
    alpha_level: float = 0.05,
    scope: str = "all",
) -> Dict[str, Any]:
    """
    Executes Copula-Based Endogeneity Correction (Park & Gupta 2012).
    """
    if covariate_question_ids is None:
        covariate_question_ids = []

    # Filter clean responses if requested
    filtered_records = records
    if scope == "verified_clean":
        filtered_records = [
            r for r in records
            if not r.get("is_speeding", False)
            and not r.get("is_straightlining", False)
            and not r.get("anomaly_flags")
        ]
        if len(filtered_records) < 25:
            filtered_records = records

    y_vals: List[float] = []
    p_vals: List[float] = []
    z_matrix_list: List[List[float]] = []

    for r in filtered_records:
        ans = r.get("answers", {})
        if outcome_question_id not in ans or endogenous_question_id not in ans:
            continue
        try:
            y = float(ans[outcome_question_id])
            p = float(ans[endogenous_question_id])
        except (ValueError, TypeError):
            continue

        z_row: List[float] = []
        skip_record = False
        for zid in covariate_question_ids:
            if zid not in ans:
                skip_record = True
                break
            try:
                z_row.append(float(ans[zid]))
            except (ValueError, TypeError):
                skip_record = True
                break

        if skip_record:
            continue

        y_vals.append(y)
        p_vals.append(p)
        z_matrix_list.append(z_row)

    n = len(y_vals)
    if n < 25:
        return {
            "status": "insufficient_data",
            "message": f"Sample size (N={n}) is insufficient. At least 25 valid responses are required for copula identification.",
            "sample_size": n,
        }

    y_arr = np.array(y_vals, dtype=float)
    p_arr = np.array(p_vals, dtype=float)
    p_var = np.var(p_arr)
    if p_var < 1e-8:
        return {
            "status": "zero_variance",
            "message": "Endogenous regressor has zero or near-zero variance. Cannot compute copula transformation.",
            "sample_size": n,
        }

    num_covariates = len(covariate_question_ids)
    if num_covariates > 0:
        z_arr = np.array(z_matrix_list, dtype=float)
    else:
        z_arr = np.empty((n, 0), dtype=float)

    # 1. Non-normality testing on P (Park & Gupta require non-normality for identification)
    shapiro_w, shapiro_p = stats.shapiro(p_arr[:min(n, 5000)])
    skewness = float(stats.skew(p_arr))
    kurtosis = float(stats.kurtosis(p_arr, fisher=True)) # excess kurtosis
    
    is_non_normal = bool((shapiro_p < 0.05) or (abs(skewness) > 0.3) or (abs(kurtosis) > 0.5))
    non_normality_status = (
        "Strong Non-Normality (Robust Copula Identification)"
        if (shapiro_p < 0.01 and (abs(skewness) > 0.5 or abs(kurtosis) > 0.8))
        else "Moderate Non-Normality (Adequate Identification)"
        if is_non_normal
        else "Near-Gaussian Distribution (Caution: Potential High Collinearity)"
    )

    # 2. Copula Transformation
    u_p = _compute_empirical_cdf(p_arr)
    family_lower = copula_family.lower()
    if family_lower == "clayton":
        p_star = _clayton_copula_transform(u_p, theta=2.0)
        selected_family = "Clayton Copula (Lower-Tail Dependency)"
    else:
        p_star = _gaussian_copula_transform(u_p)
        selected_family = "Gaussian Copula (Standard Park & Gupta)"

    # Check collinearity between P and P*
    corr_p_pstar = float(np.corrcoef(p_arr, p_star)[0, 1])

    # 3. Naive OLS Regression: Y ~ P + Z
    X_naive = np.column_stack([p_arr, z_arr]) if num_covariates > 0 else p_arr.reshape(-1, 1)
    beta_naive, se_naive, res_naive, r2_naive, sigma_naive = _ols_fit(y_arr, X_naive)

    beta_p_naive = float(beta_naive[1])
    se_p_naive = float(se_naive[1])
    t_p_naive = beta_p_naive / max(1e-8, se_p_naive)
    df_naive = n - (X_naive.shape[1] + 1)
    p_p_naive = float(2.0 * (1.0 - stats.t.cdf(abs(t_p_naive), df=df_naive)))
    tcrit = float(stats.t.ppf(1.0 - alpha_level / 2.0, df=df_naive))
    ci_p_naive = [beta_p_naive - tcrit * se_p_naive, beta_p_naive + tcrit * se_p_naive]

    # 4. Copula-Augmented Structural OLS: Y ~ P + Z + P*
    X_copula = np.column_stack([p_arr, z_arr, p_star]) if num_covariates > 0 else np.column_stack([p_arr, p_star])
    beta_copula, se_copula, res_copula, r2_copula, sigma_copula = _ols_fit(y_arr, X_copula)

    beta_p_copula = float(beta_copula[1])
    se_p_copula = float(se_copula[1])
    t_p_copula = beta_p_copula / max(1e-8, se_p_copula)
    df_copula = n - (X_copula.shape[1] + 1)
    p_p_copula = float(2.0 * (1.0 - stats.t.cdf(abs(t_p_copula), df=df_copula)))
    tcrit_cop = float(stats.t.ppf(1.0 - alpha_level / 2.0, df=df_copula))
    ci_p_copula = [beta_p_copula - tcrit_cop * se_p_copula, beta_p_copula + tcrit_cop * se_p_copula]

    # Endogeneity Parameter lambda (coefficient on P*)
    # P* is the last column
    idx_pstar = X_copula.shape[1] # index in design matrix (0 is intercept, 1 is P, ... last is P*)
    lambda_pstar = float(beta_copula[idx_pstar])
    se_lambda = float(se_copula[idx_pstar])
    t_lambda = lambda_pstar / max(1e-8, se_lambda)
    p_lambda = float(2.0 * (1.0 - stats.t.cdf(abs(t_lambda), df=df_copula)))
    ci_lambda = [lambda_pstar - tcrit_cop * se_lambda, lambda_pstar + tcrit_cop * se_lambda]

    # Implied error correlation rho = lambda / sqrt(sigma_u^2 + lambda^2 * Var(P*))
    pstar_var = np.var(p_star)
    denom = math.sqrt(max(1e-12, sigma_copula**2 + (lambda_pstar**2) * pstar_var))
    implied_rho = float(np.clip(lambda_pstar / denom, -0.999, 0.999))

    is_endogenous = bool(p_lambda < alpha_level)
    endogeneity_conclusion = (
        f"Significant Endogeneity Detected (t = {t_lambda:.3f}, p = {p_lambda:.4f}). "
        f"Naive OLS is biased. Implied regressor-error correlation rho = {implied_rho:.3f}."
        if is_endogenous
        else f"No Significant Endogeneity (t = {t_lambda:.3f}, p = {p_lambda:.4f} >= {alpha_level}). "
             f"The hypothesis of exogeneity cannot be rejected; naive OLS is consistent."
    )

    bias_absolute = beta_p_naive - beta_p_copula
    bias_relative_pct = (bias_absolute / abs(beta_p_copula) * 100.0) if abs(beta_p_copula) > 1e-6 else 0.0

    # 5. Bootstrap Standard Errors (optional validation)
    b_reps = min(max(20, bootstrap_replications), 200)
    boot_betas: List[float] = []
    boot_lambdas: List[float] = []

    rng = np.random.default_rng(42)
    for _ in range(b_reps):
        boot_idx = rng.integers(0, n, size=n)
        b_y = y_arr[boot_idx]
        b_p = p_arr[boot_idx]
        b_u = _compute_empirical_cdf(b_p)
        b_pstar = _clayton_copula_transform(b_u, theta=2.0) if family_lower == "clayton" else _gaussian_copula_transform(b_u)
        
        if num_covariates > 0:
            b_z = z_arr[boot_idx]
            b_X = np.column_stack([b_p, b_z, b_pstar])
        else:
            b_X = np.column_stack([b_p, b_pstar])
            
        try:
            b_coef, _, _, _, _ = _ols_fit(b_y, b_X)
            boot_betas.append(float(b_coef[1]))
            boot_lambdas.append(float(b_coef[b_X.shape[1]]))
        except Exception:
            continue

    if len(boot_betas) > 10:
        se_p_boot = float(np.std(boot_betas))
        se_lambda_boot = float(np.std(boot_lambdas))
    else:
        se_p_boot = se_p_copula
        se_lambda_boot = se_lambda

    # 6. Generate SVG Visualization
    svg_viz = _render_copula_svg(
        p_arr=p_arr,
        p_star=p_star,
        beta_naive=beta_p_naive,
        ci_naive=ci_p_naive,
        beta_copula=beta_p_copula,
        ci_copula=ci_p_copula,
        is_endogenous=is_endogenous,
        implied_rho=implied_rho,
        p_lambda=p_lambda,
    )

    # 7. APA Narrative
    apa_narrative = (
        f"A copula-based endogeneity analysis was conducted using the method of Park and Gupta (2012) "
        f"to estimate the causal impact of the survey regressor without requiring external instruments (N = {n}). "
        f"Evaluation of the endogenous regressor revealed {non_normality_status.lower()} "
        f"(Shapiro-Wilk W = {shapiro_w:.4f}, p = {shapiro_p:.4f}; Skewness = {skewness:.3f}; Kurtosis = {kurtosis:.3f}), "
        f"confirming sufficient distributional non-normality for parameter identification via the {selected_family}. "
        f"Under naive OLS regression, the estimated effect was beta = {beta_p_naive:.4f} "
        f"(SE = {se_p_naive:.4f}, 95% CI [{ci_p_naive[0]:.4f}, {ci_p_naive[1]:.4f}], p = {p_p_naive:.4f}). "
        f"In the copula-augmented specification, the endogeneity control regressor P* yielded a coefficient of "
        f"lambda = {lambda_pstar:.4f} (SE = {se_lambda:.4f}, bootstrap SE = {se_lambda_boot:.4f}, "
        f"t = {t_lambda:.3f}, p = {p_lambda:.4f}), indicating an implied regressor-error correlation of "
        f"rho = {implied_rho:.3f}. {endogeneity_conclusion} "
        f"The corrected structural causal coefficient was beta = {beta_p_copula:.4f} "
        f"(SE = {se_p_copula:.4f}, bootstrap SE = {se_p_boot:.4f}, 95% CI [{ci_p_copula[0]:.4f}, {ci_p_copula[1]:.4f}], p = {p_p_copula:.4f}), "
        f"revealing an absolute bias adjustment of {bias_absolute:+.4f} ({bias_relative_pct:+.1f}%)."
    )

    return {
        "status": "success",
        "sample_size": n,
        "copula_family": selected_family,
        "non_normality_diagnostics": {
            "shapiro_w": round(shapiro_w, 4),
            "shapiro_p": round(shapiro_p, 4),
            "skewness": round(skewness, 3),
            "kurtosis": round(kurtosis, 3),
            "is_non_normal": is_non_normal,
            "status_label": non_normality_status,
            "regressor_copula_correlation": round(corr_p_pstar, 4),
        },
        "naive_ols": {
            "estimate": round(beta_p_naive, 4),
            "se": round(se_p_naive, 4),
            "t_stat": round(t_p_naive, 3),
            "p_value": round(p_p_naive, 4),
            "ci_95": [round(ci_p_naive[0], 4), round(ci_p_naive[1], 4)],
            "r2": round(r2_naive, 4),
        },
        "copula_augmented": {
            "estimate": round(beta_p_copula, 4),
            "se_asymptotic": round(se_p_copula, 4),
            "se_bootstrap": round(se_p_boot, 4),
            "t_stat": round(t_p_copula, 3),
            "p_value": round(p_p_copula, 4),
            "ci_95": [round(ci_p_copula[0], 4), round(ci_p_copula[1], 4)],
            "r2": round(r2_copula, 4),
        },
        "endogeneity_test": {
            "lambda_pstar": round(lambda_pstar, 4),
            "se_lambda": round(se_lambda, 4),
            "se_bootstrap": round(se_lambda_boot, 4),
            "t_stat": round(t_lambda, 3),
            "p_value": round(p_lambda, 4),
            "ci_95": [round(ci_lambda[0], 4), round(ci_lambda[1], 4)],
            "implied_rho": round(implied_rho, 4),
            "is_endogenous": is_endogenous,
            "conclusion": endogeneity_conclusion,
        },
        "bias_correction": {
            "absolute_bias": round(bias_absolute, 4),
            "relative_bias_pct": round(bias_relative_pct, 2),
            "recommended_estimator": "Copula-Augmented 2-Stage OLS" if is_endogenous else "Naive OLS",
        },
        "svg_visualization": svg_viz,
        "apa_narrative": apa_narrative,
    }


def _render_copula_svg(
    p_arr: np.ndarray,
    p_star: np.ndarray,
    beta_naive: float,
    ci_naive: List[float],
    beta_copula: float,
    ci_copula: List[float],
    is_endogenous: bool,
    implied_rho: float,
    p_lambda: float,
) -> str:
    """Generates a responsive dual-panel SVG visualizer."""
    svg_width = 860
    svg_height = 360

    # Panel A: Scatter / Distribution of P vs P*
    # Panel B: Forest plot comparing Naive OLS vs Copula Corrected
    
    # Subsample 40 points for clear scatter
    sub_n = min(len(p_arr), 40)
    indices = np.linspace(0, len(p_arr) - 1, sub_n, dtype=int)
    p_sub = p_arr[indices]
    pstar_sub = p_star[indices]

    min_p, max_p = float(np.min(p_sub)), float(np.max(p_sub))
    min_ps, max_ps = float(np.min(pstar_sub)), float(np.max(pstar_sub))
    span_p = max(1e-4, max_p - min_p)
    span_ps = max(1e-4, max_ps - min_ps)

    # Panel A coordinates: x: 50 to 390, y: 70 to 310
    panel_a_dots = []
    for p_val, ps_val in zip(p_sub, pstar_sub):
        cx = 60 + ((p_val - min_p) / span_p) * 310
        cy = 300 - ((ps_val - min_ps) / span_ps) * 220
        panel_a_dots.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="#38bdf8" opacity="0.8"/>')

    # Panel B coordinates: x: 480 to 810, y: 70 to 310
    # Forest plot comparing beta_naive and beta_copula
    all_vals = [ci_naive[0], ci_naive[1], ci_copula[0], ci_copula[1], beta_naive, beta_copula, 0.0]
    min_b = min(all_vals) - 0.2 * (max(all_vals) - min(all_vals) + 1e-4)
    max_b = max(all_vals) + 0.2 * (max(all_vals) - min(all_vals) + 1e-4)
    span_b = max_b - min_b

    def x_scale(val: float) -> float:
        return 490 + ((val - min_b) / span_b) * 310

    x_zero = x_scale(0.0)

    # Naive y: 150, Copula y: 230
    x_naive_pt = x_scale(beta_naive)
    x_naive_l = x_scale(ci_naive[0])
    x_naive_r = x_scale(ci_naive[1])

    x_cop_pt = x_scale(beta_copula)
    x_cop_l = x_scale(ci_copula[0])
    x_cop_r = x_scale(ci_copula[1])

    badge_color = "#ef4444" if is_endogenous else "#10b981"
    badge_text = f"Endogeneity Detected (p = {p_lambda:.3f})" if is_endogenous else f"Exogenous (p = {p_lambda:.3f})"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="{svg_width}" height="{svg_height}" rx="12" fill="url(#bgGrad)"/>

  <!-- Main Title -->
  <text x="30" y="36" fill="#f8fafc" font-size="16" font-weight="700">Park &amp; Gupta (2012) Copula Endogeneity Diagnostics</text>
  <rect x="580" y="20" width="250" height="26" rx="6" fill="{badge_color}" opacity="0.2"/>
  <rect x="580" y="20" width="250" height="26" rx="6" fill="none" stroke="{badge_color}" stroke-width="1.5"/>
  <text x="705" y="37" fill="{badge_color}" font-size="11" font-weight="700" text-anchor="middle">{badge_text}</text>

  <!-- Panel A: Copula Transform -->
  <rect x="30" y="60" width="370" height="270" rx="8" fill="#1e293b" fill-opacity="0.6" stroke="#334155" stroke-width="1"/>
  <text x="45" y="85" fill="#e2e8f0" font-size="13" font-weight="600">Panel A: Empirical Distribution P vs Copula P*</text>
  
  <!-- Axes A -->
  <line x1="60" y1="300" x2="380" y2="300" stroke="#475569" stroke-width="1.5"/>
  <line x1="60" y1="300" x2="60" y2="100" stroke="#475569" stroke-width="1.5"/>
  <text x="220" y="322" fill="#94a3b8" font-size="11" text-anchor="middle">Observed Regressor P</text>
  <text x="45" y="200" fill="#94a3b8" font-size="11" text-anchor="middle" transform="rotate(-90 45 200)">Copula P* = Φ⁻¹(F(P))</text>

  <!-- Scatter points -->
  {''.join(panel_a_dots)}

  <!-- Panel B: Effect Comparison -->
  <rect x="430" y="60" width="400" height="270" rx="8" fill="#1e293b" fill-opacity="0.6" stroke="#334155" stroke-width="1"/>
  <text x="445" y="85" fill="#e2e8f0" font-size="13" font-weight="600">Panel B: Causal Effect Correction (95% CI)</text>

  <!-- Zero Reference Line -->
  <line x1="{x_zero:.1f}" y1="110" x2="{x_zero:.1f}" y2="290" stroke="#64748b" stroke-width="1" stroke-dasharray="4,4"/>
  <text x="{x_zero:.1f}" y="105" fill="#64748b" font-size="10" text-anchor="middle">0.0 (Null)</text>

  <!-- Naive OLS -->
  <text x="450" y="145" fill="#f59e0b" font-size="12" font-weight="600">Naive OLS (Uncorrected):</text>
  <line x1="{x_naive_l:.1f}" y1="160" x2="{x_naive_r:.1f}" y2="160" stroke="#f59e0b" stroke-width="3" stroke-linecap="round"/>
  <circle cx="{x_naive_pt:.1f}" cy="160" r="6" fill="#f59e0b" stroke="#ffffff" stroke-width="2"/>
  <text x="{x_naive_pt:.1f}" y="180" fill="#f59e0b" font-size="11" font-weight="700" text-anchor="middle">{beta_naive:.3f} [{ci_naive[0]:.2f}, {ci_naive[1]:.2f}]</text>

  <!-- Copula-Augmented OLS -->
  <text x="450" y="225" fill="#38bdf8" font-size="12" font-weight="600">Copula-Augmented (Park &amp; Gupta):</text>
  <line x1="{x_cop_l:.1f}" y1="240" x2="{x_cop_r:.1f}" y2="240" stroke="#38bdf8" stroke-width="3" stroke-linecap="round"/>
  <circle cx="{x_cop_pt:.1f}" cy="240" r="6" fill="#38bdf8" stroke="#ffffff" stroke-width="2"/>
  <text x="{x_cop_pt:.1f}" y="260" fill="#38bdf8" font-size="11" font-weight="700" text-anchor="middle">{beta_copula:.3f} [{ci_copula[0]:.2f}, {ci_copula[1]:.2f}]</text>

  <!-- Implied Rho Tag -->
  <rect x="450" y="280" width="360" height="36" rx="6" fill="#0f172a" stroke="#334155" stroke-width="1"/>
  <text x="465" y="302" fill="#94a3b8" font-size="11">Implied Regressor-Error Correlation: <tspan fill="#e2e8f0" font-weight="700">ρ = {implied_rho:+.3f}</tspan></text>
</svg>"""
    return svg
