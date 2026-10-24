import pytest
import numpy as np
from app.engine.policy_learning_engine import PolicyLearningEngine


def test_policy_learning_synthetic_data():
    np.random.seed(42)
    n = 120
    # Covariates: X1 is age/income, X2 is education
    x1 = np.random.uniform(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    x_mat = np.column_stack([x1, x2])

    # Heterogeneous treatment effect: benefit if x1 > 0.5, harm if x1 < 0.5
    tau_true = 3.0 * (x1 - 0.5)  # mean effect is 0, but optimal policy treats half
    propensity = 0.5
    w = np.random.binomial(1, propensity, n).astype(float)
    y0 = 10.0 + 2.0 * x1 + 1.5 * x2 + np.random.normal(0, 0.2, n)
    y = y0 + w * tau_true

    res = PolicyLearningEngine.evaluate(
        y=y,
        w=w,
        x_matrix=x_mat,
        feature_names=["Đặc tính X1", "Đặc tính X2"],
        primary_feature_idx=0,
        n_bootstraps=100
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "DOUBLY_ROBUST_POLICY_LEARNING_ATHEY_WAGER_2021"
    diag = res["diagnostics"]
    assert diag["sample_size"] == n
    assert 20.0 < diag["pct_recommended_treatment"] < 80.0
    assert diag["net_welfare_gain"] >= 0.0
    assert len(res["regimes_comparison"]) == 4
    assert len(res["sample_allocations"]) > 0
    assert "<svg" in res["svg_visualization"]
    assert "Athey & Wager" in res["apa_narrative"] or "Học Chính sách Kép Vững" in res["apa_narrative"]


def test_policy_learning_insufficient_sample():
    y = np.ones(10)
    w = np.zeros(10)
    x = np.ones((10, 2))
    res = PolicyLearningEngine.evaluate(y, w, x, ["X1", "X2"])
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_policy_learning_insufficient_treated():
    n = 30
    y = np.ones(n)
    w = np.zeros(n)  # 0 treated
    x = np.random.normal(0, 1, (n, 2))
    res = PolicyLearningEngine.evaluate(y, w, x, ["X1", "X2"])
    assert res["status"] == "INSUFFICIENT_VARIATION"
