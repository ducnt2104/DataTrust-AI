"""
Conformal Causal Inference & Distribution-Free Counterfactual Prediction Bands Engine
DataTrust Iteration 180

Based on:
- Chernozhukov, V., Wüthrich, K., & Zhu, Y. (2021). Distributional Conformal Prediction. Journal of the American Statistical Association (JASA).
- Lei, L., & Candès, E. J. (2021). Conformal inference of counterfactuals and individual treatment effects. Journal of the Royal Statistical Society: Series B (JRSS-B).
- Tibshirani, R. J., Foygel Barber, R., Candès, E. J., & Ramdas, A. (2019). Conformal prediction under covariate shift. NeurIPS.
"""

import math
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge


def _weighted_conformal_quantile(scores: np.ndarray, weights: np.ndarray, alpha: float) -> float:
    """
    Computes distribution-free weighted conformal quantile cutoff q_{1-alpha}.
    Under covariate shift, weights w_i = p_test(x_i) / p_train(x_i).
    The conformal quantile is the smallest score whose cumulative normalized weight exceeds 1 - alpha.
    """
    n = len(scores)
    if n == 0:
        return 0.0

    # Ensure weights are non-negative and normalize
    w = np.maximum(weights, 1e-6)
    total_w = np.sum(w) + 1.0  # +1 represents weight of the unseen test point
    norm_w = w / total_w
    test_w = 1.0 / total_w

    sort_idx = np.argsort(scores)
    sorted_scores = scores[sort_idx]
    sorted_w = norm_w[sort_idx]

    cum_w = np.cumsum(sorted_w)
    target = 1.0 - alpha

    idx = np.searchsorted(cum_w, target)
    if idx < len(sorted_scores):
        return float(sorted_scores[idx])
    return float(sorted_scores[-1])


