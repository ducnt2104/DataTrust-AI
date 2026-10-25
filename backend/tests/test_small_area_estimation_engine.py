"""
Unit tests for Small Area Estimation (SAE) & Fay-Herriot Empirical Bayes Engine.
"""

import pytest
import numpy as np
from app.engine.small_area_estimation_engine import (
    fit_fay_herriot_eblup,
    calculate_small_area_estimation
)


def test_fit_fay_herriot_eblup_basic():
    # 5 areas
    area_names = ["Khu_vuc_1", "Khu_vuc_2", "Khu_vuc_3", "Khu_vuc_4", "Khu_vuc_5"]
    direct_y = np.array([45.0, 52.0, 48.0, 55.0, 50.0])
    # Area 1 has large variance (small n), Area 5 has tiny variance (large n)
    sampling_d = np.array([25.0, 16.0, 9.0, 4.0, 1.0])
    sample_n = np.array([5, 8, 15, 30, 100])

    res = fit_fay_herriot_eblup(
        area_names=area_names,
        direct_estimates=direct_y,
        sampling_variances=sampling_d,
        sample_sizes=sample_n
    )

    assert res["status"] == "SUCCESS"
    assert res["area_count"] == 5
    assert res["between_area_variance_sigma_v2"] >= 0.0
    assert 0.0 <= res["mean_shrinkage_weight_gamma"] <= 1.0
    assert res["mean_efficiency_gain_pct"] >= 0.0

    estimates = {e["area_name"]: e for e in res["area_estimates"]}
    # Area 1 (large variance) should shrink more towards synthetic line (smaller gamma)
    # than Area 5 (tiny variance, larger gamma)
    assert estimates["Khu_vuc_1"]["shrinkage_weight_gamma"] < estimates["Khu_vuc_5"]["shrinkage_weight_gamma"]
    # Area 1 (large sampling variance) should see substantial efficiency gain from shrinkage
    assert estimates["Khu_vuc_1"]["efficiency_gain_pct"] > 10.0
    assert estimates["Khu_vuc_1"]["eblup_se"] < estimates["Khu_vuc_1"]["direct_se"]
    assert res["mean_efficiency_gain_pct"] > 0.0

    assert "<svg" in res["svg_chart"]
    assert "Fay-Herriot" in res["apa_narrative"]


def test_calculate_small_area_estimation_from_rows():
    # Generate individual level survey data across 4 departments
    data_rows = []
    # Dept A: n=4, mean~50
    for val in [48, 52, 49, 51]:
        data_rows.append({"dept": "Dept_A", "score": val, "tenure": 2})
    # Dept B: n=6, mean~60
    for val in [58, 62, 59, 61, 60, 60]:
        data_rows.append({"dept": "Dept_B", "score": val, "tenure": 5})
    # Dept C: n=8, mean~70
    for val in [69, 71, 70, 72, 68, 70, 71, 69]:
        data_rows.append({"dept": "Dept_C", "score": val, "tenure": 8})
    # Dept D: n=10, mean~40
    for val in [38, 42, 39, 41, 40, 40, 39, 41, 40, 40]:
        data_rows.append({"dept": "Dept_D", "score": val, "tenure": 1})

    res = calculate_small_area_estimation(
        data_rows=data_rows,
        area_col="dept",
        outcome_col="score",
        auxiliary_cols=["tenure"]
    )

    assert res["status"] == "SUCCESS"
    assert res["area_count"] == 4
    assert len(res["area_estimates"]) == 4
    assert len(res["regression_coefficients"]) == 2  # Intercept + tenure


def test_small_area_estimation_edge_cases():
    # Empty data
    res_empty = calculate_small_area_estimation([], "area", "score")
    assert res_empty["status"] == "NO_DATA"

    # Only 2 areas
    res_2areas = calculate_small_area_estimation([
        {"area": "A", "score": 10},
        {"area": "A", "score": 12},
        {"area": "B", "score": 20},
        {"area": "B", "score": 22}
    ], "area", "score")
    assert res_2areas["status"] == "INSUFFICIENT_AREAS"
