"""
Unit tests for PowerAnalysisEngine (Cochran, Yamane, T-Test & Correlation Power)
"""

import pytest
import math
from app.engine.power_engine import PowerAnalysisEngine

def test_normal_ppf_and_cdf():
    # Test standard normal quantiles
    z_95 = PowerAnalysisEngine.normal_ppf(0.975)
    assert abs(z_95 - 1.960) < 0.005

    z_50 = PowerAnalysisEngine.normal_ppf(0.50)
    assert abs(z_50 - 0.0) < 1e-4

    cdf_0 = PowerAnalysisEngine.normal_cdf(0.0)
    assert abs(cdf_0 - 0.50) < 1e-4

def test_cochran_infinite_and_finite_population():
    # Cochran textbook standard: e = 0.05, p = 0.5, 95% CI -> n0 = 385
    res_inf = PowerAnalysisEngine.calculate_cochran_sample_size(
        confidence_level=0.95,
        margin_of_error=0.05,
        proportion=0.50
    )
    assert res_inf["required_sample_size"] == 385
    assert res_inf["fpc_applied"] is False

    # Finite population correction (e.g., N_pop = 500) -> n_adj should be smaller (~217)
    res_fpc = PowerAnalysisEngine.calculate_cochran_sample_size(
        confidence_level=0.95,
        margin_of_error=0.05,
        proportion=0.50,
        population_size=500
    )
    assert res_fpc["fpc_applied"] is True
    assert res_fpc["required_sample_size"] < 385
    assert 200 <= res_fpc["required_sample_size"] <= 230

def test_ttest_power_and_required_n():
    # Cohen (1988) standard: for d = 0.5, alpha = 0.05, power = 0.80 -> n ≈ 64 per group (total 128)
    req_n = PowerAnalysisEngine.calculate_ttest_required_n(effect_size_d=0.50, target_power=0.80)
    assert 60 <= req_n <= 70

    # Calculate post-hoc power with this n
    pwr = PowerAnalysisEngine.calculate_ttest_power(n_per_group=req_n, effect_size_d=0.50)
    assert pwr >= 0.79

def test_correlation_power_and_required_n():
    # Pearson r = 0.30, alpha = 0.05, power = 0.80 -> N ≈ 84-86
    req_n = PowerAnalysisEngine.calculate_correlation_required_n(expected_r=0.30, target_power=0.80)
    assert 80 <= req_n <= 90

    # Verify post-hoc power
    pwr = PowerAnalysisEngine.calculate_correlation_power(n_total=req_n, expected_r=0.30)
    assert pwr >= 0.79

def test_generate_power_curve():
    curve = PowerAnalysisEngine.generate_power_curve(analysis_type="ttest", effect_size=0.50, max_n=100, step=20)
    assert len(curve) > 3
    # Check monotonically increasing power
    powers = [p["power"] for p in curve]
    for i in range(len(powers) - 1):
        assert powers[i] <= powers[i + 1]

def test_evaluate_survey_sample_adequacy():
    # Evaluation on N = 120
    eval_res = PowerAnalysisEngine.evaluate_survey_sample_adequacy(current_n=120)
    assert eval_res["status"] in ("ADEQUATE", "MODERATE")
    assert "apa_narrative" in eval_res
    assert eval_res["achieved_margin_of_error"] < 0.10  # less than 10%
    assert eval_res["ttest_power"]["large_d_08"] >= 0.80
