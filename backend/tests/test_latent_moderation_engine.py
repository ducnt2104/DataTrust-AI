# -*- coding: utf-8 -*-
"""
Unit tests for LatentModerationEngine (LMS / QML)
"""
import pytest
import numpy as np
from app.engine.latent_moderation_engine import LatentModerationEngine


def test_lms_insufficient_sample():
    res = LatentModerationEngine.estimate(
        data=[{"x1": 1.0, "m1": 2.0, "y1": 3.0}],
        predictor_items=["x1"],
        moderator_items=["m1"],
        outcome_items=["y1"]
    )
    assert res["status"] in ["INSUFFICIENT_DATA", "INSUFFICIENT_VALID_SAMPLE"]


def test_lms_estimation_end_to_end():
    np.random.seed(42)
    n = 100

    # True latent factors: xi_1, xi_2 ~ N(0, 1)
    xi_1 = np.random.normal(0, 1.0, n)
    xi_2 = np.random.normal(0, 1.0, n)

    # True structural equation: eta = 0.5 * xi_1 + 0.3 * xi_2 + 0.4 * (xi_1 * xi_2) + error
    zeta = np.random.normal(0, 0.4, n)
    eta = 0.5 * xi_1 + 0.3 * xi_2 + 0.4 * (xi_1 * xi_2) + zeta

    # Observed indicators with measurement noise (reliability ~ 0.80)
    x1_1 = xi_1 + np.random.normal(0, 0.4, n)
    x1_2 = 0.8 * xi_1 + np.random.normal(0, 0.4, n)

    x2_1 = xi_2 + np.random.normal(0, 0.4, n)
    x2_2 = 0.9 * xi_2 + np.random.normal(0, 0.4, n)

    y_1 = eta + np.random.normal(0, 0.4, n)
    y_2 = 0.85 * eta + np.random.normal(0, 0.4, n)

    data = [
        {
            "pred_item1": float(x1_1[i]),
            "pred_item2": float(x1_2[i]),
            "mod_item1": float(x2_1[i]),
            "mod_item2": float(x2_2[i]),
            "out_item1": float(y_1[i]),
            "out_item2": float(y_2[i]),
        }
        for i in range(n)
    ]

    res = LatentModerationEngine.estimate(
        data=data,
        predictor_items=["pred_item1", "pred_item2"],
        moderator_items=["mod_item1", "mod_item2"],
        outcome_items=["out_item1", "out_item2"]
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "LATENT_MODERATED_STRUCTURAL_EQUATIONS_LMS"

    diag = res["diagnostics"]
    assert diag["sample_size"] == 100
    assert diag["converged"] is True
    assert diag["structural_r2"] > 0.20
    assert diag["cohen_f2_effect_size"] > 0
    assert "attenuation_bias_gap_pct" in diag
    assert diag["latent_predictor_reliability_alpha"] > 0.5
    assert diag["latent_moderator_reliability_alpha"] > 0.5
    assert diag["latent_outcome_reliability_alpha"] > 0.5

    # Check coefficients
    coeffs = res["coefficients"]
    assert len(coeffs) == 3
    g3 = next(c for c in coeffs if c["parameter"] == "gamma_3")
    assert g3["estimate"] > 0.15  # detects the positive interaction

    # Check simple slopes
    slopes = res["simple_slopes"]
    assert len(slopes) == 3
    # High moderator slope should be greater than low moderator slope for positive interaction
    s_low = next(s for s in slopes if "-1 SD" in s["level_label"])
    s_high = next(s for s in slopes if "+1 SD" in s["level_label"])
    assert s_high["simple_slope"] > s_low["simple_slope"]

    # Check SVG & APA narrative
    assert "<svg" in res["svg_visualization"]
    assert "Latent Moderated Structural Equations" in res["apa_narrative"]
    assert "Klein & Moosbrugger" in res["apa_narrative"]
