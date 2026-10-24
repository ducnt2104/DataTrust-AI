"""
Manski Non-Parametric Partial Identification & Worst-Case Bounds Engine
Author: DataTrust Platform Architecture
Reference:
- Manski, C. F. (1990). Nonparametric bounds on treatment effects. The American Economic Review, 80(2), 319-323.
- Manski, C. F. (1995). Identification Problems in the Social Sciences. Harvard University Press.
- Manski, C. F., & Pepper, J. V. (2000). Monotone instrumental variables: With an application to the returns to schooling. Econometrica, 68(5), 997-1010.
- Manski, C. F. (2003). Partial Identification of Probability Distributions. Springer New York.
- Horowitz, J. L., & Manski, C. F. (2000). Nonparametric analysis of randomized experiments with missing covariate and outcome data. Journal of the American Statistical Association, 95(449), 77-84.
- Imbens, G. W., & Manski, C. F. (2004). Confidence intervals for partially identified parameters. Econometrica, 72(6), 1845-1857.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats


def _compute_imbens_manski_critical_value(
    theta_l: float,
    theta_u: float,
    se_l: float,
    se_u: float,
    n: int,
    alpha: float = 0.05
) -> float:
    """
    Computes Imbens & Manski (2004) critical value c_alpha solving:
    Phi(c_alpha + sqrt(N) * (theta_u - theta_l) / max(se_l, se_u)) - Phi(-c_alpha) = 1 - alpha.
    """
    delta = (theta_u - theta_l) * np.sqrt(n) / max(se_l, se_u, 1e-6)
    target = 1.0 - alpha
    
    # If width is large relative to standard error, c_alpha approaches normal quantile z_{1-alpha} (e.g. 1.645)
    # If width is zero (point identification), c_alpha approaches two-sided normal quantile z_{1-alpha/2} (e.g. 1.96)
    if delta > 20.0:
        return float(stats.norm.ppf(target))
    
    # Bisection search for c_alpha in [1.0, 3.5]
    low, high = 0.5, 3.5
    for _ in range(35):
        mid = 0.5 * (low + high)
        val = stats.norm.cdf(mid + delta) - stats.norm.cdf(-mid)
        if val < target:
            low = mid
        else:
            high = mid
            
    return float(0.5 * (low + high))


def generate_manski_bounds_svg(
    worst_lb: float,
    worst_ub: float,
    mts_lb: float,
    mts_ub: float,
    mtr_lb: float,
    mtr_ub: float,
    joint_lb: float,
    joint_ub: float,
    ci_joint_lower: float,
    ci_joint_upper: float,
    naive_ate: float,
    missing_rates: List[float],
    lb_trajectory: List[float],
    ub_trajectory: List[float],
    outcome_label: str,
    treatment_label: str
) -> str:
    """
    Generates dual-panel scientific SVG:
    Panel A: Manski Partial Identification Hierarchy (Worst-Case -> MTS -> MTR -> MTS+MTR + CI)
    Panel B: Attrition Sensitivity Curve & Sign Breakdown Point
    """
    w, h = 960, 420
    
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%" '
        f'style="background: #0f172a; border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;">',
        '<defs>',
        '  <linearGradient id="jointGrad" x1="0" y1="0" x2="1" y2="0">',
        '    <stop offset="0%" stop-color="#10b981" stop-opacity="0.8"/>',
        '    <stop offset="100%" stop-color="#059669" stop-opacity="0.95"/>',
        '  </linearGradient>',
        '  <linearGradient id="sensGrad" x1="0" y1="0" x2="0" y2="1">',
        '    <stop offset="0%" stop-color="#6366f1" stop-opacity="0.30"/>',
        '    <stop offset="100%" stop-color="#a855f7" stop-opacity="0.05"/>',
        '  </linearGradient>',
        '  <filter id="glowGreen" x="-20%" y="-20%" width="140%" height="140%">',
        '    <feGaussianBlur stdDeviation="3" result="blur"/>',
        '    <feComposite in="SourceGraphic" in2="blur" operator="over"/>',
        '  </filter>',
        '</defs>'
    ]
    
    # Header Title
    svg.append(
        f'<text x="24" y="30" fill="#f8fafc" font-size="14" font-weight="700">'
        f'Manski Non-Parametric Partial Identification Bounds &bull; Manski &amp; Pepper (2000)</text>'
    )
    svg.append(
        f'<text x="24" y="48" fill="#94a3b8" font-size="11">'
        f'Khoảng xác định ATE dưới rủi ro dữ liệu khuyết NMAR &bull; Outcome: {outcome_label} &bull; Treatment: {treatment_label}</text>'
    )
    
    # -------------------------------------------------------------
    # PANEL A: Bounds Spectrum (Left: x in [60, 470], y in [80, 360])
    # -------------------------------------------------------------
    p1_x, p1_y, p1_w, p1_h = 60, 80, 410, 270
    
    all_vals = [
        worst_lb, worst_ub, mts_lb, mts_ub, mtr_lb, mtr_ub,
        joint_lb, joint_ub, ci_joint_lower, ci_joint_upper, naive_ate, 0.0
    ]
    val_min = min(all_vals)
    val_max = max(all_vals)
    span = max(val_max - val_min, 0.2)
    axis_min = val_min - 0.12 * span
    axis_max = val_max + 0.12 * span
    
    def map_x_p1(val: float) -> float:
        return p1_x + (val - axis_min) / (axis_max - axis_min) * p1_w

    # Card background
    svg.append(f'<rect x="{p1_x-15}" y="{p1_y-15}" width="{p1_w+30}" height="{p1_h+55}" rx="8" fill="#1e293b" fill-opacity="0.5" stroke="#334155" stroke-width="1"/>')
    svg.append(f'<text x="{p1_x}" y="{p1_y - 22}" fill="#38bdf8" font-size="12" font-weight="600">Panel A: Phổ Khoảng Xác định ATE qua các Giả định Tiên đề</text>')
    
    # Zero line
    x_zero = map_x_p1(0.0)
    svg.append(f'<line x1="{x_zero}" y1="{p1_y}" x2="{x_zero}" y2="{p1_y+p1_h}" stroke="#64748b" stroke-width="1.5" stroke-dasharray="3 3"/>')
    svg.append(f'<text x="{x_zero}" y="{p1_y + p1_h + 16}" fill="#64748b" font-size="9" text-anchor="middle">0.0</text>')
    
    # Naive ATE vertical marker
    x_naive = map_x_p1(naive_ate)
    svg.append(f'<line x1="{x_naive}" y1="{p1_y}" x2="{x_naive}" y2="{p1_y+p1_h}" stroke="#f43f5e" stroke-width="1.5" stroke-dasharray="2 2"/>')
    svg.append(f'<text x="{x_naive}" y="{p1_y - 6}" fill="#f43f5e" font-size="9" text-anchor="middle">Naive ATE={naive_ate:+.2f}</text>')

    # 4 Tiers of Bounds
    bounds_tiers = [
        ("1. Worst-Case (Không giả định)", worst_lb, worst_ub, "#475569", 20),
        ("2. MTR (Can thiệp không gây hại)", mtr_lb, mtr_ub, "#3b82f6", 70),
        ("3. MTS (Tự lựa chọn tích cực)", mts_lb, mts_ub, "#8b5cf6", 120),
        ("4. MTS + MTR (Hợp nhất Tiên đề)", joint_lb, joint_ub, "#10b981", 170)
    ]
    
    for label, lb, ub, color, y_offset in bounds_tiers:
        y_bar = p1_y + y_offset
        x1 = map_x_p1(lb)
        x2 = map_x_p1(ub)
        bar_w = max(x2 - x1, 4)
        
        svg.append(f'<text x="{p1_x}" y="{y_bar - 4}" fill="#cbd5e1" font-size="10" font-weight="500">{label}</text>')
        # Bar rect
        is_joint = (label.startswith("4."))
        fill_attr = 'fill="url(#jointGrad)" filter="url(#glowGreen)"' if is_joint else f'fill="{color}" fill-opacity="0.75"'
        svg.append(f'<rect x="{x1}" y="{y_bar}" width="{bar_w}" height="14" rx="4" {fill_attr}/>')
        # Labels on ends
        svg.append(f'<text x="{x1 - 4}" y="{y_bar + 11}" fill="#94a3b8" font-size="9" text-anchor="end">{lb:+.2f}</text>')
        svg.append(f'<text x="{x2 + 4}" y="{y_bar + 11}" fill="#94a3b8" font-size="9" text-anchor="start">{ub:+.2f}</text>')

    # Imbens & Manski 95% Confidence Interval for Joint Bounds
    y_ci = p1_y + 220
    x_ci1 = map_x_p1(ci_joint_lower)
    x_ci2 = map_x_p1(ci_joint_upper)
    svg.append(f'<text x="{p1_x}" y="{y_ci - 4}" fill="#38bdf8" font-size="10" font-weight="600">Khoảng Tin cậy 95% Imbens-Manski (MTS+MTR)</text>')
    svg.append(f'<line x1="{x_ci1}" y1="{y_ci + 6}" x2="{x_ci2}" y2="{y_ci + 6}" stroke="#38bdf8" stroke-width="3"/>')
    svg.append(f'<line x1="{x_ci1}" y1="{y_ci}" x2="{x_ci1}" y2="{y_ci + 12}" stroke="#38bdf8" stroke-width="2"/>')
    svg.append(f'<line x1="{x_ci2}" y1="{y_ci}" x2="{x_ci2}" y2="{y_ci + 12}" stroke="#38bdf8" stroke-width="2"/>')
    svg.append(f'<text x="{x_ci1 - 4}" y="{y_ci + 9}" fill="#38bdf8" font-size="9" text-anchor="end">{ci_joint_lower:+.2f}</text>')
    svg.append(f'<text x="{x_ci2 + 4}" y="{y_ci + 9}" fill="#38bdf8" font-size="9" text-anchor="start">{ci_joint_upper:+.2f}</text>')
    
    svg.append(f'<text x="{p1_x + p1_w/2}" y="{p1_y + p1_h + 34}" fill="#cbd5e1" font-size="11" font-weight="600" text-anchor="middle">Hiệu ứng Can thiệp ATE</text>')
    
    # -------------------------------------------------------------
    # PANEL B: Sensitivity over Attrition Rate (Right: x in [540, 920])
    # -------------------------------------------------------------
    p2_x, p2_y, p2_w, p2_h = 540, 80, 380, 270
    
    m_min, m_max = float(missing_rates[0]), float(missing_rates[-1])
    m_span = max(m_max - m_min, 1e-4)
    
    all_traj = lb_trajectory + ub_trajectory + [0.0]
    t_min, t_max = min(all_traj), max(all_traj)
    t_span = max(t_max - t_min, 0.2)
    y_traj_min = t_min - 0.1 * t_span
    y_traj_max = t_max + 0.1 * t_span
    
    def map_x_p2(m_val: float) -> float:
        return p2_x + (m_val - m_min) / m_span * p2_w
        
    def map_y_p2(val: float) -> float:
        return p2_y + p2_h - (val - y_traj_min) / (y_traj_max - y_traj_min) * p2_h

    # Card background
    svg.append(f'<rect x="{p2_x-15}" y="{p2_y-15}" width="{p2_w+30}" height="{p2_h+55}" rx="8" fill="#1e293b" fill-opacity="0.5" stroke="#334155" stroke-width="1"/>')
    svg.append(f'<text x="{p2_x}" y="{p2_y - 22}" fill="#38bdf8" font-size="12" font-weight="600">Panel B: Phân tích Độ nhạy theo Tỷ lệ Mất mẫu (Breakdown Point)</text>')
    
    # Zero line
    y_zero_p2 = map_y_p2(0.0)
    svg.append(f'<line x1="{p2_x}" y1="{y_zero_p2}" x2="{p2_x+p2_w}" y2="{y_zero_p2}" stroke="#64748b" stroke-width="1.5" stroke-dasharray="3 3"/>')
    svg.append(f'<text x="{p2_x + p2_w + 4}" y="{y_zero_p2 + 3}" fill="#64748b" font-size="9">0.0</text>')
    
    # Polygon of identification envelope as missingness grows
    poly_pts = []
    # Upper curve left to right
    for m_val, ub in zip(missing_rates, ub_trajectory):
        poly_pts.append(f"{map_x_p2(m_val):.1f},{map_y_p2(ub):.1f}")
    # Lower curve right to left
    for m_val, lb in zip(reversed(missing_rates), reversed(lb_trajectory)):
        poly_pts.append(f"{map_x_p2(m_val):.1f},{map_y_p2(lb):.1f}")
    svg.append(f'<polygon points="{" ".join(poly_pts)}" fill="url(#sensGrad)"/>')
    
    # Lines
    pts_ub = " ".join([f"{map_x_p2(m_val):.1f},{map_y_p2(ub):.1f}" for m_val, ub in zip(missing_rates, ub_trajectory)])
    pts_lb = " ".join([f"{map_x_p2(m_val):.1f},{map_y_p2(lb):.1f}" for m_val, lb in zip(missing_rates, lb_trajectory)])
    svg.append(f'<polyline points="{pts_ub}" fill="none" stroke="#818cf8" stroke-width="2"/>')
    svg.append(f'<polyline points="{pts_lb}" fill="none" stroke="#6366f1" stroke-width="2"/>')
    
    # Find Breakdown point where lb_trajectory crosses zero
    breakdown_m = None
    for m_val, lb in zip(missing_rates, lb_trajectory):
        if lb <= 0.0:
            breakdown_m = m_val
            break
            
    if breakdown_m is not None:
        bx = map_x_p2(breakdown_m)
        by = map_y_p2(0.0)
        svg.append(f'<circle cx="{bx}" cy="{by}" r="5" fill="#f59e0b" stroke="#ffffff" stroke-width="1.5"/>')
        svg.append(f'<text x="{bx}" y="{by - 12}" fill="#f59e0b" font-size="9" text-anchor="middle" font-weight="bold">Điểm gãy dấu: {breakdown_m*100:.1f}%</text>')

    # Legend for Panel B
    svg.append(f'<text x="{p2_x + 12}" y="{p2_y + 18}" fill="#818cf8" font-size="9">Cận trên UB(p)</text>')
    svg.append(f'<text x="{p2_x + 12}" y="{p2_y + 32}" fill="#6366f1" font-size="9">Cận dưới LB(p)</text>')
    
    # X-axis ticks
    for m_tick in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
        if m_tick <= m_max:
            xt = map_x_p2(m_tick)
            svg.append(f'<line x1="{xt}" y1="{p2_y+p2_h}" x2="{xt}" y2="{p2_y+p2_h+4}" stroke="#64748b"/>')
            svg.append(f'<text x="{xt}" y="{p2_y+p2_h+16}" fill="#94a3b8" font-size="9" text-anchor="middle">{int(m_tick*100)}%</text>')

    svg.append(f'<text x="{p2_x + p2_w/2}" y="{p2_y + p2_h + 34}" fill="#cbd5e1" font-size="11" font-weight="600" text-anchor="middle">Tỷ lệ Mất mẫu / Khuyết dữ liệu (Missingness Rate p)</text>')
    
    # Footer notice
    svg.append(
        f'<text x="24" y="{h - 12}" fill="#64748b" font-size="10">'
        f'Định lý Manski (1990) &amp; Manski &amp; Pepper (2000): Khoảng xác định không phụ thuộc giả định phân phối MAR. '
        f'Cung cấp biên độ khoa học trung thực ngay cả khi dữ liệu khuyết NMAR.'
        f'</text>'
    )
    
    svg.append('</svg>')
    return '\n'.join(svg)


class ManskiBoundsEngine:
    """
    Engine executing Manski Non-Parametric Partial Identification,
    Worst-Case Bounds, Monotone Treatment Selection (MTS), Monotone Treatment Response (MTR),
    and Imbens-Manski (2004) confidence intervals.
    """

    @staticmethod
    def evaluate_bounds(
        y_observed: np.ndarray,
        d_treatment: np.ndarray,
        r_response: np.ndarray,
        support_min: Optional[float] = None,
        support_max: Optional[float] = None,
        confidence_level: float = 0.95,
        outcome_label: str = "Outcome",
        treatment_label: str = "Treatment"
    ) -> Dict[str, Any]:
        """
        Executes non-parametric partial identification bounds under missing/attrited survey data.
        """
        y = np.asarray(y_observed, dtype=float)
        d = np.asarray(d_treatment, dtype=int)
        r = np.asarray(r_response, dtype=int)
        
        n_total = len(d)
        if n_total < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Kích thước mẫu không đủ để ước lượng biên Manski (N={n_total}). Cần tối thiểu 20 mẫu."
            }
            
        n_treated = int(np.sum(d == 1))
        n_control = int(np.sum(d == 0))
        if n_treated < 8 or n_control < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Không đủ số quan sát ở từng nhánh can thiệp (Treated={n_treated}, Control={n_control}). Cần tối thiểu 8 quan sát mỗi nhóm."
            }

        # Observed subset
        obs_idx = (r == 1) & ~np.isnan(y)
        if np.sum(obs_idx) < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Số lượng phản hồi quan sát được (non-missing) quá ít (< 10)."
            }
            
        y_obs = y[obs_idx]
        y_min = float(support_min if support_min is not None else np.min(y_obs))
        y_max = float(support_max if support_max is not None else np.max(y_obs))
        
        if y_max <= y_min:
            y_max = y_min + 1.0

        # Conditional probabilities of response
        d1_idx = (d == 1)
        d0_idx = (d == 0)
        
        n1 = int(np.sum(d1_idx))
        n0 = int(np.sum(d0_idx))
        
        n1_obs = int(np.sum(d1_idx & obs_idx))
        n0_obs = int(np.sum(d0_idx & obs_idx))
        
        p_r_given_d1 = n1_obs / max(n1, 1)
        p_r_given_d0 = n0_obs / max(n0, 1)
        
        overall_missing_rate = float(1.0 - (n1_obs + n0_obs) / n_total)
        
        y1_obs = y[d1_idx & obs_idx]
        y0_obs = y[d0_idx & obs_idx]
        
        mean_y1_obs = float(np.mean(y1_obs)) if len(y1_obs) > 0 else 0.5 * (y_min + y_max)
        mean_y0_obs = float(np.mean(y0_obs)) if len(y0_obs) > 0 else 0.5 * (y_min + y_max)
        naive_ate = float(mean_y1_obs - mean_y0_obs)
        
        # 1. Worst-Case Bounds on E[Y(1)] and E[Y(0)] (Manski 1990)
        # E[Y(1)] = P(R=1|D=1)*E[Y|D=1,R=1] + P(R=0|D=1)*E[Y(1)|D=1,R=0]
        ey1_lb = float(p_r_given_d1 * mean_y1_obs + (1.0 - p_r_given_d1) * y_min)
        ey1_ub = float(p_r_given_d1 * mean_y1_obs + (1.0 - p_r_given_d1) * y_max)
        
        ey0_lb = float(p_r_given_d0 * mean_y0_obs + (1.0 - p_r_given_d0) * y_min)
        ey0_ub = float(p_r_given_d0 * mean_y0_obs + (1.0 - p_r_given_d0) * y_max)
        
        worst_lb = float(ey1_lb - ey0_ub)
        worst_ub = float(ey1_ub - ey0_lb)
        worst_width = float(worst_ub - worst_lb)
        
        # 2. Monotone Treatment Selection (MTS; Manski & Pepper 2000)
        # Assumption: E[Y(d)|D=1] >= E[Y(d)|D=0]
        # Under MTS: ATE <= E[Y|D=1] - E[Y|D=0]
        mts_lb = worst_lb
        mts_ub = float(mean_y1_obs - mean_y0_obs)
        if mts_ub < mts_lb:
            # Empirical contradiction of MTS or sample noise
            mts_ub = max(mts_lb, mts_ub)
        mts_width = float(mts_ub - mts_lb)
        
        # 3. Monotone Treatment Response (MTR; Manski 1997)
        # Assumption: Y_i(1) >= Y_i(0) => ATE >= 0
        mtr_lb = max(0.0, worst_lb)
        mtr_ub = worst_ub
        mtr_width = float(mtr_ub - mtr_lb)
        
        # 4. Joint MTS + MTR Bounds (Manski & Pepper 2000)
        joint_lb = max(0.0, worst_lb)
        joint_ub = max(joint_lb, min(worst_ub, float(mean_y1_obs - mean_y0_obs)))
        joint_width = float(joint_ub - joint_lb)
        
        # 5. Imbens & Manski (2004) Confidence Intervals for Joint Bounds
        # Asymptotic variance via delta method
        var_y1 = float(np.var(y1_obs, ddof=1)) if len(y1_obs) > 1 else 1.0
        var_y0 = float(np.var(y0_obs, ddof=1)) if len(y0_obs) > 1 else 1.0
        se_lb = float(np.sqrt(var_y1 / max(n1_obs, 1) + var_y0 / max(n0_obs, 1)))
        se_ub = se_lb
        
        alpha = 1.0 - confidence_level
        c_alpha = _compute_imbens_manski_critical_value(joint_lb, joint_ub, se_lb, se_ub, n_total, alpha=alpha)
        
        ci_joint_lower = float(joint_lb - c_alpha * se_lb / np.sqrt(n_total))
        ci_joint_upper = float(joint_ub + c_alpha * se_ub / np.sqrt(n_total))
        
        # 6. Sensitivity Analysis over Attrition Rates (0% to 50%)
        grid_missing = np.linspace(0.0, 0.50, 15)
        lb_traj = []
        ub_traj = []
        
        for m_p in grid_missing:
            # Simulated bounds if missingness were m_p
            sim_ey1_lb = (1.0 - m_p) * mean_y1_obs + m_p * y_min
            sim_ey0_ub = (1.0 - m_p) * mean_y0_obs + m_p * y_max
            sim_ey1_ub = (1.0 - m_p) * mean_y1_obs + m_p * y_max
            sim_ey0_lb = (1.0 - m_p) * mean_y0_obs + m_p * y_min
            
            sim_worst_lb = sim_ey1_lb - sim_ey0_ub
            sim_worst_ub = sim_ey1_ub - sim_ey0_lb
            lb_traj.append(float(sim_worst_lb))
            ub_traj.append(float(sim_worst_ub))
            
        # Sign Breakdown Point
        breakdown_rate = None
        for m_p, lb_val in zip(grid_missing, lb_traj):
            if lb_val <= 0.0:
                breakdown_rate = float(m_p)
                break

        # Generate SVG visualization
        svg_chart = generate_manski_bounds_svg(
            worst_lb=worst_lb,
            worst_ub=worst_ub,
            mts_lb=mts_lb,
            mts_ub=mts_ub,
            mtr_lb=mtr_lb,
            mtr_ub=mtr_ub,
            joint_lb=joint_lb,
            joint_ub=joint_ub,
            ci_joint_lower=ci_joint_lower,
            ci_joint_upper=ci_joint_upper,
            naive_ate=naive_ate,
            missing_rates=list(grid_missing),
            lb_trajectory=lb_traj,
            ub_trajectory=ub_traj,
            outcome_label=outcome_label,
            treatment_label=treatment_label
        )

        # APA 7th Narrative
        bd_phrase = (
            f"Điểm gãy dấu (Sign Breakdown Point) xuất hiện tại tỷ lệ khuyết dữ liệu p = {breakdown_rate*100:.1f}%, "
            f"tại đó biên dưới của hiệu ứng chuyển sang giá trị âm."
            if breakdown_rate is not None else
            "Biên dưới duy trì giá trị dương trên toàn bộ phổ tỷ lệ mất mẫu kiểm tra (0% - 50%)."
        )
        
        sign_robust = (joint_lb > 0)
        conclusion_phrase = (
            f"Ngay cả dưới kịch bản bất lợi nhất của dữ liệu khuyết NMAR, hiệu ứng can thiệp vẫn được định dạng dương chắc chắn "
            f"(Biên hợp nhất MTS+MTR [{joint_lb:+.3f}, {joint_ub:+.3f}] hoàn toàn nằm phía trên 0)."
            if sign_robust else
            f"Khoảng xác định bao hàm giá trị 0 ([{joint_lb:+.3f}, {joint_ub:+.3f}]), "
            f"cho thấy cần thận trọng khi đưa ra kết luận khẳng định nếu không có thêm thông tin công cụ (MIV)."
        )

        apa = (
            f"Phân tích Xác định Bán phần Không tham số Manski (Non-parametric Partial Identification Bounds; "
            f"Manski, 1990; Manski & Pepper, 2000; Imbens & Manski, 2004) được thực hiện trên mẫu dữ liệu gồm N = {n_total} "
            f"quan sát với tỷ lệ khuyết dữ liệu chung {overall_missing_rate*100:.1f}% "
            f"(Nhánh can thiệp N1 = {n1}, tỷ lệ quan sát {p_r_given_d1*100:.1f}%; Nhánh đối chứng N0 = {n0}, tỷ lệ quan sát {p_r_given_d0*100:.1f}%). "
            f"Ước lượng điểm trung bình ngây thơ đạt Naive ATE = {naive_ate:+.3f}. "
            f"Dưới mô hình Không Giả định Tồi tệ nhất (Worst-Case Bounds), khoảng xác định của ATE là [{worst_lb:+.3f}, {worst_ub:+.3f}] "
            f"(độ rộng biên w = {worst_width:.3f}). "
            f"Khi áp dụng Tiên đề Lựa chọn Điều trị Đơn điệu (MTS), khoảng xác định thu hẹp thành [{mts_lb:+.3f}, {mts_ub:+.3f}]. "
            f"Khi áp dụng đồng thời Tiên đề MTS và Đáp ứng Đơn điệu (MTR), khoảng xác định đạt độ hội tụ chặt chẽ nhất là "
            f"[{joint_lb:+.3f}, {joint_ub:+.3f}] (Khoảng tin cậy 95% Imbens-Manski [{ci_joint_lower:+.3f}, {ci_joint_upper:+.3f}]). "
            f"{conclusion_phrase} {bd_phrase}"
        )

        return {
            "status": "SUCCESS",
            "model_type": "MANSKI_PARTIAL_IDENTIFICATION_BOUNDS_2000",
            "diagnostics": {
                "sample_size_total": n_total,
                "n_treated": n1,
                "n_control": n0,
                "observed_count": int(np.sum(obs_idx)),
                "missing_rate": round(overall_missing_rate, 4),
                "support_min": y_min,
                "support_max": y_max,
                "naive_ate": round(naive_ate, 4),
                "worst_case_lower": round(worst_lb, 4),
                "worst_case_upper": round(worst_ub, 4),
                "worst_case_width": round(worst_width, 4),
                "mts_lower": round(mts_lb, 4),
                "mts_upper": round(mts_ub, 4),
                "mtr_lower": round(mtr_lb, 4),
                "mtr_upper": round(mtr_ub, 4),
                "joint_mts_mtr_lower": round(joint_lb, 4),
                "joint_mts_mtr_upper": round(joint_ub, 4),
                "ci_joint_lower_95": round(ci_joint_lower, 4),
                "ci_joint_upper_95": round(ci_joint_upper, 4),
                "breakdown_rate": round(breakdown_rate, 4) if breakdown_rate is not None else None,
                "is_sign_identified": sign_robust
            },
            "tiers": [
                {"tier": "Worst-Case (No Assumptions)", "lower": round(worst_lb, 4), "upper": round(worst_ub, 4), "width": round(worst_width, 4)},
                {"tier": "Monotone Treatment Selection (MTS)", "lower": round(mts_lb, 4), "upper": round(mts_ub, 4), "width": round(mts_width, 4)},
                {"tier": "Monotone Treatment Response (MTR)", "lower": round(mtr_lb, 4), "upper": round(mtr_ub, 4), "width": round(mtr_width, 4)},
                {"tier": "Joint MTS + MTR Bounds", "lower": round(joint_lb, 4), "upper": round(joint_ub, 4), "width": round(joint_width, 4)}
            ],
            "sensitivity_grid": [
                {"missing_rate": round(float(m), 3), "lower_bound": round(float(lb), 4), "upper_bound": round(float(ub), 4)}
                for m, lb, ub in zip(grid_missing, lb_traj, ub_traj)
            ],
            "svg_visualization": svg_chart,
            "apa_narrative": apa
        }
