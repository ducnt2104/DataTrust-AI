import pytest
import numpy as np
from app.engine.spatial_econometrics_engine import SpatialEconometricsEngine


def test_spatial_econometrics_clustered():
    np.random.seed(42)
    n = 60

    # Create 3 spatial clusters (e.g., North, Central, South)
    cluster_centers = [
        (21.0285, 105.8542),  # Hanoi
        (16.0544, 108.2022),  # Danang
        (10.8231, 106.6297),  # HCMC
    ]

    data = []
    for i in range(n):
        c_idx = i % 3
        c_lat, c_lon = cluster_centers[c_idx]
        lat = c_lat + np.random.normal(0, 0.05)
        lon = c_lon + np.random.normal(0, 0.05)

        # Base regional effect creates strong spatial clustering
        reg_effect = [15.0, 5.0, -10.0][c_idx]
        x1 = np.random.normal(0, 1)
        y = reg_effect + 1.2 * x1 + np.random.normal(0, 1.0)

        data.append({
            "latitude": lat,
            "longitude": lon,
            "outcome_score": y,
            "covariate_x": x1,
        })

    res = SpatialEconometricsEngine.analyze(
        data=data,
        lat_field="latitude",
        lon_field="longitude",
        outcome_var="outcome_score",
        covariate_vars=["covariate_x"],
    )

    assert res["status"] == "success"
    moran = res["morans_i"]
    assert moran["morans_i"] > 0.4
    assert moran["p_value"] < 0.001
    assert moran["classification"] == "SPATIAL_CLUSTERING_POSITIVE"

    sar = res["spatial_lag_model"]
    assert "rho" in sar
    assert len(sar["impact_decomposition"]) == 1
    imp = sar["impact_decomposition"][0]
    assert imp["variable"] == "covariate_x"
    assert "direct_impact" in imp
    assert "indirect_spillover_impact" in imp

    assert "<svg" in res["svg_chart"]
    assert "Phân tích Kinh tế lượng Không gian" in res["apa_narrative"]


def test_spatial_econometrics_random():
    np.random.seed(999)
    n = 45

    # Uniform random coordinates and i.i.d. normal outcomes
    data = []
    for _ in range(n):
        data.append({
            "lat": float(np.random.uniform(10.0, 20.0)),
            "lon": float(np.random.uniform(102.0, 108.0)),
            "y": float(np.random.normal(0, 1)),
            "x": float(np.random.normal(0, 1)),
        })

    res = SpatialEconometricsEngine.analyze(
        data=data,
        lat_field="lat",
        lon_field="lon",
        outcome_var="y",
        covariate_vars=["x"],
    )

    assert res["status"] == "success"
    moran = res["morans_i"]
    assert moran["classification"] == "RANDOM_SPATIAL_DISTRIBUTION" or moran["p_value"] >= 0.05


def test_spatial_econometrics_insufficient_data():
    data = [{"lat": 10.0, "lon": 105.0, "y": 1.0, "x": 2.0}] * 8
    res = SpatialEconometricsEngine.analyze(
        data=data,
        lat_field="lat",
        lon_field="lon",
        outcome_var="y",
        covariate_vars=["x"],
    )
    assert res["status"] == "error"
    assert "không đủ tọa độ" in res["message"]
