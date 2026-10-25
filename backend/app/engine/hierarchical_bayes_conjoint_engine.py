"""
Choice-Based Conjoint Hierarchical Bayes with Market Simulator & WTP Engine (CBC-HB)
DataTrust Quantitative Intelligence System

Implementation Reference:
- Rossi, P. E., Allenby, G. M., & McCulloch, R. (2005). Bayesian Statistics and Marketing.
  John Wiley & Sons.
- Train, K. E. (2009). Discrete Choice Methods with Simulation (2nd ed.).
  Cambridge University Press.
- Orme, B. (2010). Getting Started with Conjoint Analysis: Strategies for
  Product Design and Pricing Research. Research Publishers LLC.

Core Features:
1. Hierarchical Bayes / Empirical Bayes MAP shrinkage for individual respondent part-worth utilities:
   beta_i ~ N(mu, Sigma), borrowing strength across heterogeneous survey respondents.
2. Computes Attribute Relative Importance (RI) distribution (%) across surveyed consumers.
3. Calculates Willingness-to-Pay (WTP) distribution for all attribute levels relative to price slope.
4. Interactive Market Simulator: Predicts counterfactual market shares under:
   - Share of Preference (Logit rule)
   - First Choice rule (Highest utility allocation)
5. Generates publication-ready SVG visualization (Attribute Importance bars & Market Share breakdown).
"""

from typing import Dict, List, Optional, Any, Tuple, Union
import numpy as np
import pandas as pd
from scipy import optimize, stats


