# -*- coding: utf-8 -*-
"""
Route tests for High-Dimensional Post-Double-Selection Lasso Endpoint.
(POST /api/surveys/{survey_id}/analytics/post-double-selection-lasso)
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)


def test_post_double_selection_lasso_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Workforce Training High-Dimensional Evaluation",
        "description": "Post-Double-Selection Lasso for high-dimensional observational survey"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions: Outcome Y, Treatment D, and 6 candidate controls
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Workforce Training High-Dimensional Evaluation",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Hourly Wage Rate ($)", "is_required": True},
            {"order_index": 1, "question_type": "number", "title": "Completed Training Certificate (0=No, 1=Yes)", "is_required": True},
            {"order_index": 2, "question_type": "number", "title": "Years of Prior Experience", "is_required": True},
            {"order_index": 3, "question_type": "number", "title": "Cognitive Aptitude Score", "is_required": True},
            {"order_index": 4, "question_type": "number", "title": "Age of Respondent", "is_required": True},
            {"order_index": 5, "question_type": "number", "title": "Regional Economic Index", "is_required": True},
            {"order_index": 6, "question_type": "number", "title": "Weekly Hours Worked", "is_required": True},
            {"order_index": 7, "question_type": "number", "title": "Baseline Technical Literacy", "is_required": True}
        ]
    })
    assert put_res.status_code == 200
    questions = put_res.json()["questions"]
    q_y = questions[0]["id"]
    q_d = questions[1]["id"]
    q_controls = [q["id"] for q in questions[2:]]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Ingest 45 synthetic respondents
    now_time = datetime.now(timezone.utc)
    rng = np.random.RandomState(888)

    for i in range(45):
        c_vals = [float(rng.normal(0, 1.0)) for _ in range(6)]
        # Treatment model: depends on C0, C1, C4
        d_latent = 0.7 * c_vals[0] + 0.5 * c_vals[1] + 0.8 * c_vals[4] + float(rng.normal(0, 0.7))
        d_val = 1.0 if d_latent > 0.0 else 0.0

        # Outcome model: Wage = 15.0 + 2.5 * D + 1.2 * C0 + 0.8 * C1 + 1.5 * C2 + eps
        eps = float(rng.normal(0, 0.8))
        wage = 15.0 + 2.5 * d_val + 1.2 * c_vals[0] + 0.8 * c_vals[1] + 1.5 * c_vals[2] + eps

        answers_dict = {
            q_y: str(round(wage, 2)),
            q_d: str(d_val)
        }
        for idx, cid in enumerate(q_controls):
            answers_dict[cid] = str(round(c_vals[idx], 2))

        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": answers_dict,
                "started_at": (now_time - timedelta(minutes=6)).isoformat(),
                "submitted_at": now_time.isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Call Post-Double-Selection Lasso Endpoint
    payload = {
        "outcome_question_id": q_y,
        "treatment_question_id": q_d,
        "candidate_control_question_ids": q_controls,
        "cv_folds": 4,
        "alpha_level": 0.05,
        "scope": "all"
    }

    res = client.post(f"/api/surveys/{survey_id}/analytics/post-double-selection-lasso", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "POST_DOUBLE_SELECTION_LASSO_BELLONI_2014"
    diag = data["diagnostics"]
    assert diag["sample_size"] == 45
    assert diag["total_candidate_controls"] == 6
    assert diag["union_selected_controls"] > 0

    est = data["estimates"]
    assert "post_double_selection_lasso" in est
    assert "naive_single_selection_lasso" in est
    assert "unadjusted_base_ols" in est
    assert est["post_double_selection_lasso"]["is_significant"] is True

    assert len(data["selected_controls"]) == 6
    assert "<svg" in data["svg_visualization"]
    assert "DataTrust" in data["apa_narrative"]
    assert "Belloni" in data["apa_narrative"]

    # 6. Test 404 for nonexistent survey
    err_res = client.post("/api/surveys/nonexistent-survey/analytics/post-double-selection-lasso", json=payload)
    assert err_res.status_code == 404

    # 7. Verify audit log entry
    with get_db() as conn:
        log_entry = conn.execute(
            "SELECT action FROM audit_logs WHERE entity_id = ? AND action = 'POST_DOUBLE_SELECTION_LASSO_EVALUATED'",
            (survey_id,)
        ).fetchone()
        assert log_entry is not None
