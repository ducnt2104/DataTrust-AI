"""
Unit tests for Bayesian Additive Regression Trees (BART) Causal Engine
"""

import numpy as np
import pytest
from app.engine.bart_causal_engine import BARTCausalEngine


def test_bart_causal_insufficient_sample():
    # N < 25
    data_small = [{"T": 1, "Y": 10, "X1": 5} for _ in range(15)]
    res = BARTCausalEngine.estimate(data_small, "T", "Y", ["X1"])
    assert res["status"] == "INSUFFICIENT_SAMPLE"

    # k < 1
    data_no_cov = [{"T": i % 2, "Y": 10 + i} for i in range(30)]
    res_no_cov = BARTCausalEngine.estimate(data_no_cov, "T", "Y", [])
    assert res_no_cov["status"] == "INSUFFICIENT_SAMPLE"


def test_bart_causal_synthetic_data():
    np.random.seed(42)
    N = 100
    rows = []
    for i in range(N):
        x1 = float(np.random.normal(0, 1))
        x2 = float(np.random.uniform(1, 5))
        # Treatment propensity
        prob_t = 1.0 / (1.0 + np.exp(-(0.5 * x1 - 0.2 * x2)))
        t = 1 if np.random.rand() < prob_t else 0
        # True heterogeneous treatment effect: tau = 3.0 + 2.0 * x1
        tau = 3.0 + 2.0 * x1
        base_y = 10.0 + 1.5 * x1 + 0.8 * x2
        noise = float(np.random.normal(0, 0.5))
        y = base_y + t * tau + noise

        rows.append({
            "Treatment": t,
            "Outcome": y,
            "Cov1": x1,
            "Cov2": x2
        })

    result = BARTCausalEngine.estimate(
        data=rows,
        treatment_var="Treatment",
        outcome_var="Outcome",
        covariates=["Cov1", "Cov2"],
        n_trees=30,
        n_samples=100,
        seed=42
    )

    assert result["status"] == "SUCCESS"
    assert result["model_type"] == "BAYESIAN_ADDITIVE_REGRESSION_TREES_CAUSAL"
    assert "treatment_effects" in result
    assert "ate" in result["treatment_effects"]
    assert "att" in result["treatment_effects"]
    assert "ite_distribution" in result
    assert "variable_importance" in result
    assert len(result["variable_importance"]) == 2
    assert "svg_visualization" in result
    assert "<svg" in result["svg_visualization"]
    assert "apa_narrative" in result
    assert "Chipman et al." in result["apa_narrative"]
