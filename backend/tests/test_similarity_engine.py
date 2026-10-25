"""
Unit tests for DataTrust SimilarityEngine (backend/app/engine/similarity_engine.py)
Kiểm thử thuật toán đo lường tương đồng cặp phản hồi (Categorical & Text Jaccard),
nhận diện dấu vân tay thiết bị/IP, và bóc tách đồ thị vòng thông đồng (Collusion Syndicate Rings).
"""

import pytest
try:
    from app.engine.similarity_engine import SimilarityEngine
except ModuleNotFoundError:
    from backend.app.engine.similarity_engine import SimilarityEngine


def test_categorical_similarity():
    """Kiểm thử tính toán tương đồng trên vector câu hỏi đóng"""
    # 1. Trùng khớp hoàn toàn
    vec_a = ["1", "a", "vinfast", "true"]
    vec_b = ["1", "a", "vinfast", "true"]
    sim, matches, valid = SimilarityEngine.calculate_categorical_similarity(vec_a, vec_b)
    assert sim == 1.0
    assert matches == 4
    assert valid == 4

    # 2. Khác biệt hoàn toàn
    vec_c = ["2", "b", "tesla", "false"]
    sim_diff, matches_diff, valid_diff = SimilarityEngine.calculate_categorical_similarity(vec_a, vec_c)
    assert sim_diff == 0.0
    assert matches_diff == 0
    assert valid_diff == 4

    # 3. Trùng một phần
    vec_d = ["1", "b", "vinfast", "false"]
    sim_part, matches_part, valid_part = SimilarityEngine.calculate_categorical_similarity(vec_a, vec_d)
    assert sim_part == 0.50
    assert matches_part == 2
    assert valid_part == 4

    # 4. Có trường hợp bỏ trống (empty)
    vec_e = ["1", "", "vinfast", ""]
    sim_empty, matches_empty, valid_empty = SimilarityEngine.calculate_categorical_similarity(vec_a, vec_e)
    # 2 câu có câu trả lời từ cả hai: q0 ("1" == "1"), q2 ("vinfast" == "vinfast")
    # q1 và q3: vec_a có giá trị nhưng vec_e bỏ trống -> valid_comparisons = 4, matches = 2
    assert sim_empty == 0.50
    assert matches_empty == 2
    assert valid_empty == 4


def test_text_jaccard_similarity():
    """Kiểm thử tính toán n-gram và token Jaccard trên văn bản câu hỏi mở"""
    # 1. Chuỗi giống hệt
    t1 = "Chất lượng dịch vụ xuất sắc và nhân viên rất nhiệt tình"
    t2 = "Chất lượng dịch vụ xuất sắc và nhân viên rất nhiệt tình"
    assert SimilarityEngine.calculate_text_jaccard(t1, t2) == 1.0

    # 2. Chuỗi rỗng
    assert SimilarityEngine.calculate_text_jaccard("", "") == 0.0
    assert SimilarityEngine.calculate_text_jaccard(t1, "") == 0.0

    # 3. Chuỗi biến thể nhẹ (paraphrasing / chèn từ)
    t3 = "Chất lượng dịch vụ rất xuất sắc, nhân viên cực kỳ nhiệt tình"
    sim_near = SimilarityEngine.calculate_text_jaccard(t1, t3)
    assert sim_near > 0.45

    # 4. Chuỗi ngắn (< 3 ký tự) dùng token fallback
    assert SimilarityEngine.calculate_text_jaccard("ok", "ok") == 1.0
    assert SimilarityEngine.calculate_text_jaccard("ok", "no") == 0.0


def test_pair_metrics_detection():
    """Kiểm thử đo lường cặp phản hồi tích hợp nhận diện thông đồng & thời gian"""
    closed_questions = [
        {"id": "q1", "question_type": "single_choice"},
        {"id": "q2", "question_type": "rating"},
        {"id": "q3", "question_type": "single_choice"}
    ]
    open_questions = [
        {"id": "q_open", "question_type": "long_text"}
    ]

    resp_1 = {
        "id": "resp-001",
        "device_id": "device_xyz_999",
        "ip_address": "192.168.1.100",
        "enumerator_id": "enum-1",
        "submitted_at": "2026-10-24T04:00:00Z",
        "answers": {
            "q1": "opt_a",
            "q2": "5",
            "q3": "opt_c",
            "q_open": "Sản phẩm dùng rất tốt và mượt mà"
        }
    }

    # Phản hồi clone hoàn toàn nộp cùng thiết bị chỉ sau 30 giây
    resp_2 = {
        "id": "resp-002",
        "device_id": "device_xyz_999",
        "ip_address": "192.168.1.100",
        "enumerator_id": "enum-1",
        "submitted_at": "2026-10-24T04:00:30Z",
        "answers": {
            "q1": "opt_a",
            "q2": "5",
            "q3": "opt_c",
            "q_open": "Sản phẩm dùng rất tốt và mượt mà"
        }
    }

    metrics = SimilarityEngine.calculate_pair_metrics(resp_1, resp_2, closed_questions, open_questions)
    assert metrics["composite_similarity"] >= 0.99
    assert metrics["same_device"] is True
    assert metrics["same_ip"] is True
    assert metrics["same_enumerator"] is True
    assert metrics["rapid_succession"] is True
    assert metrics["time_delta_seconds"] == 30.0
    assert metrics["risk_category"] == "IDENTICAL_DUPLICATE"
    assert metrics["is_collusion_syndicate"] is True
    assert metrics["severity"] == "CRITICAL"


