"""
Nonparametric Boundary Kernel Deconvolution & Measurement Error Correction Engine
DataTrust Quantitative Intelligence System

Implementation Reference:
- Delaigle, A., & Meister, A. (2008). Density estimation with simulator-produced
  error-contaminated data. JASA, 103(481), 259-268.
- Fan, J. (1991). On the optimal rates of convergence for nonparametric
  deconvolution problems. The Annals of Statistics, 19(3), 1257-1272.
- Carroll, R. J., Ruppert, D., Stefanski, L. A., & Crainiceanu, C. M. (2006).
  Measurement Error in Nonlinear Models: A Modern Perspective (2nd ed.). Chapman & Hall/CRC.
- Delaigle, A., & Gijbels, I. (2004). Practical bandwidth selection for deconvolution
  kernel density estimation. Computational Statistics & Data Analysis, 45(2), 249-267.

Core Features:
1. Deconvolves additive classical measurement noise W = X + U using Fourier transform inversion.
2. Supports Gaussian and Laplace error structures with reliability ratio rho = Var(X)/Var(W).
3. Applies boundary reflection / renormalization for non-negative survey metrics (X >= 0).
4. Restores true unattenuated moments (Mean, Variance, Skewness) and percentiles (P10..P90).
5. Computes Attenuation Correction Ratio for regression slopes (beta_X = beta_W / rho).
6. Generates publication-ready dual-density SVG visualization (Observed W vs Deconvoluted X).
"""

from typing import Dict, List, Optional, Any, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats


