# -*- coding: utf-8 -*-
"""
Unit tests for FractionalResponseEngine (backend/app/engine/fractional_response_engine.py)
"""
import pytest
import numpy as np
from app.engine.fractional_response_engine import FractionalResponseEngine


def test_fractional_response_insufficient_sample():
    # Few rows
    res = FractionalResponseEngine.estimate(
        data=[{"rate": 0.5, "x": 1.0}],
        outcome_var="rate",
        covariate_vars=["x"]
    )
    assert res["status"] == "INSUFFICIENT_DATA"

    # Missing covariates
    res2 = FractionalResponseEngine.estimate(
        data=[{"rate": 0.5}] * 20,
        outcome_var="rate",
        covariate_vars=[]
    )
    assert res2["status"] == "MISSING_COVARIATES"


def test_fractional_logit_estimation_and_ame():
    np.random.seed(42)
    n = 100
    x1 = np.random.normal(0, 1.5, n)
    x2 = np.random.uniform(-2, 2, n)

    # True data generating process: logit link
    z = -0.5 + 0.8 * x1 - 0.6 * x2
    prob = 1.0 / (1.0 + np.exp(-z))
    # Some true mass points at 0 and 1 plus continuous rates
    rates = np.clip(prob + np.random.normal(0, 0.1, n), 0.0, 1.0)
    # Force some exact 0s and 1s
    rates[rates < 0.08] = 0.0
    rates[rates > 0.92] = 1.0

    data = [
        {"y_rate": float(rates[i]), "feat1": float(x1[i]), "feat2": float(x2[i])}
        for i in range(n)
    ]

    res = FractionalResponseEngine.estimate(
        data=data,
        outcome_var="y_rate",
        covariate_vars=["feat1", "feat2"],
        link="logit"
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "FRACTIONAL_RESPONSE_QMLE"

    diag = res["diagnostics"]
    assert diag["n_samples"] == 100
    assert diag["n_covariates"] == 2
    assert diag["converged"] is True
    assert diag["boundary_zeros"] > 0 or diag["boundary_ones"] > 0
    assert diag["mcfadden_pseudo_r2"] > 0.0
    assert diag["qmle_rmse"] < 0.5

    coeffs = res["coefficients"]
    assert len(coeffs) == 3  # Intercept + 2 covariates
    # feat1 should have positive estimate and AME
    f1 = next(c for c in coeffs if c["variable"] == "feat1")
    assert f1["estimate"] > 0.3
    assert f1["average_marginal_effect"] > 0.05
    assert f1["robust_se"] > 0.0

    # feat2 should have negative estimate and AME
    f2 = next(c for c in coeffs if c["variable"] == "feat2")
    assert f2["estimate"] < -0.2
    assert f2["average_marginal_effect"] < -0.05

    # Check SVG and narrative
    assert "<svg" in res["svg_visualization"]
    assert "Papke & Wooldridge" in res["apa_narrative"]
    assert "Average Marginal Effect" in res["apa_narrative"]


def test_fractional_probit_and_cloglog_links():
    np.random.seed(123)
    n = 60
    x = np.random.uniform(1, 10, n)
    # Outcome in percentage 0 - 100%
    pct = np.clip((x * 8.0) + np.random.normal(0, 5, n), 0.0, 100.0)

    data = [{"pct_score": float(pct[i]), "study_hours": float(x[i])} for i in range(n)]

    # Probit
    res_probit = FractionalResponseEngine.estimate(
        data=data,
        outcome_var="pct_score",
        covariate_vars=["study_hours"],
        link="probit",
        scale_from_percentage=True
    )
    assert res_probit["status"] == "SUCCESS"
    assert res_probit["diagnostics"]["link_function"] == "probit"

    # Complementary log-log
    res_cloglog = FractionalResponseEngine.estimate(
        data=data,
        outcome_var="pct_score",
        covariate_vars=["study_hours"],
        link="cloglog",
        scale_from_percentage=True
    )
    assert res_cloglog["status"] == "SUCCESS"
    assert res_cloglog["diagnostics"]["link_function"] == "cloglog"
