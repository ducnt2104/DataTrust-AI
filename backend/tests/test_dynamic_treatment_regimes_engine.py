# -*- coding: utf-8 -*-
"""
Unit tests for Dynamic Treatment Regimes (DTR) & Sequential Q-Learning Decision Engine
"""
import pytest
import numpy as np
from app.engine.dynamic_treatment_regimes_engine import (
    DynamicTreatmentRegimesEngine,
    generate_dtr_svg
)


def test_dtr_insufficient_sample():
    np.random.seed(42)
    y = np.random.randn(15)
    a1 = np.random.randint(0, 2, 15)
    a2 = np.random.randint(0, 2, 15)
    x1 = np.random.randn(15)
    x2 = np.random.randn(15)

    res = DynamicTreatmentRegimesEngine.evaluate_dtr(
        y_outcome=y,
        a1_stage1=a1,
        a2_stage2=a2,
        x1_baseline=x1,
        x2_interim=x2
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"
    assert "Cần tối thiểu 25" in res["message"]


def test_dtr_two_stage_q_learning_optimization():
    np.random.seed(42)
    n = 120
    x1 = np.random.normal(0, 1, n)
    # Stage 1 action
    a1 = np.random.binomial(1, 0.5, n)
    # Interim state
    x2 = 0.5 * x1 + 0.8 * a1 + np.random.normal(0, 0.5, n)
    # Stage 2 action
    a2 = np.random.binomial(1, 0.5, n)
    # Final outcome with positive interaction A2 * X2
    y = 5.0 + 1.2 * x1 + 0.8 * a1 + 1.5 * x2 + 1.0 * a2 + 2.0 * (a2 * x2) + np.random.normal(0, 0.5, n)

    res = DynamicTreatmentRegimesEngine.evaluate_dtr(
        y_outcome=y,
        a1_stage1=a1,
        a2_stage2=a2,
        x1_baseline=x1,
        x2_interim=x2,
        x1_label="Initial Need Level",
        x2_label="Interim Engagement Score",
        outcome_label="Long-Term Platform Retention"
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "DYNAMIC_TREATMENT_REGIMES_Q_LEARNING_2003"
    assert "diagnostics" in res
    diag = res["diagnostics"]
    assert diag["sample_size"] == n
    assert diag["v_optimal"] >= diag["v_never_treated"]
    assert diag["policy_value_gain"] >= 0.0
    assert 0.0 <= diag["pct_stage1_treated"] <= 1.0
    assert 0.0 <= diag["pct_stage2_treated"] <= 1.0

    # Models
    assert "stage1_model" in res
    assert "stage2_model" in res
    assert res["stage2_model"]["interaction_a2_x2"] > 1.0  # DGP has +2.0

    # Chart & APA
    assert "<svg" in res["svg_visualization"]
    assert "Panel A: Cây Quyết định" in res["svg_visualization"]
    assert "Panel B: Kỳ vọng Kết quả" in res["svg_visualization"]
    assert "Dynamic Treatment Regimes" in res["apa_narrative"]
    assert "Q-Learning" in res["apa_narrative"]


def test_generate_dtr_svg_direct():
    svg = generate_dtr_svg(
        v_optimal=8.45,
        v_always=7.80,
        v_never=5.20,
        v_observed=6.90,
        stage1_tailor_name="Initial Literacy",
        stage1_threshold=0.35,
        stage2_tailor_name="Interim Progress",
        stage2_threshold=1.10,
        pct_stage1_treated=0.62,
        pct_stage2_treated=0.48,
        outcome_label="Final Digital Trust Index"
    )
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "8.450" in svg
    assert "Giai đoạn 1" in svg
    assert "Giai đoạn 2" in svg
