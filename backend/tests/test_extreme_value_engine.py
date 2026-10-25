import pytest
import numpy as np
from app.engine.extreme_value_engine import ExtremeValueEngine


def test_extreme_value_engine_success():
    np.random.seed(42)
    # Generate heavy-tailed Pareto sample
    # Pareto Type II / Lomax or standard Pareto
    base = np.random.pareto(a=2.5, size=200) * 10.0 + 5.0
    data = base.tolist()

    res = ExtremeValueEngine.estimate(
        data=data,
        threshold_percentile=0.85,
        alpha_levels=[0.95, 0.99]
    )

    assert res["status"] == "success"
    assert res["sample_size"] == 200
    assert res["threshold"] > 0
    assert res["exceedances_count"] >= 10
    assert res["scale_sigma"] > 0
    assert "tail_classification" in res
    assert len(res["risk_measures"]) == 2
    assert res["risk_measures"][0]["confidence_level"] == 0.95
    assert res["risk_measures"][0]["var_p"] > res["threshold"]
    assert "<svg" in res["svg_chart"]
    assert "APA 7th" in res["apa_narrative"] or "Pickands" in res["apa_narrative"]


def test_extreme_value_engine_insufficient_sample():
    small_data = [1.0, 2.0, 3.0, 4.0]
    res = ExtremeValueEngine.estimate(small_data)
    assert res["status"] == "error"
    assert "Cỡ mẫu quá nhỏ" in res["message"]


def test_extreme_value_engine_too_high_threshold():
    np.random.seed(42)
    data = np.random.normal(10, 2, 50).tolist()
    res = ExtremeValueEngine.estimate(data, custom_threshold=999.0)
    assert res["status"] == "error"
    assert "Số lượng quan sát vượt ngưỡng quá ít" in res["message"]
