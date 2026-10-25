"""
Tests for DataTrust Entropy Balancing & Exact Moment-Condition Causal Reweighting Engine.
"""

import pytest
import numpy as np
from app.engine.entropy_balancing_engine import (
    compute_moments,
    entropy_balance_weights,
    calculate_balance_metrics,
    estimate_att_and_se,
    run_entropy_balancing
)


def test_entropy_balancing_estimation_success():
    np.random.seed(42)
    N = 200
    # Covariates
    X1 = np.random.normal(5.0, 2.0, N)
    X2 = np.random.normal(10.0, 3.0, N)
    
    # Treatment with selection bias on X1 and X2
    z = -3.0 + 0.4 * X1 + 0.2 * X2
    prob = 1.0 / (1.0 + np.exp(-z))
    T = (np.random.uniform(0, 1, N) < prob).astype(int)

    # True treatment effect = 4.5
    true_tau = 4.5
    Y = 20.0 + true_tau * T + 2.0 * X1 + 1.5 * X2 + np.random.normal(0, 1.0, N)

    records = []
    for i in range(N):
        records.append({
            "treatment": int(T[i]),
            "outcome": float(Y[i]),
            "x1": float(X1[i]),
            "x2": float(X2[i])
        })

    res = run_entropy_balancing(
        records=records,
        treatment_col="treatment",
        outcome_col="outcome",
        covariate_cols=["x1", "x2"],
        moment_orders=[1, 2]
    )

    assert res["status"] == "success"
    assert res["sample_size"] == N
    assert res["treated_count"] > 10
    assert res["control_count"] > 10

    # Verify that post-weighting SMDs are effectively zero or < 0.05
    for bal in res["covariate_balance"]:
        assert abs(bal["smd_weighted"]) < 0.05
        assert abs(bal["smd_weighted"]) < abs(bal["smd_unweighted"])

    # ATT estimate should be close to true_tau (4.5)
    att_info = res["treatment_effect"]
    assert abs(att_info["att"] - true_tau) < 1.0
    assert att_info["p_value"] < 0.05

    # Check diagnostics
    assert res["diagnostics"]["converged"] is True
    assert res["diagnostics"]["effective_sample_size"] > 5.0
    assert "<svg" in res["svg_visualization"]
    assert "DataTrust" in res["apa_narrative"]


def test_entropy_balancing_insufficient_sample():
    records = [{"treatment": 1, "outcome": 10.0, "x": 1.0}] * 8
    with pytest.raises(ValueError, match="Cần tối thiểu 15 quan sát"):
        run_entropy_balancing(records, "treatment", "outcome", ["x"])


def test_entropy_balancing_empty_covariates():
    records = [{"treatment": 1, "outcome": 10.0, "x": 1.0}] * 25
    with pytest.raises(ValueError, match="Cần cung cấp ít nhất một biến đồng biến"):
        run_entropy_balancing(records, "treatment", "outcome", [])
