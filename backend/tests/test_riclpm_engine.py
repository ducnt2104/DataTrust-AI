"""
Unit tests for Random-Intercept Cross-Lagged Panel Model (RI-CLPM) & Structural Mediation Engine.
DataTrust Quantitative Econometrics Architecture.
"""

import pytest
import numpy as np
from app.engine.riclpm_engine import RICLPMEngine, run_riclpm_analysis


def test_riclpm_three_waves_bidirectional():
    """Test 3-wave longitudinal panel with stable traits and dynamic reciprocal causal transmission."""
    np.random.seed(42)
    N = 120
    T = 3

    # Stable between-person random intercepts (correlated traits)
    mean_traits = [0, 0]
    cov_traits = [[1.0, 0.45], [0.45, 1.0]]
    traits = np.random.multivariate_normal(mean_traits, cov_traits, size=N)
    I_X = traits[:, 0]
    I_Y = traits[:, 1]

    # Initialize within-person deviations
    w_x = np.zeros((N, T))
    w_y = np.zeros((N, T))
    w_x[:, 0] = np.random.normal(0, 0.5, size=N)
    w_y[:, 0] = np.random.normal(0, 0.5, size=N)

    # Autoregressive & cross-lagged parameters
    alpha_x = 0.4
    alpha_y = 0.35
    beta_xy = 0.28  # X -> subsequent Y
    beta_yx = 0.12  # Y -> subsequent X

    for t in range(T - 1):
        w_x[:, t + 1] = alpha_x * w_x[:, t] + beta_yx * w_y[:, t] + np.random.normal(0, 0.4, size=N)
        w_y[:, t + 1] = alpha_y * w_y[:, t] + beta_xy * w_x[:, t] + np.random.normal(0, 0.4, size=N)

    # Observed data = Grand mean + Trait + Within deviation
    mu_x = [10.0, 10.5, 11.0]
    mu_y = [20.0, 21.0, 22.0]
    data_x = mu_x + I_X[:, np.newaxis] + w_x
    data_y = mu_y + I_Y[:, np.newaxis] + w_y

    res = RICLPMEngine.estimate(
        data_x=data_x,
        data_y=data_y,
        var_x_name="Trust",
        var_y_name="Compliance",
        wave_labels=["Wave 1", "Wave 2", "Wave 3"],
        n_bootstraps=30,
        seed=42,
    )

    assert res["status"] == "success"
    assert res["sample_size"] == N
    assert res["waves_count"] == T

    # Trait correlation should be positive
    assert res["between_person_traits"]["trait_correlation"] > 0.15

    # Within-person cross-lag X -> Y should be positive and greater than Y -> X
    assert res["within_person_dynamics"]["mean_cross_lag_x_to_y"] > 0.05
    assert len(res["within_person_dynamics"]["wave_transitions"]) == 2

    # Fit indices should indicate adequate fit
    assert res["goodness_of_fit"]["cfi"] >= 0.88
    assert res["goodness_of_fit"]["rmsea"] <= 0.10
    assert res["goodness_of_fit"]["clpm_comparison"]["ri_clpm_preferred"] is True

    assert "<svg" in res["svg_visualization"]
    assert "Random-Intercept Cross-Lagged Panel Model" in res["apa_narrative"]


def test_riclpm_with_longitudinal_mediator():
    """Test 3-wave longitudinal panel with explicit mediator M (X1 -> M2 -> Y3)."""
    np.random.seed(123)
    N = 90
    T = 3

    I_X = np.random.normal(0, 0.8, size=N)
    I_M = np.random.normal(0, 0.8, size=N)
    I_Y = np.random.normal(0, 0.8, size=N)

    w_x = np.random.normal(0, 0.5, size=(N, T))
    w_m = np.random.normal(0, 0.5, size=(N, T))
    w_y = np.random.normal(0, 0.5, size=(N, T))

    # Path a: X1 -> M2
    w_m[:, 1] = 0.5 * w_x[:, 0] + np.random.normal(0, 0.3, size=N)
    # Path b: M2 -> Y3
    w_y[:, 2] = 0.6 * w_m[:, 1] + 0.2 * w_x[:, 0] + np.random.normal(0, 0.3, size=N)

    data_x = 5.0 + I_X[:, np.newaxis] + w_x
    data_m = 15.0 + I_M[:, np.newaxis] + w_m
    data_y = 25.0 + I_Y[:, np.newaxis] + w_y

    res = RICLPMEngine.estimate(
        data_x=data_x,
        data_y=data_y,
        data_m=data_m,
        var_x_name="Intervention",
        var_y_name="Retention",
        var_m_name="Engagement",
        n_bootstraps=30,
        seed=123,
    )

    assert res["status"] == "success"
    assert "path_a_x_to_m" in res["longitudinal_mediation"]
    assert res["longitudinal_mediation"]["path_a_x_to_m"] > 0.10
    assert res["longitudinal_mediation"]["path_b_m_to_y"] > 0.05
    assert res["longitudinal_mediation"]["indirect_effect"] > 0.01


def test_riclpm_insufficient_sample_or_waves_error():
    """Test error handling for T < 3 and N < 25."""
    data_small = np.random.normal(0, 1, size=(10, 3))
    with pytest.raises(ValueError, match="Sample size N=10 is too small"):
        RICLPMEngine.estimate(data_small, data_small)

    data_2waves = np.random.normal(0, 1, size=(30, 2))
    with pytest.raises(ValueError, match="Longitudinal panel requires at least T=3 waves"):
        RICLPMEngine.estimate(data_2waves, data_2waves)
