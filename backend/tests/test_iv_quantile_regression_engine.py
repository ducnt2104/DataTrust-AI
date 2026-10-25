import pytest
import numpy as np
from app.engine.iv_quantile_regression_engine import IVQuantileRegressionEngine


def test_iv_qr_end_to_end():
    np.random.seed(42)
    n = 150

    # Strong instrument Z
    z = np.random.normal(0, 1.5, n)
    # Unobserved confounder U
    u = np.random.normal(0, 1.0, n)
    # Endogenous treatment D: correlated with U and driven by Z
    d = 1.8 * z + 1.2 * u + np.random.normal(0, 0.5, n)

    # Outcome Y with heterogeneous treatment effect: higher at upper quantiles
    # Y = alpha(U) * D + X + U
    # Heterogeneous effect: alpha is higher when U is higher
    x = np.random.normal(0, 1.0, n)
    y = 2.0 * d + 0.8 * x + u * (1.0 + 0.3 * np.abs(d))

    data = []
    for i in range(n):
        data.append({
            "y": float(y[i]),
            "d": float(d[i]),
            "z": float(z[i]),
            "x": float(x[i]),
        })

    res = IVQuantileRegressionEngine.analyze(
        data=data,
        outcome_var="y",
        treatment_var="d",
        instrument_var="z",
        covariate_vars=["x"],
        quantiles=[0.10, 0.25, 0.50, 0.75, 0.90],
    )

    assert res["status"] == "success"
    summary = res["summary"]
    assert summary["n_samples"] == n
    assert summary["instrument_strength"] == "STRONG_INSTRUMENT"
    assert summary["instrument_f_stat"] > 10.0
    assert "tsls_estimate" in summary

    q_estimates = res["quantile_estimates"]
    assert len(q_estimates) == 5

    # Check median estimate
    q50 = next(q for q in q_estimates if abs(q["quantile"] - 0.50) < 1e-4)
    assert q50["ci_lower"] <= q50["iv_qr_estimate"] <= q50["ci_upper"]
    assert "endogeneity_bias_gap" in q50

    assert "<svg" in res["svg_chart"]
    assert "Hồi quy Phân vị Biến công cụ" in res["apa_narrative"]


def test_iv_qr_weak_instrument():
    np.random.seed(123)
    n = 60
    z = np.random.normal(0, 1, n)
    d = 0.05 * z + np.random.normal(0, 1, n)
    y = 1.0 * d + np.random.normal(0, 1, n)

    data = [{"y": float(y[i]), "d": float(d[i]), "z": float(z[i])} for i in range(n)]

    res = IVQuantileRegressionEngine.analyze(
        data=data,
        outcome_var="y",
        treatment_var="d",
        instrument_var="z",
        quantiles=[0.50],
    )

    assert res["status"] == "success"
    assert res["summary"]["instrument_strength"] == "WEAK_INSTRUMENT"
    assert "Biến công cụ yếu" in res["summary"]["strength_warning"]


def test_iv_qr_insufficient_sample():
    data = [{"y": 1.0, "d": 2.0, "z": 0.5}] * 10
    res = IVQuantileRegressionEngine.analyze(
        data=data,
        outcome_var="y",
        treatment_var="d",
        instrument_var="z",
    )
    assert res["status"] == "error"
    assert "không đủ quan sát" in res["message"]
