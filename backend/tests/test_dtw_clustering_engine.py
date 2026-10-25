import pytest
import numpy as np
from app.engine.dtw_clustering_engine import (
    compute_dtw_distance,
    run_dtw_trajectory_clustering
)


def test_dtw_distance_properties():
    ts1 = np.array([1.0, 2.0, 3.0, 4.0])
    ts2 = np.array([1.0, 2.0, 3.0, 4.0])
    # Identical series
    assert compute_dtw_distance(ts1, ts2) == 0.0

    # Time-shifted series
    ts_base = np.array([0.0, 5.0, 0.0, 0.0, 0.0])
    ts_shift = np.array([0.0, 0.0, 5.0, 0.0, 0.0])
    euclidean = np.linalg.norm(ts_base - ts_shift)
    dtw = compute_dtw_distance(ts_base, ts_shift, window_radius=2)
    # DTW should warp the shift with equal or lower distance than direct Euclidean
    assert dtw <= euclidean


def test_dtw_clustering_insufficient_time_points():
    records = [{"t1": 1.0, "t2": 2.0} for _ in range(20)]
    res = run_dtw_trajectory_clustering(records, ["t1", "t2"])
    assert res["status"] == "error"
    assert "tối thiểu 3" in res["message"]


def test_dtw_clustering_insufficient_sample():
    records = [{"t1": 1.0, "t2": 2.0, "t3": 3.0} for _ in range(8)]
    res = run_dtw_trajectory_clustering(records, ["t1", "t2", "t3"])
    assert res["status"] == "error"
    assert "N=8" in res["message"]


def test_dtw_clustering_valid_synthetic():
    np.random.seed(42)
    records = []
    # Cluster 1: Upward trend [1, 2, 4, 6]
    for _ in range(20):
        noise = np.random.normal(0, 0.2, 4)
        t = np.array([1.0, 2.0, 4.0, 6.0]) + noise
        records.append({"t1": t[0], "t2": t[1], "t3": t[2], "t4": t[3]})

    # Cluster 2: Downward trend [6, 4, 2, 1]
    for _ in range(20):
        noise = np.random.normal(0, 0.2, 4)
        t = np.array([6.0, 4.0, 2.0, 1.0]) + noise
        records.append({"t1": t[0], "t2": t[1], "t3": t[2], "t4": t[3]})

    res = run_dtw_trajectory_clustering(
        records=records,
        time_series_cols=["t1", "t2", "t3", "t4"],
        time_labels=["Wave 1", "Wave 2", "Wave 3", "Wave 4"],
        n_clusters=2
    )

    assert res["status"] == "success"
    assert res["sample_diagnostics"]["n_total"] == 40
    assert res["sample_diagnostics"]["n_time_points"] == 4
    assert res["sample_diagnostics"]["n_clusters"] == 2
    assert res["sample_diagnostics"]["mean_silhouette_score"] > 0.4

    assert len(res["clusters"]) == 2
    for c in res["clusters"]:
        assert c["size"] > 10
        assert len(c["mean_trajectory"]) == 4
        assert "archetype_title" in c

    assert "<svg" in res["svg_chart"]
    assert "Dynamic Time Warping" in res["apa_narrative"]