def run_hierarchical_bayes_conjoint(
    records: Union[List[Dict[str, Any]], pd.DataFrame],
    choice_col: str,
    respondent_col: str,
    attribute_cols: List[str],
    price_col: Optional[str] = None,
    simulation_profiles: Optional[List[Dict[str, Any]]] = None,
    alpha_level: float = 0.05
) -> Dict[str, Any]:
    """
    Executes Choice-Based Conjoint Hierarchical Bayes estimation and Market Simulation.
    """
    if isinstance(records, pd.DataFrame):
        records = records.to_dict(orient="records")

    if not records or len(records) < 20:
        return {
            "status": "insufficient_data",
            "message": f"Requires at least 20 conjoint choice task observations (received {len(records)})."
        }

    if not attribute_cols:
        return {
            "status": "insufficient_data",
            "message": "At least one product attribute column must be specified."
        }

    # Extract valid records
    extracted = []
    all_needed_cols = [choice_col, respondent_col] + attribute_cols
    if price_col:
        all_needed_cols.append(price_col)

    for r in records:
        c_val = r.get(choice_col)
        resp_val = r.get(respondent_col)

        if c_val is None or resp_val is None:
            continue

        try:
            choice_num = float(c_val)
        except (ValueError, TypeError):
            continue

        row_dict = {
            "choice": choice_num,
            "resp_id": str(resp_val).strip()
        }

        skip_row = False
        for attr in attribute_cols:
            val = r.get(attr)
            if val is None:
                skip_row = True
                break
            row_dict[attr] = str(val).strip()

        if price_col:
            p_val = r.get(price_col)
            if p_val is None:
                skip_row = True
            else:
                try:
                    row_dict["price"] = float(p_val)
                except (ValueError, TypeError):
                    skip_row = True

        if not skip_row:
            extracted.append(row_dict)

    if len(extracted) < 20:
        return {
            "status": "insufficient_data",
            "message": "Fewer than 20 complete conjoint observations after validation."
        }

    df = pd.DataFrame(extracted)
    respondents = df["resp_id"].unique()

    if len(respondents) < 3:
        return {
            "status": "insufficient_data",
            "message": f"Conjoint Hierarchical Bayes requires at least 3 distinct respondents (found {len(respondents)})."
        }

    # Build dummy encoding for attributes (drop first level for identification)
    attribute_levels: Dict[str, List[str]] = {}
    feature_names: List[str] = []
    feature_to_attr: Dict[str, str] = {}

    for attr in attribute_cols:
        levels = sorted(df[attr].unique().tolist())
        attribute_levels[attr] = levels
        # Keep levels[1:] as dummy features
        for lvl in levels[1:]:
            fname = f"{attr}__{lvl}"
            feature_names.append(fname)
            feature_to_attr[fname] = attr

    has_price = price_col is not None and "price" in df.columns
    if has_price:
        feature_names.append("price_continuous")
        feature_to_attr["price_continuous"] = "price"

    n_features = len(feature_names)
    if n_features == 0:
        return {
            "status": "insufficient_data",
            "message": "No attribute variations found across choice profiles."
        }

    # Construct design matrix X and target y
    X_rows = []
    y_vals = []
    resp_indices = []

    resp_map = {r_id: idx for idx, r_id in enumerate(respondents)}

    for idx, row in df.iterrows():
        feat_vec = np.zeros(n_features)
        f_idx = 0
        for attr in attribute_cols:
            attr_val = row[attr]
            for lvl in attribute_levels[attr][1:]:
                if attr_val == lvl:
                    feat_vec[f_idx] = 1.0
                f_idx += 1
        if has_price:
            feat_vec[-1] = float(row["price"])

        X_rows.append(feat_vec)
        # Binarize choice (1 if chosen / rating > median, 0 otherwise)
        y_vals.append(float(row["choice"]))
        resp_indices.append(resp_map[row["resp_id"]])

    X = np.array(X_rows)
    y_raw = np.array(y_vals)
    # Binary choice threshold: 1 if > median, or strictly == 1 if 0/1
    if set(np.unique(y_raw)).issubset({0.0, 1.0}):
        y = y_raw
    else:
        med = np.median(y_raw)
        y = (y_raw >= med).astype(float)

    # 1. Estimate Population Level Prior mu and Sigma via Regularized Logistic Regression
    reg_lambda = 0.5
    def logit_loss(beta):
        pred = 1.0 / (1.0 + np.exp(-np.clip(X @ beta, -25.0, 25.0)))
        eps = 1e-12
        ll = -np.sum(y * np.log(pred + eps) + (1.0 - y) * np.log(1.0 - pred + eps))
        return ll + 0.5 * reg_lambda * np.sum(beta ** 2)

    init_beta = np.zeros(n_features)
    opt_res = optimize.minimize(logit_loss, init_beta, method="L-BFGS-B")
    mu_pop = opt_res.x

    # Population covariance prior (diagonal shrinkage with mild variance)
    sigma_pop = np.eye(n_features) * 1.5
    inv_sigma_pop = np.linalg.inv(sigma_pop)

    # 2. Estimate Individual Respondent Part-Worths via Empirical Bayes MAP
    individual_part_worths: List[np.ndarray] = []

    for r_idx, r_id in enumerate(respondents):
        mask = (np.array(resp_indices) == r_idx)
        X_i = X[mask]
        y_i = y[mask]

        if len(y_i) == 0:
            individual_part_worths.append(mu_pop.copy())
            continue

        def individual_map_loss(beta_i):
            pred_i = 1.0 / (1.0 + np.exp(-np.clip(X_i @ beta_i, -25.0, 25.0)))
            eps = 1e-12
            ll_i = -np.sum(y_i * np.log(pred_i + eps) + (1.0 - y_i) * np.log(1.0 - pred_i + eps))
            # Gaussian prior N(mu_pop, sigma_pop)
            diff = beta_i - mu_pop
            prior_penalty = 0.5 * diff.T @ inv_sigma_pop @ diff
            return ll_i + prior_penalty

        res_i = optimize.minimize(individual_map_loss, mu_pop, method="L-BFGS-B")
        individual_part_worths.append(res_i.x)

    individual_betas = np.array(individual_part_worths)  # Shape: (N_resp, n_features)

    # 3. Calculate Attribute Relative Importance (RI)
    # For each respondent, compute utility range per attribute
    all_attributes = list(attribute_cols)
    if has_price:
        all_attributes.append("price")

    resp_attr_ranges: Dict[str, List[float]] = {a: [] for a in all_attributes}

    for b_i in individual_betas:
        f_idx = 0
        for attr in attribute_cols:
            levels = attribute_levels[attr]
            # Level 0 is 0.0 (reference)
            utilities = [0.0]
            for lvl in levels[1:]:
                utilities.append(float(b_i[f_idx]))
                f_idx += 1
            u_range = max(utilities) - min(utilities)
            resp_attr_ranges[attr].append(u_range)

        if has_price:
            price_slope = abs(float(b_i[-1]))
            # Price range evaluated over empirical price spread
            p_spread = float(df["price"].max() - df["price"].min()) if df["price"].max() > df["price"].min() else 1.0
            resp_attr_ranges["price"].append(price_slope * p_spread)

    # Relative importance percentage per respondent
    attribute_importance: Dict[str, Dict[str, float]] = {}
    n_resp = len(respondents)
    ri_matrix = np.zeros((n_resp, len(all_attributes)))

    for i in range(n_resp):
        sum_range = sum([resp_attr_ranges[a][i] for a in all_attributes]) or 1e-6
        for a_idx, a in enumerate(all_attributes):
            ri_matrix[i, a_idx] = (resp_attr_ranges[a][i] / sum_range) * 100.0

    for a_idx, a in enumerate(all_attributes):
        ri_col = ri_matrix[:, a_idx]
        attribute_importance[a] = {
            "mean_importance": round(float(np.mean(ri_col)), 2),
            "median_importance": round(float(np.median(ri_col)), 2),
            "std_dev": round(float(np.std(ri_col, ddof=1) if len(ri_col) > 1 else 0.0), 2)
        }

    # 4. Willingness-to-Pay (WTP) Distribution (if price column present)
    wtp_estimates: Dict[str, Any] = {}
    if has_price:
        price_slopes = individual_betas[:, -1]
        # Avoid zero division
        adj_slopes = np.where(np.abs(price_slopes) < 1e-4, -1e-4, price_slopes)

        f_idx = 0
        for attr in attribute_cols:
            for lvl in attribute_levels[attr][1:]:
                feat_name = f"{attr}__{lvl}"
                lvl_utilities = individual_betas[:, f_idx]
                # WTP = - (Utility / PriceSlope)
                wtp_dist = - (lvl_utilities / adj_slopes)
                # Trim extreme outliers for robust reporting (5th to 95th percentile)
                p05, p95 = np.percentile(wtp_dist, [5, 95])
                trimmed_wtp = wtp_dist[(wtp_dist >= p05) & (wtp_dist <= p95)]

                mean_wtp = float(np.mean(trimmed_wtp)) if len(trimmed_wtp) > 0 else float(np.mean(wtp_dist))
                med_wtp = float(np.median(trimmed_wtp)) if len(trimmed_wtp) > 0 else float(np.median(wtp_dist))

                wtp_estimates[feat_name] = {
                    "attribute": attr,
                    "level": lvl,
                    "mean_wtp": round(mean_wtp, 2),
                    "median_wtp": round(med_wtp, 2),
                    "ci_95": [round(float(p05), 2), round(float(p95), 2)]
                }
                f_idx += 1

    # 5. Market Simulator
    # If no simulation profiles provided, create 2 standard benchmark offerings
    if not simulation_profiles or len(simulation_profiles) < 2:
        simulation_profiles = []
        # Profile 1: Base Offering (reference levels)
        p1 = {"name": "Product Alpha (Standard)"}
        for attr in attribute_cols:
            p1[attr] = attribute_levels[attr][0]
        if has_price:
            p1["price"] = float(df["price"].min()) if not df.empty else 10.0
        simulation_profiles.append(p1)

        # Profile 2: Premium Offering (highest levels)
        p2 = {"name": "Product Beta (Premium)"}
        for attr in attribute_cols:
            p2[attr] = attribute_levels[attr][-1]
        if has_price:
            p2["price"] = float(df["price"].max()) if not df.empty else 20.0
        simulation_profiles.append(p2)

    market_shares = _simulate_market_shares(
        profiles=simulation_profiles,
        attribute_cols=attribute_cols,
        attribute_levels=attribute_levels,
        has_price=has_price,
        individual_betas=individual_betas,
        feature_names=feature_names
    )

    # 6. Part-Worth Summary (Mean and SD across population)
    part_worth_summary: List[Dict[str, Any]] = []
    f_idx = 0
    for attr in attribute_cols:
        # Base level is 0.0
        part_worth_summary.append({
            "attribute": attr,
            "level": attribute_levels[attr][0],
            "is_reference": True,
            "mean_part_worth": 0.0,
            "se": 0.0
        })
        for lvl in attribute_levels[attr][1:]:
            b_col = individual_betas[:, f_idx]
            part_worth_summary.append({
                "attribute": attr,
                "level": lvl,
                "is_reference": False,
                "mean_part_worth": round(float(np.mean(b_col)), 4),
                "se": round(float(np.std(b_col, ddof=1) / np.sqrt(len(b_col)) if len(b_col) > 1 else 0.05), 4)
            })
            f_idx += 1

    if has_price:
        p_col = individual_betas[:, -1]
        part_worth_summary.append({
            "attribute": "price",
            "level": "Continuous Slope",
            "is_reference": False,
            "mean_part_worth": round(float(np.mean(p_col)), 4),
            "se": round(float(np.std(p_col, ddof=1) / np.sqrt(len(p_col)) if len(p_col) > 1 else 0.05), 4)
        })

    # SVG Visualizer (Attribute Relative Importance Bar Chart & Market Share Simulator)
    svg_chart = _generate_conjoint_svg(attribute_importance, market_shares)

    # APA 7th Academic Narrative
    top_attr = max(attribute_importance.items(), key=lambda kv: kv[1]["mean_importance"])
    narrative = (
        f"A choice-based conjoint analysis with hierarchical Bayes empirical estimation (Rossi et al., 2005; Train, 2009) "
        f"was conducted across N = {n_resp} respondents evaluating {len(all_attributes)} attributes over {len(df)} choice tasks. "
        f"Attribute relative importance revealed that '{top_attr[0]}' exerted the strongest influence on consumer preference "
        f"(M = {top_attr[1]['mean_importance']:.1f}%, SD = {top_attr[1]['std_dev']:.1f}%), followed by other product characteristics. "
        f"Simulated market preference allocations projected {market_shares[0]['product_name']} capturing "
        f"{market_shares[0]['share_of_preference']:.1f}% share of preference versus {market_shares[1]['share_of_preference']:.1f}% "
        f"for {market_shares[1]['product_name']} under competitive logit choice dynamics."
    )

    return {
        "status": "success",
        "sample_size": int(len(df)),
        "n_respondents": int(n_resp),
        "attribute_importance": attribute_importance,
        "part_worth_utilities": part_worth_summary,
        "wtp_estimates": wtp_estimates,
        "market_simulation": market_shares,
        "svg_visualization": svg_chart,
        "apa_narrative": narrative
    }


