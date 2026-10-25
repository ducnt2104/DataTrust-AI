"""
Unit tests for Synthetic Control Method (SCM) Engine.
"""

import pytest
import numpy as np
from app.engine.synthetic_control_engine import (
    solve_synthetic_control_weights,
    calculate_synthetic_control
)


def test_solve_synthetic_control_weights():
    # 3 distinct non-collinear donors
    x0 = np.array([
        [10.0, 5.0, 25.0],
        [20.0, 15.0, 10.0],
        [30.0, 45.0, 15.0]
    ])
    # x1 is constructed as 0.5 * D0 + 0.3 * D1 + 0.2 * D2
    true_w = np.array([0.5, 0.3, 0.2])
    x1 = x0 @ true_w

    w_opt, loss = solve_synthetic_control_weights(x1, x0)

    assert len(w_opt) == 3
    assert np.isclose(np.sum(w_opt), 1.0, atol=1e-4)
    assert np.all(w_opt >= -1e-5)
    # Reconstructed synthetic series should match x1 exactly
    reconstructed = x0 @ w_opt
    assert np.allclose(reconstructed, x1, atol=1e-2)
    assert loss < 1e-3


def test_calculate_synthetic_control_full_pipeline():
    # 5 units: Region_T (treated), Region_D1, Region_D2, Region_D3, Region_D4
    # 6 periods: 1, 2, 3 (pre), 4, 5, 6 (post)
    # True data: Region_T = 0.6 * D1 + 0.4 * D2 in pre-periods
    # In post-periods, Region_T gets +10.0 intervention bump
    panel_data = []
    periods = [1, 2, 3, 4, 5, 6]

    d1_vals = [20.0, 22.0, 24.0, 25.0, 26.0, 27.0]
    d2_vals = [10.0, 12.0, 14.0, 15.0, 16.0, 17.0]
    d3_vals = [5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    d4_vals = [30.0, 32.0, 31.0, 33.0, 35.0, 34.0]

    for idx, p in enumerate(periods):
        # Donors
        panel_data.append({"unit": "D1", "wave": p, "score": d1_vals[idx]})
        panel_data.append({"unit": "D2", "wave": p, "score": d2_vals[idx]})
        panel_data.append({"unit": "D3", "wave": p, "score": d3_vals[idx]})
        panel_data.append({"unit": "D4", "wave": p, "score": d4_vals[idx]})

        # Treated unit
        base_t = 0.6 * d1_vals[idx] + 0.4 * d2_vals[idx]
        if p >= 4:
            base_t += 10.0  # true treatment effect
        panel_data.append({"unit": "Treated_Unit", "wave": p, "score": base_t})

    res = calculate_synthetic_control(
        panel_data=panel_data,
        unit_col="unit",
        period_col="wave",
        outcome_col="score",
        treated_unit="Treated_Unit",
        treatment_period=4
    )

    assert res["status"] == "SUCCESS"
    assert res["donor_pool_count"] == 4
    # ATT should be very close to +10.0
    assert np.isclose(res["att_effect"], 10.0, atol=0.5)
    # Pre RMSPE should be near 0
    assert res["rmspe_pre"] < 0.2
    # Post RMSPE should be near 10.0
    assert res["rmspe_post"] > 8.0
    # RMSPE ratio should be high
    assert res["rmspe_ratio"] > 10.0
    # Placebo empirical p-value should be low
    assert res["empirical_p_value"] <= 0.25
    # Trajectory length
    assert len(res["trajectory"]) == 6
    assert "<svg" in res["svg_chart"]
    assert "Synthetic Control Method" in res["apa_narrative"]
    assert len(res["top_donor_weights"]) >= 1


def test_calculate_synthetic_control_edge_cases():
    # Empty data
    res_empty = calculate_synthetic_control([], "unit", "wave", "score", "T", 2)
    assert res_empty["status"] == "NO_DATA"

    # Treated unit not found
    res_not_found = calculate_synthetic_control([
        {"unit": "A", "wave": 1, "score": 10},
        {"unit": "B", "wave": 1, "score": 20}
    ], "unit", "wave", "score", "NonExistent", 1)
    assert res_not_found["status"] == "TREATED_UNIT_NOT_FOUND"

    # Insufficient donors
    res_no_donors = calculate_synthetic_control([
        {"unit": "T", "wave": 1, "score": 10},
        {"unit": "A", "wave": 1, "score": 20}
    ], "unit", "wave", "score", "T", 1)
    assert res_no_donors["status"] == "INSUFFICIENT_DONORS"
