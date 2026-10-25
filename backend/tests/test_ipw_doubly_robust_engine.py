import pytest
import numpy as np
from app.engine.ipw_doubly_robust_engine import IPWDoublyRobustEngine


def test_ipw_doubly_robust_engine_basic_estimation():
    # Giả lập 100 quan sát với confounding
    np.random.seed(42)
    n = 120
    # Covariate X1 (tuổi, chuẩn hóa), X2 (thu nhập, chuẩn hóa)
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(0, 1, n)
    
    # Propensity to receive treatment D depends on X1 and X2
    z = 0.5 * x1 + 0.3 * x2
    p_true = 1.0 / (1.0 + np.exp(-z))
    d = (np.random.uniform(0, 1, n) < p_true).astype(int)
    
    # Ensure both groups have enough samples
    if np.sum(d) < 10:
        d[:15] = 1
    if np.sum(1 - d) < 10:
        d[-15:] = 0

    # True treatment effect tau = 3.5, with confounding from X1
    y = 2.0 + 3.5 * d + 1.2 * x1 + 0.8 * x2 + np.random.normal(0, 0.5, n)

    data_rows = [
        {"treated": int(d[i]), "outcome": float(y[i]), "cov1": float(x1[i]), "cov2": float(x2[i])}
        for i in range(n)
    ]

    res = IPWDoublyRobustEngine.estimate_causal_effects(
        data_rows=data_rows,
        treatment_key="treated",
        outcome_key="outcome",
        covariate_keys=["cov1", "cov2"],
        weight_scheme="ate",
        trim_weights=True,
        labels={"treated": "Can thiệp", "outcome": "Điểm hài lòng", "cov1": "Tuổi", "cov2": "Thu nhập"}
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == n
    assert res["treated_count"] > 5
    assert res["control_count"] > 5
    assert res["weight_scheme"] == "ATE"
    
    # Estimated effect should be reasonably close to 3.5
    assert 2.0 < res["doubly_robust_estimator"]["treatment_effect"] < 5.0
    assert res["doubly_robust_estimator"]["is_significant"] is True
    assert res["ipw_estimator"]["is_significant"] is True
    
    # Balance diagnostics
    assert len(res["covariate_balance"]["diagnostics"]) == 2
    assert "svg_love_plot" in res
    assert "<svg" in res["svg_love_plot"]
    assert "apa_narrative" in res
    assert "APA 7th" in res["apa_narrative"] or "Rosenbaum & Rubin" in res["apa_narrative"]


def test_ipw_doubly_robust_schemes():
    # Test ATT and Overlap schemes
    np.random.seed(123)
    data = []
    for i in range(60):
        t = 1 if i % 2 == 0 else 0
        c = float(i % 5)
        out = 10.0 + 2.5 * t + 0.5 * c
        data.append({"t": t, "y": out, "c": c})

    res_att = IPWDoublyRobustEngine.estimate_causal_effects(
        data_rows=data,
        treatment_key="t",
        outcome_key="y",
        covariate_keys=["c"],
        weight_scheme="att"
    )
    assert res_att["status"] == "SUCCESS"
    assert res_att["weight_scheme"] == "ATT"

    res_overlap = IPWDoublyRobustEngine.estimate_causal_effects(
        data_rows=data,
        treatment_key="t",
        outcome_key="y",
        covariate_keys=["c"],
        weight_scheme="overlap"
    )
    assert res_overlap["status"] == "SUCCESS"
    assert res_overlap["weight_scheme"] == "OVERLAP"


def test_ipw_doubly_robust_edge_cases():
    # 1. Missing covariates
    res_no_cov = IPWDoublyRobustEngine.estimate_causal_effects(
        data_rows=[{"t": 1, "y": 2}],
        treatment_key="t",
        outcome_key="y",
        covariate_keys=[]
    )
    assert res_no_cov["status"] == "INVALID_SPECIFICATION"

    # 2. Insufficient samples
    res_few = IPWDoublyRobustEngine.estimate_causal_effects(
        data_rows=[{"t": 1, "y": 2, "c": 3} for _ in range(5)],
        treatment_key="t",
        outcome_key="y",
        covariate_keys=["c"]
    )
    assert res_few["status"] == "INSUFFICIENT_SAMPLE"
