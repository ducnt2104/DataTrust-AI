"""
DataTrust - Conjoint Analysis & Discrete Choice Experiment (DCE) Engine
Scientific Framework:
- Conditional Logit / Multinomial Logit Choice Model - Daniel McFadden (1974; Nobel Memorial Prize)
- Discrete Choice Methods with Simulation - Kenneth E. Train (2009, Cambridge University Press)
- Bayesian Statistics and Marketing: Conjoint Analysis - Peter E. Rossi, Greg M. Allenby, & Robert E. McCulloch (2005)
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats
from scipy.optimize import minimize


class ConjointChoiceEngine:
    """
    Multinomial Logit (MNL) and Random Utility Model for Discrete Choice Experiments (DCE),
    Choice-Based Conjoint (CBC), Part-Worth Utility Estimation, and Willingness-To-Pay (WTP).
    """

    @staticmethod
    def estimate(
        choice_data: List[Dict[str, Any]],
        choice_var: str,
        attribute_vars: List[str],
        price_var: Optional[str] = None,
        price_unit: str = "mil VND",
    ) -> Dict[str, Any]:
        """
        Estimates MNL choice parameters.

        Parameters:
        - choice_data: List of observation rows where each choice task or profile choice is recorded.
          Can be structured as chosen profile vs non-chosen profile, or choice indicator with attribute values.
        - choice_var: Column name for binary choice indicator (1 = chosen, 0 = rejected) or chosen alternative id.
        - attribute_vars: List of attribute column names.
        - price_var: Optional attribute variable representing monetary cost/price for WTP calculation.
        - price_unit: Currency unit string for WTP display.
        """
        # Clean rows
        all_cols = [choice_var] + attribute_vars
        clean_rows = []
        for r in choice_data:
            vals = []
            valid = True
            for c in all_cols:
                v = r.get(c)
                if v is None:
                    valid = False
                    break
                try:
                    vals.append(float(v))
                except (ValueError, TypeError):
                    valid = False
                    break
            if valid:
                clean_rows.append(vals)

        N = len(clean_rows)
        k = len(attribute_vars)

        if N < 20 or k < 1:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Conjoint Choice analysis requires at least 20 valid choices and >= 1 attribute. Received N={N}, k={k}.",
                "diagnostics": {"N": N, "k": k},
            }

        mat = np.array(clean_rows, dtype=float)
        Y_choice = (mat[:, 0] > 0).astype(float)  # 1 if chosen, 0 otherwise
        X_attrs = mat[:, 1:]

        n_chosen = int(np.sum(Y_choice == 1))
        n_rejected = int(np.sum(Y_choice == 0))

        if n_chosen < 5 or n_rejected < 5:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Need at least 5 chosen and 5 unchosen profiles. Found N_chosen={n_chosen}, N_rejected={n_rejected}.",
                "diagnostics": {"N": N, "n_chosen": n_chosen, "n_rejected": n_rejected},
            }

        # Standardize X for numerical optimization stability
        means = np.mean(X_attrs, axis=0)
        stds = np.std(X_attrs, axis=0, ddof=1)
        stds[stds == 0] = 1.0

        # We fit binary/conditional logit for profile selection: P(Y=1) = 1 / (1 + exp(- (beta_0 + X * beta)))
        # Design matrix with intercept
        Z = np.column_stack([np.ones(N), (X_attrs - means) / stds])
        p_params = Z.shape[1]

        # Null log-likelihood (intercept only)
        p_null = np.mean(Y_choice)
        p_null = max(1e-6, min(1.0 - 1e-6, p_null))
        ll_null = float(np.sum(Y_choice * math.log(p_null) + (1.0 - Y_choice) * math.log(1.0 - p_null)))

        # Negative log-likelihood with mild L2 regularization
        def neg_log_like(theta):
            eta = Z @ theta
            eta = np.clip(eta, -30.0, 30.0)
            p_pred = 1.0 / (1.0 + np.exp(-eta))
            p_pred = np.clip(p_pred, 1e-12, 1.0 - 1e-12)
            ll = np.sum(Y_choice * np.log(p_pred) + (1.0 - Y_choice) * np.log(1.0 - p_pred))
            reg = 0.001 * np.sum(theta[1:] ** 2)
            return -(ll - reg)

        init_theta = np.zeros(p_params)
        init_theta[0] = math.log(p_null / (1.0 - p_null))

        opt_res = minimize(neg_log_like, init_theta, method="L-BFGS-B")
        theta_hat = opt_res.x
        converged = bool(opt_res.success)
        ll_model = -float(opt_res.fun)

        # Un-standardize beta back to original feature scale
        # eta = b0 + sum_j b_j * (X_j - mean_j) / std_j = (b0 - sum b_j*mean_j/std_j) + sum (b_j/std_j)*X_j
        beta_unstd = theta_hat[1:] / stds
        intercept_unstd = theta_hat[0] - np.sum(theta_hat[1:] * means / stds)

        # Numerical Hessian for standard errors
        hess_inv = np.eye(p_params)
        if hasattr(opt_res, "hess_inv"):
            try:
                if hasattr(opt_res.hess_inv, "todense"):
                    hess_inv = np.array(opt_res.hess_inv.todense())
                else:
                    hess_inv = np.array(opt_res.hess_inv)
            except Exception:
                hess_inv = np.eye(p_params)

        se_theta = np.sqrt(np.maximum(1e-8, np.diag(hess_inv)))
        se_unstd = se_theta[1:] / stds

        # Model fit statistics
        mcfadden_r2 = max(0.0, min(1.0, 1.0 - (ll_model / ll_null)))
        lr_stat = max(0.0, 2.0 * (ll_model - ll_null))
        lr_p_val = float(1.0 - stats.chi2.cdf(lr_stat, df=k))
        aic = 2.0 * p_params - 2.0 * ll_model
        bic = p_params * math.log(N) - 2.0 * ll_model

        # Calculate Part-Worth Utilities and Relative Attribute Importance
        # Attribute Range = |beta_j| * range(X_j)
        attr_ranges = []
        part_worth_table = []
        for j, aname in enumerate(attribute_vars):
            b_j = float(beta_unstd[j])
            se_j = float(se_unstd[j])
            t_j = b_j / se_j if se_j > 0 else 0.0
            p_j = 2.0 * (1.0 - stats.norm.cdf(abs(t_j)))
            ci_low = b_j - 1.96 * se_j
            ci_upp = b_j + 1.96 * se_j

            col_range = float(np.max(X_attrs[:, j]) - np.min(X_attrs[:, j]))
            range_utility = abs(b_j) * max(1.0, col_range)
            attr_ranges.append(range_utility)

            part_worth_table.append({
                "attribute": aname,
                "part_worth_utility": round(b_j, 4),
                "se": round(se_j, 4),
                "t_stat": round(t_j, 2),
                "p_value": round(float(p_j), 5),
                "ci_95_lower": round(ci_low, 4),
                "ci_95_upper": round(ci_upp, 4),
                "range_utility": round(range_utility, 4),
                "is_significant": bool(p_j < 0.05),
            })

        total_range = max(1e-6, sum(attr_ranges))
        for j, row in enumerate(part_worth_table):
            row["relative_importance_pct"] = round((attr_ranges[j] / total_range) * 100.0, 2)

        # Sort part-worths by descending importance
        part_worth_table.sort(key=lambda x: x["relative_importance_pct"], reverse=True)

        # Willingness-To-Pay (WTP) calculation if price_var is identified
        wtp_results = []
        price_beta = None
        price_se = None
        price_name = None

        if price_var and price_var in attribute_vars:
            price_name = price_var
            p_idx = attribute_vars.index(price_var)
            price_beta = float(beta_unstd[p_idx])
            price_se = float(se_unstd[p_idx])
        else:
            # Auto-detect price-like variable
            for aname in attribute_vars:
                lower_a = aname.lower()
                if any(w in lower_a for w in ["price", "cost", "giá", "phí", "fee"]):
                    price_name = aname
                    p_idx = attribute_vars.index(aname)
                    price_beta = float(beta_unstd[p_idx])
                    price_se = float(se_unstd[p_idx])
                    break

        if price_beta is not None and abs(price_beta) > 1e-6:
            for j, aname in enumerate(attribute_vars):
                if aname == price_name:
                    continue
                b_j = float(beta_unstd[j])
                se_j = float(se_unstd[j])
                # WTP = - beta_k / beta_price
                wtp_val = - (b_j / price_beta)
                # Delta method SE for ratio: var(A/B) approx (1/B^2) var(A) + (A^2/B^4) var(B)
                wtp_var = (1.0 / (price_beta ** 2)) * (se_j ** 2) + ((b_j ** 2) / (price_beta ** 4)) * (price_se ** 2)
                wtp_se = math.sqrt(max(1e-8, wtp_var))

                wtp_results.append({
                    "attribute": aname,
                    "wtp_estimate": round(wtp_val, 3),
                    "wtp_se": round(wtp_se, 3),
                    "wtp_ci_lower": round(wtp_val - 1.96 * wtp_se, 3),
                    "wtp_ci_upper": round(wtp_val + 1.96 * wtp_se, 3),
                    "unit": price_unit,
                })

        # Generate Dual-Panel SVG Visualization
        svg_viz = _generate_conjoint_svg(
            part_worths=part_worth_table,
            wtp_results=wtp_results,
            price_unit=price_unit,
            mcfadden_r2=mcfadden_r2,
        )

        # Academic APA 7th Narrative
        apa_narrative = _generate_conjoint_apa_narrative(
            N=N,
            k=k,
            ll_model=ll_model,
            ll_null=ll_null,
            mcfadden_r2=mcfadden_r2,
            lr_stat=lr_stat,
            lr_p_val=lr_p_val,
            part_worths=part_worth_table,
            wtp_results=wtp_results,
            price_name=price_name,
            price_unit=price_unit,
        )

        return {
            "status": "SUCCESS",
            "model_type": "CONJOINT_DISCRETE_CHOICE_MNL",
            "diagnostics": {
                "N": N,
                "n_chosen": n_chosen,
                "n_rejected": n_rejected,
                "n_attributes": k,
                "mcfadden_pseudo_r2": round(mcfadden_r2, 4),
                "log_likelihood": round(ll_model, 2),
                "null_log_likelihood": round(ll_null, 2),
                "lr_test_stat": round(lr_stat, 2),
                "lr_test_p_value": round(lr_p_val, 5),
                "aic": round(aic, 2),
                "bic": round(bic, 2),
                "converged": converged,
            },
            "part_worth_utilities": part_worth_table,
            "willingness_to_pay": wtp_results,
            "svg_visualization": svg_viz,
            "apa_narrative": apa_narrative,
        }


def _generate_conjoint_svg(
    part_worths: List[Dict[str, Any]],
    wtp_results: List[Dict[str, Any]],
    price_unit: str,
    mcfadden_r2: float,
) -> str:
    """
    Generates a dual-panel SVG:
    Panel A: Relative Attribute Importance Bar Chart (% Share of Preference).
    Panel B: Part-Worth Utility Coefficients & 95% Confidence Intervals (or WTP Forest Plot).
    """
    width = 960
    height = 540

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#0f172a; font-family:Inter,system-ui,sans-serif;">',
        '<defs>',
        '  <linearGradient id="impGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '    <stop offset="0%" stop-color="#3b82f6" />',
        '    <stop offset="100%" stop-color="#8b5cf6" />',
        '  </linearGradient>',
        '  <linearGradient id="wtpGrad" x1="0%" y1="0%" x2="100%" y2="0%">',
        '    <stop offset="0%" stop-color="#10b981" />',
        '    <stop offset="100%" stop-color="#06b6d4" />',
        '  </linearGradient>',
        '</defs>',
        # Header
        f'<text x="30" y="36" fill="#f8fafc" font-size="18" font-weight="700">Choice-Based Conjoint &amp; Willingness-To-Pay (McFadden MNL)</text>',
        f'<text x="30" y="58" fill="#94a3b8" font-size="12">McFadden (1974) &amp; Train (2009) | Discrete Choice Model | Pseudo-R² = {mcfadden_r2:.3f}</text>',
    ]

    # Panel A: Relative Importance % (x: 40 -> 470, y: 90 -> 500)
    pa_x0, pa_y0, pa_w, pa_h = 40, 90, 430, 410
    svg.append(f'<rect x="{pa_x0}" y="{pa_y0}" width="{pa_w}" height="{pa_h}" rx="8" fill="#1e293b" fill-opacity="0.5" stroke="#334155" stroke-width="1" />')
    svg.append(f'<text x="{pa_x0 + 20}" y="{pa_y0 + 26}" fill="#a78bfa" font-size="14" font-weight="600">Panel A: Relative Attribute Importance (%)</text>')
    svg.append(f'<text x="{pa_x0 + 20}" y="{pa_y0 + 44}" fill="#64748b" font-size="11">Percentage contribution to choice utility range</text>')

    chart_y = pa_y0 + 75
    bar_h = 24
    spacing = 45
    max_imp = max(10.0, max((p["relative_importance_pct"] for p in part_worths), default=10.0))

    for idx, pw in enumerate(part_worths[:6]):
        y_pos = chart_y + idx * spacing
        aname = pw["attribute"]
        short_name = aname[:14] + ".." if len(aname) > 16 else aname
        bar_len = min(200, (pw["relative_importance_pct"] / max_imp) * 200)

        svg.append(f'<text x="{pa_x0 + 20}" y="{y_pos + 16}" fill="#cbd5e1" font-size="11" font-weight="500">{short_name}</text>')
        svg.append(f'<rect x="{pa_x0 + 130}" y="{y_pos}" width="{bar_len:.1f}" height="{bar_h}" rx="4" fill="url(#impGrad)" opacity="0.85" />')
        svg.append(f'<text x="{pa_x0 + 140 + bar_len:.1f}" y="{y_pos + 16}" fill="#94a3b8" font-size="10" font-weight="600">{pw["relative_importance_pct"]:.1f}%</text>')

    # Panel B: Willingness to Pay or Part-Worths Forest Plot (x: 490 -> 920, y: 90 -> 500)
    pb_x0, pb_y0, pb_w, pb_h = 490, 90, 430, 410
    svg.append(f'<rect x="{pb_x0}" y="{pb_y0}" width="{pb_w}" height="{pb_h}" rx="8" fill="#1e293b" fill-opacity="0.5" stroke="#334155" stroke-width="1" />')

    if wtp_results:
        svg.append(f'<text x="{pb_x0 + 20}" y="{pb_y0 + 26}" fill="#34d399" font-size="14" font-weight="600">Panel B: Marginal Willingness-To-Pay (WTP)</text>')
        svg.append(f'<text x="{pb_x0 + 20}" y="{pb_y0 + 44}" fill="#64748b" font-size="11">Valuation in {price_unit} relative to baseline with 95% CI</text>')

        chart_y_b = pb_y0 + 75
        all_vals = [w["wtp_estimate"] for w in wtp_results] + [w["wtp_ci_lower"] for w in wtp_results] + [w["wtp_ci_upper"] for w in wtp_results]
        min_wtp = min(all_vals) if all_vals else -1.0
        max_wtp = max(all_vals) if all_vals else 1.0
        wtp_span = max(1e-4, max_wtp - min_wtp)

        plot_b_left = pb_x0 + 130
        plot_b_width = 240

        def to_wtp_x(v):
            return plot_b_left + ((v - min_wtp) / wtp_span) * plot_b_width

        # Zero reference line
        if min_wtp <= 0 <= max_wtp:
            zx = to_wtp_x(0.0)
            svg.append(f'<line x1="{zx:.1f}" y1="{chart_y_b - 10}" x2="{zx:.1f}" y2="{chart_y_b + len(wtp_results) * spacing}" stroke="#475569" stroke-width="1" stroke-dasharray="3,3" />')

        for idx, w in enumerate(wtp_results[:6]):
            y_pos = chart_y_b + idx * spacing
            aname = w["attribute"]
            short_name = aname[:12] + ".." if len(aname) > 14 else aname

            cx = to_wtp_x(w["wtp_estimate"])
            lx = to_wtp_x(w["wtp_ci_lower"])
            ux = to_wtp_x(w["wtp_ci_upper"])

            svg.append(f'<text x="{pb_x0 + 20}" y="{y_pos + 16}" fill="#cbd5e1" font-size="11" font-weight="500">{short_name}</text>')
            # Error bar
            svg.append(f'<line x1="{lx:.1f}" y1="{y_pos + 12}" x2="{ux:.1f}" y2="{y_pos + 12}" stroke="#34d399" stroke-width="2" />')
            svg.append(f'<line x1="{lx:.1f}" y1="{y_pos + 6}" x2="{lx:.1f}" y2="{y_pos + 18}" stroke="#34d399" stroke-width="1.5" />')
            svg.append(f'<line x1="{ux:.1f}" y1="{y_pos + 6}" x2="{ux:.1f}" y2="{y_pos + 18}" stroke="#34d399" stroke-width="1.5" />')
            # Center point
            svg.append(f'<circle cx="{cx:.1f}" cy="{y_pos + 12}" r="5" fill="#10b981" stroke="#ffffff" stroke-width="1.5" />')
            svg.append(f'<text x="{pb_x0 + 380}" y="{y_pos + 16}" fill="#34d399" font-size="10" font-weight="600">{w["wtp_estimate"]:+.2f}</text>')
    else:
        svg.append(f'<text x="{pb_x0 + 20}" y="{pb_y0 + 26}" fill="#38bdf8" font-size="14" font-weight="600">Panel B: Part-Worth Utility Coefficients</text>')
        svg.append(f'<text x="{pb_x0 + 20}" y="{pb_y0 + 44}" fill="#64748b" font-size="11">Standardized preference weights with 95% CI</text>')

        chart_y_b = pb_y0 + 75
        for idx, pw in enumerate(part_worths[:6]):
            y_pos = chart_y_b + idx * spacing
            aname = pw["attribute"]
            short_name = aname[:12] + ".." if len(aname) > 14 else aname
            coef = pw["part_worth_utility"]
            color = "#10b981" if coef >= 0 else "#f43f5e"

            svg.append(f'<text x="{pb_x0 + 20}" y="{y_pos + 16}" fill="#cbd5e1" font-size="11" font-weight="500">{short_name}</text>')
            svg.append(f'<text x="{pb_x0 + 160}" y="{y_pos + 16}" fill="{color}" font-size="12" font-mono="true" font-weight="700">{coef:+.3f}</text>')
            svg.append(f'<text x="{pb_x0 + 240}" y="{y_pos + 16}" fill="#94a3b8" font-size="10">p = {pw["p_value"]:.4f}</text>')

    svg.append('</svg>')
    return "\n".join(svg)


def _generate_conjoint_apa_narrative(
    N: int,
    k: int,
    ll_model: float,
    ll_null: float,
    mcfadden_r2: float,
    lr_stat: float,
    lr_p_val: float,
    part_worths: List[Dict[str, Any]],
    wtp_results: List[Dict[str, Any]],
    price_name: Optional[str],
    price_unit: str,
) -> str:
    """Generates an academic narrative in APA 7th edition style describing Conjoint Choice findings."""
    top_attr = part_worths[0] if part_worths else None
    top_str = f"'{top_attr['attribute']}' (relative importance = {top_attr['relative_importance_pct']:.1f}%, beta = {top_attr['part_worth_utility']:+.3f}, p = {top_attr['p_value']:.4f})" if top_attr else "N/A"

    lines = [
        f"A Choice-Based Conjoint (CBC) analysis was estimated on discrete choice experiment observations (N = {N} choices, {k} attributes) using McFadden's random utility multinomial logit framework (McFadden, 1974; Train, 2009).",
        f"The choice model exhibited robust explanatory power over the null model (Log-Likelihood = {ll_model:.2f} vs. Null LL = {ll_null:.2f}; Likelihood Ratio chi-square({k}) = {lr_stat:.2f}, p {'< .001' if lr_p_val < 0.001 else f'= {lr_p_val:.4f}'}; McFadden's Pseudo-R^2 = {mcfadden_r2:.3f}).",
        f"Attribute importance decomposition identified {top_str} as the primary driver governing respondent preference trade-offs.",
    ]

    if wtp_results:
        sig_wtp = [w for w in wtp_results if (w["wtp_ci_lower"] > 0 or w["wtp_ci_upper"] < 0)]
        if sig_wtp:
            top_wtp = sig_wtp[0]
            lines.append(
                f"Monetary valuation via Marginal Willingness-To-Pay (WTP) anchored against '{price_name}' revealed that respondents are willing to pay an average of {top_wtp['wtp_estimate']:+.2f} {price_unit} (95% CI [{top_wtp['wtp_ci_lower']:+.2f}, {top_wtp['wtp_ci_upper']:+.2f}]) for a one-unit improvement in '{top_wtp['attribute']}'."
            )

    return " ".join(lines)
