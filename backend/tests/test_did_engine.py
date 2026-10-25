import pytest
from app.engine.did_engine import DifferenceInDifferencesEngine


def test_did_estimation_clean():
    """Kiểm thử tính toán hiệu ứng can thiệp DiD và hồi quy TWFE."""
    # Mô phỏng dữ liệu kinh điển kiểu Card & Krueger:
    # Control Pre: y ~ 10.0 (n=4)
    # Control Post: y ~ 12.0 (n=4, xu thế tự nhiên = +2.0)
    # Treat Pre: y ~ 14.0 (n=4, chênh lệch cơ sở = +4.0)
    # Treat Post: y ~ 20.0 (n=4, can thiệp gia tăng thuần +4.0, tổng biến thiên = +6.0)
    data = [
        {"y": 9.8, "group": "Control", "period": "Trước"},
        {"y": 10.2, "group": "Control", "period": "Trước"},
        {"y": 9.9, "group": "Control", "period": "Trước"},
        {"y": 10.1, "group": "Control", "period": "Trước"},

        {"y": 11.8, "group": "Control", "period": "Sau"},
        {"y": 12.2, "group": "Control", "period": "Sau"},
        {"y": 11.9, "group": "Control", "period": "Sau"},
        {"y": 12.1, "group": "Control", "period": "Sau"},

        {"y": 13.8, "group": "Treatment", "period": "Trước"},
        {"y": 14.2, "group": "Treatment", "period": "Trước"},
        {"y": 13.9, "group": "Treatment", "period": "Trước"},
        {"y": 14.1, "group": "Treatment", "period": "Trước"},

        {"y": 19.8, "group": "Treatment", "period": "Sau"},
        {"y": 20.2, "group": "Treatment", "period": "Sau"},
        {"y": 19.9, "group": "Treatment", "period": "Sau"},
        {"y": 20.1, "group": "Treatment", "period": "Sau"},
    ]

    res = DifferenceInDifferencesEngine.compute_did_analysis(
        data_rows=data,
        outcome_key="y",
        treatment_key="group",
        time_key="period",
        treatment_value="Treatment",
        post_value="Sau"
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == 16
    assert abs(res["cell_means_2x2"]["control_pre"]["mean"] - 10.0) < 0.1
    assert abs(res["cell_means_2x2"]["control_post"]["mean"] - 12.0) < 0.1
    assert abs(res["cell_means_2x2"]["treat_pre"]["mean"] - 14.0) < 0.1
    assert abs(res["cell_means_2x2"]["treat_post"]["mean"] - 20.0) < 0.1

    # Phản thực tế = 14.0 + (12.0 - 10.0) = 16.0
    assert abs(res["cell_means_2x2"]["counterfactual_post"] - 16.0) < 0.1

    # Hiệu ứng DiD = (20.0 - 14.0) - (12.0 - 10.0) = +4.0
    att = res["did_treatment_effect"]
    assert abs(att["att_estimate"] - 4.0) < 0.1
    assert att["p_value"] < 0.001
    assert att["is_statistically_significant"] is True
    assert att["relative_gain_pct"] > 20.0

    # Đồ thị SVG và Thuyết minh APA
    assert "<svg" in res["svg_trajectory_chart"]
    assert "Card & Krueger" in res["apa_narrative"]
    assert "ATT" in res["apa_narrative"]
    assert "có ý nghĩa thống kê" in res["apa_narrative"]


def test_did_insufficient_sample_and_groups():
    """Kiểm thử bắt lỗi dữ liệu thiếu mẫu hoặc không đủ 2 nhóm/2 kỳ."""
    # Thiếu mẫu (< 8)
    res_sample = DifferenceInDifferencesEngine.compute_did_analysis(
        data_rows=[{"y": 10, "g": "T", "t": "Post"}] * 4,
        outcome_key="y",
        treatment_key="g",
        time_key="t"
    )
    assert res_sample["status"] == "INSUFFICIENT_SAMPLE"

    # Chỉ có 1 nhóm can thiệp
    res_group = DifferenceInDifferencesEngine.compute_did_analysis(
        data_rows=[
            {"y": 10, "g": "T", "t": "Pre"},
            {"y": 12, "g": "T", "t": "Post"}
        ] * 5,
        outcome_key="y",
        treatment_key="g",
        time_key="t"
    )
    assert res_group["status"] == "INVALID_TREATMENT_GROUPS"
