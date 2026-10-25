"""
Unit tests for Generalized Additive Models (GAM) & Penalized Spline Engine
"""

import math
import numpy as np
import pytest
from app.engine.gam_spline_engine import GAMSplineEngine


def test_gam_insufficient_sample():
    # N < 25
    small_data = [{"X": i, "Y": i * 2} for i in range(15)]
    res = GAMSplineEngine.estimate(small_data, "X", "Y")
    assert res["status"] == "INSUFFICIENT_SAMPLE"

    # Zero variance in predictor
    const_data = [{"X": 5.0, "Y": i} for i in range(30)]
    res_const = GAMSplineEngine.estimate(const_data, "X", "Y")
    assert res_const["status"] == "INSUFFICIENT_SAMPLE"


def test_gam_synthetic_nonlinear():
    np.random.seed(42)
    N = 100
    rows = []
    # Inverted-U quadratic curve: Y = 10 + 6*X - 0.75*X^2 + noise, peak around X = 4
    for i in range(N):
        x = float(np.random.uniform(0.5, 7.5))
        y = 10.0 + 6.0 * x - 0.75 * (x ** 2) + float(np.random.normal(0, 0.4))
        rows.append({"Hours": x, "Satisfaction": y})

    result = GAMSplineEngine.estimate(
        data=rows,
        predictor_var="Hours",
        outcome_var="Satisfaction",
        n_knots=8,
        grid_points=50,
    )

    assert result["status"] == "SUCCESS"
    assert result["model_type"] == "GENERALIZED_ADDITIVE_MODEL_SPLINE"
    assert "diagnostics" in result
    assert result["diagnostics"]["effective_degrees_of_freedom"] > 1.2
    assert "smooth_curve" in result
    assert len(result["smooth_curve"]) == 50
    assert "tipping_points" in result
    assert "svg_visualization" in result
    assert "<svg" in result["svg_visualization"]
    assert "apa_narrative" in result
    assert "Hastie" in result["apa_narrative"]


def test_gam_with_covariates():
    np.random.seed(123)
    N = 80
    rows = []
    for i in range(N):
        x = float(np.random.uniform(1, 10))
        z = float(np.random.normal(0, 1))
        y = 5.0 + 2.0 * math.sin(x) + 1.5 * z + float(np.random.normal(0, 0.3))
        rows.append({"X": x, "Y": y, "Z": z})

    res = GAMSplineEngine.estimate(
        data=rows,
        predictor_var="X",
        outcome_var="Y",
        covariate_vars=["Z"],
        n_knots=8,
    )
    assert res["status"] == "SUCCESS"
    assert res["diagnostics"]["N"] == 80
