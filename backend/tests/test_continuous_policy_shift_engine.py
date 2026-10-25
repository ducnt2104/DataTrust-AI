# -*- coding: utf-8 -*-
"""
Unit tests for Continuous Policy Shift & Doubly Robust Nonparametric Dosage Response Engine
"""

import pytest
import numpy as np
import pandas as pd
from backend.app.engine.continuous_policy_shift_engine import run_continuous_policy_shift


def test_continuous_policy_shift_synthetic_recovery():
    np.random.seed(42)
    N = 120

    x1 = np.random.normal(0, 1.0, size=N)
    x2 = np.random.normal(0, 1.0, size=N)

    # Treatment continuous dosage: range ~ 5 to 25
    a = 15.0 + 2.5 * x1 - 1.8 * x2 + np.random.normal(0, 2.0, size=N)

    # Nonlinear response: Peak around a = 18.0
    # Y = 40.0 + 3.6 * A - 0.1 * A^2 + 1.5 * x1 + N(0, 0.8)
    y = 40.0 + 3.6 * a - 0.1 * (a ** 2) + 1.5 * x1 + np.random.normal(0, 0.8, size=N)

    df = pd.DataFrame({
        "voucher_amount": a,
        "satisfaction_score": y,
        "tenure": x1,
        "income_tier": x2
    })

    res = run_continuous_policy_shift(
        df=df,
        outcome_col="satisfaction_score",
        treatment_col="voucher_amount",
        covariate_cols=["tenure", "income_tier"],
        grid_points=20,
        shift_delta=2.0
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == N
    assert len(res["dose_response_curve"]) == 20

    # Policy shift
    ps = res["policy_shift"]
    assert ps["delta_shift"] == 2.0
    assert "average_policy_effect" in ps
    assert "ci_95" in ps

    # Support & optimal dosage
    supp = res["treatment_support"]
    assert "current_mean" in supp
    assert "optimal_dosage" in supp
    assert supp["min_evaluated"] < supp["max_evaluated"]

    # SVG diagram
    assert "svg_visualization" in res
    assert "<svg" in res["svg_visualization"]


def test_continuous_policy_shift_edge_cases():
    # Empty df
    empty_df = pd.DataFrame()
    r1 = run_continuous_policy_shift(empty_df, "Y", "A")
    assert r1["status"] == "ERROR"

    # Missing column
    df = pd.DataFrame({"Y": [1, 2], "X": [3, 4]})
    r2 = run_continuous_policy_shift(df, "Y", "A")
    assert r2["status"] == "ERROR"

    # Zero variance treatment
    df_const = pd.DataFrame({
        "Y": np.random.normal(10, 1, size=40),
        "A": np.full(40, 5.0)
    })
    r3 = run_continuous_policy_shift(df_const, "Y", "A")
    assert r3["status"] == "ERROR"

    # Small sample
    df_small = pd.DataFrame({
        "Y": [1.0, 2.0, 3.0],
        "A": [5.0, 6.0, 7.0]
    })
    r4 = run_continuous_policy_shift(df_small, "Y", "A")
    assert r4["status"] == "INSUFFICIENT_SAMPLE"
