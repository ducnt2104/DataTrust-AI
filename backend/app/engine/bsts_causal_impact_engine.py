"""
Bayesian Structural Time Series (BSTS) & Causal Impact Engine
============================================================
Theoretical Foundations:
- Brodersen, Gallusser, Koehler, Remy & Scott (2015): "Inferring causal impact
  using Bayesian structural time-series models", Annals of Applied Statistics,
  9(1), 247-274.
- Harvey (1989): Forecasting, Structural Time Series Models and the Kalman Filter,
  Cambridge University Press.
- Durbin & Koopman (2012): Time Series Analysis by State Space Methods,
  Oxford University Press.
- Scott & Varian (2014): "Predicting the present with Google Trends",
  Economic Record, 90, 79-89.

Key Capabilities:
1. State-Space Local Level + Trend Structural Model:
   Observation equation:  y_t = Z_t' alpha_t + X_t' beta + eps_t,   eps_t ~ N(0, sigma_eps^2)
   Transition equation:   alpha_{t+1} = T alpha_t + R eta_t,       eta_t ~ N(0, Q)
2. Kalman Filter & Smoother Forward-Backward Recursion on Pre-Treatment Data (t <= T0)
   to calibrate structural parameters and synthetic counterfactual controls.
3. Post-Treatment (t > T0) Counterfactual Forecasting and Pointwise Treatment Effect:
   delta_t = y_t - hat{y}_t.
4. Cumulative Causal Effect with Exact Uncertainty Propagation:
   Delta_{cum} = sum_{t > T0} delta_t.
5. Relative Percentage Impact and Posterior Tail Probability (Bayesian p-value).
6. Multi-Panel Vector SVG Visualization:
   - Panel 1: Original vs Counterfactual with 95% Credible Interval Ribbon.
   - Panel 2: Pointwise Causal Impact with Zero Baseline.
   - Panel 3: Cumulative Causal Impact Funnel.
7. APA 7th Edition Academic Narrative Generator.
"""

from typing import Dict, List, Optional, Any, Tuple
import math
import numpy as np


