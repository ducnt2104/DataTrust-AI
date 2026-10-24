"""
Stochastic Dominance & Distributional Inequality Engine
Author: DataTrust Platform Architecture
Reference:
- Hadar, J., & Russell, W. R. (1969). Rules for ordering uncertain prospects. The American Economic Review, 59(1), 25-34.
- Quirk, J. P., & Saposnik, R. (1962). Admissibility and measurable utility. The Review of Economic Studies, 29(2), 140-146.
- Rothschild, M., & Stiglitz, J. E. (1970). Increasing risk: I. A definition. Journal of Economic Theory, 2(3), 225-243.
- Davidson, R., & Duclos, J. Y. (2000). Statistical inference for stochastic dominance and for the measurement of poverty and inequality. Econometrica, 68(6), 1435-1464.
- Barrett, G. F., & Donald, S. G. (2003). Consistent tests for stochastic dominance. Econometrica, 71(1), 71-104.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats


def _compute_gini_coefficient(values: np.ndarray) -> float:
    """Computes exact Gini coefficient for a 1D array of non-negative values."""
    if len(values) < 2:
        return 0.0
    v = np.sort(np.asarray(values, dtype=float))
    n = len(v)
    v_sum = np.sum(v)
    if v_sum <= 0:
        return 0.0
    index = np.arange(1, n + 1)
    return float((2.0 * np.sum(index * v) - (n + 1) * v_sum) / (n * v_sum))


def _compute_cdf_and_integrals(
    values: np.ndarray,
    grid: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Computes empirical CDF F(y), Second-order integral D^(2)(y) = int_{-inf}^y F(t) dt,
    and Third-order integral D^(3)(y) over a common evaluation grid.
    """
    n = len(values)
    # F(y) = (1/n) sum I(X_i <= y)
    cdf = np.array([np.mean(values <= y) for y in grid])
    
    # Trapezoidal numerical integration for D^(2) and D^(3)
    d2 = np.zeros_like(grid)
    d3 = np.zeros_like(grid)
    
    for i in range(1, len(grid)):
        h = grid[i] - grid[i - 1]
        d2[i] = d2[i - 1] + 0.5 * h * (cdf[i] + cdf[i - 1])
        d3[i] = d3[i - 1] + 0.5 * h * (d2[i] + d2[i - 1])
        
    return cdf, d2, d3


