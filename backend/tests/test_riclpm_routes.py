"""
Route tests for Random-Intercept Cross-Lagged Panel Model (RI-CLPM) Endpoint
(POST /api/surveys/{survey_id}/analytics/riclpm)
DataTrust Iteration 187
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import numpy as np
from app.main import app

client = TestClient(app)


def test_riclpm_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "DataTrust RI-CLPM Longitudinal Survey",
        "description": "Multi-wave dynamic reciprocal causal transmission (Hamaker et al. 2015)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions for 3 waves: X1, X2, X3 and Y1, Y2, Y3
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "DataTrust RI-CLPM Longitudinal Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Nỗ Lực Học Tập T1 (X1)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Nỗ Lực Học Tập T2 (X2)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Nỗ Lực Học Tập T3 (X3)", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Điểm Số Học Kỳ T1 (Y1)", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Điểm Số Học Kỳ T2 (Y2)", "is_required": True},
            {"order_index": 5, "question_type": "number", "title": "Điểm Số Học Kỳ T3 (Y3)", "is_required": True},
        ]
    })
    assert put_res.status_code == 200

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Fetch question IDs
    detail_res = client.get(f"/api/surveys/{survey_id}")
    assert detail_res.status_code == 200
    questions = detail_res.json()["questions"]
    x_qids = [questions[0]["id"], questions[1]["id"], questions[2]["id"]]
    y_qids = [questions[3]["id"], questions[4]["id"], questions[5]["id"]]

    # 5. Submit 40 longitudinal responses
    np.random.seed(42)
    now = datetime.now(timezone.utc)
    N = 40
    T = 3

    traits = np.random.multivariate_normal([0, 0], [[1.0, 0.4], [0.4, 1.0]], size=N)
    IX, IY = traits[:, 0], traits[:, 1]
    wx, wy = np.zeros((N, T)), np.zeros((N, T))
    wx[:, 0], wy[:, 0] = np.random.normal(0, 0.5, size=N), np.random.normal(0, 0.5, size=N)
    for t in range(T - 1):
        wx[:, t + 1] = 0.4 * wx[:, t] + 0.15 * wy[:, t] + np.random.normal(0, 0.4, size=N)
        wy[:, t + 1] = 0.35 * wy[:, t] + 0.30 * wx[:, t] + np.random.normal(0, 0.4, size=N)

    for i in range(N):
        answers = {}
        for t in range(T):
            x_val = float(10.0 + IX[i] + wx[i, t])
            y_val = float(20.0 + IY[i] + wy[i, t])
            answers[x_qids[t]] = str(round(x_val, 2))
            answers[y_qids[t]] = str(round(y_val, 2))

        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": answers,
            "started_at": (now - timedelta(minutes=5)).isoformat(),
            "submitted_at": now.isoformat()
        })
        assert submit_res.status_code == 201

    # 6. Call RI-CLPM endpoint
    res_riclpm = client.post(f"/api/surveys/{survey_id}/analytics/riclpm", json={
        "x_question_ids": x_qids,
        "y_question_ids": y_qids,
        "var_x_name": "NoLucHocTap",
        "var_y_name": "DiemSoHocKy",
        "wave_labels": ["HocKy 1", "HocKy 2", "HocKy 3"],
        "n_bootstraps": 20,
        "scope": "all"
    })

    assert res_riclpm.status_code == 200
    data = res_riclpm.json()

    assert data["status"] == "success"
    assert data["sample_size"] == N
    assert data["waves_count"] == 3
    assert "between_person_traits" in data
    assert "within_person_dynamics" in data
    assert len(data["within_person_dynamics"]["wave_transitions"]) == 2
    assert "goodness_of_fit" in data
    assert data["goodness_of_fit"]["cfi"] >= 0.85
    assert "<svg" in data["svg_visualization"]
    assert "Random-Intercept Cross-Lagged Panel Model" in data["apa_narrative"]
