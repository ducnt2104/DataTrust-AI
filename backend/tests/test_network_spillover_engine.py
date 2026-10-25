# -*- coding: utf-8 -*-
"""
Unit tests for Causal Inference with Network Interference & Peer Spillover Effects Engine (Network SUTVA)
"""

import pytest
import numpy as np
import pandas as pd
from backend.app.engine.network_spillover_engine import run_network_spillover_analysis


def test_network_spillover_synthetic_recovery():
    np.random.seed(42)
    n_teams = 12
    team_size = 6

    records = []
    for team_id in range(n_teams):
        # Assign varying treatment saturation per team
        prob_treat = 0.6 if team_id % 2 == 0 else 0.2
        treatments = np.random.binomial(1, prob_treat, size=team_size)
        
        for member_id in range(team_size):
            z_i = treatments[member_id]
            peer_share = (np.sum(treatments) - z_i) / (team_size - 1)

            # True model: Y = 10 + 4.0*Z + 6.0*PeerShare + N(0, 0.4)
            y_i = 10.0 + 4.0 * z_i + 6.0 * peer_share + np.random.normal(0, 0.4)

            records.append({
                "team": f"Team_{team_id + 1}",
                "treated": z_i,
                "performance": y_i,
                "tenure": np.random.normal(3, 1)
            })

    df = pd.DataFrame(records)

    res = run_network_spillover_analysis(
        df=df,
        outcome_col="performance",
        treatment_col="treated",
        cluster_col="team",
        covariate_cols=["tenure"],
        spillover_threshold=0.0
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == n_teams * team_size
    assert res["n_clusters"] == n_teams

    # Check direct effect ADE (~4.0)
    ade = res["average_direct_effect"]["estimate"]
    assert 2.0 < ade < 6.0

    # Check spillover effect AIE (~positive)
    aie = res["average_spillover_effect"]["estimate"]
    assert aie > 0.5

    # Check SUTVA violation test: Should be violated
    assert res["sutva_test"]["is_violated"] is True
    assert res["sutva_test"]["p_value"] < 0.05

    # Dosage regression slope
    slope = res["dosage_regression"]["peer_spillover_slope"]
    assert 3.0 < slope < 9.0

    # SVG diagram
    assert "svg_visualization" in res
    assert "<svg" in res["svg_visualization"]


def test_network_spillover_edge_cases():
    # Empty df
    empty_df = pd.DataFrame()
    r1 = run_network_spillover_analysis(empty_df, "Y", "Z", "cluster")
    assert r1["status"] == "ERROR"

    # Missing column
    df = pd.DataFrame({"Y": [1, 2], "Z": [0, 1]})
    r2 = run_network_spillover_analysis(df, "Y", "Z", "cluster")
    assert r2["status"] == "ERROR"

    # Small sample
    df_small = pd.DataFrame({
        "Y": [1.0, 2.0, 3.0, 4.0],
        "Z": [0, 1, 0, 1],
        "cluster": ["A", "A", "B", "B"]
    })
    r3 = run_network_spillover_analysis(df_small, "Y", "Z", "cluster")
    assert r3["status"] == "INSUFFICIENT_SAMPLE"