def test_collusion_rings_connected_components():
    """Kiểm thử thuật toán đồ thị phát hiện vòng lừa đảo tập trung"""
    responses_dict = {
        "r1": {"id": "r1", "device_id": "dev_ring1", "ip_address": "10.0.0.1", "submitted_at": "2026-10-24T04:00:00Z"},
        "r2": {"id": "r2", "device_id": "dev_ring1", "ip_address": "10.0.0.1", "submitted_at": "2026-10-24T04:00:20Z"},
        "r3": {"id": "r3", "device_id": "dev_ring1", "ip_address": "10.0.0.1", "submitted_at": "2026-10-24T04:00:40Z"},
        "r4": {"id": "r4", "device_id": "dev_other", "ip_address": "10.0.0.2", "submitted_at": "2026-10-24T04:05:00Z"},
        "r5": {"id": "r5", "device_id": "dev_other", "ip_address": "10.0.0.2", "submitted_at": "2026-10-24T04:05:25Z"},
        "clean1": {"id": "clean1", "device_id": "dev_clean1", "ip_address": "172.16.0.5", "submitted_at": "2026-10-24T04:10:00Z"}
    }

    high_risk_pairs = [
        # Nhóm 1: r1, r2, r3 tạo thành tam giác thông đồng chia sẻ cùng thiết bị dev_ring1
        {"response_id_a": "r1", "response_id_b": "r2", "composite_similarity": 0.95, "is_collusion_syndicate": True},
        {"response_id_a": "r2", "response_id_b": "r3", "composite_similarity": 0.92, "is_collusion_syndicate": True},
        {"response_id_a": "r1", "response_id_b": "r3", "composite_similarity": 0.90, "is_collusion_syndicate": True},
        # Nhóm 2: r4, r5 là cặp gần trùng
        {"response_id_a": "r4", "response_id_b": "r5", "composite_similarity": 0.88, "is_collusion_syndicate": False}
    ]

    rings = SimilarityEngine.extract_collusion_rings(high_risk_pairs, responses_dict, threshold=0.85)

    assert len(rings) == 2
    # Vòng 1 chứa r1, r2, r3 (kích thước 3, có cùng thiết bị)
    ring_1 = next(r for r in rings if "r1" in r["response_ids"])
    assert ring_1["member_count"] == 3
    assert set(ring_1["response_ids"]) == {"r1", "r2", "r3"}
    assert ring_1["has_shared_device"] is True
    assert ring_1["threat_level"] == "CRITICAL"

    # Vòng 2 chứa r4, r5
    ring_2 = next(r for r in rings if "r4" in r["response_ids"])
    assert ring_2["member_count"] == 2
    assert set(ring_2["response_ids"]) == {"r4", "r5"}


def test_academic_narrative_output():
    """Kiểm thử câu diễn giải học thuật định dạng chuẩn APA/ISO"""
    # Không có vòng nào
    clean_narrative = SimilarityEngine.generate_academic_narrative(
        total_responses=100,
        high_risk_count=0,
        rings_count=0,
        collusion_nodes_count=0,
        highest_sim=0.35,
        avg_sim=0.18,
        threshold=0.80
    )
    assert "ISO 20252:2019" in clean_narrative
    assert "không phát hiện" in clean_narrative

    # Có vòng gian lận
    fraud_narrative = SimilarityEngine.generate_academic_narrative(
        total_responses=100,
        high_risk_count=8,
        rings_count=2,
        collusion_nodes_count=6,
        highest_sim=0.98,
        avg_sim=0.25,
        threshold=0.80
    )
    assert "AAPOR Fraud Detection Standards" in fraud_narrative
    assert "2 cụm/vòng thông đồng" in fraud_narrative
    assert "Quarantine Filter" in fraud_narrative
