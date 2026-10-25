"""
API Route integration tests for Complex Survey Sampling Design & Horvitz-Thompson Taylor Series Linearization.
"""

from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_complex_sampling_route_workflow():
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-id/analytics/complex-sampling", json={
        "target_question_id": "q1",
        "cluster_question_id": "q2"
    })
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát thử nghiệm thiết kế mẫu phức hợp
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Đánh Giá Dịch Vụ Y Tế Theo Cụm Đa Tầng (Two-Stage Cluster)",
        "description": "Đo lường mức độ hài lòng theo 4 bệnh viện (PSU) và 2 khu vực phân tầng"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo các câu hỏi: Target Y (Rating), Cluster PSU (Multiple Choice/Dropdown), Stratum (Dropdown), Weight (Number)
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Đánh Giá Dịch Vụ Y Tế Theo Cụm Đa Tầng (Two-Stage Cluster)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "rating",
                "title": "Y: Mức độ hài lòng dịch vụ y tế",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "multiple_choice",
                "title": "PSU: Bệnh viện tiếp nhận (Cụm)",
                "is_required": True,
                "options": [
                    {"label": "Bệnh viện A (Bắc)", "value": "BV_A"},
                    {"label": "Bệnh viện B (Bắc)", "value": "BV_B"},
                    {"label": "Bệnh viện C (Nam)", "value": "BV_C"},
                    {"label": "Bệnh viện D (Nam)", "value": "BV_D"}
                ],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "multiple_choice",
                "title": "Stratum: Khu vực phân tầng",
                "is_required": True,
                "options": [
                    {"label": "Miền Bắc", "value": "MB"},
                    {"label": "Miền Nam", "value": "MN"}
                ],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Weight: Trọng số thiết kế",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")
    surv_data = client.get(f"/api/surveys/{survey_id}").json()
    qs = surv_data["questions"]
    y_id = qs[0]["id"]
    cluster_id = qs[1]["id"]
    stratum_id = qs[2]["id"]
    weight_id = qs[3]["id"]

    # 4. Kiểm tra lỗi 400 nếu trùng biến Y và PSU
    res_400_dup = client.post(f"/api/surveys/{survey_id}/analytics/complex-sampling", json={
        "target_question_id": y_id,
        "cluster_question_id": y_id
    })
    assert res_400_dup.status_code == 400

    # 5. Kiểm tra lỗi 400 nếu question_id không tồn tại
    res_400_not_found = client.post(f"/api/surveys/{survey_id}/analytics/complex-sampling", json={
        "target_question_id": y_id,
        "cluster_question_id": "non_existent_cluster"
    })
    assert res_400_not_found.status_code == 400

    # 6. Gửi 20 phản hồi thử nghiệm phân bổ trên 4 cụm và 2 tầng
    now = datetime.now(timezone.utc)
    cluster_options = ["BV_A", "BV_B", "BV_C", "BV_D"]
    for idx in range(20):
        c_val = cluster_options[idx % 4]
        s_val = "MB" if c_val in ["BV_A", "BV_B"] else "MN"
        w_val = "1.2" if s_val == "MB" else "0.8"
        # Bệnh viện A & B điểm cao (4 hoặc 5), C & D điểm thấp (1 hoặc 2) -> ICC rõ rệt
        if c_val in ["BV_A", "BV_B"]:
            y_val = "5" if idx % 2 == 0 else "4"
        else:
            y_val = "2" if idx % 2 == 0 else "1"

        sub_body = {
            "started_at": (now - timedelta(minutes=30 - idx, seconds=30)).isoformat(),
            "submitted_at": (now - timedelta(minutes=30 - idx)).isoformat(),
            "answers": {
                y_id: y_val,
                cluster_id: c_val,
                stratum_id: s_val,
                weight_id: w_val
            },
            "client_metadata": {
                "ip_hash": f"ip_complex_{idx}",
                "user_agent": "Mozilla/5.0 TestBrowser",
                "screen_resolution": "1920x1080"
            }
        }
        resp = client.post(f"/api/public/surveys/{slug}/submit", json=sub_body)
        assert resp.status_code == 201

    # 7. Gọi API phân tích thiết kế mẫu phức hợp
    analysis_res = client.post(f"/api/surveys/{survey_id}/analytics/complex-sampling", json={
        "target_question_id": y_id,
        "cluster_question_id": cluster_id,
        "stratum_question_id": stratum_id,
        "weight_question_id": weight_id
    })

    assert analysis_res.status_code == 200
    data = analysis_res.json()
    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 20
    assert data["strata_count"] == 2
    assert data["psu_count"] == 4
    assert data["degrees_of_freedom"] == 2  # 4 PSUs - 2 Strata = 2 df

    # Horvitz-Thompson estimates
    ht = data["horvitz_thompson_estimates"]
    assert "weighted_mean" in ht
    assert "unweighted_mean" in ht
    assert "weighting_bias_shift" in ht
    assert 1.0 <= ht["weighted_mean"] <= 5.0

    # Taylor Series Linearization Variance
    taylor = data["taylor_linearization_variance"]
    assert "complex_se" in taylor
    assert "ci_95_lower" in taylor
    assert "ci_95_upper" in taylor
    assert taylor["ci_95_lower"] < ht["weighted_mean"] < taylor["ci_95_upper"]

    # SRS comparison
    srs = data["srs_comparison"]
    assert "srs_se" in srs
    assert "se_inflation_ratio" in srs

    # Design effects
    deff = data["design_effects"]
    assert "deff" in deff
    assert "deft" in deff
    assert "icc" in deff
    assert "effective_sample_size" in deff
    assert "efficiency_loss_pct" in deff
    assert "rating" in deff
    assert deff["deff"] > 0.0  # Design effect is computed and positive

    # APA Narrative
    apa = data["apa_narrative"]
    assert isinstance(apa, str)
    assert "Two-Stage Complex Survey Design" in apa
    assert "Horvitz-Thompson" in apa
    assert "Taylor Series Linearization" in apa
