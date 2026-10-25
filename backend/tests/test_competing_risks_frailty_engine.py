import pytest
from app.engine.competing_risks_frailty_engine import CompetingRisksFrailtyEngine


def test_competing_risks_frailty_analysis():
    """Kiểm thử động cơ phân tích Nguy cơ Cạnh tranh & Mô hình Suy yếu Chung (CIF & Shared Frailty)."""
    # 24 đối tượng khảo sát phân bố qua 3 điều tra viên với các nguyên nhân kết thúc khác nhau
    durations = [
        30.0, 45.0, 60.0, 75.0, 90.0, 110.0, 130.0, 150.0,
        180.0, 200.0, 220.0, 240.0, 260.0, 280.0, 300.0, 320.0,
        350.0, 380.0, 400.0, 420.0, 450.0, 480.0, 500.0, 520.0
    ]
    event_types = [
        "voluntary_dropoff", "quota_screenout", "voluntary_dropoff", "completed",
        "voluntary_dropoff", "fraud_rejected", "completed", "voluntary_dropoff",
        "quota_screenout", "completed", "voluntary_dropoff", "completed",
        "fraud_rejected", "voluntary_dropoff", "completed", "completed",
        "quota_screenout", "completed", "completed", "completed",
        "voluntary_dropoff", "completed", "completed", "completed"
    ]
    cluster_ids = [
        "Enumerator_A", "Enumerator_A", "Enumerator_A", "Enumerator_A",
        "Enumerator_A", "Enumerator_A", "Enumerator_A", "Enumerator_A",
        "Enumerator_B", "Enumerator_B", "Enumerator_B", "Enumerator_B",
        "Enumerator_B", "Enumerator_B", "Enumerator_B", "Enumerator_B",
        "Enumerator_C", "Enumerator_C", "Enumerator_C", "Enumerator_C",
        "Enumerator_C", "Enumerator_C", "Enumerator_C", "Enumerator_C"
    ]

    res = CompetingRisksFrailtyEngine.analyze_competing_risks_and_frailty(
        durations=durations,
        event_types=event_types,
        cluster_ids=cluster_ids
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == 24
    assert set(res["competing_causes"]) == {"voluntary_dropoff", "quota_screenout", "fraud_rejected"}

    # Kiểm tra CIF cuối cùng
    final_cif = res["final_cumulative_incidence"]
    assert 0.0 < final_cif["voluntary_dropoff"] < 1.0
    assert 0.0 < final_cif["quota_screenout"] < 1.0
    assert 0.0 < final_cif["fraud_rejected"] < 1.0
    # Tổng xác suất CIF của tất cả các nguyên nhân phải <= 1.0
    total_cif = sum(final_cif.values())
    assert total_cif <= 1.0

    # Kiểm tra đánh giá mốc thời gian và sai lệch thổi phồng của KM cổ điển
    milestones = res["milestone_evaluations"]
    assert len(milestones) >= 2
    for ms in milestones:
        assert "cumulative_incidence" in ms
        assert "naive_kaplan_meier" in ms
        assert "km_overestimation_bias" in ms
        # Naive KM phải luôn lớn hơn hoặc bằng CIF (Fine & Gray 1999 theorem)
        for c in res["competing_causes"]:
            cif_val = ms["cumulative_incidence"].get(c, 0.0)
            naive_val = ms["naive_kaplan_meier"].get(c, 0.0)
            assert naive_val >= cif_val - 1e-4

    # Kiểm tra mô hình suy yếu chung (Shared Frailty)
    frailty = res["shared_frailty_model"]
    assert frailty["clusters_count"] == 3
    assert frailty["frailty_variance_theta"] > 0
    assert len(frailty["cluster_frailty_estimates"]) == 3
    for est in frailty["cluster_frailty_estimates"]:
        assert est["frailty_relative_risk"] > 0
        assert "interpretation" in est

    # Kiểm tra đồ họa SVG và báo cáo APA
    assert "<svg" in res["svg_cif_chart"]
    assert "</svg>" in res["svg_cif_chart"]
    assert "Nguy cơ Cạnh tranh" in res["apa_narrative"]
    assert "Fine & Gray" in res["apa_narrative"]


def test_competing_risks_edge_cases():
    """Kiểm thử các trường hợp dữ liệu biên."""
    # 1. Cỡ mẫu quá nhỏ (< 8)
    res_few = CompetingRisksFrailtyEngine.analyze_competing_risks_and_frailty(
        durations=[10, 20, 30],
        event_types=["completed", "voluntary_dropoff", "completed"]
    )
    assert res_few["status"] == "INSUFFICIENT_SAMPLE"

    # 2. Không khớp độ dài
    res_mismatch = CompetingRisksFrailtyEngine.analyze_competing_risks_and_frailty(
        durations=[10, 20, 30, 40, 50, 60, 70, 80],
        event_types=["completed", "completed"]
    )
    assert res_mismatch["status"] == "INVALID_DATA"

    # 3. Không có rủi ro cạnh tranh nào (toàn bộ hoàn thành)
    res_no_comp = CompetingRisksFrailtyEngine.analyze_competing_risks_and_frailty(
        durations=[10, 20, 30, 40, 50, 60, 70, 80],
        event_types=["completed"] * 8
    )
    assert res_no_comp["status"] == "NO_COMPETING_RISKS"
