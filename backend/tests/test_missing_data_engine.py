import pytest
import numpy as np
from app.engine.missing_data_engine import MissingDataEngine

def test_missing_data_engine_complete_data():
    data = [
        {"q1": 4.0, "q2": 5.0, "q3": 3.0},
        {"q1": 3.0, "q2": 4.0, "q3": 2.0},
        {"q1": 5.0, "q2": 5.0, "q3": 4.0},
        {"q1": 2.0, "q2": 3.0, "q3": 1.0},
        {"q1": 4.0, "q2": 4.0, "q3": 3.0},
    ]
    vars = ["q1", "q2", "q3"]

    diag = MissingDataEngine.diagnose_missing_patterns(data, vars)
    assert diag["status"] == "OK"
    assert diag["complete_cases_count"] == 5
    assert diag["incomplete_cases_count"] == 0
    assert diag["overall_missing_rate"] == 0.0
    assert diag["patterns_count"] == 1
    assert diag["littles_mcar_test"]["applicable"] is False

    imp = MissingDataEngine.impute_missing_data(data, vars, method="mean")
    assert imp["status"] == "NO_MISSING_DATA"
    assert imp["imputed_cells_count"] == 0

def test_missing_data_engine_diagnostics_with_missingness():
    data = [
        {"q1": 5.0, "q2": 4.0, "q3": 5.0},
        {"q1": 4.0, "q2": None, "q3": 4.0},
        {"q1": 3.0, "q2": 3.0, "q3": None},
        {"q1": 5.0, "q2": 5.0, "q3": 5.0},
        {"q1": None, "q2": 2.0, "q3": 2.0},
        {"q1": 2.0, "q2": 1.0, "q3": 1.0},
        {"q1": 4.0, "q2": 4.0, "q3": 3.0},
        {"q1": 5.0, "q2": None, "q3": 4.0},
    ]
    vars = ["q1", "q2", "q3"]

    diag = MissingDataEngine.diagnose_missing_patterns(data, vars)
    assert diag["status"] == "OK"
    assert diag["sample_size"] == 8
    assert diag["total_cells"] == 24
    assert diag["total_missing_cells"] == 4
    assert diag["overall_missing_rate"] > 0
    assert diag["complete_cases_count"] == 4
    assert diag["incomplete_cases_count"] == 4

    # Little's MCAR
    mcar = diag["littles_mcar_test"]
    assert mcar["applicable"] is True
    assert mcar["chi_square"] is not None
    assert mcar["p_value"] is not None
    assert "apa_writeup" in mcar
    assert "χ²" in mcar["apa_writeup"]

def test_missing_data_engine_imputation_methods():
    data = [
        {"q1": 5.0, "q2": 4.0, "q3": 5.0},
        {"q1": 4.0, "q2": None, "q3": 4.0},
        {"q1": 3.0, "q2": 3.0, "q3": None},
        {"q1": 5.0, "q2": 5.0, "q3": 5.0},
        {"q1": None, "q2": 2.0, "q3": 2.0},
        {"q1": 2.0, "q2": 1.0, "q3": 1.0},
        {"q1": 4.0, "q2": 4.0, "q3": 3.0},
        {"q1": 5.0, "q2": None, "q3": 4.0},
    ]
    vars = ["q1", "q2", "q3"]

    for method in ["mean", "median", "hot_deck", "em", "pmm"]:
        res = MissingDataEngine.impute_missing_data(
            data,
            vars,
            method=method,
            discrete_bounds={"q1": (1.0, 5.0), "q2": (1.0, 5.0), "q3": (1.0, 5.0)}
        )
        assert res["status"] == "OK"
        assert res["imputed_cells_count"] == 4
        assert len(res["comparison"]) == 3
        assert "apa_writeup" in res
        sample = res["imputed_data_sample"]
        assert len(sample) == 8
        # Ensure no None or NaN in imputed values
        for row in sample:
            for v in vars:
                val = row[v]
                assert val is not None
                assert 1.0 <= val <= 5.0

def test_missing_data_engine_edge_cases():
    diag_empty = MissingDataEngine.diagnose_missing_patterns([], [])
    assert diag_empty["status"] == "EMPTY_DATA"

    imp_empty = MissingDataEngine.impute_missing_data([], [])
    assert imp_empty["status"] == "EMPTY_DATA"
