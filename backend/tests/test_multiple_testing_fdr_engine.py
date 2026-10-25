import pytest
import numpy as np
from app.engine.multiple_testing_fdr_engine import (
    compute_fdr_corrections,
    run_pairwise_fdr_matrix
)


def test_fdr_empty_p_values():
    res = compute_fdr_corrections([])
    assert res["status"] == "error"


def test_fdr_benjamini_hochberg_exact():
    # 4 hypotheses
    p_vals = [0.01, 0.04, 0.03, 0.20]
    labels = ["H1", "H2", "H3", "H4"]

    res = compute_fdr_corrections(p_vals, labels, fdr_q=0.05)
    assert res["status"] == "success"
    assert res["sample_diagnostics"]["total_hypotheses_m"] == 4

    corr = res["corrections"]
    # Sorted order: H1 (0.01), H3 (0.03), H2 (0.04), H4 (0.20)
    assert corr[0]["hypothesis"] == "H1"
    assert corr[0]["rank"] == 1
    assert corr[0]["is_significant_bh"] is True

    # H3: p = 0.03 > (2/4)*0.05 = 0.025, not significant under BH at 0.05
    assert corr[1]["hypothesis"] == "H3"
    assert corr[1]["is_significant_bh"] is False

    assert res["sample_diagnostics"]["bh_fdr_significant_count"] == 1
    assert "<svg" in res["svg_chart"]
    assert "Benjamini & Hochberg" in res["apa_narrative"]


def test_pairwise_fdr_matrix_synthetic():
    np.random.seed(42)
    n = 30
    # Create 3 variables: Q1 and Q2 strongly correlated, Q3 noise
    q1 = np.random.normal(0, 1, n)
    q2 = q1 * 0.9 + np.random.normal(0, 0.2, n)
    q3 = np.random.normal(0, 1, n)

    records = [{"q1": q1[i], "q2": q2[i], "q3": q3[i]} for i in range(n)]

    res = run_pairwise_fdr_matrix(
        records=records,
        question_ids=["q1", "q2", "q3"],
        question_titles={"q1": "Satisfaction", "q2": "Loyalty", "q3": "NoiseVar"},
        fdr_q=0.05
    )

    assert res["status"] == "success"
    # m = 3 * 2 / 2 = 3 pairs
    assert res["sample_diagnostics"]["total_hypotheses_m"] == 3
    assert res["sample_diagnostics"]["bh_fdr_significant_count"] >= 1

    # First pair (Satisfaction <-> Loyalty) should be top rank
    assert "Satisfaction" in res["corrections"][0]["hypothesis"]
    assert res["corrections"][0]["is_significant_bh"] is True
