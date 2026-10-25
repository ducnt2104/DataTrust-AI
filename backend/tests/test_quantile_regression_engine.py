import pytest
import numpy as np
from app.engine.quantile_regression_engine import QuantileRegressionEngine


def test_quantile_regression_heteroskedastic_data():
    """Kiểm thử hồi quy phân vị với dữ liệu có phương sai thay đổi (Heteroskedasticity)."""
    np.random.seed(42)
    n = 100
    x = np.random.uniform(1.0, 10.0, n)
    # Phương sai của nhiễu tăng dần theo X: y = 2.0 + 1.0 * x + (0.5 * x) * error
    # Ở phân vị thấp, tác động nhỏ; ở phân vị cao, tác động rất lớn
    noise = np.random.normal(0, 1.0, n)
    y = 2.0 + 1.0 * x + (0.4 * x) * noise

    data_rows = [{"x": float(x[i]), "y": float(y[i])} for i in range(n)]

    res = QuantileRegressionEngine.fit_quantile_regression(
        data_rows=data_rows,
        predictor_key="x",
        outcome_key="y",
        quantiles=[0.10, 0.25, 0.50, 0.75, 0.90],
        labels={"x": "Số giờ đào tạo", "y": "Điểm kiểm tra"}
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == n
    assert len(res["quantile_estimates"]) == 5
    assert "ols_baseline" in res
    assert "heterogeneity_test" in res
    
    # Do phương sai tăng theo X, hệ số tại tau=0.90 phải lớn hơn tại tau=0.10
    slope_010 = res["quantile_estimates"][0]["slope"]
    slope_090 = res["quantile_estimates"][-1]["slope"]
    assert slope_090 > slope_010
    assert res["heterogeneity_test"]["slope_difference"] > 0
    assert "svg_process_plot" in res
    assert "<svg" in res["svg_process_plot"]
    assert "apa_narrative" in res
    assert "Koenker & Bassett" in res["apa_narrative"]


def test_quantile_regression_with_covariates():
    """Kiểm thử hồi quy phân vị có kèm biến đồng biến kiểm soát."""
    np.random.seed(123)
    n = 70
    x = np.random.uniform(0, 5, n)
    cov = np.random.uniform(10, 20, n)
    y = 5.0 + 2.0 * x + 0.3 * cov + np.random.normal(0, 1.0, n)

    data_rows = [{"x": float(x[i]), "y": float(y[i]), "c": float(cov[i])} for i in range(n)]

    res = QuantileRegressionEngine.fit_quantile_regression(
        data_rows=data_rows,
        predictor_key="x",
        outcome_key="y",
        covariate_keys=["c"],
        quantiles=[0.25, 0.50, 0.75]
    )

    assert res["status"] == "SUCCESS"
    assert res["covariates_count"] == 1
    assert len(res["quantile_estimates"]) == 3
    # Trung vị slope xấp xỉ 2.0
    med_est = res["quantile_estimates"][1]
    assert 1.0 < med_est["slope"] < 3.0


def test_quantile_regression_edge_cases():
    # 1. Cỡ mẫu quá nhỏ < 16
    res_few = QuantileRegressionEngine.fit_quantile_regression(
        data_rows=[{"x": i, "y": i} for i in range(10)],
        predictor_key="x",
        outcome_key="y"
    )
    assert res_few["status"] == "INSUFFICIENT_SAMPLE"
