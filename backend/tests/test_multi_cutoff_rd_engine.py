# -*- coding: utf-8 -*-
"""
Unit tests for Multi-Cutoff Regression Discontinuity & Boundary Treatment Effects Engine
(Cattaneo et al. 2015 JASA; Bertanha 2020 JASA).
"""

import pytest
import numpy as np
import pandas as pd
from app.engine.multi_cutoff_rd_engine import (
    estimate_multi_cutoff_rd,
    _local_linear_rd
)


def test_local_linear_rd_isolated():
    np.random.seed(42)
    N = 200
    x = np.random.uniform(-5, 5, N)
    true_tau = 6.0
    # Y = 10 + 2*X + tau * (X >= 0) + noise
    y = 10.0 + 2.0 * x + true_tau * (x >= 0).astype(float) + np.random.normal(0, 0.5, N)

    tau, se, eff_n = _local_linear_rd(x, y, bandwidth=3.0)
    assert abs(tau - true_tau) < 0.8
    assert se > 0
    assert eff_n > 50


def test_estimate_multi_cutoff_rd_pipeline():
    np.random.seed(123)
    # 3 distinct regional cutoffs: North (40), Central (55), South (70)
    cutoffs = {"North": 40.0, "Central": 55.0, "South": 70.0}
    records = []

    for region, c in cutoffs.items():
        for _ in range(80):
            # Running variable centered around regional cutoff
            running = np.random.normal(c, 8.0)
            is_treated = float(running >= c)
            # True treatment effect = 5.0
            outcome = 100.0 + 1.2 * (running - c) + 5.0 * is_treated + np.random.normal(0, 1.5)
            records.append({
                "satisfaction_outcome": outcome,
                "credit_score_running": running,
                "region_group": region
            })

    df = pd.DataFrame(records)

    res = estimate_multi_cutoff_rd(
        df=df,
        outcome_col="satisfaction_outcome",
        running_col="credit_score_running",
        group_col="region_group",
        fixed_cutoffs=cutoffs,
        bandwidth=6.0
    )

    assert res["status"] == "SUCCESS"
    summ = res["overall_summary"]
    assert summ["sample_size"] == 240
    assert summ["n_distinct_cutoffs"] == 3
    # Pooled treatment effect should be near 5.0
    assert abs(summ["tau_pooled"] - 5.0) < 1.0
    assert summ["se_pooled"] > 0
    assert summ["p_value_pooled"] < 0.05
    assert len(res["cutoff_summaries"]) == 3
    assert "<svg" in res["svg_visualization"]
    assert "Multi-Cutoff Regression Discontinuity" in res["apa_narrative"]


def test_multi_cutoff_validation_errors():
    df_small = pd.DataFrame({"y": [1.0] * 10, "x": [0.0] * 10})
    with pytest.raises(ValueError, match="too small"):
        estimate_multi_cutoff_rd(df_small, "y", "x")

    df_large = pd.DataFrame({"y": np.random.randn(35), "x": np.random.randn(35)})
    with pytest.raises(ValueError, match="not found"):
        estimate_multi_cutoff_rd(df_large, "y", "x", cutoff_col="nonexistent")
