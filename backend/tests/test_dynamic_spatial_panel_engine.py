# -*- coding: utf-8 -*-
"""
Unit tests for Dynamic Spatial Panel Econometrics & Spatio-Temporal Diffusion Engine (Dynamic Spatial Panel)
"""

import pytest
import numpy as np
import pandas as pd
from backend.app.engine.dynamic_spatial_panel_engine import run_dynamic_spatial_panel


def test_dynamic_spatial_panel_synthetic_recovery():
    np.random.seed(42)
    regions = [f"Province_{i+1}" for i in range(6)]
    times = [f"Wave_{t+1}" for t in range(4)]
    N = len(regions)
    T = len(times)

    # Synthetic coordinates
    lats = [10.5, 11.2, 12.0, 10.8, 11.5, 12.3]
    lons = [106.5, 107.0, 106.8, 107.5, 108.0, 107.8]

    # Generate spatial weight matrix W
    coords = {regions[i]: (lats[i], lons[i]) for i in range(N)}
    D = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            if i != j:
                D[i, j] = max(0.01, np.sqrt((lats[i] - lats[j])**2 + (lons[i] - lons[j])**2))
    W = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            if i != j:
                W[i, j] = 1.0 / D[i, j]
        W[i, :] /= np.sum(W[i, :])

    # Simulate dynamic spatial autoregressive process
    # Y_t = (I - 0.3*W)^(-1) [0.4*Y_{t-1} + 0.1*W*Y_{t-1} + 0.8*X_t + mu + e_t]
    inv_spatial = np.linalg.inv(np.eye(N) - 0.3 * W)
    mu = np.random.normal(0, 1.0, size=N)
    
    Y_history = [np.random.normal(20, 2, size=N)]
    X_history = [np.random.normal(5, 1, size=N)]

    records = []
    for t in range(T):
        if t == 0:
            Y_curr = Y_history[0]
            X_curr = X_history[0]
        else:
            X_curr = np.random.normal(5, 1, size=N)
            Y_prev = Y_history[t - 1]
            rhs = 0.4 * Y_prev + 0.1 * (W @ Y_prev) + 0.8 * X_curr + mu + np.random.normal(0, 0.4, size=N)
            Y_curr = inv_spatial @ rhs
            Y_history.append(Y_curr)
            X_history.append(X_curr)

        for i in range(N):
            records.append({
                "province": regions[i],
                "wave": times[t],
                "lat": lats[i],
                "lon": lons[i],
                "citizen_trust": Y_curr[i],
                "infrastructure_investment": X_curr[i]
            })

    df = pd.DataFrame(records)

    res = run_dynamic_spatial_panel(
        df=df,
        outcome_col="citizen_trust",
        region_col="province",
        time_col="wave",
        covariate_cols=["infrastructure_investment"],
        lat_col="lat",
        lon_col="lon",
        alpha_level=0.05
    )

    assert res["status"] == "SUCCESS"
    assert res["n_regions"] == 6
    assert res["n_time_periods"] == 4
    assert res["effective_panel_observations"] == 6 * 3

    # Check spatio-temporal parameters
    params = res["spatio_temporal_parameters"]
    assert "time_persistence_gamma" in params
    assert "contemporaneous_spatial_rho" in params
    assert "spatio_temporal_diffusion_eta" in params

    # Check system stability
    assert res["system_stability"]["is_stable"] is True
    assert res["system_stability"]["max_eigen_modulus"] < 1.0

    # Check LeSage-Pace spatial multiplier impacts
    sr = res["short_run_impacts"]
    assert "direct" in sr
    assert "indirect" in sr
    assert "total" in sr
    assert abs(sr["direct"] + sr["indirect"] - sr["total"]) < 1e-3

    lr = res["long_run_impacts"]
    assert "direct" in lr
    assert "indirect" in lr
    assert "total" in lr

    # SVG diagram
    assert "svg_visualization" in res
    assert "<svg" in res["svg_visualization"]


def test_dynamic_spatial_panel_edge_cases():
    # Empty df
    empty_df = pd.DataFrame()
    r1 = run_dynamic_spatial_panel(empty_df, "Y", "R", "T")
    assert r1["status"] == "ERROR"

    # Missing column
    df = pd.DataFrame({"Y": [1, 2], "R": ["A", "B"]})
    r2 = run_dynamic_spatial_panel(df, "Y", "R", "T")
    assert r2["status"] == "ERROR"

    # Insufficient regions (N=2, requires N>=3)
    df_few_r = pd.DataFrame({
        "Y": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "R": ["R1", "R1", "R1", "R2", "R2", "R2"],
        "T": ["T1", "T2", "T3", "T1", "T2", "T3"]
    })
    r3 = run_dynamic_spatial_panel(df_few_r, "Y", "R", "T")
    assert r3["status"] == "INSUFFICIENT_SAMPLE"
