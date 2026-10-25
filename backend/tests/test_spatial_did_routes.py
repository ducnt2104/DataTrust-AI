"""
Route tests for Semiparametric Spatial Difference-in-Differences Endpoint
(POST /api/surveys/{survey_id}/analytics/spatial-did)
DataTrust Iteration 182
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_spatial_did_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust Spatial Difference-in-Differences Survey",
        "description": "Assessment of regional economic development policy and spatial spillover (Delgado & Florax 2015)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: outcome, treatment, latitude, longitude, covariate
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust Spatial Difference-in-Differences Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Tăng trưởng Doanh thu Chi nhánh (Outcome Y)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Chính sách Hỗ trợ Đổi mới (Treatment D: 1/0)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Vĩ độ Tọa độ Địa lý (Latitude)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Kinh độ Tọa độ Địa lý (Longitude)", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Quy mô Nhân sự (Covariate X)", "is_required": False}
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Fetch questions to get IDs
    detail_res = client.get(f"/api/surveys/{survey_id}")
    assert detail_res.status_code == 200
    questions = detail_res.json()["questions"]
    y_qid = questions[0]["id"]
    d_qid = questions[1]["id"]
    lat_qid = questions[2]["id"]
    lon_qid = questions[3]["id"]
    x_qid = questions[4]["id"]

    # 5. Simulate 40 observations
    np.random.seed(42)
    n = 40
    now = datetime.now(timezone.utc)

    for i in range(n):
        lat_val = 10.0 + (i % 6) * 1.5
        lon_val = 106.0 + (i // 6) * 1.2
        d_val = 1 if (i % 2 == 0) else 0
        x_val = float(np.random.normal(50.0, 10.0))
        y_val = 50.0 + 8.0 * d_val + 0.4 * x_val + float(np.random.normal(0, 2.0))

        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                y_qid: str(round(y_val, 2)),
                d_qid: str(d_val),
                lat_qid: str(round(lat_val, 4)),
                lon_qid: str(round(lon_val, 4)),
                x_qid: str(round(x_val, 2))
            },
            "started_at": (now - timedelta(minutes=5)).isoformat(),
            "submitted_at": now.isoformat()
        })
        assert submit_res.status_code == 201

    # 6. Execute Spatial Difference-in-Differences endpoint
    payload = {
        "treatment_question_id": d_qid,
        "outcome_question_id": y_qid,
        "lat_field": lat_qid,
        "lon_field": lon_qid,
        "covariate_question_ids": [x_qid],
        "weight_type": "inverse_distance",
        "power": 1.0,
        "scope": "all"
    }

    eval_res = client.post(f"/api/surveys/{survey_id}/analytics/spatial-did", json=payload)
    assert eval_res.status_code == 200
    data = eval_res.json()

    assert data["status"] == "success"
    assert data["sample_size"] == 40
    assert "direct_effect" in data
    assert "spillover_effect" in data
    assert "total_impact" in data
    assert "morans_i_diagnostic" in data
    assert "<svg" in data["svg_visualization"]
    assert "DataTrust" in data["apa_narrative"]

    # 7. Test 404 for nonexistent survey
    fake_res = client.post("/api/surveys/nonexistent-uuid-999/analytics/spatial-did", json=payload)
    assert fake_res.status_code == 404
