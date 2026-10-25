import pytest
import numpy as np
from app.engine.irt_4pl_engine import IRT4PLEngine


def test_irt_3pl_model():
    """Kiểm thử mô hình IRT 3PL (cố định d = 1.0, ước lượng đoán mò c)"""
    np.random.seed(42)
    n = 100
    p = 4
    # Sinh ma trận phản hồi Likert 1-5 có phân hóa năng lực
    theta = np.random.normal(0, 1, n)
    matrix = []
    for th in theta:
        row = [
            1 if IRT4PLEngine.prob_4pl(th, 1.2, -1.0, 0.2, 1.0) > np.random.rand() else 0,
            1 if IRT4PLEngine.prob_4pl(th, 1.5, 0.0, 0.15, 1.0) > np.random.rand() else 0,
            1 if IRT4PLEngine.prob_4pl(th, 1.0, 1.0, 0.1, 1.0) > np.random.rand() else 0,
            1 if IRT4PLEngine.prob_4pl(th, 0.8, 1.5, 0.2, 1.0) > np.random.rand() else 0
        ]
        matrix.append([float(val) for val in row])

    item_names = ["Item 1", "Item 2", "Item 3", "Item 4"]
    res = IRT4PLEngine.fit_irt_4pl(matrix, item_names, model_type="3pl")

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == n
    assert res["items_count"] == p
    assert res["model_type"] == "3PL"

    # Kiểm tra tham số từng item
    for item in res["items_parameters"]:
        assert item["discrimination_a"] > 0
        assert item["guessing_c"] > 0
        assert item["inattention_d"] == 1.0

    # Kiểm tra Hàm thông tin TIF
    tif = res["test_information_function"]
    assert tif["peak_information"] > 0
    assert tif["minimum_standard_error"] > 0
    assert len(tif["information_values"]) == len(tif["theta_grid"])

    # Kiểm tra mô phỏng CAT
    cat = res["cat_simulation"]
    assert len(cat) >= 2
    for step in cat:
        assert "provisional_theta" in step
        assert "measurement_se" in step

    # Kiểm tra SVG và APA
    assert "<svg" in res["svg_curves"]
    assert "3PL" in res["apa_narrative"]
    assert "Test Information Function" in res["apa_narrative"]


def test_irt_4pl_model():
    """Kiểm thử mô hình IRT 4PL (ước lượng cả tham số đoán mò c và đãng trí d)"""
    np.random.seed(123)
    n = 120
    p = 3
    theta = np.random.normal(0, 1, n)
    matrix = []
    for th in theta:
        row = [
            1 if IRT4PLEngine.prob_4pl(th, 1.4, -0.5, 0.2, 0.90) > np.random.rand() else 0,
            1 if IRT4PLEngine.prob_4pl(th, 1.1, 0.5, 0.15, 0.85) > np.random.rand() else 0,
            1 if IRT4PLEngine.prob_4pl(th, 1.6, 1.2, 0.1, 0.92) > np.random.rand() else 0
        ]
        matrix.append([float(val) for val in row])

    item_names = ["Toán Q1", "Toán Q2", "Toán Q3"]
    res = IRT4PLEngine.fit_irt_4pl(matrix, item_names, model_type="4pl")

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "4PL"
    for item in res["items_parameters"]:
        assert item["discrimination_a"] > 0
        assert item["guessing_c"] >= 0.02
        assert item["inattention_d"] <= 1.0


def test_irt_4pl_edge_cases():
    """Kiểm thử các trường hợp dữ liệu biên."""
    # 1. Quá ít quan sát (< 8)
    res_few = IRT4PLEngine.fit_irt_4pl([[1, 0], [0, 1]], ["Q1", "Q2"])
    assert res_few["status"] == "INSUFFICIENT_SAMPLE"

    # 2. Quá ít items (< 2)
    res_one = IRT4PLEngine.fit_irt_4pl([[1], [0], [1], [0], [1], [0], [1], [0]], ["Q1"])
    assert res_one["status"] == "INSUFFICIENT_ITEMS"

    # 3. Item suy biến (toàn bộ 0 hoặc 1)
    res_degen = IRT4PLEngine.fit_irt_4pl(
        [[1, 1], [1, 1], [1, 1], [1, 1], [1, 1], [1, 1], [1, 1], [1, 1]],
        ["Q1", "Q2"]
    )
    assert res_degen["status"] == "DEGENERATE_ITEM"
