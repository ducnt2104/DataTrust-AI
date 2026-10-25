import pytest
from app.engine.regression_engine import RegressionEngine

def test_simple_ols_perfect_fit():
    # y = 2 + 3*x
    x = [[1.0], [2.0], [3.0], [4.0], [5.0], [6.0]]
    y = [5.0, 8.0, 11.0, 14.0, 17.0, 20.0]

    res = RegressionEngine.fit_ols(
        X_matrix=x,
        y_vector=y,
        predictor_labels=["VAR_X"],
        predictor_titles=["Biến Độc Lập X"],
        dependent_title="Biến Phụ Thuộc Y"
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == 6
    assert res["predictors_count"] == 1
    assert abs(res["model_summary"]["r_squared"] - 1.0) < 1e-4
    assert res["model_summary"]["is_significant_05"] is True

    # Coefficients: Intercept = 2.0, B = 3.0
    coeffs = res["coefficients"]
    assert len(coeffs) == 2
    assert abs(coeffs[0]["b_unstandardized"] - 2.0) < 1e-3
    assert abs(coeffs[1]["b_unstandardized"] - 3.0) < 1e-3
    assert coeffs[1]["vif"] == 1.0

def test_multiple_ols_vif_and_significance():
    # 2 predictors: x1, x2 (độc lập tương đối), y = 1.5 + 2.0*x1 - 1.0*x2 + noise
    # 10 mẫu
    x = [
        [1.0, 5.0],
        [2.0, 4.0],
        [3.0, 6.0],
        [4.0, 2.0],
        [5.0, 1.0],
        [6.0, 3.0],
        [7.0, 2.0],
        [8.0, 1.0],
        [9.0, 4.0],
        [10.0, 2.0]
    ]
    # y = 1.5 + 2*x1 - 1*x2
    y = [
        1.5 + 2*r[0] - 1*r[1] for r in x
    ]

    res = RegressionEngine.fit_ols(
        X_matrix=x,
        y_vector=y,
        predictor_labels=["X1", "X2"],
        predictor_titles=["Biến X1", "Biến X2"],
        dependent_title="Mục Tiêu Y"
    )

    assert res["status"] == "SUCCESS"
    assert res["predictors_count"] == 2
    assert res["model_summary"]["r_squared"] > 0.95
    assert res["multicollinearity_risk"] == "LOW"

    # Kiểm tra VIF cho cả 2 biến
    for c in res["coefficients"][1:]:
        assert c["vif"] < 5.0
        assert c["tolerance"] > 0.20

    # Diễn giải APA 7th
    assert "R²" in res["apa_interpretation"]
    assert "F(" in res["apa_interpretation"]

def test_insufficient_sample_defense():
    # p = 3, N = 3 (N <= p + 1)
    x = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]
    y = [10.0, 20.0, 30.0]
    res = RegressionEngine.fit_ols(
        X_matrix=x,
        y_vector=y,
        predictor_labels=["A", "B", "C"],
        predictor_titles=["A", "B", "C"],
        dependent_title="Y"
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"
