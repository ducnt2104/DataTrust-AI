"""
Unit tests for Bifactor Psychometric Modeling & Omega Hierarchical Engine.
"""

import numpy as np
import pytest
from app.engine.bifactor_engine import BifactorEngine


def test_bifactor_engine_essential_unidimensionality():
    """
    Verify Bifactor correctly identifies an essentially unidimensional scale (dominant G factor).
    """
    np.random.seed(42)
    N = 300
    P = 6  # 2 subscales of 3 items each

    # Strong general factor G ~ N(0, 1)
    G = np.random.normal(0, 1, N)

    # Moderate specific factors S1, S2 ~ N(0, 1)
    S1 = np.random.normal(0, 1, N)
    S2 = np.random.normal(0, 1, N)

    # Subscale 1 items: dominant G loading (0.85), small S1 loading (0.25)
    data = np.zeros((N, P))
    for i in range(3):
        data[:, i] = 0.85 * G + 0.25 * S1 + np.random.normal(0, 0.4, N)

    # Subscale 2 items: dominant G loading (0.80), small S2 loading (0.30)
    for i in range(3, 6):
        data[:, i] = 0.80 * G + 0.30 * S2 + np.random.normal(0, 0.4, N)

    subscales = {
        "Subscale_A": [0, 1, 2],
        "Subscale_B": [3, 4, 5]
    }

    res = BifactorEngine.estimate(data=data, subscale_assignments=subscales)

    assert res["status"] == "success"
    assert res["omega_hierarchical"] >= 0.75
    assert res["explained_common_variance"] >= 0.60
    assert res["is_essentially_unidimensional"] is True
    assert "Composite Sum Score" in res["recommendation"]
    assert len(res["subscale_metrics"]) == 2
    assert "<svg" in res["svg_chart"]
    assert "Bifactor" in res["apa_narrative"]


def test_bifactor_engine_multidimensional_scale():
    """
    Verify Bifactor flags a scale that is genuinely multidimensional (weak G, strong subscales).
    """
    np.random.seed(101)
    N = 300
    P = 6

    # Weak G, strong S1 and S2
    G = np.random.normal(0, 1, N)
    S1 = np.random.normal(0, 1, N)
    S2 = np.random.normal(0, 1, N)

    data = np.zeros((N, P))
    for i in range(3):
        data[:, i] = 0.25 * G + 0.85 * S1 + np.random.normal(0, 0.3, N)
    for i in range(3, 6):
        data[:, i] = 0.20 * G + 0.85 * S2 + np.random.normal(0, 0.3, N)

    subscales = {
        "Subscale_1": [0, 1, 2],
        "Subscale_2": [3, 4, 5]
    }

    res = BifactorEngine.estimate(data=data, subscale_assignments=subscales)

    assert res["status"] == "success"
    assert res["omega_hierarchical"] < 0.70
    assert res["is_essentially_unidimensional"] is False
    assert "tiểu thang đo riêng biệt" in res["recommendation"]


def test_bifactor_engine_edge_cases():
    """
    Verify error handling on small sample or incomplete subscales.
    """
    data = np.ones((5, 4))
    res = BifactorEngine.estimate(data=data, subscale_assignments={"A": [0, 1], "B": [2, 3]})
    assert res["status"] == "insufficient_data"

    data_ok = np.random.normal(0, 1, (20, 4))
    # Missing item 3 in mapping
    res_bad = BifactorEngine.estimate(data=data_ok, subscale_assignments={"A": [0, 1], "B": [2]})
    assert res_bad["status"] == "invalid_subscales"
