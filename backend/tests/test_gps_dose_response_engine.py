# -*- coding: utf-8 -*-
"""
Unit tests for GPSDoseResponseEngine (Hirano & Imbens 2004)
"""
import pytest
import numpy as np
from app.engine.gps_dose_response_engine import GPSDoseResponseEngine


def test_gps_insufficient_sample():
    res = GPSDoseResponseEngine.estimate(
        data=[{"t": 1.0, "y": 10.0, "x": 2.0}],
        treatment_var="t",
        outcome_var="y",
        covariates=["x"]
    )
    assert res["status"] in ["INSUFFICIENT_DATA", "INSUFFICIENT_VALID_SAMPLE"]


def test_gps_dose_response_end_to_end():
    np.random.seed(42)
    n = 100

    # Covariates
    x1 = np.random.uniform(1.0, 5.0, n)
    x2 = np.random.normal(0, 1.0, n)

    # Continuous treatment: T = 2.0 + 0.8 * x1 - 0.5 * x2 + error
    t_dose = 2.0 + 0.8 * x1 - 0.5 * x2 + np.random.normal(0, 0.6, n)
    t_dose = np.maximum(0.5, t_dose)

    # True non-linear dose-response: Y = 10.0 + 3.0 * T - 0.25 * T^2 + 1.5 * x1 + error
    # Derivative dY/dT = 3.0 - 0.5 * T -> Peak at T* = 6.0
    y_outcome = 10.0 + 3.0 * t_dose - 0.25 * (t_dose ** 2) + 1.5 * x1 + np.random.normal(0, 0.8, n)

    data = [
        {
            "training_hours": float(t_dose[i]),
            "job_performance": float(y_outcome[i]),
            "baseline_skill": float(x1[i]),
            "motivation_score": float(x2[i])
        }
        for i in range(n)
    ]

    res = GPSDoseResponseEngine.estimate(
        data=data,
        treatment_var="training_hours",
        outcome_var="job_performance",
        covariates=["baseline_skill", "motivation_score"],
        n_grid_points=25
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "GENERALIZED_PROPENSITY_SCORE_DOSE_RESPONSE"

    diag = res["diagnostics"]
    assert diag["sample_size"] == 100
    assert diag["n_covariates"] == 2
    assert diag["treatment_model_r2"] > 0.15
    assert diag["outcome_model_r2"] > 0.20
    assert diag["optimal_dosage_peak"] > 1.0
    assert diag["peak_expected_outcome"] > diag["baseline_expected_outcome"]

    # Curve checks
    dr_curve = res["dose_response_curve"]
    assert len(dr_curve) == 25
    for pt in dr_curve:
        assert pt["ci_95_lower"] <= pt["expected_outcome_mu"] <= pt["ci_95_upper"]

    mte_curve = res["marginal_effects_curve"]
    assert len(mte_curve) == 25

    # SVG & Narrative
    assert "<svg" in res["svg_visualization"]
    assert "Generalized Propensity Score" in res["apa_narrative"]
    assert "Hirano & Imbens" in res["apa_narrative"]
