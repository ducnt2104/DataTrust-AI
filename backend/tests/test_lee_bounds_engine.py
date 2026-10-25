# -*- coding: utf-8 -*-
"""
Unit tests for Non-random Survey Attrition and Selection Bounds Engine (Lee Bounds; Lee 2009).
"""

import pytest
import numpy as np
import pandas as pd
from app.engine.lee_bounds_engine import estimate_lee_bounds


@pytest.fixture
def synthetic_lee_data():
    """
    Generates synthetic survey dataset with selective attrition:
    - Treatment T ~ Bernoulli(0.5)
    - Baseline covariate X ~ Normal(0, 1)
    - Response indicator R:
      T=1 has 85% retention, T=0 has 60% retention (differential attrition = 25%)
    - Outcome Y:
      True effect = +2.0, but only observed when R=1
    """
    np.random.seed(42)
    n = 200
    t = np.random.binomial(1, 0.5, n)
    x = np.random.normal(0, 1, n)
    
    # Selective response
    # Treated units respond with probability 0.85
    # Control units respond with probability 0.60
    p_resp = np.where(t == 1, 0.85, 0.60)
    r = (np.random.uniform(0, 1, n) <= p_resp).astype(int)
    
    # Outcome Y: Y = 10.0 + 2.0*T + 1.5*X + noise
    y_latent = 10.0 + 2.0 * t + 1.5 * x + np.random.normal(0, 0.8, n)
    # Outcome is missing if R == 0
    y_observed = [y_latent[i] if r[i] == 1 else np.nan for i in range(n)]

    return pd.DataFrame({
        "q_outcome": y_observed,
        "q_treatment": t,
        "q_response": r,
        "q_covariate": x
    })


def test_lee_bounds_basic(synthetic_lee_data):
    res = estimate_lee_bounds(
        df=synthetic_lee_data,
        outcome_col="q_outcome",
        treatment_col="q_treatment",
        response_col="q_response",
        covariate_cols=["q_covariate"],
        n_bootstraps=50
    )
    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "LEE_BOUNDS_RESTUD_2009"
    assert res["sample_size"] == 200
    assert "response_rates" in res
    assert res["response_rates"]["trimming_fraction_q"] > 0.1
    assert "unconditional" in res["bounds"]
    lb = res["bounds"]["unconditional"]["lower_bound"]
    ub = res["bounds"]["unconditional"]["upper_bound"]
    assert lb <= ub
    assert "<svg" in res["svg_visualization"]
    assert "Lee" in res["apa_narrative"]


def test_lee_bounds_tightening(synthetic_lee_data):
    res = estimate_lee_bounds(
        df=synthetic_lee_data,
        outcome_col="q_outcome",
        treatment_col="q_treatment",
        covariate_cols=["q_covariate"],
        n_bootstraps=30
    )
    assert res["status"] == "SUCCESS"
    uncond_lb = res["bounds"]["unconditional"]["lower_bound"]
    uncond_ub = res["bounds"]["unconditional"]["upper_bound"]
    tight_lb = res["bounds"]["covariate_tightened"]["lower_bound"]
    tight_ub = res["bounds"]["covariate_tightened"]["upper_bound"]
    # Tightened bounds should be within or equal to unconditional
    assert tight_lb >= uncond_lb - 0.05
    assert tight_ub <= uncond_ub + 0.05


def test_lee_bounds_insufficient_sample():
    small_df = pd.DataFrame({
        "y": [1.0] * 10,
        "t": [1] * 5 + [0] * 5
    })
    res = estimate_lee_bounds(small_df, "y", "t")
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_lee_bounds_missing_column(synthetic_lee_data):
    res = estimate_lee_bounds(synthetic_lee_data, "bad_col", "q_treatment")
    assert res["status"] == "ERROR"
