import numpy as np
import pytest
from app.engine.gee_engine import GEEEngine


def test_gee_longitudinal_gaussian_estimation():
    np.random.seed(42)
    N = 30  # 30 subjects
    T = 3   # 3 waves
    M = N * T

    cluster_ids = np.repeat(np.arange(N), T)
    time_points = np.tile(np.arange(T), N)

    # Random subject effect u_i ~ N(0, 1.5)
    subject_effect = np.repeat(np.random.normal(0, 1.2, N), T)

    # Predictor X (e.g. training hours)
    X = np.random.normal(5, 2, M)

    # Outcome Y = 10 + 2.5 * X + 1.0 * time + u_i + eps
    Y = 10.0 + 2.5 * X + 1.0 * time_points + subject_effect + np.random.normal(0, 0.8, M)

    predictors = np.column_stack([X, time_points])

    res = GEEEngine.estimate(
        cluster_ids=cluster_ids,
        time_points=time_points,
        outcomes=Y,
        predictors=predictors,
        feature_names=["Số giờ đào tạo", "Đợt khảo sát"],
        family="gaussian",
        corstr="exchangeable"
    )

    assert res["status"] == "success"
    assert res["clusters_count"] == N
    assert res["observations_count"] == M
    assert res["working_correlation_structure"] == "exchangeable"
    assert res["estimated_correlation_parameter"] > 0.2
    
    # Check X coefficient ~ 2.5
    coefs = {c["term"]: c for c in res["coefficients"]}
    assert "Số giờ đào tạo" in coefs
    assert 2.0 <= coefs["Số giờ đào tạo"]["estimate"] <= 3.0
    assert coefs["Số giờ đào tạo"]["p_value"] < 0.001
    assert coefs["Số giờ đào tạo"]["robust_se"] > 0

    assert "<svg" in res["svg_chart"]
    assert "Mô hình Phương trình Ước lượng Tổng quát" in res["apa_narrative"]


def test_gee_insufficient_sample():
    # Only 5 clusters (N < 15)
    c_ids = np.repeat(np.arange(5), 3)
    times = np.tile(np.arange(3), 5)
    Y = np.ones(15)
    X = np.ones((15, 1))

    res = GEEEngine.estimate(
        cluster_ids=c_ids,
        time_points=times,
        outcomes=Y,
        predictors=X
    )
    assert res["status"] == "insufficient_data"
    assert "15 đối tượng" in res["message"]
