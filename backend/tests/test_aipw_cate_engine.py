"""
Unit tests for Doubly Robust AIPW & Heterogeneous CATE Engine.
"""

import numpy as np
import pytest
from app.engine.aipw_cate_engine import AIPWCATEEngine


def test_aipw_cate_unbiasedness_under_confounding():
    """
    Verify Doubly Robust AIPW recovers true treatment effect under confounding.
    """
    np.random.seed(42)
    N = 350
    # Confounders X1, X2
    X1 = np.random.normal(0, 1, N)
    X2 = np.random.normal(0, 1, N)
    X = np.column_stack([X1, X2])

    # Propensity depends on X1, X2
    logits = 0.8 * X1 - 0.5 * X2
    probs = 1.0 / (1.0 + np.exp(-logits))
    W = (np.random.rand(N) < probs).astype(float)

    # True treatment effect tau = 3.5
    true_tau = 3.5
    # Outcome model with confounding
    Y = 2.0 + 1.5 * X1 + 2.0 * X2 + true_tau * W + np.random.normal(0, 0.5, N)

    res = AIPWCATEEngine.estimate(W=W, Y=Y, X=X, trim_alpha=0.05)

    assert res["status"] == "success"
    assert "ate" in res
    assert np.isclose(res["ate"], true_tau, atol=0.45)
    assert res["is_significant"] is True
    assert res["p_value"] < 0.001
    assert res["ci_95_lower"] <= true_tau <= res["ci_95_upper"]
    assert "svg_chart" in res
    assert "<svg" in res["svg_chart"]
    assert "apa_narrative" in res
    assert len(res["apa_narrative"]) > 50


def test_aipw_cate_subgroup_heterogeneity():
    """
    Verify CATE detects significant treatment effect heterogeneity between subgroups.
    """
    np.random.seed(123)
    N = 400
    X = np.random.normal(0, 1, (N, 2))
    W = np.random.binomial(1, 0.5, N).astype(float)

    # Subgroups: Youth vs Senior
    subgroups = ["Youth" if i < 200 else "Senior" for i in range(N)]

    # Youth has treatment effect +5.0, Senior has treatment effect -1.0
    Y = np.zeros(N)
    for i in range(N):
        tau_i = 5.0 if subgroups[i] == "Youth" else -1.0
        Y[i] = 10.0 + 1.2 * X[i, 0] + tau_i * W[i] + np.random.normal(0, 0.5)

    res = AIPWCATEEngine.estimate(W=W, Y=Y, X=X, subgroups=subgroups, trim_alpha=0.05)

    assert res["status"] == "success"
    assert len(res["subgroup_cate"]) == 2
    youth_res = next(s for s in res["subgroup_cate"] if s["subgroup"] == "Youth")
    senior_res = next(s for s in res["subgroup_cate"] if s["subgroup"] == "Senior")

    assert youth_res["cate"] > 4.0
    assert senior_res["cate"] < 0.0
    assert res["heterogeneity_test"]["is_heterogeneous"] is True
    assert res["heterogeneity_test"]["p_value"] < 0.01


def test_aipw_cate_edge_cases():
    """
    Verify graceful error handling on small or imbalanced data.
    """
    W = np.array([1, 1, 1, 0, 0])
    Y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    X = np.ones((5, 1))

    res = AIPWCATEEngine.estimate(W=W, Y=Y, X=X)
    assert res["status"] == "insufficient_data"
    assert "tối thiểu 10 quan sát" in res["message"]
