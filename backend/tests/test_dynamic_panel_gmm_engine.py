# -*- coding: utf-8 -*-
"""
Unit tests for DynamicPanelGMMEngine (Arellano-Bond 1991, Blundell-Bond 1998, Windmeijer 2005).
"""

import pytest
import numpy as np
from app.engine.dynamic_panel_gmm_engine import DynamicPanelGMMEngine


def generate_synthetic_panel(
    n_units: int = 35,
    n_waves: int = 4,
    true_alpha: float = 0.5,
    true_beta: float = 0.8,
    seed: int = 42
):
    rng = np.random.RandomState(seed)
    records = []
    for i in range(n_units):
        u_i = rng.normal(0, 1.0)
        y_prev = rng.normal(0, 1.0)
        for t in range(n_waves):
            x_it = rng.normal(1.0, 0.5)
            eps_it = rng.normal(0, 0.5)
            y_it = true_alpha * y_prev + true_beta * x_it + u_i + eps_it
            records.append({
                "unit_id": f"unit_{i}",
                "wave": t + 1,
                "satisfaction": float(y_it),
                "feature_usage": float(x_it)
            })
            y_prev = y_it
    return records


def test_dynamic_panel_system_gmm_success():
    data = generate_synthetic_panel(n_units=40, n_waves=4, true_alpha=0.5, true_beta=0.7)
    res = DynamicPanelGMMEngine.estimate(
        panel_data=data,
        unit_id_col="unit_id",
        time_col="wave",
        outcome_col="satisfaction",
        covariate_cols=["feature_usage"],
        method="system",
        two_step=True,
        windmeijer_correction=True
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "DYNAMIC_PANEL_SYSTEM_GMM"
    diag = res["diagnostics"]
    assert diag["num_panel_units"] == 40
    assert diag["time_waves"] == 4
    assert diag["method"] == "system"
    assert diag["two_step"] is True
    assert diag["windmeijer_correction"] is True
    assert diag["instrument_count"] > 0
    assert "alpha_gmm" in diag
    assert "alpha_ols_bound" in diag
    assert "alpha_fe_bound" in diag
    assert "ar1_p_value" in diag
    assert "ar2_p_value" in diag
    assert "hansen_j_statistic" in diag
    assert "hansen_p_value" in diag

    params = res["parameters"]
    assert len(params) == 2  # L1.satisfaction, feature_usage
    assert params[0]["parameter"] == "L1.satisfaction"
    assert params[1]["parameter"] == "feature_usage"
    assert "estimate" in params[0]
    assert "std_error" in params[0]
    assert "p_value" in params[0]

    assert "<svg" in res["svg_visualization"]
    assert "DataTrust" in res["apa_narrative"] or "Dynamic Panel" in res["apa_narrative"]


def test_dynamic_panel_difference_gmm():
    data = generate_synthetic_panel(n_units=30, n_waves=4, true_alpha=0.4, true_beta=0.6)
    res = DynamicPanelGMMEngine.estimate(
        panel_data=data,
        unit_id_col="unit_id",
        time_col="wave",
        outcome_col="satisfaction",
        covariate_cols=["feature_usage"],
        method="difference",
        two_step=False,
        windmeijer_correction=False
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "DYNAMIC_PANEL_DIFFERENCE_GMM"
    diag = res["diagnostics"]
    assert diag["two_step"] is False
    assert diag["windmeijer_correction"] is False
    assert len(res["parameters"]) == 2
    assert "<svg" in res["svg_visualization"]


def test_dynamic_panel_insufficient_sample():
    # Only 5 units
    data = generate_synthetic_panel(n_units=5, n_waves=3)
    res = DynamicPanelGMMEngine.estimate(
        panel_data=data,
        unit_id_col="unit_id",
        time_col="wave",
        outcome_col="satisfaction"
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"
    assert "requires at least 15 panel units" in res["message"]


def test_dynamic_panel_missing_values_handled():
    data = generate_synthetic_panel(n_units=25, n_waves=4)
    # Inject some corrupt rows
    data.append({"unit_id": "unit_99", "wave": None, "satisfaction": 1.2})
    data.append({"unit_id": "unit_98", "wave": 1, "satisfaction": "corrupt_string"})
    res = DynamicPanelGMMEngine.estimate(
        panel_data=data,
        unit_id_col="unit_id",
        time_col="wave",
        outcome_col="satisfaction"
    )
    assert res["status"] == "SUCCESS"
    assert res["diagnostics"]["num_panel_units"] == 25