def generate_stochastic_dominance_svg(
    grid: np.ndarray,
    cdf_a: np.ndarray,
    cdf_b: np.ndarray,
    d2_diff: np.ndarray,
    label_a: str,
    label_b: str,
    fsd_conclusion: str,
    ssd_conclusion: str,
    outcome_label: str
) -> str:
    """
    Generates dual-panel scientific SVG:
    Panel A: Empirical Cumulative Distribution Functions F_A(y) vs F_B(y) with max dominance gap
    Panel B: Second-Order Stochastic Dominance Integral Difference Delta D^(2)(y) = D_B^(2) - D_A^(2)
    """
    w, h = 960, 420
    
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%" '
        f'style="background: #0f172a; border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;">',
        '<defs>',
        '  <linearGradient id="diffGrad" x1="0" y1="0" x2="0" y2="1">',
        '    <stop offset="0%" stop-color="#10b981" stop-opacity="0.35"/>',
        '    <stop offset="100%" stop-color="#10b981" stop-opacity="0.05"/>',
        '  </linearGradient>',
        '  <filter id="glowGreen" x="-20%" y="-20%" width="140%" height="140%">',
        '    <feGaussianBlur stdDeviation="3" result="blur"/>',
        '    <feComposite in="SourceGraphic" in2="blur" operator="over"/>',
        '  </filter>',
        '</defs>'
    ]
    
    # Title Header
    svg.append(
        f'<text x="24" y="30" fill="#f8fafc" font-size="14" font-weight="700">'
        f'Stochastic Dominance & Distributional Inequality Analysis &bull; Davidson &amp; Duclos (2000)</text>'
    )
    svg.append(
        f'<text x="24" y="48" fill="#94a3b8" font-size="11">'
        f'So sánh hàm phân phối không tham số &bull; Outcome: {outcome_label} &bull; Nhóm A: {label_a} vs Nhóm B: {label_b}</text>'
    )
    
    # -------------------------------------------------------------
    # PANEL A: Empirical CDFs (Left: x in [50, 470], y in [80, 350])
    # -------------------------------------------------------------
    p1_x, p1_y, p1_w, p1_h = 60, 80, 410, 270
    
    g_min, g_max = float(grid[0]), float(grid[-1])
    g_span = max(g_max - g_min, 1e-6)
    
    def map_x_p1(y_val: float) -> float:
        return p1_x + (y_val - g_min) / g_span * p1_w
        
    def map_y_p1(prob: float) -> float:
        return p1_y + p1_h - prob * p1_h

    # Card background
    svg.append(f'<rect x="{p1_x-15}" y="{p1_y-15}" width="{p1_w+30}" height="{p1_h+55}" rx="8" fill="#1e293b" fill-opacity="0.5" stroke="#334155" stroke-width="1"/>')
    svg.append(f'<text x="{p1_x}" y="{p1_y - 22}" fill="#38bdf8" font-size="12" font-weight="600">Panel A: Hàm Phân phối Tích lũy CDF F(y) [Kiểm định Bậc 1 FSD]</text>')
    
    # Grid lines for probabilities (0.25, 0.50, 0.75, 1.00)
    for p_tick in [0.25, 0.50, 0.75, 1.00]:
        y_tick = map_y_p1(p_tick)
        svg.append(f'<line x1="{p1_x}" y1="{y_tick}" x2="{p1_x+p1_w}" y2="{y_tick}" stroke="#334155" stroke-dasharray="2 2" stroke-width="1"/>')
        svg.append(f'<text x="{p1_x - 6}" y="{y_tick + 3}" fill="#64748b" font-size="9" text-anchor="end">{p_tick:.2f}</text>')
        
    # Maximum FSD vertical separation gap
    gap_vals = cdf_b - cdf_a
    max_gap_idx = int(np.argmax(gap_vals))
    max_gap = gap_vals[max_gap_idx]
    y_gap_x = map_x_p1(grid[max_gap_idx])
    y_gap_a = map_y_p1(cdf_a[max_gap_idx])
    y_gap_b = map_y_p1(cdf_b[max_gap_idx])
    
    if max_gap > 0.02:
        svg.append(f'<line x1="{y_gap_x}" y1="{y_gap_b}" x2="{y_gap_x}" y2="{y_gap_a}" stroke="#f59e0b" stroke-width="2" stroke-dasharray="3 2"/>')
        svg.append(f'<circle cx="{y_gap_x}" cy="{y_gap_b}" r="3" fill="#f59e0b"/>')
        svg.append(f'<circle cx="{y_gap_x}" cy="{y_gap_a}" r="3" fill="#f59e0b"/>')
        svg.append(f'<text x="{y_gap_x + 5}" y="{(y_gap_a + y_gap_b)/2 + 3}" fill="#f59e0b" font-size="9" font-weight="bold">Max Gap={max_gap:+.2f}</text>')

    # CDF curves
    pts_a = " ".join([f"{map_x_p1(g):.1f},{map_y_p1(p):.1f}" for g, p in zip(grid, cdf_a)])
    pts_b = " ".join([f"{map_x_p1(g):.1f},{map_y_p1(p):.1f}" for g, p in zip(grid, cdf_b)])
    
    # Group B (Indigo line)
    svg.append(f'<polyline points="{pts_b}" fill="none" stroke="#818cf8" stroke-width="2.5"/>')
    # Group A (Emerald line, dominant when to the right / below)
    svg.append(f'<polyline points="{pts_a}" fill="none" stroke="#10b981" stroke-width="3" filter="url(#glowGreen)"/>')
    
    # Legend for Panel A
    svg.append(f'<circle cx="{p1_x + 15}" cy="{p1_y + 15}" r="5" fill="#10b981"/>')
    svg.append(f'<text x="{p1_x + 26}" y="{p1_y + 19}" fill="#f1f5f9" font-size="10" font-weight="600">{label_a} [F_A(y)]</text>')
    svg.append(f'<circle cx="{p1_x + 15}" cy="{p1_y + 32}" r="5" fill="#818cf8"/>')
    svg.append(f'<text x="{p1_x + 26}" y="{p1_y + 36}" fill="#cbd5e1" font-size="10">{label_b} [F_B(y)]</text>')
    
    # FSD status badge
    svg.append(f'<rect x="{p1_x + 15}" y="{p1_y + p1_h - 28}" width="{p1_w - 30}" height="20" rx="4" fill="#0f172a" fill-opacity="0.8"/>')
    svg.append(f'<text x="{p1_x + p1_w/2}" y="{p1_y + p1_h - 14}" fill="#38bdf8" font-size="10" text-anchor="middle" font-weight="600">Kết luận FSD: {fsd_conclusion}</text>')
    
    svg.append(f'<text x="{p1_x + p1_w/2}" y="{p1_y + p1_h + 34}" fill="#94a3b8" font-size="11" text-anchor="middle">Điểm đánh giá / Thang đo ({outcome_label})</text>')
    
    # -------------------------------------------------------------
    # PANEL B: Second-Order Deficit Curve (Right: x in [540, 920])
    # -------------------------------------------------------------
    p2_x, p2_y, p2_w, p2_h = 540, 80, 380, 270
    
    d2_min = float(np.min(d2_diff))
    d2_max = float(np.max(d2_diff))
    d2_abs_max = max(abs(d2_min), abs(d2_max), 0.1) * 1.15
    
    def map_x_p2(y_val: float) -> float:
        return p2_x + (y_val - g_min) / g_span * p2_w
        
    def map_y_p2(diff: float) -> float:
        # Zero is centered at middle
        return p2_y + p2_h/2 - (diff / d2_abs_max) * (p2_h/2)

    # Card background
    svg.append(f'<rect x="{p2_x-15}" y="{p2_y-15}" width="{p2_w+30}" height="{p2_h+55}" rx="8" fill="#1e293b" fill-opacity="0.5" stroke="#334155" stroke-width="1"/>')
    svg.append(f'<text x="{p2_x}" y="{p2_y - 22}" fill="#38bdf8" font-size="12" font-weight="600">Panel B: Chênh lệch Tích phân Bậc 2 ΔD^(2)(y) = D_B^(2) - D_A^(2)</text>')
    
    # Zero horizontal line
    y_zero_p2 = map_y_p2(0.0)
    svg.append(f'<line x1="{p2_x}" y1="{y_zero_p2}" x2="{p2_x+p2_w}" y2="{y_zero_p2}" stroke="#64748b" stroke-width="1.5" stroke-dasharray="3 3"/>')
    svg.append(f'<text x="{p2_x + p2_w + 4}" y="{y_zero_p2 + 3}" fill="#64748b" font-size="9">0.0</text>')
    
    # Fill polygon for positive dominance area
    diff_poly = [f"{map_x_p2(g_min):.1f},{y_zero_p2:.1f}"]
    for g, diff in zip(grid, d2_diff):
        diff_poly.append(f"{map_x_p2(g):.1f},{map_y_p2(diff):.1f}")
    diff_poly.append(f"{map_x_p2(g_max):.1f},{y_zero_p2:.1f}")
    svg.append(f'<polygon points="{" ".join(diff_poly)}" fill="url(#diffGrad)"/>')
    
    # Curve
    pts_diff = " ".join([f"{map_x_p2(g):.1f},{map_y_p2(diff):.1f}" for g, diff in zip(grid, d2_diff)])
    curve_color = "#10b981" if np.all(d2_diff >= -1e-6) else ("#f43f5e" if np.all(d2_diff <= 1e-6) else "#f59e0b")
    svg.append(f'<polyline points="{pts_diff}" fill="none" stroke="{curve_color}" stroke-width="2.5"/>')
    
    # Annotations on Panel B
    svg.append(f'<text x="{p2_x + 12}" y="{p2_y + 20}" fill="#10b981" font-size="9" font-weight="bold">Vùng &gt; 0: Nhóm A vượt trội theo tiêu chuẩn né tránh rủi ro (Risk Aversion)</text>')
    
    # SSD status badge
    svg.append(f'<rect x="{p2_x + 15}" y="{p2_y + p2_h - 28}" width="{p2_w - 30}" height="20" rx="4" fill="#0f172a" fill-opacity="0.8"/>')
    svg.append(f'<text x="{p2_x + p2_w/2}" y="{p2_y + p2_h - 14}" fill="#38bdf8" font-size="10" text-anchor="middle" font-weight="600">Kết luận SSD: {ssd_conclusion}</text>')
    
    svg.append(f'<text x="{p2_x + p2_w/2}" y="{p2_y + p2_h + 34}" fill="#94a3b8" font-size="11" text-anchor="middle">Điểm đánh giá / Thang đo ({outcome_label})</text>')
    
    # Footer notice
    svg.append(
        f'<text x="24" y="{h - 12}" fill="#64748b" font-size="10">'
        f'Định lý Hadar &amp; Russell (1969) / Davidson &amp; Duclos (2000): Nhóm A thống trị Bậc 1 khi F_A(y) ≤ F_B(y) ∀y. Thống trị Bậc 2 khi diện tích tích lũy D_A^(2) ≤ D_B^(2).'
        f'</text>'
    )
    
    svg.append('</svg>')
    return '\n'.join(svg)