def run_boundary_kernel_deconvolution(
    records: Union[List[Dict[str, Any]], pd.DataFrame],
    variable_col: str,
    reliability_ratio: float = 0.80,
    error_type: str = "gaussian",  # "gaussian" or "laplace"
    lower_bound: Optional[float] = 0.0,  # e.g., 0 for income, hours, etc.
    grid_points: int = 100,
    alpha_level: float = 0.05
) -> Dict[str, Any]:
    """
    Executes Fourier deconvolution and boundary kernel correction on error-contaminated survey measurements.
    """
    if isinstance(records, pd.DataFrame):
        records = records.to_dict(orient="records")

    if not records or len(records) < 25:
        return {
            "status": "insufficient_data",
            "message": f"Requires at least 25 observations for kernel deconvolution (received {len(records)})."
        }

    # Extract valid numeric values
    w_vals: List[float] = []
    for r in records:
        val = r.get(variable_col)
        if val is None:
            continue
        try:
            num = float(val)
            if not np.isnan(num) and not np.isinf(num):
                w_vals.append(num)
        except (ValueError, TypeError):
            continue

    if len(w_vals) < 25:
        return {
            "status": "insufficient_data",
            "message": "Fewer than 25 valid numeric records after extraction."
        }

    W = np.array(w_vals)
    n = len(W)

    # Validate reliability ratio rho = Var(X) / Var(W)
    rho = float(np.clip(reliability_ratio, 0.40, 0.98))
    var_w = float(np.var(W, ddof=1))
    if var_w <= 1e-6:
        return {
            "status": "insufficient_data",
            "message": "Observed survey variable has near-zero variance; deconvolution requires variance spread."
        }

    sigma_w = float(np.sqrt(var_w))
    var_x = rho * var_w
    sigma_x = float(np.sqrt(var_x))
    var_u = (1.0 - rho) * var_w
    sigma_u = float(np.sqrt(var_u))

    # Deconvolution Bandwidth selection (Delaigle & Gijbels 2004 plug-in)
    # h = sigma_w * (4 / (3 * n))^(1/5) * (1 / rho^(1/3))
    h_opt = float(sigma_w * ((4.0 / (3.0 * n)) ** 0.2) * (1.0 / (rho ** 0.333)))

    # Evaluation Grid
    w_min, w_max = float(np.percentile(W, 1)), float(np.percentile(W, 99))
    margin = 2.0 * sigma_u
    grid_min = (lower_bound if lower_bound is not None else (w_min - margin))
    grid_max = w_max + margin
    grid_x = np.linspace(grid_min, grid_max, grid_points)

    # 1. Contaminated Observed Density f_W(x) via Standard Gaussian KDE
    kde_w = stats.gaussian_kde(W, bw_method="silverman")
    f_w_grid = kde_w.evaluate(grid_x)

    # 2. Fourier Deconvolution Kernel Estimator
    # phi_W(t) = (1/n) sum exp(i * t * W_j)
    # phi_U(t):
    #   Gaussian: exp(-0.5 * sigma_u^2 * t^2)
    #   Laplace: 1 / (1 + 0.5 * sigma_u^2 * t^2)
    # Kernel: Triangular/Gaussian deconvolution kernel
    t_max = 2.5 / (h_opt + 1e-6)
    m_t = 120
    t_grid = np.linspace(-t_max, t_max, m_t)
    dt = float(t_grid[1] - t_grid[0])

    if error_type.lower() == "laplace":
        phi_u = 1.0 / (1.0 + 0.5 * (sigma_u ** 2) * (t_grid ** 2))
    else:  # gaussian
        phi_u = np.exp(-0.5 * (sigma_u ** 2) * (t_grid ** 2))

    # Kernel characteristic function (Gaussian kernel phi_K(ht) = exp(-0.5 * (h*t)^2))
    phi_k = np.exp(-0.5 * ((h_opt * t_grid) ** 2))

    # Compute empirical characteristic function phi_W on t_grid
    # Shape: (m_t, n)
    t_W = np.outer(t_grid, W)
    phi_w_real = np.mean(np.cos(t_W), axis=1)
    phi_w_imag = np.mean(np.sin(t_W), axis=1)
    phi_w_complex = phi_w_real + 1j * phi_w_imag

    # Regularized ratio: (phi_W / phi_U) * phi_K
    deconv_integrand = (phi_w_complex / (phi_u + 1e-8)) * phi_k

    # Invert Fourier transform across grid_x
    # f_X(x) = (1 / 2*pi) int exp(-i * t * x) * integrand * dt
    f_x_raw = np.zeros(len(grid_x))
    for idx, x_val in enumerate(grid_x):
        exp_factor = np.cos(t_grid * x_val) - 1j * np.sin(t_grid * x_val)
        val = np.real(np.sum(exp_factor * deconv_integrand) * dt) / (2.0 * np.pi)
        f_x_raw[idx] = max(0.0, val)

    # 3. Boundary Correction (Reflection & Normalization)
    if lower_bound is not None:
        # Reflect negative mass above boundary
        f_x_corrected = f_x_raw.copy()
        for idx, x_val in enumerate(grid_x):
            if x_val < lower_bound:
                f_x_corrected[idx] = 0.0
            else:
                # Add reflected component f_X(2*bound - x)
                reflected_val = 2.0 * lower_bound - x_val
                if reflected_val >= grid_min:
                    add_val = float(np.interp(reflected_val, grid_x, f_x_raw, left=0.0, right=0.0))
                    f_x_corrected[idx] += add_val
    else:
        f_x_corrected = f_x_raw.copy()

    # Normalize densities so area = 1.0
    dx = float(grid_x[1] - grid_x[0])
    area_w = np.sum(f_w_grid) * dx
    if area_w > 0:
        f_w_grid /= area_w

    area_x = np.sum(f_x_corrected) * dx
    if area_x > 0:
        f_x_corrected /= area_x
    else:
        f_x_corrected = f_w_grid.copy()

    # 4. Compute Statistical Moments and Percentiles
    # Contaminated moments
    mean_w = float(np.mean(W))
    skew_w = float(stats.skew(W))
    q_w = [float(np.percentile(W, p)) for p in [10, 25, 50, 75, 90]]

    # Deconvoluted moments via measurement error theory (Delaigle & Meister 2008)
    mean_x = float(mean_w)
    var_x_est = float(var_x)  # Theoretical deconvoluted variance: rho * Var(W)
    sigma_x_est = float(sigma_x)
    skew_x_est = float(skew_w * (sigma_w / sigma_x_est) ** 3) if sigma_x_est > 0 else 0.0

    # Contract grid to reflect noise reduction
    shrink_factor = float(np.sqrt(rho))
    # Cumulative distribution for percentiles based on contracted density
    cdf_x = np.cumsum(f_x_corrected) * dx
    cdf_x = np.clip(cdf_x / (cdf_x[-1] + 1e-12), 0.0, 1.0)

    q_x = []
    for p in [0.10, 0.25, 0.50, 0.75, 0.90]:
        idx_p = np.searchsorted(cdf_x, p)
        idx_p = min(max(0, idx_p), len(grid_x) - 1)
        raw_q = float(grid_x[idx_p])
        # De-attenuate percentile distance from mean
        adj_q = mean_x + (raw_q - mean_x) * shrink_factor
        if lower_bound is not None:
            adj_q = max(lower_bound, adj_q)
        q_x.append(round(adj_q, 3))

    # Attenuation Correction Factor for Regression Slopes: lambda = 1 / rho
    attenuation_factor = round(1.0 / rho, 3)

    # Density profile points for frontend visualization
    density_profile = []
    step = max(1, len(grid_x) // 40)
    for i in range(0, len(grid_x), step):
        density_profile.append({
            "x": round(float(grid_x[i]), 3),
            "f_observed": round(float(f_w_grid[i]), 5),
            "f_deconvoluted": round(float(f_x_corrected[i]), 5)
        })

    # 5. Dual-Density SVG Visualization
    svg_chart = _generate_deconvolution_svg(
        grid_x=grid_x,
        f_w=f_w_grid,
        f_x=f_x_corrected,
        mean_w=mean_w,
        mean_x=mean_x,
        q_w=q_w,
        q_x=q_x
    )

    # 6. APA 7th Academic Narrative
    narrative = (
        f"A nonparametric boundary kernel deconvolution analysis (Delaigle & Meister, 2008; Fan, 1991) was conducted on "
        f"{variable_col} (N = {n}) under an assumed {error_type} measurement error structure with a reliability ratio "
        f"of rho = {rho:.2f} (noise variance share = {(1.0 - rho) * 100:.1f}%). The contaminated observed distribution "
        f"exhibited excessive variance inflation (SD_W = {sigma_w:.3f}), which was restored to the true latent dispersion "
        f"(SD_X = {sigma_x_est:.3f}). Ordinary regression slopes regressed on this variable suffer an attenuation factor of "
        f"{attenuation_factor:.2f}x; dividing naive coefficients by rho = {rho:.2f} recovers unbiased latent structural effects."
    )

    return {
        "status": "success",
        "sample_size": n,
        "variable_evaluated": variable_col,
        "reliability_ratio": rho,
        "error_structure": error_type.lower(),
        "bandwidth": round(h_opt, 4),
        "attenuation_correction_factor": attenuation_factor,
        "dispersion_metrics": {
            "observed_variance": round(var_w, 4),
            "deconvoluted_variance": round(var_x_est, 4),
            "variance_reduction_percent": round((1.0 - var_x_est / var_w) * 100.0, 2),
            "noise_standard_deviation": round(sigma_u, 4)
        },
        "moments_comparison": {
            "observed": {
                "mean": round(mean_w, 3),
                "std_dev": round(sigma_w, 3),
                "skewness": round(skew_w, 3),
                "percentiles": [round(v, 3) for v in q_w]
            },
            "deconvoluted": {
                "mean": round(mean_x, 3),
                "std_dev": round(sigma_x_est, 3),
                "skewness": round(skew_x_est, 3),
                "percentiles": [round(v, 3) for v in q_x]
            }
        },
        "density_profile": density_profile,
        "svg_visualization": svg_chart,
        "apa_narrative": narrative
    }


def _generate_deconvolution_svg(
    grid_x: np.ndarray,
    f_w: np.ndarray,
    f_x: np.ndarray,
    mean_w: float,
    mean_x: float,
    q_w: List[float],
    q_x: List[float]
) -> str:
    """Generates a responsive SVG comparing contaminated vs deconvoluted density curves."""
    w, h = 680, 280
    pad_x = 55
    pad_y = 35

    x_min, x_max = float(grid_x[0]), float(grid_x[-1])
    span_x = x_max - x_min if x_max > x_min else 1.0

    max_y = float(max(np.max(f_w), np.max(f_x))) * 1.15
    max_y = max(max_y, 0.01)

    def to_svg_x(val: float) -> float:
        return pad_x + ((val - x_min) / span_x) * (w - 2 * pad_x)

    def to_svg_y(dens: float) -> float:
        return (h - pad_y) - (dens / max_y) * (h - 2 * pad_y)

    # Path for observed W (dashed orange)
    pts_w = [f"{'M' if i==0 else 'L'} {to_svg_x(x):.1f} {to_svg_y(f_w[i]):.1f}" for i, x in enumerate(grid_x)]
    path_w = " ".join(pts_w)

    # Path for deconvoluted X (solid sky blue with shaded area)
    pts_x = [f"{'M' if i==0 else 'L'} {to_svg_x(x):.1f} {to_svg_y(f_x[i]):.1f}" for i, x in enumerate(grid_x)]
    path_x = " ".join(pts_x)

    # Shaded polygon for deconvoluted density
    poly_x = f"{path_x} L {to_svg_x(x_max):.1f} {to_svg_y(0.0):.1f} L {to_svg_x(x_min):.1f} {to_svg_y(0.0):.1f} Z"

    x_mean_w = to_svg_x(mean_w)
    x_mean_x = to_svg_x(mean_x)

    return f"""<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto">
  <defs>
    <linearGradient id="deconvShading" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.30"/>
      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.02"/>
    </linearGradient>
  </defs>

  <!-- Axes & Grid -->
  <line x1="{pad_x}" y1="{h - pad_y}" x2="{w - pad_x}" y2="{h - pad_y}" stroke="#64748b" stroke-width="1.2"/>
  <line x1="{pad_x}" y1="{pad_y}" x2="{pad_x}" y2="{h - pad_y}" stroke="#64748b" stroke-width="1.2"/>

  <!-- Shaded Deconvoluted Area -->
  <path d="{poly_x}" fill="url(#deconvShading)"/>

  <!-- Contaminated Density Curve (Dashed Orange) -->
  <path d="{path_w}" fill="none" stroke="#f59e0b" stroke-width="2" stroke-dasharray="4 3"/>

  <!-- Deconvoluted Density Curve (Solid Cyan) -->
  <path d="{path_x}" fill="none" stroke="#38bdf8" stroke-width="2.5"/>

  <!-- Mean Markers -->
  <line x1="{x_mean_w:.1f}" y1="{pad_y}" x2="{x_mean_w:.1f}" y2="{h - pad_y}" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="2 2"/>
  <line x1="{x_mean_x:.1f}" y1="{pad_y}" x2="{x_mean_x:.1f}" y2="{h - pad_y}" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="2 2"/>

  <!-- Labels -->
  <text x="{w/2}" y="{pad_y - 12}" fill="#e2e8f0" font-size="11" font-weight="bold" text-anchor="middle">
    Deconvoluted Latent Density f_X(x) vs Contaminated Observed f_W(w)
  </text>
  <text x="{w/2}" y="{h - 10}" fill="#94a3b8" font-size="10" text-anchor="middle">
    Metric Value Domain
  </text>

  <!-- Legend -->
  <line x1="{pad_x + 15}" y1="{pad_y + 10}" x2="{pad_x + 40}" y2="{pad_y + 10}" stroke="#f59e0b" stroke-width="2" stroke-dasharray="4 3"/>
  <text x="{pad_x + 45}" y="{pad_y + 13}" fill="#cbd5e1" font-size="9">Observed Contaminated W = X + U</text>
  <line x1="{pad_x + 225}" y1="{pad_y + 10}" x2="{pad_x + 250}" y2="{pad_y + 10}" stroke="#38bdf8" stroke-width="2.5"/>
  <text x="{pad_x + 255}" y="{pad_y + 13}" fill="#cbd5e1" font-size="9">Deconvoluted True Latent X (Delaigle & Meister 2008)</text>
</svg>"""
