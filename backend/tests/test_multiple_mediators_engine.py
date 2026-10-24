import pytest
import numpy as np
from app.engine.multiple_mediators_engine import MultipleMediatorsEngine


def test_multiple_mediators_synthetic_data():
    np.random.seed(42)
    n = 150
    # Simulate causal chain: X -> M1 -> M2 -> Y
    x = np.random.normal(0, 1.0, n)
    m1 = 0.6 * x + np.random.normal(0, 0.4, n)
    m2 = 0.4 * x + 0.5 * m1 + np.random.normal(0, 0.4, n)
    y = 0.8 * x + 0.7 * m1 + 0.9 * m2 + np.random.normal(0, 0.4, n)

    res = MultipleMediatorsEngine.evaluate(
        x=x,
        m1=m1,
        m2=m2,
        y=y,
        n_bootstraps=150,
        x_label="Chính sách X",
        m1_label="Niềm tin M1",
        m2_label="Sự hài lòng M2",
        y_label="Lòng trung thành Y"
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "MULTIPLE_SEQUENTIAL_MEDIATORS_VANDERWEELE_2014"
    diag = res["diagnostics"]
    assert diag["sample_size"] == n
    assert diag["total_effect"] > 0
    assert diag["direct_effect"] > 0
    assert diag["total_indirect_effect"] > 0
    assert diag["nie_m1"] > 0
    assert diag["nie_m2"] > 0
    assert diag["nie_seq"] > 0
    assert diag["proportion_mediated_pct"] > 0

    assert len(res["path_coefficients"]) == 6
    assert len(res["effects_summary"]) == 6
    assert "<svg" in res["svg_visualization"]
    assert "Sequential Multiple Mediation" in res["apa_narrative"] or "Trung gian Causal Đa biến Tuần tự" in res["apa_narrative"]


def test_multiple_mediators_insufficient_sample():
    x = np.array([1.0, 2.0, 3.0])
    m1 = np.array([1.0, 2.0, 3.0])
    m2 = np.array([1.0, 2.0, 3.0])
    y = np.array([1.0, 2.0, 3.0])

    res = MultipleMediatorsEngine.evaluate(x, m1, m2, y)
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_multiple_mediators_zero_variance():
    n = 30
    x = np.ones(n)  # zero variance
    m1 = np.random.normal(0, 1, n)
    m2 = np.random.normal(0, 1, n)
    y = np.random.normal(0, 1, n)

    res = MultipleMediatorsEngine.evaluate(x, m1, m2, y)
    assert res["status"] == "ZERO_VARIANCE"
