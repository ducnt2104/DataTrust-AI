"""
Unit tests for Abadie (2003) Kappa-Weighting Complier Profiling & Compliance Typology Engine.
DataTrust Quantitative Econometrics Architecture.
"""

import pytest
import numpy as np
from app.engine.abadie_complier_profiling_engine import (
    AbadieComplierProfilingEngine,
    run_abadie_complier_profiling,
)


def test_abadie_complier_profiling_synthetic_data():
    """Test Abadie complier profiling with synthetic encouragement design."""
    np.random.seed(42)
    N = 300

    # Covariates: Age (continuous), PriorEngagement (continuous), TechSavvy (binary 0/1)
    Age = np.random.normal(45, 10, size=N)
    PriorEngagement = np.random.normal(5, 2, size=N)
    TechSavvy = (np.random.uniform(0, 1, size=N) > 0.4).astype(float)
    X = np.column_stack([Age, PriorEngagement, TechSavvy])

    # Randomized Instrument Z ~ Bernoulli(0.5)
    Z = (np.random.uniform(0, 1, size=N) > 0.5).astype(float)

    # Compliance Types:
    # Compliers are much more likely to be TechSavvy
    # Latent probability of being a complier
    p_comp = 0.3 + 0.4 * TechSavvy
    is_complier = np.random.uniform(0, 1, size=N) < p_comp

    # Treatment D:
    # If complier, D = Z
    # If not complier, 20% always-takers (D=1 always), 80% never-takers (D=0 always)
    always_taker = (np.random.uniform(0, 1, size=N) < 0.2) & (~is_complier)
    D = np.zeros(N)
    for i in range(N):
        if is_complier[i]:
            D[i] = Z[i]
        elif always_taker[i]:
            D[i] = 1.0
        else:
            D[i] = 0.0

    # Outcome Y: LATE = +3.5 for compliers
    Y0 = 10.0 + 0.1 * Age + 0.5 * PriorEngagement + np.random.normal(0, 1, size=N)
    Y1 = Y0 + 3.5
    Y = np.where(D == 1.0, Y1, Y0)

    res = AbadieComplierProfilingEngine.profile(
        treatment=D,
        instrument=Z,
        covariates=X,
        outcome=Y,
        covariate_names=["Age", "PriorEngagement", "TechSavvy"],
        estimate_instrument_propensity=True,
        n_bootstraps=50,
        seed=42,
    )

    assert res["status"] == "success"
    assert res["sample_size"] == N

    # Compliance Typology
    typology = res["compliance_typology"]
    assert 0.0 < typology["p_compliers"] < 1.0
    assert 0.0 <= typology["p_always_takers"] < 1.0
    assert 0.0 <= typology["p_never_takers"] < 1.0
    sum_strata = typology["p_compliers"] + typology["p_always_takers"] + typology["p_never_takers"]
    assert pytest.approx(sum_strata, abs=0.05) == 1.0

    # First-stage F-statistic should be substantial
    assert typology["first_stage_f"] > 10.0
    assert not typology["weak_instrument"]

    # Feature profiles
    profiles = res["feature_profiles"]
    assert len(profiles) == 3

    # TechSavvy should have relative likelihood ratio > 1.0 because compliers are enriched for TechSavvy
    tech_prof = next(p for p in profiles if p["feature_name"] == "TechSavvy")
    assert tech_prof["relative_likelihood_ratio"] > 1.0
    assert "Overrepresented" in tech_prof["representation"]

    # LATE effect
    late = res["late_causal_effect"]
    assert late is not None
    assert late["late_estimate"] > 1.5  # True effect is 3.5
    assert late["is_significant"]
    assert late["ci_95"][0] < late["late_estimate"] < late["ci_95"][1]

    # SVG Visualization & APA Narrative
    assert "<svg" in res["svg_visualization"]
    assert "Panel A: Compliance Typology" in res["svg_visualization"]
    assert "Panel B: Complier Profiling" in res["svg_visualization"]
    assert "Abadie (2003)" in res["apa_narrative"]


def test_abadie_complier_profiling_helper_records():
    """Test helper wrapper function with dictionary records."""
    np.random.seed(123)
    records = []
    for i in range(100):
        z = 1 if i % 2 == 0 else 0
        tech = 1 if i % 3 == 0 else 0
        # Complier if tech==1 else never-taker
        d = z if tech == 1 else 0
        y = 50.0 + 5.0 * d + np.random.normal(0, 1)
        records.append({
            "respondent_id": f"R_{i}",
            "encouragement_iv": z,
            "treatment_taken": d,
            "tech_score": tech,
            "satisfaction_post": y,
        })

    res = run_abadie_complier_profiling(
        records=records,
        treatment_col="treatment_taken",
        instrument_col="encouragement_iv",
        covariate_cols=["tech_score"],
        outcome_col="satisfaction_post",
        n_bootstraps=30,
        seed=123,
    )

    assert res["status"] == "success"
    assert res["sample_size"] == 100
    assert len(res["feature_profiles"]) == 1
    assert res["late_causal_effect"] is not None


def test_abadie_complier_profiling_monotonicity_error():
    """Test that monotonicity violation raises a descriptive ValueError."""
    # Defier population: Z=1 leads to D=0, Z=0 leads to D=1
    D = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1] * 5)
    Z = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0] * 5)
    X = np.ones((50, 1))

    with pytest.raises(ValueError, match="Monotonicity violation"):
        AbadieComplierProfilingEngine.profile(
            treatment=D,
            instrument=Z,
            covariates=X,
        )


def test_abadie_complier_profiling_sample_size_error():
    """Test sample size validation (<25 records)."""
    with pytest.raises(ValueError, match="too small"):
        AbadieComplierProfilingEngine.profile(
            treatment=np.array([1, 0, 1]),
            instrument=np.array([1, 0, 0]),
            covariates=np.array([[1], [2], [3]]),
        )
