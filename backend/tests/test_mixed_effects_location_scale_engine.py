"""
Unit tests for Mixed-Effects Location Scale Models (MELSM) Engine
(Hedeker et al. 2008 Biometrics; Hedeker et al. 2012 Psychological Methods)
DataTrust Iteration 194
"""

import pytest
import numpy as np
from app.engine.mixed_effects_location_scale_engine import (
    MELSMEngine,
    run_melsm_analysis,
)


def test_melsm_synthetic():
    np.random.seed(194)
    N_subj = 12
    n_per_subj = 6
    N_total = N_subj * n_per_subj

    subjs = []
    y_vals = []

    # True parameters:
    # beta_0 = 10.0, sigma_u = 2.0
    # tau_0 = 0.0 (baseline var = 1.0), sigma_omega = 0.8
    # Correlation rho = -0.3
    s_u = 2.0
    s_w = 0.8
    rho = -0.3

    for i in range(N_subj):
        z1 = np.random.normal(0, 1)
        z2 = np.random.normal(0, 1)
        u_i = s_u * z1
        om_i = s_w * (rho * z1 + np.sqrt(1 - rho ** 2) * z2)
        var_i = np.exp(om_i)

        for _ in range(n_per_subj):
            e_ij = np.random.normal(0, np.sqrt(var_i))
            y_ij = 10.0 + u_i + e_ij
            subjs.append(f"Subj_{i+1}")
            y_vals.append(y_ij)

    res = MELSMEngine.evaluate(
        subject_ids=np.array(subjs),
        y=np.array(y_vals),
        alpha=0.05,
    )

    assert res["status"] == "success"
    assert res["sample_size_total"] == N_total
    assert res["sample_size_subjects"] == N_subj

    # Location fixed effect close to 10.0
    loc_eff = res["location_fixed_effects"][0]
    assert 7.0 <= loc_eff["coefficient"] <= 13.0
    assert loc_eff["std_error"] > 0

    # Scale components
    vc = res["random_effects_variance_components"]
    assert vc["between_subject_mean_sd_sigma_u"] > 0
    assert vc["between_subject_scale_sd_sigma_omega"] > 0
    assert -1.0 <= vc["location_scale_correlation_rho"] <= 1.0

    # Likelihood Ratio Test
    lrt = res["scale_heterogeneity_test"]
    assert lrt["lrt_statistic"] >= 0
    assert lrt["degrees_of_freedom"] == 2

    # Typology
    typ = res["subject_consistency_typology"]
    assert sum(typ.values()) == N_subj

    # SVG & APA
    assert "<svg" in res["svg_visualization"]
    assert "Panel A:" in res["svg_visualization"]
    assert "Panel B:" in res["svg_visualization"]
    assert "Hedeker" in res["apa_narrative"]


def test_melsm_helper_records():
    records = []
    for i in range(8):
        for rep in range(4):
            records.append({
                "respondent_id": f"R_{i}",
                "satisfaction_score": str(round(5.0 + i * 0.5 + float(np.random.normal(0, 0.4)), 2)),
                "time_index": str(rep),
            })

    res = run_melsm_analysis(
        records=records,
        subject_col="respondent_id",
        outcome_col="satisfaction_score",
        location_covariate_cols=["time_index"],
    )
    assert res["status"] == "success"
    assert res["sample_size_subjects"] == 8
    assert len(res["location_fixed_effects"]) == 2  # Intercept and time_index


def test_melsm_insufficient_sample():
    with pytest.raises(ValueError, match="Cỡ mẫu quá nhỏ"):
        MELSMEngine.evaluate(
            subject_ids=np.array(["A", "A", "B", "B"]),
            y=np.array([1.0, 2.0, 3.0, 4.0]),
        )


def test_melsm_insufficient_subjects():
    subjs = np.array(["A"] * 30)
    y = np.random.normal(0, 1, 30)
    with pytest.raises(ValueError, match="Số lượng đối tượng"):
        MELSMEngine.evaluate(subjs, y)
