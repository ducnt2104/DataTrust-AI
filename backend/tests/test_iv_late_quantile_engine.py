"""
Tests for Nonparametric IV-LATE Quantile Decomposition Engine
DataTrust Iteration 179
"""

import pytest
import numpy as np
from app.engine.iv_late_quantile_engine import run_iv_late_quantile_decomposition


def test_iv_late_quantile_decomposition_success():
    np.random.seed(42)
    records = []

    # 150 observations
    # Compliers (60%): D = Z
    # Always-takers (20%): D = 1
    # Never-takers (20%): D = 0
    # True LATE on compliers = +4.0
    for _ in range(150):
        z = 1.0 if np.random.uniform(0, 1) < 0.5 else 0.0
        u_type = np.random.uniform(0, 1)
        if u_type < 0.60:
            # Complier
            d = z
            y = 4.0 * d + float(np.random.normal(15, 1.5))
        elif u_type < 0.80:
            # Always-taker
            d = 1.0
            y = 4.0 * d + float(np.random.normal(18, 1.5))
        else:
            # Never-taker
            d = 0.0
            y = 4.0 * d + float(np.random.normal(12, 1.5))

        records.append({"treatment": d, "instrument": z, "outcome": y})

    res = run_iv_late_quantile_decomposition(
        records=records,
        treatment_col="treatment",
        instrument_col="instrument",
        outcome_col="outcome",
        num_quantiles=15
    )

    assert res["status"] == "success"
    assert res["sample_size"] == 150

    # Complier share should be roughly 0.50 - 0.70
    assert 0.45 <= res["complier_share"] <= 0.75
    assert res["first_stage_diff"] > 0.30

    # LATE should be around 4.0 (+- 1.5)
    assert 2.5 <= res["mean_late"] <= 5.5
    assert 2.5 <= res["median_qte_complier"] <= 5.5

    # Monotonicity test passes (no defiers)
    assert res["monotonicity_test"]["passed"] is True
    assert res["monotonicity_test"]["defiers_detected"] is False

    # Inequality and dominance
    ineq = res["complier_inequality"]
    assert "delta_gini_c" in ineq
    assert ineq["first_order_stochastic_dominance"] is True

    # Quantile points and visualizer
    assert len(res["quantile_curve"]) == 15
    assert "<svg" in res["svg_visualization"]
    assert "Abadie et al." in res["apa_narrative"]


def test_iv_late_quantile_weak_instrument():
    # Instrument completely uncorrelated with treatment (diff = 0)
    records = []
    for _ in range(40):
        records.append({"treatment": 1.0, "instrument": 1.0, "outcome": 10.0})
        records.append({"treatment": 1.0, "instrument": 0.0, "outcome": 10.0})
    res = run_iv_late_quantile_decomposition(
        records=records,
        treatment_col="treatment",
        instrument_col="instrument",
        outcome_col="outcome"
    )
    assert res["status"] in ["weak_instrument", "invalid_treatment"]


def test_iv_late_quantile_insufficient_sample():
    records = [{"treatment": 1.0, "instrument": 1.0, "outcome": 10.0} for _ in range(5)]
    res = run_iv_late_quantile_decomposition(
        records=records,
        treatment_col="treatment",
        instrument_col="instrument",
        outcome_col="outcome"
    )
    assert res["status"] == "insufficient_data"
