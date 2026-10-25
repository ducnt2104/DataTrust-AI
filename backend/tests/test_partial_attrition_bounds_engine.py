"""
Unit tests for Partial Identification & Non-Random Attrition Bounds Engine
(Horowitz & Manski 2000; Lee 2009; Manski & Pepper 2000)
DataTrust Iteration 192
"""

import pytest
import numpy as np
from app.engine.partial_attrition_bounds_engine import (
    PartialAttritionBoundsEngine,
    run_partial_attrition_bounds_analysis,
)


def test_partial_attrition_bounds_synthetic():
    np.random.seed(192)
    N = 100

    # Half treated, half control
    d = np.array([1] * 50 + [0] * 50)

    # Latent outcomes: True ATE = 2.0
    y_star = np.where(d == 1, 10.0 + np.random.normal(0, 1.5, N), 8.0 + np.random.normal(0, 1.5, N))

    # Differential attrition: Treatment response rate ~ 85%, Control response rate ~ 60%
    prob_resp = np.where(d == 1, 0.85, 0.60)
    r = np.random.binomial(1, prob_resp, N)

    # Observed outcome (zeros where r=0)
    y_obs = np.where(r == 1, y_star, 0.0)

    res = PartialAttritionBoundsEngine.evaluate(
        treatment=d,
        outcome=y_obs,
        response_indicator=r,
        treatment_name="Treatment",
        outcome_name="Score",
        user_ymin=0.0,
        user_ymax=15.0,
        alpha=0.05,
    )

    assert res["status"] == "success"
    assert res["sample_size"] == 100
    assert res["sample_treatment"] == 50
    assert res["sample_control"] == 50
    assert 0.70 <= res["response_rate_treatment"] <= 1.0
    assert 0.40 <= res["response_rate_control"] <= 0.80

    # Naive complete case
    naive = res["naive_complete_case"]
    assert "ate" in naive
    assert "ci_95" in naive

    # Manski worst-case bounds
    manski = res["manski_horowitz_bounds"]
    assert manski["lower_bound"] < manski["upper_bound"]
    assert manski["interval_width"] > 0
    assert len(manski["imbens_manski_ci_95"]) == 2

    # Lee trimming bounds should be strictly tighter than Manski worst-case bounds
    lee = res["lee_trimming_bounds"]
    assert lee["lower_bound"] < lee["upper_bound"]
    assert lee["interval_width"] < manski["interval_width"]
    assert lee["lower_bound"] >= manski["lower_bound"]
    assert lee["upper_bound"] <= manski["upper_bound"]

    # MTS bounds
    mts = res["mts_bounds"]
    assert mts["upper_bound"] <= manski["upper_bound"]

    # Sensitivity grid
    sens = res["sensitivity_grid"]
    assert len(sens) == 25

    # SVG & APA
    assert "<svg" in res["svg_visualization"]
    assert "</svg>" in res["svg_visualization"]
    assert "Panel A:" in res["svg_visualization"]
    assert "Panel B:" in res["svg_visualization"]
    assert len(res["apa_narrative"]) > 100
    assert "Horowitz & Manski" in res["apa_narrative"]
    assert "Lee (2009)" in res["apa_narrative"]


def test_partial_attrition_helper_records():
    records = []
    for i in range(40):
        t_val = 1 if i % 2 == 0 else 0
        # When i % 5 == 0, outcome is missing (attrited)
        if i % 5 == 0:
            y_val = None
        else:
            y_val = 5.0 + 2.0 * t_val + float(np.random.normal(0, 0.5))

        records.append({
            "treat": str(t_val),
            "score": str(round(y_val, 2)) if y_val is not None else "",
        })

    res = run_partial_attrition_bounds_analysis(
        records=records,
        treatment_col="treat",
        outcome_col="score",
        user_ymin=0.0,
        user_ymax=12.0,
    )
    assert res["status"] == "success"
    assert res["sample_size"] == 40
    assert res["overall_attrition_rate"] > 0.10


def test_partial_attrition_sample_size_error():
    records = [{"treat": "1", "score": "5.0"} for _ in range(10)]
    with pytest.raises(ValueError, match="Không đủ dữ liệu hợp lệ"):
        run_partial_attrition_bounds_analysis(records, "treat", "score")


def test_partial_attrition_bounds_order_error():
    t = np.array([1] * 15 + [0] * 15)
    y = np.random.normal(5, 1, 30)
    r = np.ones(30)
    with pytest.raises(ValueError, match="phải nhỏ hơn"):
        PartialAttritionBoundsEngine.evaluate(
            treatment=t,
            outcome=y,
            response_indicator=r,
            user_ymin=10.0,
            user_ymax=5.0,
        )
