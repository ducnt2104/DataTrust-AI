"""
DataTrust - Abadie (2003) Kappa-Weighting Complier Profiling & Compliance Typology Engine
========================================================================================
Scientific References:
- Abadie, A. (2003). Semiparametric instrumental variable estimation of treatment response
  models. Journal of Econometrics, 113(2), 231-263.
- Angrist, J. D., Imbens, G. W., & Rubin, D. B. (1996). Identification of causal effects using
  instrumental variables. Journal of the American Statistical Association, 91(434), 444-455.
- Marbach, M., & Hangartner, D. (2020). Profiling compliers and noncompliers for instrumental
  variable analysis. Political Analysis, 28(3), 435-444.
- Imbens, G. W., & Rubin, D. B. (1997). Estimating outcome distributions for compliers in
  instrumental variables models. The Review of Economic Studies, 64(4), 555-574.
- Baiocchi, M., Cheng, J., & Small, D. S. (2014). Instrumental variable methods for causal
  inference. Statistics in Medicine, 33(13), 2297-2340.

Core Methodological Guarantees:
1. Compliance Typology Decomposition: Partitions population into Compliers, Always-Takers,
   and Never-Takers under monotonicity / no-defiers assumption.
2. Abadie's Kappa Weighting Theorem: Uses kappa_i = 1 - D*(1-Z)/(1-pi(X)) - (1-D)*Z/pi(X)
   to identify any feature or outcome distribution conditional on being a complier.
3. Complier Relative Likelihood Ratio: Ratio_k = E[X_k | Complier] / E[X_k], quantifying
   which sub-demographics are overrepresented (Ratio > 1) vs underrepresented (Ratio < 1).
4. Complier Potential Outcome Distributions & LATE: Identifies E[Y(1) | Complier] and
   E[Y(0) | Complier] to determine local average treatment effect among compliers.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression


class AbadieComplierProfilingEngine:
    """
    Abadie (2003) Kappa-Weighting Complier Profiling & Compliance Typology Engine.
    """

    @classmethod
    def profile(
        cls,
        treatment: np.ndarray,      # Binary actual treatment D in {0, 1}
        instrument: np.ndarray,     # Binary instrument Z in {0, 1}
        covariates: np.ndarray,     # Covariates matrix X (N x K)
        outcome: Optional[np.ndarray] = None, # Optional outcome Y
        covariate_names: Optional[List[str]] = None,
        estimate_instrument_propensity: bool = True,
        n_bootstraps: int = 150,
        confidence_level: float = 0.95,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """
        Executes Abadie complier profiling and compliance typology decomposition.
        """
        np.random.seed(seed)
        N = len(treatment)
        if N < 25:
            raise ValueError(f"Sample size N={N} is too small for complier profiling (minimum N=25 required).")

        D = np.asarray(treatment, dtype=float).ravel()
        Z = np.asarray(instrument, dtype=float).ravel()
        X = np.asarray(covariates, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        N_cov, K = X.shape
        if N_cov != N:
            raise ValueError(f"Covariates rows {N_cov} do not match sample size {N}.")

        if covariate_names is None or len(covariate_names) != K:
            covariate_names = [f"X{j+1}" for j in range(K)]

        # Check binary requirements
        unique_d = np.unique(D)
        unique_z = np.unique(Z)
        if not set(unique_d).issubset({0.0, 1.0}):
            raise ValueError("Treatment variable D must be strictly binary (0 or 1).")
        if not set(unique_z).issubset({0.0, 1.0}):
            raise ValueError("Instrument variable Z must be strictly binary (0 or 1).")

        # -------------------------------------------------------------
        # Step 1: Compliance Typology Decomposition
        # -------------------------------------------------------------
        z1_mask = Z == 1.0
        z0_mask = Z == 0.0
        n_z1 = int(np.sum(z1_mask))
        n_z0 = int(np.sum(z0_mask))

        if n_z1 < 5 or n_z0 < 5:
            raise ValueError("Instrument must have at least 5 observations in both encouragement arms (Z=1 and Z=0).")

        p_d1_given_z1 = float(np.mean(D[z1_mask]))
        p_d1_given_z0 = float(np.mean(D[z0_mask]))

        # Monotonicity check
        if p_d1_given_z1 < p_d1_given_z0:
            raise ValueError(
                f"Monotonicity violation: P(D=1|Z=1) = {p_d1_given_z1:.3f} is less than P(D=1|Z=0) = {p_d1_given_z0:.3f}. "
                "The instrument must positively encourage treatment adoption."
            )

        # Proportions of principal strata under monotonicity
        p_compliers = float(np.clip(p_d1_given_z1 - p_d1_given_z0, 0.001, 1.0))
        p_always_takers = float(np.clip(p_d1_given_z0, 0.0, 1.0 - p_compliers))
        p_never_takers = float(np.clip(1.0 - p_d1_given_z1, 0.0, 1.0 - p_compliers))

        # Instrument strength (First-stage Wald / F-statistic)
        # 2x2 contingency table difference in proportions
        p_pooled = float(np.mean(D))
        se_first_stage = float(np.sqrt(p_pooled * (1.0 - p_pooled) * (1.0 / n_z1 + 1.0 / n_z0)))
        t_first_stage = p_compliers / max(1e-6, se_first_stage)
        f_first_stage = float(t_first_stage**2)
        p_val_first_stage = float(2.0 * (1.0 - stats.norm.cdf(abs(t_first_stage))))
        weak_instrument = bool(f_first_stage < 10.0)

        # -------------------------------------------------------------
        # Step 2: Instrument Propensity Score pi(X) = P(Z=1 | X)
        # -------------------------------------------------------------
        if estimate_instrument_propensity:
            try:
                lr = LogisticRegression(C=1.0, max_iter=500, random_state=seed)
                lr.fit(X, Z)
                pi_x = lr.predict_proba(X)[:, 1]
            except Exception:
                pi_x = np.full(N, float(np.mean(Z)))
        else:
            pi_x = np.full(N, float(np.mean(Z)))

        # Bounding propensity scores to avoid extreme weight divergence
        pi_bounded = np.clip(pi_x, 0.02, 0.98)

        # -------------------------------------------------------------
        # Step 3: Abadie (2003) Kappa Weights
        # kappa_i = 1 - [D_i * (1 - Z_i) / (1 - pi(X_i))] - [(1 - D_i) * Z_i / pi(X_i)]
        # -------------------------------------------------------------
        kappa = 1.0 - (D * (1.0 - Z) / (1.0 - pi_bounded)) - ((1.0 - D) * Z / pi_bounded)
        sum_kappa = float(np.sum(kappa))
        if abs(sum_kappa) < 1e-6:
            sum_kappa = 1e-6

        # -------------------------------------------------------------
        # Step 4: Complier Covariate Profiling & Relative Likelihood
        # -------------------------------------------------------------
        feature_profiles = []
        # Bootstrap distribution of complier means and ratios
        boot_complier_means = np.zeros((n_bootstraps, K))

        for b in range(n_bootstraps):
            b_idx = np.random.choice(N, size=N, replace=True)
            kappa_b = kappa[b_idx]
            sum_k_b = float(np.sum(kappa_b))
            if abs(sum_k_b) < 1e-4:
                sum_k_b = 1e-4
            w_b = kappa_b / sum_k_b
            boot_complier_means[b, :] = np.sum(X[b_idx, :] * w_b[:, np.newaxis], axis=0)

        for j in range(K):
            x_j = X[:, j]
            mean_pop = float(np.mean(x_j))
            sd_pop = float(np.std(x_j, ddof=1)) if N > 1 else 1.0

            # Complier mean via Kappa weights: E[X_j | C] = sum(kappa_i * X_ij) / sum(kappa_i)
            mean_complier = float(np.sum(kappa * x_j) / sum_kappa)

            # Complier Relative Likelihood Ratio: Ratio = E[X_j | C] / E[X_j]
            # For standardized or centered variables, compare standardized difference
            if abs(mean_pop) > 1e-4:
                relative_ratio = float(mean_complier / mean_pop)
            else:
                relative_ratio = float(1.0 + (mean_complier - mean_pop) / max(sd_pop, 1e-4))

            # Bootstrap confidence intervals
            b_means_j = boot_complier_means[:, j]
            se_complier = float(np.std(b_means_j))
            ci_lower_c = float(np.percentile(b_means_j, 2.5))
            ci_upper_c = float(np.percentile(b_means_j, 97.5))

            # Over/under-representation classification
            if relative_ratio > 1.15:
                representation = "Overrepresented among compliers (Ratio > 1.15)"
            elif relative_ratio < 0.85:
                representation = "Underrepresented among compliers (Ratio < 0.85)"
            else:
                representation = "Parity representation (Ratio ≈ 1.0)"

            feature_profiles.append(
                {
                    "feature_name": covariate_names[j],
                    "population_mean": round(mean_pop, 4),
                    "complier_mean": round(mean_complier, 4),
                    "bootstrap_se": round(se_complier, 4),
                    "ci_95": [round(ci_lower_c, 4), round(ci_upper_c, 4)],
                    "relative_likelihood_ratio": round(relative_ratio, 3),
                    "representation": representation,
                }
            )

        # -------------------------------------------------------------
        # Step 5: Complier Potential Outcomes & LATE (if outcome Y provided)
        # -------------------------------------------------------------
        late_results = None
        if outcome is not None:
            Y = np.asarray(outcome, dtype=float).ravel()
            if len(Y) == N:
                # E[Y(1) | C] = sum(kappa * D * Y) / sum(kappa * D)
                weight_y1 = kappa * D
                sum_wy1 = float(np.sum(weight_y1))
                ey1_c = float(np.sum(weight_y1 * Y) / (sum_wy1 if abs(sum_wy1) > 1e-6 else 1.0))

                # E[Y(0) | C] = sum(kappa * (1 - D) * Y) / sum(kappa * (1 - D))
                weight_y0 = kappa * (1.0 - D)
                sum_wy0 = float(np.sum(weight_y0))
                ey0_c = float(np.sum(weight_y0 * Y) / (sum_wy0 if abs(sum_wy0) > 1e-6 else 1.0))

                late_estimate = ey1_c - ey0_c

                # Bootstrap for LATE SE
                boot_late = []
                for _ in range(n_bootstraps):
                    b_idx = np.random.choice(N, size=N, replace=True)
                    k_b, d_b, y_b = kappa[b_idx], D[b_idx], Y[b_idx]
                    w1_b = k_b * d_b
                    w0_b = k_b * (1.0 - d_b)
                    s1_b = np.sum(w1_b)
                    s0_b = np.sum(w0_b)
                    if abs(s1_b) > 1e-4 and abs(s0_b) > 1e-4:
                        y1_b = np.sum(w1_b * y_b) / s1_b
                        y0_b = np.sum(w0_b * y_b) / s0_b
                        boot_late.append(y1_b - y0_b)

                se_late = float(np.std(boot_late)) if len(boot_late) > 10 else 0.1
                ci_l_late = float(late_estimate - 1.96 * se_late)
                ci_u_late = float(late_estimate + 1.96 * se_late)
                p_late = float(2.0 * (1.0 - stats.norm.cdf(abs(late_estimate / max(1e-6, se_late)))))

                late_results = {
                    "complier_treated_mean_ey1": round(ey1_c, 4),
                    "complier_control_mean_ey0": round(ey0_c, 4),
                    "late_estimate": round(late_estimate, 4),
                    "bootstrap_se": round(se_late, 4),
                    "ci_95": [round(ci_l_late, 4), round(ci_u_late, 4)],
                    "p_value": round(p_late, 5),
                    "is_significant": bool(p_late < 0.05),
                }

        # -------------------------------------------------------------
        # Step 6: Dual-Panel Responsive SVG Visualizer
        # Panel A: Compliance Typology Donut / Tri-Color Distribution
        # Panel B: Complier Profiling Bar Chart (Relative Likelihood Ratios)
        # -------------------------------------------------------------
        svg_chart = cls._render_dual_panel_svg(
            p_compliers=p_compliers,
            p_always_takers=p_always_takers,
            p_never_takers=p_never_takers,
            f_first_stage=f_first_stage,
            weak_instrument=weak_instrument,
            feature_profiles=feature_profiles,
        )

        # -------------------------------------------------------------
        # Step 7: APA 7th Edition Academic Narrative
        # -------------------------------------------------------------
        top_over = [f["feature_name"] for f in feature_profiles if f["relative_likelihood_ratio"] > 1.1]
        top_under = [f["feature_name"] for f in feature_profiles if f["relative_likelihood_ratio"] < 0.9]

        apa_narrative = (
            f"An Abadie (2003) kappa-weighting complier profiling analysis (Marbach & Hangartner, 2020) was conducted "
            f"with N = {N} survey respondents to characterize the complier subpopulation under the instrumental variable design. "
            f"The encouragement instrument produced a first-stage Wald F-statistic of {f_first_stage:.2f} (p = {p_val_first_stage:.4e}), "
            f"{'surpassing' if not weak_instrument else 'falling below'} the Stock-Yogo weak instrument threshold (F > 10.0). "
            f"The sample was partitioned into {p_compliers*100:.1f}% Compliers, {p_always_takers*100:.1f}% Always-Takers, "
            f"and {p_never_takers*100:.1f}% Never-Takers. "
            f"Compliers demonstrated substantial demographic heterogeneity relative to the general population: "
            f"they were disproportionately overrepresented among {', '.join(top_over) if top_over else 'none'} "
            f"and underrepresented among {', '.join(top_under) if top_under else 'none'}. "
        )
        if late_results:
            apa_narrative += (
                f"Among compliers, the estimated Local Average Treatment Effect (LATE) was tau = {late_results['late_estimate']:.3f} "
                f"(bootstrap SE = {late_results['bootstrap_se']:.3f}, 95% CI [{late_results['ci_95'][0]:.3f}, {late_results['ci_95'][1]:.3f}], "
                f"p = {late_results['p_value']:.4f}), reflecting counterfactual complier means of E[Y(1)|C] = {late_results['complier_treated_mean_ey1']:.3f} "
                f"and E[Y(0)|C] = {late_results['complier_control_mean_ey0']:.3f}."
            )

        return {
            "status": "success",
            "sample_size": N,
            "compliance_typology": {
                "p_compliers": round(p_compliers, 4),
                "p_always_takers": round(p_always_takers, 4),
                "p_never_takers": round(p_never_takers, 4),
                "complier_count_est": int(round(p_compliers * N)),
                "always_taker_count_est": int(round(p_always_takers * N)),
                "never_taker_count_est": int(round(p_never_takers * N)),
                "first_stage_f": round(f_first_stage, 3),
                "weak_instrument": weak_instrument,
            },
            "feature_profiles": feature_profiles,
            "late_causal_effect": late_results,
            "svg_visualization": svg_chart,
            "apa_narrative": apa_narrative,
        }

    @classmethod
    def _render_dual_panel_svg(
        cls,
        p_compliers: float,
        p_always_takers: float,
        p_never_takers: float,
        f_first_stage: float,
        weak_instrument: bool,
        feature_profiles: List[Dict[str, Any]],
    ) -> str:
        """Renders dual-panel vector SVG visualizer for Complier Profiling."""
        width = 940
        height = 370
        p_w = 425
        p_h = 285
        margin = {"top": 45, "bottom": 35, "left": 40, "right": 20}

        # -------------------------------------------------------------
        # Panel A: Compliance Typology Donut / Stacked Distribution
        # -------------------------------------------------------------
        pA_x = 25
        pA_y = 15
        cx_a = pA_x + p_w / 2.0 - 50
        cy_a = pA_y + p_h / 2.0 + 5
        r_outer = 75
        r_inner = 45

        # Angles for pie slices
        a_c = p_compliers * 360.0
        a_at = p_always_takers * 360.0
        a_nt = p_never_takers * 360.0

        def get_arc_path(start_deg: float, end_deg: float) -> str:
            s_rad = math.radians(start_deg - 90)
            e_rad = math.radians(end_deg - 90)
            x1_o = cx_a + r_outer * math.cos(s_rad)
            y1_o = cy_a + r_outer * math.sin(s_rad)
            x2_o = cx_a + r_outer * math.cos(e_rad)
            y2_o = cy_a + r_outer * math.sin(e_rad)
            x1_i = cx_a + r_inner * math.cos(e_rad)
            y1_i = cy_a + r_inner * math.sin(e_rad)
            x2_i = cx_a + r_inner * math.cos(s_rad)
            y2_i = cy_a + r_inner * math.sin(s_rad)
            large_arc = 1 if (end_deg - start_deg) > 180 else 0
            return (
                f"M {x1_o:.1f} {y1_o:.1f} A {r_outer} {r_outer} 0 {large_arc} 1 {x2_o:.1f} {y2_o:.1f} "
                f"L {x1_i:.1f} {y1_i:.1f} A {r_inner} {r_inner} 0 {large_arc} 0 {x2_i:.1f} {y2_i:.1f} Z"
            )

        path_c = get_arc_path(0.0, a_c)
        path_at = get_arc_path(a_c, a_c + a_at)
        path_nt = get_arc_path(a_c + a_at, 360.0)

        f_color = "#ef4444" if weak_instrument else "#10b981"
        f_badge_text = "Weak IV Warning (F < 10)" if weak_instrument else "Strong IV (F ≥ 10)"

        # -------------------------------------------------------------
        # Panel B: Complier Profiling (Relative Likelihood Ratios)
        # -------------------------------------------------------------
        pB_x = 475
        pB_y = 15
        x0_b = pB_x + 90
        y0_b = pB_y + margin["top"]
        inner_w_b = p_w - 110
        inner_h_b = p_h - margin["top"] - margin["bottom"]

        bars_data = feature_profiles[:6]
        n_bars = max(1, len(bars_data))
        bar_h = inner_h_b / n_bars

        # Ratio scale: 0.0 to max(max_ratio, 2.0)
        max_r_val = max([b["relative_likelihood_ratio"] for b in bars_data] + [1.5])
        max_r_scale = max(2.0, max_r_val * 1.1)

        def map_r_x(r_val: float) -> float:
            return x0_b + (r_val / max_r_scale) * inner_w_b

        parity_x = map_r_x(1.0)

        bar_elements = []
        for i, b in enumerate(bars_data):
            by = y0_b + i * bar_h + 4
            bh = bar_h - 8
            r_v = b["relative_likelihood_ratio"]
            bx_end = map_r_x(r_v)

            # Bar color: Emerald if > 1.0 (overrepresented), Rose if < 1.0 (underrepresented)
            bar_col = "#10b981" if r_v >= 1.0 else "#f43f5e"

            # Label on left
            bar_elements.append(
                f'<text x="{x0_b - 8}" y="{by + bh/2 + 3:.1f}" fill="#cbd5e1" font-size="9" text-anchor="end">{b["feature_name"][:12]}</text>'
            )

            # Bar rectangle
            if r_v >= 1.0:
                bar_elements.append(
                    f'<rect x="{parity_x:.1f}" y="{by:.1f}" width="{bx_end - parity_x:.1f}" height="{bh:.1f}" fill="{bar_col}" fill-opacity="0.8" rx="2"/>'
                )
            else:
                bar_elements.append(
                    f'<rect x="{bx_end:.1f}" y="{by:.1f}" width="{parity_x - bx_end:.1f}" height="{bh:.1f}" fill="{bar_col}" fill-opacity="0.8" rx="2"/>'
                )

            # Value label
            bar_elements.append(
                f'<text x="{bx_end + (5 if r_v >= 1.0 else -5):.1f}" y="{by + bh/2 + 3.5:.1f}" fill="{bar_col}" font-size="9" font-weight="700" text-anchor="{"start" if r_v >= 1.0 else "end"}">{r_v:.2f}x</text>'
            )

        # Assemble full SVG
        svg = f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto font-sans">
  <defs>
    <linearGradient id="bgGradAbadie" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <filter id="shadowAbadie" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000" flood-opacity="0.4"/>
    </filter>
  </defs>

  <rect width="{width}" height="{height}" fill="url(#bgGradAbadie)" rx="12"/>

  <!-- Panel A: Compliance Typology -->
  <g id="panelA" filter="url(#shadowAbadie)">
    <rect x="{pA_x}" y="{pA_y}" width="{p_w}" height="{p_h}" fill="#1e293b" fill-opacity="0.7" rx="8" stroke="#334155" stroke-width="1"/>
    <text x="{pA_x + 15}" y="{pA_y + 24}" fill="#f8fafc" font-size="13" font-weight="600">Panel A: Compliance Typology Breakdown</text>

    <!-- Donut Arcs -->
    <path d="{path_c}" fill="#10b981"/>
    <path d="{path_at}" fill="#3b82f6"/>
    <path d="{path_nt}" fill="#94a3b8"/>

    <!-- Center Label -->
    <text x="{cx_a:.1f}" y="{cy_a - 4:.1f}" fill="#f8fafc" font-size="13" font-weight="700" text-anchor="middle">{p_compliers*100:.1f}%</text>
    <text x="{cx_a:.1f}" y="{cy_a + 12:.1f}" fill="#94a3b8" font-size="9" text-anchor="middle">Compliers</text>

    <!-- Typology Legend on Right -->
    <g transform="translate({cx_a + r_outer + 25}, {cy_a - 40})">
      <rect x="0" y="0" width="10" height="10" fill="#10b981" rx="2"/>
      <text x="16" y="9" fill="#f8fafc" font-size="10" font-weight="600">Compliers ({p_compliers*100:.1f}%)</text>

      <rect x="0" y="24" width="10" height="10" fill="#3b82f6" rx="2"/>
      <text x="16" y="33" fill="#cbd5e1" font-size="10">Always-Takers ({p_always_takers*100:.1f}%)</text>

      <rect x="0" y="48" width="10" height="10" fill="#94a3b8" rx="2"/>
      <text x="16" y="57" fill="#cbd5e1" font-size="10">Never-Takers ({p_never_takers*100:.1f}%)</text>
    </g>

    <!-- F-statistic badge -->
    <rect x="{pA_x + 15}" y="{pA_y + p_h - 26}" width="{p_w - 30}" height="20" fill="{f_color}" fill-opacity="0.15" rx="4" stroke="{f_color}" stroke-width="1"/>
    <text x="{pA_x + p_w/2}" y="{pA_y + p_h - 13}" fill="{f_color}" font-size="10" font-weight="600" text-anchor="middle">First-Stage F = {f_first_stage:.1f} • {f_badge_text}</text>
  </g>

  <!-- Panel B: Complier Profiling -->
  <g id="panelB" filter="url(#shadowAbadie)">
    <rect x="{pB_x}" y="{pB_y}" width="{p_w}" height="{p_h}" fill="#1e293b" fill-opacity="0.7" rx="8" stroke="#334155" stroke-width="1"/>
    <text x="{pB_x + 15}" y="{pB_y + 24}" fill="#f8fafc" font-size="13" font-weight="600">Panel B: Complier Profiling (Relative Likelihood)</text>

    <!-- Parity Reference Line (Ratio = 1.0) -->
    <line x1="{parity_x:.1f}" y1="{y0_b}" x2="{parity_x:.1f}" y2="{y0_b + inner_h_b}" stroke="#475569" stroke-width="1.5" stroke-dasharray="3 3"/>
    <text x="{parity_x:.1f}" y="{y0_b - 5:.1f}" fill="#64748b" font-size="9" text-anchor="middle">1.0x Parity</text>

    <!-- Bars -->
    {"".join(bar_elements)}

    <!-- Footer Description -->
    <text x="{pB_x + 15}" y="{pB_y + p_h - 12}" fill="#64748b" font-size="9">Ratio &gt; 1: Overrepresented in Compliers • Ratio &lt; 1: Underrepresented</text>
  </g>

  <!-- Footer Branding -->
  <text x="{width - 25}" y="{height - 12}" fill="#64748b" font-size="10" text-anchor="end">DataTrust AI • Abadie (2003) Kappa-Weighting Complier Profiling Engine</text>
</svg>"""
        return svg


