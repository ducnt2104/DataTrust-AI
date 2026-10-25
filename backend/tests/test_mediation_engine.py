import pytest
import math
import random

try:
    from app.engine.mediation_engine import MediationEngine
except ModuleNotFoundError:
    from backend.app.engine.mediation_engine import MediationEngine


def test_simple_regression_fit():
    """Kiểm tra độ chính xác của hàm hồi quy đơn biến OLS"""
    random.seed(42)
    # y = 2.0 + 1.5 * x + noise
    x = [float(i) for i in range(1, 31)]
    y = [2.0 + 1.5 * xi + random.uniform(-0.5, 0.5) for xi in x]

    res = MediationEngine.fit_simple_regression(x, y)
    assert res["status"] == "OK"
    assert res["n"] == 30
    assert abs(res["slope"] - 1.5) < 0.2
    assert abs(res["intercept"] - 2.0) < 1.0
    assert res["r_squared"] > 0.95
    assert res["p_value"] < 0.001
    assert res["t_stat"] > 10.0


def test_full_mediation_simulation():
    """
    Kiểm định trường hợp Trung gian Toàn phần (Full Mediation):
    X -> M -> Y. Khi có M trong mô hình, tác động trực tiếp c' bị triệt tiêu về 0.
    """
    random.seed(123)
    n = 100
    x_data = [float(random.gauss(10, 2)) for _ in range(n)]
    # Path a: M = 2.0 + 0.8 * X + e
    m_data = [2.0 + 0.8 * xi + random.gauss(0, 0.5) for xi in x_data]
    # Path b: Y = 1.0 + 0.7 * M + e (Không có tác động trực tiếp từ X)
    y_data = [1.0 + 0.7 * mi + random.gauss(0, 0.5) for mi in m_data]

    res = MediationEngine.analyze_mediation(
        x_data=x_data,
        m_data=m_data,
        y_data=y_data,
        x_label="Chất lượng giao diện (X)",
        m_label="Độ tin cậy người dùng (M)",
        y_label="Ý định gắn bó (Y)",
        bootstrap_samples=500
    )

    assert res["status"] == "OK"
    assert res["sample_size"] == n
    assert len(res["steps"]) == 3

    # Step 1: Total effect c có ý nghĩa
    assert res["steps"][0]["is_significant"] is True
    # Step 2: Path a có ý nghĩa
    assert res["steps"][1]["is_significant"] is True
    assert res["steps"][1]["coefficient"] > 0.6
    # Step 3: Path b có ý nghĩa
    assert res["steps"][2]["path_b"]["is_significant"] is True

    # Indirect effect a * b
    indirect = res["effects_summary"]["indirect_effect_ab"]
    assert indirect > 0.3

    # Sobel test
    sobel = res["significance_tests"]["sobel_test"]
    assert sobel["is_significant"] is True
    assert sobel["p_value"] < 0.01

    # Bootstrap 95% CI không chứa 0
    boot = res["significance_tests"]["bootstrap_resampling"]
    assert boot["is_significant"] is True
    assert boot["ci_lower"] > 0.0

    # Phân loại trung gian (Full Mediation hoặc Complementary Partial)
    conclusion = res["conclusion"]
    assert conclusion["mediation_type"] in ["FULL_MEDIATION", "COMPLEMENTARY_PARTIAL_MEDIATION"]
    assert res["effects_summary"]["vaf_percent"] > 50.0

    # Diagram nodes & paths đầy đủ
    diagram = res["diagram"]
    assert len(diagram["nodes"]) == 3
    assert len(diagram["paths"]) == 4


def test_direct_only_non_mediation():
    """
    Kiểm định trường hợp Chỉ có tác động trực tiếp (Direct-only Non-Mediation):
    X tác động mạnh lên Y, nhưng M là biến độc lập không liên quan (nhiễu).
    """
    random.seed(999)
    n = 80
    x_data = [float(random.uniform(1, 10)) for _ in range(n)]
    # M là biến ngẫu nhiên độc lập với X
    m_data = [float(random.uniform(20, 50)) for _ in range(n)]
    # Y phụ thuộc hoàn toàn vào X
    y_data = [5.0 + 2.0 * xi + random.gauss(0, 0.8) for xi in x_data]

    res = MediationEngine.analyze_mediation(
        x_data=x_data,
        m_data=m_data,
        y_data=y_data,
        x_label="Độ tuổi (X)",
        m_label="Nhiệt độ phòng (M)",
        y_label="Điểm khảo sát (Y)",
        bootstrap_samples=300
    )

    assert res["status"] == "OK"
    # Sobel test không có ý nghĩa
    sobel = res["significance_tests"]["sobel_test"]
    assert sobel["is_significant"] is False

    # Bootstrap CI chứa 0
    boot = res["significance_tests"]["bootstrap_resampling"]
    assert (boot["ci_lower"] <= 0 <= boot["ci_upper"])

    # Kết luận là Direct-only hoặc Inconclusive
    assert res["conclusion"]["mediation_type"] in ["DIRECT_ONLY", "INCONCLUSIVE", "NO_EFFECT"]


def test_insufficient_sample_and_errors():
    """Kiểm tra xử lý lỗi khi cỡ mẫu không đủ N < 10 hoặc dữ liệu lệch kích thước"""
    res_small = MediationEngine.analyze_mediation(
        x_data=[1.0, 2.0, 3.0],
        m_data=[2.0, 3.0, 4.0],
        y_data=[3.0, 4.0, 5.0]
    )
    assert res_small["status"] == "ERROR"
    assert "tối thiểu N >= 10" in res_small["message"]

    res_mismatch = MediationEngine.analyze_mediation(
        x_data=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        m_data=[2.0, 3.0, 4.0],
        y_data=[3.0, 4.0, 5.0]
    )
    assert res_mismatch["status"] == "ERROR"
    assert "không đồng nhất" in res_mismatch["message"]
