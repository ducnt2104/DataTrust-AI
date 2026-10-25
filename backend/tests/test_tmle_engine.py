import pytest
import numpy as np
from app.engine.tmle_engine import TMLEEngine


def test_tmle_insufficient_records():
    records = [{"a": 1, "y": 3.0, "w": 2.0} for _ in range(10)]
    res = TMLEEngine.estimate_ate(
        records=records,
        treatment_field="a",
        outcome_field="y",
        covariate_fields=["w"]
    )
    assert res["status"] == "error"
    assert "tối thiểu 20" in res["message"]


def test_tmle_unbalanced_treatment():
    # Only 2 treated units
    records = []
    for i in range(25):
        records.append({
            "a": 1 if i < 2 else 0,
            "y": float(i),
            "w": float(i * 0.5)
        })
    res = TMLEEngine.estimate_ate(
        records=records,
        treatment_field="a",
        outcome_field="y",
        covariate_fields=["w"]
    )
    assert res["status"] == "error"
    assert "tối thiểu 5 mẫu" in res["message"]


def test_tmle_valid_continuous_outcome():
    np.random.seed(42)
    n = 60
    records = []
    for i in range(n):
        w1 = float(np.random.normal(0.0, 1.0))
        w2 = float(np.random.uniform(1.0, 5.0))
        # Treatment assignment dependent on confounders (confounding bias)
        ps_logit = 0.5 * w1 - 0.3 * (w2 - 3.0)
        ps = 1.0 / (1.0 + np.exp(-ps_logit))
        a = 1 if np.random.uniform() < ps else 0

        # True causal effect of A is +1.5
        y = 2.0 + 1.5 * a + 0.8 * w1 + 0.4 * w2 + float(np.random.normal(0.0, 0.5))

        records.append({
            "treatment": a,
            "outcome": y,
            "cov1": w1,
            "cov2": w2
        })

    res = TMLEEngine.estimate_ate(
        records=records,
        treatment_field="treatment",
        outcome_field="outcome",
        covariate_fields=["cov1", "cov2"]
    )

    assert res["status"] == "success"
    assert res["sample_diagnostics"]["n_total"] == 60
    assert res["sample_diagnostics"]["n_treated"] > 5
    assert res["sample_diagnostics"]["n_control"] > 5

    # Check targeted parameters
    params = res["targeted_parameters"]
    assert "targeted_tmle_ate" in params
    assert "se_tmle" in params
    assert "ci_95_lower" in params
    assert "ci_95_upper" in params
    assert params["ci_95_lower"] < params["ci_95_upper"]
    # Check that TMLE estimate is positive and close to true 1.5
    assert 0.5 <= params["targeted_tmle_ate"] <= 2.5

    # Check comparison estimators
    assert len(res["estimator_comparisons"]) == 4
    assert "<svg" in res["svg_chart"]
    assert "APA 7th Standard" in res["apa_narrative"]
