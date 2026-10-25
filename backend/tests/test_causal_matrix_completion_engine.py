"""
Tests for Causal Matrix Completion Engine (Athey et al. 2021 JASA)
DataTrust Iteration 178
"""

import pytest
import numpy as np
from app.engine.causal_matrix_completion_engine import run_causal_matrix_completion


def test_causal_matrix_completion_estimation_success():
    np.random.seed(42)
    records = []

    # 6 units, 5 periods
    units = [f"Unit_{i}" for i in range(1, 7)]
    periods = [f"202{t}" for t in range(5)]

    # Latent factors: 2 components
    u_factors = np.array([1.0, 1.5, 2.0, 1.2, 0.8, 1.8])
    v_factors = np.array([2.0, 2.5, 3.0, 3.2, 4.0])
    true_tau = 5.0

    for i, u in enumerate(units):
        for t, p in enumerate(periods):
            baseline = u_factors[i] * v_factors[t]
            # Staggered treatment:
            # Units 1, 2: Never treated
            # Units 3, 4: Adopt at t >= 2 (2022)
            # Units 5, 6: Adopt at t >= 3 (2023)
            is_treated = False
            if i in [2, 3] and t >= 2:
                is_treated = True
            elif i in [4, 5] and t >= 3:
                is_treated = True

            effect = true_tau if is_treated else 0.0
            # Multiple survey respondents per cell
            for _ in range(5):
                y = baseline + effect + float(np.random.normal(0, 0.3))
                records.append({
                    "unit": u,
                    "period": p,
                    "outcome": y,
                    "treatment": 1.0 if is_treated else 0.0
                })

    res = run_causal_matrix_completion(
        records=records,
        unit_col="unit",
        period_col="period",
        outcome_col="outcome",
        treatment_col="treatment",
        lambda_nuc=0.2,
        max_iter=100
    )

    assert res["status"] == "success"
    assert res["dimensions"]["units_count"] == 6
    assert res["dimensions"]["periods_count"] == 5
    assert res["adoption_counts"]["treated_cells"] > 0
    assert res["adoption_counts"]["control_cells"] > 0

    est = res["estimates"]
    # ATT should be around +5.0 (+- 1.5)
    assert 3.5 <= est["att"] <= 6.5
    assert est["se"] > 0
    assert est["p_value"] < 0.05

    algo = res["algorithm_convergence"]
    assert algo["latent_rank"] >= 1
    assert algo["control_rmse"] >= 0.0

    assert len(res["unit_heterogeneity"]) == 4  # 4 treated units
    assert len(res["event_study_trajectory"]) >= 2
    assert "<svg" in res["svg_visualization"]
    assert "Athey et al." in res["apa_narrative"]


def test_causal_matrix_completion_insufficient_sample():
    records = [{"unit": "U1", "period": "2020", "outcome": 10.0, "treatment": 0.0} for _ in range(5)]
    res = run_causal_matrix_completion(
        records=records,
        unit_col="unit",
        period_col="period",
        outcome_col="outcome",
        treatment_col="treatment"
    )
    assert res["status"] == "insufficient_data"


def test_causal_matrix_completion_insufficient_dimensions():
    # Only 2 units
    records = []
    for u in ["U1", "U2"]:
        for t in ["2020", "2021", "2022"]:
            for _ in range(5):
                records.append({"unit": u, "period": t, "outcome": 10.0, "treatment": 0.0})
    res = run_causal_matrix_completion(
        records=records,
        unit_col="unit",
        period_col="period",
        outcome_col="outcome",
        treatment_col="treatment"
    )
    assert res["status"] == "insufficient_dimensions"
