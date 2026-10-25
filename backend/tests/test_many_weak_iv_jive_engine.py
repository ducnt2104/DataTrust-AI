"""
Unit tests for Many-Weak-IV Robust JIVE, LIML & Fuller (1977) Engine.
DataTrust Quantitative Econometrics Architecture.
"""

import pytest
import numpy as np
from app.engine.many_weak_iv_jive_engine import (
    ManyWeakIVJIVEEngine,
    run_many_weak_iv_jive_analysis,
)


def test_many_weak_iv_jive_synthetic_data():
    """Test JIVE, LIML, and Fuller with many weak/moderate instruments under unobserved confounding."""
    np.random.seed(42)
    N = 250
    K = 4  # 4 instruments

    # Unobserved confounder U
    U = np.random.normal(0, 1, size=N)

    # Exogenous control X
    X = np.random.normal(10, 2, size=(N, 1))

    # K Instruments Z
    Z = np.random.normal(0, 1, size=(N, K))

    # First stage: D is driven by Z, X, and U (endogeneity!)
    pi = np.array([0.35, 0.30, 0.25, 0.20])
    D = Z @ pi + 0.4 * X.ravel() + 0.8 * U + np.random.normal(0, 0.5, size=N)

    # Second stage structural model: True beta = 2.2
    true_beta = 2.2
    Y = true_beta * D + 0.5 * X.ravel() + 1.2 * U + np.random.normal(0, 0.6, size=N)

    res = ManyWeakIVJIVEEngine.estimate(
        treatment=D,
        outcome=Y,
        instruments=Z,
        covariates=X,
        instrument_names=["Z1", "Z2", "Z3", "Z4"],
        covariate_names=["X1"],
        fuller_a=1.0,
        seed=42,
    )

    assert res["status"] == "success"
    assert res["sample_size"] == N
    assert res["instruments_count"] == K
    assert res["covariates_count"] == 1

    # First stage diagnostics
    fs = res["first_stage_diagnostics"]
    assert fs["f_statistic"] > 5.0
    assert fs["mean_leverage"] > 0.0
    assert fs["max_leverage"] < 1.0

    # Estimator comparisons
    comp = res["estimator_comparisons"]
    assert len(comp) == 5

    ols = next(c for c in comp if "OLS" in c["estimator"])
    tsls = next(c for c in comp if "2SLS" in c["estimator"])
    jive = next(c for c in comp if "JIVE" in c["estimator"])
    liml = next(c for c in comp if "LIML" in c["estimator"])
    fuller = next(c for c in comp if "Fuller" in c["estimator"])

    # OLS is biased upward by U (true beta = 2.2)
    assert ols["estimate"] > tsls["estimate"] or ols["estimate"] > 2.0

    # JIVE and Fuller should produce valid, non-divergent point estimates
    assert 1.0 < jive["estimate"] < 3.5
    assert 1.0 < fuller["estimate"] < 3.5
    assert jive["std_error"] > 0.0
    assert fuller["std_error"] > 0.0

    # Overidentification Test (Sargan J)
    overid = res["overidentification_test"]
    assert overid["is_overidentified"]
    assert overid["df"] == K - 1
    assert overid["sargan_statistic"] is not None

    # SVG & APA Narrative
    assert "<svg" in res["svg_visualization"]
    assert "Panel A: Estimator Bias Comparison" in res["svg_visualization"]
    assert "Panel B: Instrument Strength" in res["svg_visualization"]
    assert "Angrist et al., 1999" in res["apa_narrative"]


def test_many_weak_iv_jive_helper_records():
    """Test helper wrapper with dictionary records."""
    np.random.seed(123)
    records = []
    for i in range(80):
        z1 = float(np.random.normal())
        z2 = float(np.random.normal())
        u = float(np.random.normal())
        d = 0.5 * z1 + 0.4 * z2 + 0.7 * u + float(np.random.normal(0, 0.3))
        y = 3.0 * d + 0.9 * u + float(np.random.normal(0, 0.4))
        records.append({
            "respondent_id": f"R_{i}",
            "treatment_d": d,
            "outcome_y": y,
            "instrument_z1": z1,
            "instrument_z2": z2,
        })

    res = run_many_weak_iv_jive_analysis(
        records=records,
        treatment_col="treatment_d",
        outcome_col="outcome_y",
        instrument_cols=["instrument_z1", "instrument_z2"],
    )

    assert res["status"] == "success"
    assert res["sample_size"] == 80
    assert res["instruments_count"] == 2
    assert len(res["estimator_comparisons"]) == 5


def test_many_weak_iv_jive_sample_size_error():
    """Test validation on sample size N < 30."""
    with pytest.raises(ValueError, match="too small"):
        ManyWeakIVJIVEEngine.estimate(
            treatment=np.array([1, 2, 3]),
            outcome=np.array([10, 20, 30]),
            instruments=np.array([[1], [2], [3]]),
        )


def test_many_weak_iv_jive_empty_instruments_error():
    """Test validation on zero instruments."""
    with pytest.raises(ValueError, match="At least one instrumental variable"):
        ManyWeakIVJIVEEngine.estimate(
            treatment=np.ones(40),
            outcome=np.ones(40),
            instruments=np.empty((40, 0)),
        )
