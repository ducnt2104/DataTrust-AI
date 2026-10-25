import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_g_theory_routes_workflow():
    """Kiểm thử tích hợp đầu-cuối API Lý thuyết Khái quát hóa Đo lường (G-Theory; Cronbach 1972, Brennan 2001)."""
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey/analytics/g-theory", json={
        "item_question_ids": ["q1", "q2"]
    })
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Kiểm định Độ tin cậy Thang đo Đa diện mạo (G-Theory & D-Study)",
        "description": "Phân rã phương sai nguồn gốc sai số đo lường khảo sát"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 4 câu hỏi đánh giá 1-5 sao
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Kiểm định Độ tin cậy Thang đo Đa diện mạo (G-Theory & D-Study)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "rating",
                "title": "Chỉ báo Đo lường 1 (Relevance)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Chỉ báo Đo lường 2 (Clarity)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Chỉ báo Đo lường 3 (Consistency)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "rating",
                "title": "Chỉ báo Đo lường 4 (Robustness)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200

    # Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    assert len(questions) == 4
    q_ids = [q["id"] for q in questions]

    # 4. Khi chưa có dữ liệu phản hồi (< 8)
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/g-theory", json={
        "item_question_ids": q_ids
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_DATA", "INSUFFICIENT_SAMPLE"]

    # 5. Sinh 24 phản hồi có phân hóa năng lực và độ khó câu
    now = datetime.now(timezone.utc)
    for i in range(24):
        p_ability = 1 + (i % 5)
        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=600 + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 20)).isoformat(),
            "answers": {
                q_ids[0]: min(5, max(1, p_ability)),
                q_ids[1]: min(5, max(1, p_ability + (1 if i % 2 == 0 else 0))),
                q_ids[2]: min(5, max(1, p_ability - (1 if i % 3 == 0 else 0))),
                q_ids[3]: min(5, max(1, p_ability))
            }
        })
        assert sub_res.status_code == 201

    # 6. Gọi API ước lượng mô hình G-Theory
    res_g = client.post(f"/api/surveys/{survey_id}/analytics/g-theory", json={
        "item_question_ids": q_ids,
        "scope": "all"
    })
    assert res_g.status_code == 200
    data = res_g.json()
    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 24
    assert data["items_count"] == 4
    assert len(data["variance_components"]) == 3
    assert "current_design_metrics" in data
    assert "d_study_projections" in data
    assert "svg_chart" in data
    assert "<svg" in data["svg_chart"]
    assert "apa_narrative" in data
    assert "Generalizability Theory" in data["apa_narrative"]

    # 7. Kiểm tra audit log
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    events = audit_res.json()["events"]
    actions = [evt["action"] for evt in events]
    assert "G_THEORY_MODEL_EVALUATED" in actions
