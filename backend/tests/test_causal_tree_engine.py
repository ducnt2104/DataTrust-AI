import pytest
import numpy as np
from app.engine.causal_tree_engine import run_causal_interaction_tree


def test_causal_tree_no_features():
    records = [{"t": 1, "y": 2.0} for _ in range(40)]
    res = run_causal_interaction_tree(records, "t", "y", [])
    assert res["status"] == "error"
    assert "ít nhất một biến" in res["message"]


def test_causal_tree_insufficient_sample():
    records = [{"t": 1, "y": 2.0, "x1": 3.0} for _ in range(12)]
    res = run_causal_interaction_tree(records, "t", "y", ["x1"])
    assert res["status"] == "error"
    assert "N=12" in res["message"]


def test_causal_tree_valid_subgroups():
    np.random.seed(42)
    n = 100
    records = []
    # 50 respondents with X1 <= 0: strong positive effect (tau = +4.0)
    # 50 respondents with X1 > 0: negative backfire effect (tau = -3.0)
    for i in range(n):
        x1 = float(np.random.uniform(-5.0, 5.0))
        x2 = float(np.random.uniform(1.0, 10.0))
        t = 1.0 if (i % 2 == 0) else 0.0
        base_y = 10.0 + 0.5 * x2 + float(np.random.normal(0, 0.5))

        tau = 4.0 if x1 <= 0.0 else -3.0
        y = base_y + tau * t

        records.append({
            "treatment": t,
            "outcome": y,
            "x1": x1,
            "x2": x2
        })

    res = run_causal_interaction_tree(
        records=records,
        treatment_col="treatment",
        outcome_col="outcome",
        feature_cols=["x1", "x2"],
        min_leaf_size=5
    )

    assert res["status"] == "success"
    assert res["sample_diagnostics"]["n_total"] == n
    assert res["sample_diagnostics"]["n_subgroups"] >= 2
    assert "ate_overall" in res["sample_diagnostics"]

    # Verify leaves
    leaves = res["subgroups"]
    taus = [l["tau_subgroup"] for l in leaves]
    assert max(taus) > 1.0   # Detected positive subgroup
    assert min(taus) < 0.0   # Detected negative backfire subgroup

    assert "<svg" in res["svg_chart"]
    assert "Athey & Imbens" in res["apa_narrative"]
