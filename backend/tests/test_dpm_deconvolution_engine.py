# -*- coding: utf-8 -*-
"""
Unit tests for Bayesian Nonparametric Dirichlet Process Mixture Density Deconvolution Engine
(Ferguson 1973; Escobar & West 1995; Delaigle et al. 2008).
"""

import pytest
import numpy as np
import pandas as pd
from app.engine.dpm_deconvolution_engine import estimate_dpm_deconvolution


def test_dpm_deconvolution_synthetic_mixture():
    np.random.seed(42)
    N = 250
    # True latent mixture: bimodal distribution
    component_choice = np.random.uniform(0, 1, N) < 0.6
    x_star = np.where(component_choice, np.random.normal(20.0, 2.0, N), np.random.normal(32.0, 2.5, N))
    
    # Additive survey noise: epsilon ~ N(0, 2.0^2)
    noise = np.random.normal(0, 2.0, N)
    y_obs = x_star + noise

    df = pd.DataFrame({"satisfaction_score": y_obs})

    res = estimate_dpm_deconvolution(
        df=df,
        target_col="satisfaction_score",
        error_variance_ratio=0.30,
        max_components=5,
        n_mcmc_samples=80
    )

    assert res["status"] == "SUCCESS"
    summ = res["overall_summary"]
    assert summ["sample_size"] == N
    # True latent variance is smaller than contaminated variance
    assert summ["latent_true_variance"] < summ["observed_variance"]
    assert 0.0 < summ["reliability_ratio"] < 1.0
    assert summ["measurement_error_sd"] > 0
    assert len(summ["quantiles_deconvolved"]) == 5
    assert len(res["components"]) == 5
    assert abs(sum(c["weight"] for c in res["components"]) - 1.0) < 1e-3
    assert "<svg" in res["svg_visualization"]
    assert "Dirichlet Process Mixture" in res["apa_narrative"]


def test_dpm_deconvolution_with_replicate():
    np.random.seed(123)
    N = 200
    x_star = np.random.normal(50.0, 8.0, N)
    # Two repeated measurements with noise variance sigma_eps^2 = 3.0^2 = 9.0
    y1 = x_star + np.random.normal(0, 3.0, N)
    y2 = x_star + np.random.normal(0, 3.0, N)

    df = pd.DataFrame({"score_wave1": y1, "score_wave2": y2})

    res = estimate_dpm_deconvolution(
        df=df,
        target_col="score_wave1",
        replicate_col="score_wave2",
        max_components=4,
        n_mcmc_samples=60
    )

    assert res["status"] == "SUCCESS"
    summ = res["overall_summary"]
    # Replicate noise estimation should recover noise SD near 3.0
    assert abs(summ["measurement_error_sd"] - 3.0) < 1.0
    assert summ["latent_true_variance"] > 0
    assert "cặp câu hỏi lặp lại" in summ["measurement_error_source"]


def test_dpm_deconvolution_validation_errors():
    df_small = pd.DataFrame({"y": [1.0] * 10})
    with pytest.raises(ValueError, match="too small"):
        estimate_dpm_deconvolution(df_small, "y")

    df_zero_var = pd.DataFrame({"y": [5.0] * 35})
    with pytest.raises(ValueError, match="effectively zero"):
        estimate_dpm_deconvolution(df_zero_var, "y")
