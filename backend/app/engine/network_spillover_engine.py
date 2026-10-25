# -*- coding: utf-8 -*-
"""
Causal Inference with Network Interference & Peer Spillover Effects Engine (Network SUTVA)
Methodological References:
- Hudgens, M. G., & Halloran, M. E. (2008). "Toward causal inference with interference."
  Journal of the American Statistical Association, 103(482), 832–842.
- Aronow, P. M., & Samii, C. (2017). "Estimating average causal effects under general interference,
  with application to a social network experiment." The Annals of Applied Statistics, 11(4), 1912–1947.
- Basse, G. W., & Feller, A. (2018). "Analyzing two-stage experiments in the presence of interference."
  Biometrika, 105(1), 41–58.
- Sävje, F., Aronow, P. M., & Hudgens, M. G. (2021). "Average treatment effects in the presence of unknown
  interference." Journal of the Royal Statistical Society: Series B, 83(1), 152–183.

Implements causal inference under SUTVA violations in clustered, departmental, or social network surveys.
Decomposes causal impacts into Average Direct Effect (ADE), Average Indirect/Spillover Effect (AIE),
and Overall Total Effect (OTE). Tests sharp null hypothesis of no spillover (SUTVA validity),
and computes continuous neighborhood dosage regressions.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
import pandas as pd
from scipy import stats


def _generate_network_svg(
    clusters: List[Dict[str, Any]],
    ade: float,
    aie: float,
    ote: float,
    spillover_share: float,
    p_sutva: float,
    width: int = 860,
    height: int = 420
) -> str:
    """
    Renders dark-themed SVG network visualizer displaying clustered survey peer networks
    colored by causal exposure state (Isolated Control, Direct, Spillover, Joint).
    """
    svg = [
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="background: #0f172a; border-radius: 8px; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;">',
        '<defs>',
        '  <radialGradient id="clusterGlow" cx="50%" cy="50%" r="50%">',
        '    <stop offset="0%" stop-color="#334155" stop-opacity="0.3"/>',
        '    <stop offset="100%" stop-color="#1e293b" stop-opacity="0.0"/>',
        '  </radialGradient>',
        '</defs>',
        f'<text x="24" y="32" fill="#f8fafc" font-size="16" font-weight="bold">Network Interference &amp; Peer Spillover Graph (DataTrust SUTVA Guard)</text>',
        f'<text x="24" y="50" fill="#94a3b8" font-size="12">Decomposition of Personal Treatment vs Peer Neighborhood Contagion</text>',
    ]

    # Legend at top right
    leg_x = width - 360
    svg.extend([
        f'<circle cx="{leg_x}" cy="30" r="5" fill="#64748b"/>',
        f'<text x="{leg_x + 10}" y="34" fill="#cbd5e1" font-size="10">Control (0,0)</text>',
        f'<circle cx="{leg_x + 90}" cy="30" r="5" fill="#3b82f6"/>',
        f'<text x="{leg_x + 100}" y="34" fill="#93c5fd" font-size="10">Direct (1,0)</text>',
        f'<circle cx="{leg_x + 175}" cy="30" r="5" fill="#f59e0b"/>',
        f'<text x="{leg_x + 185}" y="34" fill="#fcd34d" font-size="10">Spillover (0,1)</text>',
        f'<circle cx="{leg_x + 270}" cy="30" r="5" fill="#a855f7"/>',
        f'<text x="{leg_x + 280}" y="34" fill="#d8b4fe" font-size="10">Joint (1,1)</text>',
    ])

    # Draw clusters as network rings
    n_clus = min(len(clusters), 4)
    clus_spacing = int((width - 80) / max(1, n_clus))

    state_colors = {
        "isolated_control": "#64748b",
        "direct_only": "#3b82f6",
        "spillover_only": "#f59e0b",
        "joint_treated": "#a855f7"
    }

    for c_idx, clus in enumerate(clusters[:n_clus]):
        cx = 60 + c_idx * clus_spacing + int(clus_spacing / 2)
        cy = 180
        radius = 70

        # Cluster boundary circle
        c_name = str(clus.get("cluster_id", f"Group {c_idx+1}"))[:12]
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{radius + 15}" fill="url(#clusterGlow)" stroke="#334155" stroke-dasharray="3,3" stroke-width="1.2"/>')
        svg.append(f'<text x="{cx}" y="{cy - radius - 20}" fill="#94a3b8" font-size="11" font-weight="bold" text-anchor="middle">{c_name}</text>')

        nodes = clus.get("nodes", [])[:7]
        n_nodes = len(nodes)
        node_coords = []

        for n_idx, node in enumerate(nodes):
            angle = (2 * math.pi * n_idx) / max(1, n_nodes)
            nx = cx + int((radius - 10) * math.cos(angle))
            ny = cy + int((radius - 10) * math.sin(angle))
            node_coords.append((nx, ny, node.get("state", "isolated_control")))

        # Connect intra-cluster edges
        for i in range(len(node_coords)):
            for j in range(i + 1, len(node_coords)):
                x1, y1, _ = node_coords[i]
                x2, y2, _ = node_coords[j]
                svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#334155" stroke-opacity="0.6" stroke-width="1"/>')

        # Draw nodes
        for nx, ny, st in node_coords:
            col = state_colors.get(st, "#64748b")
            svg.append(f'<circle cx="{nx}" cy="{ny}" r="8" fill="{col}" stroke="#ffffff" stroke-width="1.5"/>')

    # Bottom KPI Summary Card
    panel_y = height - 70
    sutva_text = "VIOLATED (p < .05)" if p_sutva < 0.05 else "UPHELD (p >= .05)"
    sutva_color = "#f43f5e" if p_sutva < 0.05 else "#10b981"

    svg.extend([
        f'<rect x="24" y="{panel_y}" width="{width - 48}" height="55" rx="6" fill="#1e293b" stroke="#334155" stroke-width="1"/>',
        f'<text x="40" y="{panel_y + 20}" fill="#94a3b8" font-size="10">AVERAGE DIRECT (ADE)</text>',
        f'<text x="40" y="{panel_y + 40}" fill="#3b82f6" font-size="14" font-weight="bold">{ade:+.3f}</text>',
        f'<text x="200" y="{panel_y + 20}" fill="#94a3b8" font-size="10">AVERAGE SPILLOVER (AIE)</text>',
        f'<text x="200" y="{panel_y + 40}" fill="#f59e0b" font-size="14" font-weight="bold">{aie:+.3f}</text>',
        f'<text x="380" y="{panel_y + 20}" fill="#94a3b8" font-size="10">TOTAL OVERALL (OTE)</text>',
        f'<text x="380" y="{panel_y + 40}" fill="#a855f7" font-size="14" font-weight="bold">{ote:+.3f}</text>',
        f'<text x="540" y="{panel_y + 20}" fill="#94a3b8" font-size="10">SPILLOVER SHARE</text>',
        f'<text x="540" y="{panel_y + 40}" fill="#38bdf8" font-size="14" font-weight="bold">{spillover_share:.1f}%</text>',
        f'<text x="700" y="{panel_y + 20}" fill="#94a3b8" font-size="10">SUTVA STATUS</text>',
        f'<text x="700" y="{panel_y + 40}" fill="{sutva_color}" font-size="13" font-weight="bold">{sutva_text}</text>',
    ])

    svg.append('</svg>')
    return '\n'.join(svg)


def run_network_spillover_analysis(
    df: pd.DataFrame,
    outcome_col: str,
    treatment_col: str,
    cluster_col: str,
    covariate_cols: Optional[List[str]] = None,
    spillover_threshold: float = 0.0,
    alpha_level: float = 0.05
) -> Dict[str, Any]:
    """
    Executes Causal Inference under Network Interference & Spillover Effects.
    """
    if df is None or len(df) == 0:
        return {"status": "ERROR", "message": "Input survey dataset is empty."}

    req_cols = [outcome_col, treatment_col, cluster_col]
    if covariate_cols:
        req_cols.extend(covariate_cols)

    missing = [c for c in req_cols if c not in df.columns]
    if missing:
        return {"status": "ERROR", "message": f"Missing required columns: {missing}"}

    sub_df = df[req_cols].dropna().copy()
    if len(sub_df) < 20:
        return {"status": "INSUFFICIENT_SAMPLE", "message": f"Sample size {len(sub_df)} is too small for network spillover analysis."}

    # Binarize treatment
    z_raw = sub_df[treatment_col].values
    if np.issubdtype(z_raw.dtype, np.number):
        unique_z = np.unique(z_raw)
        if len(unique_z) == 2 and set(unique_z).issubset({0, 1}):
            Z = z_raw.astype(float)
        else:
            med_z = float(np.median(z_raw))
            Z = (z_raw > med_z).astype(float)
    else:
        top_val = sub_df[treatment_col].mode().iloc[0]
        Z = (sub_df[treatment_col] == top_val).astype(float).values

    Y = sub_df[outcome_col].astype(float).values
    sub_df["_Z"] = Z
    sub_df["_Y"] = Y

    # Calculate peer neighborhood treatment share S_i for each unit
    peer_shares = []
    exposure_states = []

    for idx, row in sub_df.iterrows():
        c_id = row[cluster_col]
        cluster_rows = sub_df[sub_df[cluster_col] == c_id]
        n_c = len(cluster_rows)
        if n_c <= 1:
            # Single-node cluster, peer share is 0
            s_i = 0.0
        else:
            total_treated_cluster = float(cluster_rows["_Z"].sum())
            s_i = (total_treated_cluster - float(row["_Z"])) / (n_c - 1)
        
        peer_shares.append(s_i)

        z_i = int(row["_Z"])
        is_spill = (s_i > spillover_threshold)

        if z_i == 0 and not is_spill:
            st = "isolated_control"
        elif z_i == 1 and not is_spill:
            st = "direct_only"
        elif z_i == 0 and is_spill:
            st = "spillover_only"
        else:
            st = "joint_treated"

        exposure_states.append(st)

    sub_df["_peer_share"] = peer_shares
    sub_df["_exposure_state"] = exposure_states

    # Compute Potential Outcome Means by Exposure State
    groups = {
        "isolated_control": sub_df[sub_df["_exposure_state"] == "isolated_control"]["_Y"].values,
        "direct_only": sub_df[sub_df["_exposure_state"] == "direct_only"]["_Y"].values,
        "spillover_only": sub_df[sub_df["_exposure_state"] == "spillover_only"]["_Y"].values,
        "joint_treated": sub_df[sub_df["_exposure_state"] == "joint_treated"]["_Y"].values,
    }

    n_ctrl = len(groups["isolated_control"])
    n_dir = len(groups["direct_only"])
    n_spill = len(groups["spillover_only"])
    n_joint = len(groups["joint_treated"])

    mu_ctrl = float(np.mean(groups["isolated_control"])) if n_ctrl > 0 else 0.0
    mu_dir = float(np.mean(groups["direct_only"])) if n_dir > 0 else 0.0
    mu_spill = float(np.mean(groups["spillover_only"])) if n_spill > 0 else 0.0
    mu_joint = float(np.mean(groups["joint_treated"])) if n_joint > 0 else 0.0

    se_ctrl = float(stats.sem(groups["isolated_control"])) if n_ctrl > 1 else 0.1
    se_dir = float(stats.sem(groups["direct_only"])) if n_dir > 1 else 0.1
    se_spill = float(stats.sem(groups["spillover_only"])) if n_spill > 1 else 0.1
    se_joint = float(stats.sem(groups["joint_treated"])) if n_joint > 1 else 0.1

    # Causal Estimands
    # 1. Average Direct Effect (ADE)
    if n_dir > 0 and n_ctrl > 0:
        ade = mu_dir - mu_ctrl
        se_ade = math.sqrt(se_dir ** 2 + se_ctrl ** 2)
    elif n_joint > 0 and n_spill > 0:
        ade = mu_joint - mu_spill
        se_ade = math.sqrt(se_joint ** 2 + se_spill ** 2)
    else:
        # Pooled direct effect
        treated_mean = float(np.mean(sub_df[sub_df["_Z"] == 1]["_Y"])) if np.sum(Z) > 0 else 0.0
        untreated_mean = float(np.mean(sub_df[sub_df["_Z"] == 0]["_Y"])) if np.sum(1 - Z) > 0 else 0.0
        ade = treated_mean - untreated_mean
        se_ade = 0.1

    # 2. Average Spillover / Indirect Effect (AIE)
    if n_spill > 0 and n_ctrl > 0:
        aie = mu_spill - mu_ctrl
        se_aie = math.sqrt(se_spill ** 2 + se_ctrl ** 2)
    else:
        aie = 0.0
        se_aie = 0.1

    # 3. Overall Total Effect (OTE)
    if n_joint > 0 and n_ctrl > 0:
        ote = mu_joint - mu_ctrl
        se_ote = math.sqrt(se_joint ** 2 + se_ctrl ** 2)
    else:
        ote = ade + aie
        se_ote = math.sqrt(se_ade ** 2 + se_aie ** 2)

    # Hypothesis tests
    z_ade = ade / (se_ade + 1e-12)
    p_ade = float(2.0 * (1.0 - stats.norm.cdf(abs(z_ade))))

    z_aie = aie / (se_aie + 1e-12)
    p_aie = float(2.0 * (1.0 - stats.norm.cdf(abs(z_aie))))

    # SUTVA Sharp Null Test: Is Spillover Effect != 0?
    p_sutva = p_aie
    is_sutva_violated = bool(p_sutva < alpha_level and abs(aie) > 1e-4)

    # Spillover share of total effect
    denom_share = abs(ade) + abs(aie)
    spillover_share = float((abs(aie) / (denom_share + 1e-12)) * 100.0) if denom_share > 1e-6 else 0.0

    # Continuous Dosage Regression Model: Y = beta_0 + beta_direct * Z + beta_spill * S + gamma * X
    X_reg = [np.ones(len(sub_df)), Z, np.array(peer_shares)]
    cov_names = []
    if covariate_cols:
        for c in covariate_cols:
            c_vals = sub_df[c].astype(float).values
            X_reg.append((c_vals - np.mean(c_vals)) / (np.std(c_vals) + 1e-8))
            cov_names.append(c)

    X_mat = np.column_stack(X_reg)
    try:
        coef_reg, resids, _, _ = np.linalg.lstsq(X_mat, Y, rcond=None)
        residuals = Y - X_mat @ coef_reg
        dof = max(1, len(sub_df) - X_mat.shape[1])
        mse = np.sum(residuals ** 2) / dof
        inv_xx = np.linalg.inv(X_mat.T @ X_mat + 1e-6 * np.eye(X_mat.shape[1]))
        se_reg = np.sqrt(np.maximum(1e-12, np.diag(mse * inv_xx)))
    except Exception:
        coef_reg = np.zeros(X_mat.shape[1])
        se_reg = np.ones(X_mat.shape[1])

    dosage_regression = {
        "direct_coefficient": round(float(coef_reg[1]), 4),
        "direct_se": round(float(se_reg[1]), 4),
        "direct_pvalue": round(float(2.0 * (1.0 - stats.norm.cdf(abs(coef_reg[1] / (se_reg[1] + 1e-12))))), 4),
        "peer_spillover_slope": round(float(coef_reg[2]), 4),
        "spillover_se": round(float(se_reg[2]), 4),
        "spillover_pvalue": round(float(2.0 * (1.0 - stats.norm.cdf(abs(coef_reg[2] / (se_reg[2] + 1e-12))))), 4),
        "interpretation": (
            f"Tăng 10% tỷ lệ đồng nghiệp được can thiệp trong nhóm làm dịch chuyển kết quả thêm {coef_reg[2] * 0.1:+.3f} điểm."
        )
    }

    # Prepare cluster preview for SVG
    cluster_preview = []
    for c_id, group in sub_df.groupby(cluster_col):
        nodes_list = []
        for _, r in group.iterrows():
            nodes_list.append({"state": r["_exposure_state"]})
        cluster_preview.append({"cluster_id": c_id, "nodes": nodes_list})

    svg_viz = _generate_network_svg(
        clusters=cluster_preview,
        ade=ade,
        aie=aie,
        ote=ote,
        spillover_share=spillover_share,
        p_sutva=p_sutva
    )

    return {
        "status": "SUCCESS",
        "sample_size": len(sub_df),
        "n_clusters": int(sub_df[cluster_col].nunique()),
        "outcome_variable": outcome_col,
        "treatment_variable": treatment_col,
        "cluster_variable": cluster_col,
        "exposure_sample_sizes": {
            "isolated_control": n_ctrl,
            "direct_only": n_dir,
            "spillover_only": n_spill,
            "joint_treated": n_joint
        },
        "potential_outcome_means": {
            "isolated_control": round(mu_ctrl, 4),
            "direct_only": round(mu_dir, 4),
            "spillover_only": round(mu_spill, 4),
            "joint_treated": round(mu_joint, 4)
        },
        "average_direct_effect": {
            "estimate": round(ade, 4),
            "se": round(se_ade, 4),
            "z_stat": round(z_ade, 3),
            "p_value": round(p_ade, 4),
            "ci_95": [round(ade - 1.96 * se_ade, 4), round(ade + 1.96 * se_ade, 4)]
        },
        "average_spillover_effect": {
            "estimate": round(aie, 4),
            "se": round(se_aie, 4),
            "z_stat": round(z_aie, 3),
            "p_value": round(p_aie, 4),
            "ci_95": [round(aie - 1.96 * se_aie, 4), round(aie + 1.96 * se_aie, 4)]
        },
        "total_overall_effect": {
            "estimate": round(ote, 4),
            "se": round(se_ote, 4),
            "ci_95": [round(ote - 1.96 * se_ote, 4), round(ote + 1.96 * se_ote, 4)]
        },
        "spillover_share_pct": round(spillover_share, 2),
        "sutva_test": {
            "is_violated": is_sutva_violated,
            "p_value": round(p_sutva, 4),
            "verdict": (
                "VI PHẠM SUTVA (Phát hiện hiệu ứng lan truyền đồng nghiệp có ý nghĩa thống kê p < 0.05)"
                if is_sutva_violated else
                "SUTVA THỎA MÃN (Không phát hiện bằng chứng lan truyền đáng kể giữa các đồng nghiệp p >= 0.05)"
            )
        },
        "dosage_regression": dosage_regression,
        "svg_visualization": svg_viz
    }
