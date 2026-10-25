# -*- coding: utf-8 -*-
"""
Unit tests for SequentialMediationEngine (Hayes Model 6 / Imai & Yamamoto 2013).
"""

import pytest
import numpy as np
from app.engine.sequential_mediation_engine import SequentialMediationEngine


def generate_sequential_mediation_data(
    n_samples: int = 150,
    a1: float = 0.7,
    a2: float = 0.3,
    d21: float = 0.5,
    b1: float = 0.4,
    b2: float = 0.6,
    c_prime: float = 0.5,
    seed: int = 42
):
    rng = np.random.RandomState(seed)
    # Treatment T (Binary or Continuous, e.g. randomized nudge 0 or 1)
    t = rng.binomial(1, 0.5, size=n_samples).astype(float)
    # Exogenous control X
    x = rng.normal(0, 1.0, size=(n_samples, 1))

    # Model 1: M1 = 1.0 + a1 * T + 0.2 * X + e1
    e1 = rng.normal(0, 0.5, size=n_samples)
    m1 = 1.0 + a1 * t + 0.2 * x[:, 0] + e1

    # Model 2: M2 = 0.5 + a2 * T + d21 * M1 + 0.3 * X + e2
    e2 = rng.normal(0, 0.5, size=n_samples)
    m2 = 0.5 + a2 * t + d21 * m1 + 0.3 * x[:, 0] + e2

    # Model 3: Y = 2.0 + c_prime * T + b1 * M1 + b2 * M2 + 0.25 * X + ey
    ey = rng.normal(0, 0.6, size=n_samples)
    y = 2.0 + c_prime * t + b1 * m1 + b2 * m2 + 0.25 * x[:, 0] + ey

    return t, m1, m2, y, x


def test_sequential_mediation_success():
    t, m1, m2, y, x = generate_sequential_mediation_data(
        n_samples=180, a1=0.7, a2=0.3, d21=0.5, b1=0.4, b2=0.6, c_prime=0.5
    )

    res = SequentialMediationEngine.estimate(
        treatment=t,
        mediator1=m1,
        mediator2=m2,
        outcome=y,
        covariates=x,
        n_bootstraps=300,
        alpha_level=0.05,
        treatment_label="Thử nghiệm Nudge",
        mediator1_label="Niềm tin Hệ thống",
        mediator2_label="Sẵn sàng Chia sẻ",
        outcome_label="Mức độ Ứng dụng"
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "SEQUENTIAL_CAUSAL_MEDIATION_HAYES_6"
    assert res["sample_size"] == 180
    assert res["bootstrap_replications"] > 0

    eff = res["effects"]
    assert "direct_effect" in eff
    assert "indirect_path1_m1" in eff
    assert "indirect_path2_m2" in eff
    assert "indirect_sequential_m1_m2" in eff
    assert "indirect_total" in eff
    assert "total_effect" in eff

    # Verify sequential indirect effect is positive and significant
    seq_eff = eff["indirect_sequential_m1_m2"]
    assert seq_eff["estimate"] > 0.05
    assert seq_eff["is_significant"] is True
    assert seq_eff["ci_lower"] > 0.0

    # Verify proportions
    props = res["proportions"]
    assert "proportion_mediated_total" in props
    assert "proportion_mediated_sequential" in props

    # Verify regression equations
    eqs = res["regression_equations"]
    assert len(eqs) == 3
    assert "r_squared" in eqs[0]
    assert "r_squared" in eqs[1]
    assert "r_squared" in eqs[2]

    # Verify SVG and APA Narrative
    assert "<svg" in res["svg_visualization"]
    assert "DataTrust" in res["apa_narrative"]
    assert "Hayes Model 6" in res["apa_narrative"]


def test_sequential_mediation_direct_only():
    # Set a1 = 0, a2 = 0, d21 = 0 -> No mediation
    t, m1, m2, y, x = generate_sequential_mediation_data(
        n_samples=150, a1=0.0, a2=0.0, d21=0.0, b1=0.0, b2=0.0, c_prime=1.2
    )

    res = SequentialMediationEngine.estimate(
        treatment=t,
        mediator1=m1,
        mediator2=m2,
        outcome=y,
        covariates=x,
        n_bootstraps=200
    )

    assert res["status"] == "SUCCESS"
    eff = res["effects"]
    # Direct effect should be significant
    assert eff["direct_effect"]["is_significant"] is True
    # Sequential indirect effect should not be significant (CI covers 0)
    assert eff["indirect_sequential_m1_m2"]["is_significant"] is False


def test_sequential_mediation_insufficient_sample():
    # Only 10 samples
    t = np.ones(10)
    m1 = np.ones(10)
    m2 = np.ones(10)
    y = np.ones(10)
    res = SequentialMediationEngine.estimate(
        treatment=t,
        mediator1=m1,
        mediator2=m2,
        outcome=y
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"
    assert "yêu cầu ít nhất 25 quan sát" in res["message"]


def test_sequential_mediation_mismatched_dimensions():
    t = np.ones(30)
    m1 = np.ones(25)
    m2 = np.ones(30)
    y = np.ones(30)
    res = SequentialMediationEngine.estimate(
        treatment=t,
        mediator1=m1,
        mediator2=m2,
        outcome=y
    )
    assert res["status"] == "ERROR"
    assert "Kích thước mẫu không đồng nhất" in res["message"]
