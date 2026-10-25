"""
Unit tests for Panel Vector Autoregression (PVAR) & Granger Causality Engine.
"""

import numpy as np
import pytest
from app.engine.panel_var_engine import PanelVAREngine


def test_panel_var_unidirectional_granger_causality():
    """
    Verify PVAR correctly detects unidirectional Granger causality: Var1 -> Var2.
    """
    np.random.seed(42)
    N_units = 10
    T_periods = 6

    panel_rows = []
    for u in range(N_units):
        unit_name = f"Unit_{u+1}"
        u_fixed_1 = np.random.normal(0, 1)
        u_fixed_2 = np.random.normal(0, 1)

        v1_prev = 10.0 + u_fixed_1
        v2_prev = 20.0 + u_fixed_2

        for t in range(T_periods):
            # Var1 is independent AR(1): v1_t = 0.5 * v1_{t-1} + u_fixed_1 + eps1
            v1_curr = 0.5 * v1_prev + 0.3 * u_fixed_1 + np.random.normal(0, 0.4)
            # Var2 is driven by lagged Var1: v2_t = 0.4 * v2_{t-1} + 0.8 * v1_{t-1} + u_fixed_2 + eps2
            v2_curr = 0.4 * v2_prev + 0.8 * v1_prev + 0.3 * u_fixed_2 + np.random.normal(0, 0.4)

            panel_rows.append({
                "unit": unit_name,
                "time": t + 1,
                "trust": v1_curr,
                "loyalty": v2_curr
            })

            v1_prev = v1_curr
            v2_prev = v2_curr

    res = PanelVAREngine.estimate(
        panel_rows=panel_rows,
        unit_col="unit",
        time_col="time",
        var1_col="trust",
        var2_col="loyalty"
    )

    assert res["status"] == "success"
    assert res["panel_units_count"] == 10
    assert res["is_stable"] is True
    assert res["stability_max_modulus"] < 1.0

    # Var1 -> Var2 should be significant
    assert res["granger_causality"]["var1_causes_var2"]["is_significant"] is True
    assert res["granger_causality"]["var1_causes_var2"]["p_value"] < 0.05

    # Var2 -> Var1 should NOT be significant (or substantially weaker)
    p_2_to_1 = res["granger_causality"]["var2_causes_var1"]["p_value"]
    p_1_to_2 = res["granger_causality"]["var1_causes_var2"]["p_value"]
    assert p_1_to_2 < p_2_to_1

    # OIRF and SVG chart checks
    assert len(res["oirf_trajectory"]["response_of_var2_to_var1"]) == 7
    assert "<svg" in res["svg_chart"]
    assert "Panel VAR" in res["apa_narrative"]


def test_panel_var_insufficient_data():
    """
    Verify graceful error handling on small or invalid panel data.
    """
    rows = [{"unit": "U1", "time": 1, "v1": 1.0, "v2": 2.0}]
    res = PanelVAREngine.estimate(rows, "unit", "time", "v1", "v2")
    assert res["status"] == "insufficient_data"
    assert "tối thiểu 15 bản ghi" in res["message"]
