"""
Integration tests for Bifactor Psychometric Modeling API routes.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_bifactor_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Bifactor Mental Health Dimensionality Audit",
        "description": "Evaluating general distress factor saturation and subscale viability"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add 4 questions via PUT (2 Cognitive, 2 Somatic)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Bifactor Mental Health Dimensionality Audit",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Lo âu nhận thức 1 (Cognitive Worry 1)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Lo âu nhận thức 2 (Cognitive Worry 2)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Triệu chứng thể chất 1 (Somatic 1)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Triệu chứng thể chất 2 (Somatic 2)",
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
    q1 = questions[0]["id"]
    q2 = questions[1]["id"]
    q3 = questions[2]["id"]
    q4 = questions[3]["id"]

    # 3. Empty survey check
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/bifactor", json={
        "subscales": [
            {"subscale_name": "Cognitive", "question_ids": [q1, q2]},
            {"subscale_name": "Somatic", "question_ids": [q3, q4]}
        ],
        "scope": "all"
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_DATA", "INSUFFICIENT_SAMPLE"]

    # 4. Submit 20 responses
    now = datetime.now(timezone.utc)
    for i in range(20):
        g_trait = 3.0 + (i * 0.2)
        s1 = (i % 3) * 0.5
        s2 = (i % 2) * 0.4

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=1200 + i * 15)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 15)).isoformat(),
            "answers": {
                q1: g_trait + s1,
                q2: g_trait + s1 * 0.8,
                q3: g_trait + s2,
                q4: g_trait + s2 * 0.9
            }
        })
        assert sub_res.status_code == 201

    # 5. Run Bifactor Analysis
    bifactor_res = client.post(f"/api/surveys/{survey_id}/analytics/bifactor", json={
        "subscales": [
            {"subscale_name": "Cognitive", "question_ids": [q1, q2]},
            {"subscale_name": "Somatic", "question_ids": [q3, q4]}
        ],
        "scope": "all"
    })
    assert bifactor_res.status_code == 200
    data = bifactor_res.json()
    assert data["status"] == "success"
    assert data["sample_size"] == 20
    assert data["items_count"] == 4
    assert data["subscales_count"] == 2
    assert data["omega_total"] is not None
    assert data["omega_hierarchical"] is not None
    assert data["explained_common_variance"] is not None
    assert data["percent_uncontaminated_correlations"] is not None
    assert isinstance(data["is_essentially_unidimensional"], bool)
    assert len(data["subscale_metrics"]) == 2
    assert len(data["item_diagnostics"]) == 4
    assert "<svg" in data["svg_chart"]
    assert "Bifactor" in data["apa_narrative"]
