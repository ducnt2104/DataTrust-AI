"""
Multiple Testing Correction & False Discovery Rate (FDR) Matrix Engine.
Based on the foundational statistical methodologies of:
- Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. Journal of the Royal Statistical Society: Series B (Methodological), 57(1), 289-300.
- Benjamini, Y., & Yekutieli, D. (2001). The control of the false discovery rate in multiple testing under dependency. Annals of Statistics, 29(4), 1165-1188.
- Storey, J. D. (2002). A direct approach to false discovery rates. Journal of the Royal Statistical Society: Series B (Statistical Methodology), 64(3), 479-498.
"""

from typing import Dict, List, Any, Optional
import math
import numpy as np


def _t_to_p_two_tailed(t_stat: float, dof: int) -> float:
    """
    Approximates two-tailed p-value for Student t-distribution.
    """
    if dof <= 0:
        return 1.0
    x = t_stat ** 2 / (dof + t_stat ** 2)
    # Regularized incomplete beta function approximation or normal approximation if dof > 30
    if dof >= 30:
        z = abs(t_stat)
        p = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))
        return max(1e-15, min(1.0, float(p)))
    else:
        # Hill's approximation for moderate dof
        z = abs(t_stat) * (1.0 - 1.0 / (4.0 * dof)) / math.sqrt(1.0 + t_stat ** 2 / (2.0 * dof))
        p = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))
        return max(1e-15, min(1.0, float(p)))


