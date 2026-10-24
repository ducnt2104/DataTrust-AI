# -*- coding: utf-8 -*-
"""
Unit tests for Staggered Difference-in-Differences Engine
Callaway & Sant'Anna (2021); Goodman-Bacon (2021); Sun & Abraham (2021)
"""
import pytest
import numpy as np
from app.engine.staggered_did_engine import StaggeredDIDEngine


def test_staggered_did_balanced_panel():
    np.random.seed(42)
    # 30 units observed across 4 time periods (t = 1, 2, 3, 4) -> 120 observations
    # 10 units never treated (g = inf)
    # 10 units treated at t = 2 (g = 2) with true dynamic effect: +2.0 at t=2, +3.0 at t=3, +4.0 at t=4
    # 10 units treated at t = 3 (g = 3) with true dynamic effect: +2.5 at t=3, +3.5 at t=4
    units = []
    times = []
    g_treated = []
    y_vals = []

    for u in range(30):
        if u < 10:
            g = float('inf')
        elif u < 20:
            g = 2.0
        else:
            g = 3.0

        unit_fe = np.random.normal(10.0, 1.0)
        for t in [1.0, 2.0, 3.0, 4.0]:
            time_fe = 1.5 * t
            # True dynamic treatment effect
            tau = 0.0
            if g != float('inf') and t >= g:
                tau = 2.0 + (t - g) * 1.0

            noise = np.random.normal(0, 0.2)
            y = unit_fe + time_fe + tau + noise

            units.append(f"unit_{u}")
            times.append(t)
            g_treated.append(g if g != float('inf') else 0.0)
            y_vals.append(y)

    res = StaggeredDIDEngine.evaluate_staggered_did(
        y_outcome=np.array(y_vals, dtype=float),
        unit_ids=np.array(units),
        time_periods=np.array(times, dtype=float),
        first_treated_periods=np.array(g_treated, dtype=float),
        outcome_label="Log Labor Productivity",
        unit_label="Enterprise",
        time_label="Survey Quarter"
    )

    assert res["status"] == "SUCCESS"
    diag = res["diagnostics"]
    assert diag["n_observations"] == 120
    assert diag["n_units"] == 30
    assert diag["n_time_periods"] == 4
    assert diag["n_cohorts"] == 2
    assert diag["n_never_treated_units"] == 10

    # Overall ATT should be positive and around 2.5 - 3.2
    assert 2.0 < diag["overall_att"] < 4.0
    assert diag["overall_p_value"] < 0.05
    assert diag["is_statistically_significant"] is True

    # Pre-trends should be supported (p >= 0.05)
    assert diag["parallel_trends_supported"] is True

    # Event study effects
    es = res["event_study_effects"]
    assert len(es) > 0
    # At e = 0, effect should be around +2.0
    e0 = next((item for item in es if item["event_time"] == 0), None)
    assert e0 is not None
    assert abs(e0["att"] - 2.0) < 0.6

    # Goodman-Bacon decomposition
    bacon = res["bacon_decomposition"]
    assert bacon is not None
    assert bacon["n_comparisons"] > 0
    assert len(bacon["components"]) > 0

    # SVG and APA narrative
    assert "<svg" in res["svg_visualization"]
    assert "Callaway & Sant'Anna, 2021" in res["apa_narrative"]


def test_staggered_did_insufficient_sample():
    res = StaggeredDIDEngine.evaluate_staggered_did(
        y_outcome=np.array([1.0, 2.0, 3.0]),
        unit_ids=np.array(["u1", "u2", "u3"]),
        time_periods=np.array([1.0, 2.0, 1.0]),
        first_treated_periods=np.array([2.0, 0.0, 0.0])
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"
    assert "tối thiểu 20 quan sát" in res["message"]


def test_staggered_did_insufficient_time_periods():
    # 25 observations but only 1 time period
    y = np.ones(25)
    u = np.array([f"u_{i}" for i in range(25)])
    t = np.ones(25)
    g = np.zeros(25)
    res = StaggeredDIDEngine.evaluate_staggered_did(y, u, t, g)
    assert res["status"] == "INSUFFICIENT_TIME_PERIODS"


def test_staggered_did_no_treated_units():
    # 30 observations across 2 periods, but all g = 0
    y = np.ones(30)
    u = np.array([f"u_{i % 15}" for i in range(30)])
    t = np.array([1.0 if i < 15 else 2.0 for i in range(30)])
    g = np.zeros(30)
    res = StaggeredDIDEngine.evaluate_staggered_did(y, u, t, g)
    assert res["status"] == "NO_TREATED_UNITS"
