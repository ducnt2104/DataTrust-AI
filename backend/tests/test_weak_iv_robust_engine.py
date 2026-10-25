# -*- coding: utf-8 -*-
"""
Unit tests for WeakIVRobustEngine (Anderson-Rubin 1949, Moreira 2003 CLR, Montiel Olea & Pflueger 2013).
"""

import pytest
import numpy as np
from app.engine.weak_iv_robust_engine import WeakIVRobustEngine


def generate_iv_data(
    n_samples: int = 150,
    pi_strength: float = 0.8,
    beta_true: float = 1.25,
    seed: int = 42
):
    rng = np.random.RandomState(seed)
    # Exogenous controls X
    x = rng.normal(0, 1.0, size=(n_samples, 2))
    # Excluded instruments Z (2 instruments)
    z = rng.normal(0, 1.0, size=(n_samples, 2))
    # Structural error u and first-stage error v (correlated for endogeneity)
    cov_errors = np.array([[1.0, 0.65], [0.65, 1.0]])
    errors = rng.multivariate_normal(mean=[0, 0], cov=cov_errors, size=n_samples)
    u = errors[:, 0]
    v = errors[:, 1]

    # First stage: Y_endog = Z * Pi + X * Gamma + v
    y_endog = z[:, 0] * pi_strength + z[:, 1] * (pi_strength * 0.7) + x[:, 0] * 0.4 + v
    # Structural outcome: y = beta * Y_endog + X * Gamma_y + u
    y = beta_true * y_endog + x[:, 0] * 0.5 + x[:, 1] * -0.3 + u

    return y, y_endog, z, x


def test_weak_iv_strong_instrument():
    y, y_endog, z, x = generate_iv_data(n_samples=200, pi_strength=0.9, beta_true=1.5)
    res = WeakIVRobustEngine.estimate(
        y=y,
        endogenous_y=y_endog,
        instruments_z=z,
        covariates_x=x,
        alpha_level=0.05
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "WEAK_IV_ROBUST_MOREIRA_CLR_AR"

    diag = res["diagnostics"]
    assert diag["sample_size"] == 200
    assert diag["num_instruments"] == 2
    assert diag["first_stage_f"] > 10.0
    assert diag["effective_f"] > 10.0
    assert diag["ar_null_zero_p_value"] < 0.05

    est = res["estimates"]
    assert "beta_2sls" in est
    assert "wald_ci_95" in est
    assert est["ar_ci_type"] == "BOUNDED_INTERVAL"
    assert len(est["ar_ci_95"]) == 1
    assert est["clr_ci_95"] is not None
    assert len(est["clr_ci_95"]) == 2

    # Check that true beta (1.5) is inside the CLR confidence interval
    clr_lo, clr_hi = est["clr_ci_95"]
    assert clr_lo <= 1.5 <= clr_hi

    # Verify SVG and APA narrative
    assert "<svg" in res["svg_visualization"]
    assert "DataTrust" in res["apa_narrative"]
    assert "Moreira" in res["apa_narrative"]


def test_weak_iv_weak_instrument():
    # Very weak pi_strength -> weak instruments
    y, y_endog, z, x = generate_iv_data(n_samples=100, pi_strength=0.08, beta_true=1.0)
    res = WeakIVRobustEngine.estimate(
        y=y,
        endogenous_y=y_endog,
        instruments_z=z,
        covariates_x=x,
        alpha_level=0.05
    )

    assert res["status"] == "SUCCESS"
    diag = res["diagnostics"]
    # Effective F should indicate weak instruments
    assert diag["identification_status"] in ["WEAK_IDENTIFICATION", "SEVERELY_WEAK_OR_UNIDENTIFIED"]
    assert "<svg" in res["svg_visualization"]
    assert "DataTrust" in res["apa_narrative"]


def test_weak_iv_insufficient_sample():
    # Only 10 observations
    y = np.ones(10)
    y_endog = np.ones(10)
    z = np.ones((10, 1))
    res = WeakIVRobustEngine.estimate(
        y=y,
        endogenous_y=y_endog,
        instruments_z=z
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"
    assert "yêu cầu ít nhất 25 quan sát" in res["message"]


def test_weak_iv_mismatched_dimensions():
    y = np.ones(30)
    y_endog = np.ones(25)
    z = np.ones((30, 1))
    res = WeakIVRobustEngine.estimate(
        y=y,
        endogenous_y=y_endog,
        instruments_z=z
    )
    assert res["status"] == "ERROR"
    assert "Kích thước mẫu không đồng nhất" in res["message"]
