import pytest
import json
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_spatial_econometrics_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Geo Spatial Survey Study",
        "description": "Spatial econometrics test on field survey"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Covariate X
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Geo Spatial Survey Study",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Regional Price Index Y", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Local Transport Cost X", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    y_qid = q_objs[0]["id"]
    x_qid = q_objs[1]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 25 responses with GPS coordinates in client_metadata
    now_time = datetime.now(timezone.utc)
    for i in range(25):
        # 2 regional clusters: Hanoi vs HCMC
        is_north = (i % 2 == 0)
        base_lat = 21.0285 if is_north else 10.8231
        base_lon = 105.8542 if is_north else 106.6297
        lat = base_lat + (i * 0.005)
        lon = base_lon + (i * 0.005)

        x_val = 5.0 + (i % 5) * 1.2
        y_val = (20.0 if is_north else 10.0) + 1.5 * x_val

        meta = {
            "latitude": lat,
            "longitude": lon,
            "device_id": f"dev_{i}",
            "browser": "Chrome",
            "os": "Android"
        }

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    y_qid: str(round(y_val, 2)),
                    x_qid: str(round(x_val, 2)),
                },
                "client_metadata": meta,
                "started_at": (now_time - timedelta(minutes=60 - i * 2, seconds=30)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=60 - i * 2)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call spatial-econometrics endpoint
    res = client.post(
        f"/api/surveys/{survey_id}/analytics/spatial-econometrics",
        json={
            "outcome_question_id": y_qid,
            "covariate_question_ids": [x_qid],
            "weights_type": "inverse_distance",
            "scope": "all"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "morans_i" in data
    assert "spatial_lag_model" in data
    assert data["morans_i"]["morans_i"] > 0.0
    assert "rho" in data["spatial_lag_model"]
    assert "<svg" in data["svg_chart"]
    assert "Phân tích Kinh tế lượng Không gian" in data["apa_narrative"]


def test_spatial_econometrics_routes_missing_survey():
    res = client.post(
        "/api/surveys/missing-survey-id/analytics/spatial-econometrics",
        json={
            "outcome_question_id": "q1",
            "covariate_question_ids": ["q2"]
        }
    )
    assert res.status_code == 404
