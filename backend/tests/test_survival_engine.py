import pytest
from app.engine.survival_engine import SurvivalDropOffEngine


def test_survival_analysis_basic_km():
    """Kiểm thử tính toán Kaplan-Meier cơ bản trên tập mẫu 12 người."""
    durations = [30.0, 45.0, 60.0, 90.0, 120.0, 150.0, 180.0, 240.0, 300.0, 360.0, 420.0, 480.0]
    # 4 người bỏ dở (event=1), 8 người hoàn thành (event=0, censored)
    events = [1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0]

    res = SurvivalDropOffEngine.analyze_survival(durations, events)
    assert res["status"] == "SUCCESS"
    assert res["total_participants"] == 12
    assert res["drop_off_count"] == 4
    assert res["completed_count"] == 8
    assert res["overall_drop_off_rate"] == 33.3
    assert res["overall_completion_rate"] == 66.7

    km = res["overall_km"]
    assert len(km["steps"]) > 0
    assert km["steps"][0]["survival_prob"] == 1.0
    # Vì hoàn thành 66.7% > 50%, median survival time là None
    assert km["median_survival_time"] is None
    assert "svg_path" in km
    assert km["svg_path"].startswith("M")

    # Kiểm tra các mốc thời gian (milestones)
    assert len(res["milestones"]) == 4
    assert res["milestones"][0]["time_seconds"] == 60.0
    assert "apa_narrative" in res
    assert "Kaplan-Meier" in res["apa_narrative"]


def test_survival_analysis_two_groups_log_rank():
    """Kiểm thử so sánh 2 nhóm (Mobile vs Desktop) với Log-Rank test và Cox HR."""
    durations = [
        30.0, 45.0, 60.0, 90.0, 120.0, 150.0,  # Mobile: bỏ dở sớm
        180.0, 240.0, 300.0, 360.0, 420.0, 480.0  # Desktop: duy trì lâu
    ]
    events = [
        1, 1, 1, 1, 0, 0,   # Mobile: 4 events
        0, 1, 0, 0, 0, 0    # Desktop: 1 event
    ]
    groups = [
        "Mobile", "Mobile", "Mobile", "Mobile", "Mobile", "Mobile",
        "Desktop", "Desktop", "Desktop", "Desktop", "Desktop", "Desktop"
    ]

    res = SurvivalDropOffEngine.analyze_survival(durations, events, group_labels=groups)
    assert res["status"] == "SUCCESS"
    assert res["group_comparison"] is not None
    assert "group_1" in res["group_comparison"]
    assert "group_2" in res["group_comparison"]

    lr = res["log_rank_test"]
    assert lr is not None
    assert lr["degrees_of_freedom"] == 1
    assert lr["chi2_statistic"] > 0.0
    assert 0.0 <= lr["p_value"] <= 1.0

    hr = res["cox_hazard_ratio"]
    assert hr is not None
    assert hr["hazard_ratio"] > 0.0
    assert "risk_interpretation" in hr


def test_survival_analysis_insufficient_sample():
    """Kiểm thử bắt lỗi mẫu nhỏ (< 5)."""
    res = SurvivalDropOffEngine.analyze_survival([30.0, 60.0, 90.0], [1, 0, 1])
    assert res["status"] == "INSUFFICIENT_SAMPLE"