def compute_fdr_corrections(
    p_values: List[float],
    labels: Optional[List[str]] = None,
    fdr_q: float = 0.05
) -> Dict[str, Any]:
    """
    Computes Benjamini-Hochberg (BH), Benjamini-Yekutieli (BY), and Bonferroni adjustments.
    """
    m = len(p_values)
    if m == 0:
        return {
            "status": "error",
            "message": "Không có giá trị p-value nào để hiệu chỉnh kiểm định lặp."
        }

    lbls = labels or [f"Hypothesis_{i+1}" for i in range(m)]

    # Validate and cap p-values
    clean_items = []
    for i, p in enumerate(p_values):
        try:
            pv = float(p)
            pv = max(0.0, min(1.0, pv))
            clean_items.append((pv, lbls[i], i))
        except (ValueError, TypeError):
            continue

    m_clean = len(clean_items)
    if m_clean == 0:
        return {
            "status": "error",
            "message": "Không có p-value hợp lệ."
        }

    # Sort ascending by p-value: p_(1) <= p_(2) <= ... <= p_(m)
    sorted_items = sorted(clean_items, key=lambda x: x[0])

    # 1. Harmonic sum for BY
    c_m = sum(1.0 / j for j in range(1, m_clean + 1))

    # 2. Compute BH step-up adjusted p-values
    # q_bh[i] = min_{j >= i} { (m / j) * p_(j) }
    bh_adjusted = [0.0] * m_clean
    running_min_bh = 1.0
    for rank_idx in range(m_clean - 1, -1, -1):
        j = rank_idx + 1  # 1-based rank
        val = (m_clean / float(j)) * sorted_items[rank_idx][0]
        running_min_bh = min(running_min_bh, val)
        bh_adjusted[rank_idx] = min(1.0, float(running_min_bh))

    # 3. Compute BY adjusted p-values
    by_adjusted = [0.0] * m_clean
    running_min_by = 1.0
    for rank_idx in range(m_clean - 1, -1, -1):
        j = rank_idx + 1
        val = (m_clean * c_m / float(j)) * sorted_items[rank_idx][0]
        running_min_by = min(running_min_by, val)
        by_adjusted[rank_idx] = min(1.0, float(running_min_by))

    # 4. Storey pi_0 estimate (lambda = 0.5)
    n_above_half = sum(1 for item in sorted_items if item[0] > 0.5)
    pi_0_est = min(1.0, max(0.05, float(n_above_half) / (m_clean * 0.5)))

    # Reconstruct results in sorted rank order
    results_list = []
    n_raw_sig = 0
    n_bh_sig = 0
    n_by_sig = 0
    n_bonf_sig = 0
    n_rescued_by_bh = 0
    n_false_pos_filtered = 0

    for rank_idx in range(m_clean):
        raw_p, label, orig_idx = sorted_items[rank_idx]
        rank_1b = rank_idx + 1
        q_bh = bh_adjusted[rank_idx]
        q_by = by_adjusted[rank_idx]
        p_bonf = min(1.0, raw_p * m_clean)

        bh_threshold = (float(rank_1b) / float(m_clean)) * fdr_q

        is_raw_sig = raw_p < fdr_q
        is_bh_sig = q_bh <= fdr_q
        is_by_sig = q_by <= fdr_q
        is_bonf_sig = p_bonf < fdr_q

        if is_raw_sig:
            n_raw_sig += 1
        if is_bh_sig:
            n_bh_sig += 1
        if is_by_sig:
            n_by_sig += 1
        if is_bonf_sig:
            n_bonf_sig += 1

        if is_bonf_sig:
            status = "SURVIVES_BONFERRONI"
            badge = "Vững chắc tuyệt đối (Vượt qua cả Bonferroni)"
        elif is_bh_sig:
            status = "DISCOVERED_BH_FDR"
            badge = "Ý nghĩa thực thụ (Được bảo toàn bởi FDR)"
            n_rescued_by_bh += 1
        elif is_raw_sig and not is_bh_sig:
            status = "FILTERED_FALSE_POSITIVE"
            badge = "Dương tính giả đã lọc (Loại trừ Type I Error)"
            n_false_pos_filtered += 1
        else:
            status = "NON_SIGNIFICANT"
            badge = "Không có ý nghĩa thống kê"

        results_list.append({
            "rank": rank_1b,
            "hypothesis": label,
            "raw_p_value": round(raw_p, 5),
            "bh_q_value": round(q_bh, 5),
            "by_adjusted_p": round(q_by, 5),
            "bonferroni_p": round(p_bonf, 5),
            "bh_critical_value": round(bh_threshold, 5),
            "is_significant_bh": is_bh_sig,
            "is_significant_bonferroni": is_bonf_sig,
            "decision_status": status,
            "decision_badge": badge
        })

    # Generate Dual-Panel SVG Chart
    svg_chart = _generate_fdr_svg(
        sorted_items=sorted_items,
        fdr_q=fdr_q,
        m=m_clean,
        n_raw=n_raw_sig,
        n_bh=n_bh_sig,
        n_by=n_by_sig,
        n_bonf=n_bonf_sig
    )

    # APA 7th Edition Narrative
    apa_narrative = (
        f"Kiểm soát tỷ lệ phát hiện sai (False Discovery Rate - FDR) theo quy chuẩn Benjamini & Hochberg (1995) "
        f"và Benjamini & Yekutieli (2001) được thực hiện trên tổng số m = {m_clean} giả thuyết đồng thời "
        f"tại mức ý nghĩa mục tiêu Q = {fdr_q:.2f}. "
        f"Ước lượng tỷ lệ giả thuyết vô hiệu thực tế đạt pi_0 = {pi_0_est:.3f}. "
        f"Khi chưa hiệu chỉnh, có {n_raw_sig} giả thuyết đạt p < {fdr_q}. "
        f"Sau khi kiểm soát FDR Benjamini-Hochberg, có {n_bh_sig} mối quan hệ được xác nhận là phát hiện có ý nghĩa thống kê thực thụ "
        f"(trong đó {n_rescued_by_bh} phát hiện được cứu khỏi sự bảo thủ quá mức của Bonferroni, "
        f"và {n_false_pos_filtered} giả thuyết dương tính giả do kiểm định lặp đã được sàng lọc loại bỏ thành công). "
        f"Nếu áp dụng chuẩn bảo thủ tối đa Bonferroni (alpha/m = {fdr_q/m_clean:.5f}), chỉ có {n_bonf_sig} giả thuyết được giữ lại."
    )

    return {
        "status": "success",
        "sample_diagnostics": {
            "total_hypotheses_m": m_clean,
            "fdr_target_q": fdr_q,
            "estimated_pi_0_null_proportion": round(pi_0_est, 3),
            "raw_significant_count": n_raw_sig,
            "bh_fdr_significant_count": n_bh_sig,
            "by_fdr_significant_count": n_by_sig,
            "bonferroni_significant_count": n_bonf_sig,
            "rescued_by_bh_count": n_rescued_by_bh,
            "filtered_false_positives_count": n_false_pos_filtered
        },
        "corrections": results_list,
        "svg_chart": svg_chart,
        "apa_narrative": apa_narrative
    }


