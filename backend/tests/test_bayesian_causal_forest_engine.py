"""
Unit tests for Bayesian Causal Forests Engine (BCF)
(Hahn, Murray, & Carvalho 2020 Bayesian Analysis)
DataTrust Iteration 181
"""

import pytest
import numpy as np
from app.engine.bayesian_causal_forest_engine import run_bayesian_causal_forest


def test_bayesian_causal_forest_success():
    np.random.seed(42)
    n = 60
    records = []

    for i in range(n):
        x1 = float(np.random.normal(0, 1))
        x2 = float(np.random.normal(2, 1))
        # Non-random treatment assignment: selection on observables
        prop_prob = 1.0 / (1.0 + np.exp(-(0.6 * x1 + 0.3 * x2)))
        d = 1 if np.random.uniform() < prop_prob else 0
        # True outcome with true treatment effect tau = 4.0
        y = 10.0 + 3.0 * x1 + 2.0 * x2 + 4.0 * d + float(np.random.normal(0, 0.8))

        records.append({
            "treatment": d,
            "outcome": y,
            "cov1": x1,
            "cov2": x2
        })

    res = run_bayesian_causal_forest(
        records=records,
        treatment_col="treatment",
        outcome_col="outcome",
        covariate_cols=["cov1", "cov2"],
        num_mcmc_draws=150,
        credibility_level=0.95
    )

    assert res["status"] == "success"
    assert res["sample_size"] == 60
    assert res["mcmc_draws_count"] == 150
    assert res["effective_sample_size"] > 20
    assert res["ate_estimates"]["posterior_mean"] > 2.0
    assert res["ate_estimates"]["ci_lower_95"] < res["ate_estimates"]["ci_upper_95"]
    assert res["ate_estimates"]["prob_positive_effect"] >= 0.85
    assert len(res["propensity_quintiles"]) == 5
    assert len(res["sample_cate_estimates"]) > 5
    assert "<svg" in res["svg_visualization"]
    assert "DataTrust" in res["apa_narrative"]
    assert "Hahn" in res["apa_narrative"]


def test_bayesian_causal_forest_insufficient_sample():
    records = [{"treatment": 1, "outcome": 5.0} for _ in range(12)]
    res = run_bayesian_causal_forest(
        records=records,
        treatment_col="treatment",
        outcome_col="outcome"
    )
    assert res["status"] == "insufficient_data"


def test_bayesian_causal_forest_invalid_treatment():
    # Only control
    records = [{"treatment": 0, "outcome": float(i)} for i in range(35)]
    res = run_bayesian_causal_forest(
        records=records,
        treatment_col="treatment",
        outcome_col="outcome"
    )
    assert res["status"] == "invalid_treatment"
