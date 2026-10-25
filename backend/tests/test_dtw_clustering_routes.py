"""
Integration tests for Dynamic Time Warping (DTW) Trajectory Clustering API routes.
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_dtw_clustering_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Longitudinal Digital Well-Being Trajectory Study",
        "description": "Multi-wave panel study tracking digital engagement trajectories across 4 quarters"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT (4 waves)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Longitudinal Digital Well-Being Trajectory Study",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Mức độ cam kết Quý 1 (Engagement Q1)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Mức độ cam kết Quý 2 (Engagement Q2)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Mức độ cam kết Quý 3 (Engagement Q3)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Mức độ cam kết Quý 4 (Engagement Q4)",
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

    # Retrieve question IDs
    get_survey = client.get(f"/api/surveys/{survey_id}")
    assert get_survey.status_code == 200
    questions = get_survey.json()["questions"]
    q1_id = questions[0]["id"]
    q2_id = questions[1]["id"]
    q3_id = questions[2]["id"]
    q4_id = questions[3]["id"]

    # 3. Check empty survey
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/dtw-clustering", json={
        "time_series_question_ids": [q1_id, q2_id, q3_id, q4_id]
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_RESPONSES", "INSUFFICIENT_SAMPLE"]

    # 4. Ingest 24 respondents (12 early risers, 12 steady decliners)
    np.random.seed(88)
    now_time = datetime.now(timezone.utc)

    for i in range(24):
        if i % 2 == 0:
            # Upward trajectory
            vals = [1.0, 2.5, 4.0, 6.0] + np.random.normal(0, 0.2, 4)
        else:
            # Downward trajectory
            vals = [6.0, 4.0, 2.5, 1.0] + np.random.normal(0, 0.2, 4)

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                q1_id: str(round(float(vals[0]), 2)),
                q2_id: str(round(float(vals[1]), 2)),
                q3_id: str(round(float(vals[2]), 2)),
                q4_id: str(round(float(vals[3]), 2))
            },
            "started_at": (now_time - timedelta(minutes=45 + i)).isoformat(),
            "submitted_at": (now_time - timedelta(minutes=i)).isoformat()
        })
        assert sub_res.status_code in [200, 201]

    # 5. Run DTW clustering analysis
    dtw_res = client.post(f"/api/surveys/{survey_id}/analytics/dtw-clustering", json={
        "time_series_question_ids": [q1_id, q2_id, q3_id, q4_id],
        "time_labels": ["Q1-2025", "Q2-2025", "Q3-2025", "Q4-2025"],
        "n_clusters": 2,
        "scope": "all"
    })
    assert dtw_res.status_code == 200
    data = dtw_res.json()

    assert data["status"] == "success"
    assert data["sample_diagnostics"]["n_total"] == 24
    assert data["sample_diagnostics"]["n_time_points"] == 4
    assert data["sample_diagnostics"]["n_clusters"] == 2
    assert "mean_silhouette_score" in data["sample_diagnostics"]

    # Clusters check
    assert len(data["clusters"]) == 2
    for c in data["clusters"]:
        assert c["size"] > 5
        assert len(c["mean_trajectory"]) == 4
        assert "archetype_title" in c

    # SVG & Narrative check
    assert "<svg" in data["svg_chart"]
    assert "Dynamic Time Warping" in data["apa_narrative"]

    # 6. Verify audit trail event logged
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    events = audit_res.json()["events"]
    dtw_events = [e for e in events if e["action"] == "DTW_TRAJECTORY_CLUSTERING_EVALUATED"]
    assert len(dtw_events) >= 1
