import pytest
import numpy as np
from app.engine.dynamic_factor_model_engine import (
    run_kalman_filter_smoother,
    compute_dynamic_factor_analysis
)


def test_kalman_filter_smoother_direct():
    rng = np.random.RandomState(42)
    T = 15
    P = 3
    K = 1

    # True state AR(1)
    f = np.zeros(T)
    for t in range(1, T):
        f[t] = 0.8 * f[t - 1] + rng.normal(0, 0.5)

    Lambda = np.array([[1.2], [0.9], [1.0]])
    Y = np.zeros((T, P))
    for t in range(T):
        Y[t] = Lambda[:, 0] * f[t] + rng.normal(0, 0.3, size=P)

    A = np.array([[0.8]])
    Q = np.array([[0.25]])
    R = np.diag([0.09, 0.09, 0.09])

    filt_s, filt_cov, smooth_s, smooth_cov = run_kalman_filter_smoother(
        Y=Y, Lambda=Lambda, A=A, Q=Q, R=R
    )

    assert filt_s.shape == (T, 1)
    assert smooth_s.shape == (T, 1)
    # RTS smoothed variances should be lower than or equal to forward-only filtered variances
    for t in range(T - 1):
        assert smooth_cov[t, 0, 0] <= filt_cov[t, 0, 0] + 1e-4


def test_dynamic_factor_analysis_full():
    rng = np.random.RandomState(101)
    waves = [1, 2, 3, 4, 5, 6]
    records = []

    # Common macro state across waves
    macro_trend = [0.2, 0.8, 1.5, 1.2, 0.6, -0.4]

    for w_idx, w in enumerate(waves):
        trend_val = macro_trend[w_idx]
        for _ in range(20):  # 20 respondents per wave
            records.append({
                "wave": w,
                "q_sentiment": float(trend_val + rng.normal(0, 0.3)),
                "q_spending": float(0.8 * trend_val + rng.normal(0, 0.4)),
                "q_trust": float(1.1 * trend_val + rng.normal(0, 0.3)),
                "q_outlook": float(0.7 * trend_val + rng.normal(0, 0.5))
            })

    res = compute_dynamic_factor_analysis(
        records=records,
        indicator_question_ids=["q_sentiment", "q_spending", "q_trust", "q_outlook"],
        time_field="wave"
    )

    assert res["status"] == "success"
    diag = res["sample_diagnostics"]
    assert diag["total_waves_t"] == 6
    assert diag["total_indicators_p"] == 4
    assert diag["total_observations"] == 120
    assert 0.0 <= diag["overall_signal_variance_share"] <= 1.0

    # Trajectory assertions
    traj = res["trajectory"]
    assert len(traj) == 6
    for pt in traj:
        assert "wave_label" in pt
        assert "smoothed_factor" in pt
        assert pt["ci_lower_95"] < pt["smoothed_factor"] < pt["ci_upper_95"]

    # Variance decomposition assertions
    decomp = res["variance_decomposition"]
    assert len(decomp) == 4
    for item in decomp:
        assert 0.0 < item["common_variance_share_r2"] < 1.0
        assert item["common_variance_share_r2"] + item["idiosyncratic_noise_share"] == pytest.approx(1.0, abs=1e-3)

    # Chart & APA Narrative
    assert "<svg" in res["svg_chart"]
    assert "Stock & Watson" in res["apa_narrative"]
    assert "Kalman" in res["apa_narrative"]


def test_dynamic_factor_analysis_errors():
    # Insufficient indicators (< 2)
    res_ind = compute_dynamic_factor_analysis(
        records=[{"wave": 1, "q1": 1.0}],
        indicator_question_ids=["q1"]
    )
    assert res_ind["status"] == "error"

    # Insufficient waves (< 4)
    res_wave = compute_dynamic_factor_analysis(
        records=[
            {"wave": 1, "q1": 1.0, "q2": 2.0},
            {"wave": 2, "q1": 2.0, "q2": 3.0}
        ],
        indicator_question_ids=["q1", "q2"]
    )
    assert res_wave["status"] == "error"
    assert "quá ngắn" in res_wave["message"]
