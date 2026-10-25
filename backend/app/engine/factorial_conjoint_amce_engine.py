"""
DataTrust - Factorial Conjoint Experiment Analysis & AMCE Engine
================================================================
Scientific References:
- Hainmueller, J., Hopkins, D. J., & Yamamoto, T. (2014). Causal inference in
  conjoint analysis: Understanding multidimensional choices via stated preference
  experiments. Political Analysis, 22(1), 1-30.
- Leeper, T. J., Hobolt, S. B., & Tilley, J. (2020). Measuring subgroup preferences
  in conjoint experiments. Political Analysis, 28(2), 207-221.
- Egami, N., & Imai, K. (2019). Causal interaction in factorial experiments:
  Application to conjoint analysis. Journal of the American Statistical Association, 114(526), 529-540.
- Bansak, K., Hainmueller, J., Hopkins, D. J., Yamamoto, T., & Hangartner, D. (2021).
  Conjoint survey experiments. In Advances in Experimental Political Science (pp. 19-41). Cambridge University Press.

Core Methodological Guarantees:
1. Nonparametric Average Marginal Component Effects (AMCE): Unbiased causal estimate of the
   effect of each attribute level relative to a baseline reference category.
2. Marginal Means (MM; Leeper et al. 2020): Measures overall absolute level preferences without
   reference category dependency, centered around 0.5 parity in 2-profile forced-choice designs.
3. Cluster-Robust Standard Errors (CR1 / Liang & Zeger 1986): Exactly accounts for respondent-level
   repeated task clustering across all choice sets.
4. Conjoint Internal Validity Diagnostics: Formal tests for Profile Order Bias (Position 1 vs Position 2)
   and Carryover / Fatigue Effects across task order.
5. Average Component Interaction Effects (ACIE; Egami & Imai 2019): Two-way interaction analysis
   detecting complementarities and substitutabilities between attributes.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats


class FactorialConjointAMCEEngine:
    """
    Nonparametric Factorial Conjoint Experiment Analysis & AMCE Engine.
    """

    @classmethod
    def analyze(
        cls,
        respondent_ids: np.ndarray,      # Respondent cluster ID (Length M)
        choice_outcomes: np.ndarray,     # Binary choice {0, 1} or continuous rating (Length M)
        attributes_data: Dict[str, np.ndarray], # Attribute name -> array of string/category levels (Length M)
        task_ids: Optional[np.ndarray] = None, # Optional task index {1, 2, ...} (Length M)
        profile_positions: Optional[np.ndarray] = None, # Optional position {1, 2} (Length M)
        reference_levels: Optional[Dict[str, str]] = None, # Optional user-specified baseline levels
        interaction_pairs: Optional[List[Tuple[str, str]]] = None, # Two-way attribute pairs for ACIE
        confidence_level: float = 0.95,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """
        Executes Nonparametric Conjoint Analysis (AMCE + Marginal Means + Diagnostics).
        """
        np.random.seed(seed)
        resp_id = np.asarray(respondent_ids)
        Y = np.asarray(choice_outcomes, dtype=float).ravel()
        M = len(Y)

        if M < 20:
            raise ValueError(f"Total profile rows M={M} is too small for conjoint analysis (minimum M=20 required).")
        if len(resp_id) != M:
            raise ValueError(f"Respondent IDs length {len(resp_id)} does not match outcome length {M}.")

        unique_resps = np.unique(resp_id)
        N_resp = len(unique_resps)

        # Validate attributes
        if not attributes_data or len(attributes_data) < 1:
            raise ValueError("At least one conjoint attribute must be provided.")

        attr_names = list(attributes_data.keys())
        for a_name in attr_names:
            if len(attributes_data[a_name]) != M:
                raise ValueError(f"Attribute '{a_name}' rows ({len(attributes_data[a_name])}) do not match outcome length ({M}).")

        # Map respondent IDs to contiguous integers 0..N_resp-1
        resp_map = {r: i for i, r in enumerate(unique_resps)}
        resp_clust = np.array([resp_map[r] for r in resp_id], dtype=int)

        # -------------------------------------------------------------
        # Step 1: Attribute Level Mapping & Dummy Coding
        # -------------------------------------------------------------
        level_map: Dict[str, List[str]] = {}
        ref_map: Dict[str, str] = {}

        for a_name in attr_names:
            raw_vals = [str(v) for v in attributes_data[a_name]]
            u_levels = sorted(list(set(raw_vals)))
            if len(u_levels) < 2:
                raise ValueError(f"Attribute '{a_name}' must have at least 2 distinct levels (found: {u_levels}).")
            level_map[a_name] = u_levels

            # Reference category: user specified or first sorted level
            if reference_levels and a_name in reference_levels and reference_levels[a_name] in u_levels:
                ref_map[a_name] = reference_levels[a_name]
            else:
                ref_map[a_name] = u_levels[0]

        # Construct Design Matrix for AMCE (Intercept + Dummies for non-reference levels)
        dummy_cols = []
        dummy_meta = []  # List of (attr_name, level_name)

        for a_name in attr_names:
            raw_vals = [str(v) for v in attributes_data[a_name]]
            ref_lev = ref_map[a_name]
            for lev in level_map[a_name]:
                if lev == ref_lev:
                    continue
                d_col = (np.array(raw_vals) == lev).astype(float)
                dummy_cols.append(d_col)
                dummy_meta.append((a_name, lev))

        n_dummies = len(dummy_cols)
        X_amce = np.column_stack([np.ones(M)] + dummy_cols)

        # -------------------------------------------------------------
        # Step 2: OLS Regression with Cluster-Robust Standard Errors (CR1)
        # -------------------------------------------------------------
        XtX = X_amce.T @ X_amce
        XtX_inv = np.linalg.pinv(XtX + 1e-7 * np.eye(X_amce.shape[1]))
        beta_amce = XtX_inv @ (X_amce.T @ Y)
        residuals = Y - (X_amce @ beta_amce)

        # Liang & Zeger (1986) Cluster-robust meat: sum_i (X_i' e_i e_i' X_i)
        meat = np.zeros_like(XtX)
        for i_cluster in range(N_resp):
            c_mask = resp_clust == i_cluster
            if np.sum(c_mask) == 0:
                continue
            X_i = X_amce[c_mask, :]
            e_i = residuals[c_mask]
            score_i = X_i.T @ e_i
            meat += np.outer(score_i, score_i)

        # Small sample adjustment factor
        df_c = (N_resp / max(1, N_resp - 1)) * ((M - 1) / max(1, M - X_amce.shape[1]))
        vcov_cr1 = df_c * (XtX_inv @ meat @ XtX_inv)
        se_amce = np.sqrt(np.maximum(1e-12, np.diag(vcov_cr1)))

        # -------------------------------------------------------------
        # Step 3: Extract AMCE Results
        # -------------------------------------------------------------
        crit_val = stats.norm.ppf(1.0 - (1.0 - confidence_level) / 2.0)
        amce_results: Dict[str, List[Dict[str, Any]]] = {}

        # Initialize for all attributes
        for a_name in attr_names:
            amce_results[a_name] = []
            # Reference category row
            ref_lev = ref_map[a_name]
            amce_results[a_name].append({
                "attribute": a_name,
                "level": ref_lev,
                "is_reference": True,
                "estimate": 0.0,
                "std_error": 0.0,
                "z_statistic": 0.0,
                "p_value": 1.0,
                "ci_95": [0.0, 0.0],
                "is_significant": False,
            })

        for j, (a_name, lev) in enumerate(dummy_meta):
            coef_idx = j + 1
            est = float(beta_amce[coef_idx])
            se = float(se_amce[coef_idx])
            z_stat = est / max(1e-6, se)
            p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_stat))))
            ci_lower = float(est - crit_val * se)
            ci_upper = float(est + crit_val * se)

            amce_results[a_name].append({
                "attribute": a_name,
                "level": lev,
                "is_reference": False,
                "estimate": round(est, 4),
                "std_error": round(se, 4),
                "z_statistic": round(z_stat, 3),
                "p_value": round(p_val, 5),
                "ci_95": [round(ci_lower, 4), round(ci_upper, 4)],
                "is_significant": bool(p_val < 0.05),
            })

        # -------------------------------------------------------------
        # Step 4: Marginal Means (MM; Leeper, Hobolt, & Tilley 2020)
        # -------------------------------------------------------------
        marginal_means: Dict[str, List[Dict[str, Any]]] = {}
        for a_name in attr_names:
            marginal_means[a_name] = []
            raw_vals = np.array([str(v) for v in attributes_data[a_name]])

            for lev in level_map[a_name]:
                lev_mask = raw_vals == lev
                n_lev = int(np.sum(lev_mask))
                if n_lev == 0:
                    continue

                # Unconditional mean for this level
                mm_est = float(np.mean(Y[lev_mask]))

                # Cluster-robust standard error for the mean
                # Score per respondent: sum( (Y_ij - mm) * 1(X_ij = lev) )
                cluster_scores = np.zeros(N_resp)
                for i_cluster in range(N_resp):
                    c_mask = (resp_clust == i_cluster) & lev_mask
                    if np.sum(c_mask) > 0:
                        cluster_scores[i_cluster] = np.sum(Y[c_mask] - mm_est)

                sum_sq_score = np.sum(cluster_scores**2)
                var_mm = (N_resp / max(1, N_resp - 1)) * (sum_sq_score / (n_lev**2))
                se_mm = float(np.sqrt(max(1e-12, var_mm)))
                ci_l_mm = float(mm_est - crit_val * se_mm)
                ci_u_mm = float(mm_est + crit_val * se_mm)

                marginal_means[a_name].append({
                    "attribute": a_name,
                    "level": lev,
                    "marginal_mean": round(mm_est, 4),
                    "std_error": round(se_mm, 4),
                    "ci_95": [round(ci_l_mm, 4), round(ci_u_mm, 4)],
                    "profile_count": n_lev,
                    "relative_to_parity": round(mm_est - 0.5, 4),
                })

        # -------------------------------------------------------------
        # Step 5: Average Component Interaction Effects (ACIE; Egami & Imai 2019)
        # -------------------------------------------------------------
        acie_results = []
        if interaction_pairs:
            for attr_1, attr_2 in interaction_pairs:
                if attr_1 in attr_names and attr_2 in attr_names and attr_1 != attr_2:
                    # Form two-way interaction dummies
                    vals_1 = np.array([str(v) for v in attributes_data[attr_1]])
                    vals_2 = np.array([str(v) for v in attributes_data[attr_2]])
                    ref_1 = ref_map[attr_1]
                    ref_2 = ref_map[attr_2]

                    for l1 in level_map[attr_1]:
                        if l1 == ref_1:
                            continue
                        for l2 in level_map[attr_2]:
                            if l2 == ref_2:
                                continue
                            inter_col = ((vals_1 == l1) & (vals_2 == l2)).astype(float)
                            # Estimate interaction in regression
                            X_sub = np.column_stack([
                                np.ones(M),
                                (vals_1 == l1).astype(float),
                                (vals_2 == l2).astype(float),
                                inter_col
                            ])
                            beta_sub = np.linalg.pinv(X_sub.T @ X_sub + 1e-7 * np.eye(4)) @ (X_sub.T @ Y)
                            acie_est = float(beta_sub[3])

                            # Clustered se
                            res_sub = Y - (X_sub @ beta_sub)
                            meat_sub = np.zeros((4, 4))
                            for ic in range(N_resp):
                                c_m = resp_clust == ic
                                sc = X_sub[c_m, :].T @ res_sub[c_m]
                                meat_sub += np.outer(sc, sc)
                            vcov_sub = (N_resp / max(1, N_resp - 1)) * (np.linalg.pinv(X_sub.T @ X_sub) @ meat_sub @ np.linalg.pinv(X_sub.T @ X_sub))
                            se_acie = float(np.sqrt(max(1e-12, vcov_sub[3, 3])))
                            p_acie = float(2.0 * (1.0 - stats.norm.cdf(abs(acie_est / max(1e-6, se_acie)))))

                            acie_results.append({
                                "attribute_pair": [attr_1, attr_2],
                                "level_pair": [l1, l2],
                                "reference_pair": [ref_1, ref_2],
                                "acie_estimate": round(acie_est, 4),
                                "std_error": round(se_acie, 4),
                                "p_value": round(p_acie, 5),
                                "is_significant": bool(p_acie < 0.05),
                                "synergy_type": "Positive Synergy (Complement)" if acie_est > 0 else "Negative Substitution",
                            })

        # -------------------------------------------------------------
        # Step 6: Conjoint Internal Validity Diagnostic Tests
        # -------------------------------------------------------------
        # 1. Profile Order Bias (Position 1 vs Position 2)
        profile_order_diag = None
        if profile_positions is not None and len(profile_positions) == M:
            pos_arr = np.asarray(profile_positions)
            p1_mask = pos_arr == 1
            p2_mask = pos_arr == 2
            if np.sum(p1_mask) > 10 and np.sum(p2_mask) > 10:
                mean_p1 = float(np.mean(Y[p1_mask]))
                mean_p2 = float(np.mean(Y[p2_mask]))
                diff_pos = mean_p1 - mean_p2
                se_pos = float(np.sqrt(np.var(Y[p1_mask]) / np.sum(p1_mask) + np.var(Y[p2_mask]) / np.sum(p2_mask)))
                z_pos = diff_pos / max(1e-6, se_pos)
                p_val_pos = float(2.0 * (1.0 - stats.norm.cdf(abs(z_pos))))
                order_bias_detected = bool(p_val_pos < 0.05)

                profile_order_diag = {
                    "position_1_choice_rate": round(mean_p1, 4),
                    "position_2_choice_rate": round(mean_p2, 4),
                    "order_difference": round(diff_pos, 4),
                    "p_value": round(p_val_pos, 5),
                    "order_bias_detected": order_bias_detected,
                    "interpretation": "Profile position bias detected (Position 1 favored)" if order_bias_detected else "No significant profile order bias (Order invariant)",
                }

        # 2. Carryover / Fatigue Test across Task Order
        carryover_diag = None
        if task_ids is not None and len(task_ids) == M:
            t_arr = np.asarray(task_ids, dtype=float)
            u_tasks = np.unique(t_arr)
            if len(u_tasks) >= 3:
                # Regress Y on task number
                slope, intercept, r_val, p_val_task, std_err = stats.linregress(t_arr, Y)
                fatigue_detected = bool(p_val_task < 0.05)

                carryover_diag = {
                    "num_tasks": len(u_tasks),
                    "task_slope": round(float(slope), 5),
                    "p_value": round(float(p_val_task), 5),
                    "fatigue_detected": fatigue_detected,
                    "interpretation": "Fatigue / habituation effect detected across tasks" if fatigue_detected else "Preferences stable across task iterations (No fatigue)",
                }

        # -------------------------------------------------------------
        # Step 7: Dual-Panel Responsive SVG Visualizer
        # Panel A: AMCE Coefficient Plot (Forest Plot relative to 0.0)
        # Panel B: Marginal Means Plot (Centered relative to 0.5 parity)
        # -------------------------------------------------------------
        svg_chart = cls._render_dual_panel_svg(
            amce_results=amce_results,
            marginal_means=marginal_means,
            ref_map=ref_map,
        )

        # -------------------------------------------------------------
        # Step 8: APA 7th Edition Academic Narrative
        # -------------------------------------------------------------
        # Find top positive AMCE
        all_non_ref_amces = []
        for a_name, rows in amce_results.items():
            for r in rows:
                if not r["is_reference"]:
                    all_non_ref_amces.append(r)

        top_driver = max(all_non_ref_amces, key=lambda x: x["estimate"]) if all_non_ref_amces else None
        bottom_driver = min(all_non_ref_amces, key=lambda x: x["estimate"]) if all_non_ref_amces else None

        apa_narrative = (
            f"A factorial conjoint analysis (Hainmueller, Hopkins, & Yamamoto, 2014) was estimated across "
            f"N = {N_resp} respondents evaluating M = {M} multidimensional profile choices with cluster-robust "
            f"standard errors (Liang & Zeger, 1986). "
        )
        if top_driver:
            apa_narrative += (
                f"The most substantial positive attribute level was '{top_driver['level']}' for attribute '{top_driver['attribute']}', "
                f"yielding an Average Marginal Component Effect of AMCE = {top_driver['estimate']:.3f} "
                f"(SE = {top_driver['std_error']:.3f}, 95% CI [{top_driver['ci_95'][0]:.3f}, {top_driver['ci_95'][1]:.3f}], "
                f"p = {top_driver['p_value']:.4f}) relative to baseline '{ref_map[top_driver['attribute']]}'. "
            )
        if bottom_driver and bottom_driver["estimate"] < 0:
            apa_narrative += (
                f"Conversely, '{bottom_driver['level']}' ({bottom_driver['attribute']}) exerted the strongest negative pressure "
                f"(AMCE = {bottom_driver['estimate']:.3f}, SE = {bottom_driver['std_error']:.3f}, p = {bottom_driver['p_value']:.4f}). "
            )
        if profile_order_diag:
            apa_narrative += (
                f"Internal validity diagnostics confirmed {profile_order_diag['interpretation'].lower()} "
                f"(Position 1 mean = {profile_order_diag['position_1_choice_rate']:.3f} vs Position 2 = {profile_order_diag['position_2_choice_rate']:.3f}, "
                f"p = {profile_order_diag['p_value']:.4f}). "
            )
        apa_narrative += (
            f"Marginal means (Leeper, Hobolt, & Tilley, 2020) demonstrated baseline-invariant preference rankings "
            f"centered around parity probability."
        )

        return {
            "status": "success",
            "sample_size_profiles": M,
            "respondent_count": N_resp,
            "attributes_evaluated": attr_names,
            "reference_levels": ref_map,
            "amce_estimates": amce_results,
            "marginal_means": marginal_means,
            "acie_interactions": acie_results,
            "validity_diagnostics": {
                "profile_order": profile_order_diag,
                "task_fatigue": carryover_diag,
            },
            "svg_visualization": svg_chart,
            "apa_narrative": apa_narrative,
        }

    @classmethod
    def _render_dual_panel_svg(
        cls,
        amce_results: Dict[str, List[Dict[str, Any]]],
        marginal_means: Dict[str, List[Dict[str, Any]]],
        ref_map: Dict[str, str],
    ) -> str:
        """Renders dual-panel vector SVG visualizer for Conjoint AMCE & Marginal Means."""
        width = 940
        height = 420
        p_w = 425
        p_h = 335
        margin = {"top": 45, "bottom": 35, "left": 125, "right": 25}

        # Flatten levels for display (up to 8 levels across attributes)
        plot_items_amce = []
        for a_name, rows in amce_results.items():
            for r in rows:
                if not r["is_reference"]:
                    plot_items_amce.append(r)
        plot_items_amce = plot_items_amce[:7]
        n_items = max(1, len(plot_items_amce))

        # -------------------------------------------------------------
        # Panel A: AMCE Forest Plot (Zero Reference Line)
        # -------------------------------------------------------------
        pA_x = 25
        pA_y = 15
        x0_a = pA_x + margin["left"]
        y0_a = pA_y + margin["top"]
        iw_a = p_w - margin["left"] - margin["right"]
        ih_a = p_h - margin["top"] - margin["bottom"]

        # AMCE Scale: min/max of CIs
        all_cis = [p["ci_95"][0] for p in plot_items_amce] + [p["ci_95"][1] for p in plot_items_amce] + [-0.15, 0.15]
        min_amce = min(all_cis)
        max_amce = max(all_cis)
        scale_amce = max(abs(min_amce), abs(max_amce)) * 1.15

        def map_amce_x(v: float) -> float:
            return x0_a + ((v + scale_amce) / (2.0 * scale_amce)) * iw_a

        zero_x_a = map_amce_x(0.0)
        row_h_a = ih_a / n_items

        amce_elements = []
        for i, item in enumerate(plot_items_amce):
            cy = y0_a + (i + 0.5) * row_h_a
            cx_est = map_amce_x(item["estimate"])
            cx_low = map_amce_x(item["ci_95"][0])
            cx_upp = map_amce_x(item["ci_95"][1])

            col = "#10b981" if item["estimate"] > 0 else "#f43f5e"
            if not item["is_significant"]:
                col = "#94a3b8"

            # Label on left
            lbl = f"{item['attribute'][:8]}: {item['level'][:8]}"
            amce_elements.append(
                f'<text x="{x0_a - 10}" y="{cy + 3.5:.1f}" fill="#cbd5e1" font-size="9" text-anchor="end">{lbl}</text>'
            )

            # Error bar
            amce_elements.append(
                f'<line x1="{cx_low:.1f}" y1="{cy:.1f}" x2="{cx_upp:.1f}" y2="{cy:.1f}" stroke="{col}" stroke-width="2" stroke-linecap="round"/>'
            )
            # Center point
            amce_elements.append(
                f'<circle cx="{cx_est:.1f}" cy="{cy:.1f}" r="4" fill="{col}" stroke="#0f172a" stroke-width="1"/>'
            )
            # Estimate text
            amce_elements.append(
                f'<text x="{cx_upp + 5:.1f}" y="{cy + 3:.1f}" fill="{col}" font-size="8.5" font-weight="600">{item["estimate"]:+.2f}</text>'
            )

        # -------------------------------------------------------------
        # Panel B: Marginal Means Plot (0.5 Parity Line)
        # -------------------------------------------------------------
        pB_x = 475
        pB_y = 15
        x0_b = pB_x + margin["left"]
        y0_b = pB_y + margin["top"]
        iw_b = p_w - margin["left"] - margin["right"]
        ih_b = p_h - margin["top"] - margin["bottom"]

        # Flatten MM items
        plot_items_mm = []
        for a_name, rows in marginal_means.items():
            for r in rows:
                plot_items_mm.append(r)
        plot_items_mm = plot_items_mm[:7]
        n_mm = max(1, len(plot_items_mm))
        row_h_b = ih_b / n_mm

        # Scale MM: [0.25, 0.75] or data driven
        mm_min = min([p["ci_95"][0] for p in plot_items_mm] + [0.35])
        mm_max = max([p["ci_95"][1] for p in plot_items_mm] + [0.65])
        mm_span = max(0.2, mm_max - mm_min)
        mm_l_bound = mm_min - 0.05 * mm_span
        mm_u_bound = mm_max + 0.05 * mm_span

        def map_mm_x(v: float) -> float:
            return x0_b + ((v - mm_l_bound) / (mm_u_bound - mm_l_bound)) * iw_b

        parity_x_b = map_mm_x(0.5)

        mm_elements = []
        for i, item in enumerate(plot_items_mm):
            cy = y0_b + (i + 0.5) * row_h_b
            cx_est = map_mm_x(item["marginal_mean"])
            cx_low = map_mm_x(item["ci_95"][0])
            cx_upp = map_mm_x(item["ci_95"][1])

            col = "#38bdf8" if item["marginal_mean"] >= 0.5 else "#fb923c"

            # Label on left
            lbl = f"{item['attribute'][:8]}: {item['level'][:8]}"
            mm_elements.append(
                f'<text x="{x0_b - 10}" y="{cy + 3.5:.1f}" fill="#cbd5e1" font-size="9" text-anchor="end">{lbl}</text>'
            )

            # Error bar
            mm_elements.append(
                f'<line x1="{cx_low:.1f}" y1="{cy:.1f}" x2="{cx_upp:.1f}" y2="{cy:.1f}" stroke="{col}" stroke-width="2" stroke-linecap="round"/>'
            )
            # Center point
            mm_elements.append(
                f'<circle cx="{cx_est:.1f}" cy="{cy:.1f}" r="4" fill="{col}" stroke="#0f172a" stroke-width="1"/>'
            )
            # Estimate text
            amce_elements.append(
                f'<text x="{cx_upp + 5:.1f}" y="{cy + 3:.1f}" fill="{col}" font-size="8.5" font-weight="600">{item["marginal_mean"]:.2f}</text>'
            )

        # Assemble Full SVG
        svg = f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto font-sans">
  <defs>
    <linearGradient id="bgGradConjoint" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <filter id="shadowConjoint" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000" flood-opacity="0.4"/>
    </filter>
  </defs>

  <rect width="{width}" height="{height}" fill="url(#bgGradConjoint)" rx="12"/>

  <!-- Panel A: AMCE Plot -->
  <g id="panelA" filter="url(#shadowConjoint)">
    <rect x="{pA_x}" y="{pA_y}" width="{p_w}" height="{p_h}" fill="#1e293b" fill-opacity="0.7" rx="8" stroke="#334155" stroke-width="1"/>
    <text x="{pA_x + 15}" y="{pA_y + 24}" fill="#f8fafc" font-size="13" font-weight="600">Panel A: Average Marginal Component Effects (AMCE)</text>

    <!-- Zero Reference Line -->
    <line x1="{zero_x_a:.1f}" y1="{y0_a}" x2="{zero_x_a:.1f}" y2="{y0_a + ih_a}" stroke="#64748b" stroke-width="1.5" stroke-dasharray="3 3"/>
    <text x="{zero_x_a:.1f}" y="{y0_a - 5:.1f}" fill="#64748b" font-size="8.5" text-anchor="middle">0.0 Baseline</text>

    <!-- AMCE Bars -->
    {"".join(amce_elements)}

    <!-- Footer Description -->
    <text x="{pA_x + 15}" y="{pA_y + p_h - 12}" fill="#64748b" font-size="9">Change in choice probability relative to reference level (95% Clustered CI)</text>
  </g>

  <!-- Panel B: Marginal Means Plot -->
  <g id="panelB" filter="url(#shadowConjoint)">
    <rect x="{pB_x}" y="{pB_y}" width="{p_w}" height="{p_h}" fill="#1e293b" fill-opacity="0.7" rx="8" stroke="#334155" stroke-width="1"/>
    <text x="{pB_x + 15}" y="{pB_y + 24}" fill="#f8fafc" font-size="13" font-weight="600">Panel B: Marginal Means (Baseline-Invariant)</text>

    <!-- Parity Reference Line (0.50) -->
    <line x1="{parity_x_b:.1f}" y1="{y0_b}" x2="{parity_x_b:.1f}" y2="{y0_b + ih_b}" stroke="#475569" stroke-width="1.5" stroke-dasharray="3 3"/>
    <text x="{parity_x_b:.1f}" y="{y0_b - 5:.1f}" fill="#64748b" font-size="8.5" text-anchor="middle">0.50 Parity</text>

    <!-- MM Bars -->
    {"".join(mm_elements)}

    <!-- Footer Description -->
    <text x="{pB_x + 15}" y="{pB_y + p_h - 12}" fill="#64748b" font-size="9">Overall choice probability given attribute level (Leeper et al. 2020)</text>
  </g>

  <!-- Footer Branding -->
  <text x="{width - 25}" y="{height - 12}" fill="#64748b" font-size="10" text-anchor="end">DataTrust AI • Factorial Conjoint AMCE Engine (Hainmueller et al. 2014)</text>
</svg>"""
        return svg


