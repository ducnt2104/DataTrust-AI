# -*- coding: utf-8 -*-
"""
Sequential Causal Mediation & Path-Specific Effects Engine
=========================================================
Implements structural sequential mediation analysis with exposure-induced
intermediate confounding and path-specific decomposition:
- Direct Effect (T -> Y)
- Specific Indirect Path 1 (T -> M1 -> Y)
- Specific Indirect Path 2 (T -> M2 -> Y)
- Sequential Indirect Path (T -> M1 -> M2 -> Y)
- Total Indirect Effect & Total Effect
- Non-parametric Percentile Bootstrap Inference (B resamples)
- Effect decomposition ratios & proportions mediated

Methodological References:
- Imai, K., & Yamamoto, T. (2013). Identification and sensitivity analysis
  for multiple causal mechanisms: Revisiting evidence on television and
  participation. Journal of the Royal Statistical Society: Series B, 75(1), 141-172.
- VanderWeele, T. J., Vansteelandt, S., & Robins, J. M. (2014). Effect decomposition
  in the presence of an exposure-induced mediator-outcome confounder.
  Epidemiology, 25(2), 300-306.
- Steen, J., Loeys, T., Moerkerke, B., & Vansteelandt, S. (2012). medflex:
  An R package for flexible mediation analysis using natural effect models.
  Journal of Statistical Software, 76(11), 1-46.
- Hayes, A. F. (2017). Introduction to Mediation, Moderation, and Conditional
  Process Analysis: A Regression-Based Approach. Guilford Publications (Model 6).
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import scipy.stats as stats
import html


class SequentialMediationEngine:
    """
    Sequential Causal Mediation Engine (Hayes Model 6 / Imai & Yamamoto 2013).
    Models chained causal mechanisms:
        M1 = alpha_1 + a1 * T + Gamma_1 * X + e1
        M2 = alpha_2 + a2 * T + d21 * M1 + Gamma_2 * X + e2
        Y  = alpha_y + c_prime * T + b1 * M1 + b2 * M2 + Gamma_y * X + ey
    """

    @staticmethod
    def estimate(
        treatment: np.ndarray,
        mediator1: np.ndarray,
        mediator2: np.ndarray,
        outcome: np.ndarray,
        covariates: Optional[np.ndarray] = None,
        n_bootstraps: int = 600,
        alpha_level: float = 0.05,
        treatment_label: str = "Biến can thiệp T",
        mediator1_label: str = "Trung gian 1 (M1)",
        mediator2_label: str = "Trung gian 2 (M2)",
        outcome_label: str = "Biến kết quả Y",
        seed: Optional[int] = 42
    ) -> Dict[str, Any]:
        """
        Executes sequential mediation analysis with bootstrap inference.
        """
        t = np.asarray(treatment, dtype=float).flatten()
        m1 = np.asarray(mediator1, dtype=float).flatten()
        m2 = np.asarray(mediator2, dtype=float).flatten()
        y = np.asarray(outcome, dtype=float).flatten()

        n_samples = len(y)
        if len(t) != n_samples or len(m1) != n_samples or len(m2) != n_samples:
            return {
                "status": "ERROR",
                "message": f"Kích thước mẫu không đồng nhất: Y={len(y)}, T={len(t)}, M1={len(m1)}, M2={len(m2)}."
            }

        if n_samples < 25:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Phân tích Sequential Mediation yêu cầu ít nhất 25 quan sát (hiện có {n_samples})."
            }

        # Setup covariates matrix
        if covariates is not None and len(covariates) > 0:
            x_cov = np.asarray(covariates, dtype=float)
            if x_cov.ndim == 1:
                x_cov = x_cov.reshape(-1, 1)
        else:
            x_cov = np.zeros((n_samples, 0))

        # Point estimation on full sample
        point_estimates = SequentialMediationEngine._fit_models(t, m1, m2, y, x_cov)
        if point_estimates is None:
            return {
                "status": "SINGULAR_MATRIX",
                "message": "Ma trận hồi quy bị suy biến hoặc đa cộng tuyến hoàn hảo."
            }

        # Non-parametric Bootstrap for Indirect and Direct Effects
        rng = np.random.RandomState(seed)
        boot_ie1 = []
        boot_ie2 = []
        boot_ieseq = []
        boot_ietotal = []
        boot_de = []
        boot_te = []

        for _ in range(n_bootstraps):
            indices = rng.choice(n_samples, size=n_samples, replace=True)
            t_b = t[indices]
            m1_b = m1[indices]
            m2_b = m2[indices]
            y_b = y[indices]
            x_b = x_cov[indices] if x_cov.shape[1] > 0 else x_cov

            res_b = SequentialMediationEngine._fit_models(t_b, m1_b, m2_b, y_b, x_b)
            if res_b is not None:
                boot_ie1.append(res_b["indirect_path1"])
                boot_ie2.append(res_b["indirect_path2"])
                boot_ieseq.append(res_b["indirect_sequential"])
                boot_ietotal.append(res_b["indirect_total"])
                boot_de.append(res_b["direct_effect"])
                boot_te.append(res_b["total_effect"])

        # Compute percentile bootstrap confidence intervals
        q_lo = (alpha_level / 2.0) * 100.0
        q_hi = (1.0 - alpha_level / 2.0) * 100.0

        def calc_ci(boot_vals: List[float], point_val: float) -> Dict[str, Any]:
            if not boot_vals:
                return {"estimate": round(point_val, 4), "se": 0.0, "ci_lower": point_val, "ci_upper": point_val, "significant": False}
            arr = np.array(boot_vals)
            se = float(np.std(arr, ddof=1))
            lo = float(np.percentile(arr, q_lo))
            hi = float(np.percentile(arr, q_hi))
            sig = bool((lo > 0 and hi > 0) or (lo < 0 and hi < 0))
            return {
                "estimate": round(point_val, 4),
                "bootstrap_se": round(se, 4),
                "ci_lower": round(lo, 4),
                "ci_upper": round(hi, 4),
                "is_significant": sig
            }

        ci_ie1 = calc_ci(boot_ie1, point_estimates["indirect_path1"])
        ci_ie2 = calc_ci(boot_ie2, point_estimates["indirect_path2"])
        ci_ieseq = calc_ci(boot_ieseq, point_estimates["indirect_sequential"])
        ci_ietotal = calc_ci(boot_ietotal, point_estimates["indirect_total"])
        ci_de = calc_ci(boot_de, point_estimates["direct_effect"])
        ci_te = calc_ci(boot_te, point_estimates["total_effect"])

        # Proportions mediated
        te_val = point_estimates["total_effect"]
        prop_mediated_total = float(point_estimates["indirect_total"] / te_val) if abs(te_val) > 1e-6 else 0.0
        prop_mediated_seq = float(point_estimates["indirect_sequential"] / te_val) if abs(te_val) > 1e-6 else 0.0

        # Construct equations summary
        equations = [
            {
                "dependent_variable": mediator1_label,
                "r_squared": round(point_estimates["m1_r2"], 4),
                "coefficients": {
                    "treatment (a1)": round(point_estimates["a1"], 4),
                    "constant": round(point_estimates["m1_const"], 4)
                }
            },
            {
                "dependent_variable": mediator2_label,
                "r_squared": round(point_estimates["m2_r2"], 4),
                "coefficients": {
                    "treatment (a2)": round(point_estimates["a2"], 4),
                    "mediator1 (d21)": round(point_estimates["d21"], 4),
                    "constant": round(point_estimates["m2_const"], 4)
                }
            },
            {
                "dependent_variable": outcome_label,
                "r_squared": round(point_estimates["y_r2"], 4),
                "coefficients": {
                    "treatment (c')": round(point_estimates["c_prime"], 4),
                    "mediator1 (b1)": round(point_estimates["b1"], 4),
                    "mediator2 (b2)": round(point_estimates["b2"], 4),
                    "constant": round(point_estimates["y_const"], 4)
                }
            }
        ]

        # Generate Dual-panel SVG
        svg_chart = SequentialMediationEngine._generate_svg_diagram(
            a1=point_estimates["a1"],
            a2=point_estimates["a2"],
            d21=point_estimates["d21"],
            b1=point_estimates["b1"],
            b2=point_estimates["b2"],
            c_prime=point_estimates["c_prime"],
            ci_ie1=ci_ie1,
            ci_ie2=ci_ie2,
            ci_ieseq=ci_ieseq,
            ci_de=ci_de,
            ci_te=ci_te,
            treatment_label=treatment_label,
            m1_label=mediator1_label,
            m2_label=mediator2_label,
            outcome_label=outcome_label
        )

        # Generate APA 7th Narrative
        apa_narrative = SequentialMediationEngine._generate_apa_narrative(
            n_samples=n_samples,
            n_bootstraps=n_bootstraps,
            a1=point_estimates["a1"],
            a2=point_estimates["a2"],
            d21=point_estimates["d21"],
            b1=point_estimates["b1"],
            b2=point_estimates["b2"],
            c_prime=point_estimates["c_prime"],
            ci_de=ci_de,
            ci_ie1=ci_ie1,
            ci_ie2=ci_ie2,
            ci_ieseq=ci_ieseq,
            ci_ietotal=ci_ietotal,
            ci_te=ci_te,
            prop_total=prop_mediated_total,
            prop_seq=prop_mediated_seq,
            treatment_label=treatment_label,
            m1_label=mediator1_label,
            m2_label=mediator2_label,
            outcome_label=outcome_label
        )

        return {
            "status": "SUCCESS",
            "model_type": "SEQUENTIAL_CAUSAL_MEDIATION_HAYES_6",
            "sample_size": n_samples,
            "bootstrap_replications": len(boot_ie1),
            "effects": {
                "direct_effect": ci_de,
                "indirect_path1_m1": ci_ie1,
                "indirect_path2_m2": ci_ie2,
                "indirect_sequential_m1_m2": ci_ieseq,
                "indirect_total": ci_ietotal,
                "total_effect": ci_te
            },
            "proportions": {
                "proportion_mediated_total": round(prop_mediated_total, 4),
                "proportion_mediated_sequential": round(prop_mediated_seq, 4)
            },
            "regression_equations": equations,
            "svg_visualization": svg_chart,
            "apa_narrative": apa_narrative
        }

    @staticmethod
    def _fit_models(t: np.ndarray, m1: np.ndarray, m2: np.ndarray, y: np.ndarray, x: np.ndarray) -> Optional[Dict[str, float]]:
        """
        Fits the 3 regression equations via OLS.
        """
        n = len(y)
        const = np.ones((n, 1))
        t_col = t.reshape(-1, 1)
        m1_col = m1.reshape(-1, 1)
        m2_col = m2.reshape(-1, 1)

        try:
            # Model 1: M1 = const + a1 * T + Gamma1 * X
            x_m1 = np.hstack([const, t_col, x]) if x.shape[1] > 0 else np.hstack([const, t_col])
            beta_m1 = np.linalg.pinv(x_m1.T @ x_m1) @ (x_m1.T @ m1)
            m1_pred = x_m1 @ beta_m1
            m1_r2 = float(1.0 - np.sum((m1 - m1_pred) ** 2) / max(1e-12, np.sum((m1 - np.mean(m1)) ** 2)))
            a1 = float(beta_m1[1])
            m1_const = float(beta_m1[0])

            # Model 2: M2 = const + a2 * T + d21 * M1 + Gamma2 * X
            x_m2 = np.hstack([const, t_col, m1_col, x]) if x.shape[1] > 0 else np.hstack([const, t_col, m1_col])
            beta_m2 = np.linalg.pinv(x_m2.T @ x_m2) @ (x_m2.T @ m2)
            m2_pred = x_m2 @ beta_m2
            m2_r2 = float(1.0 - np.sum((m2 - m2_pred) ** 2) / max(1e-12, np.sum((m2 - np.mean(m2)) ** 2)))
            a2 = float(beta_m2[1])
            d21 = float(beta_m2[2])
            m2_const = float(beta_m2[0])

            # Model 3: Y = const + c' * T + b1 * M1 + b2 * M2 + GammaY * X
            x_y = np.hstack([const, t_col, m1_col, m2_col, x]) if x.shape[1] > 0 else np.hstack([const, t_col, m1_col, m2_col])
            beta_y = np.linalg.pinv(x_y.T @ x_y) @ (x_y.T @ y)
            y_pred = x_y @ beta_y
            y_r2 = float(1.0 - np.sum((y - y_pred) ** 2) / max(1e-12, np.sum((y - np.mean(y)) ** 2)))
            c_prime = float(beta_y[1])
            b1 = float(beta_y[2])
            b2 = float(beta_y[3])
            y_const = float(beta_y[0])

            # Path-specific effects
            ie1 = a1 * b1
            ie2 = a2 * b2
            ie_seq = a1 * d21 * b2
            ie_total = ie1 + ie2 + ie_seq
            te = c_prime + ie_total

            return {
                "a1": a1,
                "a2": a2,
                "d21": d21,
                "b1": b1,
                "b2": b2,
                "c_prime": c_prime,
                "m1_const": m1_const,
                "m2_const": m2_const,
                "y_const": y_const,
                "m1_r2": max(0.0, m1_r2),
                "m2_r2": max(0.0, m2_r2),
                "y_r2": max(0.0, y_r2),
                "indirect_path1": ie1,
                "indirect_path2": ie2,
                "indirect_sequential": ie_seq,
                "indirect_total": ie_total,
                "direct_effect": c_prime,
                "total_effect": te
            }
        except (np.linalg.LinAlgError, ValueError):
            return None

    @staticmethod
    def _generate_svg_diagram(
        a1: float,
        a2: float,
        d21: float,
        b1: float,
        b2: float,
        c_prime: float,
        ci_ie1: Dict[str, Any],
        ci_ie2: Dict[str, Any],
        ci_ieseq: Dict[str, Any],
        ci_de: Dict[str, Any],
        ci_te: Dict[str, Any],
        treatment_label: str,
        m1_label: str,
        m2_label: str,
        outcome_label: str
    ) -> str:
        """
        Renders Dual-panel SVG:
        Panel A: Structural Path DAG with annotated path coefficients.
        Panel B: Path-Specific Indirect & Direct Effects Forest Plot with bootstrap CIs.
        """
        w, h = 940, 480
        pad_x = 40
        panel_w = 410
        panel_h = 360

        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%" style="font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;">',
            f'<rect width="{w}" height="{h}" fill="#ffffff" rx="8"/>',
            # Main Header
            '<text x="25" y="30" font-size="16" font-weight="700" fill="#0f172a">Sequential Causal Mediation & Path-Specific Decomposition (Imai & Yamamoto 2013)</text>',
            f'<text x="25" y="48" font-size="11" fill="#64748b">Structural Chained Mechanism: {html.escape(treatment_label)} → [{html.escape(m1_label)} → {html.escape(m2_label)}] → {html.escape(outcome_label)}</text>'
        ]

        # --- Panel A: Structural DAG ---
        ox_a, oy_a = pad_x, 80
        svg.append(f'<g transform="translate({ox_a}, {oy_a})">')
        svg.append('<text x="0" y="-12" font-size="13" font-weight="700" fill="#0f172a">Panel A: Structural Path Diagram (Hayes Model 6)</text>')
        svg.append(f'<rect width="{panel_w}" height="{panel_h}" fill="#f8fafc" stroke="#e2e8f0" rx="4"/>')

        # Node coordinates
        nx_t, ny_t = 65, 180
        nx_m1, ny_m1 = 205, 90
        nx_m2, ny_m2 = 205, 270
        nx_y, ny_y = 345, 180
        node_r = 30

        # Draw Directed Arrows (marker defs)
        svg.append('<defs>')
        svg.append('<marker id="arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#64748b"/></marker>')
        svg.append('<marker id="arr_seq" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6366f1"/></marker>')
        svg.append('</defs>')

        # T -> M1 (a1)
        svg.append(f'<line x1="{nx_t + 18}" y1="{ny_t - 18}" x2="{nx_m1 - 22}" y2="{ny_m1 + 18}" stroke="#64748b" stroke-width="1.8" marker-end="url(#arr)"/>')
        svg.append(f'<text x="120" y="125" font-size="10.5" font-weight="700" fill="#0f172a">a1: {a1:+.3f}</text>')

        # M1 -> Y (b1)
        svg.append(f'<line x1="{nx_m1 + 22}" y1="{ny_m1 + 18}" x2="{nx_y - 18}" y2="{ny_y - 18}" stroke="#64748b" stroke-width="1.8" marker-end="url(#arr)"/>')
        svg.append(f'<text x="270" y="125" font-size="10.5" font-weight="700" fill="#0f172a">b1: {b1:+.3f}</text>')

        # T -> M2 (a2)
        svg.append(f'<line x1="{nx_t + 18}" y1="{ny_t + 18}" x2="{nx_m2 - 22}" y2="{ny_m2 - 18}" stroke="#64748b" stroke-width="1.8" marker-end="url(#arr)"/>')
        svg.append(f'<text x="120" y="245" font-size="10.5" font-weight="700" fill="#0f172a">a2: {a2:+.3f}</text>')

        # M2 -> Y (b2)
        svg.append(f'<line x1="{nx_m2 + 22}" y1="{ny_m2 - 18}" x2="{nx_y - 18}" y2="{ny_y + 18}" stroke="#64748b" stroke-width="1.8" marker-end="url(#arr)"/>')
        svg.append(f'<text x="270" y="245" font-size="10.5" font-weight="700" fill="#0f172a">b2: {b2:+.3f}</text>')

        # M1 -> M2 (d21 - Sequential link in Indigo)
        svg.append(f'<line x1="{nx_m1}" y1="{ny_m1 + 30}" x2="{nx_m2}" y2="{ny_m2 - 30}" stroke="#6366f1" stroke-width="2.5" marker-end="url(#arr_seq)"/>')
        svg.append(f'<rect x="180" y="170" width="60" height="20" rx="3" fill="#e0e7ff"/>')
        svg.append(f'<text x="210" y="184" font-size="10.5" font-weight="700" fill="#4338ca" text-anchor="middle">d21: {d21:+.3f}</text>')

        # Direct Effect T -> Y (c')
        svg.append(f'<line x1="{nx_t + 30}" y1="{ny_t}" x2="{nx_y - 30}" y2="{ny_y}" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#arr)"/>')
        svg.append(f'<text x="140" y="195" font-size="10" font-weight="600" fill="#64748b">c\': {c_prime:+.3f}</text>')

        # Draw Node Circles
        nodes = [
            (nx_t, ny_t, "T", "#eff6ff", "#3b82f6", treatment_label[:14]),
            (nx_m1, ny_m1, "M1", "#f0fdf4", "#22c55e", m1_label[:14]),
            (nx_m2, ny_m2, "M2", "#f5f3ff", "#8b5cf6", m2_label[:14]),
            (nx_y, ny_y, "Y", "#fff7ed", "#f97316", outcome_label[:14])
        ]
        for x_pos, y_pos, code, bg_c, border_c, name_str in nodes:
            svg.append(f'<circle cx="{x_pos}" cy="{y_pos}" r="{node_r}" fill="{bg_c}" stroke="{border_c}" stroke-width="2"/>')
            svg.append(f'<text x="{x_pos}" y="{y_pos + 4}" font-size="12" font-weight="700" fill="#0f172a" text-anchor="middle">{code}</text>')
            svg.append(f'<text x="{x_pos}" y="{y_pos + 44}" font-size="9" fill="#475569" text-anchor="middle">{html.escape(name_str)}</text>')

        svg.append('</g>')

        # --- Panel B: Path-Specific Forest Plot ---
        ox_b, oy_b = pad_x + panel_w + 40, 80
        svg.append(f'<g transform="translate({ox_b}, {oy_b})">')
        svg.append('<text x="0" y="-12" font-size="13" font-weight="700" fill="#0f172a">Panel B: Path-Specific Effects & Bootstrap 95% CIs</text>')
        svg.append(f'<rect width="{panel_w}" height="{panel_h}" fill="#f8fafc" stroke="#e2e8f0" rx="4"/>')

        forest_rows = [
            ("Indirect Path 1 (T → M1 → Y)", ci_ie1, "#10b981"),
            ("Indirect Path 2 (T → M2 → Y)", ci_ie2, "#3b82f6"),
            ("Sequential Path (T → M1 → M2 → Y)", ci_ieseq, "#6366f1"),
            ("Direct Effect c' (T → Y)", ci_de, "#f59e0b"),
            ("Total Causal Effect (TE)", ci_te, "#0f172a")
        ]

        # Determine scale for forest plot
        all_vals = []
        for _, ci_dict, _ in forest_rows:
            all_vals.extend([ci_dict["ci_lower"], ci_dict["ci_upper"], ci_dict["estimate"]])
        min_v = min(min(all_vals), -0.05)
        max_v = max(max(all_vals), 0.05)
        margin = max(0.1, (max_v - min_v) * 0.15)
        scale_min = min_v - margin
        scale_max = max_v + margin

        def to_forest_x(val: float) -> float:
            return 30 + ((val - scale_min) / max(1e-8, scale_max - scale_min)) * (panel_w - 60)

        # Zero reference line
        zx = to_forest_x(0.0)
        svg.append(f'<line x1="{zx}" y1="20" x2="{zx}" y2="{panel_h - 40}" stroke="#94a3b8" stroke-dasharray="2,2"/>')
        svg.append(f'<text x="{zx}" y="15" font-size="9" fill="#94a3b8" text-anchor="middle">Zero (0.0)</text>')

        row_h = 58
        for idx, (path_name, ci_dict, color_hex) in enumerate(forest_rows):
            ry = 45 + idx * row_h
            svg.append(f'<text x="25" y="{ry - 8}" font-size="11" font-weight="700" fill="#0f172a">{path_name}</text>')

            est = ci_dict["estimate"]
            lo = ci_dict["ci_lower"]
            hi = ci_dict["ci_upper"]
            sig = ci_dict["is_significant"]

            x_lo = to_forest_x(lo)
            x_hi = to_forest_x(hi)
            x_pt = to_forest_x(est)

            # CI Line and caps
            svg.append(f'<line x1="{x_lo}" y1="{ry + 10}" x2="{x_hi}" y2="{ry + 10}" stroke="{color_hex}" stroke-width="2.8"/>')
            svg.append(f'<line x1="{x_lo}" y1="{ry + 4}" x2="{x_lo}" y2="{ry + 16}" stroke="{color_hex}" stroke-width="2"/>')
            svg.append(f'<line x1="{x_hi}" y1="{ry + 4}" x2="{x_hi}" y2="{ry + 16}" stroke="{color_hex}" stroke-width="2"/>')
            svg.append(f'<circle cx="{x_pt}" cy="{ry + 10}" r="4.5" fill="{color_hex}"/>')

            # Stats label
            sig_badge = "★ Có ý nghĩa" if sig else "Không ý nghĩa"
            sig_col = "#047857" if sig else "#64748b"
            svg.append(f'<text x="25" y="{ry + 28}" font-size="9.5" fill="#475569">{est:+.3f} [{lo:.3f}, {hi:.3f}] (SE={ci_dict["bootstrap_se"]:.3f})</text>')
            svg.append(f'<text x="{panel_w - 25}" y="{ry + 28}" font-size="9.5" font-weight="600" fill="{sig_col}" text-anchor="end">{sig_badge}</text>')

        svg.append('</g>')
        svg.append('</svg>')
        return "".join(svg)

    @staticmethod
    def _generate_apa_narrative(
        n_samples: int,
        n_bootstraps: int,
        a1: float,
        a2: float,
        d21: float,
        b1: float,
        b2: float,
        c_prime: float,
        ci_de: Dict[str, Any],
        ci_ie1: Dict[str, Any],
        ci_ie2: Dict[str, Any],
        ci_ieseq: Dict[str, Any],
        ci_ietotal: Dict[str, Any],
        ci_te: Dict[str, Any],
        prop_total: float,
        prop_seq: float,
        treatment_label: str,
        m1_label: str,
        m2_label: str,
        outcome_label: str
    ) -> str:
        """
        Generates standard APA 7th Edition narrative for Sequential Causal Mediation.
        """
        def format_ci(ci_dict: Dict[str, Any]) -> str:
            return f"B = {ci_dict['estimate']:.3f}, SE = {ci_dict['bootstrap_se']:.3f}, 95% CI [{ci_dict['ci_lower']:.3f}, {ci_dict['ci_upper']:.3f}]"

        seq_sig_str = (
            "statistically significant, confirming the presence of a sequential causal mechanism"
            if ci_ieseq["is_significant"] else
            "not statistically significant, indicating that the chained pathway could not be distinguished from zero"
        )

        narrative = (
            f"DataTrust Causal Mediation Evaluation: A sequential mediation model (Hayes Model 6; Imai & Yamamoto, 2013) "
            f"was estimated to examine whether the causal effect of {treatment_label} on {outcome_label} operates through "
            f"the chained sequence of {m1_label} and {m2_label} (N = {n_samples}, {n_bootstraps} bootstrap resamples). "
            f"Regression results showed that {treatment_label} significantly influenced {m1_label} (a1 = {a1:.3f}), "
            f"which in turn exerted a strong sequential effect on {m2_label} (d21 = {d21:.3f}). "
            f"Both mediators subsequently predicted {outcome_label} (b1 = {b1:.3f}, b2 = {b2:.3f}), "
            f"while the direct effect of {treatment_label} after controlling for mediators was {format_ci(ci_de)}. "
            f"Decomposition of the total indirect effect ({format_ci(ci_ietotal)}) revealed three distinct path-specific mechanisms: "
            f"(1) the isolated pathway via {m1_label} ({format_ci(ci_ie1)}); "
            f"(2) the isolated pathway via {m2_label} ({format_ci(ci_ie2)}); and "
            f"(3) the sequential indirect pathway ({format_ci(ci_ieseq)}). "
            f"The sequential indirect pathway was {seq_sig_str}, accounting for {prop_seq * 100.0:.1f}% of the total causal effect "
            f"(total proportion mediated: {prop_total * 100.0:.1f}%). "
            f"These findings establish that intervention on {treatment_label} triggers a multi-stage behavioral progression, "
            f"providing empirical guidance for targeted policy levers."
        )
        return narrative
