import numpy as np
import pytest
from app.engine.qte_engine import QTEEngine


def test_qte_compensatory_treatment():
    np.random.seed(42)
    N = 100
    # Confounder X (e.g. baseline capability)
    X = np.random.normal(0, 1, (N, 2))
    
    # Treatment assignment D based on X
    propensity = 1.0 / (1.0 + np.exp(-(0.5 * X[:, 0] - 0.3 * X[:, 1])))
    D = (np.random.uniform(0, 1, N) < propensity).astype(int)

    # Ensure both groups have at least 15
    while np.sum(D == 1) < 15 or np.sum(D == 0) < 15:
        D = (np.random.uniform(0, 1, N) < 0.5).astype(int)

    # Outcome Y: baseline + effect
    # Ground truth: treatment boosts low-scoring individuals more (compensatory)
    # Control: Y0 = 10 + 2*X1 + eps
    # Treated: Y1 = 10 + 2*X1 + 5.0 - 0.5*(10 + 2*X1) + eps
    base = 10.0 + 2.0 * X[:, 0] + np.random.normal(0, 1, N)
    treatment_effect = np.where(D == 1, 6.0 - 0.2 * base, 0.0)
    Y = base + treatment_effect

    res = QTEEngine.estimate(
        outcomes=Y,
        treatment=D,
        covariates=X,
        quantiles=[0.10, 0.25, 0.50, 0.75, 0.90]
    )

    assert res["status"] == "success"
    assert res["sample_size"] <= N
    assert res["treated_count"] >= 10
    assert res["control_count"] >= 10
    assert "average_treatment_effect" in res
    assert "median_treatment_effect" in res
    assert "delta_iqr_effect" in res
    assert len(res["quantile_effects"]) == 5
    
    for q_item in res["quantile_effects"]:
        assert "quantile" in q_item
        assert "qte" in q_item
        assert "std_error" in q_item
        assert q_item["std_error"] > 0
        assert "ci_95_lower" in q_item
        assert "ci_95_upper" in q_item
        assert q_item["ci_95_lower"] < q_item["ci_95_upper"]

    assert "<svg" in res["svg_chart"]
    assert "Semiparametric Quantile Treatment Effects" in res["apa_narrative"]


def test_qte_insufficient_sample():
    # Only 5 treated
    Y = np.ones(15)
    D = np.array([1]*5 + [0]*10)
    res = QTEEngine.estimate(outcomes=Y, treatment=D)
    assert res["status"] == "insufficient_data"
    assert "tối thiểu 10" in res["message"]