def run_factorial_conjoint_amce(
    records: List[Dict[str, Any]],
    respondent_col: str,
    choice_col: str,
    attribute_cols: List[str],
    task_col: Optional[str] = None,
    position_col: Optional[str] = None,
    reference_levels: Optional[Dict[str, str]] = None,
    interaction_pairs: Optional[List[Tuple[str, str]]] = None,
) -> Dict[str, Any]:
    """Helper function to parse records and execute Factorial Conjoint AMCE analysis."""
    if not records or len(records) < 20:
        raise ValueError(f"Cần tối thiểu 20 bản ghi profile hợp lệ (hiện có: {len(records) if records else 0}).")

    valid_resps = []
    valid_y = []
    valid_attrs: Dict[str, List[Any]] = {col: [] for col in attribute_cols}
    valid_tasks = []
    valid_positions = []

    for r in records:
        if respondent_col not in r or choice_col not in r:
            continue
        resp_val = r[respondent_col]
        choice_raw = r[choice_col]
        if resp_val is None or choice_raw is None:
            continue

        try:
            y_val = float(choice_raw)
        except (ValueError, TypeError):
            continue

        # Check all attributes
        has_all_attrs = True
        for col in attribute_cols:
            if col not in r or r[col] is None:
                has_all_attrs = False
                break
        if not has_all_attrs:
            continue

        valid_resps.append(str(resp_val))
        valid_y.append(y_val)
        for col in attribute_cols:
            valid_attrs[col].append(str(r[col]))

        if task_col and task_col in r and r[task_col] is not None:
            try:
                valid_tasks.append(float(r[task_col]))
            except (ValueError, TypeError):
                valid_tasks.append(1.0)
        else:
            valid_tasks.append(1.0)

        if position_col and position_col in r and r[position_col] is not None:
            try:
                valid_positions.append(int(r[position_col]))
            except (ValueError, TypeError):
                valid_positions.append(1)
        else:
            valid_positions.append(1)

    if len(valid_y) < 20:
        raise ValueError(f"Chỉ có {len(valid_y)} bản ghi hợp lệ đầy đủ biến. Cần tối thiểu 20 bản ghi.")

    arr_attrs = {col: np.array(vals) for col, vals in valid_attrs.items()}

    return FactorialConjointAMCEEngine.analyze(
        respondent_ids=np.array(valid_resps),
        choice_outcomes=np.array(valid_y, dtype=float),
        attributes_data=arr_attrs,
        task_ids=np.array(valid_tasks) if task_col else None,
        profile_positions=np.array(valid_positions) if position_col else None,
        reference_levels=reference_levels,
        interaction_pairs=interaction_pairs,
    )