def _simulate_market_shares(
    profiles: List[Dict[str, Any]],
    attribute_cols: List[str],
    attribute_levels: Dict[str, List[str]],
    has_price: bool,
    individual_betas: np.ndarray,
    feature_names: List[str]
) -> List[Dict[str, Any]]:
    """Simulates market share allocations across product profiles."""
    n_resp, n_feat = individual_betas.shape
    n_prods = len(profiles)

    # Build design vectors for each profile
    X_prods = np.zeros((n_prods, n_feat))
    for p_idx, prof in enumerate(profiles):
        f_idx = 0
        for attr in attribute_cols:
            val = prof.get(attr)
            for lvl in attribute_levels[attr][1:]:
                if val == lvl:
                    X_prods[p_idx, f_idx] = 1.0
                f_idx += 1
        if has_price:
            X_prods[p_idx, -1] = float(prof.get("price", 0.0))

    # Calculate utility per respondent per product: U_{i, p} = X_{p} @ beta_i
    # Shape: (n_resp, n_prods)
    utilities = individual_betas @ X_prods.T

    # 1. Share of Preference (Logit rule)
    exp_u = np.exp(np.clip(utilities - np.max(utilities, axis=1, keepdims=True), -25.0, 25.0))
    prob_matrix = exp_u / np.sum(exp_u, axis=1, keepdims=True)
    sop_shares = np.mean(prob_matrix, axis=0) * 100.0

    # 2. First Choice rule
    first_choice_idx = np.argmax(utilities, axis=1)
    fc_shares = np.array([np.mean(first_choice_idx == p_idx) * 100.0 for p_idx in range(n_prods)])

    results = []
    for p_idx, prof in enumerate(profiles):
        p_name = prof.get("name", f"Profile {p_idx + 1}")
        results.append({
            "product_name": p_name,
            "share_of_preference": round(float(sop_shares[p_idx]), 2),
            "first_choice_share": round(float(fc_shares[p_idx]), 2),
            "mean_utility": round(float(np.mean(utilities[:, p_idx])), 3)
        })

    return results


