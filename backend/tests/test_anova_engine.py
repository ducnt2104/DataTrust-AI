import pytest
from app.engine.anova_engine import ANOVAEngine

def test_anova_engine_significant_three_groups():
    # 3 nhóm với điểm số khác biệt rõ rệt
    # Nhóm A: THPT (thấp)
    g_thpt = [2.0, 2.5, 2.2, 2.8, 2.1, 2.4, 2.3, 2.6, 2.2, 2.5]
    # Nhóm B: Đại học (trung bình)
    g_dh = [3.5, 3.8, 3.2, 3.9, 3.6, 3.4, 3.7, 3.5, 3.8, 3.6]
    # Nhóm C: Sau đại học (cao)
    g_sdh = [4.8, 5.0, 4.7, 4.9, 4.6, 5.0, 4.8, 4.9, 4.7, 5.0]

    groups = {
        "THPT": g_thpt,
        "Đại học": g_dh,
        "Sau đại học": g_sdh
    }

    res = ANOVAEngine.compute_oneway_anova(
        groups_data=groups,
        grouping_label="Trình độ học vấn",
        variable_label="Mức độ tin cậy dữ liệu"
    )

    assert res["status"] == "SUCCESS"
    assert res["groups_count"] == 3
    assert res["total_sample_size"] == 30
    assert res["anova_table"]["df_between"] == 2
    assert res["anova_table"]["df_within"] == 27
    assert res["anova_table"]["f_stat"] > 50.0
    assert res["anova_table"]["is_significant_01"] is True

    # Kích thước hiệu ứng lớn (Eta-squared > 0.14)
    assert res["effect_size"]["eta_squared"] > 0.50
    assert res["effect_size"]["magnitude"] == "Lớn (Large)"

    # Kiểm định hậu nghiệm Tukey HSD
    assert len(res["post_hoc_tukey"]) == 3  # 3 cặp: THPT vs ĐH, THPT vs Sau ĐH, ĐH vs Sau ĐH
    for pair in res["post_hoc_tukey"]:
        assert pair["is_significant"] is True
        assert pair["q_stat"] >= pair["q_critical_05"]

    assert "Trình độ học vấn" in res["apa_interpretation"]
    assert "Tukey" in res["apa_interpretation"]

def test_anova_engine_insignificant_three_groups():
    # 3 nhóm không có sự khác biệt
    g1 = [4.0, 4.2, 3.9, 4.1, 4.0, 3.8, 4.2, 4.0]
    g2 = [4.1, 3.9, 4.0, 4.2, 3.8, 4.0, 4.1, 3.9]
    g3 = [4.0, 4.0, 4.1, 3.9, 4.2, 3.8, 4.0, 4.1]

    res = ANOVAEngine.compute_oneway_anova({
        "Miền Bắc": g1,
        "Miền Trung": g2,
        "Miền Nam": g3
    })

    assert res["status"] == "SUCCESS"
    assert res["anova_table"]["is_significant_05"] is False
    assert res["effect_size"]["magnitude"] == "Không đáng kể (Trivial)"
    # Tất cả các cặp Tukey đều không có ý nghĩa
    for pair in res["post_hoc_tukey"]:
        assert pair["is_significant"] is False

def test_anova_engine_edge_cases():
    # 1. Dưới 2 nhóm
    res_k1 = ANOVAEngine.compute_oneway_anova({"Nhóm 1": [1.0, 2.0, 3.0]})
    assert res_k1["status"] == "INSUFFICIENT_GROUPS"

    # 2. Cỡ mẫu quá nhỏ
    res_small = ANOVAEngine.compute_oneway_anova({"G1": [1.0], "G2": [2.0]})
    assert res_small["status"] == "INSUFFICIENT_SAMPLE"
