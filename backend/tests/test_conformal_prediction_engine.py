import pytest
import numpy as np
from app.engine.conformal_prediction_engine import ConformalPredictionEngine


def test_conformal_prediction_insufficient_records():
    # Less than 15 records
    records = [{"x": 1.0, "y": 2.0} for _ in range(10)]
    res = ConformalPredictionEngine.fit_and_predict(
        records=records,
        target_field="y",
        feature_fields=["x"]
    )
    assert res["status"] == "error"
    assert "tối thiểu 15" in res["message"]


def test_conformal_prediction_invalid_alpha():
    records = [{"x": float(i), "y": float(i * 2)} for i in range(25)]
    res = ConformalPredictionEngine.fit_and_predict(
        records=records,
        target_field="y",
        feature_fields=["x"],
        alpha=1.5
    )
    assert res["status"] == "error"
    assert "alpha" in res["message"]


def test_conformal_prediction_standard_split():
    np.random.seed(42)
    n = 60
    records = []
    for i in range(n):
        x1 = float(np.random.uniform(1.0, 5.0))
        x2 = float(np.random.uniform(10.0, 50.0))
        # Non-gaussian skewed noise
        noise = float(np.random.exponential(scale=0.5))
        y = 2.0 + 0.8 * x1 + 0.05 * x2 + noise
        records.append({"q1": x1, "q2": x2, "satisfaction": y})

    res = ConformalPredictionEngine.fit_and_predict(
        records=records,
        target_field="satisfaction",
        feature_fields=["q1", "q2"],
        alpha=0.10,  # 90% coverage
        method="split_conformal",
        seed=42
    )

    assert res["status"] == "success"
    assert res["method"] == "split_conformal"
    assert res["parameters"]["nominal_coverage"] == 0.90
    assert res["parameters"]["conformal_quantile"] > 0
    assert res["evaluation_metrics"]["conformal_coverage"] >= 0.75
    assert len(res["calibration_curve"]) > 0
    assert len(res["sample_predictions"]) > 0
    assert "<svg" in res["svg_chart"]
    assert "Conformal Prediction" in res["apa_narrative"]


def test_conformal_prediction_locally_weighted_and_clamping():
    np.random.seed(123)
    n = 80
    records = []
    for i in range(n):
        x = float(np.random.uniform(1.0, 10.0))
        # Heteroscedastic noise proportional to x
        noise = float(np.random.normal(0.0, 0.2 * x))
        y = np.clip(1.0 + 0.3 * x + noise, 1.0, 5.0)
        records.append({"x": x, "score": float(y)})

    res = ConformalPredictionEngine.fit_and_predict(
        records=records,
        target_field="score",
        feature_fields=["x"],
        alpha=0.05,  # 95% coverage
        method="locally_weighted",
        clamp_min=1.0,
        clamp_max=5.0,
        seed=123
    )

    assert res["status"] == "success"
    assert res["method"] == "locally_weighted"
    # Check that sample prediction bounds satisfy clamping
    for p in res["sample_predictions"]:
        assert p["lower_bound"] >= 1.0 - 1e-4
        assert p["upper_bound"] <= 5.0 + 1e-4
    assert res["evaluation_metrics"]["conformal_mean_width"] > 0
    assert "<svg" in res["svg_chart"]
