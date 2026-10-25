# -*- coding: utf-8 -*-
import pytest
import numpy as np
import pandas as pd
from app.engine.shift_share_iv_engine import estimate_shift_share_iv


@pytest.fixture
def synthetic_shift_share_data():
    np.random.seed(66)
    n = 100
    K = 4
    
    # 4 portfolio shares z_ik summing to ~1
    raw_shares = np.random.dirichlet(np.ones(K) * 2, size=n)
    
    # National shocks g_k
    g_shocks = np.array([2.5, -1.0, 4.0, 0.5])
    
    # Bartik instrument: Z_i = sum_k z_ik * g_k
    bartik_z = raw_shares @ g_shocks
    
    # Baseline control x
    x = np.random.normal(10, 2, n)
    
    # Endogenous treatment D_i: correlated with Bartik Z + confounding
    d = 1.8 * bartik_z + 0.5 * (x - 10) + np.random.normal(0, 0.8, n)
    
    # Outcome Y: true causal effect beta = 1.5
    y = 20.0 + 1.5 * d + 1.2 * (x - 10) + np.random.normal(0, 1.0, n)
    
    df = pd.DataFrame({
        "outcome": y,
        "treatment": d,
        "share_mfg": raw_shares[:, 0],
        "share_tech": raw_shares[:, 1],
        "share_svc": raw_shares[:, 2],
        "share_agr": raw_shares[:, 3],
        "control_exp": x
    })
    return df, g_shocks


def test_shift_share_iv_success(synthetic_shift_share_data):
    df, g_shocks = synthetic_shift_share_data
    res = estimate_shift_share_iv(
        df=df,
        outcome_col="outcome",
        treatment_col="treatment",
        share_cols=["share_mfg", "share_tech", "share_svc", "share_agr"],
        shocks=list(g_shocks),
        covariate_cols=["control_exp"],
        alpha_level=0.05
    )
    
    assert res["status"] == "SUCCESS"
    
    # Summary assertions
    summary = res["overall_summary"]
    assert summary["sample_size"] == 100
    assert summary["n_shares_k"] == 4
    assert summary["first_stage_f_statistic"] > 10.0
    assert summary["is_weak_instrument"] is False
    assert abs(summary["beta_2sls"] - 1.5) < 0.6
    assert summary["se_conventional"] > 0
    assert summary["se_akm_robust"] > 0
    assert len(summary["confidence_interval_95"]) == 2
    assert summary["confidence_interval_95"][0] < summary["confidence_interval_95"][1]
    
    # Rotemberg decomposition assertions
    rot_items = res["rotemberg_decomposition"]
    assert len(rot_items) == 4
    
    # GPSS mathematical equivalence: sum of Rotemberg weights = 1.0
    total_alpha = sum(item["rotemberg_weight"] for item in rot_items)
    assert abs(total_alpha - 1.0) < 1e-3
    
    # GPSS equivalence: sum(alpha_k * beta_k) = beta_2sls
    weighted_beta = sum(item["rotemberg_weight"] * item["just_identified_beta"] for item in rot_items)
    assert abs(weighted_beta - summary["beta_2sls"]) < 1e-3
    
    # Overidentification and HHI
    assert summary["rotemberg_hhi"] > 0
    assert "overid_sargan_stat" in summary
    assert "overid_p_value" in summary
    
    # SVG and Narrative
    assert "<svg" in res["svg_visualization"]
    assert "Shift-Share" in res["apa_narrative"]
    assert "Rotemberg" in res["apa_narrative"]
    assert "Goldsmith-Pinkham" in res["apa_narrative"]


def test_shift_share_default_shocks(synthetic_shift_share_data):
    df, _ = synthetic_shift_share_data
    res = estimate_shift_share_iv(
        df=df,
        outcome_col="outcome",
        treatment_col="treatment",
        share_cols=["share_mfg", "share_tech", "share_svc", "share_agr"],
        shocks=None
    )
    assert res["status"] == "SUCCESS"
    assert res["overall_summary"]["n_shares_k"] == 4


def test_shift_share_validation_errors(synthetic_shift_share_data):
    df, _ = synthetic_shift_share_data
    
    # Fewer than 2 shares
    with pytest.raises(ValueError, match="requires at least 2 share categories"):
        estimate_shift_share_iv(
            df=df,
            outcome_col="outcome",
            treatment_col="treatment",
            share_cols=["share_mfg"]
        )
        
    # Mismatched shocks vector
    with pytest.raises(ValueError, match="Length of shocks vector"):
        estimate_shift_share_iv(
            df=df,
            outcome_col="outcome",
            treatment_col="treatment",
            share_cols=["share_mfg", "share_tech"],
            shocks=[1.0, 2.0, 3.0]
        )
