import pytest
import numpy as np
from app.engine.sdid_engine import SDIDEngine


def test_sdid_insufficient_records():
    records = [{"unit": "u1", "time": 1, "y": 2.0} for _ in range(10)]
    res = SDIDEngine.estimate(
        records=records,
        unit_field="unit",
        time_field="time",
        outcome_field="y",
        treated_units=["u1"],
        treatment_start_time=2
    )
    assert res["status"] == "error"
    assert "tối thiểu 20" in res["message"]


def test_sdid_insufficient_time_periods():
    # 10 units with 2 time periods (20 records, but only 1 pre, 1 post)
    records = []
    for u in [f"u{i}" for i in range(1, 11)]:
        for t in [1, 2]:
            records.append({"unit": u, "time": t, "y": 3.0})
    res = SDIDEngine.estimate(
        records=records,
        unit_field="unit",
        time_field="time",
        outcome_field="y",
        treated_units=["u1"],
        treatment_start_time=2
    )
    assert res["status"] == "error"
    assert "tối thiểu 3 mốc thời gian" in res["message"]


def test_sdid_valid_panel_estimation():
    np.random.seed(42)
    units = [f"Region_{i}" for i in range(1, 9)]  # 8 units: 1 treated, 7 controls
    times = [1, 2, 3, 4, 5]  # 3 pre (1,2,3), 2 post (4,5)
    treated_units = ["Region_1"]
    start_time = 4

    records = []
    for u in units:
        is_tr = (u in treated_units)
        unit_intercept = float(np.random.normal(10.0, 2.0))
        trend_slope = float(np.random.normal(0.8, 0.2))

        for t in times:
            is_post = (t >= start_time)
            # True treatment effect: +3.0 in post periods for treated
            treatment_effect = 3.0 if (is_tr and is_post) else 0.0
            noise = float(np.random.normal(0.0, 0.3))
            y = unit_intercept + trend_slope * t + treatment_effect + noise

            records.append({
                "region_id": u,
                "wave": t,
                "sales_growth": y
            })

    res = SDIDEngine.estimate(
        records=records,
        unit_field="region_id",
        time_field="wave",
        outcome_field="sales_growth",
        treated_units=treated_units,
        treatment_start_time=start_time,
        n_placebo_reps=50,
        seed=42
    )

    assert res["status"] == "success"
    assert res["sample_diagnostics"]["n_treated_units"] == 1
    assert res["sample_diagnostics"]["n_control_units"] == 7
    assert res["sample_diagnostics"]["t_pre_periods"] == 3
    assert res["sample_diagnostics"]["t_post_periods"] == 2

    # Check SDID estimates
    sdid = res["sdid_estimates"]
    assert "tau_sdid" in sdid
    assert "se_sdid" in sdid
    assert "ci_95_lower" in sdid
    assert "ci_95_upper" in sdid
    assert sdid["ci_95_lower"] < sdid["ci_95_upper"]
    # Check that tau_sdid is close to true effect of +3.0
    assert 1.5 <= sdid["tau_sdid"] <= 4.5

    # Check weights and trajectories
    assert len(res["top_donor_weights"]) > 0
    assert len(res["time_weights"]) == 3
    assert len(res["time_trajectories"]) == 5
    assert "<svg" in res["svg_chart"]
    assert "APA 7th Standard" in res["apa_narrative"]
