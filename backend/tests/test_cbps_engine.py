"""
Unit tests for Covariate Balancing Propensity Score Engine (CBPS)
(Imai & Ratkovic 2014 JRSS-B; Fong et al. 2018)
DataTrust Iteration 184
"""

import pytest
import numpy as np
from app.engine.cbps_engine import (
    sigmoid,
    estimate_cbps,
    calculate_cbps_weights,
    calculate_cbps_balance,
    estimate_cbps_causal_effect,
    run_cbps_analysis
)


def test_cbps_estimation_success():
    np.random.seed(42)
    N = 120
    X1 = np.random.normal(0, 1, N)
    X2 = np.random.normal(2, 1, N)

    # Treatment selection
    logit_p = 0.5 * X1 - 0.4 * X2 + 0.2
    prob = 1.0 / (1.0 + np.exp(-logit_p))
    T = (np.random.uniform(0, 1, N) < prob).astype(int)

    # True treatment effect = 3.5
    true_tau = 3.5
    Y = 10.0 + true_tau * T + 1.5 * X1 + 2.0 * X2 + np.random.normal(0, 1.0, N)

    records = []
    for i in range(N):
        records.append({
            "treatment": int(T[i]),
            "outcome": float(Y[i]),
            "x1": float(X1[i]),
            "x2": float(X2[i])
        })

    res = run_cbps_analysis(
        records=records,
        treatment_col="treatment",
        outcome_col="outcome",
        covariate_cols=["x1", "x2"],
        method="overidentified",
        estimand="ATE"
    )

    assert res["status"] == "success"
    assert res["sample_size"] == N
    assert res["treated_count"] > 10
    assert res["control_count"] > 10

    # Verify that post-weighting SMDs are well controlled
    for bal in res["covariate_balance"]:
        assert abs(bal["smd_weighted"]) < 0.15
        assert abs(bal["smd_weighted"]) < abs(bal["smd_raw"])

    # Causal effect estimate close to 3.5
    eff = res["causal_effect"]
    assert abs(eff["effect"] - true_tau) < 1.0
    assert eff["p_value"] < 0.05

    # Check Hansen J test diagnostics
    diag = res["diagnostics"]
    assert diag["converged"] is True
    assert "hansen_j_stat" in diag
    assert "hansen_j_p_value" in diag
    assert "<svg" in res["svg_visualization"]
    assert "DataTrust" in res["apa_narrative"]


def test_cbps_insufficient_sample():
    records = [{"treatment": 1, "outcome": 5.0, "x1": 1.0}] * 10
    with pytest.raises(ValueError, match="Cần tối thiểu 20 quan sát"):
        run_cbps_analysis(records, "treatment", "outcome", ["x1"])


def test_cbps_empty_covariates():
    records = [{"treatment": 1, "outcome": 5.0, "x1": 1.0}] * 30
    with pytest.raises(ValueError, match="Cần cung cấp ít nhất một biến đồng biến"):
        run_cbps_analysis(records, "treatment", "outcome", [])
