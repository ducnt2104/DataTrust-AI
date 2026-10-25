"""
Unit tests for Two-Stage Residual Inclusion (2SRI) & Control Function Causal Engine.
DataTrust Quantitative Econometrics Architecture.
"""

import pytest
import numpy as np
from app.engine.control_function_2sri_engine import ControlFunction2SRIEngine


def test_2sri_binary_treatment_logistic_outcome():
    """Test 2SRI with binary endogenous treatment, binary outcome (logistic), and instrumental variable."""
    np.random.seed(42)
    N = 200

    # Exogenous covariate X
    X = np.random.normal(0, 1, size=(N, 1))

    # Instrument Z (correlated with treatment D, excluded from outcome Y)
    Z = np.random.normal(0, 1, size=(N, 1))

    # Unobserved confounder U
    U = np.random.normal(0, 1, size=N)

    # First stage: D is driven by Z, X, and U (endogeneity!)
    d_latent = 0.8 * Z.ravel() + 0.4 * X.ravel() + 0.9 * U - 0.2
    D = (d_latent > 0).astype(float)

    # Second stage structural model: Y is driven by D, X, and U
    true_alpha = 1.2
    y_latent = true_alpha * D + 0.5 * X.ravel() + 0.8 * U
    p_y = 1.0 / (1.0 + np.exp(-y_latent))
    Y = (np.random.uniform(0, 1, size=N) < p_y).astype(float)

    res = ControlFunction2SRIEngine.estimate(
        treatment=D,
        outcome=Y,
        instruments=Z,
        covariates=X,
        instrument_names=["IV_Z1"],
        covariate_names=["Cov_X1"],
        outcome_family="logistic",
        n_bootstraps=30,
        seed=42,
    )

    assert res["status"] == "success"
    assert res["sample_size"] == N
    assert res["treatment_type"] == "binary"
    assert res["outcome_family"] == "logistic"

    # Instrument should be strong (F > 10)
    assert res["first_stage"]["f_statistic"] > 5.0
    assert not res["first_stage"]["weak_instrument"]

    # Causal effect (ATE & ATT) should be positive
    assert res["causal_effects"]["ate"]["estimate"] > 0.0
    assert res["causal_effects"]["att"]["estimate"] > 0.0

    # Model comparison should have 3 rows
    assert len(res["model_comparison"]) == 3
    assert "<svg" in res["svg_visualization"]
    assert "Two-Stage Residual Inclusion" in res["apa_narrative"]


def test_2sri_continuous_treatment_linear_outcome():
    """Test 2SRI with continuous treatment, continuous outcome (linear), and instrumental variable."""
    np.random.seed(123)
    N = 150

    Z = np.random.normal(2, 1, size=(N, 1))
    X = np.random.normal(0, 1, size=(N, 1))
    U = np.random.normal(0, 1, size=N)

    # Continuous D
    D = 1.5 * Z.ravel() + 0.3 * X.ravel() + 1.2 * U + np.random.normal(0, 0.5, size=N)

    # Structural continuous Y
    true_alpha = 2.0
    Y = true_alpha * D + 0.8 * X.ravel() + 1.5 * U + np.random.normal(0, 0.5, size=N)

    res = ControlFunction2SRIEngine.estimate(
        treatment=D,
        outcome=Y,
        instruments=Z,
        covariates=X,
        outcome_family="linear",
        n_bootstraps=25,
        seed=123,
    )

    assert res["status"] == "success"
    assert res["sample_size"] == N
    assert res["treatment_type"] == "continuous"
    assert res["outcome_family"] == "linear"

    # Endogeneity test should detect positive residual coefficient rho
    assert res["endogeneity_test"]["residual_coefficient_rho"] > 0.0
    assert res["endogeneity_test"]["is_endogenous"] is True

    # 2SRI structural alpha should be close to true alpha 2.0
    assert abs(res["causal_effects"]["structural_alpha"] - true_alpha) < 0.6


def test_2sri_minimum_sample_size_error():
    """Test sample size validation."""
    D = np.array([1.0, 0.0, 1.0, 0.0])
    Y = np.array([1.0, 0.0, 1.0, 0.0])
    Z = np.array([[1.0], [2.0], [3.0], [4.0]])

    with pytest.raises(ValueError, match="Sample size N=4 is too small"):
        ControlFunction2SRIEngine.estimate(treatment=D, outcome=Y, instruments=Z)
