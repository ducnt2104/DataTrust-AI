import pytest
from app.engine.equating_engine import EquatingEngine

def test_equating_engine_likert_5_to_7():
    # Thang X: 1-5 (N=10)
    x_data = [1.0, 2.0, 2.0, 3.0, 3.0, 4.0, 4.0, 4.0, 5.0, 5.0]
    # Thang Y: 1-7 (N=10)
    y_data = [1.0, 2.0, 3.0, 4.0, 4.0, 5.0, 5.0, 6.0, 6.0, 7.0]

    res = EquatingEngine.equate_scales(
        x_values=x_data,
        y_values=y_data,
        x_label="Likert 5 điểm",
        y_label="Likert 7 điểm",
        x_min=1.0,
        x_max=5.0,
        y_min=1.0,
        y_max=7.0
    )

    assert res["status"] == "OK"
    assert res["sample_sizes"]["x_count"] == 10
    assert res["sample_sizes"]["y_count"] == 10

    # Linear equating
    lin = res["linear_equating"]
    assert lin["slope_alpha"] > 0
    assert "formula" in lin

    # Concordance table
    table = res["concordance_table"]
    assert len(table) >= 5
    for row in table:
        assert 1.0 <= row["linear_equivalent"] <= 7.0
        assert 1.0 <= row["equipercentile_equivalent"] <= 7.0
        assert 0.0 <= row["percentile_rank"] <= 100.0
        assert 1 <= row["stanine"] <= 9

    # APA writeup
    assert "apa_narrative" in res
    assert "Observed-score equating was performed" in res["apa_narrative"]

def test_equating_engine_identical_scales():
    # Khi hai thang đo giống nhau
    data = [2.0, 3.0, 4.0, 4.0, 5.0, 5.0, 6.0, 7.0]
    res = EquatingEngine.equate_scales(
        x_values=data,
        y_values=data,
        x_label="Scale A",
        y_label="Scale B",
        x_min=1.0,
        x_max=7.0,
        y_min=1.0,
        y_max=7.0
    )
    assert res["status"] == "OK"
    assert abs(res["linear_equating"]["slope_alpha"] - 1.0) < 0.01
    assert abs(res["linear_equating"]["intercept_beta"]) < 0.01
    assert res["discrepancy_analysis"]["agreement_verdict"] == "EXCELLENT"

def test_equating_engine_insufficient_sample():
    res = EquatingEngine.equate_scales(
        x_values=[1.0, 2.0],
        y_values=[1.0, 2.0, 3.0]
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"

def test_transform_respondent_scores():
    scores = [1.0, 3.0, 5.0, None]
    # alpha = 1.5, beta = 0.5 => 1*1.5+0.5=2.0, 3*1.5+0.5=5.0, 5*1.5+0.5=8.0 (clamped to 7.0)
    transformed = EquatingEngine.transform_respondent_scores(
        scores,
        linear_alpha=1.5,
        linear_beta=0.5,
        y_bounds=(1.0, 7.0)
    )
    assert transformed[0] == 2.0
    assert transformed[1] == 5.0
    assert transformed[2] == 7.0
    assert transformed[3] is None
