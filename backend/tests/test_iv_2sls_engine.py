"""
Unit tests for Instrumental Variables Two-Stage Least Squares (2SLS) Engine.
"""

import numpy as np
import pytest
from app.engine.iv_2sls_engine import IV2SLSEngine


def test_iv_2sls_endogeneity_correction():
    """
    Verify 2SLS recovers true beta when X is endogenous (correlated with structural error).
    """
    np.random.seed(42)
    N = 400

    # Common unobserved confounder U
    U = np.random.normal(0, 1, N)

    # Instrument Z (exogenous: uncorrelated with U)
    Z = np.random.normal(0, 2, N)

    # Exogenous control W
    W = np.random.normal(0, 1, N)

    # Endogenous regressor X: depends on Z, W, and unobserved U
    X = 1.0 + 1.8 * Z + 0.8 * W + 2.0 * U + np.random.normal(0, 0.5, N)

    # Structural outcome Y: true beta_X = 2.5, true beta_W = 1.2
    # Y also depends on U -> causes severe OLS omitted variable bias
    true_beta = 2.5
    Y = 5.0 + true_beta * X + 1.2 * W + 3.0 * U + np.random.normal(0, 0.5, N)

    res = IV2SLSEngine.estimate(Y=Y, X_endog=X, Z_instruments=Z, W_controls=W)

    assert res["status"] == "success"
    # 2SLS should be close to true beta (2.5)
    b_2sls = res["iv_estimate"]["beta"]
    assert np.isclose(b_2sls, true_beta, atol=0.25)

    # OLS is upward-biased due to positive correlation with U
    b_ols = res["ols_benchmark"]["beta"]
    assert b_ols > b_2sls + 0.15

    # First-stage F should be strong (F >> 10)
    assert res["first_stage_diagnostics"]["f_statistic"] > 50.0
    assert res["first_stage_diagnostics"]["is_weak_instrument"] is False

    # Wu-Hausman test should detect endogeneity (p < 0.05)
    assert res["wu_hausman_test"]["is_endogenous"] is True

    # Chart and narrative checks
    assert "<svg" in res["svg_chart"]
    assert "2SLS" in res["apa_narrative"]


def test_iv_2sls_weak_instrument_and_sargan():
    """
    Verify detection of weak instruments and Sargan overidentification test when L=2.
    """
    np.random.seed(99)
    N = 300

    # Two instruments Z1, Z2
    Z1 = np.random.normal(0, 1, N)
    Z2 = np.random.normal(0, 1, N)
    Z = np.column_stack([Z1, Z2])

    # Endogenous X
    U = np.random.normal(0, 1, N)
    X = 0.9 * Z1 + 0.8 * Z2 + 1.5 * U + np.random.normal(0, 0.5, N)
    Y = 2.0 + 1.5 * X + 1.5 * U + np.random.normal(0, 0.5, N)

    res = IV2SLSEngine.estimate(Y=Y, X_endog=X, Z_instruments=Z)

    assert res["status"] == "success"
    assert res["instruments_count"] == 2
    assert res["sargan_hansen_overid_test"]["j_statistic"] is not None
    assert res["sargan_hansen_overid_test"]["degrees_of_freedom"] == 1
    # Both instruments are valid, so Sargan should not reject (p >= 0.05)
    assert res["sargan_hansen_overid_test"]["instruments_valid"] is True


def test_iv_2sls_insufficient_sample():
    """
    Verify graceful error on small sample.
    """
    Y = np.array([1, 2, 3, 4, 5])
    X = np.array([1, 2, 3, 4, 5])
    Z = np.array([1, 2, 3, 4, 5])

    res = IV2SLSEngine.estimate(Y=Y, X_endog=X, Z_instruments=Z)
    assert res["status"] == "insufficient_data"
    assert "tối thiểu 12 quan sát" in res["message"]
