import pytest
import math
from app.engine.correlation_engine import CorrelationEngine

def test_pearson_r_exact():
    # Dữ liệu hoàn toàn đồng biến x = [1, 2, 3, 4, 5], y = [2, 4, 6, 8, 10] -> r = 1.0, p < 0.001
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [2.0, 4.0, 6.0, 8.0, 10.0]
    r, p_val, ci_low, ci_up = CorrelationEngine.compute_pearson_r(x, y)
    assert abs(r - 1.0) < 1e-6
    assert p_val < 0.001
    assert ci_low > 0.90

    # Dữ liệu nghịch biến y = [10, 8, 6, 4, 2] -> r = -1.0
    y_rev = [10.0, 8.0, 6.0, 4.0, 2.0]
    r_rev, p_rev, _, _ = CorrelationEngine.compute_pearson_r(x, y_rev)
    assert abs(r_rev - (-1.0)) < 1e-6
    assert p_rev < 0.001

def test_spearman_rho_with_ties():
    # Kiểm tra xếp hạng có giá trị bằng nhau
    values = [10.0, 20.0, 20.0, 40.0]
    ranks = CorrelationEngine._compute_ranks(values)
    # Ranks mong đợi: [1.0, 2.5, 2.5, 4.0]
    assert ranks == [1.0, 2.5, 2.5, 4.0]

    # Spearman rho trên quan hệ đơn điệu phi tuyến
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [1.0, 4.0, 9.0, 16.0, 25.0] # y = x^2 (đơn điệu tuyệt đối)
    rho, p_val, _, _ = CorrelationEngine.compute_spearman_rho(x, y)
    assert abs(rho - 1.0) < 1e-6
    assert p_val < 0.001

def test_zero_variance_defense():
    # Nếu một biến không có phương sai (tất cả giá trị bằng nhau)
    x = [5.0, 5.0, 5.0, 5.0]
    y = [1.0, 2.0, 3.0, 4.0]
    r, p_val, _, _ = CorrelationEngine.compute_pearson_r(x, y)
    assert r == 0.0
    assert p_val == 1.0

def test_analyze_correlation_matrix_full():
    # 3 biến: V1, V2 tương quan cao (0.9+), V3 tương quan thấp
    variables_data = {
        "q1": {
            "title": "Chất lượng sản phẩm",
            "label": "VAR_QUAL",
            "values": [1.0, 2.0, 3.0, 4.0, 5.0, 3.0, 4.0, 2.0, 5.0, 4.0]
        },
        "q2": {
            "title": "Mức độ hài lòng",
            "label": "VAR_SAT",
            "values": [1.2, 2.1, 3.2, 4.1, 4.9, 3.1, 4.0, 2.2, 4.8, 3.9]
        },
        "q3": {
            "title": "Khoảng cách địa lý",
            "label": "VAR_DIST",
            "values": [5.0, 1.0, 4.0, 2.0, 3.0, 5.0, 2.0, 4.0, 1.0, 3.0]
        }
    }

    res = CorrelationEngine.analyze_correlation_matrix(variables_data, method="pearson")
    assert res["status"] == "SUCCESS"
    assert res["variables_count"] == 3
    assert res["total_pairs_count"] == 3
    assert len(res["matrix"]) == 3
    assert len(res["matrix"][0]) == 3

    # Đường chéo chính phải là 1.0
    for i in range(3):
        assert res["matrix"][i][i]["correlation"] == 1.0

    # q1 và q2 phải có tương quan rất cao
    q1_q2 = res["matrix"][0][1]
    assert q1_q2["correlation"] > 0.90
    assert q1_q2["is_significant_05"] is True
    assert q1_q2["direction"] == "Đồng biến (Positive)"

    # Cảnh báo đa cộng tuyến phải kích hoạt cho q1-q2 vì r > 0.85
    assert len(res["multicollinearity_warnings"]) >= 1
    assert "0.85" in res["multicollinearity_warnings"][0]["warning"]

    # Đoạn văn APA phải chứa thông tin hợp lệ
    assert "APA" not in res["apa_interpretation"] # diễn giải tự nhiên
    assert "Pearson" in res["apa_interpretation"]
