# -*- coding: utf-8 -*-
"""
Unit tests for Nested Logit Structural Choice Engine (McFadden 1978 Nobel Prize).
"""

import pytest
import numpy as np
import pandas as pd
from app.engine.nested_logit_engine import estimate_nested_logit


def test_nested_logit_red_bus_blue_bus_dgp():
    # Classic McFadden Red Bus / Blue Bus setup:
    # Nests: 'Private' (Car), 'Public' (Red Bus, Blue Bus)
    np.random.seed(42)
    N_commuters = 60
    alternatives = ["Car", "Red_Bus", "Blue_Bus"]
    nest_map = {"Car": "Private", "Red_Bus": "Public", "Blue_Bus": "Public"}

    records = []
    # Shared public transit shock eps_public ~ N(0, 1.5)
    for i in range(N_commuters):
        cid = f"commuter_{i}"
        eps_public = np.random.normal(0, 1.5)
        
        # Utilities
        v_dict = {}
        for alt in alternatives:
            cost = 15.0 if alt == "Car" else 5.0
            time = 25.0 if alt == "Car" else 45.0
            
            # Utility function: V = -0.15 * cost - 0.05 * time
            v_det = -0.15 * cost - 0.05 * time
            
            # Error term: correlated for public transit
            if nest_map[alt] == "Public":
                eps = eps_public + np.random.normal(0, 0.4)
            else:
                eps = np.random.normal(0, 1.0)
                
            u_total = v_det + eps
            v_dict[alt] = (cost, time, u_total)

        # Decision maker chooses max utility
        chosen_alt = max(v_dict.keys(), key=lambda k: v_dict[k][2])

        for alt in alternatives:
            cost, time, _ = v_dict[alt]
            records.append({
                "commuter_id": cid,
                "mode": alt,
                "nest": nest_map[alt],
                "cost": cost,
                "time": time,
                "chosen": 1.0 if alt == chosen_alt else 0.0
            })

    df = pd.DataFrame(records)

    res = estimate_nested_logit(
        df=df,
        choice_col="chosen",
        alternative_col="mode",
        nest_col="nest",
        id_col="commuter_id",
        attribute_cols=["time"],
        cost_col="cost"
    )

    assert res["status"] == "SUCCESS"
    summary = res["overall_summary"]
    assert summary["n_choice_situations"] == N_commuters
    assert summary["n_alternatives"] == 3
    assert summary["n_nests"] == 2
    assert summary["log_likelihood_nested_logit"] > summary["log_likelihood_null"]
    
    # Verify nest diagnostics
    assert len(res["nests"]) == 2
    public_nest = [n for n in res["nests"] if n["nest_name"] == "Public"][0]
    # Strong correlation within public transit produces lambda < 1.0
    assert public_nest["dissimilarity_lambda"] < 0.95
    assert public_nest["intra_nest_correlation_rho"] > 0.05
    assert res["elasticity_comparison"] is not None
    assert "<svg" in res["svg_visualization"]
    assert "Nested Logit" in res["apa_narrative"]


def test_nested_logit_edge_cases():
    df_small = pd.DataFrame({
        "cid": ["1", "1"],
        "mode": ["A", "B"],
        "nest": ["N1", "N2"],
        "chosen": [1, 0],
        "cost": [10, 20]
    })
    # Fewer than 3 alternatives
    with pytest.raises(ValueError, match="at least 3 distinct alternatives"):
        estimate_nested_logit(
            df=df_small,
            choice_col="chosen",
            alternative_col="mode",
            nest_col="nest",
            id_col="cid",
            attribute_cols=["cost"]
        )
