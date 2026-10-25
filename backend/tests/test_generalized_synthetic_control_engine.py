"""
Unit tests for Generalized Synthetic Control Engine (Gsynth)
DataTrust Quantitative Intelligence System
"""

import pytest
import numpy as np
from app.engine.generalized_synthetic_control_engine import evaluate_generalized_synthetic_control


def test_gsynth_insufficient_data():
    res = evaluate_generalized_synthetic_control(
        records=[],
        outcome_col="y",
        unit_col="unit",
        time_col="time",
        treatment_col="d"
    )
    assert res["status"] == "insufficient_data"


def test_gsynth_panel_estimation():
    np.random.seed(42)
    # 4 control units, 2 treated units across 6 time periods (t = 1..6)
    # Unit 1 treated at t=4, Unit 2 treated at t=5
    records = []
    times = [1, 2, 3, 4, 5, 6]
    ctrl_units = ["C1", "C2", "C3", "C4"]
    tr_units = ["T1", "T2"]

    # Latent factor f_t
    factor_t = np.array([1.0, 1.5, 2.0, 2.5, 3.0, 3.5])

    # Control units
    for u_idx, u in enumerate(ctrl_units):
        lambda_u = 0.5 + 0.3 * u_idx
        for t_idx, t in enumerate(times):
            y_val = 10.0 + lambda_u * factor_t[t_idx] + np.random.normal(0, 0.1)
            records.append({
                "unit": u,
                "time": t,
                "y": y_val,
                "d": 0,
                "x_cov": 2.0 + 0.1 * t
            })

    # Treated units
    for u in tr_units:
        t_adopt = 4 if u == "T1" else 5
        lambda_u = 1.2
        for t_idx, t in enumerate(times):
            treat = 1 if t >= t_adopt else 0
            treatment_effect = 4.5 if treat == 1 else 0.0
            y_val = 10.0 + lambda_u * factor_t[t_idx] + treatment_effect + np.random.normal(0, 0.1)
            records.append({
                "unit": u,
                "time": t,
                "y": y_val,
                "d": treat,
                "x_cov": 2.0 + 0.1 * t
            })

    res = evaluate_generalized_synthetic_control(
        records=records,
        outcome_col="y",
        unit_col="unit",
        time_col="time",
        treatment_col="d",
        covariate_cols=["x_cov"],
        n_factors=1
    )

    assert res["status"] == "success"
    assert res["n_treated_units"] == 2
    assert res["n_control_units"] == 4
    assert res["n_time_periods"] == 6
    assert res["n_latent_factors"] >= 1
    assert "overall_att" in res
    # True treatment effect is +4.5; estimate should be positive and close
    assert res["overall_att"]["estimate"] > 3.0
    assert "svg_visualization" in res
    assert "<svg" in res["svg_visualization"]
    assert len(res["event_study_trajectory"]) > 0
    assert "apa_narrative" in res
