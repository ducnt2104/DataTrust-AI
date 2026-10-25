import pytest
import numpy as np
from app.engine.causal_mediation_sensitivity_engine import run_causal_mediation_sensitivity


def test_causal_mediation_sensitivity_insufficient_records():
    records = [{"t": 1, "m": 2.0, "y": 3.0} for _ in range(10)]
    res = run_causal_mediation_sensitivity(records, "t", "m", "y")
    assert res["status"] == "error"
    assert "N=10" in res["message"]


def test_causal_mediation_sensitivity_imbalanced_treatment():
    # 30 records all with treatment = 0
    records = [{"t": 0, "m": float(i), "y": float(i * 2)} for i in range(30)]
    res = run_causal_mediation_sensitivity(records, "t", "m", "y")
    assert res["status"] == "error"
    assert "Treated=0" in res["message"]


def test_causal_mediation_sensitivity_valid():
    np.random.seed(42)
    n = 120
    t = np.random.binomial(1, 0.5, n)
    c1 = np.random.normal(0, 1, n)
    # M = 1.0 + 0.8 * T + 0.3 * C1 + e_M
    e_m = np.random.normal(0, 0.4, n)
    m = 1.0 + 0.8 * t + 0.3 * c1 + e_m
    # Y = 2.0 + 0.4 * T + 0.9 * M + 0.5 * C1 + e_Y
    e_y = np.random.normal(0, 0.4, n)
    y = 2.0 + 0.4 * t + 0.9 * m + 0.5 * c1 + e_y

    records = []
    for i in range(n):
        records.append({
            "treatment": int(t[i]),
            "mediator": float(m[i]),
            "outcome": float(y[i]),
            "covariate1": float(c1[i])
        })

    res = run_causal_mediation_sensitivity(
        records=records,
        treatment_col="treatment",
        mediator_col="mediator",
        outcome_col="outcome",
        covariate_cols=["covariate1"]
    )

    assert res["status"] == "success"
    assert res["sample_diagnostics"]["n_total"] == n
    assert res["sample_diagnostics"]["n_treated"] > 30
    assert res["sample_diagnostics"]["n_control"] > 30

    # Path a (T -> M) should be positive and significant
    path_a = res["path_estimates"]["path_a"]
    assert path_a["coefficient"] > 0.5
    assert path_a["is_significant"] is True

    # Path b (M -> Y) should be positive and significant
    path_b = res["path_estimates"]["path_b"]
    assert path_b["coefficient"] > 0.6
    assert path_b["is_significant"] is True

    # ACME should be positive
    baseline = res["baseline_effects"]
    assert baseline["acme"] > 0.4
    assert baseline["is_significant"] is True
    assert baseline["total_effect"] > baseline["acme"]

    # Sensitivity analysis
    sens = res["sensitivity_analysis"]
    assert "critical_rho_threshold" in sens
    assert sens["critical_rho_threshold"] > 0.3  # Robust because true effect is strong
    assert sens["robustness_level"] in ["HIGHLY_ROBUST", "MODERATELY_ROBUST"]
    assert len(sens["sensitivity_curve"]) > 5

    # SVG chart and narrative
    assert "<svg" in res["svg_chart"]
    assert "</svg>" in res["svg_chart"]
    assert "Imai, Keele" in res["apa_narrative"]
