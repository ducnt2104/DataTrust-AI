import pytest
import math
from app.engine.ttest_engine import TTestEngine

def test_ttest_math_primitives():
    # 1. Kiểm tra p-value của t-distribution
    # Với df = 60, t = 2.0 thì p-value 2-tailed khoảng 0.0499...
    p_val = TTestEngine._t_p_value(2.0, 60.0)
    assert 0.045 < p_val < 0.055

    # Khi t = 0 thì p-value = 1.0
    p_zero = TTestEngine._t_p_value(0.0, 30.0)
    assert abs(p_zero - 1.0) < 1e-6

    # 2. Kiểm tra F p-value
    p_f = TTestEngine._f_p_value(4.0, 1.0, 60.0)
    assert 0.045 < p_f < 0.055

def test_independent_ttest_equal_variances():
    # Nhóm 1: M ~ 5.0, SD ~ 1.0
    g1 = [4.5, 5.0, 5.2, 4.8, 5.5, 5.1, 4.9, 5.3, 4.7, 5.0]
    # Nhóm 2: M ~ 3.5, SD ~ 1.0
    g2 = [3.2, 3.8, 3.4, 3.6, 3.5, 3.7, 3.3, 3.9, 3.1, 3.5]

    res = TTestEngine.compute_independent_ttest(
        group1_values=g1,
        group2_values=g2,
        group1_label="Thử nghiệm",
        group2_label="Đối chứng",
        variable_label="Điểm CSAT"
    )

    assert res["status"] == "SUCCESS"
    assert res["test_type"] == "independent"
    assert res["group1"]["n"] == 10
    assert res["group2"]["n"] == 10
    assert res["mean_difference"] > 1.0
    assert res["primary_test"]["t_stat"] > 5.0
    assert res["primary_test"]["is_significant_01"] is True
    assert res["levene_test"]["equal_variances_assumed"] is True
    assert res["effect_size"]["magnitude"] == "Lớn (Large)"
    assert res["ci_95_lower"] > 0
    assert "Điểm CSAT" in res["apa_interpretation"]

def test_independent_ttest_unequal_variances():
    # Nhóm 1: phương sai rất nhỏ
    g1 = [4.0, 4.1, 4.0, 4.1, 4.0, 4.0, 4.1, 4.0, 4.1, 4.0]
    # Nhóm 2: phương sai rất lớn
    g2 = [1.0, 5.0, 2.0, 4.0, 1.5, 5.5, 2.5, 4.5, 1.0, 5.0]

    res = TTestEngine.compute_independent_ttest(
        group1_values=g1,
        group2_values=g2,
        group1_label="Nhóm A",
        group2_label="Nhóm B"
    )

    assert res["status"] == "SUCCESS"
    # Levene phải phát hiện phương sai không đồng nhất
    assert res["levene_test"]["equal_variances_assumed"] is False
    assert "Welch's t-test" in res["test_method"]

def test_paired_ttest_pre_post():
    # 12 học sinh trước và sau khóa đào tạo
    pre = [2.5, 3.0, 2.8, 3.2, 2.9, 3.1, 2.7, 3.0, 2.6, 3.3, 2.8, 3.0]
    post = [4.2, 4.5, 4.0, 4.6, 4.3, 4.7, 4.1, 4.4, 4.0, 4.8, 4.2, 4.5]
    pairs = list(zip(post, pre))  # Chênh lệch post - pre > 0

    res = TTestEngine.compute_paired_ttest(
        pairs=pairs,
        variable1_label="Sau đào tạo (Post)",
        variable2_label="Trước đào tạo (Pre)"
    )

    assert res["status"] == "SUCCESS"
    assert res["test_type"] == "paired"
    assert res["sample_size"] == 12
    assert res["degrees_of_freedom"] == 11
    assert res["mean_difference"] > 1.0
    assert res["t_stat"] > 10.0
    assert res["is_significant_01"] is True
    assert res["effect_size"]["magnitude"] == "Lớn (Large)"
    assert res["pearson_r"] > 0
    assert "Paired-Samples T-Test" in res["apa_interpretation"]

def test_ttest_insufficient_sample():
    # Kiểm tra thiếu mẫu
    res_ind = TTestEngine.compute_independent_ttest([1.0], [2.0, 3.0])
    assert res_ind["status"] == "INSUFFICIENT_SAMPLE"

    res_paired = TTestEngine.compute_paired_ttest([(1.0, 2.0)])
    assert res_paired["status"] == "INSUFFICIENT_SAMPLE"
