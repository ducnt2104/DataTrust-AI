# -*- coding: utf-8 -*-
import pytest
import numpy as np
import pandas as pd
from app.engine.causal_sensitivity_bias_engine import estimate_causal_sensitivity_bias


@pytest.fixture
def synthetic_sensitivity_data():
    np.random.seed(42)
    n = 100
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(2, 0.5, n)
    x3 = np.random.uniform(10, 20, n)
    
    # Treatment D influenced by x1, x2
    d = 0.8 * x1 + 0.4 * x2 + np.random.normal(0, 0.5, n)
    
    # Outcome Y: causal effect tau = 2.5
    y = 5.0 + 2.5 * d + 1.2 * x1 + 0.9 * x2 - 0.3 * x3 + np.random.normal(0, 0.8, n)
    
    return pd.DataFrame({
        "outcome": y,
        "treatment": d,
        "cov_x1": x1,
        "cov_x2": x2,
        "cov_x3": x3
    })


def test_causal_sensitivity_bias_success(synthetic_sensitivity_data):
    df = synthetic_sensitivity_data
    res = estimate_causal_sensitivity_bias(
        df=df,
        outcome_col="outcome",
        treatment_col="treatment",
        covariate_cols=["cov_x1", "cov_x2", "cov_x3"],
        q_reduction=1.0,
        alpha_level=0.05,
        benchmark_multipliers=[1.0, 2.0, 3.0]
    )
    
    assert res["status"] == "SUCCESS"
    
    # Summary assertions
    summary = res["overall_summary"]
    assert summary["sample_size"] == 100
    assert summary["residual_df"] == 100 - 5  # intercept, d, 3 covs
    assert abs(summary["baseline_estimate"] - 2.5) < 1.0
    assert summary["baseline_se"] > 0
    assert summary["baseline_t"] > 2.0
    assert summary["baseline_p_value"] < 0.05
    assert len(summary["baseline_ci"]) == 2
    assert summary["baseline_ci"][0] < summary["baseline_ci"][1]
    
    # Robustness Values
    assert 0.0 < summary["robustness_value_q"] < 1.0
    assert 0.0 < summary["robustness_value_alpha"] <= summary["robustness_value_q"]
    assert summary["partial_r2_treatment"] > 0
    
    # Benchmarks
    benchmarks = res["covariate_benchmarks"]
    assert len(benchmarks) == 3
    for b in benchmarks:
        assert "covariate" in b
        assert 0.0 <= b["r2_d_given_x"] <= 1.0
        assert 0.0 <= b["r2_y_given_dx"] <= 1.0
        
    # Scenarios
    scenarios = res["benchmark_scenarios"]
    assert len(scenarios) > 0
    for sc in scenarios:
        assert "adjusted_estimate" in sc
        assert "adjusted_se" in sc
        assert "adjusted_t" in sc
        assert "remains_significant" in sc
        assert "is_overturned" in sc
        
    # SVG and Narrative
    assert "<svg" in res["svg_visualization"]
    assert "Cinelli & Hazlett" in res["apa_narrative"]
    assert "Robustness Value" in res["apa_narrative"]


def test_causal_sensitivity_bias_no_covariates(synthetic_sensitivity_data):
    df = synthetic_sensitivity_data
    res = estimate_causal_sensitivity_bias(
        df=df,
        outcome_col="outcome",
        treatment_col="treatment",
        covariate_cols=[]
    )
    assert res["status"] == "SUCCESS"
    assert res["overall_summary"]["residual_df"] == 100 - 2
    assert len(res["covariate_benchmarks"]) == 0
    assert len(res["benchmark_scenarios"]) == 0


def test_causal_sensitivity_bias_errors(synthetic_sensitivity_data):
    df = synthetic_sensitivity_data
    
    # Missing column
    with pytest.raises(ValueError, match="Required column 'missing' not found"):
        estimate_causal_sensitivity_bias(
            df=df,
            outcome_col="missing",
            treatment_col="treatment"
        )
        
    # Tiny sample size
    df_tiny = df.head(10)
    with pytest.raises(ValueError, match="Sample size too small"):
        estimate_causal_sensitivity_bias(
            df=df_tiny,
            outcome_col="outcome",
            treatment_col="treatment"
        )