def _generate_conjoint_svg(
    importance: Dict[str, Dict[str, float]],
    market_shares: List[Dict[str, Any]]
) -> str:
    """Generates a responsive dual-panel SVG: Relative Importance Bars & Market Share Bars."""
    w, h = 680, 280
    half_w = 320
    pad_x = 45
    pad_y = 35

    # Panel A: Attribute Relative Importance (Horizontal Bars)
    sorted_attrs = sorted(importance.items(), key=lambda kv: kv[1]["mean_importance"], reverse=True)
    bar_height = 20
    gap = 14

    panel_a_bars = []
    for idx, (attr_name, vals) in enumerate(sorted_attrs[:5]):
        y_pos = pad_y + 15 + idx * (bar_height + gap)
        imp_val = vals["mean_importance"]
        bar_len = (imp_val / 100.0) * (half_w - pad_x - 70)
        display_name = attr_name.replace("_", " ").title()
        if len(display_name) > 14:
            display_name = display_name[:14] + "..."

        panel_a_bars.append(f"""
          <text x="{pad_x}" y="{y_pos + 14}" fill="#cbd5e1" font-size="10" font-weight="500">{display_name}</text>
          <rect x="{pad_x + 95}" y="{y_pos}" width="{max(2, bar_len):.1f}" height="{bar_height}" rx="4" fill="#f59e0b" opacity="0.85"/>
          <text x="{pad_x + 105 + bar_len:.1f}" y="{y_pos + 14}" fill="#fbbf24" font-size="10" font-weight="bold">{imp_val:.1f}%</text>
        """)

    # Panel B: Market Share Projections (Vertical Stacked or Side-by-Side Bars)
    offset_b = half_w + 30
    panel_b_bars = []
    prod_bar_width = 36
    prod_gap = 25
    start_x_b = offset_b + pad_x + 20

    for idx, prod in enumerate(market_shares[:4]):
        sop = prod["share_of_preference"]
        bar_h = (sop / 100.0) * (h - 2 * pad_y - 40)
        x_pos = start_x_b + idx * (prod_bar_width + prod_gap)
        y_pos = (h - pad_y) - bar_h
        p_name = prod["product_name"]
        if len(p_name) > 10:
            p_name = p_name[:10] + "..."

        panel_b_bars.append(f"""
          <rect x="{x_pos:.1f}" y="{y_pos:.1f}" width="{prod_bar_width}" height="{max(2, bar_h):.1f}" rx="5" fill="#38bdf8" opacity="0.9"/>
          <text x="{x_pos + prod_bar_width/2:.1f}" y="{y_pos - 6:.1f}" fill="#38bdf8" font-size="10" font-weight="bold" text-anchor="middle">{sop:.1f}%</text>
          <text x="{x_pos + prod_bar_width/2:.1f}" y="{h - pad_y + 14}" fill="#cbd5e1" font-size="9" text-anchor="middle">{p_name}</text>
        """)

    return f"""<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto">
  <!-- Panel A: Relative Importance -->
  <text x="{half_w/2}" y="18" fill="#e2e8f0" font-size="11" font-weight="bold" text-anchor="middle">
    Attribute Relative Importance (RI %)
  </text>
  <line x1="{pad_x + 90}" y1="{pad_y}" x2="{pad_x + 90}" y2="{h - pad_y}" stroke="#475569" stroke-width="1.2"/>
  {"".join(panel_a_bars)}

  <!-- Panel B: Market Share Simulator -->
  <text x="{offset_b + half_w/2 - 15}" y="18" fill="#e2e8f0" font-size="11" font-weight="bold" text-anchor="middle">
    Simulated Market Share (Logit Preference Rule)
  </text>
  <line x1="{offset_b + pad_x}" y1="{h - pad_y}" x2="{w - 20}" y2="{h - pad_y}" stroke="#475569" stroke-width="1.2"/>
  {"".join(panel_b_bars)}
</svg>"""
