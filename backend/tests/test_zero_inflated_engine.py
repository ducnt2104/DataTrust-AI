# -*- coding: utf-8 -*-
"""
Unit tests for ZeroInflatedEngine (ZIP & ZINB)
"""
import pytest
import numpy as np
from app.engine.zero_inflated_engine import ZeroInflatedEngine


def test_zero_inflated_insufficient_sample():
    res = ZeroInflatedEngine.estimate(
        data=[{"cnt": 0, "x1": 1.0}],
        count_var="cnt",
        covariates=["x1"]
    )
    assert res["status"] in ["INSUFFICIENT_DATA", "INSUFFICIENT_VALID_SAMPLE"]


def test_zip_estimation_end_to_end():
    np.random.seed(42)
    n = 120
    x1 = np.random.uniform(1.0, 5.0, n)
    z1 = np.random.uniform(-2.0, 2.0, n)

    # Inflation process: logit(p) = -0.5 + 1.2 * z1
    p_infl = 1.0 / (1.0 + np.exp(-(-0.5 + 1.2 * z1)))
    is_structural_zero = np.random.binomial(1, p_infl)

    # Count process: ln(mu) = 0.5 + 0.4 * x1
    mu = np.exp(0.5 + 0.4 * x1)
    raw_counts = np.random.poisson(mu)

    # Final counts: structural zeros become 0
    final_y = np.where(is_structural_zero == 1, 0, raw_counts)

    data = [
        {"doctor_visits": int(final_y[i]), "health_risk": float(x1[i]), "uninsured_flag": float(z1[i])}
        for i in range(n)
    ]

    res = ZeroInflatedEngine.estimate(
        data=data,
        count_var="doctor_visits",
        covariates=["health_risk"],
        inflation_covariates=["uninsured_flag"],
        model_type="ZIP"
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "ZERO_INFLATED_ZIP"

    diag = res["diagnostics"]
    assert diag["sample_size"] == 120
    assert diag["zero_observations_count"] > 20
    assert diag["converged"] is True
    assert "vuong_test_z" in diag
    assert "aic_zi" in diag
    assert "bic_zi" in diag

    # Check coefficients
    c_coeffs = res["count_model_coefficients"]
    assert len(c_coeffs) == 2  # Intercept + health_risk
    x1_item = next(c for c in c_coeffs if c["variable"] == "health_risk")
    assert x1_item["incidence_rate_ratio_irr"] > 0
    assert x1_item["ci_95_lower"] < x1_item["ci_95_upper"]

    i_coeffs = res["inflation_model_coefficients"]
    assert len(i_coeffs) == 2  # Intercept + uninsured_flag
    z1_item = next(c for c in i_coeffs if c["variable"] == "uninsured_flag")
    assert z1_item["odds_ratio"] > 0

    # Frequency distribution
    freq = res["frequency_distribution"]
    assert len(freq["counts"]) > 0
    assert len(freq["observed_frequencies"]) == len(freq["counts"])
    assert len(freq["predicted_frequencies"]) == len(freq["counts"])

    # Visual & narrative
    assert "<svg" in res["svg_visualization"]
    assert "Zero-Inflated" in res["apa_narrative"]
    assert "Vuong" in res["apa_narrative"]


def test_zinb_estimation():
    np.random.seed(123)
    n = 100
    x1 = np.random.uniform(0.5, 4.0, n)

    # Count process with overdispersion
    mu = np.exp(0.3 + 0.5 * x1)
    # Negative binomial counts
    alpha = 0.5
    r = 1.0 / alpha
    p_nb = r / (r + mu)
    y_nb = np.random.negative_binomial(r, p_nb)

    # 30% random structural zeros
    mask_zero = (np.random.uniform(0, 1, n) < 0.35)
    final_y = np.where(mask_zero, 0, y_nb)

    data = [{"complaints": int(final_y[i]), "service_usage": float(x1[i])} for i in range(n)]

    res = ZeroInflatedEngine.estimate(
        data=data,
        count_var="complaints",
        covariates=["service_usage"],
        model_type="ZINB"
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "ZERO_INFLATED_ZINB"
    assert res["diagnostics"]["dispersion_parameter_alpha"] is not None
    assert res["diagnostics"]["dispersion_parameter_alpha"] > 0
