"""
Synthetic Control Method (SCM) Engine for Comparative Case Studies & Policy Impact
==================================================================================
Theoretical Foundations:
- Abadie & Gardeazabal (2003): "The Economic Costs of Conflict: A Case Study of the
  Basque Country", American Economic Review, 93(1), 113-132.
- Abadie, Diamond & Hainmueller (2010): "Synthetic Control Methods for Comparative
  Case Studies: Estimating the Effect of California's Tobacco Control Program",
  Journal of the American Statistical Association, 105(490), 493-505.
- Abadie (2021): "Using Synthetic Controls: Feasibility, Data Requirements, and
  Methodological Aspects", Journal of Economic Literature, 59(2), 391-425.
- Doudchenko & Imbens (2016): "Balancing, Regression, and Difference-in-Differences:
  Synthetic Control Methods in Comparative Case Studies", NBER.

Key Capabilities:
1. Constrained Convex Optimization:
   min_W (X_1 - X_0 W)' V (X_1 - X_0 W) subject to w_j >= 0 and sum(w_j) = 1.
2. Synthetic Counterfactual Trajectory & Average Post-Treatment Effect (ATT).
3. Pre- and Post-Treatment Root Mean Squared Prediction Error (RMSPE).
4. Placebo in-Space Permutation Inference (Abadie et al. 2010) across all donor units
   to calculate exact empirical p-values without normality assumptions.
5. Dual-Panel Vector SVG Plot: Trajectory + Placebo Gap Envelope.
6. APA 7th Edition Academic Narrative Generator.
"""

from typing import Dict, List, Optional, Any, Tuple
import math
import numpy as np
import scipy.optimize as opt


def solve_synthetic_control_weights(
    x1: np.ndarray,
    x0: np.ndarray,
    v_weights: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, float]:
    """
    Solve for donor unit weights W >= 0, sum(W) = 1 that minimize:
        (X1 - X0 @ W).T @ V @ (X1 - X0 @ W)
    x1: (K, ) vector of treated unit predictors.
    x0: (K, J) matrix of donor unit predictors.
    v_weights: (K, ) diagonal elements of V matrix. Defaults to normalized inverse variances.
    Returns:
        (w_opt, loss_val)
    """
    k, j = x0.shape
    if v_weights is None:
        # Standardize scale across predictors using inverse sample variance
        var_x0 = np.var(x0, axis=1)
        var_x0 = np.where(var_x0 < 1e-6, 1.0, var_x0)
        v_weights = 1.0 / var_x0
        v_weights = v_weights / np.sum(v_weights)

    sqrt_v = np.sqrt(v_weights)[:, np.newaxis]  # (K, 1)
    scaled_x0 = x0 * sqrt_v                     # (K, J)
    scaled_x1 = x1 * np.sqrt(v_weights)         # (K, )

    # Quadratic objective: 0.5 * W.T @ (2 * X0.T @ X0) @ W - (2 * X1.T @ X0) @ W + const
    h = 2.0 * (scaled_x0.T @ scaled_x0)
    # Regularization to ensure strict positive definiteness
    h += 1e-5 * np.eye(j)
    c = -2.0 * (scaled_x1.T @ scaled_x0)

    def objective(w: np.ndarray) -> float:
        return float(0.5 * w @ h @ w + c @ w)

    def gradient(w: np.ndarray) -> np.ndarray:
        return h @ w + c

    # Bounds: w_j in [0, 1]
    bounds = [(0.0, 1.0) for _ in range(j)]
    # Constraint: sum(w_j) = 1
    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0, 'jac': lambda w: np.ones(j)}]

    # Initial guess: equal weights
    w0 = np.full(j, 1.0 / j)

    res = opt.minimize(
        objective,
        w0,
        jac=gradient,
        bounds=bounds,
        constraints=constraints,
        method='SLSQP',
        options={'maxiter': 1000, 'ftol': 1e-9}
    )

    w_opt = np.maximum(res.x, 0.0)
    w_opt /= np.sum(w_opt)
    loss = float(np.sum(v_weights * ((x1 - x0 @ w_opt) ** 2)))
    return w_opt, loss


