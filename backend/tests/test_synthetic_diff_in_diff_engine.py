"""
Unit tests for Synthetic Difference-in-Differences Engine (SDID)
DataTrust Iteration 172
"""

import pytest
import numpy as np
from app.engine.synthetic_diff_in_diff_engine import compute_synthetic_diff_in_diff


def test_synthetic_diff_in_diff_estimation():
    np.random.seed(42)
    # Generate 4 treated units and 16 control units across 6 periods (4 pre, 2 post)
    records = []
    true_tau = 3.5

    units = [f"Unit_{i}" for i in range(20)]
    periods = [2018, 2019, 2020, 2021, 2022, 2023]

    for i, u in enumerate(units):
        is_treated = (i < 4)
        base_u = 10.0 + i * 0.5
        for t_idx, yr in enumerate(periods):
            # Non-linear trend
            trend = 0.5 * t_idx
            noise = np.random.normal(0, 0.2)
            y = base_u + trend + noise
            w = 0
            if is_treated and yr >= 2022:
                w = 1
                y += true_tau

            records.append({
                "unit_id": u,
                "year": yr,
                "treatment": w,
                "outcome": round(float(y), 3)
            })

    res = compute_synthetic_diff_in_diff(
        records=records,
        unit_col="unit_id",
        time_col="year",
        treatment_col="treatment",
        outcome_col="outcome",
        num_bootstrap_reps=50
    )

    assert res["status"] == "success"
    assert res["num_treated_units"] == 4
    assert res["num_control_units"] == 16
    assert res["num_pre_periods"] == 4
    assert res["num_post_periods"] == 2
    assert res["first_treated_period"] == "2022"

    estimates = res["estimates"]
    # Check that tau_sdid is close to true_tau = 3.5
    assert abs(estimates["sdid_tau"] - true_tau) < 0.6
    assert estimates["is_significant"] is True
    assert estimates["sdid_p_value"] < 0.05
    assert estimates["sdid_se"] > 0

    diagnostics = res["diagnostics"]
    assert diagnostics["effective_donors_n_eff"] > 1.0
    assert diagnostics["rmse_sdid_pre"] >= 0.0

    assert len(res["top_donor_weights"]) > 0
    assert len(res["period_profiles"]) == 6
    assert "<svg" in res["svg_visualization"]
    assert "Arkhangelsky" in res["apa_narrative"]


def test_synthetic_diff_in_diff_insufficient_data():
    records = [
        {"unit": "A", "time": 1, "w": 0, "y": 10},
        {"unit": "B", "time": 1, "w": 1, "y": 12}
    ]
    res = compute_synthetic_diff_in_diff(
        records=records,
        unit_col="unit",
        time_col="time",
        treatment_col="w",
        outcome_col="y"
    )
    assert res["status"] == "error"
    assert "không đủ" in res["message"]


def test_synthetic_diff_in_diff_no_control_or_treated():
    # All treated
    records = []
    for i in range(25):
        records.append({"unit": f"U{i}", "time": 1, "w": 1, "y": 10})
        records.append({"unit": f"U{i}", "time": 2, "w": 1, "y": 12})
        records.append({"unit": f"U{i}", "time": 3, "w": 1, "y": 15})

    res = compute_synthetic_diff_in_diff(
        records=records,
        unit_col="unit",
        time_col="time",
        treatment_col="w",
        outcome_col="y"
    )
    assert res["status"] == "error"
    assert "đối chứng" in res["message"]
