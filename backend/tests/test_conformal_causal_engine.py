"""
Unit tests for Conformal Causal Inference Engine
(Chernozhukov et al. 2021; Lei & Candès 2021)
DataTrust Iteration 180
"""

import pytest
import numpy as np
from app.engine.conformal_causal_engine import run_conformal_causal_inference


def test_conformal_causal_inference_success():
    np.random.seed(42)
    n = 70
    records = []

    for i in range(n):
        x1 = float(np.random.normal(0, 1))
        x2 = float(np.random.normal(5, 2))
        # Treatment assignment dependent on covariates (selection on observables)
        prob_d = 1.0 / (1.0 + np.exp(-(0.5 * x1 + 0.2 * (x2 - 5.0))))
        d = 1 if np.random.uniform() < prob_d else 0
        # True outcome with true treatment effect tau = 5.0
        y = 20.0 + 2.0 * x1 + 1.5 * x2 + 5.0 * d + float(np.random.normal(0, 1.0))

        records.append({
            "treatment": d,
            "outcome": y,
            "cov1": x1,
            "cov2": x2
        })

    res = run_conformal_causal_inference(
        records=records,
        treatment_col="treatment",
        outcome_col="outcome",
        covariate_cols=["cov1", "cov2"],
        alpha=0.05,
        calibration_ratio=0.4
    )

    assert res["status"] == "success"
    assert res["sample_size"] == 70
    assert res["nominal_coverage"] == 0.95
    assert res["empirical_calibration_coverage"] >= 0.80
    assert res["treatment_effect_summary"]["ate_conformal"] > 3.0
    assert res["treatment_effect_summary"]["avg_width_ite"] > 0
    assert len(res["sample_ite_points"]) > 5
    assert "<svg" in res["svg_visualization"]
    assert "DataTrust" in res["apa_narrative"]
    assert "Chernozhukov" in res["apa_narrative"]


def test_conformal_causal_insufficient_sample():
    records = [{"treatment": 1, "outcome": 10.0} for _ in range(15)]
    res = run_conformal_causal_inference(
        records=records,
        treatment_col="treatment",
        outcome_col="outcome"
    )
    assert res["status"] == "insufficient_data"
    assert "tối thiểu 30" in res["message"]


def test_conformal_causal_invalid_treatment():
    # All treated
    records = [{"treatment": 1, "outcome": float(10.0 + i)} for i in range(35)]
    res = run_conformal_causal_inference(
        records=records,
        treatment_col="treatment",
        outcome_col="outcome"
    )
    assert res["status"] == "invalid_treatment"
