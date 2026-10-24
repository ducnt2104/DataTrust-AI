# -*- coding: utf-8 -*-
"""
Unit tests for Finite Mixture Rasch Models (FMRM) & Latent Class IRT Engine
"""
import pytest
import numpy as np
from app.engine.finite_mixture_rasch_engine import (
    FiniteMixtureRaschEngine,
    generate_fmrm_svg
)


def test_fmrm_insufficient_sample():
    x = np.random.randint(0, 2, (15, 4))
    res = FiniteMixtureRaschEngine.evaluate_fmrm(
        responses_matrix=x,
        item_labels=["Item 1", "Item 2", "Item 3", "Item 4"],
        n_classes=2
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"
    assert "Cần tối thiểu 30" in res["message"]


def test_fmrm_insufficient_items():
    x = np.random.randint(0, 2, (40, 2))
    res = FiniteMixtureRaschEngine.evaluate_fmrm(
        responses_matrix=x,
        item_labels=["Item 1", "Item 2"],
        n_classes=2
    )
    assert res["status"] == "INSUFFICIENT_ITEMS"


def test_fmrm_two_class_estimation():
    np.random.seed(42)
    n_per_class = 50
    # Class 1: endorses item 0, 1 easily, item 3, 4 difficult
    p_c1 = [0.85, 0.80, 0.50, 0.20, 0.15]
    # Class 2: endorses item 3, 4 easily, item 0, 1 difficult
    p_c2 = [0.20, 0.25, 0.50, 0.80, 0.85]

    x1 = np.array([np.random.binomial(1, p_c1) for _ in range(n_per_class)])
    x2 = np.array([np.random.binomial(1, p_c2) for _ in range(n_per_class)])
    x = np.vstack([x1, x2])

    item_names = [
        "Q1: Tốc độ xử lý",
        "Q2: Tính bảo mật",
        "Q3: Hỗ trợ kỹ thuật",
        "Q4: Giao diện trực quan",
        "Q5: Chi phí tối ưu"
    ]

    res = FiniteMixtureRaschEngine.evaluate_fmrm(
        responses_matrix=x,
        item_labels=item_names,
        n_classes=2,
        max_iter=40
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "FINITE_MIXTURE_RASCH_ROST_1990"
    assert "diagnostics" in res
    diag = res["diagnostics"]
    assert diag["n_classes"] == 2
    assert diag["n_items"] == 5
    assert diag["sample_size_total"] == 100
    assert diag["sample_size"] >= 95
    assert 0.0 <= diag["entropy"] <= 1.0
    assert diag["entropy"] > 0.40  # Well-separated synthetic classes

    # Proportions
    assert len(res["class_proportions"]) == 2
    p_sum = sum(cp["proportion"] for cp in res["class_proportions"])
    assert p_sum == pytest.approx(1.0, abs=1e-3)

    # Items
    assert len(res["items_parameters"]) == 5
    assert "beta_class_1" in res["items_parameters"][0]
    assert "beta_class_2" in res["items_parameters"][0]

    # Visuals & Narrative
    assert "<svg" in res["svg_visualization"]
    assert "Panel A: Quỹ đạo Độ khó" in res["svg_visualization"]
    assert "Finite Mixture Rasch Model" in res["apa_narrative"]
    assert "Entropy" in res["apa_narrative"]


def test_generate_fmrm_svg_direct():
    svg = generate_fmrm_svg(
        item_labels=["I1", "I2", "I3", "I4"],
        class_difficulties=[[-1.2, -0.4, 0.5, 1.1], [1.0, 0.6, -0.3, -1.3]],
        class_proportions=[0.55, 0.45],
        class_names=["Class A", "Class B"],
        entropy=0.88,
        bic=524.2
    )
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "Class A (55.0%)" in svg
    assert "0.880" in svg
