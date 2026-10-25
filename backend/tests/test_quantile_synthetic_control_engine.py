# -*- coding: utf-8 -*-
"""
Unit tests for Quantile Synthetic Control & Distributional Counterfactuals Engine (Gunsilius 2023 Econometrica).
"""

import pytest
import numpy as np
import pandas as pd
from app.engine.quantile_synthetic_control_engine import (
    estimate_quantile_synthetic_control,
    _compute_gini_coefficient,
    _fit_quantile_synthetic_weights
)


def test_compute_gini_coefficient():
    # Uniform/equal sample has Gini close to 0
    equal_sample = np.array([10.0, 10.0, 10.0, 10.0, 10.0])
    gini_eq = _compute_gini_coefficient(equal_sample)
    assert abs(gini_eq) < 1e-4

    # Highly unequal sample has higher Gini
    unequal_sample = np.array([1.0, 1.0, 1.0, 100.0])
    gini_uneq = _compute_gini_coefficient(unequal_sample)
    assert gini_uneq > 0.5


def test_fit_quantile_synthetic_weights():
    # Synthetic target constructed as 0.7 * donor_A + 0.3 * donor_B
    np.random.seed(42)
    donor_A = np.linspace(10, 50, 15)
    donor_B = np.linspace(20, 80, 15)
    Q_donors = np.column_stack([donor_A, donor_B])
    Q_treated = 0.7 * donor_A + 0.3 * donor_B

    weights = _fit_quantile_synthetic_weights(Q_treated, Q_donors)
    assert len(weights) == 2
    assert abs(np.sum(weights) - 1.0) < 1e-3
    assert weights[0] > 0.6  # Dominant weight on donor_A
    assert weights[1] > 0.2


def test_estimate_quantile_synthetic_control_full_pipeline():
    np.random.seed(123)
    # Generate panel dataset with 1 treated unit and 4 donor units across 6 time waves (waves 1-4 pre, 5-6 post)
    records = []
    units = ["Unit_Treated", "Donor_1", "Donor_2", "Donor_3", "Donor_4"]
    times = [1, 2, 3, 4, 5, 6]

    for u in units:
        base_mean = 50.0 if "Donor_1" in u else (40.0 if "Donor_2" in u else 45.0)
        for t in times:
            # Add treatment effect for Unit_Treated at t >= 5
            tau_shift = 8.0 if (u == "Unit_Treated" and t >= 5) else 0.0
            for i in range(30):
                val = np.random.normal(base_mean + 0.5 * t + tau_shift, 4.0)
                records.append({
                    "unit": u,
                    "wave": t,
                    "satisfaction": val
                })

    df = pd.DataFrame(records)

    res = estimate_quantile_synthetic_control(
        df=df,
        outcome_col="satisfaction",
        unit_col="unit",
        time_col="wave",
        treated_unit_id="Unit_Treated",
        treatment_time=5,
        quantiles=[0.10, 0.25, 0.50, 0.75, 0.90]
    )

    assert res["status"] == "SUCCESS"
    summary = res["overall_summary"]
    assert summary["treated_unit"] == "Unit_Treated"
    assert summary["treatment_time"] == "5"
    assert summary["n_valid_donors"] == 4
    assert summary["pre_treatment_periods"] == 4
    assert summary["post_treatment_periods"] == 2
    assert summary["median_qte_effect"] > 3.0  # Captures positive treatment effect ~8.0
    assert len(res["quantile_treatment_effects"]) == 5
    assert len(res["donor_weights"]) > 0
    assert "<svg" in res["svg_visualization"]
    assert "Quantile Synthetic Control" in res["apa_narrative"]
