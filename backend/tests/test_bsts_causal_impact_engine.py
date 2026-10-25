"""
Unit tests for Bayesian Structural Time Series (BSTS) & Causal Impact Engine.
"""

import pytest
import numpy as np
from app.engine.bsts_causal_impact_engine import (
    estimate_bsts_causal_impact,
    KalmanFilterLocalLevel
)


def test_kalman_filter_local_level_convergence():
    kf = KalmanFilterLocalLevel(sigma_eps=0.5, sigma_level=0.2, sigma_slope=0.05)
    # Generate linear series with noise
    t_vals = np.arange(15)
    y = 10.0 + 2.0 * t_vals + np.random.normal(0, 0.2, size=15)

    a_hist, p_hist, log_lik = kf.filter_and_smooth(y)
    assert a_hist.shape == (15, 2)
    # Final slope estimate should be close to 2.0
    assert np.isclose(a_hist[-1, 1], 2.0, atol=0.5)

    # Forecast 4 steps ahead
    y_f, y_v = kf.forecast(4, a_hist[-1], p_hist[-1])
    assert len(y_f) == 4
    # Next step should continue slope
    assert y_f[0] > y[-1]


def test_bsts_causal_impact_full_pipeline():
    # 10 time periods: 1..6 pre-intervention, 7..10 post-intervention
    series_data = []
    periods = list(range(1, 11))

    for p in periods:
        base_y = 50.0 + 1.2 * p
        if p >= 7:
            base_y += 15.0  # true positive intervention effect
        # Add 3 responses per period to test aggregation
        for noise in [-0.5, 0.0, 0.5]:
            series_data.append({
                "period": p,
                "score": base_y + noise,
                "control_metric": 100.0 + 0.5 * p
            })

    res = estimate_bsts_causal_impact(
        series_data=series_data,
        time_col="period",
        outcome_col="score",
        intervention_time=7,
        covariate_cols=["control_metric"]
    )

    assert res["status"] == "SUCCESS"
    assert res["pre_periods_count"] == 6
    assert res["post_periods_count"] == 4
    # Pointwise effect should be close to +15.0
    assert np.isclose(res["avg_pointwise_effect"], 15.0, atol=2.5)
    # Cumulative effect should be around 4 * 15 = 60.0
    assert res["cumulative_effect"] > 45.0
    assert res["relative_effect_pct"] > 15.0
    # Statistically significant
    assert res["is_significant"] is True
    assert res["posterior_tail_p_value"] < 0.05
    assert len(res["trajectory"]) == 10
    assert "<svg" in res["svg_chart"]
    assert "Bayesian Structural Time Series" in res["apa_narrative"]


def test_bsts_causal_impact_edge_cases():
    # Empty data
    res_empty = estimate_bsts_causal_impact([], "t", "y", 5)
    assert res_empty["status"] == "NO_DATA"

    # Insufficient periods (< 5)
    res_few = estimate_bsts_causal_impact([
        {"t": 1, "y": 10},
        {"t": 2, "y": 20},
        {"t": 3, "y": 30}
    ], "t", "y", 2)
    assert res_few["status"] == "INSUFFICIENT_PERIODS"

    # Intervention time not found
    res_not_found = estimate_bsts_causal_impact([
        {"t": 1, "y": 10},
        {"t": 2, "y": 20},
        {"t": 3, "y": 30},
        {"t": 4, "y": 40},
        {"t": 5, "y": 50}
    ], "t", "y", 999)
    assert res_not_found["status"] == "INTERVENTION_TIME_NOT_FOUND"
