import numpy as np
import pytest
from app.engine.msm_iptw_engine import MSMIPTWEngine


def test_msm_iptw_longitudinal_estimation():
    np.random.seed(42)
    N = 80
    T = 3

    # Generate multi-wave data with time-varying confounding
    # L_t: health/satisfaction status, A_t: policy/treatment intervention
    treatments = np.zeros((N, T), dtype=int)
    confounders = np.zeros((N, T), dtype=float)

    # Wave 1
    L1 = np.random.normal(0, 1, N)
    p1 = 1.0 / (1.0 + np.exp(-(-0.2 + 0.8 * L1)))
    A1 = (np.random.uniform(0, 1, N) < p1).astype(int)
    confounders[:, 0] = L1
    treatments[:, 0] = A1

    # Wave 2: L2 influenced by A1 and L1; A2 influenced by A1 and L2
    L2 = 0.5 * L1 + 0.6 * A1 + np.random.normal(0, 0.5, N)
    p2 = 1.0 / (1.0 + np.exp(-(0.4 * A1 + 0.7 * L2)))
    A2 = (np.random.uniform(0, 1, N) < p2).astype(int)
    confounders[:, 1] = L2
    treatments[:, 1] = A2

    # Wave 3: L3 influenced by A2 and L2; A3 influenced by A2 and L3
    L3 = 0.5 * L2 + 0.6 * A2 + np.random.normal(0, 0.5, N)
    p3 = 1.0 / (1.0 + np.exp(-(0.4 * A2 + 0.7 * L3)))
    A3 = (np.random.uniform(0, 1, N) < p3).astype(int)
    confounders[:, 2] = L3
    treatments[:, 2] = A3

    # Final Outcome Y: True causal effect of cumulative treatment is +2.0 per wave
    cum_a = np.sum(treatments, axis=1)
    Y = 10.0 + 2.0 * cum_a + 1.2 * L3 + np.random.normal(0, 0.8, N)

    res = MSMIPTWEngine.estimate(
        treatments=treatments,
        confounders=confounders,
        outcomes=Y,
        wave_labels=["Wave 1", "Wave 2", "Wave 3"]
    )

    assert res["status"] == "success"
    assert res["sample_size"] == N
    assert res["waves_count"] == 3
    # Causal effect per wave should be positive and close to ~2.0
    assert 1.0 <= res["causal_effect_per_wave"] <= 3.5
    assert res["p_value"] < 0.05
    assert res["ci_95_lower"] < res["ci_95_upper"]
    
    # Weight diagnostics
    sw_diag = res["stabilized_weights_diagnostics"]
    assert 0.7 <= sw_diag["mean"] <= 1.3
    assert sw_diag["min"] > 0
    assert sw_diag["max"] < 100.0

    # Naive OLS and bias verdict
    assert "naive_ols_effect" in res
    assert "confounding_bias_pct" in res
    assert "<svg" in res["svg_chart"]
    assert "Marginal Structural Model" in res["apa_narrative"]


def test_msm_iptw_insufficient_sample():
    # Only 10 individuals (N < 25)
    A = np.ones((10, 2))
    L = np.ones((10, 2))
    Y = np.ones(10)
    res = MSMIPTWEngine.estimate(A, L, Y)
    assert res["status"] == "insufficient_data"
    assert "25 cá nhân" in res["message"]

    # Only 1 wave (T < 2)
    A_t1 = np.ones((30, 1))
    L_t1 = np.ones((30, 1))
    Y_30 = np.ones(30)
    res2 = MSMIPTWEngine.estimate(A_t1, L_t1, Y_30)
    assert res2["status"] == "insufficient_data"
    assert "2 làn sóng" in res2["message"]
