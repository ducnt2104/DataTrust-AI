"""
Unit Tests for DataTrust Dynamic Discrete Choice Structural Dynamic Programming Engine (Iteration 171)
"""

import pytest
import numpy as np
from app.engine.dynamic_discrete_choice_engine import run_dynamic_discrete_choice_estimation


def test_dynamic_discrete_choice_engine_estimation():
    rng = np.random.default_rng(42)
    n = 200

    # Simulate dynamic Markov decision process
    # State s in [0, 50], decision d in {0, 1}
    s_curr = 0.0
    records = []

    for i in range(n):
        # Probability of replacement increases as state s increases
        prob_replace = 1.0 / (1.0 + np.exp(-(0.15 * s_curr - 3.0)))
        d_val = 1 if rng.uniform(0, 1) < prob_replace else 0

        records.append({
            "id": f"resp_{i}",
            "answers": {
                "q_state": float(s_curr),
                "q_decision": int(d_val),
            }
        })

        if d_val == 1:
            # Replacement resets state to near 0
            s_curr = float(rng.uniform(0.0, 3.0))
        else:
            # Maintain advances state
            s_curr = float(s_curr + rng.uniform(1.0, 4.0))

    res = run_dynamic_discrete_choice_estimation(
        records=records,
        state_question_id="q_state",
        decision_question_id="q_decision",
        discount_factor=0.95,
        num_discretized_states=12,
        counterfactual_subsidy_pct=25.0,
        alpha_level=0.05,
    )

    assert res["status"] == "success"
    assert res["sample_size"] == n
    assert res["num_states"] == 12

    # Structural parameters
    params = res["structural_parameters"]
    assert params["replacement_cost_rc"]["estimate"] > 0.1
    assert params["linear_operating_cost_th1"]["estimate"] > 0.001

    # Equilibrium thresholds
    thresh = res["equilibrium_thresholds"]
    assert thresh["baseline_threshold_state"] > 0.0
    # Subsidy lowers or keeps replacement state boundary
    assert thresh["counterfactual_threshold_state"] <= thresh["baseline_threshold_state"] + 1.0
    assert thresh["counterfactual_stationary_rate_pct"] >= thresh["baseline_stationary_rate_pct"] - 1.0

    # Profiles & Visuals
    assert len(res["state_profiles"]) == 12
    assert "<svg" in res["svg_visualization"]
    assert "Rust" in res["apa_narrative"]
    assert "Nested Fixed Point" in res["apa_narrative"]


def test_dynamic_discrete_choice_engine_insufficient_sample():
    records = [{"answers": {"q_s": 1.0, "q_d": 0}} for _ in range(10)]
    res = run_dynamic_discrete_choice_estimation(
        records=records,
        state_question_id="q_s",
        decision_question_id="q_d",
    )
    assert res["status"] == "insufficient_data"
    assert res["sample_size"] == 10
