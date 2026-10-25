# -*- coding: utf-8 -*-
import pytest
import numpy as np
import pandas as pd
from app.engine.larf_engine import estimate_larf


@pytest.fixture
def synthetic_larf_data():
    """
    Generates synthetic survey dataset with:
    - Instrument Z ~ Bernoulli(0.5)
    - Confounder U ~ N(0, 1)
    - Endogenous binary treatment D affected by Z and U
    - Outcome Y affected by D, U, and covariates X1, X2
    """
    np.random.seed(42)
    n = 200
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(1, 0.5, n)
    u = np.random.normal(0, 1, n)
    
    # Instrument Z randomly assigned
    z = np.random.binomial(1, 0.5, n)
    
    # Endogenous treatment: Compliers take treatment if Z=1 and high U
    d_latent = 1.2 * z + 0.8 * u + 0.3 * x1 - 0.5
    d = (d_latent > 0).astype(float)
    
    # Outcome: True causal effect of D is +1.0, but confounded by U
    y_latent = 0.9 * d + 1.1 * u + 0.4 * x1 - 0.2 * x2 + np.random.normal(0, 0.5, n)
    y_binary = (y_latent > 0).astype(float)
    
    return pd.DataFrame({
        "q_outcome": y_binary,
        "q_treatment": d,
        "q_instrument": z,
        "q_x1": x1,
        "q_x2": x2
    })


def test_larf_logit_basic(synthetic_larf_data):
    res = estimate_larf(
        df=synthetic_larf_data,
        outcome_col="q_outcome",
        treatment_col="q_treatment",
        instrument_col="q_instrument",
        covariate_cols=["q_x1", "q_x2"],
        model_type="logit",
        n_bootstraps=50
    )
    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "LARF_LOGIT_ABADIE_2003"
    assert res["sample_size"] == 200
    assert res["complier_probability"] > 0.05
    assert "late" in res["effects"]
    assert "ci_lower" in res["effects"]["late"]
    assert "ci_upper" in res["effects"]["late"]
    assert "<svg" in res["svg_visualization"]
    assert "Abadie" in res["apa_narrative"]
    assert len(res["model_coefficients"]) >= 3


def test_larf_linear(synthetic_larf_data):
    res = estimate_larf(
        df=synthetic_larf_data,
        outcome_col="q_outcome",
        treatment_col="q_treatment",
        instrument_col="q_instrument",
        covariate_cols=["q_x1", "q_x2"],
        model_type="linear",
        n_bootstraps=50
    )
    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "LARF_LINEAR_ABADIE_2003"
    assert "late" in res["effects"]
    assert isinstance(res["effects"]["late"]["estimate"], float)


def test_larf_trim_negative(synthetic_larf_data):
    res = estimate_larf(
        df=synthetic_larf_data,
        outcome_col="q_outcome",
        treatment_col="q_treatment",
        instrument_col="q_instrument",
        covariate_cols=["q_x1"],
        model_type="logit",
        trim_negative=True,
        n_bootstraps=30
    )
    assert res["status"] == "SUCCESS"
    assert res["effective_sample_size"] > 0


def test_larf_insufficient_sample():
    small_df = pd.DataFrame({
        "y": [1.0] * 10,
        "d": [0.0] * 10,
        "z": [1.0] * 10
    })
    res = estimate_larf(small_df, "y", "d", "z")
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_larf_missing_column(synthetic_larf_data):
    res = estimate_larf(synthetic_larf_data, "non_existent_col", "q_treatment", "q_instrument")
    assert res["status"] == "ERROR"
