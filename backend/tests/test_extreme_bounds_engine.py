import pytest
import numpy as np
from app.engine.extreme_bounds_engine import ExtremeBoundsEngine


def test_extreme_bounds_robust_positive():
    np.random.seed(42)
    n = 120

    # Strong positive relationship
    p = np.random.normal(5.0, 1.5, n)
    z1 = np.random.normal(0, 1, n)
    z2 = np.random.normal(0, 1, n)
    z3 = np.random.normal(0, 1, n)
    z4 = np.random.normal(0, 1, n)

    y = 2.5 * p + 0.8 * z1 - 0.6 * z2 + 0.3 * z3 + np.random.normal(0, 0.5, n)

    data = []
    for i in range(n):
        data.append({
            "y": float(y[i]),
            "p": float(p[i]),
            "z1": float(z1[i]),
            "z2": float(z2[i]),
            "z3": float(z3[i]),
            "z4": float(z4[i]),
        })

    res = ExtremeBoundsEngine.analyze(
        data=data,
        focus_var="p",
        outcome_var="y",
        candidate_vars=["z1", "z2", "z3", "z4"],
    )

    assert res["status"] == "success"
    summary = res["summary"]
    assert summary["n_samples"] == n
    assert summary["total_models_evaluated"] > 10
    assert summary["mean_beta"] > 2.0
    assert summary["sala_i_martin_cdf"] >= 0.99
    assert summary["sala_i_martin_verdict"] == "ROBUST"
    assert summary["leamer_verdict"] == "ROBUST_POSITIVE"
    assert summary["significant_models_fraction"] == 1.0
    assert "<svg" in res["svg_chart"]
    assert "APA" not in res["apa_narrative"] or "Phân tích Cực trị" in res["apa_narrative"]
    assert len(res["specifications_sample"]) > 0


def test_extreme_bounds_fragile():
    np.random.seed(123)
    n = 60

    # Weak/spurious relationship
    p = np.random.normal(0, 1, n)
    z1 = np.random.normal(0, 1, n)
    z2 = np.random.normal(0, 1, n)
    y = 0.05 * p + 1.2 * z1 - 0.9 * z2 + np.random.normal(0, 1.5, n)

    data = []
    for i in range(n):
        data.append({
            "y": float(y[i]),
            "p": float(p[i]),
            "z1": float(z1[i]),
            "z2": float(z2[i]),
        })

    res = ExtremeBoundsEngine.analyze(
        data=data,
        focus_var="p",
        outcome_var="y",
        candidate_vars=["z1", "z2"],
    )

    assert res["status"] == "success"
    summary = res["summary"]
    assert summary["leamer_verdict"] == "FRAGILE"
    assert summary["leamer_lower_bound"] < 0
    assert summary["leamer_upper_bound"] > 0


def test_extreme_bounds_insufficient_data():
    data = [{"y": 1.0, "p": 2.0, "z1": 0.5}] * 5
    res = ExtremeBoundsEngine.analyze(
        data=data,
        focus_var="p",
        outcome_var="y",
        candidate_vars=["z1"],
    )
    assert res["status"] == "error"
    assert "không đủ quan sát" in res["message"]