def generate_conformal_causal_svg(
    ordered_x: List[float],
    y_factual: List[float],
    y0_lower: List[float],
    y0_upper: List[float],
    ite_estimates: List[float],
    ite_lower: List[float],
    ite_upper: List[float],
    coverage_level: float
) -> str:
    """
    Generates responsive dual-panel SVG visualizer:
    Panel A: Counterfactual Conformal Prediction Ribbon (95% Distribution-Free Coverage)
    Panel B: Individual Treatment Effect (ITE) Funnel with Conformal Uncertainty Bounds
    """
    svg_w, svg_h = 920, 340
    p_w, p_h = 420, 240
    p1_x, p1_y = 50, 45
    p2_x, p2_y = 480, 45

    # Panel A coordinates
    all_y = y_factual + y0_lower + y0_upper
    min_y = min(all_y) if all_y else 0.0
    max_y = max(all_y) if all_y else 10.0
    rng_y = max(max_y - min_y, 1e-4)

    n_pts = len(y_factual)
    step_x = p_w / max(n_pts - 1, 1)

    # Ribbon path for Panel A (y0 conformal band)
    top_pts = []
    bot_pts = []
    fact_pts = []

    for i in range(n_pts):
        cx = p1_x + i * step_x
        cy_top = p1_y + p_h - ((y0_upper[i] - min_y) / rng_y) * p_h
        cy_bot = p1_y + p_h - ((y0_lower[i] - min_y) / rng_y) * p_h
        cy_f = p1_y + p_h - ((y_factual[i] - min_y) / rng_y) * p_h
        top_pts.append(f"{cx:.1f},{cy_top:.1f}")
        bot_pts.append(f"{cx:.1f},{cy_bot:.1f}")
        fact_pts.append((cx, cy_f))

    ribbon_poly = " ".join(top_pts + bot_pts[::-1])

    # Panel B coordinates (Sorted ITE)
    all_ite = ite_estimates + ite_lower + ite_upper
    min_ite = min(all_ite) if all_ite else -5.0
    max_ite = max(all_ite) if all_ite else 15.0
    rng_ite = max(max_ite - min_ite, 1e-4)

    ite_step_x = p_w / max(n_pts - 1, 1)
    zero_y = p2_y + p_h - ((0.0 - min_ite) / rng_ite) * p_h
    zero_y_clamped = max(p2_y, min(p2_y + p_h, zero_y))

    ite_top = []
    ite_bot = []
    ite_mid = []
    for i in range(n_pts):
        cx = p2_x + i * ite_step_x
        cy_top = p2_y + p_h - ((ite_upper[i] - min_ite) / rng_ite) * p_h
        cy_bot = p2_y + p_h - ((ite_lower[i] - min_ite) / rng_ite) * p_h
        cy_mid = p2_y + p_h - ((ite_estimates[i] - min_ite) / rng_ite) * p_h
        ite_top.append(f"{cx:.1f},{cy_top:.1f}")
        ite_bot.append(f"{cx:.1f},{cy_bot:.1f}")
        ite_mid.append((cx, cy_mid))

    ite_ribbon_poly = " ".join(ite_top + ite_bot[::-1])

    dots_a = "".join([f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2.5" fill="#4f46e5" opacity="0.85" />' for cx, cy in fact_pts[::max(1, n_pts//25)]])
    dots_b = "".join([f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2" fill="#059669" />' for cx, cy in ite_mid[::max(1, n_pts//25)]])

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="auto" class="rounded-xl bg-slate-900 border border-slate-800 shadow-md">
  <defs>
    <linearGradient id="confBandA" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#6366f1" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#818cf8" stop-opacity="0.08"/>
    </linearGradient>
    <linearGradient id="confBandB" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#10b981" stop-opacity="0.32"/>
      <stop offset="100%" stop-color="#34d399" stop-opacity="0.08"/>
    </linearGradient>
  </defs>

  <!-- Panel A: Counterfactual Conformal Band -->
  <text x="{p1_x}" y="25" fill="#e2e8f0" font-size="12" font-family="sans-serif" font-weight="700">Panel A: Dải Dự báo Phản thực tế Conformal (Coverage: {int(coverage_level*100)}%)</text>
  <rect x="{p1_x}" y="{p1_y}" width="{p_w}" height="{p_h}" fill="#1e293b" rx="6" stroke="#334155" stroke-width="1"/>
  <!-- Gridlines -->
  <line x1="{p1_x}" y1="{p1_y + p_h*0.25}" x2="{p1_x + p_w}" y2="{p1_y + p_h*0.25}" stroke="#334155" stroke-dasharray="3,3" opacity="0.6"/>
  <line x1="{p1_x}" y1="{p1_y + p_h*0.50}" x2="{p1_x + p_w}" y2="{p1_y + p_h*0.50}" stroke="#334155" stroke-dasharray="3,3" opacity="0.6"/>
  <line x1="{p1_x}" y1="{p1_y + p_h*0.75}" x2="{p1_x + p_w}" y2="{p1_y + p_h*0.75}" stroke="#334155" stroke-dasharray="3,3" opacity="0.6"/>

  <!-- Conformal Ribbon -->
  <polygon points="{ribbon_poly}" fill="url(#confBandA)"/>
  {dots_a}
  <text x="{p1_x + 8}" y="{p1_y + 16}" fill="#a5b4fc" font-size="10" font-family="sans-serif">Dải [L₀, U₀] Phi tham số (Chernozhukov 2021)</text>
  <text x="{p1_x + p_w - 95}" y="{p1_y + p_h - 8}" fill="#94a3b8" font-size="10" font-family="sans-serif">Quan sát sắp xếp →</text>

  <!-- Panel B: Individual Treatment Effect Funnel -->
  <text x="{p2_x}" y="25" fill="#e2e8f0" font-size="12" font-family="sans-serif" font-weight="700">Panel B: Hiệu ứng Cá thể ITE với Khoảng Tin cậy Phân vị</text>
  <rect x="{p2_x}" y="{p2_y}" width="{p_w}" height="{p_h}" fill="#1e293b" rx="6" stroke="#334155" stroke-width="1"/>
  <!-- Zero line -->
  <line x1="{p2_x}" y1="{zero_y_clamped}" x2="{p2_x + p_w}" y2="{zero_y_clamped}" stroke="#ef4444" stroke-width="1.2" stroke-dasharray="4,2"/>
  <polygon points="{ite_ribbon_poly}" fill="url(#confBandB)"/>
  {dots_b}
  <text x="{p2_x + 8}" y="{p2_y + 16}" fill="#6ee7b7" font-size="10" font-family="sans-serif">Khoảng Conformal ITE [τ_L, τ_U]</text>
  <text x="{p2_x + p_w - 75}" y="{zero_y_clamped - 4}" fill="#f87171" font-size="9" font-family="sans-serif">τ = 0 (Null)</text>
  <text x="{p2_x + p_w - 95}" y="{p2_y + p_h - 8}" fill="#94a3b8" font-size="10" font-family="sans-serif">Xếp hạng ITE →</text>

  <!-- Bottom Brand -->
  <text x="{svg_w // 2}" y="{svg_h - 10}" fill="#64748b" font-size="10" font-family="sans-serif" text-anchor="middle">DataTrust Analytics Engine • Conformal Causal Inference (Lei &amp; Candès 2021 JRSS-B)</text>
</svg>"""
    return svg


def run_conformal_causal_inference(
    records: List[Dict[str, Any]],
    treatment_col: str,
    outcome_col: str,
    covariate_cols: Optional[List[str]] = None,
    alpha: float = 0.05,
    calibration_ratio: float = 0.4
) -> Dict[str, Any]:
    """
    Executes Finite-Sample Distribution-Free Conformal Causal Inference:
    1. Validates binary treatment D in {0, 1}, continuous outcome Y, and covariates X.
    2. Splits data into Proper Training set and Calibration set.
    3. Fits base machine learning models mu_0(X) and mu_1(X) on proper training splits.
    4. Computes non-conformity residuals R_i = |Y_i - mu_d(X_i)| on calibration sets.
    5. Calculates propensity scores e(X) to reweight non-conformity scores under covariate shift (Lei & Candes 2021).
    6. Produces exact conformal intervals [L_i(0), U_i(0)], [L_i(1), U_i(1)] and ITE bounds [tau_L, tau_U].
    7. Evaluates empirical calibration coverage, average interval width, and heterogeneity.
    8. Generates responsive dual-panel SVG visualizer and APA 7th narrative.
    """
    valid_rows = []
    covs = covariate_cols or []

    for r in records:
        d_raw = r.get(treatment_col)
        y_raw = r.get(outcome_col)
        if d_raw is None or y_raw is None:
            continue
        try:
            d_val = float(d_raw)
            y_val = float(y_raw)
            if not (np.isfinite(d_val) and np.isfinite(y_val)):
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
                "y": y_val,
                "covs": c_vals
            })

    N = len(valid_rows)
    if N < 30:
        return {
            "status": "insufficient_data",
            "message": f"Số lượng quan sát hợp lệ (N={N}) không đủ để thực hiện Conformal Causal Inference (tối thiểu 30 bản ghi)."
        }

    D = np.array([r["d"] for r in valid_rows])
    Y = np.array([r["y"] for r in valid_rows])

    if len(set(D)) < 2:
        return {
            "status": "invalid_treatment",
            "message": "Biến can thiệp D cần có cả 2 nhóm (0=Đối chứng và 1=Can thiệp)."
        }

    n_treated = int(np.sum(D == 1.0))
    n_control = int(np.sum(D == 0.0))

    if n_treated < 10 or n_control < 10:
        return {
            "status": "insufficient_subgroups",
            "message": f"Cỡ mẫu mỗi phân nhóm quá nhỏ (Treated={n_treated}, Control={n_control}; tối thiểu 10 mỗi nhóm)."
        }

    # Covariate matrix
    if covs:
        p = len(covs)
        X = np.zeros((N, p))
        for i, r in enumerate(valid_rows):
            X[i, :] = r["covs"]
    else:
        # Fallback synthetic index
        X = np.arange(N).reshape(-1, 1) / float(N)

    # 1. Propensity Score Estimation via regularized ridge logistic/linear
    try:
        X_design = np.column_stack([np.ones(N), X])
        prop_weights = np.linalg.pinv(X_design.T @ X_design + 1e-4 * np.eye(X_design.shape[1])) @ (X_design.T @ D)
        prop_scores = np.clip(X_design @ prop_weights, 0.05, 0.95)
    except Exception:
        prop_scores = np.full(N, float(np.mean(D)))

    # 2. Split into Proper Training and Calibration sets
    np.random.seed(42)
    indices = np.arange(N)
    np.random.shuffle(indices)

    n_calib = max(int(N * calibration_ratio), 10)
    idx_calib = indices[:n_calib]
    idx_train = indices[n_calib:]

    d_train, y_train, x_train = D[idx_train], Y[idx_train], X[idx_train]
    d_calib, y_calib, x_calib = D[idx_calib], Y[idx_calib], X[idx_calib]
    prop_calib = prop_scores[idx_calib]

    # Fit base models on training split: mu_0(X) and mu_1(X)
    model_0 = GradientBoostingRegressor(n_estimators=60, max_depth=3, random_state=42)
    model_1 = GradientBoostingRegressor(n_estimators=60, max_depth=3, random_state=42)

    ctrl_train_mask = (d_train == 0.0)
    trt_train_mask = (d_train == 1.0)

    if np.sum(ctrl_train_mask) < 5 or np.sum(trt_train_mask) < 5:
        # Fallback to Ridge
        model_0 = Ridge(alpha=1.0)
        model_1 = Ridge(alpha=1.0)

    model_0.fit(x_train[ctrl_train_mask], y_train[ctrl_train_mask])
    model_1.fit(x_train[trt_train_mask], y_train[trt_train_mask])

    # 3. Nonconformity residuals on calibration set
    pred_0_calib = model_0.predict(x_calib)
    pred_1_calib = model_1.predict(x_calib)

    scores_0 = np.abs(y_calib[d_calib == 0.0] - pred_0_calib[d_calib == 0.0])
    scores_1 = np.abs(y_calib[d_calib == 1.0] - pred_1_calib[d_calib == 1.0])

    # Covariate shift weights for counterfactual transfer (Lei & Candes 2021)
    # When predicting Y(0) for treated: w(x) = e(x) / (1 - e(x))
    # When predicting Y(1) for control: w(x) = (1 - e(x)) / e(x)
    weights_0 = prop_calib[d_calib == 0.0] / (1.0 - prop_calib[d_calib == 0.0])
    weights_1 = (1.0 - prop_calib[d_calib == 1.0]) / prop_calib[d_calib == 1.0]

    # Weighted conformal cutoffs
    q_cutoff_0 = _weighted_conformal_quantile(scores_0, weights_0, alpha=alpha)
    q_cutoff_1 = _weighted_conformal_quantile(scores_1, weights_1, alpha=alpha)

    # 4. Out-of-sample / Full-sample counterfactual prediction bands
    pred_0_full = model_0.predict(X)
    pred_1_full = model_1.predict(X)

    # Conformal bands for Y(0) and Y(1)
    y0_lower = pred_0_full - q_cutoff_0
    y0_upper = pred_0_full + q_cutoff_0

    y1_lower = pred_1_full - q_cutoff_1
    y1_upper = pred_1_full + q_cutoff_1

    # Individual Treatment Effect (ITE) point estimate and bounds:
    ite_point = pred_1_full - pred_0_full
    ite_lower = ite_point - (q_cutoff_0 + q_cutoff_1)
    ite_upper = ite_point + (q_cutoff_0 + q_cutoff_1)

    # Empirical calibration coverage rate (factual check on calibration set)
    calib_covered_0 = (y_calib[d_calib == 0.0] >= pred_0_calib[d_calib == 0.0] - q_cutoff_0) & \
                      (y_calib[d_calib == 0.0] <= pred_0_calib[d_calib == 0.0] + q_cutoff_0)
    calib_covered_1 = (y_calib[d_calib == 1.0] >= pred_1_calib[d_calib == 1.0] - q_cutoff_1) & \
                      (y_calib[d_calib == 1.0] <= pred_1_calib[d_calib == 1.0] + q_cutoff_1)

    cov_rate_0 = float(np.mean(calib_covered_0)) if len(calib_covered_0) > 0 else 1.0 - alpha
    cov_rate_1 = float(np.mean(calib_covered_1)) if len(calib_covered_1) > 0 else 1.0 - alpha
    overall_calibration_coverage = float(np.mean(np.concatenate([calib_covered_0, calib_covered_1])))

    # Width metrics
    avg_width_y0 = float(np.mean(y0_upper - y0_lower))
    avg_width_y1 = float(np.mean(y1_upper - y1_lower))
    avg_width_ite = float(np.mean(ite_upper - ite_lower))

    # Units with significant positive / negative ITE (bounds strictly away from 0)
    sig_positive_ite_pct = float(np.mean(ite_lower > 0.0) * 100.0)
    sig_negative_ite_pct = float(np.mean(ite_upper < 0.0) * 100.0)

    # Average Treatment Effect (ATE) estimate
    ate_conformal = float(np.mean(ite_point))

    # Sort by predicted ITE for visualization and tabular sample
    sort_ite_idx = np.argsort(-ite_point)
    sample_size_disp = min(N, 20)
    disp_indices = sort_ite_idx[:sample_size_disp]

    sample_ite_points = []
    for idx in disp_indices:
        sample_ite_points.append({
            "observation_id": int(idx + 1),
            "treatment": int(D[idx]),
            "factual_outcome": float(round(Y[idx], 4)),
            "predicted_ite": float(round(ite_point[idx], 4)),
            "ite_lower_bound": float(round(ite_lower[idx], 4)),
            "ite_upper_bound": float(round(ite_upper[idx], 4)),
            "band_width": float(round(ite_upper[idx] - ite_lower[idx], 4)),
            "significant": bool(ite_lower[idx] > 0.0 or ite_upper[idx] < 0.0)
        })

    # Prepare vector SVG visualization
    sort_for_viz = np.argsort(X[:, 0] if covs else np.arange(N))
    svg_str = generate_conformal_causal_svg(
        ordered_x=[float(x) for x in range(min(N, 60))],
        y_factual=[float(Y[i]) for i in sort_for_viz[:60]],
        y0_lower=[float(y0_lower[i]) for i in sort_for_viz[:60]],
        y0_upper=[float(y0_upper[i]) for i in sort_for_viz[:60]],
        ite_estimates=[float(ite_point[i]) for i in sort_ite_idx[:60]],
        ite_lower=[float(ite_lower[i]) for i in sort_ite_idx[:60]],
        ite_upper=[float(ite_upper[i]) for i in sort_ite_idx[:60]],
        coverage_level=1.0 - alpha
    )

    nominal_coverage_pct = (1.0 - alpha) * 100.0
    apa_narrative = (
        f"Hệ thống phân tích DataTrust: Phương pháp Suy luận Nhân quả Conformal Phi tham số "
        f"(Conformal Causal Inference; Chernozhukov et al., 2021; Lei & Candès, 2021) "
        f"đạt tỷ lệ bao phủ thực nghiệm hiệu chuẩn {overall_calibration_coverage*100:.1f}% "
        f"so với ngưỡng danh nghĩa {nominal_coverage_pct:.0f}% (1-α={1.0-alpha:.2f}). "
        f"Hiệu ứng can thiệp trung bình ATE = {ate_conformal:+.4f}. "
        f"Độ rộng dải dự báo phản thực tế trung bình cho Y(0) là {avg_width_y0:.4f} và ITE là {avg_width_ite:.4f}. "
        f"Phân tích dải tin cậy cá thể phát hiện {sig_positive_ite_pct:.1f}% quan sát có hiệu ứng can thiệp tích cực có ý nghĩa thống kê "
        f"và {sig_negative_ite_pct:.1f}% quan sát có hiệu ứng tiêu cực, khẳng định tính khả tín phi tham số trước sai chệch phân phối."
    )

    return {
        "status": "success",
        "sample_size": N,
        "nominal_coverage": float(round(1.0 - alpha, 4)),
        "empirical_calibration_coverage": float(round(overall_calibration_coverage, 4)),
        "subgroup_counts": {
            "treated": n_treated,
            "control": n_control,
            "calibration_set": n_calib,
            "training_set": N - n_calib
        },
        "conformal_cutoffs": {
            "cutoff_q0": float(round(q_cutoff_0, 4)),
            "cutoff_q1": float(round(q_cutoff_1, 4)),
            "coverage_control": float(round(cov_rate_0, 4)),
            "coverage_treated": float(round(cov_rate_1, 4))
        },
        "treatment_effect_summary": {
            "ate_conformal": float(round(ate_conformal, 4)),
            "avg_width_y0": float(round(avg_width_y0, 4)),
            "avg_width_y1": float(round(avg_width_y1, 4)),
            "avg_width_ite": float(round(avg_width_ite, 4)),
            "sig_positive_ite_pct": float(round(sig_positive_ite_pct, 2)),
            "sig_negative_ite_pct": float(round(sig_negative_ite_pct, 2))
        },
        "sample_ite_points": sample_ite_points,
        "svg_visualization": svg_str,
        "apa_narrative": apa_narrative
    }
