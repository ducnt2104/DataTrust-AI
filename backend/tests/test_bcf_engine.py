# -*- coding: utf-8 -*-
import pytest
import numpy as np
import pandas as pd
from app.engine.bcf_engine import estimate_bayesian_causal_forest


@pytest.fixture
def synthetic_bcf_data():
    np.random.seed(88)
    n = 120
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.uniform(-2, 2, n)
    x3 = np.random.normal(5, 1.5, n)
    
    # Propensity score correlated with x1, x2 (Confounding)
    logits = 0.6 * x1 - 0.4 * x2
    p = 1.0 / (1.0 + np.exp(-logits))
    w = (np.random.uniform(0, 1, n) < p).astype(int)
    
    # True heterogeneous effect: tau(X) = 2.0 + 1.2 * x1
    tau_true = 2.0 + 1.2 * x1
    
    # Prognostic outcome mu(X) has strong non-linear relation
    mu_true = 10.0 + 3.0 * x1 + 2.0 * x2 - 1.0 * x3
    y = mu_true + w * tau_true + np.random.normal(0, 0.8, n)
    
    return pd.DataFrame({
        "outcome": y,
        "treatment": w,
        "feat_x1": x1,
        "feat_x2": x2,
        "feat_x3": x3
    })


def test_bcf_success(synthetic_bcf_data):
    df = synthetic_bcf_data
    res = estimate_bayesian_causal_forest(
        df=df,
        outcome_col="outcome",
        treatment_col="treatment",
        covariate_cols=["feat_x1", "feat_x2", "feat_x3"],
        n_posterior_draws=300,
        random_state=42
    )
    
    assert res["status"] == "SUCCESS"
    
    # Summary
    summary = res["overall_summary"]
    assert summary["sample_size"] == 120
    assert summary["treated_count"] > 15
    assert summary["control_count"] > 15
    assert summary["posterior_draws_count"] == 300
    assert summary["posterior_ate_mean"] > 0
    assert summary["posterior_ate_se"] > 0
    assert len(summary["posterior_ate_ci_95"]) == 2
    assert summary["posterior_ate_ci_95"][0] < summary["posterior_ate_ci_95"][1]
    assert 0.0 <= summary["posterior_prob_positive_ate"] <= 1.0
    assert summary["treatment_heterogeneity_sd"] > 0
    assert summary["ric_correction_active"] is True
    
    # Variance decomposition
    v_decomp = summary["variance_decomposition"]
    assert "prognostic_baseline_pct" in v_decomp
    assert "treatment_effect_pct" in v_decomp
    assert "residual_noise_pct" in v_decomp
    total_pct = v_decomp["prognostic_baseline_pct"] + v_decomp["treatment_effect_pct"] + v_decomp["residual_noise_pct"]
    assert abs(total_pct - 100.0) < 1.0
    
    # Subgroups
    subgroups = res["subgroups"]
    assert len(subgroups) > 0
    for sg in subgroups:
        assert "segment_name" in sg
        assert "cate_mean" in sg
        assert len(sg["credible_interval_95"]) == 2
        assert sg["targeting_tier"] in ["HIGH_PRIORITY", "TARGETED", "CONTRAINDICATED"]
        
    # Individual sample
    indiv = res["individual_sample"]
    assert len(indiv) > 0
    assert "propensity_pi" in indiv[0]
    assert "cate_mean" in indiv[0]
    assert len(indiv[0]["cate_ci_95"]) == 2
    
    # SVG & Narrative
    assert "<svg" in res["svg_visualization"]
    assert "Bayesian Causal Forest" in res["apa_narrative"]
    assert "Hahn" in res["apa_narrative"]


def test_bcf_validation_errors(synthetic_bcf_data):
    df = synthetic_bcf_data
    
    # Missing covariate
    with pytest.raises(ValueError, match="BCF requires at least one covariate"):
        estimate_bayesian_causal_forest(
            df=df,
            outcome_col="outcome",
            treatment_col="treatment",
            covariate_cols=[]
        )
        
    # Non-existent column
    with pytest.raises(ValueError, match="Required column 'bad_col' not found"):
        estimate_bayesian_causal_forest(
            df=df,
            outcome_col="outcome",
            treatment_col="bad_col",
            covariate_cols=["feat_x1"]
        )
        
    # Sample too small
    df_tiny = df.head(15)
    with pytest.raises(ValueError, match="Sample size too small"):
        estimate_bayesian_causal_forest(
            df=df_tiny,
            outcome_col="outcome",
            treatment_col="treatment",
            covariate_cols=["feat_x1"]
        )
