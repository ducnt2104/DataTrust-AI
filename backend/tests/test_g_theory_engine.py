import pytest
import numpy as np
from app.engine.g_theory_engine import GTheoryEngine


def test_g_theory_pxi_basic():
    """Kiểm thử phân rã phương sai G-Theory thiết kế p x i chuẩn mực."""
    np.random.seed(42)
    n_persons = 40
    n_items = 5
    
    # Giả lập chân trị cá nhân person_effect (sigma_p = 1.2)
    person_effects = np.random.normal(0, 1.2, n_persons)
    # Độ khó câu hỏi item_effect (sigma_i = 0.5)
    item_effects = np.array([-0.8, -0.3, 0.0, 0.4, 0.7])
    
    data_rows = []
    for p in range(n_persons):
        row = {"respondent_id": f"p_{p}"}
        for i in range(n_items):
            # Điểm = Grand Mean (3.0) + person + item + error (sigma_e = 0.6)
            err = np.random.normal(0, 0.6)
            score = max(1.0, min(5.0, 3.0 + person_effects[p] + item_effects[i] + err))
            row[f"item_{i}"] = float(score)
        data_rows.append(row)

    res = GTheoryEngine.run_g_study_two_facet(
        data_rows=data_rows,
        person_key="respondent_id",
        item_keys=[f"item_{i}" for i in range(n_items)]
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == n_persons
    assert res["items_count"] == n_items
    assert len(res["variance_components"]) == 3
    
    # Tổng phần trăm phương sai xấp xỉ 100%
    total_pct = sum(vc["percent"] for vc in res["variance_components"])
    assert 99.0 <= total_pct <= 101.0

    # Hệ số G và Phi hiện tại
    metrics = res["current_design_metrics"]
    assert 0.60 <= metrics["g_coefficient_relative"] <= 0.99
    assert 0.50 <= metrics["phi_coefficient_absolute"] <= 0.99
    assert metrics["g_coefficient_relative"] >= metrics["phi_coefficient_absolute"]

    # D-Study projections
    projections = res["d_study_projections"]
    assert len(projections) >= 3
    # Khi số câu hỏi tăng, G-coefficient phải tăng dần
    assert projections[-1]["g_coefficient"] >= projections[0]["g_coefficient"]

    assert "svg_chart" in res
    assert "<svg" in res["svg_chart"]
    assert "apa_narrative" in res
    assert "Cronbach et al." in res["apa_narrative"]


def test_g_theory_edge_cases():
    # 1. Quá ít câu hỏi < 2
    res_one_item = GTheoryEngine.run_g_study_two_facet(
        data_rows=[{"p": "1", "i1": 3}],
        person_key="p",
        item_keys=["i1"]
    )
    assert res_one_item["status"] == "INVALID_SPECIFICATION"

    # 2. Cỡ mẫu quá nhỏ < 8
    res_few = GTheoryEngine.run_g_study_two_facet(
        data_rows=[{"p": f"{i}", "i1": 3, "i2": 4} for i in range(5)],
        person_key="p",
        item_keys=["i1", "i2"]
    )
    assert res_few["status"] == "INSUFFICIENT_SAMPLE"
