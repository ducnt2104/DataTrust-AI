# -*- coding: utf-8 -*-
"""
Unit tests for Local Instrumental Variables & Marginal Treatment Effects Engine
(Heckman & Vytlacil 2005 Econometrica; Mogstad et al. 2018).
"""

import pytest
import numpy as np
import pandas as pd
from app.engine.local_instrumental_variables_engine import estimate_local_instrumental_variables


def test_liv_mte_essential_heterogeneity_sorting():
    np.random.seed(42)
    N = 350
    # Instrumental variable Z (e.g., proximity / voucher / randomized subsidy)
    Z = np.random.normal(0, 1.5, N)
    X = np.random.normal(0, 1.0, N)

    # Choice model: D = 1{ P(Z, X) >= U_D }
    # Propensity: P = 1 / (1 + exp(-(0.8 * Z + 0.3 * X)))
    p_true = 1.0 / (1.0 + np.exp(-(0.8 * Z + 0.3 * X)))
    u_d = np.random.uniform(0, 1, N)
    D = (p_true >= u_d).astype(float)

    # Roy Model with Essential Heterogeneity:
    # MTE(u) = 8.0 - 6.0 * u  (Positive selection on gains: low u_d has higher return)
    # Y = Y0 + D * MTE(u_d)
    Y0 = 20.0 + 1.5 * X + np.random.normal(0, 1.0, N)
    treatment_effect = 8.0 - 6.0 * u_d
    Y = Y0 + D * treatment_effect

    df = pd.DataFrame({
        "wage": Y,
        "college": D,
        "college_distance_iv": Z,
        "ability_covariate": X
    })

    res = estimate_local_instrumental_variables(
        df=df,
        outcome_col="wage",
        treatment_col="college",
        instrument_cols=["college_distance_iv"],
        covariate_cols=["ability_covariate"],
        n_grid_points=40,
        trim_quantile=0.05
    )

    assert res["status"] == "SUCCESS"
    summ = res["overall_summary"]
    assert summ["sample_size"] == N
    assert len(res["mte_curve"]) == 40
    
    # In positive selection on gains, ATT > ATE > ATU
    assert summ["att"]["estimate"] > summ["ate"]["estimate"]
    assert summ["sorting_on_gains_att_minus_ate"] > 0
    assert summ["att"]["se"] > 0
    assert summ["ate"]["se"] > 0
    assert "<svg" in res["svg_visualization"]
    assert "Marginal Treatment Effects" in res["apa_narrative"]


def test_liv_mte_homogeneous_benchmark():
    np.random.seed(123)
    N = 250
    Z = np.random.normal(0, 1.0, N)
    p_true = 1.0 / (1.0 + np.exp(-Z))
    u_d = np.random.uniform(0, 1, N)
    D = (p_true >= u_d).astype(float)

    # Constant treatment effect = 5.0
    Y0 = 10.0 + np.random.normal(0, 0.5, N)
    Y = Y0 + 5.0 * D

    df = pd.DataFrame({"y": Y, "d": D, "z": Z})

    res = estimate_local_instrumental_variables(
        df=df,
        outcome_col="y",
        treatment_col="d",
        instrument_cols=["z"]
    )

    assert res["status"] == "SUCCESS"
    summ = res["overall_summary"]
    # All treatment parameters should be close to 5.0
    assert abs(summ["ate"]["estimate"] - 5.0) < 1.0
    assert abs(summ["att"]["estimate"] - 5.0) < 1.0
    assert abs(summ["late"]["estimate"] - 5.0) < 1.0


def test_liv_mte_validation_errors():
    df_small = pd.DataFrame({"y": [1.0] * 10, "d": [0.0] * 10, "z": [1.0] * 10})
    with pytest.raises(ValueError, match="too small"):
        estimate_local_instrumental_variables(df_small, "y", "d", ["z"])

    df_non_binary = pd.DataFrame({"y": np.random.randn(40), "d": np.random.randint(0, 4, 40), "z": np.random.randn(40)})
    with pytest.raises(ValueError, match="must be binary"):
        estimate_local_instrumental_variables(df_non_binary, "y", "d", ["z"])
