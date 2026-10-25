import pytest
import numpy as np
from app.engine.causal_forest_engine import CausalForestEngine


def test_causal_forest_insufficient_records():
    records = [{"a": 1, "y": 2.0, "x1": 3.0} for _ in range(15)]
    res = CausalForestEngine.estimate_heterogeneity(
        records=records,
        treatment_field="a",
        outcome_field="y",
        feature_fields=["x1"]
    )
    assert res["status"] == "error"
    assert "tối thiểu 25" in res["message"]


def test_causal_forest_no_features():
    records = [{"a": 1, "y": 2.0} for _ in range(30)]
    res = CausalForestEngine.estimate_heterogeneity(
        records=records,
        treatment_field="a",
        outcome_field="y",
        feature_fields=[]
    )
    assert res["status"] == "error"
    assert "ít nhất một biến đặc trưng" in res["message"]


def test_causal_forest_valid_estimation():
    np.random.seed(42)
    n = 70
    records = []

    for i in range(n):
        age = float(np.random.uniform(20.0, 60.0))
        income = float(np.random.uniform(10.0, 50.0))
        a = 1 if (i % 2 == 0) else 0

        # Strong heterogeneity: treatment is more effective for older individuals
        # tau(X) = 1.0 + 0.1 * (age - 40.0)
        true_tau = 1.0 + 0.1 * (age - 40.0)
        noise = float(np.random.normal(0.0, 0.4))
        y = 5.0 + true_tau * a + 0.05 * income + noise

        records.append({
            "treated": a,
            "satisfaction": y,
            "age": age,
            "income": income
        })

    res = CausalForestEngine.estimate_heterogeneity(
        records=records,
        treatment_field="treated",
        outcome_field="satisfaction",
        feature_fields=["age", "income"],
        n_trees=30,
        min_leaf_size=5,
        seed=42
    )

    assert res["status"] == "success"
    assert res["sample_diagnostics"]["n_total"] == 70
    assert res["sample_diagnostics"]["n_trees_built"] > 0

    # Check CATE summary
    summary = res["cate_summary"]
    assert "ate_overall" in summary
    assert "cate_std" in summary
    assert "high_responders_avg_tau" in summary
    assert "low_responders_avg_tau" in summary
    # High responders should have larger treatment effect than low responders
    assert summary["high_responders_avg_tau"] >= summary["low_responders_avg_tau"]

    # Check variable importance: age should be the primary driver
    assert len(res["variable_importance"]) == 2
    top_var = res["variable_importance"][0]["feature"]
    assert top_var == "age"

    assert len(res["cate_distribution"]) > 0
    assert "<svg" in res["svg_chart"]
    assert "APA 7th Standard" in res["apa_narrative"]