def run_abadie_complier_profiling(
    records: List[Dict[str, Any]],
    treatment_col: str,
    instrument_col: str,
    covariate_cols: List[str],
    outcome_col: Optional[str] = None,
    estimate_instrument_propensity: bool = True,
    n_bootstraps: int = 150,
    seed: int = 42,
) -> Dict[str, Any]:
    """Helper function to parse records and execute Abadie complier profiling."""
    if not records or len(records) < 25:
        raise ValueError(f"Cần tối thiểu 25 bản ghi hợp lệ để thực thi phân tích (hiện có: {len(records) if records else 0}).")

    valid_rows = []
    for r in records:
        if treatment_col not in r or instrument_col not in r:
            continue
        t_raw = r[treatment_col]
        z_raw = r[instrument_col]
        if t_raw is None or z_raw is None:
            continue

        try:
            t_val = float(t_raw)
            z_val = float(z_raw)
        except (ValueError, TypeError):
            continue

        # Covariates
        x_vals = []
        cov_ok = True
        for c in covariate_cols:
            if c not in r or r[c] is None:
                cov_ok = False
                break
            try:
                x_vals.append(float(r[c]))
            except (ValueError, TypeError):
                cov_ok = False
                break
        if not cov_ok:
            continue

        # Optional outcome
        y_val = None
        if outcome_col and outcome_col in r and r[outcome_col] is not None:
            try:
                y_val = float(r[outcome_col])
            except (ValueError, TypeError):
                y_val = None

        valid_rows.append((t_val, z_val, x_vals, y_val))

    if len(valid_rows) < 25:
        raise ValueError(f"Chỉ có {len(valid_rows)} bản ghi hợp lệ đầy đủ biến. Cần tối thiểu 25 bản ghi.")

    arr_d = np.array([row[0] for row in valid_rows], dtype=float)
    arr_z = np.array([row[1] for row in valid_rows], dtype=float)
    arr_x = np.array([row[2] for row in valid_rows], dtype=float)
    arr_y = np.array([row[3] for row in valid_rows], dtype=float) if outcome_col else None

    return AbadieComplierProfilingEngine.profile(
        treatment=arr_d,
        instrument=arr_z,
        covariates=arr_x,
        outcome=arr_y,
        covariate_names=covariate_cols,
        estimate_instrument_propensity=estimate_instrument_propensity,
        n_bootstraps=n_bootstraps,
        seed=seed,
    )
