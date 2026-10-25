"""
API Route integration tests for Moderated Mediation & Conditional Indirect Effects (PROCESS Model 7; Hayes 2018).
"""

from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_moderated_mediation_route_workflow():
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-id/analytics/moderated-mediation", json={
        "independent_question_id": "q1",
        "mediator_question_id": "q2",
        "moderator_question_id": "q3",
        "dependent_question_id": "q4"
    })
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát thử nghiệm trung gian bị điều tiết
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Tác Động Trung Gian Bị Điều Tiết (PROCESS Model 7)",
        "description": "Kiểm định X (Digital Mindset) -> M (Agility) -> Y (Firm Performance) điều tiết bởi W (Tech Env)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 4 câu hỏi thang đo
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Tác Động Trung Gian Bị Điều Tiết (PROCESS Model 7)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "rating",
                "title": "X: Tư duy số hóa (Digital Mindset)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "M: Độ linh hoạt tổ chức (Agility)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "W: Môi trường công nghệ (Tech Turbulence)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "rating",
                "title": "Y: Hiệu quả kinh doanh (Firm Performance)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")
    surv_data = client.get(f"/api/surveys/{survey_id}").json()
    qs = surv_data["questions"]
    x_id = qs[0]["id"]
    m_id = qs[1]["id"]
    w_id = qs[2]["id"]
    y_id = qs[3]["id"]

    # 4. Kiểm tra lỗi 400 nếu truyền trùng biến
    res_400_duplicate = client.post(f"/api/surveys/{survey_id}/analytics/moderated-mediation", json={
        "independent_question_id": x_id,
        "mediator_question_id": x_id,
        "moderator_question_id": w_id,
        "dependent_question_id": y_id
    })
    assert res_400_duplicate.status_code == 400

    # 5. Kiểm tra lỗi 400 nếu question_id không tồn tại trong survey
    res_400_not_found = client.post(f"/api/surveys/{survey_id}/analytics/moderated-mediation", json={
        "independent_question_id": x_id,
        "mediator_question_id": m_id,
        "moderator_question_id": w_id,
        "dependent_question_id": "non_existent_q"
    })
    assert res_400_not_found.status_code == 400

    # 6. Gửi 20 phản hồi thử nghiệm có mối tương quan định hướng
    now = datetime.now(timezone.utc)
    for idx in range(20):
        # Scale 1-5 ratings
        xv = 1 + (idx % 5)
        wv = 1 + ((idx + 2) % 5)
        # M phụ thuộc X và W và tương tác:
        mv = max(1, min(5, round(1.0 + 0.35 * xv + 0.25 * wv + 0.08 * (xv * wv))))
        # Y phụ thuộc M và X:
        yv = max(1, min(5, round(1.0 + 0.40 * mv + 0.20 * xv)))

        sub_body = {
            "started_at": (now - timedelta(minutes=30 - idx, seconds=30)).isoformat(),
            "submitted_at": (now - timedelta(minutes=30 - idx)).isoformat(),
            "answers": {
                x_id: str(xv),
                m_id: str(mv),
                w_id: str(wv),
                y_id: str(yv)
            },
            "client_metadata": {
                "ip_hash": f"ip_modmed_{idx}",
                "user_agent": "Mozilla/5.0 TestBrowser",
                "screen_resolution": "1920x1080"
            }
        }
        resp = client.post(f"/api/public/surveys/{slug}/submit", json=sub_body)
        assert resp.status_code == 201

    # 7. Thực thi kiểm định Moderated Mediation (Bootstrap 100 lần cho test nhanh)
    analysis_res = client.post(f"/api/surveys/{survey_id}/analytics/moderated-mediation", json={
        "independent_question_id": x_id,
        "mediator_question_id": m_id,
        "moderator_question_id": w_id,
        "dependent_question_id": y_id,
        "center_variables": True,
        "num_bootstrap": 100
    })

    assert analysis_res.status_code == 200
    data = analysis_res.json()
    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 20
    assert data["bootstrap_samples_executed"] == 100
    assert data["center_variables"] is True

    # Kiểm tra Stage 1 Model
    stage1 = data["stage1_mediator_model"]
    assert "r_squared" in stage1
    assert "f_stat" in stage1
    assert "coefficients" in stage1
    assert "interaction_a3_XW" in stage1["coefficients"]

    # Kiểm tra Stage 2 Model
    stage2 = data["stage2_dependent_model"]
    assert "r_squared" in stage2
    assert "coefficients" in stage2
    assert "mediator_path_b" in stage2["coefficients"]

    # Kiểm tra Index of Moderated Mediation
    imm = data["index_of_moderated_mediation"]
    assert "index_omega" in imm
    assert "boot_ci_95_lower" in imm
    assert "boot_ci_95_upper" in imm
    assert "is_significant" in imm

    # Kiểm tra Conditional Indirect Effects
    cond_effects = data["conditional_indirect_effects"]
    assert len(cond_effects) == 3
    for cond in cond_effects:
        assert cond["level"] in ["LOW", "MEAN", "HIGH"]
        assert "indirect_effect" in cond
        assert "boot_ci_95_lower" in cond
        assert "boot_ci_95_upper" in cond

    # Kiểm tra APA Narrative
    apa = data["apa_narrative"]
    assert isinstance(apa, str)
    assert len(apa) > 50
    assert "PROCESS Model 7" in apa
