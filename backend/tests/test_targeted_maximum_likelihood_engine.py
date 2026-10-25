"""
Unit tests for Targeted Maximum Likelihood Estimation Engine (TMLE)
DataTrust Quantitative Intelligence System
"""

import pytest
import numpy as np
from app.engine.targeted_maximum_likelihood_engine import run_targeted_maximum_likelihood_estimation


def test_tmle_insufficient_data():
    res = run_targeted_maximum_likelihood_estimation(
        records=[],
        outcome_col="y",
        treatment_col="a"
    )
    assert res["status"] == "insufficient_data"


def test_tmle_causal_effect_recovery():
    np.random.seed(42)
    n = 120
    # Confounders W1, W2
    W1 = np.random.normal(0.0, 1.0, size=n)
    W2 = np.random.normal(0.0, 1.0, size=n)

    # Treatment mechanism with confounding: logit(g(W)) = 0.6 * W1 - 0.5 * W2
    logit_g = 0.6 * W1 - 0.5 * W2
    prob_a = 1.0 / (1.0 + np.exp(-logit_g))
    A = (np.random.uniform(0, 1, size=n) < prob_a).astype(int)

    # True potential outcomes: Y(1) - Y(0) = 4.0
    # Y = 4.0 * A + 2.0 * W1 - 1.5 * W2 + noise
    Y = 4.0 * A + 2.0 * W1 - 1.5 * W2 + np.random.normal(0, 0.5, size=n)

    records = [
        {"y": float(Y[i]), "a": int(A[i]), "w1": float(W1[i]), "w2": float(W2[i])}
        for i in range(n)
    ]

    res = run_targeted_maximum_likelihood_estimation(
        records=records,
        outcome_col="y",
        treatment_col="a",
        covariate_cols=["w1", "w2"],
        alpha_level=0.05
    )

    assert res["status"] == "success"
    assert res["sample_size"] == 120
    assert res["n_treated"] > 10
    assert res["n_control"] > 10
    assert "ate_tmle" in res
    # Estimated ATE should be close to true +4.0
    assert res["ate_tmle"]["estimate"] > 2.5
    assert res["ate_tmle"]["p_value"] < 0.05
    assert "targeted_fluctuation" in res
    assert res["targeted_fluctuation"]["equation_solved"] is True
    assert "estimators_comparison" in res
    assert len(res["estimators_comparison"]) == 4
    assert "svg_visualization" in res
    assert "<svg" in res["svg_visualization"]
    assert "apa_narrative" in res
