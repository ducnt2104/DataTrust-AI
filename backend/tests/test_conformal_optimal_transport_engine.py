# -*- coding: utf-8 -*-
"""
Unit tests for Conformal Optimal Transport Counterfactual Distributional Alignment Engine
(Cuturi 2013 NeurIPS; Courty et al. 2017 TPAMI; Romano et al. 2019).
"""

import pytest
import numpy as np
import pandas as pd
from app.engine.conformal_optimal_transport_engine import (
    estimate_conformal_optimal_transport,
    _compute_sinkhorn_transport_plan
)


def test_sinkhorn_transport_plan_convergence_and_marginals():
    np.random.seed(42)
    N1, N0 = 15, 20
    # Random 1D positions
    x_source = np.linspace(0, 10, N1)
    y_target = np.linspace(5, 15, N0)
    C = (x_source[:, None] - y_target[None, :]) ** 2
    
    a = np.ones(N1) / N1
    b = np.ones(N0) / N0

    Pi, w2 = _compute_sinkhorn_transport_plan(C, a, b, reg_eps=0.1, max_iter=100)

    # 1. Total mass is 1.0
    assert abs(np.sum(Pi) - 1.0) < 1e-4
    # 2. Non-negative coupling
    assert np.all(Pi >= 0.0)
    # 3. Row marginals match a
    assert np.allclose(np.sum(Pi, axis=1), a, atol=1e-3)
    # 4. Column marginals match b
    assert np.allclose(np.sum(Pi, axis=0), b, atol=1e-3)
    # 5. Wasserstein distance is positive
    assert w2 > 0.0


def test_estimate_conformal_optimal_transport_full_pipeline():
    np.random.seed(88)
    n1, n0 = 35, 40
    
    # Generate covariates X
    x1 = np.random.normal(5.0, 1.0, n1)
    x0 = np.random.normal(4.5, 1.0, n0)

    # True treatment shift = +5.0
    y1 = 20.0 + 5.0 + 1.2 * x1 + np.random.normal(0, 1.0, n1)
    y0 = 20.0 + 1.2 * x0 + np.random.normal(0, 1.0, n0)

    df = pd.DataFrame({
        "outcome": np.concatenate([y1, y0]),
        "treatment": np.concatenate([np.ones(n1), np.zeros(n0)]),
        "covariate": np.concatenate([x1, x0])
    })

    res = estimate_conformal_optimal_transport(
        df=df,
        outcome_col="outcome",
        treatment_col="treatment",
        covariate_cols=["covariate"],
        reg_eps=0.05,
        covariate_weight_kappa=0.5,
        conformal_alpha=0.10
    )

    assert res["status"] == "SUCCESS"
    summ = res["overall_summary"]
    assert summ["n_treated"] == n1
    assert summ["n_control"] == n0
    assert summ["wasserstein_2_distance"] > 0
    # ATE should be near 5.0
    assert abs(summ["optimal_transport_ate"] - 5.0) < 1.8
    assert summ["conformal_half_width_delta"] > 0
    assert len(summ["quantiles"]) == 5
    assert len(summ["counterfactual_quantile_shifts"]) == 5
    assert "<svg" in res["svg_visualization"]
    assert "Conformal Optimal Transport" in res["apa_narrative"]


def test_conformal_optimal_transport_validation_errors():
    df_small = pd.DataFrame({"outcome": [1.0] * 8, "treatment": [0.0] * 8})
    with pytest.raises(ValueError, match="too small"):
        estimate_conformal_optimal_transport(df_small, "outcome", "treatment")

    df_imbalanced = pd.DataFrame({
        "outcome": np.random.randn(30),
        "treatment": [1.0] * 2 + [0.0] * 28
    })
    with pytest.raises(ValueError, match="at least 10 observations"):
        estimate_conformal_optimal_transport(df_imbalanced, "outcome", "treatment")
