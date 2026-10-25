# -*- coding: utf-8 -*-
"""
Unit tests for StochasticFrontierEngine (backend/app/engine/stochastic_frontier_engine.py)
"""
import pytest
import numpy as np
from app.engine.stochastic_frontier_engine import StochasticFrontierEngine


def test_sfa_insufficient_sample():
    res = StochasticFrontierEngine.estimate(
        data=[{"out": 10.0, "inp": 5.0}],
        output_var="out",
        input_vars=["inp"]
    )
    assert res["status"] in ["INSUFFICIENT_DATA", "INSUFFICIENT_VALID_SAMPLE"]


def test_sfa_estimation_end_to_end():
    np.random.seed(42)
    n = 100
    # Inputs: Capital K, Labor L
    k = np.random.uniform(5.0, 50.0, n)
    l = np.random.uniform(10.0, 100.0, n)

    # True error terms: v ~ N(0, 0.15^2), u ~ Half-Normal(0, 0.35^2)
    v = np.random.normal(0, 0.15, n)
    u = np.abs(np.random.normal(0, 0.35, n))

    # Production frontier: ln Y = 1.2 + 0.5 ln K + 0.5 ln L + v - u
    ln_y = 1.2 + 0.5 * np.log(k) + 0.5 * np.log(l) + v - u
    y = np.exp(ln_y)

    data = [
        {"output_y": float(y[i]), "capital_k": float(k[i]), "labor_l": float(l[i])}
        for i in range(n)
    ]

    res = StochasticFrontierEngine.estimate(
        data=data,
        output_var="output_y",
        input_vars=["capital_k", "labor_l"],
        log_transform=True
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "STOCHASTIC_FRONTIER_ANALYSIS"

    diag = res["diagnostics"]
    assert diag["n_units"] == 100
    assert diag["n_inputs"] == 2
    assert diag["converged"] is True
    assert diag["lambda_ratio"] > 0.5
    assert diag["gamma_variance_share"] > 0.2
    assert diag["mean_technical_efficiency_pct"] > 50.0
    assert diag["mean_technical_efficiency_pct"] <= 100.0

    # Check coefficients
    coeffs = res["coefficients"]
    assert len(coeffs) == 3  # Intercept + K + L
    k_item = next(c for c in coeffs if c["variable"] == "capital_k")
    l_item = next(c for c in coeffs if c["variable"] == "labor_l")
    assert abs(k_item["elasticity_estimate"] - 0.5) < 0.3
    assert abs(l_item["elasticity_estimate"] - 0.5) < 0.3

    # Check individual efficiency
    sample_eff = res["individual_efficiency_sample"]
    assert len(sample_eff) > 0
    for eff in sample_eff:
        assert 1.0 <= eff["technical_efficiency_pct"] <= 100.0

    # Check SVG and narrative
    assert "<svg" in res["svg_visualization"]
    assert "Stochastic Frontier" in res["apa_narrative"]
    assert "JLMS" in res["apa_narrative"]


def test_sfa_linear_specification():
    np.random.seed(123)
    n = 60
    x = np.random.uniform(10.0, 50.0, n)
    v = np.random.normal(0, 1.0, n)
    u = np.abs(np.random.normal(0, 2.0, n))
    y = 5.0 + 2.0 * x + v - u

    data = [{"y_score": float(y[i]), "x_resource": float(x[i])} for i in range(n)]

    res = StochasticFrontierEngine.estimate(
        data=data,
        output_var="y_score",
        input_vars=["x_resource"],
        log_transform=False
    )

    assert res["status"] == "SUCCESS"
    assert res["diagnostics"]["log_transformed"] is False
    assert len(res["coefficients"]) == 2
