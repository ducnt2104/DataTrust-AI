"""
Tests for Distributional Synthetic Control & Counterfactual Density Engine
DataTrust Iteration 176
"""

import pytest
import numpy as np
from app.engine.distributional_synthetic_control_engine import run_distributional_synthetic_control


def test_distributional_synthetic_control_estimation_success():
    np.random.seed(42)
    records = []

    # Units: Unit_T, Unit_C1, Unit_C2, Unit_C3
    # Periods: 2020, 2021 (pre), 2022 (post)
    # Unit_C1: baseline normal(10, 2)
    # Unit_C2: baseline normal(20, 2)
    # Unit_C3: baseline normal(50, 5) - outlier donor
    # Unit_T pre: 0.6 * C1 + 0.4 * C2 = normal(14, 2)
    # Unit_T post: normal(14, 2) + 5.0 true causal effect

    for period in ["2020", "2021", "2022"]:
        # Donor C1
        for _ in range(50):
            records.append({"unit": "Unit_C1", "period": period, "outcome": float(np.random.normal(10, 2))})
        # Donor C2
        for _ in range(50):
            records.append({"unit": "Unit_C2", "period": period, "outcome": float(np.random.normal(20, 2))})
        # Donor C3
        for _ in range(50):
            records.append({"unit": "Unit_C3", "period": period, "outcome": float(np.random.normal(50, 5))})
        # Treated Unit_T
        effect = 5.0 if period == "2022" else 0.0
        for _ in range(50):
            records.append({"unit": "Unit_T", "period": period, "outcome": float(np.random.normal(14, 2) + effect)})

    res = run_distributional_synthetic_control(
        records=records,
        unit_col="unit",
        period_col="period",
        outcome_col="outcome",
        treated_unit_val="Unit_T",
        post_period_vals=["2022"],
        num_quantiles=15,
        num_placebos=3
    )

    assert res["status"] == "success"
    assert res["treated_unit"] == "Unit_T"
    assert res["num_donors"] == 3
    assert "2022" in res["post_periods"]
    assert "2020" in res["pre_periods"]
    assert "2021" in res["pre_periods"]

    # Treatment effect should be around +5.0 (+- 1.5)
    assert 3.5 <= res["mean_treatment_effect"] <= 6.5
    assert 3.5 <= res["median_treatment_effect"] <= 6.5
    assert res["wasserstein_distance"] > 0.0

    # Donor C1 + C2 should dominate C3
    weights = {d["donor_unit"]: d["synthetic_weight"] for d in res["donor_weights"]}
    assert weights["Unit_C1"] + weights["Unit_C2"] > 0.80

    # Inequality and stochastic dominance checks
    ineq = res["inequality_diagnostics"]
    assert "observed_gini" in ineq
    assert "synthetic_gini" in ineq
    assert "first_order_stochastic_dominance" in ineq
    assert ineq["first_order_stochastic_dominance"] is True

    # Quantile curve and SVG check
    assert len(res["quantile_curve"]) == 15
    assert "<svg" in res["svg_visualization"]
    assert "DataTrust · Distributional Synthetic Control" in res["svg_visualization"]
    assert "Chernozhukov et al." in res["apa_narrative"]


def test_distributional_synthetic_control_insufficient_sample():
    records = [{"unit": "U1", "period": "2020", "outcome": 10.0} for _ in range(5)]
    res = run_distributional_synthetic_control(
        records=records,
        unit_col="unit",
        period_col="period",
        outcome_col="outcome",
        treated_unit_val="U1",
        post_period_vals=["2021"]
    )
    assert res["status"] == "insufficient_data"


def test_distributional_synthetic_control_missing_treated():
    records = [{"unit": f"U_{i}", "period": "2020", "outcome": 10.0 + i} for i in range(25)]
    res = run_distributional_synthetic_control(
        records=records,
        unit_col="unit",
        period_col="period",
        outcome_col="outcome",
        treated_unit_val="NonExistentTreated",
        post_period_vals=["2021"]
    )
    assert res["status"] == "error"
