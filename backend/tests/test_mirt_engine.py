# -*- coding: utf-8 -*-
"""
Unit tests for MultidimensionalIRTEngine (backend/app/engine/mirt_engine.py)
"""
import pytest
import numpy as np
from app.engine.mirt_engine import MultidimensionalIRTEngine


def test_mirt_insufficient_sample_and_items():
    res = MultidimensionalIRTEngine.estimate_mirt(
        data=[{"q1": 1, "q2": 0}],
        item_vars=["q1", "q2"]
    )
    assert res["status"] in ["INSUFFICIENT_SAMPLE", "INSUFFICIENT_ITEMS"]


def test_mirt_2d_estimation():
    np.random.seed(42)
    n = 80
    # 2 true latent dimensions: theta1, theta2
    theta1 = np.random.normal(0, 1.0, n)
    theta2 = np.random.normal(0, 1.0, n)

    # 4 items:
    # Item 1: loads primarily on theta1
    # Item 2: loads primarily on theta2
    # Item 3: balanced compensatory
    # Item 4: harder item
    z1 = 1.5 * theta1 + 0.2 * theta2 - 0.5
    z2 = 0.2 * theta1 + 1.4 * theta2 - 0.2
    z3 = 1.0 * theta1 + 1.0 * theta2 + 0.3
    z4 = 0.8 * theta1 + 0.6 * theta2 - 1.2

    data = []
    for i in range(n):
        y1 = 1 if (np.random.uniform() < 1.0 / (1.0 + np.exp(-z1[i]))) else 0
        y2 = 1 if (np.random.uniform() < 1.0 / (1.0 + np.exp(-z2[i]))) else 0
        y3 = 1 if (np.random.uniform() < 1.0 / (1.0 + np.exp(-z3[i]))) else 0
        y4 = 1 if (np.random.uniform() < 1.0 / (1.0 + np.exp(-z4[i]))) else 0
        data.append({"q1": y1, "q2": y2, "q3": y3, "q4": y4})

    res = MultidimensionalIRTEngine.estimate_mirt(
        data=data,
        item_vars=["q1", "q2", "q3", "q4"],
        n_dimensions=2,
        dimension_names=["Năng lực Logic", "Năng lực Ngôn ngữ"],
        max_em_iter=30
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "MULTIDIMENSIONAL_IRT_2PL"

    diag = res["diagnostics"]
    assert diag["n_samples"] == 80
    assert diag["n_items"] == 4
    assert diag["n_dimensions"] == 2
    assert len(diag["eap_trait_means"]) == 2

    items = res["item_parameters"]
    assert len(items) == 4
    for it in items:
        assert it["mdisc"] > 0.1
        assert len(it["directional_angles_deg"]) == 2
        assert "mdisc_classification" in it
        assert "mid" in it

    # Check SVG and narrative
    assert "<svg" in res["svg_visualization"]
    assert "Reckase" in res["apa_narrative"]
    assert "MDISC" in res["apa_narrative"]


def test_mirt_3d_estimation():
    np.random.seed(99)
    n = 60
    th1 = np.random.normal(0, 1.0, n)
    th2 = np.random.normal(0, 1.0, n)
    th3 = np.random.normal(0, 1.0, n)

    data = []
    for i in range(n):
        y1 = 1 if (th1[i] > 0.0) else 0
        y2 = 1 if (th2[i] > 0.0) else 0
        y3 = 1 if (th3[i] > 0.0) else 0
        data.append({"item_a": y1, "item_b": y2, "item_c": y3})

    res = MultidimensionalIRTEngine.estimate_mirt(
        data=data,
        item_vars=["item_a", "item_b", "item_c"],
        n_dimensions=3,
        max_em_iter=15
    )

    assert res["status"] == "SUCCESS"
    assert res["diagnostics"]["n_dimensions"] == 3
    assert len(res["item_parameters"]) == 3
