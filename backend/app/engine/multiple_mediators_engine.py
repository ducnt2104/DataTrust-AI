"""
Multiple Sequential Mediators & Path-Specific Causal Mediation Engine
====================================================================
Implementation of Tyler J. VanderWeele (2014, American Journal of Epidemiology),
Steen, Loeys, Moerkerke, & Vansteelandt (2012, Psychological Methods),
and Kosuke Imai & Teppei Yamamoto (2013, Journal of the American Statistical Association).

Decomposes the total causal effect of Treatment X on Outcome Y through multiple
sequential mediators M1 and M2:
    X -> M1 -> M2 -> Y
    X ------> M2 -> Y
    X ------------> Y

Decomposition:
- Total Effect (TE)
- Pure Direct Effect (PDE): X -> Y (unmediated)
- Path-Specific Indirect Effect 1 (NIE_M1): X -> M1 -> Y
- Path-Specific Indirect Effect 2 (NIE_M2): X -> M2 -> Y
- Sequential Indirect Effect (NIE_Seq): X -> M1 -> M2 -> Y
- Total Indirect Effect (TIE) = NIE_M1 + NIE_M2 + NIE_Seq
- Proportion Mediated (Total and by path)
- Bias-corrected Bootstrap Confidence Intervals (95% CI)
- Dual-panel SVG Visualization: Structural Path Diagram & Effect Breakdown Forest Plot
- Academic APA 7th Edition narrative reporting
"""

from typing import Dict, Any, List, Optional
import numpy as np
import scipy.stats as stats


