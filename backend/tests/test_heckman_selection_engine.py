# -*- coding: utf-8 -*-
"""
Unit tests for HeckmanSelectionEngine (backend/app/engine/heckman_selection_engine.py)
"""
import pytest
import numpy as np
from app.engine.heckman_selection_engine import HeckmanSelectionEngine


def test_heckman_insufficient_sample():
    res = HeckmanSelectionEngine.estimate(
        data=[{"s": 1, "y": 10.0, "x": 1.0}],
        selection_indicator_var="s",
        outcome_var="y",
        outcome_covariates=["x"]
    )
    assert res["status"] in ["INSUFFICIENT_DATA", "INSUFFICIENT_VALID_SAMPLE"]


def test_heckman_estimation_with_selection_bias():
    np.random.seed(42)
    n = 120
    # Covariate X and Exclusion Restriction Instrument Z
    x = np.random.normal(0, 1.0, n)
    z_excl = np.random.normal(0, 1.2, n)

    # Correlated errors: u (selection) and e (outcome) with true rho = 0.7
    mean_err = [0, 0]
    cov_err = [[1.0, 0.7 * 1.5], [0.7 * 1.5, 1.5 ** 2]]
    errors = np.random.multivariate_normal(mean_err, cov_err, n)
    u = errors[:, 0]
    e = errors[:, 1]

    # Selection equation: S* = 0.2 + 0.8 * x + 1.2 * z_excl + u
    s_star = 0.2 + 0.8 * x + 1.2 * z_excl + u
    s = (s_star > 0).astype(int)

    # Outcome equation: Y = 2.0 + 1.5 * x + e (true beta = 1.5)
    y_full = 2.0 + 1.5 * x + e

    data = []
    for i in range(n):
        row = {
            "participated": int(s[i]),
            "income_x": float(x[i]),
            "invitation_mode_z": float(z_excl[i]),
            "outcome_wage_y": float(y_full[i]) if s[i] == 1 else None
        }
        data.append(row)

    res = HeckmanSelectionEngine.estimate(
        data=data,
        selection_indicator_var="participated",
        outcome_var="outcome_wage_y",
        outcome_covariates=["income_x"],
        exclusion_restrictions=["invitation_mode_z"]
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "HECKMAN_TWO_STEP_SELECTION"

    diag = res["diagnostics"]
    assert diag["n_total_observations"] == 120
    assert diag["n_selected_observed"] > 40
    assert diag["n_unselected_censored"] > 15
    assert diag["selection_rate_pct"] > 30.0
    assert diag["has_valid_exclusion"] is True

    # Check that selection bias was detected (rho > 0.3)
    assert diag["rho_correlation"] > 0.2
    assert diag["inverse_mills_ratio_coef"] > 0.2

    # Check comparison table
    coeffs = res["coefficients_comparison"]
    assert len(coeffs) == 2  # Intercept + income_x
    x_item = next(c for c in coeffs if c["variable"] == "income_x")
    assert abs(x_item["heckman_estimate"] - 1.5) < 0.5
    assert x_item["selection_bias_gap"] != 0.0

    # Check SVG and narrative
    assert "<svg" in res["svg_visualization"]
    assert "Inverse Mills Ratio" in res["apa_narrative"]
    assert "Heckman" in res["apa_narrative"]


def test_heckman_no_selection_bias():
    np.random.seed(123)
    n = 100
    x = np.random.normal(0, 1.0, n)
    z = np.random.normal(0, 1.0, n)
    # Independent errors (rho = 0)
    u = np.random.normal(0, 1.0, n)
    e = np.random.normal(0, 1.0, n)

    s = (0.5 + 0.5 * x + 1.0 * z + u > 0).astype(int)
    y = 3.0 + 2.0 * x + e

    data = []
    for i in range(n):
        data.append({
            "is_selected": int(s[i]),
            "x_val": float(x[i]),
            "z_inst": float(z[i]),
            "y_val": float(y[i]) if s[i] == 1 else None
        })

    res = HeckmanSelectionEngine.estimate(
        data=data,
        selection_indicator_var="is_selected",
        outcome_var="y_val",
        outcome_covariates=["x_val"],
        exclusion_restrictions=["z_inst"]
    )

    assert res["status"] == "SUCCESS"
    assert res["diagnostics"]["n_total_observations"] == 100
    # Coefficients close to true beta = 2.0
    x_item = next(c for c in res["coefficients_comparison"] if c["variable"] == "x_val")
    assert abs(x_item["heckman_estimate"] - 2.0) < 0.4
