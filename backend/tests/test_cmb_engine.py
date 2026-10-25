"""
Unit tests for Common Method Bias / Variance (CMB/CMV) Engine.
"""

import math
import pytest
from app.engine.cmb_engine import CMBEngine


def test_student_t_and_beta_calculation():
    """Kiểm tra độ chính xác của hàm tính student-t p-value"""
    # t = 0 -> p = 1.0
    p0 = CMBEngine._student_t_p_value(0.0, 10)
    assert abs(p0 - 1.0) < 1e-4

    # t = 2.228 for df = 10 -> p ~ 0.05
    p_crit = CMBEngine._student_t_p_value(2.228, 10)
    assert abs(p_crit - 0.05) < 0.01

    # Large t -> p very small
    p_large = CMBEngine._student_t_p_value(6.0, 30)
    assert p_large < 0.001


def test_harman_single_factor_no_bias():
    """Kiểm tra Harman test trên tập dữ liệu nhiều nhân tố độc lập (Low CMB)"""
    # Giả lập 2 nhóm biến độc lập
    data = []
    for i in range(50):
        data.append({
            "q1": float(1 + (i % 5)),
            "q2": float(1 + ((i + 1) % 5)),
            "q3": float(5 - (i % 4)),
            "q4": float(1 + ((i * 2) % 5)),
            "q5": float(3 + ((i % 3) - 1))
        })

    res = CMBEngine.harman_single_factor_test(data, ["q1", "q2", "q3", "q4", "q5"])
    assert res["n_sample"] == 50
    assert res["n_items"] == 5
    assert res["threshold_pct"] == 50.0
    assert "first_factor_variance_pct" in res
    assert res["first_factor_variance_pct"] < 50.0
    assert res["passed"] is True
    assert res["has_cmv_risk"] is False
    assert len(res["variance_breakdown"]) > 0


def test_harman_single_factor_high_bias():
    """Kiểm tra Harman test trên tập dữ liệu biến có tương quan cực cao (High CMB)"""
    # Mọi biến đều đồng biến mạnh với nhau
    data = []
    for i in range(50):
        base = float((i % 5) + 1)
        data.append({
            "q1": base,
            "q2": base + 0.1 * (i % 2),
            "q3": base - 0.1 * ((i + 1) % 2),
            "q4": base + 0.05 * (i % 3)
        })

    res = CMBEngine.harman_single_factor_test(data, ["q1", "q2", "q3", "q4"])
    assert res["passed"] is False
    assert res["has_cmv_risk"] is True
    assert res["first_factor_variance_pct"] > 50.0


def test_marker_variable_technique():
    """Kiểm tra kỹ thuật biến đánh dấu của Lindell & Whitney (2001)"""
    data = []
    for i in range(40):
        data.append({
            "x1": float(1 + (i % 5)),
            "x2": float(1 + ((i + 1) % 5)),
            "x3": float(1 + ((i + 2) % 5)),
            "marker": float(3 + (0.1 if i % 2 == 0 else -0.1))  # Biến marker tương quan yếu
        })

    res = CMBEngine.marker_variable_technique(
        data=data,
        substantive_variables=["x1", "x2", "x3"],
        marker_variable="marker"
    )
    assert "marker_correlation_r_m" in res
    assert res["total_pairs_tested"] == 3
    assert "significance_retention_rate_pct" in res
    assert len(res["pair_comparisons"]) == 3
    for pair in res["pair_comparisons"]:
        assert "r_original" in pair
        assert "r_adjusted" in pair
        assert "p_adjusted" in pair


def test_unmeasured_latent_method_factor():
    """Kiểm tra ULMCF ước lượng phương sai sai số phương pháp"""
    data = []
    for i in range(30):
        data.append({
            "v1": float(1 + (i % 5)),
            "v2": float(1 + ((i + 2) % 5)),
            "v3": float(5 - (i % 5))
        })

    res = CMBEngine.unmeasured_latent_method_factor(data, ["v1", "v2", "v3"])
    assert res["n_sample"] == 30
    assert "estimated_cmv_variance_pct" in res
    assert res["benchmark_threshold_pct"] == 25.0
    assert "method_loadings" in res


def test_comprehensive_diagnostic():
    """Kiểm tra tổng hợp chẩn đoán đầy đủ và trích xuất báo cáo APA 7th"""
    data = []
    for i in range(40):
        data.append({
            "a1": float(1 + (i % 5)),
            "a2": float(1 + ((i + 1) % 5)),
            "b1": float(5 - (i % 4)),
            "b2": float(1 + ((i * 3) % 5)),
            "m1": float(2 + (i % 2))
        })

    diag = CMBEngine.comprehensive_diagnostic(
        data=data,
        variables=["a1", "a2", "b1", "b2"],
        marker_variable="m1"
    )

    assert "overall_risk" in diag
    assert diag["overall_risk"] in ["LOW", "MODERATE", "HIGH"]
    assert "apa_writeup" in diag
    assert "Podsakoff et al." in diag["apa_writeup"]
    assert "recommended_remedies" in diag
    assert len(diag["recommended_remedies"]) > 0
