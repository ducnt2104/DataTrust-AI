import pytest
import numpy as np
from app.engine.shapley_driver_engine import ShapleyDriverEngine


def test_shapley_driver_engine_success():
    np.random.seed(42)
    N = 60

    # 3 collinear drivers: Speed, Usability, Price
    speed = np.random.uniform(2.0, 5.0, N)
    usability = 0.7 * speed + np.random.normal(0, 0.4, N)
    price = np.random.uniform(1.0, 5.0, N)

    # Outcome Y strongly driven by Speed (weight 0.8), minor Usability (0.2), and low Price (-0.3)
    y = 0.8 * speed + 0.2 * usability - 0.3 * price + np.random.normal(0, 0.3, N)

    X_matrix = np.column_stack([speed, usability, price]).tolist()
    y_vector = y.tolist()
    names = ["Platform Speed", "System Usability", "Price Fairness"]

    res = ShapleyDriverEngine.compute_key_drivers(
        X_matrix=X_matrix,
        y_vector=y_vector,
        driver_names=names,
        outcome_name="Overall NPS Satisfaction"
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "SHAPLEY_VALUE_KEY_DRIVER_ANALYSIS"
    diag = res["diagnostics"]
    assert diag["sample_size"] == 60
    assert diag["n_drivers"] == 3
    assert diag["full_model_r2"] > 0.60
    # Axiom of Efficiency: sum of Shapley delta R^2 == full R^2
    assert abs(diag["full_model_r2"] - diag["sum_shapley_contributions"]) < 1e-4

    # Top driver should be Platform Speed
    drivers = res["drivers"]
    assert len(drivers) == 3
    total_share = sum(d["importance_share_pct"] for d in drivers)
    assert abs(total_share - 100.0) < 0.5
    assert drivers[0]["driver_name"] == "Platform Speed"

    # SVG and APA narrative presence
    assert "<svg" in res["svg_visualization"]
    assert "APA 7th Edition" in res["apa_narrative"]
    assert "Lipovetsky & Conklin" in res["apa_narrative"]


def test_shapley_driver_insufficient_sample():
    res = ShapleyDriverEngine.compute_key_drivers(
        X_matrix=[[1.0, 2.0], [2.0, 3.0]],
        y_vector=[1.0, 2.0],
        driver_names=["D1", "D2"],
        outcome_name="Y"
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_shapley_driver_insufficient_drivers():
    res = ShapleyDriverEngine.compute_key_drivers(
        X_matrix=[[1.0] for _ in range(30)],
        y_vector=[float(i) for i in range(30)],
        driver_names=["D1"],
        outcome_name="Y"
    )
    assert res["status"] == "INSUFFICIENT_DRIVERS"
