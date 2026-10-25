"""
Unit tests for Dynamic Event-Study Engine.
"""

import pytest
import numpy as np
from app.engine.event_study_engine import fit_dynamic_event_study


def test_event_study_engine_basic():
    # 6 periods: 1, 2, 3 (pre), 4, 5, 6 (post)
    # 4 units: U1, U2 (treated at period 4); U3, U4 (control/never-treated)
    panel_data = []
    periods = [1, 2, 3, 4, 5, 6]

    for p in periods:
        # Control units
        panel_data.append({"unit": "U3", "wave": p, "score": 20.0 + 1.5 * p})
        panel_data.append({"unit": "U4", "wave": p, "score": 25.0 + 1.5 * p})

        # Treated units: same pre-trend, but +8.0 bump starting at p=4
        bump = 8.0 if p >= 4 else 0.0
        panel_data.append({"unit": "U1", "wave": p, "score": 30.0 + 1.5 * p + bump})
        panel_data.append({"unit": "U2", "wave": p, "score": 35.0 + 1.5 * p + bump})

    res = fit_dynamic_event_study(
        panel_data=panel_data,
        unit_col="unit",
        time_col="wave",
        outcome_col="score",
        treated_units=["U1", "U2"],
        global_event_time=4
    )

    assert res["status"] == "SUCCESS"
    assert res["units_count"] == 4
    assert res["periods_count"] == 6
    # Parallel trends should be supported (pre-trend p-value >= 0.05)
    assert res["parallel_trends_supported"] is True
    assert res["pre_trend_p_value"] >= 0.05

    # Check event coefficients
    coefs = {c["relative_period"]: c for c in res["event_coefficients"]}
    # Reference period k = -1 must be exactly 0
    assert coefs[-1]["coefficient"] == 0.0
    assert coefs[-1]["is_reference"] is True

    # Post-treatment effects (k = 0, 1, 2) should be close to +8.0
    assert np.isclose(coefs[0]["coefficient"], 8.0, atol=1.0)
    assert coefs[0]["coefficient"] > 0
    assert res["avg_post_treatment_effect"] > 6.0

    assert "<svg" in res["svg_chart"]
    assert "Dynamic Event-Study" in res["apa_narrative"]


def test_event_study_engine_edge_cases():
    # Empty data
    res_empty = fit_dynamic_event_study([], "u", "t", "y", treated_units=["A"], global_event_time=2)
    assert res_empty["status"] == "NO_DATA"

    # Only 2 periods
    res_2p = fit_dynamic_event_study([
        {"u": "A", "t": 1, "y": 10},
        {"u": "A", "t": 2, "y": 15}
    ], "u", "t", "y", treated_units=["A"], global_event_time=2)
    assert res_2p["status"] == "INSUFFICIENT_PERIODS"

    # Missing event timing
    res_no_timing = fit_dynamic_event_study([
        {"u": "A", "t": 1, "y": 10},
        {"u": "A", "t": 2, "y": 15},
        {"u": "A", "t": 3, "y": 20}
    ], "u", "t", "y")
    assert res_no_timing["status"] == "MISSING_EVENT_TIMING"
