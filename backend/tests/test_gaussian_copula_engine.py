import pytest
import numpy as np
import scipy.stats
from app.engine.gaussian_copula_engine import (
    _inv_norm_cdf,
    _empirical_cdf,
    _jarque_bera_test,
    run_gaussian_copula_estimation
)


def test_copula_helpers():
    # 1. Test inverse standard normal CDF
    assert abs(_inv_norm_cdf(0.5) - 0.0) < 1e-4
    assert abs(_inv_norm_cdf(0.8413447) - 1.0) < 1e-3
    assert abs(_inv_norm_cdf(0.025) - (-1.96)) < 0.01
    assert abs(_inv_norm_cdf(0.975) - 1.96) < 0.01

    # 2. Test empirical CDF monotonicity
    arr = np.array([1.2, 5.4, 2.3, 8.9, 0.5])
    ecdf = _empirical_cdf(arr)
    assert len(ecdf) == 5
    assert np.all(ecdf > 0.0) and np.all(ecdf < 1.0)
    assert np.all(np.diff(ecdf[np.argsort(arr)]) > 0.0)

    # 3. Test Jarque-Bera on non-normal distribution (Exponential)
    rng = np.random.RandomState(42)
    exp_data = rng.exponential(scale=2.0, size=150)
    jb_stat, jb_p, skew, kurt = _jarque_bera_test(exp_data)
    assert jb_p < 0.01  # Correctly identifies non-normality
    assert skew > 0.5   # Positive skewness detected


def test_gaussian_copula_engine_with_endogeneity():
    rng = np.random.RandomState(42)
    N = 250

    # Canonical Park & Gupta (2012) DGP: Bivariate Gaussian Copula
    rho_true = 0.65
    cov_mat = np.array([[1.0, rho_true], [rho_true, 1.0]])
    z = rng.multivariate_normal([0, 0], cov_mat, size=N)
    z1, z2 = z[:, 0], z[:, 1]

    # Non-normal marginal for endogenous P (Exponential distribution)
    u_p = scipy.stats.norm.cdf(z1)
    P = -2.0 * np.log(1.0 - np.clip(u_p, 1e-6, 1.0 - 1e-6))

    # Control Variable X
    X1 = rng.normal(5.0, 1.0, size=N)

    # Structural error epsilon correlated with P through copula
    eps = 1.5 * z2

    # Outcome Y: True causal effect of P is 2.0
    Y = 10.0 + 2.0 * P + 0.8 * X1 + eps

    records = []
    for i in range(N):
        records.append({
            "endog_p": float(P[i]),
            "outcome_y": float(Y[i]),
            "control_x1": float(X1[i])
        })

    res = run_gaussian_copula_estimation(
        records=records,
        endogenous_var="endog_p",
        outcome_var="outcome_y",
        control_vars=["control_x1"],
        n_bootstraps=150,
        seed=42
    )

    assert res["status"] == "success"
    diag = res["sample_diagnostics"]
    assert diag["n_observations"] == N
    assert diag["non_normality_satisfied"] is True
    assert diag["copula_vif"] < 10.0  # Well conditioned

    # Naive OLS vs Copula
    naive = res["naive_ols"]
    cop = res["copula_corrected"]

    # Endogeneity detected: rho is positive and significant
    assert cop["copula_rho_parameter"] > 0
    assert cop["is_endogeneity_significant"] is True
    assert diag["endogeneity_status"] == "ENDOGENEITY_CONFIRMED"

    # Naive OLS should be higher than copula-corrected (upward bias corrected)
    assert naive["beta"] > cop["beta_copula"]
    assert cop["endogeneity_bias_gap"] > 0
    # Copula beta should be close to true 2.0
    assert abs(cop["beta_copula"] - 2.0) < 0.25

    # Chart and APA narrative
    assert "<svg" in res["svg_chart"]
    assert "Park & Gupta" in res["apa_narrative"]
    assert "Jarque-Bera" in res["apa_narrative"]


def test_gaussian_copula_engine_exogenous_case():
    rng = np.random.RandomState(202)
    N = 90

    # Exogenous non-normal regressor P (independent of error)
    P = np.exp(rng.normal(0, 0.6, size=N))
    Y = 5.0 + 1.8 * P + rng.normal(0, 1.0, size=N)

    records = [{"p": float(P[i]), "y": float(Y[i])} for i in range(N)]

    res = run_gaussian_copula_estimation(
        records=records,
        endogenous_var="p",
        outcome_var="y",
        n_bootstraps=100,
        seed=202
    )

    assert res["status"] == "success"
    cop = res["copula_corrected"]
    # In exogenous setting, rho is near zero
    assert abs(cop["copula_rho_parameter"]) < 1.0


def test_gaussian_copula_engine_insufficient_sample():
    records = [{"p": 1.0, "y": 2.0} for _ in range(12)]
    res = run_gaussian_copula_estimation(
        records=records,
        endogenous_var="p",
        outcome_var="y"
    )
    assert res["status"] == "error"
    assert "quá ít" in res["message"]
