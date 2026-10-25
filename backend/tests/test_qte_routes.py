"""
Integration tests for Quantile Treatment Effects (QTE) API routes.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_qte_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Vocational Training Wage Impact Evaluation",
        "description": "Quantile treatment effects evaluation on trainee earnings distribution"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Vocational Training Wage Impact Evaluation",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Thu nhập hàng tháng sau đào tạo (Triệu VNĐ)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Tham gia chương trình đào tạo kỹ năng số",
                "is_required": True,
                "options": [
                    {"label": "Có tham gia", "value": "1"},
                    {"label": "Không tham gia", "value": "0"}
                ],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Số năm kinh nghiệm làm việc",
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
    assert len(questions) == 3
    q_outcome = questions[0]["id"]
    q_treatment = questions[1]["id"]
    q_cov = questions[2]["id"]

    # 3. Empty survey check
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/qte", json={
        "outcome_question_id": q_outcome,
        "treatment_question_id": q_treatment,
        "covariate_question_ids": [q_cov],
        "scope": "all"
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 4. Submit 30 responses (15 treated, 15 control)
    now = datetime.now(timezone.utc)
    for i in range(30):
        is_treated = 1 if i % 2 == 0 else 0
        exp = 1.0 + (i % 6)
        base_wage = 10.0 + 1.2 * exp
        wage = base_wage + (3.5 if is_treated else 0.0)

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=2000 + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 20)).isoformat(),
            "answers": {
                q_outcome: str(round(wage, 1)),
                q_treatment: str(is_treated),
                q_cov: str(exp)
            }
        })
        assert sub_res.status_code in [200, 201]

    # 5. Evaluate QTE
    qte_res = client.post(f"/api/surveys/{survey_id}/analytics/qte", json={
        "outcome_question_id": q_outcome,
        "treatment_question_id": q_treatment,
        "covariate_question_ids": [q_cov],
        "quantiles": [0.10, 0.25, 0.50, 0.75, 0.90],
        "scope": "all"
    })
    assert qte_res.status_code == 200
    data = qte_res.json()
    assert data["status"] == "success"
    assert data["sample_size"] == 30
    assert data["treated_count"] == 15
    assert data["control_count"] == 15
    assert data["average_treatment_effect"] > 0
    assert len(data["quantile_effects"]) == 5
    assert "<svg" in data["svg_chart"]
    assert "Semiparametric Quantile Treatment Effects" in data["apa_narrative"]

    # 6. Verify audit logs
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-logs")
    if audit_res.status_code == 200:
        logs = audit_res.json()
        actions = [log["action"] for log in logs]
        assert "QUANTILE_TREATMENT_EFFECTS_EVALUATED" in actions
