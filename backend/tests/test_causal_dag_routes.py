"""
Integration tests for Causal DAG & Structure Learning API routes.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_causal_dag_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Organizational Leadership & Engagement Causal Chain",
        "description": "Structure learning of drivers behind employee performance"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add 4 questions via PUT
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Organizational Leadership & Engagement Causal Chain",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Chất lượng lãnh đạo (Leadership Quality)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Môi trường tâm lý an toàn (Psychological Safety)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Mức độ gắn kết công việc (Work Engagement)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Hiệu suất đổi mới sáng tạo (Innovation Performance)",
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
    qids = [q["id"] for q in questions]

    # 3. Empty survey check
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/causal-dag", json={
        "question_ids": qids,
        "alpha": 0.05,
        "scope": "all"
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 4. Submit 25 responses simulating causal chain
    now = datetime.now(timezone.utc)
    for i in range(25):
        x1 = 5.0 + (i % 5) * 1.0
        x2 = 0.8 * x1 + 2.0 + (i % 3) * 0.5
        x3 = 0.7 * x2 + 1.5 + (i % 4) * 0.4
        x4 = 0.6 * x3 + 0.3 * x2 + 2.0

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=2000 + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 20)).isoformat(),
            "answers": {
                qids[0]: str(round(x1, 1)),
                qids[1]: str(round(x2, 1)),
                qids[2]: str(round(x3, 1)),
                qids[3]: str(round(x4, 1))
            }
        })
        assert sub_res.status_code in [200, 201]

    # 5. Evaluate Causal DAG
    dag_res = client.post(f"/api/surveys/{survey_id}/analytics/causal-dag", json={
        "question_ids": qids,
        "alpha": 0.05,
        "scope": "all"
    })
    assert dag_res.status_code == 200
    data = dag_res.json()
    assert data["status"] == "success"
    assert data["sample_size"] == 25
    assert data["variables_count"] == 4
    assert len(data["nodes"]) == 4
    assert "<svg" in data["svg_chart"]
    assert "Mạng lưới Nhân quả Có hướng" in data["apa_narrative"]

    # 6. Verify audit logs
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-logs")
    if audit_res.status_code == 200:
        logs = audit_res.json()
        actions = [log["action"] for log in logs]
        assert "CAUSAL_DAG_DISCOVERY_EVALUATED" in actions
