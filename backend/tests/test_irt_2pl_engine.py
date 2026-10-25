import pytest
import math
from app.engine.irt_2pl_engine import IRT2PLEngine


def test_irt_2pl_synthetic_binary_data():
    """
    Kiểm thử ước lượng mô hình IRT 2PL trên tập dữ liệu nhị phân giả lập (N=20, P=3).
    Item 1: Dễ (nhiều 1)
    Item 2: Trung bình
    Item 3: Khó (ít 1)
    """
    data = [
        [1, 1, 0],
        [1, 1, 1],
        [1, 0, 0],
        [1, 1, 0],
        [1, 1, 1],
        [0, 0, 0],
        [1, 1, 0],
        [1, 0, 0],
        [1, 1, 1],
        [1, 1, 0],
        [0, 0, 0],
        [1, 1, 0],
        [1, 1, 1],
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0],
        [1, 1, 1],
        [1, 0, 0],
        [1, 1, 0],
        [1, 1, 1]
    ]
    item_names = ["Item Dễ", "Item Trung Bình", "Item Khó"]

    res = IRT2PLEngine.analyze_irt_2pl(data, item_names)
    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == 20
    assert res["num_items"] == 3
    assert res["is_already_binary"] is True

    # Kiểm tra phân loại item
    items = res["items"]
    assert len(items) == 3
    # Item 1 có tỷ lệ 1 cao hơn Item 3 -> Item 1 difficulty b phải nhỏ hơn Item 3
    b1 = items[0]["difficulty_b"]
    b3 = items[2]["difficulty_b"]
    assert b1 < b3, f"Item 1 difficulty ({b1}) phải nhỏ hơn Item 3 ({b3})"

    # Kiểm tra đường cong ICC và TIF
    assert len(res["icc_curves"]) == 3
    assert len(res["icc_curves"][0]["points"]) == 36
    assert "test_information_curve" in res
    assert len(res["test_information_curve"]["tif_points"]) == 36

    # Kiểm tra APA 7th narrative
    assert "IRT 2PL" in res["apa_narrative"]
    assert "rho_IRT" in res["apa_narrative"]


def test_irt_2pl_likert_binarization():
    """
    Kiểm thử tự động binarize thang đo Likert 1-5 theo ngưỡng median.
    """
    data = [
        [5, 4, 3],
        [4, 5, 2],
        [3, 3, 1],
        [5, 5, 4],
        [2, 2, 1],
        [4, 4, 3],
        [5, 4, 2],
        [1, 2, 1],
        [4, 5, 4],
        [3, 4, 2]
    ]
    item_names = ["Hài Lòng", "Chất Lượng", "Giới Thiệu"]

    res = IRT2PLEngine.analyze_irt_2pl(data, item_names)
    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == 10
    assert res["num_items"] == 3
    assert res["is_already_binary"] is False
    assert 0.0 <= res["marginal_reliability"] <= 1.0


def test_irt_2pl_insufficient_sample():
    """
    Kiểm thử bắt lỗi khi mẫu quá nhỏ (< 6).
    """
    data = [
        [1, 0],
        [1, 1],
        [0, 1]
    ]
    res = IRT2PLEngine.analyze_irt_2pl(data, ["Q1", "Q2"])
    assert res["status"] == "INSUFFICIENT_SAMPLE"
