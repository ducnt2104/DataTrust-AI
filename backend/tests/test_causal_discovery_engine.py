"""
Unit tests for Causal Discovery DAG Engine (LiNGAM & ANM)
"""

import numpy as np
import pytest
from app.engine.causal_discovery_engine import run_causal_discovery


def test_causal_discovery_insufficient_sample():
    # p < 2
    res_small_p = run_causal_discovery(np.random.randn(50, 1), ["Var1"])
    assert res_small_p["status"] == "INSUFFICIENT_SAMPLE"

    # N < 15
    res_small_n = run_causal_discovery(np.random.randn(10, 3), ["Var1", "Var2", "Var3"])
    assert res_small_n["status"] == "INSUFFICIENT_SAMPLE"


def test_causal_discovery_synthetic_dag():
    np.random.seed(42)
    N = 250
    # True causal chain: X0 -> X1 -> X2
    # Non-Gaussian disturbances (Uniform and Exponential)
    e0 = np.random.uniform(-1.5, 1.5, size=N)
    e1 = np.random.exponential(scale=1.0, size=N) - 1.0
    e2 = np.random.uniform(-2.0, 2.0, size=N)

    x0 = e0
    x1 = 0.7 * x0 + e1
    x2 = 0.5 * x1 + e2

    data = np.column_stack([x0, x1, x2])
    varnames = ["PlatformTrust", "SurveyEffort", "DataAccuracy"]

    result = run_causal_discovery(
        data=data,
        variable_names=varnames,
        prune_threshold=0.05,
        seed=42,
    )

    assert result["status"] == "SUCCESS"
    assert result["model_type"] == "CAUSAL_DISCOVERY_LINGAM_ANM"
    assert len(result["causal_order"]) == 3
    assert len(result["directed_edges"]) >= 1
    assert "adjacency_matrix" in result
    assert "svg_visualization" in result
    assert "<svg" in result["svg_visualization"]
    assert "apa_narrative" in result
    assert "Shimizu et al." in result["apa_narrative"]
    assert len(result["non_gaussianity_tests"]) == 3


def test_causal_discovery_with_pruning():
    np.random.seed(123)
    N = 180
    data = np.random.exponential(size=(N, 4))
    varnames = ["A", "B", "C", "D"]

    res = run_causal_discovery(data, varnames, prune_threshold=0.2, seed=123)
    assert res["status"] == "SUCCESS"
    assert res["diagnostics"]["N"] == 180
    assert res["diagnostics"]["p"] == 4
    for edge in res["directed_edges"]:
        assert abs(edge["path_coefficient"]) >= 0.05
