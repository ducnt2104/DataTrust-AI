"""
Unit tests for Randomized Response Technique (RRT) & Crosswise Engine
(Warner 1965; Yu et al. 2008; Jann et al. 2012)
DataTrust Iteration 193
"""

import pytest
import numpy as np
from app.engine.randomized_response_engine import (
    RandomizedResponseEngine,
    run_randomized_response_analysis,
)


def test_rrt_crosswise_synthetic():
    np.random.seed(193)
    N = 300
    p_rand = 0.70
    true_pi = 0.30

    # True latent status (1 with prob 0.30)
    latent_trait = np.random.binomial(1, true_pi, N)

    # Crosswise model: respondent generates auxiliary event with prob p_rand
    aux_event = np.random.binomial(1, p_rand, N)
    # Observed response = 1 if (latent == aux) else 0
    y_rrt = np.where(latent_trait == aux_event, 1, 0)

    # Direct questioning: severe under-reporting (only 10% admit)
    y_direct = np.where(latent_trait == 1, np.random.binomial(1, 0.33, N), 0)

    res = RandomizedResponseEngine.evaluate(
        rrt_responses=y_rrt,
        model_type="crosswise",
        p_randomizer=p_rand,
        direct_responses=y_direct,
        alpha=0.05,
    )

    assert res["status"] == "success"
    assert res["sample_size"] == N
    assert res["model_type"] == "crosswise"
    # Latent prevalence estimate should be close to 0.30
    assert 0.20 <= res["estimated_prevalence"] <= 0.40
    assert res["std_error"] > 0
    assert len(res["ci_95"]) == 2

    # Social desirability diagnostics
    sdb = res["social_desirability_diagnostics"]
    assert sdb is not None
    assert sdb["direct_prevalence"] < res["estimated_prevalence"]
    assert sdb["sdb_gap_percentage_points"] > 0
    assert sdb["significant_underreporting"] is True

    # Efficiency curve & SVG
    assert len(res["efficiency_curve"]) == 20
    assert "<svg" in res["svg_visualization"]
    assert "Panel A:" in res["svg_visualization"]
    assert "Panel B:" in res["svg_visualization"]
    assert "Crosswise Model" in res["apa_narrative"]


def test_rrt_warner_model():
    np.random.seed(193)
    N = 250
    p_rand = 0.75
    true_pi = 0.20

    latent = np.random.binomial(1, true_pi, N)
    randomizer = np.random.binomial(1, p_rand, N)
    # Warner: if randomizer == 1, answer sensitive trait; else answer negation (1 - latent)
    y_warner = np.where(randomizer == 1, latent, 1 - latent)

    res = RandomizedResponseEngine.evaluate(
        rrt_responses=y_warner,
        model_type="warner",
        p_randomizer=p_rand,
    )
    assert res["status"] == "success"
    assert 0.10 <= res["estimated_prevalence"] <= 0.32


def test_rrt_helper_records():
    records = []
    for i in range(50):
        # rrt answer alternates with some noise
        r_val = 1 if (i % 3 == 0 or i % 5 == 0) else 0
        d_val = 1 if i % 6 == 0 else 0
        records.append({
            "rrt_item": str(r_val),
            "direct_item": str(d_val),
        })

    res = run_randomized_response_analysis(
        records=records,
        rrt_question_id="rrt_item",
        direct_question_id="direct_item",
        model_type="crosswise",
        p_randomizer=0.70,
    )
    assert res["status"] == "success"
    assert res["sample_size"] == 50


def test_rrt_invalid_probability():
    y = np.ones(30)
    with pytest.raises(ValueError, match="không được bằng 0.50"):
        RandomizedResponseEngine.evaluate(y, p_randomizer=0.50)


def test_rrt_sample_size_error():
    records = [{"rrt": "1"} for _ in range(10)]
    with pytest.raises(ValueError, match="Không đủ phản hồi hợp lệ"):
        run_randomized_response_analysis(records, "rrt")
