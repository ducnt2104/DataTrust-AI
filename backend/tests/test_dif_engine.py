import pytest
from app.engine.dif_engine import DIFEngine

def test_chi2_survival_function():
    # Kiểm tra các giá trị phân phối chi-square chuẩn df=1
    # Với chi2 = 0, p-value = 1.0
    assert abs(DIFEngine._chi2_sf(0.0) - 1.0) < 1e-4
    # Với chi2 = 3.841 (ngưỡng p=0.05), p-value ~ 0.05
    assert abs(DIFEngine._chi2_sf(3.841) - 0.05) < 0.005
    # Với chi2 = 6.635 (ngưỡng p=0.01), p-value ~ 0.01
    assert abs(DIFEngine._chi2_sf(6.635) - 0.01) < 0.005

def test_dif_engine_fair_scale_class_a():
    """
    Kiểm thử thang đo công bằng: cả 2 nhóm Nam và Nữ có phân bố điểm số đồng nhất.
    Toàn bộ các câu hỏi phải được phân loại là Class A (Không thiên lệch).
    """
    records = []
    # 30 Nam và 30 Nữ có cùng phân bố điểm
    for i in range(30):
        # Nam
        records.append({
            "id": f"m_{i}",
            "answers": {
                "gender": "Nam",
                "q1": (i % 5) + 1,
                "q2": ((i + 1) % 5) + 1,
                "q3": ((i + 2) % 5) + 1
            }
        })
        # Nữ
        records.append({
            "id": f"f_{i}",
            "answers": {
                "gender": "Nữ",
                "q1": (i % 5) + 1,
                "q2": ((i + 1) % 5) + 1,
                "q3": ((i + 2) % 5) + 1
            }
        })

    res = DIFEngine.compute_mantel_haenszel_dif(
        records=records,
        scale_question_ids=["q1", "q2", "q3"],
        grouping_var="gender",
        reference_group="Nam",
        focal_group="Nữ"
    )

    assert res["overall_verdict"] == "ĐẠT_CHUẨN_BẤT_BIẾN_ĐO_LƯỜNG"
    assert res["class_a_count"] == 3
    assert res["class_c_count"] == 0
    assert len(res["items"]) == 3
    for it in res["items"]:
        assert it["ets_class"] == "A"
        assert it["is_statistically_significant"] is False

def test_dif_engine_detects_biased_item():
    """
    Mô phỏng trường hợp thiên lệch:
    q1 bị thiên vị mạnh mẽ cho nhóm 'Nam' (nam đạt điểm cao hơn nhiều trên q1 mặc dù tổng điểm được điều tiết),
    trong khi q2 và q3 không thiên lệch.
    """
    records = []
    for i in range(40):
        # Nam được điểm q1 cao (4 hoặc 5), q2/q3 bình thường
        records.append({
            "id": f"m_{i}",
            "answers": {
                "gender": "Nam",
                "q1": 5 if i % 2 == 0 else 4,
                "q2": (i % 5) + 1,
                "q3": ((i + 2) % 5) + 1
            }
        })
        # Nữ bị điểm q1 thấp (1 hoặc 2), q2/q3 bình thường
        records.append({
            "id": f"f_{i}",
            "answers": {
                "gender": "Nữ",
                "q1": 1 if i % 2 == 0 else 2,
                "q2": (i % 5) + 1,
                "q3": ((i + 2) % 5) + 1
            }
        })

    res = DIFEngine.compute_mantel_haenszel_dif(
        records=records,
        scale_question_ids=["q1", "q2", "q3"],
        grouping_var="gender",
        reference_group="Nam",
        focal_group="Nữ"
    )

    q1_result = next(it for it in res["items"] if it["question_id"] == "q1")
    # q1 phải có p_value < 0.05 và được gắn Class B hoặc C
    assert q1_result["is_statistically_significant"] is True
    assert q1_result["ets_class"] in ("B", "C")
    assert "Nam" in q1_result["favored_group"]
    assert res["class_a_count"] < 3

def test_dif_engine_insufficient_sample():
    records = [{"id": "r1", "answers": {"gender": "Nam", "q1": 5, "q2": 4}}]
    res = DIFEngine.compute_mantel_haenszel_dif(
        records=records,
        scale_question_ids=["q1", "q2"],
        grouping_var="gender",
        reference_group="Nam",
        focal_group="Nữ"
    )
    assert res["overall_verdict"] == "CHƯA_ĐỦ_MẪU"
    assert len(res["items"]) == 0
