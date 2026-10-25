import pytest
from app.engine.invariance_engine import MeasurementInvarianceEngine

def test_measurement_invariance_supported():
    # 2 nhóm (Nam, Nữ) trả lời thang đo 3 câu hỏi (Likert 1-5)
    # Nhóm 1: N=8
    g1 = [
        [4.0, 4.0, 5.0],
        [3.0, 4.0, 4.0],
        [5.0, 5.0, 5.0],
        [2.0, 3.0, 3.0],
        [4.0, 4.0, 4.0],
        [3.0, 3.0, 4.0],
        [5.0, 4.0, 5.0],
        [4.0, 5.0, 4.0],
    ]
    # Nhóm 2: N=8 (cùng cấu trúc đo lường)
    g2 = [
        [4.0, 4.0, 5.0],
        [3.0, 4.0, 4.0],
        [5.0, 5.0, 5.0],
        [2.0, 2.0, 3.0],
        [4.0, 4.0, 4.0],
        [3.0, 3.0, 3.0],
        [5.0, 5.0, 5.0],
        [4.0, 4.0, 4.0],
    ]

    grouped_data = {
        "Nam": g1,
        "Nữ": g2
    }
    items = ["Hài lòng quy trình", "Độ tin cậy", "Khả năng gắn bó"]

    res = MeasurementInvarianceEngine.evaluate_invariance(grouped_data, items)

    assert res["status"] == "OK"
    assert res["k_groups"] == 2
    assert res["total_sample_size"] == 16
    assert res["items_count"] == 3

    # Kiểm tra 4 mô hình học thuật
    models = res["models_summary"]
    assert len(models) == 4
    assert models[0]["level"] == "CONFIGURAL"
    assert models[1]["level"] == "METRIC"
    assert models[2]["level"] == "SCALAR"
    assert models[3]["level"] == "STRICT"

    # Kiểm tra cấp bậc đạt được
    assert res["highest_level_achieved"] in ["METRIC_INVARIANCE", "SCALAR_INVARIANCE", "STRICT_INVARIANCE"]
    assert "verdict_badge" in res
    assert "recommendation" in res

    # Chi tiết biến số
    assert len(res["item_details"]) == 3
    for it in res["item_details"]:
        assert "loadings" in it
        assert "Nam" in it["loadings"]
        assert "Nữ" in it["loadings"]

    # APA writeup
    assert "apa_narrative" in res
    assert "Measurement invariance across 2 groups" in res["apa_narrative"]

def test_measurement_invariance_insufficient_groups():
    res = MeasurementInvarianceEngine.evaluate_invariance(
        {"OnlyGroup": [[1.0, 2.0], [2.0, 3.0]]},
        ["Q1", "Q2"]
    )
    assert res["status"] == "INSUFFICIENT_GROUPS"

def test_measurement_invariance_insufficient_items():
    res = MeasurementInvarianceEngine.evaluate_invariance(
        {"G1": [[1.0], [2.0], [3.0], [4.0]], "G2": [[2.0], [3.0], [4.0], [5.0]]},
        ["OnlyOneItem"]
    )
    assert res["status"] == "INSUFFICIENT_ITEMS"

def test_measurement_invariance_insufficient_sample():
    res = MeasurementInvarianceEngine.evaluate_invariance(
        {
            "G1": [[1.0, 2.0], [2.0, 3.0]],  # chỉ có 2 phản hồi (< 4)
            "G2": [[2.0, 3.0], [3.0, 4.0], [4.0, 5.0], [5.0, 5.0]]
        },
        ["Q1", "Q2"]
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"
