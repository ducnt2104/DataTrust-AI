import numpy as np
import pytest
from app.engine.manski_bounds_engine import ManskiBoundsEngine, _compute_imbens_manski_critical_value


def test_imbens_manski_critical_value():
    # Large separation: delta -> infty => c_alpha -> 1.645
    c_large = _compute_imbens_manski_critical_value(0.0, 10.0, 1.0, 1.0, 100, alpha=0.05)
    assert c_large == pytest.approx(1.645, abs=0.05)

    # Point identification: delta = 0 => c_alpha -> 1.96
    c_zero = _compute_imbens_manski_critical_value(0.0, 0.0, 1.0, 1.0, 100, alpha=0.05)
    assert c_zero == pytest.approx(1.96, abs=0.05)


def test_manski_bounds_synthetic():
    np.random.seed(42)
    n = 100
    # Treatment indicator
    d = np.random.binomial(1, 0.5, size=n)
    # Outcome scale 1 to 10
    base_y = np.random.uniform(3.0, 7.0, size=n)
    y_full = np.where(d == 1, base_y + 1.5, base_y)
    
    # Missingness: 25% missing
    r = np.random.binomial(1, 0.75, size=n)
    y_obs = np.where(r == 1, y_full, np.nan)

    res = ManskiBoundsEngine.evaluate_bounds(
        y_observed=y_obs,
        d_treatment=d,
        r_response=r,
        support_min=1.0,
        support_max=10.0,
        outcome_label="Satisfaction Rating",
        treatment_label="VIP Loyalty Program"
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "MANSKI_PARTIAL_IDENTIFICATION_BOUNDS_2000"
    diag = res["diagnostics"]
    assert diag["sample_size_total"] == n
    assert diag["observed_count"] > 60
    assert 0.15 <= diag["missing_rate"] <= 0.35

    # Worst-case bounds must contain the naive ATE
    assert diag["worst_case_lower"] <= diag["naive_ate"] <= diag["worst_case_upper"]

    # Monotone Treatment Selection (MTS) upper bound <= naive ATE + tol
    assert diag["mts_upper"] <= diag["naive_ate"] + 1e-4

    # Joint MTS + MTR lower bound >= 0
    assert diag["joint_mts_mtr_lower"] >= 0.0

    # Imbens & Manski CI covers joint bounds
    assert diag["ci_joint_lower_95"] <= diag["joint_mts_mtr_lower"]
    assert diag["ci_joint_upper_95"] >= diag["joint_mts_mtr_upper"]

    assert len(res["tiers"]) == 4
    assert len(res["sensitivity_grid"]) == 15
    assert "<svg" in res["svg_visualization"]
    assert "Manski" in res["apa_narrative"]
    assert "Imbens" in res["apa_narrative"]


def test_insufficient_sample():
    # Only 8 samples
    y = np.array([1, 2, 3, 4, 5, 6, 7, 8])
    d = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    r = np.array([1, 1, 1, 1, 1, 1, 1, 1])

    res = ManskiBoundsEngine.evaluate_bounds(y_observed=y, d_treatment=d, r_response=r)
    assert res["status"] == "INSUFFICIENT_SAMPLE"
    assert "Kích thước mẫu không đủ" in res["message"]