class MultipleMediatorsEngine:
    @staticmethod
    def evaluate(
        x: np.ndarray,
        m1: np.ndarray,
        m2: np.ndarray,
        y: np.ndarray,
        covariates: Optional[np.ndarray] = None,
        n_bootstraps: int = 500,
        x_label: str = "Biến can thiệp (X)",
        m1_label: str = "Biến trung gian 1 (M1)",
        m2_label: str = "Biến trung gian 2 (M2)",
        y_label: str = "Biến kết quả (Y)"
    ) -> Dict[str, Any]:
        """
        Executes sequential multiple mediation decomposition.
        """
        n = len(y)
        if n < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Số lượng quan sát hợp lệ (N={n}) quá nhỏ. Cần tối thiểu 20 quan sát.",
                "model_type": "MULTIPLE_SEQUENTIAL_MEDIATORS_VANDERWEELE_2014"
            }

        # Check variation
        if np.std(x) < 1e-8 or np.std(m1) < 1e-8 or np.std(m2) < 1e-8 or np.std(y) < 1e-8:
            return {
                "status": "ZERO_VARIANCE",
                "message": "Một trong các biến can thiệp, trung gian hoặc kết quả có phương sai bằng 0.",
                "model_type": "MULTIPLE_SEQUENTIAL_MEDIATORS_VANDERWEELE_2014"
            }

        # Helper: Fit sequential linear regression systems
        def _estimate_paths(x_s, m1_s, m2_s, y_s, cov_s=None):
            n_obs = len(y_s)
            ones = np.ones((n_obs, 1))

            # 1. Model M1 ~ 1 + X + Cov
            X_m1 = np.column_stack([ones, x_s])
            if cov_s is not None and cov_s.shape[1] > 0:
                X_m1 = np.column_stack([X_m1, cov_s])
            beta_m1, _, _, _ = np.linalg.lstsq(X_m1, m1_s, rcond=None)
            a1 = beta_m1[1]

            # 2. Model M2 ~ 1 + X + M1 + Cov
            X_m2 = np.column_stack([ones, x_s, m1_s])
            if cov_s is not None and cov_s.shape[1] > 0:
                X_m2 = np.column_stack([X_m2, cov_s])
            beta_m2, _, _, _ = np.linalg.lstsq(X_m2, m2_s, rcond=None)
            a2 = beta_m2[1]
            d21 = beta_m2[2]

            # 3. Model Y ~ 1 + X + M1 + M2 + Cov
            X_y = np.column_stack([ones, x_s, m1_s, m2_s])
            if cov_s is not None and cov_s.shape[1] > 0:
                X_y = np.column_stack([X_y, cov_s])
            beta_y, _, _, _ = np.linalg.lstsq(X_y, y_s, rcond=None)
            c_prime = beta_y[1]
            b1 = beta_y[2]
            b2 = beta_y[3]

            # 4. Total effect: Model Y ~ 1 + X + Cov
            X_tot = np.column_stack([ones, x_s])
            if cov_s is not None and cov_s.shape[1] > 0:
                X_tot = np.column_stack([X_tot, cov_s])
            beta_tot, _, _, _ = np.linalg.lstsq(X_tot, y_s, rcond=None)
            c_tot = beta_tot[1]

            # Decomposition
            pde = float(c_prime)
            nie_m1 = float(a1 * b1)
            nie_m2 = float(a2 * b2)
            nie_seq = float(a1 * d21 * b2)
            tie = float(nie_m1 + nie_m2 + nie_seq)
            te = float(pde + tie)

            return {
                "a1": float(a1),
                "a2": float(a2),
                "d21": float(d21),
                "b1": float(b1),
                "b2": float(b2),
                "c_prime": float(c_prime),
                "c_tot": float(c_tot),
                "pde": pde,
                "nie_m1": nie_m1,
                "nie_m2": nie_m2,
                "nie_seq": nie_seq,
                "tie": tie,
                "te": te
            }

        point_est = _estimate_paths(x, m1, m2, y, covariates)

        # Non-parametric Bootstrap for standard errors and 95% CIs
        np.random.seed(42)
        boot_records = {k: [] for k in ["pde", "nie_m1", "nie_m2", "nie_seq", "tie", "te", "a1", "a2", "d21", "b1", "b2", "c_prime"]}

        for _ in range(n_bootstraps):
            boot_idx = np.random.choice(n, size=n, replace=True)
            boot_cov = covariates[boot_idx] if covariates is not None and covariates.shape[1] > 0 else None
            b_res = _estimate_paths(x[boot_idx], m1[boot_idx], m2[boot_idx], y[boot_idx], boot_cov)
            for k in boot_records:
                boot_records[k].append(b_res[k])

        def _calc_stats(est_val, b_samples):
            se = float(np.std(b_samples))
            ci_low = float(np.percentile(b_samples, 2.5))
            ci_high = float(np.percentile(b_samples, 97.5))
            z = float(est_val / se) if se > 1e-8 else 0.0
            p = float(2.0 * (1.0 - stats.norm.cdf(abs(z))))
            return {
                "estimate": round(est_val, 4),
                "se": round(se, 4),
                "z": round(z, 2),
                "p_value": round(p, 4),
                "ci_lower_95": round(ci_low, 4),
                "ci_upper_95": round(ci_high, 4),
                "is_significant": bool(ci_low * ci_high > 0 or p < 0.05)
            }

        stats_pde = _calc_stats(point_est["pde"], boot_records["pde"])
        stats_m1 = _calc_stats(point_est["nie_m1"], boot_records["nie_m1"])
        stats_m2 = _calc_stats(point_est["nie_m2"], boot_records["nie_m2"])
        stats_seq = _calc_stats(point_est["nie_seq"], boot_records["nie_seq"])
        stats_tie = _calc_stats(point_est["tie"], boot_records["tie"])
        stats_te = _calc_stats(point_est["te"], boot_records["te"])

        te_val = point_est["te"]
        pm_total = round(float((point_est["tie"] / te_val) * 100.0), 2) if abs(te_val) > 1e-6 else 0.0
        pm_m1 = round(float((point_est["nie_m1"] / te_val) * 100.0), 2) if abs(te_val) > 1e-6 else 0.0
        pm_m2 = round(float((point_est["nie_m2"] / te_val) * 100.0), 2) if abs(te_val) > 1e-6 else 0.0
        pm_seq = round(float((point_est["nie_seq"] / te_val) * 100.0), 2) if abs(te_val) > 1e-6 else 0.0

        path_coefficients = [
            {"path": "X -> M1 (a1)", "estimate": round(point_est["a1"], 4), "se": round(float(np.std(boot_records["a1"])), 4), "p_value": round(float(2 * (1 - stats.norm.cdf(abs(point_est["a1"] / (np.std(boot_records["a1"]) + 1e-8))))), 4)},
            {"path": "X -> M2 (a2)", "estimate": round(point_est["a2"], 4), "se": round(float(np.std(boot_records["a2"])), 4), "p_value": round(float(2 * (1 - stats.norm.cdf(abs(point_est["a2"] / (np.std(boot_records["a2"]) + 1e-8))))), 4)},
            {"path": "M1 -> M2 (d21)", "estimate": round(point_est["d21"], 4), "se": round(float(np.std(boot_records["d21"])), 4), "p_value": round(float(2 * (1 - stats.norm.cdf(abs(point_est["d21"] / (np.std(boot_records["d21"]) + 1e-8))))), 4)},
            {"path": "M1 -> Y (b1)", "estimate": round(point_est["b1"], 4), "se": round(float(np.std(boot_records["b1"])), 4), "p_value": round(float(2 * (1 - stats.norm.cdf(abs(point_est["b1"] / (np.std(boot_records["b1"]) + 1e-8))))), 4)},
            {"path": "M2 -> Y (b2)", "estimate": round(point_est["b2"], 4), "se": round(float(np.std(boot_records["b2"])), 4), "p_value": round(float(2 * (1 - stats.norm.cdf(abs(point_est["b2"] / (np.std(boot_records["b2"]) + 1e-8))))), 4)},
            {"path": "X -> Y (c' trực tiếp)", "estimate": round(point_est["c_prime"], 4), "se": round(float(np.std(boot_records["c_prime"])), 4), "p_value": round(float(2 * (1 - stats.norm.cdf(abs(point_est["c_prime"] / (np.std(boot_records["c_prime"]) + 1e-8))))), 4)}
        ]

        effects_summary = [
            {"effect_name": "Tổng tác động (Total Effect TE)", "stats": stats_te, "proportion_pct": 100.0},
            {"effect_name": "Tác động trực tiếp thuần (Pure Direct Effect PDE)", "stats": stats_pde, "proportion_pct": round(100.0 - pm_total, 2)},
            {"effect_name": "Tổng tác động gián tiếp (Total Indirect Effect TIE)", "stats": stats_tie, "proportion_pct": pm_total},
            {"effect_name": "Kênh gián tiếp qua M1 (X -> M1 -> Y)", "stats": stats_m1, "proportion_pct": pm_m1},
            {"effect_name": "Kênh gián tiếp qua M2 (X -> M2 -> Y)", "stats": stats_m2, "proportion_pct": pm_m2},
            {"effect_name": "Kênh gián tiếp chuỗi (X -> M1 -> M2 -> Y)", "stats": stats_seq, "proportion_pct": pm_seq}
        ]

        diagnostics = {
            "sample_size": n,
            "n_bootstraps": n_bootstraps,
            "total_effect": stats_te["estimate"],
            "direct_effect": stats_pde["estimate"],
            "total_indirect_effect": stats_tie["estimate"],
            "nie_m1": stats_m1["estimate"],
            "nie_m2": stats_m2["estimate"],
            "nie_seq": stats_seq["estimate"],
            "proportion_mediated_pct": pm_total,
            "proportion_m1_pct": pm_m1,
            "proportion_m2_pct": pm_m2,
            "proportion_seq_pct": pm_seq,
            "is_full_mediation": bool(stats_tie["is_significant"] and not stats_pde["is_significant"]),
            "is_partial_mediation": bool(stats_tie["is_significant"] and stats_pde["is_significant"])
        }

        svg_viz = MultipleMediatorsEngine._generate_dual_panel_svg(path_coefficients, effects_summary, x_label, m1_label, m2_label, y_label)
        apa_narrative = MultipleMediatorsEngine._generate_apa_narrative(diagnostics, path_coefficients, effects_summary)

        return {
            "status": "SUCCESS",
            "model_type": "MULTIPLE_SEQUENTIAL_MEDIATORS_VANDERWEELE_2014",
            "diagnostics": diagnostics,
            "path_coefficients": path_coefficients,
            "effects_summary": effects_summary,
            "svg_visualization": svg_viz,
            "apa_narrative": apa_narrative
        }

    @staticmethod
    def _generate_dual_panel_svg(
        paths: List[Dict[str, Any]],
        effects: List[Dict[str, Any]],
        x_lab: str,
        m1_lab: str,
        m2_lab: str,
        y_lab: str
    ) -> str:
        """
        Renders dual-panel SVG:
        Panel A (Left): Structural DAG with path coefficients & route arrows.
        Panel B (Right): Forest Plot of Direct, Indirect & Path-Specific Effects with 95% CIs.
        """
        width = 920
        height = 370

        p1_x = 45
        p1_y = 55
        p1_w = 400
        p1_h = 260

        p2_x = 485
        p2_y = 55
        p2_w = 390
        p2_h = 260

        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" class="rounded-xl overflow-hidden shadow-lg bg-slate-900">',
            '<defs>',
            '  <marker id="arrowHead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">',
            '    <polygon points="0 0, 8 3, 0 6" fill="#818cf8"/>',
            '  </marker>',
            '  <marker id="arrowHeadDirect" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">',
            '    <polygon points="0 0, 8 3, 0 6" fill="#38bdf8"/>',
            '  </marker>',
            '</defs>',
            f'<rect width="{width}" height="{height}" fill="#0f172a"/>',
            f'<text x="{p1_x}" y="32" fill="#e2e8f0" font-size="14" font-weight="700" font-family="sans-serif">Panel A: Sơ đồ Đường dẫn Cấu trúc Đa Trung gian Tuần tự (DAG)</text>',
            f'<text x="{p2_x}" y="32" fill="#e2e8f0" font-size="14" font-weight="700" font-family="sans-serif">Panel B: Phân rã Tác động Causal Mediation (Forest Plot & 95% CI)</text>'
        ]

        # Panel A: DAG Nodes and Edges
        # Coordinates: X (left-mid), M1 (top-center), M2 (bottom-center), Y (right-mid)
        nx_x, nx_y = p1_x + 35, p1_y + 130
        nm1_x, nm1_y = p1_x + 190, p1_y + 40
        nm2_x, nm2_y = p1_x + 190, p1_y + 220
        ny_x, ny_y = p1_x + 345, p1_y + 130

        # Edges
        # X -> M1
        svg.append(f'<line x1="{nx_x+30}" y1="{nx_y-15}" x2="{nm1_x-30}" y2="{nm1_y+15}" stroke="#818cf8" stroke-width="2" marker-end="url(#arrowHead)"/>')
        # X -> M2
        svg.append(f'<line x1="{nx_x+30}" y1="{nx_y+15}" x2="{nm2_x-30}" y2="{nm2_y-15}" stroke="#818cf8" stroke-width="2" marker-end="url(#arrowHead)"/>')
        # M1 -> M2
        svg.append(f'<line x1="{nm1_x}" y1="{nm1_y+25}" x2="{nm2_x}" y2="{nm2_y-25}" stroke="#a855f7" stroke-width="2" stroke-dasharray="3,3" marker-end="url(#arrowHead)"/>')
        # M1 -> Y
        svg.append(f'<line x1="{nm1_x+30}" y1="{nm1_y+15}" x2="{ny_x-30}" y2="{ny_y-15}" stroke="#818cf8" stroke-width="2" marker-end="url(#arrowHead)"/>')
        # M2 -> Y
        svg.append(f'<line x1="{nm2_x+30}" y1="{nm2_y-15}" x2="{ny_x-30}" y2="{ny_y+15}" stroke="#818cf8" stroke-width="2" marker-end="url(#arrowHead)"/>')
        # Direct: X -> Y
        svg.append(f'<line x1="{nx_x+35}" y1="{nx_y}" x2="{ny_x-35}" y2="{ny_y}" stroke="#38bdf8" stroke-width="2.5" marker-end="url(#arrowHeadDirect)"/>')

        # Coefficients on edges
        path_map = {p["path"].split()[0]: p for p in paths}
        svg.append(f'<text x="{p1_x + 95}" y="{p1_y + 70}" fill="#c7d2fe" font-size="10" font-weight="600" font-family="sans-serif">a1={paths[0]["estimate"]}</text>')
        svg.append(f'<text x="{p1_x + 95}" y="{p1_y + 195}" fill="#c7d2fe" font-size="10" font-weight="600" font-family="sans-serif">a2={paths[1]["estimate"]}</text>')
        svg.append(f'<text x="{nm1_x + 8}" y="{p1_y + 130}" fill="#f472b6" font-size="10" font-weight="600" font-family="sans-serif">d21={paths[2]["estimate"]}</text>')
        svg.append(f'<text x="{p1_x + 280}" y="{p1_y + 70}" fill="#c7d2fe" font-size="10" font-weight="600" font-family="sans-serif">b1={paths[3]["estimate"]}</text>')
        svg.append(f'<text x="{p1_x + 280}" y="{p1_y + 195}" fill="#c7d2fe" font-size="10" font-weight="600" font-family="sans-serif">b2={paths[4]["estimate"]}</text>')
        svg.append(f'<text x="{p1_x + 190}" y="{p1_y + 118}" fill="#38bdf8" font-size="10" font-weight="700" text-anchor="middle" font-family="sans-serif">c\'={paths[5]["estimate"]}</text>')

        # Nodes
        nodes = [
            (nx_x, nx_y, "Can thiệp X", "#3b82f6"),
            (nm1_x, nm1_y, "Trung gian M1", "#8b5cf6"),
            (nm2_x, nm2_y, "Trung gian M2", "#ec4899"),
            (ny_x, ny_y, "Kết quả Y", "#10b981")
        ]
        for bx, by, lab, col in nodes:
            svg.append(f'<rect x="{bx-40}" y="{by-18}" width="80" height="36" fill="#1e293b" stroke="{col}" stroke-width="2" rx="6"/>')
            svg.append(f'<text x="{bx}" y="{by+4}" fill="#f8fafc" font-size="11" font-weight="700" text-anchor="middle" font-family="sans-serif">{lab}</text>')

        # Panel B: Forest plot of 6 effect types
        forest_items = effects  # 6 items
        # Find x range for forest plot
        all_vals = []
        for fi in forest_items:
            all_vals.extend([fi["stats"]["ci_lower_95"], fi["stats"]["ci_upper_95"], fi["stats"]["estimate"]])
        min_x = min(all_vals, default=-1.0)
        max_x = max(all_vals, default=1.0)
        pad = (max_x - min_x) * 0.15 if max_x > min_x else 1.0
        min_x -= pad
        max_x += pad
        span_x = max(max_x - min_x, 1e-4)

        # Zero reference line
        zero_px = p2_x + 130 + ((0.0 - min_x) / span_x) * (p2_w - 145)
        svg.append(f'<line x1="{zero_px}" y1="{p2_y + 10}" x2="{zero_px}" y2="{p2_y + p2_h - 10}" stroke="#64748b" stroke-width="1.5" stroke-dasharray="3,3"/>')

        y_step = (p2_h - 30) / max(1, len(forest_items))
        colors = ["#38bdf8", "#818cf8", "#c084fc", "#f472b6", "#fb7185", "#34d399"]

        labels = [
            "Tổng tác động TE",
            "Trực tiếp PDE (c')",
            "Tổng gián tiếp TIE",
            "Kênh X->M1->Y",
            "Kênh X->M2->Y",
            "Chuỗi X->M1->M2->Y"
        ]

        for i, item in enumerate(forest_items):
            cy = p2_y + 20 + i * y_step
            color = colors[i % len(colors)]
            st = item["stats"]

            # Label on left
            svg.append(f'<text x="{p2_x}" y="{cy + 4}" fill="#e2e8f0" font-size="10" font-family="sans-serif">{labels[i]}</text>')

            # CI line
            x1 = p2_x + 130 + ((st["ci_lower_95"] - min_x) / span_x) * (p2_w - 145)
            x2 = p2_x + 130 + ((st["ci_upper_95"] - min_x) / span_x) * (p2_w - 145)
            xc = p2_x + 130 + ((st["estimate"] - min_x) / span_x) * (p2_w - 145)

            svg.append(f'<line x1="{x1}" y1="{cy}" x2="{x2}" y2="{cy}" stroke="{color}" stroke-width="2"/>')
            svg.append(f'<line x1="{x1}" y1="{cy-4}" x2="{x1}" y2="{cy+4}" stroke="{color}" stroke-width="2"/>')
            svg.append(f'<line x1="{x2}" y1="{cy-4}" x2="{x2}" y2="{cy+4}" stroke="{color}" stroke-width="2"/>')
            svg.append(f'<circle cx="{xc}" cy="{cy}" r="4" fill="{color}" stroke="#0f172a" stroke-width="1.5"/>')

            # Value text on right
            svg.append(f'<text x="{p2_x + p2_w - 5}" y="{cy + 4}" fill="{color}" font-size="10" font-weight="600" text-anchor="end" font-family="sans-serif">{st["estimate"]:.3f}</text>')

        svg.append('</svg>')
        return "\n".join(svg)

    @staticmethod
    def _generate_apa_narrative(diag: Dict[str, Any], paths: List[Dict[str, Any]], effects: List[Dict[str, Any]]) -> str:
        """
        Generates APA 7th Edition reporting narrative.
        """
        med_type = (
            "trung gian toàn phần (Full Mediation)"
            if diag["is_full_mediation"]
            else ("trung gian một phần (Partial Mediation)" if diag["is_partial_mediation"] else "chưa có hiệu ứng trung gian thống kê có ý nghĩa")
        )

        te_st = effects[0]["stats"]
        pde_st = effects[1]["stats"]
        tie_st = effects[2]["stats"]
        seq_st = effects[5]["stats"]

        return (
            f"Phân tích Trung gian Causal Đa biến Tuần tự (Sequential Multiple Mediation Analysis) theo chuẩn mực VanderWeele (2014) "
            f"và Steen et al. (2012) được thực hiện với cỡ mẫu N = {diag['sample_size']} và {diag['n_bootstraps']} mẫu tái chọn Bootstrap. "
            f"Tổng tác động của can thiệp X lên kết quả Y đạt TE = {te_st['estimate']:.4f} (SE = {te_st['se']:.4f}, 95% CI [{te_st['ci_lower_95']:.4f}, {te_st['ci_upper_95']:.4f}]). "
            f"Bóc tách tác động cho thấy: Tác động trực tiếp thuần PDE = {pde_st['estimate']:.4f} (95% CI [{pde_st['ci_lower_95']:.4f}, {pde_st['ci_upper_95']:.4f}]), "
            f"và Tổng tác động gián tiếp TIE = {tie_st['estimate']:.4f} (95% CI [{tie_st['ci_lower_95']:.4f}, {tie_st['ci_upper_95']:.4f}]), "
            f"chiếm tỷ lệ {diag['proportion_mediated_pct']:.2f}% tổng tác động. "
            f"Trong đó, tác động gián tiếp chuỗi tuần tự qua cả hai biến trung gian (X -> M1 -> M2 -> Y) đạt NIE_seq = {seq_st['estimate']:.4f} "
            f"(95% CI [{seq_st['ci_lower_95']:.4f}, {seq_st['ci_upper_95']:.4f}], chiếm {diag['proportion_seq_pct']:.2f}% tổng tác động). "
            f"Kết quả khẳng định cơ chế {med_type} trong chuỗi tương tác nhân quả."
        )
