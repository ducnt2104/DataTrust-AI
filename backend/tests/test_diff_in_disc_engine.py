"""
Unit tests for Difference-in-Discontinuities Design Engine (Diff-in-Disc / RD-DID)
DataTrust Iteration 174
"""

import pytest
import numpy as np
from app.engine.diff_in_disc_engine import run_diff_in_discontinuities, compute_optimal_bandwidth


def test_diff_in_disc_estimation_recovers_true_parameters():
    np.random.seed(42)
    cutoff = 50.0
    true_tau = 6.0
    true_gamma_0 = 3.5

    records = []
    # 200 units observed in 2 periods (0 and 1) -> 400 observations
    for i in range(200):
        x = np.random.uniform(35, 65)
        x_c = x - cutoff
        d = 1 if x >= cutoff else 0
        u = np.random.normal(0, 0.5)

        for t in [0, 1]:
            y = (
                25.0
                + 0.4 * x_c
                + true_gamma_0 * d
                + 2.0 * t
                + true_tau * (d * t)
                + u
                + np.random.normal(0, 0.5)
            )
            records.append({
                "unit_id": f"store_{i}",
                "score": round(float(x), 2),
                "wave": str(t),
                "revenue": round(float(y), 2)
            })

    res = run_diff_in_discontinuities(
        records=records,
        running_col="score",
        cutoff=cutoff,
        period_col="wave",
        outcome_col="revenue",
        unit_col="unit_id",
        post_period_val="1",
        bandwidth=12.0
    )

    assert res["status"] == "success"
    assert res["sample_size_total"] == 400
    assert res["sample_size_effective_h"] > 150
    assert res["cutoff_threshold"] == cutoff

    est = res["estimates"]
    # Check that tau is close to true_tau = 6.0
    assert abs(est["diff_in_disc_tau"] - true_tau) < 0.6
    assert est["is_significant"] is True
    assert est["p_value"] < 0.05
    assert est["se"] > 0

    # Check baseline pre-jump is close to 3.5
    assert abs(est["baseline_pre_jump_gamma0"] - true_gamma_0) < 0.6
    assert est["baseline_pre_p_value"] < 0.05

    # Check that naive post RD is higher because it confounds the pre-jump
    assert est["naive_post_rd_tau"] > est["diff_in_disc_tau"]

    diag = res["diagnostics"]
    assert diag["optimal_bandwidth_h"] > 0
    assert "bandwidth_sensitivity" in res
    assert len(res["bandwidth_sensitivity"]) == 5
    assert "<svg" in res["svg_visualization"]
    assert "Grembi" in res["apa_narrative"]


def test_diff_in_disc_insufficient_sample():
    records = [{"score": 50, "period": "1", "outcome": 10}]
    res = run_diff_in_discontinuities(
        records=records,
        running_col="score",
        cutoff=50.0,
        period_col="period",
        outcome_col="outcome"
    )
    assert res["status"] == "error"
    assert "quá ít" in res["message"]


def test_diff_in_disc_single_period():
    records = [{"score": 40 + i, "period": "1", "outcome": 100} for i in range(40)]
    res = run_diff_in_discontinuities(
        records=records,
        running_col="score",
        cutoff=50.0,
        period_col="period",
        outcome_col="outcome"
    )
    assert res["status"] == "error"
    assert "chỉ có 1 giá trị" in res["message"]
