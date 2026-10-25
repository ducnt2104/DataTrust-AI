# -*- coding: utf-8 -*-
"""
Unit tests for Factor Instrumental Variables & PC-2SLS Engine (Bai & Ng 2010 Econometrica).
"""

import pytest
import numpy as np
import pandas as pd
from app.engine.factor_iv_engine import estimate_factor_iv, _select_bai_ng_factors


def test_select_bai_ng_factors_synthetic():
    np.random.seed(42)
    N = 100
    # True latent factors: 2 factors
    F_true = np.random.normal(0, 1, size=(N, 2))
    # 8 candidate instruments generated from the 2 factors + small noise
    Lambda_true = np.random.normal(0, 1, size=(8, 2))
    Z = F_true @ Lambda_true.T + np.random.normal(0, 0.2, size=(N, 8))
    Z_std = (Z - np.mean(Z, axis=0)) / np.std(Z, axis=0)

    r_star, factors, loadings, criteria_table = _select_bai_ng_factors(Z_std, max_factors=5)
    assert r_star in [1, 2, 3]
    assert factors.shape == (N, r_star)
    assert loadings.shape == (8, r_star)
    assert len(criteria_table) >= 3


def test_estimate_factor_iv_full_pipeline():
    np.random.seed(101)
    N = 120
    # 2 true latent factor instruments
    F1 = np.random.normal(0, 1, N)
    F2 = np.random.normal(0, 1, N)

    # 6 candidate survey instruments loading on F1 and F2
    records = []
    # Confounder U influencing both D and Y
    U = np.random.normal(0, 1, N)

    for i in range(N):
        rec = {}
        # Instruments
        rec["z1"] = 0.8 * F1[i] + np.random.normal(0, 0.3)
        rec["z2"] = 0.7 * F1[i] + np.random.normal(0, 0.3)
        rec["z3"] = 0.9 * F1[i] + np.random.normal(0, 0.3)
        rec["z4"] = 0.8 * F2[i] + np.random.normal(0, 0.3)
        rec["z5"] = 0.7 * F2[i] + np.random.normal(0, 0.3)
        rec["z6"] = 0.6 * F2[i] + np.random.normal(0, 0.3)
        
        # Endogenous treatment D (true effect = 3.0)
        # Strongly influenced by F1 and U
        d_val = 1.2 * F1[i] + 0.8 * F2[i] + 1.5 * U[i] + np.random.normal(0, 0.4)
        rec["d"] = d_val
        
        # Outcome Y = 3.0 * D + 2.0 * U + noise
        # Note: OLS will be biased upwards due to U
        y_val = 3.0 * d_val + 2.0 * U[i] + np.random.normal(0, 0.5)
        rec["y"] = y_val
        records.append(rec)

    df = pd.DataFrame(records)

    res = estimate_factor_iv(
        df=df,
        outcome_col="y",
        treatment_col="d",
        instrument_cols=["z1", "z2", "z3", "z4", "z5", "z6"]
    )

    assert res["status"] == "SUCCESS"
    summary = res["overall_summary"]
    assert summary["sample_size"] == N
    assert summary["n_candidate_instruments_K"] == 6
    assert summary["n_factors_r"] >= 1
    assert summary["first_stage_f_statistic"] > 10.0  # Strong instrument
    # Factor IV cleanly identifies causal effect ~ 3.0 (within 0.6 margin)
    assert abs(summary["beta_factor_iv"] - 3.0) < 0.6
    # OLS is confounded (~ 3.0 + bias > 3.4)
    assert summary["beta_ols_baseline"] > summary["beta_factor_iv"]
    assert len(res["factor_summaries"]) == summary["n_factors_r"]
    assert len(res["instrument_loadings"]) == 6
    assert "<svg" in res["svg_visualization"]
    assert "Factor Instrumental Variables" in res["apa_narrative"]


def test_estimate_factor_iv_edge_cases():
    df_small = pd.DataFrame({"y": [1, 2], "d": [1, 0], "z1": [0.1, 0.2]})
    with pytest.raises(ValueError, match="at least 2 candidate instruments"):
        estimate_factor_iv(df_small, "y", "d", ["z1"])
