# -*- coding: utf-8 -*-
"""
Unit tests for PostDoubleSelectionLassoEngine (Belloni, Chernozhukov, & Hansen 2014).
"""

import pytest
import numpy as np
from app.engine.post_double_selection_lasso_engine import PostDoubleSelectionLassoEngine


def generate_pds_data(
    n_samples: int = 140,
    p_controls: int = 15,
    alpha_true: float = 1.85,
    seed: int = 42
):
    rng = np.random.RandomState(seed)
    # Generate candidate controls X
    x = rng.normal(0, 1.0, size=(n_samples, p_controls))

    # Treatment model: D depends on X0, X1, X4, X5
    d_latent = 0.8 * x[:, 0] + 0.6 * x[:, 1] + 0.9 * x[:, 4] + 0.7 * x[:, 5] + rng.normal(0, 0.8, size=n_samples)
    d = (d_latent > np.median(d_latent)).astype(float)  # Binary treatment

    # Outcome model: Y depends on D, X0, X1 (confounders), X2, X3 (outcome drivers)
    # Note: X4 and X5 affect D strongly but Y weakly -> Naive single-lasso might miss them, causing OVB!
    y = alpha_true * d + 1.2 * x[:, 0] + 0.9 * x[:, 1] + 1.5 * x[:, 2] + 1.1 * x[:, 3] + 0.15 * x[:, 4] + rng.normal(0, 0.8, size=n_samples)

    names = [f"Hiệp biến X{i+1}" for i in range(p_controls)]
    return y, d, x, names


def test_pds_lasso_success():
    y, d, x, names = generate_pds_data(n_samples=160, p_controls=16, alpha_true=1.85)

    res = PostDoubleSelectionLassoEngine.estimate(
        y=y,
        treatment=d,
        candidate_controls=x,
        control_names=names,
        cv_folds=5,
        alpha_level=0.05,
        outcome_label="Thu nhập Sau Khóa học",
        treatment_label="Tham gia Khóa Đào tạo"
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "POST_DOUBLE_SELECTION_LASSO_BELLONI_2014"

    diag = res["diagnostics"]
    assert diag["sample_size"] == 160
    assert diag["total_candidate_controls"] == 16
    assert diag["union_selected_controls"] > 0
    assert diag["union_selected_controls"] <= 16

    est = res["estimates"]
    pds = est["post_double_selection_lasso"]
    assert pds["is_significant"] is True
    # Verify true alpha (1.85) is within 95% CI
    assert pds["ci_lower"] <= 1.85 <= pds["ci_upper"]

    # Verify naive and unadjusted comparisons exist
    assert "naive_single_selection_lasso" in est
    assert "unadjusted_base_ols" in est

    # Verify selected controls table
    sel_table = res["selected_controls"]
    assert len(sel_table) == 16
    assert "in_union_set" in sel_table[0]

    # Verify SVG and APA narrative
    assert "<svg" in res["svg_visualization"]
    assert "DataTrust" in res["apa_narrative"]
    assert "Belloni" in res["apa_narrative"]


def test_pds_lasso_insufficient_sample():
    # Only 15 observations
    y = np.ones(15)
    d = np.ones(15)
    x = np.ones((15, 4))
    res = PostDoubleSelectionLassoEngine.estimate(y=y, treatment=d, candidate_controls=x)
    assert res["status"] == "INSUFFICIENT_SAMPLE"
    assert "yêu cầu ít nhất 30 quan sát" in res["message"]


def test_pds_lasso_mismatched_dimensions():
    y = np.ones(50)
    d = np.ones(45)
    x = np.ones((50, 4))
    res = PostDoubleSelectionLassoEngine.estimate(y=y, treatment=d, candidate_controls=x)
    assert res["status"] == "ERROR"
    assert "Kích thước mẫu không đồng nhất" in res["message"]