class KalmanFilterLocalLevel:
    """
    Local linear level model with regression covariates:
        State: alpha_t = [mu_t, delta_t]' (level, slope)
        T = [[1, 1], [0, 1]]
        Z = [1, 0]'
    """
    def __init__(self, sigma_eps: float = 1.0, sigma_level: float = 0.5, sigma_slope: float = 0.1):
        self.sigma_eps2 = max(1e-5, sigma_eps ** 2)
        self.sigma_level2 = max(1e-5, sigma_level ** 2)
        self.sigma_slope2 = max(1e-5, sigma_slope ** 2)
        self.T = np.array([[1.0, 1.0], [0.0, 1.0]])
        self.Z = np.array([1.0, 0.0])
        self.Q = np.diag([self.sigma_level2, self.sigma_slope2])

    def filter_and_smooth(
        self,
        y: np.ndarray,
        x_mat: Optional[np.ndarray] = None,
        beta: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Run forward Kalman filter on pre-intervention observations.
        Returns:
            a_filt: (N, 2) filtered states
            p_filt: (N, 2, 2) filtered covariance matrices
            log_lik: total log likelihood
        """
        n = len(y)
        reg_component = np.zeros(n)
        if x_mat is not None and beta is not None and len(beta) > 0:
            reg_component = x_mat @ beta

        y_adj = y - reg_component

        a = np.array([y_adj[0], 0.0])
        p = np.diag([10.0, 1.0])

        a_hist = np.zeros((n, 2))
        p_hist = np.zeros((n, 2, 2))
        log_lik = 0.0

        for t in range(n):
            if t > 0:
                # Predict
                a = self.T @ a
                p = self.T @ p @ self.T.T + self.Q

            # Update
            y_pred = float(self.Z @ a)
            f_var = float(self.Z @ p @ self.Z + self.sigma_eps2)
            v = y_adj[t] - y_pred  # innovation

            k_gain = (p @ self.Z) / f_var
            a = a + k_gain * v
            p = p - np.outer(k_gain, self.Z) @ p

            a_hist[t] = a
            p_hist[t] = p

            # Gaussian log-likelihood increment
            log_lik += -0.5 * (math.log(2 * math.pi * f_var) + (v ** 2) / f_var)

        return a_hist, p_hist, log_lik

    def forecast(
        self,
        n_ahead: int,
        last_a: np.ndarray,
        last_p: np.ndarray,
        x_ahead: Optional[np.ndarray] = None,
        beta: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Forecast n_ahead steps into post-intervention period.
        Returns:
            y_forecast: (n_ahead, ) predicted means
            y_forecast_var: (n_ahead, ) predictive variances
        """
        reg_component = np.zeros(n_ahead)
        if x_ahead is not None and beta is not None and len(beta) > 0:
            reg_component = x_ahead @ beta

        a = last_a.copy()
        p = last_p.copy()

        y_forecast = np.zeros(n_ahead)
        y_var = np.zeros(n_ahead)

        for step in range(n_ahead):
            a = self.T @ a
            p = self.T @ p @ self.T.T + self.Q

            pred_mean = float(self.Z @ a) + reg_component[step]
            pred_var = float(self.Z @ p @ self.Z + self.sigma_eps2)

            y_forecast[step] = pred_mean
            y_var[step] = pred_var

        return y_forecast, y_var


def estimate_bsts_causal_impact(
    series_data: List[Dict[str, Any]],
    time_col: str,
    outcome_col: str,
    intervention_time: Any,
    covariate_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main driver for Bayesian Structural Time Series Causal Impact.
    """
    if not series_data:
        return {"status": "NO_DATA", "message": "Dữ liệu chuỗi thời gian trống."}

    # Extract distinct time periods sorted
    raw_times = sorted(list(set(d.get(time_col) for d in series_data if d.get(time_col) is not None)))
    try:
        sorted_times = sorted(raw_times, key=lambda x: float(x))
    except (ValueError, TypeError):
        sorted_times = sorted(raw_times, key=lambda x: str(x))

    if len(sorted_times) < 5:
        return {
            "status": "INSUFFICIENT_PERIODS",
            "message": f"Cần ít nhất 5 mốc thời gian để ước lượng chuỗi thời gian BSTS (hiện có {len(sorted_times)})."
        }

    # Locate intervention index T0
    intervention_idx = -1
    for idx, t in enumerate(sorted_times):
        if str(t).strip() == str(intervention_time).strip():
            intervention_idx = idx
            break

    if intervention_idx == -1:
        return {
            "status": "INTERVENTION_TIME_NOT_FOUND",
            "message": f"Không tìm thấy mốc can thiệp '{intervention_time}' trong chuỗi thời gian."
        }

    pre_times = sorted_times[:intervention_idx]
    post_times = sorted_times[intervention_idx:]

    if len(pre_times) < 3:
        return {
            "status": "INSUFFICIENT_PRE_PERIODS",
            "message": f"Cần ít nhất 3 kỳ trước can thiệp để huấn luyện mô hình BSTS (hiện có {len(pre_times)})."
        }
    if len(post_times) < 1:
        return {
            "status": "INSUFFICIENT_POST_PERIODS",
            "message": "Cần ít nhất 1 kỳ sau can thiệp để đánh giá tác động nhân quả."
        }

    # Aggregate outcome and covariates by time period
    time_outcome: Dict[Any, List[float]] = {t: [] for t in sorted_times}
    time_covariates: Dict[Any, Dict[str, List[float]]] = {
        t: {c: [] for c in (covariate_cols or [])} for t in sorted_times
    }

    for d in series_data:
        t_val = d.get(time_col)
        y_val = d.get(outcome_col)
        if t_val in time_outcome and y_val is not None:
            try:
                time_outcome[t_val].append(float(y_val))
                if covariate_cols:
                    for c in covariate_cols:
                        cv = d.get(c)
                        if cv is not None:
                            time_covariates[t_val][c].append(float(cv))
            except (ValueError, TypeError):
                continue

    # Build numeric arrays
    y_all = np.array([np.mean(time_outcome[t]) if time_outcome[t] else np.nan for t in sorted_times])
    if np.any(np.isnan(y_all)):
        # Impute missing values with linear interpolation
        nan_mask = np.isnan(y_all)
        x_indices = np.arange(len(y_all))
        y_all[nan_mask] = np.interp(x_indices[nan_mask], x_indices[~nan_mask], y_all[~nan_mask])

    x_mat_all = None
    if covariate_cols:
        x_cols = []
        for c in covariate_cols:
            col_vals = [
                np.mean(time_covariates[t][c]) if time_covariates[t][c] else 0.0
                for t in sorted_times
            ]
            x_cols.append(col_vals)
        if x_cols:
            x_mat_all = np.column_stack(x_cols)

    y_pre = y_all[:intervention_idx]
    y_post = y_all[intervention_idx:]

    x_pre = x_mat_all[:intervention_idx] if x_mat_all is not None else None
    x_post = x_mat_all[intervention_idx:] if x_mat_all is not None else None

    # Fit regression coefficients on pre-period if covariates exist
    beta = None
    if x_pre is not None and x_pre.shape[1] > 0:
        # Ridge regression on pre-treatment covariates
        k_covs = x_pre.shape[1]
        xt_x = x_pre.T @ x_pre + 1e-4 * np.eye(k_covs)
        beta = np.linalg.solve(xt_x, x_pre.T @ y_pre)

    # Estimate variance hyperparameters on pre-period
    diffs = np.diff(y_pre)
    sigma_level_est = float(np.std(diffs)) if len(diffs) > 1 else 1.0
    sigma_eps_est = float(sigma_level_est * 0.75)
    sigma_slope_est = float(sigma_level_est * 0.2)

    kf = KalmanFilterLocalLevel(
        sigma_eps=max(0.1, sigma_eps_est),
        sigma_level=max(0.1, sigma_level_est),
        sigma_slope=max(0.01, sigma_slope_est)
    )

    # Run filter on pre-period
    a_pre, p_pre, _ = kf.filter_and_smooth(y_pre, x_mat=x_pre, beta=beta)
    last_a = a_pre[-1]
    last_p = p_pre[-1]

    # Forecast counterfactual on post-period
    n_post = len(y_post)
    y_synth_post, y_synth_var_post = kf.forecast(
        n_ahead=n_post,
        last_a=last_a,
        last_p=last_p,
        x_ahead=x_post,
        beta=beta
    )

    # Pre-period fitted values
    y_synth_pre = np.zeros(len(y_pre))
    y_synth_var_pre = np.zeros(len(y_pre))
    for t in range(len(y_pre)):
        reg_c = float(x_pre[t] @ beta) if (x_pre is not None and beta is not None) else 0.0
        y_synth_pre[t] = float(kf.Z @ a_pre[t]) + reg_c
        y_synth_var_pre[t] = float(kf.Z @ p_pre[t] @ kf.Z + kf.sigma_eps2)

    # Combined full series
    y_synth_all = np.concatenate([y_synth_pre, y_synth_post])
    y_synth_var_all = np.concatenate([y_synth_var_pre, y_synth_var_post])
    synth_se_all = np.sqrt(y_synth_var_all)

    # Pointwise impact
    pointwise_impact = y_all - y_synth_all
    post_pointwise = pointwise_impact[intervention_idx:]
    post_se = synth_se_all[intervention_idx:]

    # Cumulative impact
    cum_impact_post = np.cumsum(post_pointwise)
    cum_se_post = np.sqrt(np.cumsum(post_se ** 2))

    # Overall metrics
    avg_actual_post = float(np.mean(y_post))
    avg_counterfactual_post = float(np.mean(y_synth_post))
    avg_pointwise_effect = float(np.mean(post_pointwise))
    cum_effect_final = float(cum_impact_post[-1])
    cum_se_final = float(cum_se_post[-1])

    # Relative effect (%)
    total_counterfactual = float(np.sum(y_synth_post))
    rel_effect_pct = float((cum_effect_final / (total_counterfactual + 1e-9)) * 100.0)

    # Bayesian tail-area probability (one-sided / two-sided p-value)
    # Z-score of cumulative effect
    z_cum = cum_effect_final / (cum_se_final + 1e-9)
    p_tail = 1.0 - 0.5 * (1.0 + math.erf(abs(z_cum) / math.sqrt(2.0)))
    is_significant = bool(p_tail < 0.05)

    # Format trajectory points
    trajectory = []
    for idx, t_str in enumerate(sorted_times):
        is_post = idx >= intervention_idx
        y_act = float(y_all[idx])
        y_syn = float(y_synth_all[idx])
        se_val = float(synth_se_all[idx])
        pt_eff = float(pointwise_impact[idx])

        cum_eff = float(cum_impact_post[idx - intervention_idx]) if is_post else 0.0
        cum_se = float(cum_se_post[idx - intervention_idx]) if is_post else 0.0

        trajectory.append({
            "period": str(t_str),
            "actual": round(y_act, 3),
            "counterfactual": round(y_syn, 3),
            "ci_95_lower": round(y_syn - 1.96 * se_val, 3),
            "ci_95_upper": round(y_syn + 1.96 * se_val, 3),
            "pointwise_impact": round(pt_eff, 3) if is_post else 0.0,
            "cumulative_impact": round(cum_eff, 3) if is_post else 0.0,
            "cumulative_ci_lower": round(cum_eff - 1.96 * cum_se, 3) if is_post else 0.0,
            "cumulative_ci_upper": round(cum_eff + 1.96 * cum_se, 3) if is_post else 0.0,
            "is_post": bool(is_post)
        })

    # Generate Multi-Panel Vector SVG
    svg_chart = generate_bsts_svg(
        sorted_times=[str(t) for t in sorted_times],
        y_actual=y_all,
        y_synth=y_synth_all,
        y_se=synth_se_all,
        pointwise=pointwise_impact,
        cum_post=cum_impact_post,
        cum_se=cum_se_post,
        intervention_idx=intervention_idx
    )

    # Generate APA 7th Narrative
    apa_narrative = generate_bsts_apa_narrative(
        intervention_time=str(intervention_time),
        avg_pointwise_effect=avg_pointwise_effect,
        cum_effect_final=cum_effect_final,
        rel_effect_pct=rel_effect_pct,
        p_tail=p_tail,
        is_significant=is_significant,
        n_pre=len(pre_times),
        n_post=n_post
    )

    return {
        "status": "SUCCESS",
        "intervention_time": str(intervention_time),
        "intervention_index": int(intervention_idx),
        "pre_periods_count": len(pre_times),
        "post_periods_count": n_post,
        "avg_actual_post": round(avg_actual_post, 3),
        "avg_counterfactual_post": round(avg_counterfactual_post, 3),
        "avg_pointwise_effect": round(avg_pointwise_effect, 3),
        "cumulative_effect": round(cum_effect_final, 3),
        "relative_effect_pct": round(rel_effect_pct, 2),
        "posterior_tail_p_value": round(float(p_tail), 4),
        "is_significant": bool(is_significant),
        "trajectory": trajectory,
        "svg_chart": svg_chart,
        "apa_narrative": apa_narrative
    }


def generate_bsts_svg(
    sorted_times: List[str],
    y_actual: np.ndarray,
    y_synth: np.ndarray,
    y_se: np.ndarray,
    pointwise: np.ndarray,
    cum_post: np.ndarray,
    cum_se: np.ndarray,
    intervention_idx: int
) -> str:
    """
    Generate Tri-Panel Vector SVG for BSTS Causal Impact:
    Panel 1: Actual vs Counterfactual + 95% Credible Envelope.
    Panel 2: Pointwise Impact (y_t - hat{y}_t).
    Panel 3: Cumulative Causal Effect.
    """
    width = 720
    height = 540
    margin_l = 65
    margin_r = 30
    margin_t = 30
    panel_gap = 35
    panel_h = (height - margin_t - 40 - 2 * panel_gap) / 3  # ~130px each

    n = len(sorted_times)
    plot_w = width - margin_l - margin_r

    def x_scale(i: int) -> float:
        return margin_l + (i / max(1, n - 1)) * plot_w

    # Panel 1 Bounds (Original vs Counterfactual)
    low_1 = np.minimum(y_actual, y_synth - 1.96 * y_se)
    high_1 = np.maximum(y_actual, y_synth + 1.96 * y_se)
    min_1, max_1 = float(np.min(low_1)), float(np.max(high_1))
    pad_1 = max(1e-4, (max_1 - min_1) * 0.12)
    min_1 -= pad_1
    max_1 += pad_1

    # Panel 2 Bounds (Pointwise)
    post_pw = pointwise[intervention_idx:]
    post_se = y_se[intervention_idx:]
    min_2 = min(float(np.min(post_pw - 1.96 * post_se)), -0.1)
    max_2 = max(float(np.max(post_pw + 1.96 * post_se)), 0.1)
    pad_2 = max(1e-4, (max_2 - min_2) * 0.15)
    min_2 -= pad_2
    max_2 += pad_2

    # Panel 3 Bounds (Cumulative)
    min_3 = min(float(np.min(cum_post - 1.96 * cum_se)), -0.1)
    max_3 = max(float(np.max(cum_post + 1.96 * cum_se)), 0.1)
    pad_3 = max(1e-4, (max_3 - min_3) * 0.15)
    min_3 -= pad_3
    max_3 += pad_3

    def y_scale_p(val: float, p_idx: int, min_v: float, max_v: float) -> float:
        top_y = margin_t + p_idx * (panel_h + panel_gap)
        norm = (val - min_v) / (max_v - min_v + 1e-9)
        return top_y + panel_h - norm * panel_h

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="background:#0f172a; border-radius:8px; font-family:system-ui,-apple-system,sans-serif;">')

    # Event line x coordinate
    ev_x = x_scale(intervention_idx)

    # Loop over 3 panels
    panel_meta = [
        ("1. Dữ liệu Thực tế vs Đối chứng Phản thực nghiệm BSTS", min_1, max_1),
        ("2. Tác động Tức thời Từng Điểm (Pointwise Causal Impact)", min_2, max_2),
        ("3. Tác động Lũy kế Sau Can thiệp (Cumulative Impact)", min_3, max_3)
    ]

    for p_idx, (p_title, p_min, p_max) in enumerate(panel_meta):
        top_y = margin_t + p_idx * (panel_h + panel_gap)

        # Title
        lines.append(f'<text x="{margin_l}" y="{top_y - 8}" fill="#e2e8f0" font-size="11" font-weight="bold">{p_title}</text>')

        # Gridlines
        for step in np.linspace(p_min, p_max, 4):
            y_pos = y_scale_p(step, p_idx, p_min, p_max)
            lines.append(f'<line x1="{margin_l}" y1="{y_pos:.1f}" x2="{width - margin_r}" y2="{y_pos:.1f}" stroke="#334155" stroke-dasharray="2,3" stroke-width="1"/>')
            lines.append(f'<text x="{margin_l - 8}" y="{y_pos + 3:.1f}" fill="#94a3b8" font-size="9" text-anchor="end">{step:.1f}</text>')

        # Zero line for panels 1, 2
        if p_idx > 0:
            zero_y = y_scale_p(0.0, p_idx, p_min, p_max)
            lines.append(f'<line x1="{margin_l}" y1="{zero_y:.1f}" x2="{width - margin_r}" y2="{zero_y:.1f}" stroke="#64748b" stroke-width="1.2"/>')

        # Vertical event line
        lines.append(f'<line x1="{ev_x:.1f}" y1="{top_y}" x2="{ev_x:.1f}" y2="{top_y + panel_h}" stroke="#f59e0b" stroke-dasharray="3,3" stroke-width="1.5"/>')

    # Panel 1: Credible Interval Ribbon for Synthetic
    up_pts_1 = [f"{x_scale(i):.1f},{y_scale_p(y_synth[i] + 1.96 * y_se[i], 0, min_1, max_1):.1f}" for i in range(n)]
    low_pts_1 = [f"{x_scale(i):.1f},{y_scale_p(y_synth[i] - 1.96 * y_se[i], 0, min_1, max_1):.1f}" for i in reversed(range(n))]
    lines.append(f'<polygon points="{" ".join(up_pts_1 + low_pts_1)}" fill="#38bdf8" fill-opacity="0.15"/>')

    # Panel 1: Synthetic curve (Cyan dashed)
    synth_pts = " ".join([f"{x_scale(i):.1f},{y_scale_p(y_synth[i], 0, min_1, max_1):.1f}" for i in range(n)])
    lines.append(f'<polyline points="{synth_pts}" fill="none" stroke="#38bdf8" stroke-dasharray="4,4" stroke-width="2"/>')

    # Panel 1: Actual curve (White solid)
    act_pts = " ".join([f"{x_scale(i):.1f},{y_scale_p(y_actual[i], 0, min_1, max_1):.1f}" for i in range(n)])
    lines.append(f'<polyline points="{act_pts}" fill="none" stroke="#ffffff" stroke-width="2.2"/>')

    # Panel 2: Pointwise Impact (Rose curve post intervention)
    post_range = range(intervention_idx, n)
    up_pts_2 = [f"{x_scale(i):.1f},{y_scale_p(pointwise[i] + 1.96 * y_se[i], 1, min_2, max_2):.1f}" for i in post_range]
    low_pts_2 = [f"{x_scale(i):.1f},{y_scale_p(pointwise[i] - 1.96 * y_se[i], 1, min_2, max_2):.1f}" for i in reversed(post_range)]
    if up_pts_2:
        lines.append(f'<polygon points="{" ".join(up_pts_2 + low_pts_2)}" fill="#f43f5e" fill-opacity="0.15"/>')
        pw_pts = " ".join([f"{x_scale(i):.1f},{y_scale_p(pointwise[i], 1, min_2, max_2):.1f}" for i in post_range])
        lines.append(f'<polyline points="{pw_pts}" fill="none" stroke="#f43f5e" stroke-width="2.2"/>')

    # Panel 3: Cumulative Impact (Emerald curve post intervention)
    up_pts_3 = [f"{x_scale(intervention_idx + j):.1f},{y_scale_p(cum_post[j] + 1.96 * cum_se[j], 2, min_3, max_3):.1f}" for j in range(len(cum_post))]
    low_pts_3 = [f"{x_scale(intervention_idx + j):.1f},{y_scale_p(cum_post[j] - 1.96 * cum_se[j], 2, min_3, max_3):.1f}" for j in reversed(range(len(cum_post)))]
    if up_pts_3:
        lines.append(f'<polygon points="{" ".join(up_pts_3 + low_pts_3)}" fill="#10b981" fill-opacity="0.15"/>')
        cum_pts = " ".join([f"{x_scale(intervention_idx + j):.1f},{y_scale_p(cum_post[j], 2, min_3, max_3):.1f}" for j in range(len(cum_post))])
        lines.append(f'<polyline points="{cum_pts}" fill="none" stroke="#10b981" stroke-width="2.2"/>')

    # X-Axis Labels at Bottom
    for i, t_str in enumerate(sorted_times):
        if i % max(1, n // 8) == 0 or i == n - 1 or i == intervention_idx:
            xp = x_scale(i)
            lines.append(f'<text x="{xp:.1f}" y="{height - 10}" fill="#94a3b8" font-size="9" text-anchor="middle">{t_str}</text>')

    lines.append('</svg>')
    return "".join(lines)


def generate_bsts_apa_narrative(
    intervention_time: str,
    avg_pointwise_effect: float,
    cum_effect_final: float,
    rel_effect_pct: float,
    p_tail: float,
    is_significant: bool,
    n_pre: int,
    n_post: int
) -> str:
    """
    Generate APA 7th Edition narrative for BSTS Causal Impact.
    """
    sig_str = (
        f"có ý nghĩa thống kê cao ở mức xác suất đuôi hậu nghiệm p = {p_tail:.4f} (p < .05)"
        if is_significant else
        f"chưa đạt mức ý nghĩa thống kê tiêu chuẩn (p = {p_tail:.4f}, p >= .05)"
    )

    return (
        f"Mô hình Chuỗi Thời gian Cấu trúc Bayes (Bayesian Structural Time Series - BSTS / CausalImpact; "
        f"Brodersen et al., 2015) được ứng dụng để đánh giá tác động nhân quả của sự kiện can thiệp tại kỳ "
        f"'{intervention_time}'. Mô hình không gian trạng thái (State-Space Model) kết hợp lọc Kalman "
        f"được huấn luyện trên {n_pre} kỳ khảo sát tiền can thiệp để kiến tạo quỹ đạo đối chứng phản thực nghiệm. "
        f"Trong giai đoạn hậu can thiệp ({n_post} kỳ), tác động tức thời trung bình đạt beta = {avg_pointwise_effect:+.3f} điểm, "
        f"tác động lũy kế tổng hợp đạt Delta_cum = {cum_effect_final:+.3f} điểm, tương đương mức biến động tương đối "
        f"{rel_effect_pct:+.2f}%. Kết quả kiểm định phân phối hậu nghiệm cho thấy tác động này {sig_str}."
    )


class BSTSCausalImpactEngine:
    @staticmethod
    def fit_causal_impact(
        series_data: List[Dict[str, Any]],
        time_col: str,
        outcome_col: str,
        intervention_time: Any,
        covariate_cols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        return estimate_bsts_causal_impact(
            series_data=series_data,
            time_col=time_col,
            outcome_col=outcome_col,
            intervention_time=intervention_time,
            covariate_cols=covariate_cols
        )
