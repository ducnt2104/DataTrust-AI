"""
Unit tests for Nonparametric Boundary Kernel Deconvolution Engine
DataTrust Quantitative Intelligence System
"""

import pytest
import numpy as np
from app.engine.boundary_kernel_deconvolution_engine import run_boundary_kernel_deconvolution


def test_deconvolution_insufficient_data():
    res = run_boundary_kernel_deconvolution(
        records=[],
        variable_col="income"
    )
    assert res["status"] == "insufficient_data"


def test_deconvolution_gaussian_noise_recovery():
    np.random.seed(42)
    # True latent variable X ~ N(50, 10^2)
    # Measurement error U ~ N(0, 5^2)
    # Reliability ratio rho = 100 / (100 + 25) = 0.80
    n = 100
    X_true = np.random.normal(50.0, 10.0, size=n)
    U_noise = np.random.normal(0.0, 5.0, size=n)
    W_observed = X_true + U_noise

    records = [{"income": float(w)} for w in W_observed]

    res = run_boundary_kernel_deconvolution(
        records=records,
        variable_col="income",
        reliability_ratio=0.80,
        error_type="gaussian",
        lower_bound=0.0
    )

    assert res["status"] == "success"
    assert res["sample_size"] == 100
    assert res["reliability_ratio"] == 0.80
    assert res["attenuation_correction_factor"] > 1.10
    # True deconvoluted variance should be less than observed variance
    disp = res["dispersion_metrics"]
    assert disp["deconvoluted_variance"] < disp["observed_variance"]
    assert disp["variance_reduction_percent"] > 0.0
    assert "moments_comparison" in res
    assert "svg_visualization" in res
    assert "<svg" in res["svg_visualization"]
    assert "apa_narrative" in res
