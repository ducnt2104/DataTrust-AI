# -*- coding: utf-8 -*-
"""
Unit tests for Automatic Debiased Machine Learning via Riesz Representer Learning Engine
(Chernozhukov, Newey, & Singh 2022 Econometrica).
"""

import pytest
import numpy as np
import pandas as pd
from app.engine.auto_dml_riesz_engine import (
    estimate_auto_dml_riesz,
    _build_feature_dictionary,
    _evaluate_functional_vector
)


def test_build_feature_dictionary_and_functional():
    N = 20
    D = np.random.uniform(0, 1, N)
    X = np.random.normal(0, 1, (N, 2))
    
    phi = _build_feature_dictionary(D, X, degree=2)
    # 1 (const) + 1 (D) + 2 (X) + 2 (D*X) + 1 (D^2) + 2 (X^2) = 9 columns
    assert phi.shape == (N, 9)
    
    m_ate = _evaluate_functional_vector(phi, D, X, functional_type="ate")
    assert len(m_ate) == 9
    
    m_shift = _evaluate_functional_vector(phi, D, X, functional_type="policy_shift", shift_delta=0.5)
    assert len(m_shift) == 9
    
    m_deriv = _evaluate_functional_vector(phi, D, X, functional_type="marginal_derivative")
    assert len(m_deriv) == 9


def test_estimate_auto_dml_riesz_binary_ate():
    np.random.seed(42)
    N = 250
    X1 = np.random.normal(0, 1, N)
    X2 = np.random.normal(0, 1, N)
    
    # Confounded propensity
    prob = 1.0 / (1.0 + np.exp(-(0.5 * X1 - 0.3 * X2)))
    D = (np.random.uniform(0, 1, N) < prob).astype(float)
    
    # True ATE = 3.5
    true_tau = 3.5
    Y = 2.0 + true_tau * D + 1.2 * X1 + 0.8 * X2 + np.random.normal(0, 0.5, N)
    
    df = pd.DataFrame({
        "y": Y,
        "d": D,
        "x1": X1,
        "x2": X2
    })
    
    res = estimate_auto_dml_riesz(
        df=df,
        outcome_col="y",
        treatment_col="d",
        covariate_cols=["x1", "x2"],
        functional_type="ate",
        n_splits=5
    )
    
    assert res["status"] == "SUCCESS"
    summ = res["overall_summary"]
    assert summ["sample_size"] == N
    assert summ["functional_type"] == "ate"
    assert abs(summ["theta_autodml"] - true_tau) < 0.8  # Accurate recovery
    assert summ["se_autodml"] > 0
    assert summ["p_value"] < 0.05
    assert "<svg" in res["svg_visualization"]
    assert "Automatic Debiased Machine Learning" in res["apa_narrative"]


def test_estimate_auto_dml_riesz_continuous_policy_shift():
    np.random.seed(101)
    N = 200
    X1 = np.random.normal(0, 1, N)
    D = 1.5 + 0.8 * X1 + np.random.normal(0, 0.4, N)  # Continuous dosage
    
    # True marginal slope = 2.0, so shift delta = 0.5 gives delta * 2.0 = 1.0
    shift_delta = 0.5
    Y = 5.0 + 2.0 * D + 1.0 * X1 + np.random.normal(0, 0.3, N)
    
    df = pd.DataFrame({
        "y": Y,
        "d": D,
        "x1": X1
    })
    
    res = estimate_auto_dml_riesz(
        df=df,
        outcome_col="y",
        treatment_col="d",
        covariate_cols=["x1"],
        functional_type="policy_shift",
        shift_delta=shift_delta,
        n_splits=4
    )
    
    assert res["status"] == "SUCCESS"
    summ = res["overall_summary"]
    assert summ["functional_type"] == "policy_shift"
    # Target parameter is E[Y(D + delta) - Y(D)] approx 2.0 * 0.5 = 1.0
    assert abs(summ["theta_autodml"] - 1.0) < 0.5
    assert summ["riesz_weight_sd"] > 0


def test_auto_dml_validation_errors():
    df = pd.DataFrame({"y": [1.0] * 10, "d": [0.0] * 10})
    with pytest.raises(ValueError, match="too small"):
        estimate_auto_dml_riesz(df, "y", "d", [], n_splits=3)
        
    df_large = pd.DataFrame({"y": np.random.randn(30), "d": np.random.randn(30)})
    with pytest.raises(ValueError, match="not found"):
        estimate_auto_dml_riesz(df_large, "y", "d", ["nonexistent"])
