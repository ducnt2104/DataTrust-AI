"""
Unit tests for Regression Discontinuity with Discrete Running Variables & Heaping Engine.
DataTrust Quantitative Econometrics Architecture.
"""

import pytest
import numpy as np
from app.engine.discrete_rd_heaping_engine import (
    DiscreteRDHeapingEngine,
    run_discrete_rd_heaping_analysis,
)


def test_discrete_rd_heaping_synthetic_jump():
    """Test Discrete RDD with true causal jump on discrete heaped support."""
    np.random.seed(42)
    N = 300

    # Discrete running variable with integer support [-15, 15]
    # Induced heaping at multiples of 5 (-10, -5, 0, 5, 10)
    base_x = np.random.randint(-15, 16, size=N)
    focal_x = np.random.choice([-10, -5, 0, 5, 10], size=N, p=[0.2, 0.2, 0.2, 0.2, 0.2])
    # 35% reported as rounded focal multiples
    is_heaped = np.random.uniform(0, 1, size=N) < 0.35
    X = np.where(is_heaped, focal_x, base_x).astype(float)

    # Cutoff at 0.0
    cutoff = 0.0
    true_tau = 3.5

    # True structural DGP: linear with jump
    D = (X >= cutoff).astype(float)
    Y = 20.0 + 0.8 * X + true_tau * D + np.random.normal(0, 1.2, size=N)

    res = DiscreteRDHeapingEngine.estimate(
        running_var=X,
        outcome_var=Y,
        cutoff=cutoff,
        kernel="triangular",
        focal_rounding_interval=5.0,
        n_permutations=200,
        seed=42,
    )

    assert res["status"] == "success"
    assert res["sample_size"] == N
    assert res["cutoff"] == cutoff

    # Discreteness Diagnostics
    diag = res["discreteness_diagnostics"]
    assert diag["is_discrete"]
    assert diag["heaping_ratio"] > 1.2
    assert "Heaping" in diag["heaping_severity"]
    assert diag["closest_left_point"] < 0.0
    assert diag["closest_right_point"] >= 0.0

    # Conventional RDD Point Estimate
    conv = res["conventional_rdd"]
    assert conv["tau_estimate"] > 2.0  # True jump is 3.5
    assert conv["is_significant"]
    assert conv["p_value"] < 0.05

    # Kolesár & Rothe (2018) Honest Bounds
    honest = res["kolesar_rothe_honest_bounds"]
    assert len(honest) >= 3
    # Verify that as curvature bound M increases, honest CI length monotonically widens
    ci_lens = [h["honest_ci_length"] for h in honest]
    for i in range(len(ci_lens) - 1):
        assert ci_lens[i] <= ci_lens[i + 1]

    # Donut-Hole diagnostics
    donut = res["donut_hole_diagnostics"]
    assert "tau_donut" in donut
    assert donut["is_heaping_robust"]

    # Local Randomization Inference (Cattaneo et al. 2015)
    lri = res["local_randomization_inference"]
    assert "fisher_exact_p_value" in lri
    assert lri["window_observations"] >= 10

    # SVG & APA Narrative
    assert "<svg" in res["svg_visualization"]
    assert "Panel A: Discrete Support" in res["svg_visualization"]
    assert "Panel B: Kolesár &amp; Rothe" in res["svg_visualization"]
    assert "Kolesár & Rothe, 2018" in res["apa_narrative"]


def test_discrete_rd_heaping_helper_records():
    """Test helper wrapper with dictionary records."""
    np.random.seed(123)
    records = []
    for i in range(80):
        # Age rounded to whole years [50..70], pension threshold at 60
        age = float(50 + (i % 21))
        pension_eligible = 1.0 if age >= 60.0 else 0.0
        income = 15.0 + 0.3 * (age - 60.0) + 4.5 * pension_eligible + np.random.normal(0, 0.8)
        records.append({
            "respondent_id": f"R_{i}",
            "age_years": age,
            "monthly_income": income,
        })

    res = run_discrete_rd_heaping_analysis(
        records=records,
        running_var_col="age_years",
        outcome_col="monthly_income",
        cutoff=60.0,
        focal_rounding_interval=5.0,
        n_permutations=100,
    )

    assert res["status"] == "success"
    assert res["sample_size"] == 80
    assert res["cutoff"] == 60.0
    assert res["conventional_rdd"]["tau_estimate"] > 3.0


def test_discrete_rd_heaping_sample_size_error():
    """Test sample size validation (<30 records)."""
    with pytest.raises(ValueError, match="too small"):
        DiscreteRDHeapingEngine.estimate(
            running_var=np.array([1, 2, 3]),
            outcome_var=np.array([10, 20, 30]),
        )


def test_discrete_rd_heaping_insufficient_support_error():
    """Test error when all points are on one side of cutoff."""
    with pytest.raises(ValueError, match="Insufficient support"):
        DiscreteRDHeapingEngine.estimate(
            running_var=np.array([1.0, 2.0, 3.0] * 15),
            outcome_var=np.array([10.0, 20.0, 30.0] * 15),
            cutoff=10.0,  # All points are < 10.0
        )
