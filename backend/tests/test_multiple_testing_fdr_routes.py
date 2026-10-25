"""
Integration tests for Multiple Testing Correction & FDR Matrix API routes.
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_multiple_testing_fdr_custom_list():
    client = TestClient(app)

    create_res = client.post("/api/surveys", json={
        "title": "Hypotheses Family Testing Survey",
        "description": "FDR correction across custom battery of statistical tests"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]

    # Test Mode A: Custom p-values
    res = client.post(f"/api/surveys/{survey_id}/analytics/multiple-testing-fdr", json={
        "custom_p_values": [0.002, 0.015, 0.035, 0.048, 0.12, 0.45],
        "custom_labels": ["Test A", "Test B", "Test C", "Test D", "Test E", "Test F"],
        "fdr_q": 0.05
    })
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "success"
    assert data["sample_diagnostics"]["total_hypotheses_m"] == 6
    assert data["sample_diagnostics"]["bh_fdr_significant_count"] >= 1
    assert len(data["corrections"]) == 6
    assert "<svg" in data["svg_chart"]
    assert "Benjamini & Hochberg" in data["apa_narrative"]

    # Verify audit trail
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    events = audit_res.json()["events"]
    fdr_events = [e for e in events if e["action"] == "MULTIPLE_TESTING_FDR_EVALUATED"]
    assert len(fdr_events) >= 1


def test_multiple_testing_fdr_pairwise_survey_matrix():
    client = TestClient(app)

    create_res = client.post("/api/surveys", json={
        "title": "Multi-Item Consumer Sentiment Matrix Survey",
        "description": "Pairwise correlation battery with FDR control"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # Add 3 questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Multi-Item Consumer Sentiment Matrix Survey",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Mức độ tin cậy thương hiệu (Brand Trust)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Mức độ hài lòng sản phẩm (Satisfaction)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Ý định tái mua sắm (Repurchase Intent)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    client.post(f"/api/surveys/{survey_id}/publish")

    questions = client.get(f"/api/surveys/{survey_id}").json()["questions"]
    q_ids = [q["id"] for q in questions]

    # Ingest 20 responses
    np.random.seed(33)
    now_time = datetime.now(timezone.utc)

    for i in range(20):
        t_val = 5.0 + float(np.random.normal(0, 1))
        s_val = t_val * 0.8 + float(np.random.normal(0, 0.5))
        r_val = s_val * 0.7 + float(np.random.normal(0, 0.5))

        client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                q_ids[0]: str(round(t_val, 2)),
                q_ids[1]: str(round(s_val, 2)),
                q_ids[2]: str(round(r_val, 2))
            },
            "started_at": (now_time - timedelta(minutes=30 + i)).isoformat(),
            "submitted_at": (now_time - timedelta(minutes=i)).isoformat()
        })

    # Test Mode B: Pairwise question IDs
    res = client.post(f"/api/surveys/{survey_id}/analytics/multiple-testing-fdr", json={
        "question_ids": q_ids,
        "fdr_q": 0.05,
        "scope": "all"
    })
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "success"
    # 3 * 2 / 2 = 3 pairwise correlations
    assert data["sample_diagnostics"]["total_hypotheses_m"] == 3
    assert data["sample_diagnostics"]["bh_fdr_significant_count"] >= 1
    assert len(data["corrections"]) == 3