def calculate_synthetic_control(
    panel_data: List[Dict[str, Any]],
    unit_col: str,
    period_col: str,
    outcome_col: str,
    treated_unit: str,
    treatment_period: Any,
    covariate_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main computation for Synthetic Control Method.
    panel_data: list of observation dicts.
    treated_unit: identifier of treated unit.
    treatment_period: cutoff period T0 (first period of intervention).
    """
    if not panel_data:
        return {"status": "NO_DATA", "message": "Dữ liệu trống, không thể thực hiện ước lượng Synthetic Control."}

    # Extract distinct units and periods
    units_raw = sorted(list(set(str(d.get(unit_col, "")).strip() for d in panel_data if str(d.get(unit_col, "")).strip())))
    if treated_unit not in units_raw:
        return {
            "status": "TREATED_UNIT_NOT_FOUND",
            "message": f"Không tìm thấy đơn vị can thiệp '{treated_unit}' trong tập dữ liệu."
        }

    donors = [u for u in units_raw if u != treated_unit]
    if len(donors) < 2:
        return {
            "status": "INSUFFICIENT_DONORS",
            "message": f"Cần ít nhất 2 đơn vị đối chứng (donors) để tổng hợp nhóm kiểm chứng. Hiện chỉ có {len(donors)} đơn vị."
        }

    # Order periods chronologically / logically
    # Try converting to numeric or sort as string
    distinct_periods_raw = sorted(list(set(d.get(period_col) for d in panel_data if d.get(period_col) is not None)))
    
    # Try sort numerically if possible
    try:
        sorted_periods = sorted(distinct_periods_raw, key=lambda x: float(x))
    except (ValueError, TypeError):
        sorted_periods = sorted(distinct_periods_raw, key=lambda x: str(x))

    treatment_period_idx = -1
    for idx, p in enumerate(sorted_periods):
        if str(p).strip() == str(treatment_period).strip():
            treatment_period_idx = idx
            break

    if treatment_period_idx == -1:
        return {
            "status": "TREATMENT_PERIOD_NOT_FOUND",
            "message": f"Không tìm thấy thời điểm can thiệp '{treatment_period}' trong danh sách chuỗi thời gian."
        }

    pre_periods = sorted_periods[:treatment_period_idx]
    post_periods = sorted_periods[treatment_period_idx:]

    if len(pre_periods) < 1:
        return {
            "status": "INSUFFICIENT_PRE_PERIODS",
            "message": "Cần ít nhất 1 kỳ khảo sát trước can thiệp (pre-intervention) để ước lượng trọng số."
        }
    if len(post_periods) < 1:
        return {
            "status": "INSUFFICIENT_POST_PERIODS",
            "message": "Cần ít nhất 1 kỳ khảo sát sau can thiệp (post-intervention) để đánh giá tác động."
        }

    # Construct Outcome Matrix Y: shape (num_units, num_periods)
    # unit 0 is treated_unit, unit 1..J are donors
    all_units = [treated_unit] + donors
    unit_map = {u: i for i, u in enumerate(all_units)}
    period_map = {p: t for t, p in enumerate(sorted_periods)}

    y_matrix = np.full((len(all_units), len(sorted_periods)), np.nan)
    counts = np.zeros((len(all_units), len(sorted_periods)))

    for d in panel_data:
        u_val = str(d.get(unit_col, "")).strip()
        p_val = d.get(period_col)
        out_val = d.get(outcome_col)
        if u_val in unit_map and p_val in period_map and out_val is not None:
            try:
                num_val = float(out_val)
                ui = unit_map[u_val]
                pi = period_map[p_val]
                if np.isnan(y_matrix[ui, pi]):
                    y_matrix[ui, pi] = num_val
                    counts[ui, pi] = 1
                else:
                    y_matrix[ui, pi] += num_val
                    counts[ui, pi] += 1
            except (ValueError, TypeError):
                continue

    # Average for multiple observations
    counts = np.where(counts == 0, 1, counts)
    y_matrix = y_matrix / counts

    # Check for missing values in treated unit or donors in pre_periods
    treated_pre_y = y_matrix[0, :treatment_period_idx]
    if np.any(np.isnan(treated_pre_y)):
        return {
            "status": "MISSING_TREATED_DATA",
            "message": "Đơn vị can thiệp bị thiếu dữ liệu kết quả ở một số kỳ trước can thiệp."
        }

    # Filter out donors with missing pre-treatment data
    valid_donor_indices = []
    valid_donors = []
    for j_idx, d_name in enumerate(donors, start=1):
        if not np.any(np.isnan(y_matrix[j_idx, :])):  # complete series preferred
            valid_donor_indices.append(j_idx)
            valid_donors.append(d_name)

    if len(valid_donors) < 2:
        return {
            "status": "INSUFFICIENT_VALID_DONORS",
            "message": "Không đủ đơn vị đối chứng có chuỗi dữ liệu đầy đủ liên tục (cần ít nhất 2)."
        }

    # Predictor matrix X:
    # Use pre-treatment outcomes as primary predictors
    x1 = y_matrix[0, :treatment_period_idx]  # shape (T0, )
    x0 = y_matrix[valid_donor_indices, :treatment_period_idx].T  # shape (T0, J_valid)

    # Solve SCM for treated unit
    w_opt, pre_loss = solve_synthetic_control_weights(x1, x0)

    # Compute Synthetic series for treated unit
    donor_y_all = y_matrix[valid_donor_indices, :]  # shape (J_valid, T)
    treated_y_all = y_matrix[0, :]                  # shape (T, )
    synth_y_all = w_opt @ donor_y_all              # shape (T, )
    gaps = treated_y_all - synth_y_all

    # Performance metrics
    pre_gaps = gaps[:treatment_period_idx]
    post_gaps = gaps[treatment_period_idx:]

    rmspe_pre = float(np.sqrt(np.mean(pre_gaps ** 2)))
    rmspe_post = float(np.sqrt(np.mean(post_gaps ** 2)))
    rmspe_ratio = float(rmspe_post / (rmspe_pre + 1e-8))
    att_effect = float(np.mean(post_gaps))

    # Pre-treatment balance comparison
    donor_mean_pre = np.mean(x0, axis=1)
    synth_pre = x0 @ w_opt
    balance_table = []
    for t_idx, p_name in enumerate(pre_periods):
        balance_table.append({
            "period": str(p_name),
            "treated_value": round(float(x1[t_idx]), 3),
            "synthetic_value": round(float(synth_pre[t_idx]), 3),
            "donor_mean_value": round(float(donor_mean_pre[t_idx]), 3),
            "difference": round(float(x1[t_idx] - synth_pre[t_idx]), 3)
        })

    # Donor weights table
    donor_weights_list = []
    for d_name, w_val in zip(valid_donors, w_opt):
        if w_val >= 0.001:  # keep non-negligible donors
            donor_weights_list.append({
                "donor_name": d_name,
                "weight": round(float(w_val), 4),
                "weight_percentage": round(float(w_val * 100), 2)
            })
    donor_weights_list = sorted(donor_weights_list, key=lambda x: x["weight"], reverse=True)

    # Trajectory series
    trajectory = []
    for t_idx, p_name in enumerate(sorted_periods):
        is_post = t_idx >= treatment_period_idx
        trajectory.append({
            "period": str(p_name),
            "actual_treated": round(float(treated_y_all[t_idx]), 3),
            "synthetic_control": round(float(synth_y_all[t_idx]), 3),
            "gap": round(float(gaps[t_idx]), 3),
            "is_post_treatment": bool(is_post)
        })

    # Placebo in-Space Permutation Test (Abadie et al. 2010)
    # Loop over each valid donor as treated unit
    placebo_ratios = []
    placebo_trajectories = {}  # donor -> list of gaps
    num_valid_donors = len(valid_donors)

    for p_i, p_donor_name in enumerate(valid_donors):
        p_x1 = donor_y_all[p_i, :treatment_period_idx]
        other_indices = [idx for idx in range(num_valid_donors) if idx != p_i]
        p_x0 = donor_y_all[other_indices, :treatment_period_idx].T

        p_w, _ = solve_synthetic_control_weights(p_x1, p_x0)
        p_synth_all = p_w @ donor_y_all[other_indices, :]
        p_gaps = donor_y_all[p_i, :] - p_synth_all

        p_rmspe_pre = float(np.sqrt(np.mean(p_gaps[:treatment_period_idx] ** 2)))
        p_rmspe_post = float(np.sqrt(np.mean(p_gaps[treatment_period_idx:] ** 2)))
        p_ratio = float(p_rmspe_post / (p_rmspe_pre + 1e-8))

        placebo_ratios.append(p_ratio)
        placebo_trajectories[p_donor_name] = [round(float(g), 3) for g in p_gaps]

    # Calculate empirical p-value: proportion of placebos with ratio >= treated ratio
    all_ratios = [rmspe_ratio] + placebo_ratios
    p_value = float(np.mean([1.0 if r >= rmspe_ratio - 1e-9 else 0.0 for r in all_ratios]))

    # Generate Dual-Panel SVG Chart
    svg_chart = generate_scm_svg(
        sorted_periods=[str(p) for p in sorted_periods],
        actual=treated_y_all,
        synthetic=synth_y_all,
        treated_gap=gaps,
        placebo_gaps=placebo_trajectories,
        treatment_idx=treatment_period_idx,
        treated_name=treated_unit
    )

    # APA 7th Edition Narrative
    apa_narrative = generate_scm_apa_narrative(
        treated_unit=treated_unit,
        treatment_period=str(treatment_period),
        att_effect=att_effect,
        rmspe_pre=rmspe_pre,
        rmspe_post=rmspe_post,
        rmspe_ratio=rmspe_ratio,
        p_value=p_value,
        donor_count=len(valid_donors),
        top_donors=donor_weights_list[:3]
    )

    return {
        "status": "SUCCESS",
        "treated_unit": treated_unit,
        "treatment_period": str(treatment_period),
        "treatment_period_index": int(treatment_period_idx),
        "donor_pool_count": len(valid_donors),
        "att_effect": round(att_effect, 4),
        "rmspe_pre": round(rmspe_pre, 4),
        "rmspe_post": round(rmspe_post, 4),
        "rmspe_ratio": round(rmspe_ratio, 4),
        "empirical_p_value": round(p_value, 4),
        "is_significant": bool(p_value < 0.05),
        "top_donor_weights": donor_weights_list,
        "balance_table": balance_table,
        "trajectory": trajectory,
        "svg_chart": svg_chart,
        "apa_narrative": apa_narrative
    }


def generate_scm_svg(
    sorted_periods: List[str],
    actual: np.ndarray,
    synthetic: np.ndarray,
    treated_gap: np.ndarray,
    placebo_gaps: Dict[str, List[float]],
    treatment_idx: int,
    treated_name: str
) -> str:
    """
    Generate dual-panel vector SVG:
    Top Panel: Trajectory (Actual vs Synthetic)
    Bottom Panel: Gap & Placebo In-Space Permutation Curves
    """
    width = 720
    height = 500
    margin_l = 65
    margin_r = 30
    margin_t = 35
    panel_gap = 45
    panel_h = (height - margin_t - margin_r - panel_gap) / 2  # ~195px each

    t_count = len(sorted_periods)
    if t_count < 2:
        return "<svg width='100%' height='200'><text x='20' y='50'>Không đủ chuỗi thời gian để vẽ biểu đồ.</text></svg>"

    # Panel 1 Bounds: Top Panel
    y_min_1 = min(float(np.nanmin(actual)), float(np.nanmin(synthetic)))
    y_max_1 = max(float(np.nanmax(actual)), float(np.nanmax(synthetic)))
    pad_1 = max(1e-4, (y_max_1 - y_min_1) * 0.12)
    y_min_1 -= pad_1
    y_max_1 += pad_1

    # Panel 2 Bounds: Bottom Panel
    all_gaps = [g for glist in placebo_gaps.values() for g in glist] + list(treated_gap)
    y_min_2 = min(float(min(all_gaps)), -0.1)
    y_max_2 = max(float(max(all_gaps)), 0.1)
    pad_2 = max(1e-4, (y_max_2 - y_min_2) * 0.15)
    y_min_2 -= pad_2
    y_max_2 += pad_2

    plot_w = width - margin_l - margin_r

    def x_scale(idx: int) -> float:
        return margin_l + (idx / (t_count - 1)) * plot_w

    def y_scale_1(val: float) -> float:
        norm = (val - y_min_1) / (y_max_1 - y_min_1 + 1e-9)
        return margin_t + panel_h - norm * panel_h

    def y_scale_2(val: float) -> float:
        norm = (val - y_min_2) / (y_max_2 - y_min_2 + 1e-9)
        return margin_t + panel_h + panel_gap + panel_h - norm * panel_h

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="background:#0f172a; border-radius:8px; font-family:system-ui,-apple-system,sans-serif;">')

    # Gridlines for Panel 1
    for step in np.linspace(y_min_1, y_max_1, 5):
        y_pos = y_scale_1(step)
        lines.append(f'<line x1="{margin_l}" y1="{y_pos:.1f}" x2="{width - margin_r}" y2="{y_pos:.1f}" stroke="#334155" stroke-dasharray="2,3" stroke-width="1"/>')
        lines.append(f'<text x="{margin_l - 8}" y="{y_pos + 4:.1f}" fill="#94a3b8" font-size="10" text-anchor="end">{step:.1f}</text>')

    # Gridlines for Panel 2
    for step in np.linspace(y_min_2, y_max_2, 5):
        y_pos = y_scale_2(step)
        lines.append(f'<line x1="{margin_l}" y1="{y_pos:.1f}" x2="{width - margin_r}" y2="{y_pos:.1f}" stroke="#334155" stroke-dasharray="2,3" stroke-width="1"/>')
        lines.append(f'<text x="{margin_l - 8}" y="{y_pos + 4:.1f}" fill="#94a3b8" font-size="10" text-anchor="end">{step:.1f}</text>')

    # Zero baseline for Panel 2
    zero_y = y_scale_2(0.0)
    lines.append(f'<line x1="{margin_l}" y1="{zero_y:.1f}" x2="{width - margin_r}" y2="{zero_y:.1f}" stroke="#64748b" stroke-width="1.2"/>')

    # Treatment Cutoff line across both panels
    tx_pos = x_scale(treatment_idx)
    lines.append(f'<line x1="{tx_pos:.1f}" y1="{margin_t}" x2="{tx_pos:.1f}" y2="{margin_t + panel_h * 2 + panel_gap}" stroke="#f59e0b" stroke-dasharray="4,4" stroke-width="1.8"/>')
    lines.append(f'<text x="{tx_pos + 5:.1f}" y="{margin_t + 12}" fill="#fbbf24" font-size="10" font-weight="600">Can thiệp: {sorted_periods[treatment_idx]}</text>')

    # Panel 1: Synthetic Curve (Dashed Cyan)
    synth_pts = " ".join([f"{x_scale(i):.1f},{y_scale_1(synthetic[i]):.1f}" for i in range(t_count)])
    lines.append(f'<polyline points="{synth_pts}" fill="none" stroke="#38bdf8" stroke-width="2.2" stroke-dasharray="4,4"/>')

    # Panel 1: Actual Treated Curve (Solid White)
    actual_pts = " ".join([f"{x_scale(i):.1f},{y_scale_1(actual[i]):.1f}" for i in range(t_count)])
    lines.append(f'<polyline points="{actual_pts}" fill="none" stroke="#ffffff" stroke-width="2.8"/>')

    # Points for Actual Treated
    for i in range(t_count):
        lines.append(f'<circle cx="{x_scale(i):.1f}" cy="{y_scale_1(actual[i]):.1f}" r="3.5" fill="#3b82f6" stroke="#ffffff" stroke-width="1.5"/>')

    # Panel 2: Placebo Permutation Curves (Faint grey)
    for d_name, p_list in placebo_gaps.items():
        if len(p_list) == t_count:
            p_pts = " ".join([f"{x_scale(i):.1f},{y_scale_2(p_list[i]):.1f}" for i in range(t_count)])
            lines.append(f'<polyline points="{p_pts}" fill="none" stroke="#475569" stroke-width="1.2" opacity="0.65"/>')

    # Panel 2: Treated Gap Curve (Bold Indigo/Rose)
    gap_pts = " ".join([f"{x_scale(i):.1f},{y_scale_2(treated_gap[i]):.1f}" for i in range(t_count)])
    lines.append(f'<polyline points="{gap_pts}" fill="none" stroke="#f43f5e" stroke-width="2.8"/>')
    for i in range(t_count):
        lines.append(f'<circle cx="{x_scale(i):.1f}" cy="{y_scale_2(treated_gap[i]):.1f}" r="3" fill="#f43f5e"/>')

    # X-Axis Labels at Bottom
    for i, p_str in enumerate(sorted_periods):
        xp = x_scale(i)
        yp = margin_t + panel_h * 2 + panel_gap + 15
        lines.append(f'<text x="{xp:.1f}" y="{yp:.1f}" fill="#cbd5e1" font-size="10" text-anchor="middle">{p_str}</text>')

    # Panel Titles & Legend
    lines.append(f'<text x="{margin_l}" y="{margin_t - 10}" fill="#e2e8f0" font-size="12" font-weight="bold">1. Diễn tiến Giá trị Thực tế vs Đối chứng Tổng hợp</text>')
    lines.append(f'<text x="{margin_l}" y="{margin_t + panel_h + panel_gap - 10}" fill="#e2e8f0" font-size="12" font-weight="bold">2. Khoảng cách Tác động (Gap) & Kiểm định Hoán vị Placebo</text>')

    # Legend at Top Right
    lines.append(f'<line x1="{width - 230}" y1="{margin_t - 12}" x2="{width - 205}" y2="{margin_t - 12}" stroke="#ffffff" stroke-width="2.5"/>')
    lines.append(f'<text x="{width - 200}" y="{margin_t - 9}" fill="#ffffff" font-size="10">Thực tế ({treated_name})</text>')
    lines.append(f'<line x1="{width - 120}" y1="{margin_t - 12}" x2="{width - 95}" y2="{margin_t - 12}" stroke="#38bdf8" stroke-dasharray="3,3" stroke-width="2"/>')
    lines.append(f'<text x="{width - 90}" y="{margin_t - 9}" fill="#38bdf8" font-size="10">Synthetic</text>')

    lines.append('</svg>')
    return "".join(lines)


class SyntheticControlEngine:
    @staticmethod
    def fit_synthetic_control(
        panel_data: List[Dict[str, Any]],
        unit_col: str,
        period_col: str,
        outcome_col: str,
        treated_unit: str,
        treatment_period: Any,
        covariate_cols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        return calculate_synthetic_control(
            panel_data=panel_data,
            unit_col=unit_col,
            period_col=period_col,
            outcome_col=outcome_col,
            treated_unit=treated_unit,
            treatment_period=treatment_period,
            covariate_cols=covariate_cols
        )



def generate_scm_apa_narrative(
    treated_unit: str,
    treatment_period: str,
    att_effect: float,
    rmspe_pre: float,
    rmspe_post: float,
    rmspe_ratio: float,
    p_value: float,
    donor_count: int,
    top_donors: List[Dict[str, Any]]
) -> str:
    """
    Generate APA 7th Edition narrative for Synthetic Control Method.
    """
    donor_str = ", ".join([f"{d['donor_name']} ({d['weight_percentage']}%)" for d in top_donors])
    sig_str = "có ý nghĩa thống kê (p < .05)" if p_value < 0.05 else "chưa đủ bằng chứng thống kê để bác bỏ giả thuyết vô hiệu (p >= .05)"
    
    return (
        f"Phương pháp Kiểm chứng Tổng hợp (Synthetic Control Method - SCM; Abadie et al., 2010; Abadie, 2021) "
        f"được ứng dụng để đánh giá tác động nhân quả của can thiệp chính sách tại đơn vị '{treated_unit}' "
        f"bắt đầu từ kỳ '{treatment_period}'. Nhóm kiểm chứng tổng hợp được tối ưu hóa từ pool gồm {donor_count} "
        f"đơn vị đối chứng thông qua quy hoạch lồi phi tuyến có ràng buộc trọng số (W >= 0, sum(W) = 1). "
        f"Các đơn vị đóng góp trọng số lớn nhất bao gồm: {donor_str}. "
        f"Trong giai đoạn trước can thiệp (pre-intervention), đối chứng tổng hợp đạt độ khớp cao với sai số dự báo "
        f"RMSPE_pre = {rmspe_pre:.3f}. Sau khi can thiệp có hiệu lực, tác động trung bình lên đơn vị can thiệp (ATT) "
        f"đạt {att_effect:+.3f} điểm (RMSPE_post = {rmspe_post:.3f}, tỷ số RMSPE ratio = {rmspe_ratio:.2f}). "
        f"Kiểm định hoán vị không gian (In-Space Placebo Permutation Test) trên toàn bộ các đơn vị đối chứng ghi nhận "
        f"giá trị p thực nghiệm p = {p_value:.3f}, cho thấy tác động này {sig_str}."
    )
