# -*- coding: utf-8 -*-
"""
Unit tests for Double / Debiased Machine Learning (DML) Engine
"""
import pytest
import numpy as np
from app.engine.double_machine_learning_engine import (
    DoubleMachineLearningEngine,
    generate_dml_svg
)


def test_dml_insufficient_sample():
    y = np.random.randn(20)
    d = np.random.randn(20)
    x = np.random.randn(20, 3)

    res = DoubleMachineLearningEngine.evaluate_dml(
        y_outcome=y,
        d_treatment=d,
        x_covariates=x,
        covariate_names=["X1", "X2", "X3"],
        n_folds=3
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"
    assert "Cần tối thiểu 30" in res["message"]


def test_dml_causal_effect_recovery():
    np.random.seed(42)
    n = 120
    x = np.random.normal(0, 1, (n, 3))
    # Treatment D is confounded by X1 and X2
    d = 0.8 * x[:, 0] - 0.7 * x[:, 1] + np.random.normal(0, 0.5, n)
    # Outcome Y has true causal effect theta_0 = 2.0
    true_theta = 2.0
    y = true_theta * d + 1.5 * x[:, 0] + 1.2 * x[:, 1] + 0.5 * x[:, 2] + np.random.normal(0, 0.5, n)

    res = DoubleMachineLearningEngine.evaluate_dml(
        y_outcome=y,
        d_treatment=d,
        x_covariates=x,
        covariate_names=["Age", "Income", "Prior Usage"],
        n_folds=5,
        outcome_label="Customer Retention Index",
        treatment_label="Premium Feature Access"
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "DOUBLE_MACHINE_LEARNING_CHERNOZHUKOV_2018"
    assert "diagnostics" in res
    diag = res["diagnostics"]
    assert diag["sample_size"] == n
    assert diag["n_covariates"] == 3
    assert diag["n_folds"] == 5

    # Causal effect recovery
    assert 1.6 <= diag["theta_dml"] <= 2.4
    assert diag["p_value"] < 0.01
    assert diag["is_statistically_significant"] is True
    assert diag["ci_lower_95"] < diag["theta_dml"] < diag["ci_upper_95"]

    # Confounding ranking
    assert len(res["confounding_covariates"]) == 3
    assert res["confounding_covariates"][0]["confounding_score"] > 0.0

    # Visuals & APA
    assert "<svg" in res["svg_visualization"]
    assert "Panel A: Đám mây Thặng dư" in res["svg_visualization"]
    assert "Double / Debiased Machine Learning" in res["apa_narrative"]
    assert "Chernozhukov" in res["apa_narrative"]


def test_generate_dml_svg_direct():
    np.random.seed(42)
    res_d = np.random.randn(80)
    res_y = 1.8 * res_d + np.random.randn(80) * 0.4
    svg = generate_dml_svg(
        theta_dml=1.82,
        se_dml=0.15,
        ci_lower=1.52,
        ci_upper=2.12,
        theta_naive=2.95,
        se_naive=0.22,
        res_d=res_d,
        res_y=res_y,
        outcome_label="Net Promoter Score",
        treatment_label="VIP Status",
        r2_y=0.45,
        r2_d=0.38
    )
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "+1.820" in svg
    assert "+2.950" in svg
    assert "Panel B: So sánh Hiệu ứng" in svg
