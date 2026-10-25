# -*- coding: utf-8 -*-
"""
Unit tests for Marginal Treatment Effects (MTE) Engine (Heckman & Vytlacil 1999, 2005).
"""

import pytest
import numpy as np
import pandas as pd
from app.engine.mte_engine import estimate_mte


@pytest.fixture
def synthetic_mte_data():
    """
    Generates synthetic survey dataset with Generalized Roy model:
    - Instruments Z1, Z2 (e.g. distance to center, voucher discount)
    - Pre-treatment covariate X (baseline ability)
    - Unobserved resistance to treatment U_D ~ Uniform(0, 1)
    - Selection equation: D = 1{ Phi(0.7*Z1 + 0.5*Z2 + 0.3*X) >= U_D }
    - Potential outcomes with heterogeneous returns:
      Y(0) = 10.0 + 1.5*X + U0
      Y(1) = 10.0 + 1.5*X + (3.0 - 2.0*U_D) + U1  (Roy selection: returns decrease with resistance)
    """
    np.random.seed(888)
    n = 250
    z1 = np.random.normal(0, 1, n)
    z2 = np.random.binomial(1, 0.5, n).astype(float)
    x = np.random.normal(2, 1, n)
    
    # Resistance to treatment U_D in (0, 1)
    u_d = np.random.uniform(0.01, 0.99, n)
    
    # Latent propensity index
    eta = 0.8 * z1 + 0.6 * z2 + 0.2 * x
    from scipy.stats import norm
    propensity = norm.cdf(eta)
    
    # Treatment choice: individual takes treatment if propensity >= unobserved resistance
    d = (propensity >= u_d).astype(float)
    
    # Potential outcomes: return to treatment is 4.0 - 3.0*U_D
    # Higher resistance U_D -> lower returns (positive selection on gains)
    treatment_effect = 4.0 - 3.0 * u_d
    y0 = 10.0 + 1.2 * x + np.random.normal(0, 0.5, n)
    y1 = y0 + treatment_effect + np.random.normal(0, 0.5, n)
    y = d * y1 + (1.0 - d) * y0
    
    return pd.DataFrame({
        "q_outcome": y,
        "q_treatment": d,
        "q_inst1": z1,
        "q_inst2": z2,
        "q_x": x
    })


def test_mte_basic(synthetic_mte_data):
    res = estimate_mte(
        df=synthetic_mte_data,
        outcome_col="q_outcome",
        treatment_col="q_treatment",
        instrument_cols=["q_inst1", "q_inst2"],
        covariate_cols=["q_x"],
        poly_degree=3,
        n_bootstraps=50
    )
    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "MARGINAL_TREATMENT_EFFECTS_HECKMAN_VYTLACIL_2005"
    assert res["sample_size"] == 250
    assert "parameters" in res
    assert "ate" in res["parameters"]
    assert "att" in res["parameters"]
    assert "atu" in res["parameters"]
    assert "prte" in res["parameters"]
    assert isinstance(res["parameters"]["ate"]["estimate"], float)
    assert len(res["mte_curve"]) == 50
    assert "<svg" in res["svg_visualization"]
    assert "Heckman" in res["apa_narrative"]
    assert "POSITIVE_SELECTION_ON_GAINS" in res["selection_sorting_pattern"]


def test_mte_no_covariates(synthetic_mte_data):
    res = estimate_mte(
        df=synthetic_mte_data,
        outcome_col="q_outcome",
        treatment_col="q_treatment",
        instrument_cols=["q_inst1"],
        covariate_cols=[],
        poly_degree=2,
        n_bootstraps=30
    )
    assert res["status"] == "SUCCESS"
    assert "late" in res["parameters"]


def test_mte_insufficient_sample():
    small_df = pd.DataFrame({
        "y": [1.0] * 15,
        "d": [0.0] * 15,
        "z": [1.0] * 15
    })
    res = estimate_mte(small_df, "y", "d", ["z"])
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_mte_missing_column(synthetic_mte_data):
    res = estimate_mte(synthetic_mte_data, "bad_col", "q_treatment", ["q_inst1"])
    assert res["status"] == "ERROR"