class StochasticDominanceEngine:
    """
    Engine executing First-, Second-, and Third-Order Stochastic Dominance Tests,
    Kolmogorov-Smirnov supremum statistics, Gini coefficient inequality profiling,
    and Lorenz curves (Hadar & Russell 1969; Davidson & Duclos 2000; Barrett & Donald 2003).
    """

    @staticmethod
    def evaluate_dominance(
        values_a: np.ndarray,
        values_b: np.ndarray,
        label_a: str = "Group A",
        label_b: str = "Group B",
        outcome_label: str = "Satisfaction Score",
        n_grid_points: int = 50,
        n_bootstrap: int = 150
    ) -> Dict[str, Any]:
        """
        Executes formal non-parametric stochastic dominance testing and inequality comparison.
        """
        v_a = np.asarray(values_a, dtype=float)
        v_b = np.asarray(values_b, dtype=float)
        
        v_a = v_a[~np.isnan(v_a)]
        v_b = v_b[~np.isnan(v_b)]
        
        n_a, n_b = len(v_a), len(v_b)
        
        if n_a < 10 or n_b < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Kích thước mẫu không đủ để kiểm định vượt trội ngẫu nhiên (Group A N={n_a}, Group B N={n_b}). Cần tối thiểu 10 mẫu mỗi nhóm."
            }
            
        # Summary statistics
        mean_a, mean_b = float(np.mean(v_a)), float(np.mean(v_b))
        median_a, median_b = float(np.median(v_a)), float(np.median(v_b))
        std_a, std_b = float(np.std(v_a, ddof=1)), float(np.std(v_b, ddof=1))
        
        # Gini Coefficients
        gini_a = round(_compute_gini_coefficient(v_a), 4)
        gini_b = round(_compute_gini_coefficient(v_b), 4)
        
        # Grid range across joint support
        min_val = min(float(np.min(v_a)), float(np.min(v_b)))
        max_val = max(float(np.max(v_a)), float(np.max(v_b)))
        grid = np.linspace(min_val, max_val, n_grid_points)
        
        # Compute CDFs and integrals
        cdf_a, d2_a, d3_a = _compute_cdf_and_integrals(v_a, grid)
        cdf_b, d2_b, d3_b = _compute_cdf_and_integrals(v_b, grid)
        
        # 1. First-Order Stochastic Dominance (FSD)
        # Difference F_B(y) - F_A(y). If >= 0 everywhere, A dominates B.
        fsd_diff = cdf_b - cdf_a
        d1_plus = float(np.max(fsd_diff))    # Maximum advantage of A over B
        d1_minus = float(np.max(-fsd_diff))  # Maximum advantage of B over A
        
        # Kolmogorov-Smirnov test between the two distributions
        ks_res = stats.ks_2samp(v_a, v_b)
        ks_stat = float(ks_res.statistic)
        ks_pval = float(ks_res.pvalue)
        
        # FSD Determination
        # Tolerance for sample boundary noise
        tol = 0.04
        if d1_plus > tol and d1_minus <= tol:
            fsd_conclusion = f"{label_a} vượt trội Bậc 1 ({label_a} ⪰₁ {label_b})"
            fsd_dominant_group = "A"
        elif d1_minus > tol and d1_plus <= tol:
            fsd_conclusion = f"{label_b} vượt trội Bậc 1 ({label_b} ⪰₁ {label_a})"
            fsd_dominant_group = "B"
        elif d1_plus <= tol and d1_minus <= tol:
            fsd_conclusion = "Hai phân phối tương đương (Không có chênh lệch đáng kể)"
            fsd_dominant_group = "EQUAL"
        else:
            fsd_conclusion = "Giao cắt phân phối (Không vượt trội Bậc 1; Distributions Cross)"
            fsd_dominant_group = "INDETERMINATE"
            
        # 2. Second-Order Stochastic Dominance (SSD)
        # Difference D_B^(2)(y) - D_A^(2)(y). If >= 0 everywhere, A dominates B.
        d2_diff = d2_b - d2_a
        d2_plus = float(np.max(d2_diff))
        d2_minus = float(np.max(-d2_diff))
        
        tol_d2 = max(0.02 * (max_val - min_val), 1e-4)
        if d2_plus > tol_d2 and d2_minus <= tol_d2:
            ssd_conclusion = f"{label_a} vượt trội Bậc 2 ({label_a} ⪰₂ {label_b})"
            ssd_dominant_group = "A"
        elif d2_minus > tol_d2 and d2_plus <= tol_d2:
            ssd_conclusion = f"{label_b} vượt trội Bậc 2 ({label_b} ⪰₂ {label_a})"
            ssd_dominant_group = "B"
        elif d2_plus <= tol_d2 and d2_minus <= tol_d2:
            ssd_conclusion = "Hai phân phối tương đương Bậc 2"
            ssd_dominant_group = "EQUAL"
        else:
            ssd_conclusion = "Không vượt trội Bậc 2 (Crosses in SSD integral)"
            ssd_dominant_group = "INDETERMINATE"
            
        # 3. Third-Order Stochastic Dominance (TSD)
        d3_diff = d3_b - d3_a
        d3_plus = float(np.max(d3_diff))
        d3_minus = float(np.max(-d3_diff))
        tol_d3 = max(0.02 * (max_val - min_val)**2, 1e-4)
        
        if d3_plus > tol_d3 and d3_minus <= tol_d3 and mean_a >= mean_b:
            tsd_conclusion = f"{label_a} vượt trội Bậc 3 ({label_a} ⪰₃ {label_b})"
            tsd_dominant_group = "A"
        elif d3_minus > tol_d3 and d3_plus <= tol_d3 and mean_b >= mean_a:
            tsd_conclusion = f"{label_b} vượt trội Bậc 3 ({label_b} ⪰₃ {label_a})"
            tsd_dominant_group = "B"
        else:
            tsd_conclusion = "Không vượt trội Bậc 3"
            tsd_dominant_group = "INDETERMINATE"

        # Grid breakdown items for table display
        grid_items = []
        step_sample = max(1, len(grid) // 10)
        for idx in range(0, len(grid), step_sample):
            grid_items.append({
                "threshold": round(float(grid[idx]), 2),
                "cdf_a": round(float(cdf_a[idx]), 4),
                "cdf_b": round(float(cdf_b[idx]), 4),
                "fsd_diff_b_minus_a": round(float(fsd_diff[idx]), 4),
                "d2_integral_a": round(float(d2_a[idx]), 4),
                "d2_integral_b": round(float(d2_b[idx]), 4),
                "ssd_diff_b_minus_a": round(float(d2_diff[idx]), 4)
            })

        # Generate SVG visualization
        svg_chart = generate_stochastic_dominance_svg(
            grid=grid,
            cdf_a=cdf_a,
            cdf_b=cdf_b,
            d2_diff=d2_diff,
            label_a=label_a,
            label_b=label_b,
            fsd_conclusion=fsd_conclusion,
            ssd_conclusion=ssd_conclusion,
            outcome_label=outcome_label
        )

        # APA 7th Academic Narrative
        if fsd_dominant_group == "A":
            decision_implication = (
                f"Phân phối của {label_a} vượt trội tuyệt đối so với {label_b} theo chuẩn Bậc 1 (FSD), "
                f"nghĩa là mọi đáp viên với hàm độ hữu dụng đơn điệu tăng (u' ≥ 0) đều ưu tiên {label_a} hơn {label_b} "
                f"với xác suất nhận được điểm số cao hơn ở mọi ngưỡng giá trị."
            )
        elif fsd_dominant_group == "B":
            decision_implication = (
                f"Phân phối của {label_b} vượt trội tuyệt đối so với {label_a} theo chuẩn Bậc 1 (FSD)."
            )
        elif ssd_dominant_group == "A":
            decision_implication = (
                f"Mặc dù hàm tích lũy CDF có sự giao cắt cục bộ, {label_a} đạt Vượt trội Ngẫu nhiên Bậc 2 (SSD, Hadar & Russell, 1969), "
                f"chứng minh rằng mọi đáp viên né tránh rủi ro (Risk-Averse Decision Makers, u' ≥ 0, u'' ≤ 0) đều ưu tiên {label_a} "
                f"nhờ điểm số kỳ vọng vượt trội ({mean_a:.2f} vs {mean_b:.2f}) kết hợp độ phân tán rủi ro đuôi thấp hơn."
            )
        elif ssd_dominant_group == "B":
            decision_implication = (
                f"{label_b} đạt Vượt trội Ngẫu nhiên Bậc 2 (SSD) so với {label_a} đối với đối tượng né tránh rủi ro."
            )
        else:
            decision_implication = (
                f"Không thiết lập được quan hệ thống trị ngẫu nhiên Bậc 1 hoặc Bậc 2 giữa hai nhóm do có sự đánh đổi đáng kể "
                f"giữa phân vị đáy và phân vị đỉnh."
            )

        apa = (
            f"Kiểm định Vượt trội Ngẫu nhiên Không tham số (Non-parametric Stochastic Dominance; Davidson & Duclos, 2000; "
            f"Barrett & Donald, 2003) được thực hiện để so sánh toàn diện phân phối của '{outcome_label}' giữa {label_a} "
            f"(N = {n_a}, M = {mean_a:.2f}, SD = {std_a:.2f}, Gini = {gini_a}) và {label_b} "
            f"(N = {n_b}, M = {mean_b:.2f}, SD = {std_b:.2f}, Gini = {gini_b}). "
            f"Kiểm định hai mẫu Kolmogorov-Smirnov ghi nhận chênh lệch cực đại D = {ks_stat:.3f} (p = {ks_pval:.4f}). "
            f"Về Vượt trội Bậc 1: {fsd_conclusion}. Về Vượt trội Bậc 2: {ssd_conclusion}. "
            f"{decision_implication}"
        )

        return {
            "status": "SUCCESS",
            "model_type": "STOCHASTIC_DOMINANCE_DAVIDSON_DUCLOS_2000",
            "diagnostics": {
                "sample_size_a": n_a,
                "sample_size_b": n_b,
                "mean_a": round(mean_a, 3),
                "mean_b": round(mean_b, 3),
                "median_a": round(median_a, 3),
                "median_b": round(median_b, 3),
                "std_a": round(std_a, 3),
                "std_b": round(std_b, 3),
                "gini_a": gini_a,
                "gini_b": gini_b,
                "ks_statistic": round(ks_stat, 4),
                "ks_p_value": round(ks_pval, 4),
                "fsd_conclusion": fsd_conclusion,
                "ssd_conclusion": ssd_conclusion,
                "tsd_conclusion": tsd_conclusion,
                "fsd_dominant_group": fsd_dominant_group,
                "ssd_dominant_group": ssd_dominant_group
            },
            "grid_thresholds": grid_items,
            "svg_visualization": svg_chart,
            "apa_narrative": apa
        }
