"""
Unit tests for SplitBallotEngine (A/B Survey Experimentation & Wording Distortion)
"""

import pytest
from app.engine.split_ballot_engine import SplitBallotEngine

def test_assign_arm_deterministic_and_balanced():
    arms = [
        {"id": "arm_a", "weight": 50},
        {"id": "arm_b", "weight": 50}
    ]
    # Verify deterministic: same seed always gives same arm
    arm1 = SplitBallotEngine.assign_arm("survey_123", "user_abc", arms)
    arm2 = SplitBallotEngine.assign_arm("survey_123", "user_abc", arms)
    assert arm1 == arm2

    # Verify balance across 100 seeds
    counts = {"arm_a": 0, "arm_b": 0}
    for i in range(100):
        a = SplitBallotEngine.assign_arm("survey_123", f"seed_{i}", arms)
        counts[a] += 1

    # Should be close to 50/50 (e.g. between 35 and 65)
    assert 35 <= counts["arm_a"] <= 65
    assert 35 <= counts["arm_b"] <= 65

def test_compare_numeric_arms():
    # Group A: lower values, Group B: higher values
    vals_a = [3.0, 3.2, 2.9, 3.1, 3.0, 3.3, 2.8, 3.1]
    vals_b = [4.2, 4.5, 4.1, 4.3, 4.4, 4.0, 4.6, 4.3]

    res = SplitBallotEngine.compare_numeric_arms(vals_a, vals_b)
    assert res["is_sufficient"] is True
    assert res["mean_difference"] > 1.0
    assert res["p_value"] < 0.001
    assert res["is_significant"] is True
    assert res["cohens_d"] > 1.5  # Very large effect size

def test_compare_categorical_arms():
    # Arm A favors Option 1, Arm B favors Option 2
    opts_a = ["Ủng hộ"] * 30 + ["Phản đối"] * 10
    opts_b = ["Ủng hộ"] * 10 + ["Phản đối"] * 30
    all_opts = ["Ủng hộ", "Phản đối"]

    res = SplitBallotEngine.compare_categorical_arms(opts_a, opts_b, all_opts)
    assert res["is_sufficient"] is True
    assert res["chi_square"] > 15.0
    assert res["p_value"] < 0.001
    assert res["is_significant"] is True
    assert res["total_variation_distance"] == 0.5

def test_calculate_mwdi_thresholds():
    # Robust
    res_rob = SplitBallotEngine.calculate_mwdi(tvd=0.05)
    assert res_rob["level"] == "FRAME_ROBUST"
    assert res_rob["badge_color"] == "emerald"

    # Moderate
    res_mod = SplitBallotEngine.calculate_mwdi(tvd=0.20)
    assert res_mod["level"] == "MODERATELY_SENSITIVE"
    assert res_mod["badge_color"] == "amber"

    # Highly Plastic
    res_vuln = SplitBallotEngine.calculate_mwdi(tvd=0.45)
    assert res_vuln["level"] == "HIGHLY_PLASTIC"
    assert res_vuln["badge_color"] == "red"
