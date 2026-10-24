"""
Dynamic Treatment Regimes (DTR) & Sequential Q-Learning Decision Engine
Author: DataTrust Platform Architecture
Reference:
- Murphy, S. A. (2003). Optimal dynamic treatment regimes. Journal of the Royal Statistical Society: Series B (Statistical Methodology), 65(2), 331-355.
- Robins, J. M. (2004). Optimal structural nested models for optimal sequential decisions. In Proceedings of the Second Seattle Symposium in Biostatistics (pp. 189-326). Springer, New York, NY.
- Schulte, P. J., Tsiatis, A. A., Laber, E. B., & Davidian, M. (2014). Q-and A-learning methods for estimating optimal dynamic treatment regimes. Statistical Science, 29(4), 640-661.
- Chakraborty, B., & Moodie, E. E. (2013). Statistical Methods for Dynamic Treatment Regimes: Reinforcement Learning, Causal Inference, and Personalized Medicine. Springer.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats


def generate_dtr_svg(
    v_optimal: float,
    v_always: float,
    v_never: float,
    v_observed: float,
    stage1_tailor_name: str,
    stage1_threshold: float,
    stage2_tailor_name: str,
    stage2_threshold: float,
    pct_stage1_treated: float,
    pct_stage2_treated: float,
    outcome_label: str
) -> str:
    """
    Generates a high-clarity dual-panel SVG diagram:
    Panel A: Adaptive 2-Stage Sequential Decision Flowchart (DTR Tree).
    Panel B: Policy Expected Value Comparison (Optimal DTR vs Static Regimes).
    """
    w, h = 940, 480
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; background-color: #0f172a;">')
    
    # Gradients & Defs
    svg.append('''
    <defs>
      <linearGradient id="optGrad" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#10b981"/>
        <stop offset="100%" stop-color="#059669"/>
      </linearGradient>
      <linearGradient id="compGrad" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#6366f1"/>
        <stop offset="100%" stop-color="#4f46e5"/>
      </linearGradient>
      <linearGradient id="nodeGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#1e293b"/>
        <stop offset="100%" stop-color="#0f172a"/>
      </linearGradient>
      <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
        <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000000" flood-opacity="0.4"/>
      </filter>
    </defs>
    ''')

    # Title & Subtitle
    svg.append(f'<text x="24" y="32" fill="#f8fafc" font-size="16" font-weight="bold">Q-Learning: Chế độ Can thiệp Động Đa Giai đoạn (Dynamic Treatment Regimes - Murphy 2003)</text>')
    svg.append(f'<text x="24" y="52" fill="#94a3b8" font-size="11">Tối ưu hóa chính sách thích ứng hai giai đoạn (Stage 1 &rarr; Interim State &rarr; Stage 2 &rarr; Outcome: {outcome_label})</text>')

    # ------------------ PANEL A: Decision Flow Tree (Left side: w=520, h=380) ------------------
    p1_x, p1_y, p1_w, p1_h = 24, 75, 500, 360
    svg.append(f'<rect x="{p1_x}" y="{p1_y}" width="{p1_w}" height="{p1_h}" rx="10" fill="#1e293b" fill-opacity="0.4" stroke="#334155" stroke-width="1"/>')
    svg.append(f'<text x="{p1_x+16}" y="{p1_y+24}" fill="#38bdf8" font-size="12" font-weight="600">Panel A: Cây Quyết định Chính sách Thích ứng (Optimal Decision Rule d*)</text>')

    # Stage 1 Node (Root)
    s1_rx, s1_ry, s1_rw, s1_rh = p1_x + 20, p1_y + 140, 120, 60
    svg.append(f'<rect x="{s1_rx}" y="{s1_ry}" width="{s1_rw}" height="{s1_rh}" rx="8" fill="url(#nodeGrad)" stroke="#38bdf8" stroke-width="1.5" filter="url(#shadow)"/>')
    svg.append(f'<text x="{s1_rx+60}" y="{s1_ry+22}" fill="#38bdf8" font-size="11" font-weight="bold" text-anchor="middle">Giai đoạn 1 (S1)</text>')
    svg.append(f'<text x="{s1_rx+60}" y="{s1_ry+38}" fill="#cbd5e1" font-size="9.5" text-anchor="middle">{stage1_tailor_name[:14]}</text>')
    svg.append(f'<text x="{s1_rx+60}" y="{s1_ry+52}" fill="#94a3b8" font-size="8.5" text-anchor="middle">Ngưỡng &gt; {stage1_threshold:.2f}</text>')

    # Branches from S1 to S2
    # Upper branch: A1 = 1
    s2a_rx, s2a_ry, s2a_rw, s2a_rh = p1_x + 190, p1_y + 65, 130, 65
    svg.append(f'<path d="M {s1_rx+s1_rw} {s1_ry+20} C {s1_rx+s1_rw+30} {s1_ry+20}, {s2a_rx-30} {s2a_ry+32}, {s2a_rx} {s2a_ry+32}" fill="none" stroke="#10b981" stroke-width="2"/>')
    svg.append(f'<rect x="{s1_rx+s1_rw+15}" y="{s1_ry-15}" width="36" height="18" rx="4" fill="#064e3b" stroke="#10b981" stroke-width="1"/>')
    svg.append(f'<text x="{s1_rx+s1_rw+33}" y="{s1_ry-3}" fill="#34d399" font-size="9" font-weight="bold" text-anchor="middle">A1=1</text>')

    # Lower branch: A1 = 0
    s2b_rx, s2b_ry, s2b_rw, s2b_rh = p1_x + 190, p1_y + 215, 130, 65
    svg.append(f'<path d="M {s1_rx+s1_rw} {s1_ry+40} C {s1_rx+s1_rw+30} {s1_ry+40}, {s2b_rx-30} {s2b_ry+32}, {s2b_rx} {s2b_ry+32}" fill="none" stroke="#64748b" stroke-width="2"/>')
    svg.append(f'<rect x="{s1_rx+s1_rw+15}" y="{s1_ry+45}" width="36" height="18" rx="4" fill="#1e293b" stroke="#64748b" stroke-width="1"/>')
    svg.append(f'<text x="{s1_rx+s1_rw+33}" y="{s1_ry+57}" fill="#94a3b8" font-size="9" font-weight="bold" text-anchor="middle">A1=0</text>')

    # Stage 2 Node A (under A1=1)
    svg.append(f'<rect x="{s2a_rx}" y="{s2a_ry}" width="{s2a_rw}" height="{s2a_rh}" rx="8" fill="url(#nodeGrad)" stroke="#10b981" stroke-width="1.5" filter="url(#shadow)"/>')
    svg.append(f'<text x="{s2a_rx+65}" y="{s2a_ry+20}" fill="#34d399" font-size="10.5" font-weight="bold" text-anchor="middle">Giai đoạn 2 (A1=1)</text>')
    svg.append(f'<text x="{s2a_rx+65}" y="{s2a_ry+38}" fill="#cbd5e1" font-size="9" text-anchor="middle">Đo lường: {stage2_tailor_name[:12]}</text>')
    svg.append(f'<text x="{s2a_rx+65}" y="{s2a_ry+52}" fill="#94a3b8" font-size="8.5" text-anchor="middle">Ngưỡng &gt; {stage2_threshold:.2f}</text>')

    # Stage 2 Node B (under A1=0)
    svg.append(f'<rect x="{s2b_rx}" y="{s2b_ry}" width="{s2b_rw}" height="{s2b_rh}" rx="8" fill="url(#nodeGrad)" stroke="#64748b" stroke-width="1.5" filter="url(#shadow)"/>')
    svg.append(f'<text x="{s2b_rx+65}" y="{s2b_ry+20}" fill="#cbd5e1" font-size="10.5" font-weight="bold" text-anchor="middle">Giai đoạn 2 (A1=0)</text>')
    svg.append(f'<text x="{s2b_rx+65}" y="{s2b_ry+38}" fill="#cbd5e1" font-size="9" text-anchor="middle">Đo lường: {stage2_tailor_name[:12]}</text>')
    svg.append(f'<text x="{s2b_rx+65}" y="{s2b_ry+52}" fill="#94a3b8" font-size="8.5" text-anchor="middle">Ngưỡng &gt; {stage2_threshold:.2f}</text>')

    # Terminal Payoffs (4 paths)
    outcomes_y = [p1_y + 45, p1_y + 115, p1_y + 195, p1_y + 265]
    outcomes_labels = ["A2=1 (Intensive)", "A2=0 (Maintain)", "A2=1 (Rescue)", "A2=0 (Control)"]
    outcomes_colors = ["#10b981", "#3b82f6", "#f59e0b", "#64748b"]

    for idx, (oy, olbl, col) in enumerate(zip(outcomes_y, outcomes_labels, outcomes_colors)):
        src_x = s2a_rx + s2a_rw if idx < 2 else s2b_rx + s2b_rw
        src_y = s2a_ry + (20 if idx == 0 else 45) if idx < 2 else s2b_ry + (20 if idx == 2 else 45)
        dest_x = p1_x + 375
        
        svg.append(f'<path d="M {src_x} {src_y} C {src_x+25} {src_y}, {dest_x-25} {oy+15}, {dest_x} {oy+15}" fill="none" stroke="{col}" stroke-width="1.5"/>')
        svg.append(f'<rect x="{dest_x}" y="{oy}" width="110" height="30" rx="5" fill="#0f172a" stroke="{col}" stroke-width="1"/>')
        svg.append(f'<text x="{dest_x+55}" y="{oy+19}" fill="{col}" font-size="9.5" font-weight="600" text-anchor="middle">{olbl}</text>')

    # S1 treated rate caption
    svg.append(f'<text x="{p1_x+16}" y="{p1_y+p1_h-18}" fill="#94a3b8" font-size="10">Tỷ lệ can thiệp tối ưu: S1={pct_stage1_treated*100:.1f}%, S2={pct_stage2_treated*100:.1f}%</text>')

    # ------------------ PANEL B: Policy Value Comparison (Right side: w=350, h=380) ------------------
    p2_x, p2_y, p2_w, p2_h = 548, 75, 368, 360
    svg.append(f'<rect x="{p2_x}" y="{p2_y}" width="{p2_w}" height="{p2_h}" rx="10" fill="#1e293b" fill-opacity="0.4" stroke="#334155" stroke-width="1"/>')
    svg.append(f'<text x="{p2_x+16}" y="{p2_y+24}" fill="#38bdf8" font-size="12" font-weight="600">Panel B: Kỳ vọng Kết quả theo Chính sách V(d)</text>')

    # Values list for bars
    policies = [
        ("DTR Thích ứng (d*)", v_optimal, "#10b981", "url(#optGrad)"),
        ("Luôn Can thiệp (1, 1)", v_always, "#6366f1", "url(#compGrad)"),
        ("Quan sát Thực tế", v_observed, "#38bdf8", "#0284c7"),
        ("Không Can thiệp (0, 0)", v_never, "#64748b", "#475569")
    ]

    all_vals = [p[1] for p in policies]
    min_v = min(0.0, min(all_vals) * 0.8)
    max_v = max(all_vals) * 1.25 if max(all_vals) > 0 else 1.0

    bar_start_y = p2_y + 55
    bar_h = 42
    bar_gap = 25
    chart_max_w = p2_w - 140

    for idx, (p_name, val, color_code, fill_style) in enumerate(policies):
        cy = bar_start_y + idx * (bar_h + bar_gap)
        bar_len = max(10.0, (val / max_v) * chart_max_w)
        
        svg.append(f'<text x="{p2_x+16}" y="{cy+16}" fill="#e2e8f0" font-size="11" font-weight="600">{p_name}</text>')
        svg.append(f'<rect x="{p2_x+16}" y="{cy+24}" width="{bar_len}" height="20" rx="4" fill="{fill_style}" stroke="{color_code}" stroke-width="1"/>')
        svg.append(f'<text x="{p2_x+16+bar_len+8}" y="{cy+38}" fill="{color_code}" font-size="12" font-weight="bold">{val:.3f}</text>')

    # Gain highlight box
    gain = v_optimal - v_never
    gain_pct = (gain / max(abs(v_never), 0.01)) * 100
    svg.append(f'<rect x="{p2_x+16}" y="{p2_y+p2_h-65}" width="{p2_w-32}" height="48" rx="6" fill="#064e3b" fill-opacity="0.5" stroke="#10b981" stroke-width="1"/>')
    svg.append(f'<text x="{p2_x+26}" y="{p2_y+p2_h-45}" fill="#a7f3d0" font-size="10.5" font-weight="bold">Giá trị Gia tăng Chính sách (&Delta;V*): +{gain:.3f} (+{gain_pct:.1f}%)</text>')
    svg.append(f'<text x="{p2_x+26}" y="{p2_y+p2_h-28}" fill="#6ee7b7" font-size="9.5">Chính sách thích ứng cá nhân hóa vượt trội mọi chiến lược tĩnh.</text>')

    # Footer note
    svg.append(f'<text x="24" y="{h-10}" fill="#64748b" font-size="10">Q-Learning Quy nạp Ngược (Backward Induction; Murphy 2003; Robins 2004; Schulte et al. 2014) &bull; Tối ưu hóa toàn cục chuỗi quyết định động.</text>')

    svg.append('</svg>')
    return '\n'.join(svg)


class DynamicTreatmentRegimesEngine:
    """
    Engine estimating Two-Stage Dynamic Treatment Regimes (DTR)
    via Sequential Q-Learning Backward Induction (Murphy 2003, Robins 2004, Schulte et al. 2014).
    """

    @staticmethod
    def evaluate_dtr(
        y_outcome: np.ndarray,
        a1_stage1: np.ndarray,
        a2_stage2: np.ndarray,
        x1_baseline: np.ndarray,
        x2_interim: np.ndarray,
        x1_label: str = "Baseline Covariate",
        x2_label: str = "Interim State",
        outcome_label: str = "Outcome"
    ) -> Dict[str, Any]:
        """
        Executes 2-stage Q-learning backward induction:
        Stage 2: Q2(H2, A2) = beta_20 + beta_21*A2 + gamma_2*H2 + theta_2*(A2*H2)
        Stage 1: Q1(H1, A1) = beta_10 + beta_11*A1 + gamma_1*H1 + theta_1*(A1*H1)
        where pseudo-outcome Y_tilde = max_a2 Q2(H2, a2).
        """
        y = np.asarray(y_outcome, dtype=float)
        a1 = np.asarray(a1_stage1, dtype=int)
        a2 = np.asarray(a2_stage2, dtype=int)
        x1 = np.asarray(x1_baseline, dtype=float)
        x2 = np.asarray(x2_interim, dtype=float)

        n = len(y)
        if n < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 25 quan sát đầy đủ hai giai đoạn để ước lượng DTR (N={n})."
            }

        # Filter out NaN
        valid = ~np.isnan(y) & ~np.isnan(x1) & ~np.isnan(x2) & (a1 >= 0) & (a2 >= 0)
        y, a1, a2, x1, x2 = y[valid], a1[valid], a2[valid], x1[valid], x2[valid]
        n_clean = len(y)
        if n_clean < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số quan sát sạch hai giai đoạn không đủ (N={n_clean})."
            }

        # ---------------- Stage 2 Q-Learning Regression ----------------
        # History H2 = (1, x1, a1, x2)
        # Model: Y = beta_20 + gamma_21*x1 + gamma_22*a1 + gamma_23*x2 + a2*(beta_21_main + theta_21*x2)
        # Design matrix Z2: [1, x1, a1, x2, a2, a2*x2]
        ones = np.ones(n_clean)
        z2 = np.column_stack([ones, x1, a1, x2, a2, a2 * x2])
        
        try:
            beta2, residuals, rank, s = np.linalg.lstsq(z2, y, rcond=None)
            pred_y_s2 = z2 @ beta2
            res2 = y - pred_y_s2
            dof2 = max(n_clean - z2.shape[1], 1)
            sigma2_sq = float(np.sum(res2**2) / dof2)
            cov_beta2 = np.linalg.pinv(z2.T @ z2) * sigma2_sq
            se_beta2 = np.sqrt(np.maximum(np.diag(cov_beta2), 1e-8))
            t_beta2 = beta2 / se_beta2
            p_beta2 = 2.0 * (1.0 - stats.t.cdf(np.abs(t_beta2), df=dof2))
        except Exception as e:
            return {
                "status": "ESTIMATION_FAILED",
                "message": f"Lỗi tối ưu hóa hồi quy Stage 2: {str(e)}"
            }

        # Stage 2 optimal action: argmax_a2 Q2(H2, a2)
        # Difference delta_Q2 = Q2(H2, 1) - Q2(H2, 0) = beta2[4] + beta2[5]*x2
        delta_q2 = beta2[4] + beta2[5] * x2
        opt_a2 = (delta_q2 > 0).astype(int)

        # Stage 2 Threshold on x2 where delta_q2 == 0:
        # beta2[4] + beta2[5]*x2 = 0 => x2 = -beta2[4] / beta2[5]
        if abs(beta2[5]) > 1e-5:
            s2_threshold = float(-beta2[4] / beta2[5])
        else:
            s2_threshold = float(np.median(x2))

        # Predicted counterfactual outcome under optimal Stage 2:
        # Y_tilde_1 = Q2(H2, opt_a2)
        z2_opt = np.column_stack([ones, x1, a1, x2, opt_a2, opt_a2 * x2])
        y_tilde_1 = z2_opt @ beta2

        # ---------------- Stage 1 Q-Learning Regression ----------------
        # History H1 = (1, x1)
        # Model: Y_tilde_1 = beta_10 + gamma_11*x1 + a1*(beta_11_main + theta_11*x1)
        # Design matrix Z1: [1, x1, a1, a1*x1]
        z1 = np.column_stack([ones, x1, a1, a1 * x1])
        try:
            beta1, residuals1, rank1, s1 = np.linalg.lstsq(z1, y_tilde_1, rcond=None)
            pred_y_s1 = z1 @ beta1
            res1 = y_tilde_1 - pred_y_s1
            dof1 = max(n_clean - z1.shape[1], 1)
            sigma1_sq = float(np.sum(res1**2) / dof1)
            cov_beta1 = np.linalg.pinv(z1.T @ z1) * sigma1_sq
            se_beta1 = np.sqrt(np.maximum(np.diag(cov_beta1), 1e-8))
            t_beta1 = beta1 / se_beta1
            p_beta1 = 2.0 * (1.0 - stats.t.cdf(np.abs(t_beta1), df=dof1))
        except Exception as e:
            return {
                "status": "ESTIMATION_FAILED",
                "message": f"Lỗi tối ưu hóa hồi quy Stage 1: {str(e)}"
            }

        # Stage 1 optimal action: argmax_a1 Q1(H1, a1)
        # Difference delta_Q1 = Q1(H1, 1) - Q1(H1, 0) = beta1[2] + beta1[3]*x1
        delta_q1 = beta1[2] + beta1[3] * x1
        opt_a1 = (delta_q1 > 0).astype(int)

        if abs(beta1[3]) > 1e-5:
            s1_threshold = float(-beta1[2] / beta1[3])
        else:
            s1_threshold = float(np.median(x1))

        # ---------------- Policy Expected Values V(d) ----------------
        # 1. Optimal DTR: E[max_a1 Q1(H1, a1)]
        z1_opt = np.column_stack([ones, x1, opt_a1, opt_a1 * x1])
        v_optimal = float(np.mean(z1_opt @ beta1))

        # 2. Static Always Treat (1, 1)
        z1_always = np.column_stack([ones, x1, np.ones(n_clean), x1])
        v_always = float(np.mean(z1_always @ beta1))

        # 3. Static Never Treat (0, 0)
        z1_never = np.column_stack([ones, x1, np.zeros(n_clean), np.zeros(n_clean)])
        v_never = float(np.mean(z1_never @ beta1))

        # 4. Empirical observed average
        v_observed = float(np.mean(y))

        pct_s1_treated = float(np.mean(opt_a1))
        pct_s2_treated = float(np.mean(opt_a2))

        # Scientific SVG
        svg_chart = generate_dtr_svg(
            v_optimal=v_optimal,
            v_always=v_always,
            v_never=v_never,
            v_observed=v_observed,
            stage1_tailor_name=x1_label,
            stage1_threshold=s1_threshold,
            stage2_tailor_name=x2_label,
            stage2_threshold=s2_threshold,
            pct_stage1_treated=pct_s1_treated,
            pct_stage2_treated=pct_s2_treated,
            outcome_label=outcome_label
        )

        # Stage 1 / Stage 2 Tailoring Direction
        s1_dir = "lớn hơn" if beta1[3] > 0 else "nhỏ hơn"
        s2_dir = "lớn hơn" if beta2[5] > 0 else "nhỏ hơn"

        gain = float(v_optimal - v_never)
        gain_pct = float((gain / max(abs(v_never), 1e-4)) * 100)

        apa = (
            f"Phân tích Chế độ Can thiệp Động Đa Giai đoạn (Dynamic Treatment Regimes - DTR; "
            f"Murphy, 2003; Robins, 2004; Schulte et al., 2014) thông qua thuật toán Q-Learning Quy nạp Ngược "
            f"(Backward Induction) được thực hiện trên mẫu khảo sát N = {n_clean}. "
            f"Ở Giai đoạn 2 (Stage 2 Q-function), biến đo lường giữa kỳ '{x2_label}' đóng vai trò biến điều chỉnh can thiệp "
            f"(hệ số tương tác beta = {beta2[5]:.4f}, SE = {se_beta2[5]:.4f}, t = {t_beta2[5]:.3f}, p = {p_beta2[5]:.4f}), "
            f"với ngưỡng quyết định tối ưu x2* = {s2_threshold:.2f} (can thiệp A2=1 khi giá trị {s2_dir} ngưỡng). "
            f"Ở Giai đoạn 1 (Stage 1 Q-function), biến nền tảng '{x1_label}' xác định quy tắc phân bổ can thiệp ban đầu "
            f"(hệ số tương tác beta = {beta1[3]:.4f}, SE = {se_beta1[3]:.4f}, t = {t_beta1[3]:.3f}, p = {p_beta1[3]:.4f}), "
            f"với ngưỡng quyết định ban đầu x1* = {s1_threshold:.2f} (can thiệp A1=1 khi giá trị {s1_dir} ngưỡng). "
            f"Giá trị kỳ vọng của Chính sách Thích ứng Tối ưu đạt V(d*) = {v_optimal:.3f}, vượt trội hơn chiến lược Tĩnh Luôn can thiệp "
            f"V(1,1) = {v_always:.3f}, chiến lược Tĩnh Không can thiệp V(0,0) = {v_never:.3f}, và trung bình quan sát thực tế "
            f"V_obs = {v_observed:.3f} (Mức thặng dư giá trị chính sách Delta V* = +{gain:.3f}, tương đương tăng +{gain_pct:.1f}%). "
            f"Tỷ lệ cá nhân được khuyến nghị can thiệp thích ứng là {pct_s1_treated*100:.1f}% ở Giai đoạn 1 và {pct_s2_treated*100:.1f}% ở Giai đoạn 2."
        )

        return {
            "status": "SUCCESS",
            "model_type": "DYNAMIC_TREATMENT_REGIMES_Q_LEARNING_2003",
            "diagnostics": {
                "sample_size": n_clean,
                "v_optimal": round(v_optimal, 4),
                "v_always_treated": round(v_always, 4),
                "v_never_treated": round(v_never, 4),
                "v_observed": round(v_observed, 4),
                "policy_value_gain": round(gain, 4),
                "policy_value_gain_pct": round(gain_pct, 2),
                "pct_stage1_treated": round(pct_s1_treated, 4),
                "pct_stage2_treated": round(pct_s2_treated, 4),
                "stage1_threshold": round(s1_threshold, 4),
                "stage2_threshold": round(s2_threshold, 4)
            },
            "stage1_model": {
                "intercept": round(float(beta1[0]), 4),
                "main_x1": round(float(beta1[1]), 4),
                "main_a1": round(float(beta1[2]), 4),
                "interaction_a1_x1": round(float(beta1[3]), 4),
                "se_interaction": round(float(se_beta1[3]), 4),
                "t_stat": round(float(t_beta1[3]), 4),
                "p_value": round(float(p_beta1[3]), 4),
                "r_squared": round(float(1.0 - np.sum(res1**2) / np.sum((y_tilde_1 - np.mean(y_tilde_1))**2)), 4)
            },
            "stage2_model": {
                "intercept": round(float(beta2[0]), 4),
                "main_x1": round(float(beta2[1]), 4),
                "main_a1": round(float(beta2[2]), 4),
                "main_x2": round(float(beta2[3]), 4),
                "main_a2": round(float(beta2[4]), 4),
                "interaction_a2_x2": round(float(beta2[5]), 4),
                "se_interaction": round(float(se_beta2[5]), 4),
                "t_stat": round(float(t_beta2[5]), 4),
                "p_value": round(float(p_beta2[5]), 4),
                "r_squared": round(float(1.0 - np.sum(res2**2) / np.sum((y - np.mean(y))**2)), 4)
            },
            "svg_visualization": svg_chart,
            "apa_narrative": apa
        }
