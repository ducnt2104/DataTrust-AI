import pytest
import numpy as np
from app.engine.interactive_fixed_effects_engine import compute_interactive_fixed_effects


def test_interactive_fixed_effects_synthetic_panel():
    np.random.seed(42)
    n_units = 8
    n_times = 6
    true_tau = 3.5

    # True latent factor f_t across time
    f_t = np.array([0.5, 1.2, -0.8, 1.5, 2.0, -1.0])
    # True factor loadings gamma_i
    gamma_i = np.array([-1.5, -0.8, 0.2, 1.1, -0.3, 0.9, 1.8, -1.0])
    alpha_i = np.linspace(5.0, 15.0, n_units)
    lambda_t = np.linspace(1.0, 3.0, n_times)

    records = []
    for i in range(n_units):
        u_id = f"Unit_{i+1}"
        is_treated_unit = (i < 3)
        for t in range(n_times):
            # Treatment starts at t >= 3 for treated units
            w = 1.0 if (is_treated_unit and t >= 3) else 0.0
            # IFE structure: Y = alpha + lambda + gamma * f + tau * w + noise
            y = (
                alpha_i[i]
                + lambda_t[t]
                + gamma_i[i] * f_t[t]
                + true_tau * w
                + np.random.normal(0, 0.15)
            )
            records.append({
                "unit": u_id,
                "time": float(t + 1),
                "outcome": float(y),
                "treatment": float(w)
            })

    res = compute_interactive_fixed_effects(
        records=records,
        outcome_key="outcome",
        unit_key="unit",
        time_key="time",
        treatment_key="treatment"
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "INTERACTIVE_FIXED_EFFECTS_BAI_2009"
    diag = res["diagnostics"]
    assert diag["n_units"] == n_units
    assert diag["n_time_periods"] == n_times
    assert diag["n_treated_cells"] == 3 * 3  # 3 treated units * 3 post periods
    assert diag["num_factors_selected"] >= 1
    # Check that estimated tau is close to true_tau (within 1.5)
    assert abs(diag["tau_ife"] - true_tau) < 1.5
    assert diag["se_ife"] > 0
    assert "svg_visualization" in res
    assert "<svg" in res["svg_visualization"]
    assert "apa_narrative" in res
    assert "Interactive Fixed Effects" in res["apa_narrative"]
    assert len(res["latent_factors"]) == diag["num_factors_selected"]
    assert len(res["scree_spectrum"]) > 0


def test_interactive_fixed_effects_insufficient_data():
    # Only 5 observations
    records = [{"unit": f"U{i}", "time": 1.0, "outcome": 10.0, "treatment": 0.0} for i in range(5)]
    res = compute_interactive_fixed_effects(
        records=records,
        outcome_key="outcome",
        unit_key="unit",
        time_key="time",
        treatment_key="treatment"
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_interactive_fixed_effects_no_treated_units():
    records = []
    for i in range(5):
        for t in range(4):
            records.append({
                "unit": f"U_{i}",
                "time": float(t + 1),
                "outcome": float(10 + i + t),
                "treatment": 0.0  # No treatment
            })

    res = compute_interactive_fixed_effects(
        records=records,
        outcome_key="outcome",
        unit_key="unit",
        time_key="time",
        treatment_key="treatment"
    )
    assert res["status"] == "NO_TREATED_CELLS"
