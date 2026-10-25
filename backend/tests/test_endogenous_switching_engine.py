# -*- coding: utf-8 -*-
"""
Unit tests for EndogenousSwitchingEngine (ESR - Maddala 1983; Lokshin & Sajaia 2004)
"""
import pytest
import numpy as np
from app.engine.endogenous_switching_engine import EndogenousSwitchingEngine


def test_esr_insufficient_sample():
    res = EndogenousSwitchingEngine.estimate(
        data=[{"t": 1, "y": 10.0, "x": 5.0}],
        treatment_var="t",
        outcome_var="y",
        covariates=["x"]
    )
    assert res["status"] in ["INSUFFICIENT_DATA", "INSUFFICIENT_VALID_SAMPLE"]


def test_esr_estimation_end_to_end():
    np.random.seed(42)
    n = 120

    # Covariate X (e.g. experience)
    x = np.random.uniform(1.0, 10.0, n)
    # Instrumental variable Z (e.g. distance to training center / voucher)
    z_inst = np.random.normal(0, 1.0, n)

    # Trivariate normal errors: (u, e1, e0)
    # Correlation rho1 = 0.5, rho0 = -0.3
    cov_errors = np.array([
        [1.0, 0.5 * 1.5, -0.3 * 1.2],
        [0.5 * 1.5, 1.5**2, 0.2],
        [-0.3 * 1.2, 0.2, 1.2**2]
    ])
    errors = np.random.multivariate_normal([0, 0, 0], cov_errors, size=n)
    u = errors[:, 0]
    e1 = errors[:, 1]
    e0 = errors[:, 2]

    # Selection equation: I* = -0.2 + 0.3 * X + 0.8 * Z + u
    i_star = -0.2 + 0.3 * x + 0.8 * z_inst + u
    t_treat = np.where(i_star > 0, 1, 0)

    # Outcome equations:
    # Y1 = 5.0 + 1.2 * X + e1
    # Y0 = 3.0 + 0.8 * X + e0
    y1 = 5.0 + 1.2 * x + e1
    y0 = 3.0 + 0.8 * x + e0

    # Observed outcome:
    y_obs = np.where(t_treat == 1, y1, y0)

    data = [
        {
            "training_adopted": int(t_treat[i]),
            "wage_income": float(y_obs[i]),
            "experience_years": float(x[i]),
            "distance_voucher": float(z_inst[i])
        }
        for i in range(n)
    ]

    res = EndogenousSwitchingEngine.estimate(
        data=data,
        treatment_var="training_adopted",
        outcome_var="wage_income",
        covariates=["experience_years"],
        instruments=["distance_voucher"]
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "ENDOGENOUS_SWITCHING_REGRESSION_FIML"

    diag = res["diagnostics"]
    assert diag["total_sample"] == 120
    assert diag["regime1_count"] > 15
    assert diag["regime0_count"] > 15
    assert diag["converged"] is True
    assert "rho_1_treated_selection" in diag
    assert "rho_0_untreated_selection" in diag
    assert "lr_test_independence_stat" in diag

    # Treatment effects
    te = res["treatment_effects"]
    assert "att" in te
    assert "atu" in te
    assert "transitional_heterogeneity" in te
    assert te["att"]["estimate"] > 0.5  # Positive effect of training on wage
    assert te["att"]["standard_error"] > 0

    # Coefficients
    coeffs = res["coefficients"]
    assert len(coeffs) == 2  # Intercept + experience_years
    exp_item = next(c for c in coeffs if c["variable"] == "experience_years")
    assert exp_item["regime1_estimate"] > 0.5
    assert exp_item["regime0_estimate"] > 0.3

    # SVG & APA Narrative
    assert "<svg" in res["svg_visualization"]
    assert "Endogenous Switching Regression" in res["apa_narrative"]
    assert "ATT" in res["apa_narrative"]
