# -*- coding: utf-8 -*-
"""
Unit tests for Regression Kink Design (RKD) Engine
"""
import pytest
import numpy as np
from app.engine.regression_kink_engine import (
    RegressionKinkEngine,
    generate_rkd_svg
)


def test_rkd_insufficient_sample():
    y = np.random.randn(15)
    x = np.random.randn(15)
    res = RegressionKinkEngine.evaluate_rkd(
        y_outcome=y,
        x_running=x,
        cutoff=0.0
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"
    assert "Cần tối thiểu 30" in res["message"]


def test_rkd_sharp_kink_recovery():
    np.random.seed(42)
    n = 120
    cutoff = 50.0
    x = np.random.uniform(20.0, 80.0, n)
    # True DGP: left slope = 0.4, right slope = 1.8 => kink = 1.4
    x_c = x - cutoff
    d_kink = np.maximum(0.0, x_c)
    true_tau = 1.4
    y = 25.0 + 0.4 * x_c + true_tau * d_kink + np.random.normal(0, 0.4, n)

    res = RegressionKinkEngine.evaluate_rkd(
        y_outcome=y,
        x_running=x,
        cutoff=cutoff,
        known_kink_slope=1.0,
        outcome_label="Platform Activity Index",
        running_label="Loyalty Score Threshold"
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "REGRESSION_KINK_DESIGN_CARD_2015"
    assert "diagnostics" in res
    diag = res["diagnostics"]
    assert diag["cutoff"] == cutoff
    assert diag["sample_size_total"] == n
    assert diag["effective_sample_size"] > 25

    # Recovery of kink slope
    assert 1.0 <= diag["tau_rkd"] <= 1.8
    assert diag["p_value"] < 0.01
    assert diag["is_statistically_significant"] is True
    assert diag["left_slope"] < diag["right_slope"]
    assert diag["is_density_smooth"] is True  # Uniform distribution has smooth density

    # Visuals & APA
    assert "<svg" in res["svg_visualization"]
    assert "Panel A: Đường Cong Hồi Quy Gãy" in res["svg_visualization"]
    assert "Regression Kink Design" in res["apa_narrative"]
    assert "Card, Lee, Pei, & Weber" in res["apa_narrative"]


def test_generate_rkd_svg_direct():
    svg = generate_rkd_svg(
        bin_x=[40.0, 45.0, 50.0, 55.0, 60.0],
        bin_y=[12.0, 14.5, 17.0, 22.0, 28.0],
        left_x_grid=[35.0, 42.5, 50.0],
        left_y_fit=[9.5, 13.25, 17.0],
        right_x_grid=[50.0, 57.5, 65.0],
        right_y_fit=[17.0, 25.25, 33.5],
        cutoff=50.0,
        tau_rkd=1.10,
        delta_slope=1.10,
        left_slope=0.50,
        right_slope=1.60,
        se_rkd=0.12,
        bandwidth=15.0,
        outcome_label="Trust Rating",
        running_label="Tenure Months",
        mccrary_p=0.48
    )
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "+1.1000" in svg
    assert "Ngưỡng c=50.00" in svg
    assert "McCrary Density Test" in svg
