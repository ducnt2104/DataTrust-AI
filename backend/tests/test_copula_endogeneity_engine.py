"""
Unit Tests for DataTrust Copula-Based Endogeneity Correction Engine (Iteration 168)
"""

import pytest
import numpy as np
from scipy import stats
from app.engine.copula_endogeneity_engine import run_copula_endogeneity_analysis


def test_copula_endogeneity_engine_detection_and_correction():
    rng = np.random.default_rng(42)
    n = 250
    true_rho = 0.70
    true_beta_p = 2.0
    true_beta_z = 0.5

    # Draw bivariate normal latent variables with correlation true_rho
    mean = [0.0, 0.0]
    cov = [[1.0, true_rho], [true_rho, 1.0]]
    v1, v2 = rng.multivariate_normal(mean, cov, size=n).T

    # P comes from skewed non-normal marginal distribution (Exponential)
    u1 = stats.norm.cdf(v1)
    p_raw = stats.expon.ppf(u1, scale=3.0)
    z_cov = rng.normal(0, 1, size=n)

    # Structural error linked via copula
    sigma_eps = 1.0
    epsilon = sigma_eps * v2

    # Structural response equation
    y = 4.0 + true_beta_p * p_raw + true_beta_z * z_cov + epsilon

    records = []
    for i in range(n):
        records.append({
            "id": f"resp_{i}",
            "answers": {
                "q_outcome": float(y[i]),
                "q_endogenous": float(p_raw[i]),
                "q_covariate": float(z_cov[i]),
            }
        })

    res = run_copula_endogeneity_analysis(
        records=records,
        outcome_question_id="q_outcome",
        endogenous_question_id="q_endogenous",
        covariate_question_ids=["q_covariate"],
        copula_family="gaussian",
        bootstrap_replications=40,
        alpha_level=0.05,
    )

    assert res["status"] == "success"
    assert res["sample_size"] == n
    assert "non_normality_diagnostics" in res
    assert res["non_normality_diagnostics"]["is_non_normal"]

    # Naive OLS is biased
    beta_naive = res["naive_ols"]["estimate"]
    assert beta_naive > 2.10

    # Endogeneity test correctly detects significant endogeneity
    assert res["endogeneity_test"]["is_endogenous"]
    assert res["endogeneity_test"]["implied_rho"] > 0.50
    assert res["endogeneity_test"]["p_value"] < 0.001

    # Copula-augmented estimate corrects the bias towards 2.0
    beta_copula = res["copula_augmented"]["estimate"]
    assert abs(beta_copula - 2.0) < abs(beta_naive - 2.0)
    assert abs(beta_copula - 2.0) < 0.10

    # SVG & Narrative verification
    assert "<svg" in res["svg_visualization"]
    assert "Park and Gupta (2012)" in res["apa_narrative"]


def test_copula_endogeneity_engine_exogenous_case():
    rng = np.random.default_rng(999)
    n = 150
    # Regressor and error are completely independent (rho = 0)
    p_raw = rng.exponential(scale=2.0, size=n)
    epsilon = rng.normal(0, 1, size=n)
    y = 3.0 + 1.5 * p_raw + epsilon

    records = [{"answers": {"q_outcome": float(y[i]), "q_endogenous": float(p_raw[i])}} for i in range(n)]

    res = run_copula_endogeneity_analysis(
        records=records,
        outcome_question_id="q_outcome",
        endogenous_question_id="q_endogenous",
        copula_family="gaussian",
        bootstrap_replications=20,
    )

    assert res["status"] == "success"
    # Should not reject exogeneity
    assert not res["endogeneity_test"]["is_endogenous"]
    assert res["endogeneity_test"]["p_value"] >= 0.05


def test_copula_endogeneity_engine_insufficient_sample():
    records = [{"answers": {"q_y": 1.0, "q_p": 2.0}} for _ in range(12)]
    res = run_copula_endogeneity_analysis(
        records=records,
        outcome_question_id="q_y",
        endogenous_question_id="q_p",
    )
    assert res["status"] == "insufficient_data"
    assert res["sample_size"] == 12
