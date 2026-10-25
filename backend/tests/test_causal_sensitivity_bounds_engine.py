"""
Tests for Nonparametric Copula Causal Sensitivity Bounds Engine
DataTrust Iteration 177
"""

import pytest
import numpy as np
from app.engine.causal_sensitivity_bounds_engine import run_causal_sensitivity_bounds


def test_causal_sensitivity_bounds_estimation_success():
    np.random.seed(42)
    records = []

    # Generate 120 survey observations
    # Y = 4.0 * D + 1.5 * X1 + 0.8 * X2 + normal(0, 1)
    for _ in range(120):
        x1 = float(np.random.normal(10, 2))
        x2 = float(np.random.normal(5, 1.5))
        prob_d = 1.0 / (1.0 + np.exp(-(0.2 * x1 - 0.1 * x2)))
        d = 1.0 if np.random.uniform(0, 1) < prob_d else 0.0
        y = float(4.0 * d + 1.5 * x1 + 0.8 * x2 + np.random.normal(0, 1.0))

        records.append({"treatment": d, "outcome": y, "x1": x1, "x2": x2})

    res = run_causal_sensitivity_bounds(
        records=records,
        treatment_col="treatment",
        outcome_col="outcome",
        covariate_cols=["x1", "x2"],
        alpha_level=0.05
    )

    assert res["status"] == "success"
    assert res["sample_size"] == 120
    assert res["degrees_of_freedom"] == 120 - 4

    base = res["baseline_estimates"]
    assert 3.2 <= base["tau_hat"] <= 4.8
    assert base["t_statistic"] > 2.0
    assert base["p_value"] < 0.05
    assert base["partial_r2_treatment"] > 0.0

    rv = res["robustness_values"]
    assert rv["rv_q_to_zero"] > 0.10
    assert rv["rv_alpha_significance"] > 0.0
    assert rv["robustness_tier"] in ["HIGHLY_ROBUST", "MODERATELY_ROBUST"]

    benchmarks = res["covariate_benchmarks"]
    assert len(benchmarks) == 2
    assert "x1" in [b["name"] for b in benchmarks]

    wc = res["worst_case_curve"]
    assert len(wc) > 5

    copula = res["copula_tail_bounds"]
    assert "kendall_tau" in copula

    assert "<svg" in res["svg_visualization"]
    assert "Cinelli & Hazlett" in res["apa_narrative"]


def test_causal_sensitivity_bounds_insufficient_sample():
    records = [{"treatment": 1.0, "outcome": 5.0, "x1": 2.0} for _ in range(5)]
    res = run_causal_sensitivity_bounds(
        records=records,
        treatment_col="treatment",
        outcome_col="outcome",
        covariate_cols=["x1"]
    )
    assert res["status"] == "insufficient_data"


def test_causal_sensitivity_bounds_zero_variance():
    records = [{"treatment": 1.0, "outcome": 10.0, "x1": float(i)} for i in range(25)]
    res = run_causal_sensitivity_bounds(
        records=records,
        treatment_col="treatment",
        outcome_col="outcome",
        covariate_cols=["x1"]
    )
    assert res["status"] == "zero_variance"
