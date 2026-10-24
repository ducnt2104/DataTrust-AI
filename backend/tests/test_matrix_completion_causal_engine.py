# -*- coding: utf-8 -*-
"""
Unit tests for Matrix Completion for Causal Panel Data Engine
Athey, Bayati, Doudchenko, Imbens, & Khosravi (2021)
"""
import pytest
import numpy as np
from app.engine.matrix_completion_causal_engine import MatrixCompletionCausalEngine


def test_matrix_completion_synthetic_panel():
    np.random.seed(42)
    # N = 12 units, T = 6 time periods -> 72 cells
    # Rank-1 baseline: L = u * v^T
    N = 12
    T = 6
    u_factors = np.linspace(2.0, 5.0, N)
    v_factors = np.linspace(1.0, 3.0, T)
    L_true = np.outer(u_factors, v_factors)

    # Treatment assignment: units 8..11 treated at times 4..5
    W_true = np.zeros((N, T), dtype=int)
    W_true[8:, 4:] = 1  # 4 units x 2 periods = 8 treated cells

    # Realized outcome: Y = L_true + tau * W + noise
    tau_true = 3.5
    noise = np.random.normal(0, 0.1, (N, T))
    Y_realized = L_true + tau_true * W_true + noise

    # Flatten
    y_flat = []
    u_idx = []
    t_idx = []
    w_flat = []

    for i in range(N):
        for j in range(T):
            y_flat.append(Y_realized[i, j])
            u_idx.append(f"unit_{i}")
            t_idx.append(float(j + 1))
            w_flat.append(float(W_true[i, j]))

    res = MatrixCompletionCausalEngine.evaluate_matrix_completion(
        y_matrix_flat=np.array(y_flat, dtype=float),
        unit_indices=np.array(u_idx),
        time_indices=np.array(t_idx, dtype=float),
        treatment_indicator=np.array(w_flat, dtype=float),
        max_rank=1,
        lambda_penalty=0.1,
        outcome_label="Enterprise Revenue Growth",
        unit_label="Enterprise",
        time_label="Quarter"
    )

    assert res["status"] == "SUCCESS"
    diag = res["diagnostics"]
    assert diag["n_units"] == 12
    assert diag["n_time_periods"] == 6
    assert diag["n_treated_cells"] == 8
    assert diag["n_control_cells"] == 64
    assert diag["is_converged"] is True

    # Check recovered ATT is close to true effect tau = 3.5
    assert abs(diag["overall_att"] - 3.5) < 0.6
    assert diag["is_statistically_significant"] is True
    assert diag["p_value"] < 0.05

    # Check rank compression
    assert diag["effective_rank"] <= 3

    # Check cell effects
    cells = res["cell_treatment_effects"]
    assert len(cells) == 8
    for c in cells:
        assert abs(c["treatment_effect_tau"] - 3.5) < 0.8

    # Check singular value spectrum and SVG
    assert len(res["singular_value_spectrum"]) > 0
    assert "<svg" in res["svg_visualization"]
    assert "Athey, Bayati, Doudchenko, Imbens, & Khosravi, 2021" in res["apa_narrative"]


def test_matrix_completion_insufficient_sample():
    res = MatrixCompletionCausalEngine.evaluate_matrix_completion(
        y_matrix_flat=np.array([1.0, 2.0]),
        unit_indices=np.array(["u1", "u2"]),
        time_indices=np.array([1.0, 2.0]),
        treatment_indicator=np.array([1.0, 0.0])
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_matrix_completion_no_treated_cells():
    y = np.ones(25)
    u = np.array([f"u_{i % 5}" for i in range(25)])
    t = np.array([float(i // 5) for i in range(25)])
    w = np.zeros(25)
    res = MatrixCompletionCausalEngine.evaluate_matrix_completion(y, u, t, w)
    assert res["status"] == "NO_TREATED_CELLS"