def run_pairwise_fdr_matrix(
    records: List[Dict[str, Any]],
    question_ids: List[str],
    question_titles: Optional[Dict[str, str]] = None,
    fdr_q: float = 0.05
) -> Dict[str, Any]:
    """
    Computes pairwise Pearson correlation p-values across all pairs of numeric questions,
    then executes multiple testing correction.
    """
    k = len(question_ids)
    if k < 2:
        return {
            "status": "error",
            "message": "Cần tối thiểu 2 câu hỏi định lượng để lập ma trận kiểm định lặp."
        }

    q_titles = question_titles or {qid: qid for qid in question_ids}

    # Extract numeric matrix
    clean_matrix = []
    for r in records:
        row = []
        valid = True
        for qid in question_ids:
            v = r.get(qid)
            if v is None:
                valid = False
                break
            try:
                row.append(float(v))
            except (ValueError, TypeError):
                valid = False
                break
        if valid:
            clean_matrix.append(row)

    n_sample = len(clean_matrix)
    if n_sample < 10:
        return {
            "status": "error",
            "message": f"Số quan sát hoàn chỉnh (N={n_sample}) không đủ để lập ma trận tương quan kiểm định lặp (cần tối thiểu N >= 10)."
        }

    data_arr = np.array(clean_matrix, dtype=float)
    p_values = []
    labels = []

    for i in range(k):
        for j in range(i + 1, k):
            x = data_arr[:, i]
            y = data_arr[:, j]

            sd_x = np.std(x, ddof=1)
            sd_y = np.std(y, ddof=1)
            if sd_x < 1e-9 or sd_y < 1e-9:
                r_val = 0.0
                p_val = 1.0
            else:
                r_val = float(np.corrcoef(x, y)[0, 1])
                # t = r * sqrt(n - 2) / sqrt(1 - r^2)
                r_clamped = max(-0.9999, min(0.9999, r_val))
                dof = n_sample - 2
                t_stat = r_clamped * math.sqrt(dof) / math.sqrt(1.0 - r_clamped ** 2)
                p_val = _t_to_p_two_tailed(t_stat, dof)

            label = f"{q_titles.get(question_ids[i], question_ids[i])[:14]} ⟷ {q_titles.get(question_ids[j], question_ids[j])[:14]}"
            p_values.append(p_val)
            labels.append(label)

    return compute_fdr_corrections(p_values=p_values, labels=labels, fdr_q=fdr_q)


