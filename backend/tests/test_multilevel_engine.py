import pytest
from app.engine.multilevel_engine import MultilevelModelingEngine


def test_multilevel_unconditional_null_model():
    """Kiểm thử mô hình rỗng HLM tính toán ICC và phân rã phương sai."""
    # 3 cụm, mỗi cụm 4 người
    data = [
        {"y": 2.0, "cluster": "C1"},
        {"y": 2.5, "cluster": "C1"},
        {"y": 2.2, "cluster": "C1"},
        {"y": 2.1, "cluster": "C1"},
        {"y": 5.0, "cluster": "C2"},
        {"y": 5.2, "cluster": "C2"},
        {"y": 4.8, "cluster": "C2"},
        {"y": 5.1, "cluster": "C2"},
        {"y": 8.0, "cluster": "C3"},
        {"y": 8.2, "cluster": "C3"},
        {"y": 7.9, "cluster": "C3"},
        {"y": 8.1, "cluster": "C3"}
    ]
    res = MultilevelModelingEngine.fit_multilevel_model(
        data_rows=data,
        y_var="y",
        cluster_var="cluster"
    )
    assert res["status"] == "SUCCESS"
    assert res["total_sample_size"] == 12
    assert res["num_clusters"] == 3
    null_m = res["null_model"]
    # Phương sai giữa các cụm rất lớn so với trong cụm -> ICC phải cao
    assert null_m["icc"] > 0.80
    assert null_m["icc_tier"] == "HIGH"
    assert "apa_narrative" in res
    assert "ICC" in res["apa_narrative"]


def test_multilevel_full_model_random_slopes():
    """Kiểm thử mô hình 2 tầng đầy đủ có biến dự báo X và hiệu ứng ngẫu nhiên."""
    data = []
    # Cụm 1: slope ~ 1.0, intercept ~ 2.0
    for x in [1.0, 2.0, 3.0, 4.0]:
        data.append({"y": 2.0 + 1.0 * x, "x": x, "team": "Team_A"})
    # Cụm 2: slope ~ 2.0, intercept ~ 4.0
    for x in [1.0, 2.0, 3.0, 4.0]:
        data.append({"y": 4.0 + 2.0 * x, "x": x, "team": "Team_B"})
    # Cụm 3: slope ~ 0.5, intercept ~ 1.0
    for x in [1.0, 2.0, 3.0, 4.0]:
        data.append({"y": 1.0 + 0.5 * x, "x": x, "team": "Team_C"})

    res = MultilevelModelingEngine.fit_multilevel_model(
        data_rows=data,
        y_var="y",
        x_var="x",
        cluster_var="team",
        centering="grand_mean"
    )
    assert res["status"] == "SUCCESS"
    assert res["total_sample_size"] == 12
    assert res["num_clusters"] == 3
    assert res["predictor_variable"] == "x"

    fe = res["fixed_effects"]
    assert fe["slope_gamma_10"] is not None
    assert fe["slope_gamma_10"] > 0.0

    re = res["random_effects"]
    assert re["tau_00_intercept_var"] >= 0.0

    assert len(res["cluster_trajectories"]) == 3
    assert "grand_trajectory_path" in res
    assert res["grand_trajectory_path"].startswith("M")


def test_multilevel_insufficient_sample_and_clusters():
    """Kiểm thử bắt lỗi dữ liệu thiếu mẫu hoặc thiếu cụm."""
    res1 = MultilevelModelingEngine.fit_multilevel_model(
        data_rows=[{"y": 1.0, "c": "1"}],
        y_var="y",
        cluster_var="c"
    )
    assert res1["status"] == "INSUFFICIENT_SAMPLE"

    data_few_clusters = [
        {"y": 1.0, "c": "Only_One"},
        {"y": 2.0, "c": "Only_One"},
        {"y": 3.0, "c": "Only_One"},
        {"y": 4.0, "c": "Only_One"},
        {"y": 5.0, "c": "Only_One"},
        {"y": 6.0, "c": "Only_One"},
        {"y": 7.0, "c": "Only_One"},
        {"y": 8.0, "c": "Only_One"}
    ]
    res2 = MultilevelModelingEngine.fit_multilevel_model(
        data_rows=data_few_clusters,
        y_var="y",
        cluster_var="c"
    )
    assert res2["status"] == "INSUFFICIENT_CLUSTERS"
