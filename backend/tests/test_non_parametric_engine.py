import pytest

try:
    from app.engine.non_parametric_engine import NonParametricEngine
except ModuleNotFoundError:
    from backend.app.engine.non_parametric_engine import NonParametricEngine


def test_ranking_with_ties():
    """Kiểm tra thuật toán xếp hạng xử lý chính xác các giá trị trùng lặp (Ties)"""
    # Values: 10, 20, 20, 30, 40, 40, 40
    # Expected ranks:
    # 10: 1.0
    # 20, 20: (2 + 3) / 2 = 2.5
    # 30: 4.0
    # 40, 40, 40: (5 + 6 + 7) / 3 = 6.0
    vals = [10.0, 20.0, 20.0, 30.0, 40.0, 40.0, 40.0]
    ranks, tie_counts = NonParametricEngine._rank_data(vals)

    assert ranks == [1.0, 2.5, 2.5, 4.0, 6.0, 6.0, 6.0]
    assert tie_counts == [2, 3]


def test_mann_whitney_u_significance():
    """Kiểm tra kiểm định Mann-Whitney U phân biệt chính xác 2 nhóm có phân vị lệch rõ rệt"""
    # Group 1: Đánh giá rất cao
    g1 = [4.0, 5.0, 5.0, 4.0, 5.0, 4.0, 5.0, 5.0, 4.0, 5.0]
    # Group 2: Đánh giá rất thấp
    g2 = [1.0, 2.0, 2.0, 1.0, 3.0, 2.0, 1.0, 2.0, 1.0, 2.0]

    res = NonParametricEngine.mann_whitney_u_test(g1, g2, "Kỹ thuật", "Kinh doanh")

    assert res["status"] == "OK"
    assert res["total_sample_size"] == 20
    assert res["groups"]["group1"]["mean_rank"] > res["groups"]["group2"]["mean_rank"]
    assert res["statistics"]["is_significant"] is True
    assert res["statistics"]["p_value"] < 0.001
    assert res["statistics"]["u_statistic"] == 0.0  # Hoàn toàn tách biệt không chồng lấn
    assert res["effect_size"]["rosenthal_r"] > 0.7  # Tác động rất lớn
    assert res["conclusion"]["higher_group"] == "Kỹ thuật"


def test_mann_whitney_u_null_hypothesis():
    """Kiểm tra trường hợp 2 nhóm tương đương (H0 được chấp nhận, p > 0.05)"""
    g1 = [3.0, 4.0, 3.0, 4.0, 3.0, 4.0, 3.0, 4.0]
    g2 = [4.0, 3.0, 4.0, 3.0, 4.0, 3.0, 4.0, 3.0]

    res = NonParametricEngine.mann_whitney_u_test(g1, g2, "Nhóm A", "Nhóm B")

    assert res["status"] == "OK"
    assert res["statistics"]["is_significant"] is False
    assert res["statistics"]["p_value"] > 0.5
    assert res["effect_size"]["rosenthal_r"] < 0.2


def test_wilcoxon_signed_rank_significance():
    """Kiểm định hạng có dấu Wilcoxon cho cặp quan sát trước và sau can thiệp"""
    # Before
    pre = [2.0, 1.0, 3.0, 2.0, 2.0, 1.0, 3.0, 2.0, 2.0, 1.0]
    # After (Điểm tăng vọt sau can thiệp)
    post = [5.0, 4.0, 5.0, 5.0, 4.0, 4.0, 5.0, 4.0, 5.0, 4.0]

    res = NonParametricEngine.wilcoxon_signed_rank_test(post, pre, "Sau đào tạo", "Trước đào tạo")

    assert res["status"] == "OK"
    assert res["total_pairs"] == 10
    assert res["effective_pairs"] == 10
    assert res["zero_differences_count"] == 0
    assert res["statistics"]["w_minus"] == 0.0
    assert res["statistics"]["is_significant"] is True
    assert res["statistics"]["p_value"] < 0.01
    assert res["effect_size"]["rosenthal_r"] > 0.7


def test_wilcoxon_signed_rank_zero_diffs_handling():
    """Kiểm tra loại trừ chính xác các cặp có chênh lệch bằng 0"""
    s1 = [3.0, 3.0, 4.0, 5.0, 2.0, 3.0, 4.0, 5.0]
    s2 = [3.0, 3.0, 2.0, 3.0, 2.0, 3.0, 2.0, 3.0]  # 4 cặp bằng nhau (diff=0)

    res = NonParametricEngine.wilcoxon_signed_rank_test(s1, s2)

    assert res["status"] == "OK"
    assert res["total_pairs"] == 8
    assert res["zero_differences_count"] == 4
    assert res["effective_pairs"] == 4


def test_kruskal_wallis_h_and_dunn_post_hoc():
    """Kiểm định Kruskal-Wallis cho 3 nhóm độc lập và so sánh cặp hậu nghiệm Dunn"""
    groups = {
        "Hà Nội": [5.0, 5.0, 4.0, 5.0, 5.0, 4.0],
        "Đà Nẵng": [3.0, 3.0, 4.0, 3.0, 3.0, 4.0],
        "Cần Thơ": [1.0, 2.0, 1.0, 2.0, 1.0, 2.0]
    }

    res = NonParametricEngine.kruskal_wallis_h_test(groups)

    assert res["status"] == "OK"
    assert res["k_groups"] == 3
    assert res["total_sample_size"] == 18
    assert res["degrees_of_freedom"] == 2
    assert res["statistics"]["is_significant"] is True
    assert res["statistics"]["p_value"] < 0.001
    assert res["effect_size"]["epsilon_squared"] > 0.5  # Large effect size

    # Kiểm tra so sánh cặp hậu nghiệm Dunn (3 cặp so sánh: k*(k-1)/2 = 3)
    dunn = res["post_hoc_dunn_tests"]
    assert len(dunn) == 3
    # Cặp Hà Nội vs Cần Thơ phải đạt ý nghĩa thống kê cao sau hiệu chỉnh Bonferroni
    pair_hn_ct = next(p for p in dunn if "Hà Nội" in p["comparison"] and "Cần Thơ" in p["comparison"])
    assert pair_hn_ct["is_significant_bonferroni"] is True
    assert pair_hn_ct["p_value_bonferroni"] < 0.01
