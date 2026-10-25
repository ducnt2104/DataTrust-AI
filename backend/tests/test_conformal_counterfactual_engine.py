# -*- coding: utf-8 -*-
import pytest
import numpy as np
import pandas as pd
from app.engine.conformal_counterfactual_engine import estimate_conformal_counterfactuals


@pytest.fixture
def synthetic_conformal_data():
    np.random.seed(101)
    n = 120
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.uniform(-1, 1, n)
    
    # Propensity score e(X)
    logits = 0.5 * x1 - 0.3 * x2
    prob = 1.0 / (1.0 + np.exp(-logits))
    w = (np.random.uniform(0, 1, n) < prob).astype(int)
    
    # Potential outcomes: Treatment effect is heterogeneous: tau(X) = 2.0 + 1.5 * x1
    y0 = 10.0 + 2.0 * x1 + 1.0 * x2 + np.random.normal(0, 1.0, n)
    y1 = y0 + 2.0 + 1.5 * x1 + np.random.normal(0, 1.0, n)
    
    y = np.where(w == 1, y1, y0)
    dept = np.random.choice(["IT", "Finance", "HR"], size=n)
    
    df = pd.DataFrame({
        "response_time": y,
        "new_policy": w,
        "seniority": x1,
        "workload": x2,
        "department": dept
    })
    return df


def test_conformal_counterfactual_success(synthetic_conformal_data):
    df = synthetic_conformal_data
    res = estimate_conformal_counterfactuals(
        df=df,
        outcome_col="response_time",
        treatment_col="new_policy",
        covariate_cols=["seniority", "workload"],
        miscoverage_alpha=0.10,
        calibration_ratio=0.50,
        use_propensity_weighting=True,
        subgroup_col="department",
        random_state=42
    )
    
    assert res["status"] == "SUCCESS"
    
    # Summary assertions
    summary = res["overall_summary"]
    assert summary["sample_size"] == 120
    assert summary["treated_count"] > 20
    assert summary["control_count"] > 20
    assert summary["target_coverage_pct"] == 90.0
    assert isinstance(summary["estimated_ate"], float)
    assert len(summary["ate_conformal_interval"]) == 2
    assert summary["ate_conformal_interval"][0] < summary["ate_conformal_interval"][1]
    assert 0.0 <= summary["downside_risk_rate"] <= 1.0
    assert 0.0 <= summary["strictly_beneficial_rate"] <= 1.0
    
    # Diagnostics assertions
    diag = res["calibration_diagnostics"]
    assert 0.0 <= diag["propensity_auc"] <= 1.0
    assert diag["treated_calibration_size"] > 0
    assert diag["control_calibration_size"] > 0
    assert diag["treated_nonconformity_cutoff"] > 0
    assert diag["control_nonconformity_cutoff"] > 0
    assert diag["weighted_conformal_shift_applied"] is True
    
    # Subgroup profiles
    profiles = res["subgroup_risk_profiles"]
    assert len(profiles) == 3  # IT, Finance, HR
    for p in profiles:
        assert "group_name" in p
        assert p["sample_size"] > 0
        assert p["recommendation_code"] in ["ROLLOUT", "CONTRAINDICATED", "SAFEGUARDS", "MONITOR"]
        
    # Individual sample
    indiv = res["individual_predictions_sample"]
    assert len(indiv) > 0
    first = indiv[0]
    assert "unit_id" in first
    assert len(first["ite_conformal_interval"]) == 2
    assert first["ite_conformal_interval"][0] <= first["ite_conformal_interval"][1]
    
    # Narrative
    assert "Conformal Counterfactual Risk Inference" in res["apa_narrative"]
    assert "Chernozhukov" in res["apa_narrative"]


def test_conformal_counterfactual_unweighted(synthetic_conformal_data):
    df = synthetic_conformal_data
    res = estimate_conformal_counterfactuals(
        df=df,
        outcome_col="response_time",
        treatment_col="new_policy",
        covariate_cols=["seniority", "workload"],
        miscoverage_alpha=0.05,
        use_propensity_weighting=False,
        random_state=42
    )
    assert res["status"] == "SUCCESS"
    assert res["overall_summary"]["target_coverage_pct"] == 95.0
    assert res["calibration_diagnostics"]["weighted_conformal_shift_applied"] is False


def test_conformal_counterfactual_validation_errors(synthetic_conformal_data):
    df = synthetic_conformal_data
    
    # Missing column
    with pytest.raises(ValueError, match="Required column 'non_existent' not found"):
        estimate_conformal_counterfactuals(
            df=df,
            outcome_col="non_existent",
            treatment_col="new_policy",
            covariate_cols=["seniority"]
        )
        
    # Invalid alpha
    with pytest.raises(ValueError, match="miscoverage_alpha must be in"):
        estimate_conformal_counterfactuals(
            df=df,
            outcome_col="response_time",
            treatment_col="new_policy",
            covariate_cols=["seniority"],
            miscoverage_alpha=0.60
        )
        
    # Sample too small
    df_tiny = df.head(15)
    with pytest.raises(ValueError, match="Sample size too small"):
        estimate_conformal_counterfactuals(
            df=df_tiny,
            outcome_col="response_time",
            treatment_col="new_policy",
            covariate_cols=["seniority"]
        )