def _generate_fdr_svg(
    sorted_items: List[Any],
    fdr_q: float,
    m: int,
    n_raw: int,
    n_bh: int,
    n_by: int,
    n_bonf: int
) -> str:
    """
    Renders high-definition dual-panel vector SVG:
    Panel A: Benjamini-Hochberg P-Value Rank Plot
    Panel B: Methodological Discovery Comparison Bar Chart
    """
    width = 840
    height = 370

    # Panel A bounds (x: 50 to 470, y: 55 to 295)
    ax0, ax1 = 50, 470
    ay0, ay1 = 55, 295
    a_width = ax1 - ax0
    a_height = ay1 - ay0

    # Panel B bounds (x: 520 to 800, y: 55 to 310)
    bx0, bx1 = 520, 810
    by0, by1 = 55, 295
    b_width = bx1 - bx0
    b_height = by1 - by0

    svg_elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="{height}" class="w-full">',
        f'<rect width="{width}" height="{height}" fill="#090d16" rx="12" stroke="#1e293b" stroke-width="1.5"/>',

        '<text x="20" y="32" fill="#e2e8f0" font-family="system-ui, sans-serif" font-size="14" font-weight="700">PANEL A: Đồ Thị Phân Hạng P-Value & Ngưỡng FDR (Benjamini-Hochberg)</text>',
        f'<text x="{bx0}" y="32" fill="#e2e8f0" font-family="system-ui, sans-serif" font-size="14" font-weight="700">PANEL B: So Sánh Số Lượng Phát Hiện (Discovery Counts)</text>',

        # Panel A Box
        f'<rect x="{ax0}" y="{ay0}" width="{a_width}" height="{a_height}" fill="#0c1322" rx="6" stroke="#1e293b" stroke-width="1"/>',
    ]

    # Panel A: Coordinate scaling
    # x: rank from 1 to m
    # y: p-value from 0.0 to 0.25 (or max p if smaller)
    max_p_display = min(1.0, max(0.15, sorted_items[min(m - 1, int(m * 0.7))][0]))

    def scale_rank(r: int) -> float:
        return ax0 + ((r - 1) / max(1, m - 1)) * a_width

    def scale_p(p_val: float) -> float:
        pv_clamped = min(max_p_display, p_val)
        return ay1 - (pv_clamped / max_p_display) * a_height

    # Y grid lines
    for i in range(5):
        pv = (i / 4.0) * max_p_display
        gy = scale_p(pv)
        svg_elements.append(f'<line x1="{ax0}" y1="{gy:.1f}" x2="{ax1}" y2="{gy:.1f}" stroke="#1e293b" stroke-width="1" stroke-dasharray="2,2"/>')
        svg_elements.append(f'<text x="{ax0-6}" y="{gy+3:.1f}" fill="#64748b" font-family="system-ui, sans-serif" font-size="9" text-anchor="end">{pv:.3f}</text>')

    # Unadjusted alpha = 0.05 horizontal line
    y_raw_alpha = scale_p(fdr_q)
    svg_elements.append(f'<line x1="{ax0}" y1="{y_raw_alpha:.1f}" x2="{ax1}" y2="{y_raw_alpha:.1f}" stroke="#f43f5e" stroke-width="1.5" stroke-dasharray="4,3"/>')
    svg_elements.append(f'<text x="{ax1-5}" y="{y_raw_alpha-4:.1f}" fill="#fda4af" font-family="system-ui, sans-serif" font-size="9" text-anchor="end">α = {fdr_q:.2f} (Thô)</text>')

    # Benjamini-Hochberg critical line: p = (i / m) * Q
    x1_bh = scale_rank(1)
    y1_bh = scale_p((1.0 / m) * fdr_q)
    xm_bh = scale_rank(m)
    ym_bh = scale_p(fdr_q)
    svg_elements.append(f'<line x1="{x1_bh:.1f}" y1="{y1_bh:.1f}" x2="{xm_bh:.1f}" y2="{ym_bh:.1f}" stroke="#6366f1" stroke-width="2"/>')

    # Curve of sorted p-values
    curve_pts = []
    for rank_idx, item in enumerate(sorted_items):
        rx = scale_rank(rank_idx + 1)
        ry = scale_p(item[0])
        curve_pts.append(f"{rx:.1f},{ry:.1f}")

    svg_elements.append(f'<polyline points="{" ".join(curve_pts)}" fill="none" stroke="#38bdf8" stroke-width="2"/>')

    # Cutoff threshold marker if n_bh > 0
    if n_bh > 0:
        cut_x = scale_rank(n_bh)
        cut_y = scale_p(sorted_items[n_bh - 1][0])
        svg_elements.append(f'<line x1="{cut_x:.1f}" y1="{ay0}" x2="{cut_x:.1f}" y2="{ay1}" stroke="#10b981" stroke-width="1.5" stroke-dasharray="3,3"/>')
        svg_elements.append(f'<circle cx="{cut_x:.1f}" cy="{cut_y:.1f}" r="5" fill="#10b981" stroke="#ffffff" stroke-width="1.5"/>')
        svg_elements.append(f'<text x="{cut_x:.1f}" y="{ay0+15}" fill="#6ee7b7" font-family="system-ui, sans-serif" font-size="10" font-weight="700" text-anchor="middle">BH Cutoff (k={n_bh})</text>')

    # Panel A X-axis label
    svg_elements.append(f'<text x="{(ax0+ax1)/2}" y="{ay1+22}" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="10" text-anchor="middle">Thứ hạng Giả thuyết Tăng dần (Rank i = 1 ... {m})</text>')

    # Panel B Bar chart comparing methods
    # Bars: Raw Unadjusted, BH FDR, BY FDR, Bonferroni
    bars = [
        {"name": "P Thô (Chưa lọc)", "count": n_raw, "color": "#f43f5e"},
        {"name": "FDR Benjamini-Hochberg", "count": n_bh, "color": "#6366f1"},
        {"name": "FDR Benjamini-Yekutieli", "count": n_by, "color": "#0ea5e9"},
        {"name": "Bảo thủ Bonferroni", "count": n_bonf, "color": "#10b981"}
    ]

    max_bar_count = max(1, max(b["count"] for b in bars))
    bar_width = b_width - 150

    b_y_curr = by0 + 20
    for b_item in bars:
        bar_len = (b_item["count"] / max_bar_count) * bar_width
        svg_elements.append(f'<text x="{bx0}" y="{b_y_curr+14}" fill="#cbd5e1" font-family="system-ui, sans-serif" font-size="10" font-weight="600">{b_item["name"]}</text>')

        # Background track
        svg_elements.append(f'<rect x="{bx0+130}" y="{b_y_curr}" width="{bar_width}" height="18" fill="#1e293b" rx="4"/>')
        # Value fill
        if bar_len > 0:
            svg_elements.append(f'<rect x="{bx0+130}" y="{b_y_curr}" width="{bar_len:.1f}" height="18" fill="{b_item["color"]}" rx="4"/>')

        # Count label
        svg_elements.append(f'<text x="{bx0+135+bar_len:.1f}" y="{b_y_curr+13}" fill="#ffffff" font-family="system-ui, sans-serif" font-size="10" font-weight="bold">{b_item["count"]}</text>')
        b_y_curr += 48

    # Panel B Footer note
    svg_elements.append(f'<rect x="{bx0}" y="{by1-40}" width="{b_width}" height="42" fill="#0f172a" rx="6" stroke="#1e293b" stroke-width="1"/>')
    svg_elements.append(f'<text x="{bx0+10}" y="{by1-24}" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="9.5">Phát hiện cứu được bởi BH: <tspan fill="#6ee7b7" font-weight="bold">+{max(0, n_bh - n_bonf)}</tspan> so với Bonferroni</text>')
    svg_elements.append(f'<text x="{bx0+10}" y="{by1-8}" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="9.5">Dương tính giả đã lọc: <tspan fill="#fda4af" font-weight="bold">{max(0, n_raw - n_bh)}</tspan> quan hệ nhiễu</text>')

    svg_elements.append('</svg>')
    return "".join(svg_elements)
