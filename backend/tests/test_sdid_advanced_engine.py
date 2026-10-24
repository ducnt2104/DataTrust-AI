# -*- coding: utf-8 -*-
"""
Unit tests for Synthetic Difference-in-Differences (SDID) Advanced Engine
Arkhangelsky, Athey, Hirshberg, Imbens, & Wager (2021)
"""
import pytest
import numpy as np
from app.engine.sdid_advanced_engine import SDIDAdvancedEngine


def test_sdid_advanced_synthetic_panel():
    np.random.seed(42)
    # 8 control units, 2 treated units across 6 time periods (T_pre = 4, T_post = 2)
    N = 10
    T = 6
    # Base control trends
    time_trend = np.array([2.0, 3.5, 5.0, 6.2, 7.8, 9.0])
    Y_panel = np.zeros((N, T))
    W_panel = np.zeros((N, T), dtype=int)

    for i in range(8):
        # Control units
        unit_shift = 10.0 + i * 2.0
        Y_panel[i, :] = unit_shift + time_trend + np.random.normal(0, 0.2, T)

    # Treated units 8 and 9 (shift by +15.0 and true treatment effect +4.0 in post periods 4, 5)
    for i in [8, 9]:
        unit_shift = 30.0 + (i - 8) * 3.0
        # In pre-periods, follows same trend
        Y_panel[i, :4] = unit_shift + time_trend[:4] + np.random.normal(0, 0.2, 4)
        # In post-periods, adds tau = 4.0
        Y_panel[i, 4:] = unit_shift + time_trend[4:] + 4.0 + np.random.normal(0, 0.2, 2)
        W_panel[i, 4:] = 1

    # Flatten
    y_flat = []
    u_idx = []
    t_idx = []
    w_flat = []
    for i in range(N):
        for j in range(T):
            y_flat.append(Y_panel[i, j])
            u_idx.append(f"entity_{i}")
            t_idx.append(float(j + 1))
            w_flat.append(float(W_panel[i, j]))

    res = SDIDAdvancedEngine.evaluate_sdid(
        y_matrix_flat=np.array(y_flat, dtype=float),
        unit_indices=np.array(u_idx),
        time_indices=np.array(t_idx, dtype=float),
        treatment_indicator=np.array(w_flat, dtype=float),
        outcome_label="Log Output Index",
        unit_label="Production Plant",
        time_label="Half-Year"
    )

    assert res["status"] == "SUCCESS"
    diag = res["diagnostics"]
    assert diag["n_units"] == 10
    assert diag["n_treated_units"] == 2
    assert diag["n_control_units"] == 8
    assert diag["n_time_periods"] == 6
    assert diag["n_pre_periods"] == 4
    assert diag["n_post_periods"] == 2

    # Check that tau_sdid is close to 4.0
    assert abs(diag["tau_sdid"] - 4.0) < 0.6
    assert diag["p_value"] < 0.05
    assert diag["is_statistically_significant"] is True

    # Unit weights and time weights
    assert len(res["unit_weights"]) == 8
    total_w = sum(w["weight"] for w in res["unit_weights"])
    assert abs(total_w - 1.0) < 0.01

    assert len(res["time_weights"]) == 4
    total_lam = sum(l["weight"] for l in res["time_weights"])
    assert abs(total_lam - 1.0) < 0.01

    # Trajectories
    trajs = res["trajectories"]
    assert len(trajs) == 6
    assert "<svg" in res["svg_visualization"]
    assert "Arkhangelsky, Athey, Hirshberg, Imbens, & Wager, 2021" in res["apa_narrative"]


def test_sdid_advanced_insufficient_sample():
    res = SDIDAdvancedEngine.evaluate_sdid(
        y_matrix_flat=np.array([1.0, 2.0]),
        unit_indices=np.array(["u1", "u2"]),
        time_indices=np.array([1.0, 2.0]),
        treatment_indicator=np.array([1.0, 0.0])
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_sdid_advanced_no_treated_units():
    y = np.ones(30)
    u = np.array([f"u_{i % 5}" for i in range(30)])
    t = np.array([float(i // 5) for i in range(30)])
    w = np.zeros(30)
    res = SDIDAdvancedEngine.evaluate_sdid(y, u, t, w)
    assert res["status"] == "NO_TREATED_UNITS"
