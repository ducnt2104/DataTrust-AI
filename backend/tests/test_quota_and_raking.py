import pytest
from app.engine.quota_engine import QuotaEngine, RakingEngine

def test_quota_engine_evaluation_normal_and_overflow():
    quota_rules = [
        {
            "id": "q_gender_male",
            "name": "Nam giới",
            "question_id": "q_gender",
            "target_value": "Nam",
            "max_target": 10,
            "action": "flag_overflow"
        },
        {
            "id": "q_region_north",
            "name": "Miền Bắc",
            "question_id": "q_region",
            "target_value": "Miền Bắc",
            "max_target": 5,
            "action": "screen_out"
        }
    ]

    # Trường hợp 1: Chưa đầy hạn ngạch
    counts_low = {"q_gender_male": 8, "q_region_north": 3}
    answers_1 = {"q_gender": "Nam", "q_region": "Miền Bắc"}
    res_1 = QuotaEngine.evaluate_quotas(answers_1, quota_rules, counts_low)
    assert res_1["is_quota_full"] is False
    assert len(res_1["matched_cells"]) == 2
    assert "q_gender_male" in res_1["matched_cells"]
    assert "q_region_north" in res_1["matched_cells"]

    # Trường hợp 2: Hạn ngạch miền Bắc đã đầy (5/5)
    counts_full = {"q_gender_male": 8, "q_region_north": 5}
    res_2 = QuotaEngine.evaluate_quotas(answers_1, quota_rules, counts_full)
    assert res_2["is_quota_full"] is True
    assert res_2["action"] == "screen_out"
    assert len(res_2["reasons"]) == 1
    assert "đã đủ" in res_2["reasons"][0]

def test_quota_engine_compute_progress():
    quota_rules = [
        {
            "id": "q_gender_male",
            "name": "Nam giới",
            "question_id": "q_gender",
            "target_value": "Nam",
            "max_target": 50,
            "action": "flag_overflow"
        },
        {
            "id": "q_gender_female",
            "name": "Nữ giới",
            "question_id": "q_gender",
            "target_value": "Nữ",
            "max_target": 50,
            "action": "flag_overflow"
        }
    ]

    sample_responses = [
        {"answers": {"q_gender": "Nam"}},
        {"answers": {"q_gender": "Nam"}},
        {"answers": {"q_gender": "Nam"}},
        {"answers": {"q_gender": "Nữ"}},
    ]

    progress = QuotaEngine.compute_quota_progress(quota_rules, sample_responses)
    assert len(progress) == 2
    male_cell = next(p for p in progress if p["cell_id"] == "q_gender_male")
    female_cell = next(p for p in progress if p["cell_id"] == "q_gender_female")

    assert male_cell["achieved_count"] == 3
    assert male_cell["remaining_count"] == 47
    assert male_cell["completion_pct"] == 6.0
    assert male_cell["status"] == "open"

    assert female_cell["achieved_count"] == 1
    assert female_cell["remaining_count"] == 49
    assert female_cell["completion_pct"] == 2.0


def test_raking_engine_two_dimensional_convergence():
    """
    Kiểm thử thuật toán Raking (IPF) trên 2 biến nhân khẩu học:
    - Giới tính (Nam / Nữ)
    - Vùng miền (Bắc / Trung / Nam)
    Mẫu ban đầu bị lệch (skewed): 70% Nam, 30% Nữ.
    Mục tiêu chuẩn hóa: 50% Nam, 50% Nữ.
    """
    # Tạo 100 mẫu giả định có độ lệch
    sample = []
    # 70 Nam (40 Bắc, 20 Trung, 10 Nam)
    for i in range(40):
        sample.append({"id": f"resp_{len(sample)}", "gender": "Nam", "region": "Miền Bắc"})
    for i in range(20):
        sample.append({"id": f"resp_{len(sample)}", "gender": "Nam", "region": "Miền Trung"})
    for i in range(10):
        sample.append({"id": f"resp_{len(sample)}", "gender": "Nam", "region": "Miền Nam"})

    # 30 Nữ (10 Bắc, 10 Trung, 10 Nam)
    for i in range(10):
        sample.append({"id": f"resp_{len(sample)}", "gender": "Nữ", "region": "Miền Bắc"})
    for i in range(10):
        sample.append({"id": f"resp_{len(sample)}", "gender": "Nữ", "region": "Miền Trung"})
    for i in range(10):
        sample.append({"id": f"resp_{len(sample)}", "gender": "Nữ", "region": "Miền Nam"})

    targets = {
        "gender": {"Nam": 0.50, "Nữ": 0.50},
        "region": {"Miền Bắc": 0.35, "Miền Trung": 0.25, "Miền Nam": 0.40}
    }

    result = RakingEngine.run_raking(
        sample_data=sample,
        target_margins=targets,
        max_iterations=40,
        convergence_tol=1e-3
    )

    assert result["converged"] is True
    assert result["sample_size"] == 100
    assert result["iterations"] <= 20
    assert result["design_effect_deff"] >= 1.0  # Deff luôn >= 1.0 khi có điều chỉnh trọng số
    assert 0 < result["effective_sample_size_neff"] <= 100.0
    assert 0 < result["statistical_efficiency_pct"] <= 100.0

    # Kiểm tra phân bố biên sau khi cân trọng số
    gender_comp = next(m for m in result["marginal_comparisons"] if m["variable"] == "gender")
    male_row = next(c for c in gender_comp["categories"] if c["category"] == "Nam")
    female_row = next(c for c in gender_comp["categories"] if c["category"] == "Nữ")

    # Trước khi cân: 70% Nam, 30% Nữ
    assert male_row["unweighted_pct"] == 70.0
    assert female_row["unweighted_pct"] == 30.0

    # Sau khi cân: tiệm cận 50% (+/- 0.5%)
    assert abs(male_row["weighted_pct"] - 50.0) < 0.5
    assert abs(female_row["weighted_pct"] - 50.0) < 0.5
    assert male_row["absolute_bias_reduction_pct"] > 18.0

    # Trọng số của nữ phải cao hơn trọng số của nam (vì nữ bị under-represented)
    female_id = "resp_75"
    male_id = "resp_5"
    assert result["weights"][female_id] > result["weights"][male_id]

def test_raking_engine_empty_and_single_case():
    empty_res = RakingEngine.run_raking([], {"gender": {"Nam": 0.5, "Nữ": 0.5}})
    assert empty_res["converged"] is False
    assert empty_res["sample_size"] == 0

    single_sample = [{"id": "single", "gender": "Nam"}]
    single_res = RakingEngine.run_raking(single_sample, {"gender": {"Nam": 1.0}})
    assert single_res["converged"] is True
    assert single_res["weights"]["single"] == 1.0
