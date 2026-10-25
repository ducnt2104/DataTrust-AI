"""
Unit Tests for DataTrust Causal Survival Analysis & RMST Engine (Iteration 169)
"""

import pytest
import numpy as np
from app.engine.causal_survival_rmst_engine import run_causal_survival_rmst_analysis


def test_causal_survival_rmst_engine_positive_effect():
    rng = np.random.default_rng(42)
    n = 200

    # Covariate: baseline risk score
    z = rng.normal(0, 1, size=n)
    # Treatment assignment (randomized or slightly confounded)
    prob_a = 1.0 / (1.0 + np.exp(-0.4 * z))
    a = (rng.uniform(0, 1, size=n) < prob_a).astype(int)

    # Time-to-event: treated has median survival 35.0, control 7.0
    scale = np.where(a == 1, 35.0, 7.0) * np.exp(-0.2 * z)
    true_event_time = rng.exponential(scale=scale)

    # Right censoring mechanism (administrative censoring at t=30)
    cens_time = rng.uniform(8.0, 30.0, size=n)
    observed_time = np.minimum(true_event_time, cens_time)
    event_indicator = (true_event_time <= cens_time).astype(int)

    records = []
    for i in range(n):
        records.append({
            "id": f"resp_{i}",
            "answers": {
                "q_time": float(observed_time[i]),
                "q_event": int(event_indicator[i]),
                "q_treat": int(a[i]),
                "q_risk": float(z[i]),
            }
        })

    res = run_causal_survival_rmst_analysis(
        records=records,
        time_question_id="q_time",
        event_question_id="q_event",
        treatment_question_id="q_treat",
        covariate_question_ids=["q_risk"],
        tau_horizon=15.0,
        alpha_level=0.05,
    )

    assert res["status"] == "success"
    assert res["sample_size"] == n
    assert res["n_treated"] > 50
    assert res["n_control"] > 50
    assert res["tau_horizon"] == 15.0

    # Treated RMST should exceed Control RMST
    assert res["rmst_treated"] > res["rmst_control"]
    delta = res["causal_rmst_difference"]
    assert delta["estimate"] > 3.0
    assert delta["is_significant"]
    assert delta["p_value"] < 0.01

    # RMTL reduction
    assert res["rmtl_metrics"]["rmtl_reduction_pct"] > 0.0

    # SVG & Narrative
    assert "<svg" in res["svg_visualization"]
    assert "Restricted Mean Survival Time" in res["apa_narrative"]
    assert "Royston & Parmar" in res["apa_narrative"]


def test_causal_survival_rmst_engine_null_effect():
    rng = np.random.default_rng(999)
    n = 150
    a = rng.integers(0, 2, size=n)
    # Identical distribution
    true_event_time = rng.exponential(scale=12.0, size=n)
    cens_time = rng.uniform(8.0, 20.0, size=n)
    observed_time = np.minimum(true_event_time, cens_time)
    event_indicator = (true_event_time <= cens_time).astype(int)

    records = [{
        "answers": {
            "q_time": float(observed_time[i]),
            "q_event": int(event_indicator[i]),
            "q_treat": int(a[i]),
        }
    } for i in range(n)]

    res = run_causal_survival_rmst_analysis(
        records=records,
        time_question_id="q_time",
        event_question_id="q_event",
        treatment_question_id="q_treat",
        tau_horizon=10.0,
    )

    assert res["status"] == "success"
    # Should not be statistically significant
    assert not res["causal_rmst_difference"]["is_significant"]
    assert res["causal_rmst_difference"]["p_value"] >= 0.05


def test_causal_survival_rmst_engine_insufficient_sample():
    records = [{"answers": {"q_time": 5.0, "q_event": 1, "q_treat": 1}} for _ in range(10)]
    res = run_causal_survival_rmst_analysis(
        records=records,
        time_question_id="q_time",
        event_question_id="q_event",
        treatment_question_id="q_treat",
    )
    assert res["status"] == "insufficient_data"
    assert res["sample_size"] == 10
