# -*- coding: utf-8 -*-
"""
Unit tests for TWFE Decomposition & Negative Weights Engine (de Chaisemartin & D'Haultfoeuille 2020 AER).
"""

import pytest
import numpy as np
import pandas as pd
from app.engine.twfe_decomposition_engine import estimate_twfe_decomposition


def test_twfe_decomposition_constant_treatment_effects():
    # 20 units, 4 waves, simultaneous adoption at wave 3 for 10 units
    np.random.seed(42)
    records = []
    for u in range(20):
        u_fe = np.random.normal(10, 2)
        is_treated_group = (u < 10)
        for t in range(1, 5):
            t_fe = 1.5 * t
            d = 1.0 if (is_treated_group and t >= 3) else 0.0
            # Constant treatment effect = 3.0
            y = u_fe + t_fe + 3.0 * d + np.random.normal(0, 0.3)
            records.append({
                "unit": f"unit_{u}",
                "wave": t,
                "outcome": y,
                "treatment": d
            })

    df = pd.DataFrame(records)

    res = estimate_twfe_decomposition(
        df=df,
        outcome_col="outcome",
        treatment_col="treatment",
        unit_col="unit",
        time_col="wave",
        alpha_level=0.05
    )

    assert res["status"] == "SUCCESS"
    summary = res["overall_summary"]
    assert summary["n_units"] == 20
    assert summary["n_time_periods"] == 4
    assert abs(summary["beta_twfe"] - 3.0) < 0.5
    assert abs(summary["did_m_estimate"] - 3.0) < 0.5
    assert "<svg" in res["svg_visualization"]
    assert "Two-Way Fixed Effects" in res["apa_narrative"]


def test_twfe_decomposition_staggered_with_negative_weights():
    # Canonical de Chaisemartin & D'Haultfoeuille (2020 AER) DGP:
    # Group 1: Already treated at t=1, continues treated at t=2, 3 (early adopters)
    # Group 2: Switched to treatment at t=2 (switchers)
    # Group 3: Never treated (stayers)
    np.random.seed(123)
    records = []
    for u in range(30):
        u_fe = float(u % 5)
        for t in [1, 2, 3]:
            t_fe = 2.0 * t
            if u < 10:  # Already treated
                d = 1.0
                tau = 10.0 + 3.0 * t  # dynamic growing effect
            elif u < 20:  # Switchers at t >= 2
                d = 1.0 if t >= 2 else 0.0
                tau = 5.0 if t >= 2 else 0.0
            else:  # Never treated
                d = 0.0
                tau = 0.0

            y = u_fe + t_fe + tau + np.random.normal(0, 0.1)
            records.append({
                "unit": f"entity_{u}",
                "period": t,
                "score": y,
                "treated": d
            })

    df = pd.DataFrame(records)

    res = estimate_twfe_decomposition(
        df=df,
        outcome_col="score",
        treatment_col="treated",
        unit_col="unit",
        time_col="period"
    )

    assert res["status"] == "SUCCESS"
    summary = res["overall_summary"]
    assert summary["n_treated_cells"] > 0
    # Negative weights MUST appear for already-treated units serving as controls
    assert summary["n_negative_cells"] > 0
    assert summary["sum_negative_weights"] < -0.1
    assert summary["minimal_heterogeneity_sd_sigma_fe"] > 0.0
    assert len(res["top_negative_weights"]) > 0
    # DID_M cleanly captures the instantaneous switcher effect (~5.0)
    assert abs(summary["did_m_estimate"] - 5.0) < 1.0


def test_twfe_decomposition_edge_cases():
    df_small = pd.DataFrame({
        "unit": ["A", "B"],
        "wave": [1, 1],
        "outcome": [1.0, 2.0],
        "treatment": [0.0, 1.0]
    })
    # T=1 should raise error
    with pytest.raises(ValueError, match="at least 2 distinct time periods"):
        estimate_twfe_decomposition(
            df=df_small,
            outcome_col="outcome",
            treatment_col="treatment",
            unit_col="unit",
            time_col="wave"
        )
