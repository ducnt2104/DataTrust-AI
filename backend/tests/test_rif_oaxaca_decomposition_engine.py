"""
Unit tests for Recentered Influence Function (RIF) Oaxaca-Blinder Decomposition Engine
DataTrust Iteration 173
"""

import pytest
import numpy as np
from app.engine.rif_oaxaca_decomposition_engine import (
    compute_rif_quantile,
    run_rif_oaxaca_decomposition
)


def test_compute_rif_quantile_mathematical_property():
    np.random.seed(42)
    y = np.random.normal(50, 10, size=200)
    for tau in [0.10, 0.25, 0.50, 0.75, 0.90]:
        q_tau, rif, f_q = compute_rif_quantile(y, tau)
        # Fundamental property of Influence Function: E[RIF(Y; q_tau)] == q_tau
        assert abs(np.mean(rif) - q_tau) < 1e-9
        assert f_q > 0


def test_run_rif_oaxaca_decomposition_end_to_end():
    np.random.seed(123)
    # Generate 100 observations for Group 1 and 100 observations for Group 0
    records = []
    for i in range(100):
        # Group 1: higher education and experience, higher intercept
        edu = np.random.normal(16, 2)
        exp = np.random.normal(10, 3)
        y1 = 25.0 + 3.0 * edu + 1.2 * exp + np.random.normal(0, 2)
        records.append({
            "group": "1",
            "education": round(float(edu), 2),
            "experience": round(float(exp), 2),
            "wage": round(float(y1), 2)
        })

    for i in range(100):
        # Group 0: lower education and experience, lower intercept
        edu = np.random.normal(13, 2)
        exp = np.random.normal(7, 3)
        y0 = 20.0 + 2.2 * edu + 0.9 * exp + np.random.normal(0, 2)
        records.append({
            "group": "0",
            "education": round(float(edu), 2),
            "experience": round(float(exp), 2),
            "wage": round(float(y0), 2)
        })

    res = run_rif_oaxaca_decomposition(
        records=records,
        group_col="group",
        outcome_col="wage",
        covariate_cols=["education", "experience"],
        reference_group_val="1",
        num_bootstrap_reps=30
    )

    assert res["status"] == "success"
    assert res["sample_size"] == 200
    assert res["group_a_label"] == "1"
    assert res["group_b_label"] == "0"
    assert res["sample_counts"]["group_a_n"] == 100
    assert res["sample_counts"]["group_b_n"] == 100

    # Mean decomposition
    mean_decomp = res["mean_decomposition"]
    assert mean_decomp["total_mean_gap"] > 10.0
    assert mean_decomp["explained_endowments"] > 0
    assert mean_decomp["unexplained_coefficients"] > 0
    # Identity: Total Gap == Explained + Unexplained
    sum_parts = mean_decomp["explained_endowments"] + mean_decomp["unexplained_coefficients"]
    assert abs(mean_decomp["total_mean_gap"] - sum_parts) < 1e-3

    # Median RIF estimates
    med = res["median_rif_estimates"]
    assert med["total_median_gap"] > 10.0
    assert med["unexplained_se"] > 0
    assert med["is_significant"] is True

    # Quantile decomposition curve
    curve = res["quantile_decomposition_curve"]
    assert len(curve) == 5
    for q_pt in curve:
        assert q_pt["quantile"] in [0.10, 0.25, 0.50, 0.75, 0.90]
        # Total == Explained + Unexplained
        assert abs(q_pt["total_gap"] - (q_pt["explained_gap"] + q_pt["unexplained_gap"])) < 1e-3

    assert len(res["detailed_covariates"]) == 3 # Intercept, education, experience
    assert "<svg" in res["svg_visualization"]
    assert "Firpo" in res["apa_narrative"]


def test_rif_oaxaca_insufficient_sample():
    records = [{"group": "A", "wage": 100, "x": 10}]
    res = run_rif_oaxaca_decomposition(
        records=records,
        group_col="group",
        outcome_col="wage",
        covariate_cols=["x"]
    )
    assert res["status"] == "error"
    assert "quá ít" in res["message"]


def test_rif_oaxaca_single_group():
    records = [{"group": "A", "wage": 100 + i, "x": 10} for i in range(40)]
    res = run_rif_oaxaca_decomposition(
        records=records,
        group_col="group",
        outcome_col="wage",
        covariate_cols=["x"]
    )
    assert res["status"] == "error"
    assert "chỉ có 1 giá trị" in res["message"]
