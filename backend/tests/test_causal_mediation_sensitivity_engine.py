"""
Unit Tests for DataTrust Causal Mediation & Sensitivity Engine (Iteration 170)
"""

import pytest
import numpy as np
from app.engine.causal_mediation_sensitivity_engine import run_causal_mediation_sensitivity_analysis


def test_causal_mediation_sensitivity_positive_effect():
    rng = np.random.default_rng(42)
    n = 200

    # Covariate Z
    z = rng.normal(0, 1, size=n)
    # Treatment T
    t = rng.integers(0, 2, size=n).astype(float)

    # True path a = 1.8
    m = 2.0 + 1.8 * t + 0.5 * z + rng.normal(0, 0.8, size=n)

    # True path b = 1.5, true path c' = 1.2
    y = 5.0 + 1.2 * t + 1.5 * m + 0.4 * z + rng.normal(0, 1.0, size=n)

    records = []
    for i in range(n):
        records.append({
            "id": f"resp_{i}",
            "answers": {
                "q_treat": float(t[i]),
                "q_med": float(m[i]),
                "q_out": float(y[i]),
                "q_cov": float(z[i]),
            }
        })

    res = run_causal_mediation_sensitivity_analysis(
        records=records,
        treatment_question_id="q_treat",
        mediator_question_id="q_med",
        outcome_question_id="q_out",
        covariate_question_ids=["q_cov"],
        simulations=200,
        alpha_level=0.05,
    )

    assert res["status"] in ("SUCCESS", "success")
    assert res["sample_size"] == n
    assert res["n_treated"] > 70
    assert res["n_control"] > 70

    # Path coefficients
    paths = res["path_coefficients"]
    assert abs(paths["path_a_treatment_to_mediator"] - 1.8) < 0.4
    assert abs(paths["path_b_mediator_to_outcome"] - 1.5) < 0.4
    assert abs(paths["path_c_prime_direct"] - 1.2) < 0.5

    # Causal effects
    eff = res["causal_effects"]
    acme = eff["acme_indirect"]
    assert acme["estimate"] > 2.0
    assert acme["is_significant"]
    assert acme["p_value"] < 0.01

    assert eff["proportion_mediated_pct"] > 40.0

    # Sensitivity bound
    sens = res["sensitivity_analysis"]
    assert "critical_rho_zero" in sens
    assert abs(sens["critical_rho_zero"]) > 0.30
    assert len(sens["curve_points"]) > 20

    # SVG & APA Narrative
    assert "<svg" in res["svg_visualization"]
    assert "Average Causal Mediation Effect" in res["apa_narrative"]
    assert "Imai, Keele, and Yamamoto (2010)" in res["apa_narrative"]


def test_causal_mediation_sensitivity_null_effect():
    rng = np.random.default_rng(999)
    n = 150
    t = rng.integers(0, 2, size=n).astype(float)
    # T does not affect M
    m = 2.0 + 0.0 * t + rng.normal(0, 1.0, size=n)
    y = 4.0 + 1.5 * t + 0.2 * m + rng.normal(0, 1.0, size=n)

    records = [{
        "answers": {
            "q_t": float(t[i]),
            "q_m": float(m[i]),
            "q_y": float(y[i]),
        }
    } for i in range(n)]

    res = run_causal_mediation_sensitivity_analysis(
        records=records,
        treatment_question_id="q_t",
        mediator_question_id="q_m",
        outcome_question_id="q_y",
        simulations=100,
    )

    assert res["status"] in ("SUCCESS", "success")
    assert not res["causal_effects"]["acme_indirect"]["is_significant"]
    assert res["causal_effects"]["acme_indirect"]["p_value"] >= 0.05


def test_causal_mediation_sensitivity_insufficient_sample():
    records = [{"answers": {"q_t": 1.0, "q_m": 2.0, "q_y": 3.0}} for _ in range(10)]
    res = run_causal_mediation_sensitivity_analysis(
        records=records,
        treatment_question_id="q_t",
        mediator_question_id="q_m",
        outcome_question_id="q_y",
    )
    assert res["status"] in ("INSUFFICIENT_SAMPLE", "insufficient_data")
    assert res["sample_size"] == 10
