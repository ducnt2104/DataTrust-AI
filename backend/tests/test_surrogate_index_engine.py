# -*- coding: utf-8 -*-
"""
Unit tests for Surrogate Index Engine (Athey, Chetty, Imbens, & Kang 2019 Econometrica).
"""

import pytest
import numpy as np
import pandas as pd
from app.engine.surrogate_index_engine import estimate_surrogate_index


@pytest.fixture
def synthetic_surrogate_data():
    """
    Generates synthetic survey dataset with:
    - Treatment W ~ Bernoulli(0.5)
    - Short-term surrogates S1, S2, S3 influenced by W
    - Long-term outcome Y driven by surrogates: Y = 2.0*S1 + 1.5*S2 + 0.8*S3 + noise
    """
    np.random.seed(888)
    n = 150
    w = np.random.binomial(1, 0.5, n)
    
    # Surrogates
    s1 = 1.2 * w + np.random.normal(5, 1, n)
    s2 = 0.8 * w + np.random.normal(3, 1, n)
    s3 = 0.5 * w + np.random.normal(2, 0.5, n)
    
    # Long-term outcome Y (observed for follow-up sample, or all)
    y_long = 2.0 * s1 + 1.5 * s2 + 0.8 * s3 + np.random.normal(0, 1.0, n)
    
    return pd.DataFrame({
        "q_treatment": w,
        "q_s1": s1,
        "q_s2": s2,
        "q_s3": s3,
        "q_longterm_y": y_long
    })


def test_surrogate_index_basic(synthetic_surrogate_data):
    res = estimate_surrogate_index(
        df=synthetic_surrogate_data,
        treatment_col="q_treatment",
        surrogate_cols=["q_s1", "q_s2", "q_s3"],
        longterm_outcome_col="q_longterm_y",
        n_bootstraps=50
    )
    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "SURROGATE_INDEX_ATHEY_CHETTY_IMBENS_2019"
    assert res["sample_sizes"]["total"] == 150
    assert "longterm_treatment_effect" in res
    assert isinstance(res["longterm_treatment_effect"]["estimate"], float)
    assert len(res["surrogate_decomposition"]) == 3
    assert "<svg" in res["svg_visualization"]
    assert "Athey" in res["apa_narrative"]


def test_surrogate_index_with_covariates(synthetic_surrogate_data):
    df_with_cov = synthetic_surrogate_data.copy()
    df_with_cov["q_age"] = np.random.normal(30, 5, len(df_with_cov))
    res = estimate_surrogate_index(
        df=df_with_cov,
        treatment_col="q_treatment",
        surrogate_cols=["q_s1", "q_s2"],
        longterm_outcome_col="q_longterm_y",
        covariate_cols=["q_age"],
        n_bootstraps=30
    )
    assert res["status"] == "SUCCESS"
    assert res["surrogate_index_fit"]["r_squared"] > 0


def test_surrogate_index_insufficient_sample():
    small_df = pd.DataFrame({
        "w": [1] * 10 + [0] * 10,
        "s": [2.0] * 20,
        "y": [5.0] * 20
    })
    res = estimate_surrogate_index(small_df, "w", ["s"], "y")
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_surrogate_index_missing_column(synthetic_surrogate_data):
    res = estimate_surrogate_index(synthetic_surrogate_data, "non_existent", ["q_s1"], "q_longterm_y")
    assert res["status"] == "ERROR"
