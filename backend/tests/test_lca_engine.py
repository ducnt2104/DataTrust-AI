import pytest
from app.engine.lca_engine import LatentClassAnalysisEngine


def test_lca_estimation_and_selection():
    """Kiểm thử thuật toán EM phân đoạn lớp ẩn và lựa chọn số lớp tối ưu theo BIC."""
    item_keys = ["q_freq", "q_qual", "q_sat"]

    # Sinh 24 phản hồi phân bố thành 2 nhóm rõ rệt:
    # Nhóm 1 (Tích cực / Ưa chuộng): 12 người
    group_1 = [
        {"q_freq": "Thường xuyên", "q_qual": "Rất tốt", "q_sat": "Hài lòng"}
        for _ in range(12)
    ]
    # Nhóm 2 (Tiêu cực / Không quan tâm): 12 người
    group_2 = [
        {"q_freq": "Hiếm khi", "q_qual": "Kém", "q_sat": "Không hài lòng"}
        for _ in range(12)
    ]

    data = group_1 + group_2

    res = LatentClassAnalysisEngine.compute_lca(
        responses_data=data,
        item_keys=item_keys,
        max_classes_to_test=3,
        random_seed=42
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == 24
    assert res["items_count"] == 3
    assert res["optimal_classes_count"] == 2
    assert res["entropy"] >= 0.80
    assert "Rất tốt" in res["entropy_quality"]
    assert len(res["model_selection_criteria"]) >= 2
    assert len(res["class_profiles"]) == 2

    # Kiểm tra đồ họa SVG và APA narrative
    assert "<svg" in res["svg_profile_plot"]
    assert "Latent Class Analysis" in res["apa_narrative"]
    assert "Goodman" in res["apa_narrative"]
    assert "Entropy" in res["apa_narrative"]


def test_lca_fixed_k_classes():
    """Kiểm thử phân tích LCA với số lớp K ấn định."""
    item_keys = ["feature_a", "feature_b", "feature_c"]
    data = [
        {"feature_a": "Yes", "feature_b": "High", "feature_c": "Pro"},
        {"feature_a": "Yes", "feature_b": "High", "feature_c": "Pro"},
        {"feature_a": "Yes", "feature_b": "Low", "feature_c": "Basic"},
        {"feature_a": "No", "feature_b": "Low", "feature_c": "Basic"},
        {"feature_a": "No", "feature_b": "Low", "feature_c": "Basic"},
        {"feature_a": "No", "feature_b": "High", "feature_c": "Basic"},
        {"feature_a": "Yes", "feature_b": "High", "feature_c": "Pro"},
        {"feature_a": "Yes", "feature_b": "High", "feature_c": "Pro"},
        {"feature_a": "No", "feature_b": "Low", "feature_c": "Basic"},
        {"feature_a": "No", "feature_b": "Low", "feature_c": "Basic"},
    ]

    res = LatentClassAnalysisEngine.compute_lca(
        responses_data=data,
        item_keys=item_keys,
        num_classes=2,
        random_seed=123
    )

    assert res["status"] == "SUCCESS"
    assert res["optimal_classes_count"] == 2
    assert len(res["class_profiles"]) == 2
    total_prev = sum(p["prevalence_pct"] for p in res["class_profiles"])
    assert abs(total_prev - 100.0) < 0.5


def test_lca_insufficient_sample_and_items():
    """Kiểm thử bắt lỗi khi cỡ mẫu < 10 hoặc số items < 3."""
    # Cỡ mẫu < 10
    res_sample = LatentClassAnalysisEngine.compute_lca(
        responses_data=[{"q1": "A", "q2": "B", "q3": "C"}] * 5,
        item_keys=["q1", "q2", "q3"]
    )
    assert res_sample["status"] == "INSUFFICIENT_SAMPLE"

    # Số items < 3
    res_items = LatentClassAnalysisEngine.compute_lca(
        responses_data=[{"q1": "A", "q2": "B"}] * 15,
        item_keys=["q1", "q2"]
    )
    assert res_items["status"] == "INSUFFICIENT_ITEMS"
