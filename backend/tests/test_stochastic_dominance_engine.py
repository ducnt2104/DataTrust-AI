import numpy as np
import pytest
from app.engine.stochastic_dominance_engine import StochasticDominanceEngine, _compute_gini_coefficient


def test_gini_coefficient():
    # Perfectly equal distribution
    equal = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
    gini_eq = _compute_gini_coefficient(equal)
    assert gini_eq == pytest.approx(0.0, abs=1e-4)

    # Unequal distribution
    unequal = np.array([1.0, 2.0, 3.0, 10.0, 50.0])
    gini_uneq = _compute_gini_coefficient(unequal)
    assert 0.5 <= gini_uneq <= 0.85


def test_first_order_stochastic_dominance():
    np.random.seed(42)
    # Group A clearly shifted higher than Group B
    group_a = np.random.normal(loc=7.5, scale=0.8, size=40)
    group_b = np.random.normal(loc=4.5, scale=0.8, size=40)

    res = StochasticDominanceEngine.evaluate_dominance(
        values_a=group_a,
        values_b=group_b,
        label_a="Premium Users",
        label_b="Standard Users",
        outcome_label="Net Promoter Score"
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "STOCHASTIC_DOMINANCE_DAVIDSON_DUCLOS_2000"
    diag = res["diagnostics"]
    assert diag["sample_size_a"] == 40
    assert diag["sample_size_b"] == 40
    assert diag["mean_a"] > diag["mean_b"]
    assert diag["fsd_dominant_group"] == "A"
    assert "vượt trội Bậc 1" in diag["fsd_conclusion"]
    assert diag["ssd_dominant_group"] == "A"
    assert "<svg" in res["svg_visualization"]
    assert "Davidson & Duclos" in res["apa_narrative"]
    assert len(res["grid_thresholds"]) > 5


def test_second_order_stochastic_dominance_risk_aversion():
    np.random.seed(42)
    # Mean-preserving spread: same mean (5.0), but Group A has much lower variance than Group B
    group_a = np.random.normal(loc=5.0, scale=0.3, size=50)
    group_b = np.random.normal(loc=5.0, scale=2.0, size=50)

    res = StochasticDominanceEngine.evaluate_dominance(
        values_a=group_a,
        values_b=group_b,
        label_a="Consistent Quality",
        label_b="Volatile Quality",
        outcome_label="Product Rating"
    )

    assert res["status"] == "SUCCESS"
    diag = res["diagnostics"]
    # FSD is indeterminate because distributions cross
    assert diag["fsd_dominant_group"] == "INDETERMINATE"
    # SSD: Low risk Group A dominates volatile Group B for risk-averse agents
    assert diag["ssd_dominant_group"] == "A"
    assert "vượt trội Bậc 2" in diag["ssd_conclusion"]


def test_insufficient_sample():
    # Only 5 samples
    a = np.array([1, 2, 3, 4, 5])
    b = np.array([2, 3, 4, 5, 6])

    res = StochasticDominanceEngine.evaluate_dominance(values_a=a, values_b=b)
    assert res["status"] == "INSUFFICIENT_SAMPLE"
    assert "Kích thước mẫu không đủ" in res["message"]
