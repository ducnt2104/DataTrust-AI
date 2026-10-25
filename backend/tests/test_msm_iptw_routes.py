"""
Integration tests for Marginal Structural Models (MSM) API routes.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_msm_iptw_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Longitudinal Micro-Credential Workforce Evaluation",
        "description": "Marginal Structural Model evaluation with time-varying confounding"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT: A1, A2, L1, L2, Y
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Longitudinal Micro-Credential Workforce Evaluation",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Đăng ký khóa học kỹ năng Đợt 1 (A1)",
                "is_required": True,
                "options": [{"label": "Có", "value": "1"}, {"label": "Không", "value": "0"}],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Đăng ký khóa học kỹ năng Đợt 2 (A2)",
                "is_required": True,
                "options": [{"label": "Có", "value": "1"}, {"label": "Không", "value": "0"}],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Mức độ áp lực công việc Đợt 1 (L1)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Mức độ áp lực công việc Đợt 2 (L2)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 4,
                "question_type": "number",
                "title": "Năng suất lao động cuối kỳ (Outcome Y)",
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
    assert len(questions) == 5
    q_a1 = questions[0]["id"]
    q_a2 = questions[1]["id"]
    q_l1 = questions[2]["id"]
    q_l2 = questions[3]["id"]
    q_y = questions[4]["id"]

    # 3. Empty survey check
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/msm-iptw", json={
        "treatment_question_ids": [q_a1, q_a2],
        "confounder_question_ids": [q_l1, q_l2],
        "outcome_question_id": q_y,
        "scope": "all"
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 4. Submit 30 responses
    now = datetime.now(timezone.utc)
    for i in range(30):
        a1 = 1 if i % 2 == 0 else 0
        l1 = 2.0 + (i % 5) * 1.0
        a2 = 1 if (a1 == 1 or l1 > 4.0) else 0
        l2 = 0.5 * l1 + 0.8 * a1 + 1.5
        cum_a = a1 + a2
        y = 50.0 + 3.0 * cum_a + 1.2 * l2

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=2000 + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 20)).isoformat(),
            "answers": {
                q_a1: str(a1),
                q_a2: str(a2),
                q_l1: str(round(l1, 1)),
                q_l2: str(round(l2, 1)),
                q_y: str(round(y, 1))
            }
        })
        assert sub_res.status_code in [200, 201]

    # 5. Evaluate MSM IPTW
    msm_res = client.post(f"/api/surveys/{survey_id}/analytics/msm-iptw", json={
        "treatment_question_ids": [q_a1, q_a2],
        "confounder_question_ids": [q_l1, q_l2],
        "outcome_question_id": q_y,
        "wave_labels": ["Đợt 1", "Đợt 2"],
        "scope": "all"
    })
    assert msm_res.status_code == 200
    data = msm_res.json()
    assert data["status"] == "success"
    assert data["sample_size"] == 30
    assert data["waves_count"] == 2
    assert "causal_effect_per_wave" in data
    assert "stabilized_weights_diagnostics" in data
    assert "<svg" in data["svg_chart"]
    assert "Marginal Structural Model" in data["apa_narrative"]

    # 6. Verify audit logs
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-logs")
    if audit_res.status_code == 200:
        logs = audit_res.json()
        actions = [log["action"] for log in logs]
        assert "MARGINAL_STRUCTURAL_MODEL_EVALUATED" in actions
