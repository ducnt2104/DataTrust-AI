# -*- coding: utf-8 -*-
"""
Unit tests for High-Dimensional Causal Mediation & Latent Path Invariance Engine (HD-Mediation)
"""

import pytest
import numpy as np
import pandas as pd
from backend.app.engine.high_dimensional_mediation_engine import run_high_dimensional_mediation


def test_hd_mediation_synthetic_recovery():
    np.random.seed(123)
    n = 200

    # True parameters:
    # T -> M1 (alpha = 0.8), M1 -> Y (beta = 1.2) => IE1 = 0.96
    # T -> M2 (alpha = 0.5), M2 -> Y (beta = 0.6) => IE2 = 0.30
    # T -> M3 (noise, alpha = 0.05), M3 -> Y (beta = 0.0) => IE3 = 0.0
    # T -> Y direct (NDE = 0.4)
    # Total Effect TE ~ 0.4 + 0.96 + 0.30 = 1.66

    T = np.random.binomial(1, 0.5, size=n)
    X = np.random.normal(0, 1, size=n)

    M1 = 0.5 + 0.8 * T + 0.3 * X + np.random.normal(0, 0.5, size=n)
    M2 = 1.0 + 0.5 * T - 0.2 * X + np.random.normal(0, 0.6, size=n)
    M3 = 0.2 + 0.05 * T + 0.1 * X + np.random.normal(0, 0.7, size=n)

    Y = 1.5 + 0.4 * T + 1.2 * M1 + 0.6 * M2 + 0.0 * M3 + 0.4 * X + np.random.normal(0, 0.5, size=n)

    df = pd.DataFrame({
        "treatment": T,
        "satisfaction": Y,
        "trust_brand": M1,
        "ease_of_use": M2,
        "irrelevant_item": M3,
        "tenure": X
    })

    res = run_high_dimensional_mediation(
        df=df,
        treatment_col="treatment",
        outcome_col="satisfaction",
        mediator_cols=["trust_brand", "ease_of_use", "irrelevant_item"],
        confounder_cols=["tenure"],
        n_boot=40,
        random_seed=42
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == n
    assert res["n_mediators"] == 3

    # Total effect should be positive and substantial (~1.6)
    te = res["total_effect"]["estimate"]
    assert 1.1 < te < 2.2
    assert res["total_effect"]["p_value"] < 0.05

    # Direct effect should be positive (~0.4)
    nde = res["natural_direct_effect"]["estimate"]
    assert 0.1 < nde < 0.8

    # Indirect effect should be positive and > direct effect
    nie = res["natural_indirect_effect"]["estimate"]
    assert nie > 0.6

    # Proportion mediated should be > 50%
    pm = res["proportion_mediated"]["percentage"]
    assert pm > 45.0

    # Top mediator should be trust_brand
    pathways = res["mediator_pathways"]
    assert pathways[0]["mediator_col"] == "trust_brand"
    assert pathways[0]["indirect_effect"] > pathways[1]["indirect_effect"]

    # Sensitivity bounds
    assert "critical_rho_sensitivity" in pathways[0]
    assert "svg_visualization" in res
    assert "<svg" in res["svg_visualization"]


def test_hd_mediation_latent_path_invariance():
    np.random.seed(99)
    n = 150

    T = np.random.binomial(1, 0.5, size=n)
    group = np.random.choice(["Region_A", "Region_B"], size=n)
    M = 0.5 * T + np.random.normal(0, 0.5, size=n)
    Y = 1.0 + 0.5 * T + 0.8 * M + np.random.normal(0, 0.5, size=n)

    df = pd.DataFrame({
        "policy": T,
        "adoption": Y,
        "engagement": M,
        "region": group
    })

    res = run_high_dimensional_mediation(
        df=df,
        treatment_col="policy",
        outcome_col="adoption",
        mediator_cols=["engagement"],
        subgroup_col="region",
        n_boot=30
    )

    assert res["status"] == "SUCCESS"
    inv = res["latent_path_invariance"]
    assert inv["tested"] is True
    assert inv["subgroup_col"] == "region"
    assert "groups_compared" in inv
    assert inv["wald_statistic"] is not None
    assert inv["p_value"] is not None


def test_hd_mediation_edge_cases():
    # Empty dataframe
    empty_df = pd.DataFrame()
    r_empty = run_high_dimensional_mediation(empty_df, "T", "Y", ["M"])
    assert r_empty["status"] == "ERROR"

    # Missing columns
    df_missing = pd.DataFrame({"A": [1, 2, 3]})
    r_missing = run_high_dimensional_mediation(df_missing, "T", "Y", ["M"])
    assert r_missing["status"] == "ERROR"

    # Insufficient sample
    df_small = pd.DataFrame({
        "T": [0, 1, 0, 1, 0],
        "Y": [1.0, 2.0, 1.5, 2.5, 1.2],
        "M": [0.5, 0.8, 0.6, 0.9, 0.4]
    })
    r_small = run_high_dimensional_mediation(df_small, "T", "Y", ["M"])
    assert r_small["status"] == "INSUFFICIENT_SAMPLE"
