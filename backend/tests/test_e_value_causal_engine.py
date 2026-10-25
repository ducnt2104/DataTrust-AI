"""
Unit tests for Robust E-Values & Multi-Bias Causal Sensitivity Decomposition Engine
(VanderWeele & Ding 2017 Annals of Internal Medicine; Mathur & VanderWeele 2020)
DataTrust Iteration 185
"""

import pytest
import numpy as np
from app.engine.e_value_causal_engine import (
    calculate_e_value,
    convert_effect_to_rr,
    compute_e_values_and_multibias,
    run_e_value_sensitivity
)


def test_calculate_e_value_formula():
    # VanderWeele & Ding (2017) Table 1 verification:
    # RR = 1.0 -> E-value = 1.0
    assert calculate_e_value(1.0) == 1.0
    # RR = 2.0 -> E-value = 2.0 + sqrt(2.0 * 1.0) = 2.0 + 1.4142 = 3.4142
    e_val_2 = calculate_e_value(2.0)
    assert abs(e_val_2 - 3.4142) < 0.001

    # RR = 3.0 -> E-value = 3.0 + sqrt(3.0 * 2.0) = 3.0 + 2.4495 = 5.4495
    e_val_3 = calculate_e_value(3.0)
    assert abs(e_val_3 - 5.4495) < 0.001


def test_e_value_sensitivity_estimation_success():
    np.random.seed(42)
    N = 80
    T = np.random.binomial(1, 0.5, N)
    X = np.random.normal(0, 1, N)
    # Treatment effect = 4.0, SD(Y) ~ 4.0 -> Cohen's d ~ 1.0 -> RR ~ exp(0.91) ~ 2.48 -> E-value ~ 4.40
    Y = 15.0 + 4.0 * T + 1.2 * X + np.random.normal(0, 1.5, N)

    records = []
    for i in range(N):
        records.append({
            "treatment": int(T[i]),
            "outcome": float(Y[i]),
            "covariate": float(X[i])
        })

    res = run_e_value_sensitivity(
        records=records,
        treatment_col="treatment",
        outcome_col="outcome",
        covariate_cols=["covariate"],
        effect_type="OLS_CONTINUOUS",
        selection_bias_rr=1.1,
        misclassification_rr=1.05
    )

    assert res["status"] == "success"
    assert res["sample_size"] == N
    assert res["point_estimate"] > 3.0

    eval_data = res["e_value_results"]
    assert eval_data["e_value_estimate"] > 2.0
    assert eval_data["e_value_ci"] > 1.0
    assert eval_data["selection_bias_factor"] == 1.1
    assert eval_data["misclassification_factor"] == 1.05

    assert len(res["benchmarks"]) == 4
    assert "<svg" in res["svg_visualization"]
    assert "DataTrust" in res["apa_narrative"]


def test_e_value_insufficient_sample():
    records = [{"treatment": 1, "outcome": 10.0}] * 10
    with pytest.raises(ValueError, match="Cần tối thiểu 20 quan sát"):
        run_e_value_sensitivity(records, "treatment", "outcome")
