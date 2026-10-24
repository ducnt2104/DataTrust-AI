# -*- coding: utf-8 -*-
"""
Route integration tests for Interactive Fixed Effects (IFE) Causal Panel Engine
Bai (2009); Gobillon & Magnac (2016)
"""
import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_interactive_fixed_effects_route_success():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Interactive Fixed Effects Macroeconomic Survey",
        "description": "Estimating treatment effects under multidimensional latent factor structures"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Interactive Fixed Effects Macroeconomic Survey",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Chỉ số Hiệu quả Doanh nghiệp (Outcome Y)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Mã Định danh Đơn vị (Unit i)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Kỳ Khảo sát (Time t)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "single_choice",
                "title": "Chỉ báo Chính sách (Treatment W)",
                "is_required": True,
                "options": [
                    {"value": "1", "label": "Can thiệp (Treated)"},
                    {"value": "0", "label": "Đối chứng (Control)"}
                ],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200
    questions = put_res.json()["questions"]
    qid_y = questions[0]["id"]
    qid_u = questions[1]["id"]
    qid_t = questions[2]["id"]
    qid_w = questions[3]["id"]

    # Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 3. Submit 24 observations (6 units x 4 time periods)
    # Units 0..3: Control (W=0)
    # Units 4, 5: Treated at period 3, 4 (W=1)
    np.random.seed(42)
    now_time = datetime.now(timezone.utc)
    resp_idx = 0

    f_t = [0.8, -0.5, 1.4, -1.0]
    gamma_u = [1.2, -0.6, 0.4, -1.1, 1.5, -0.8]

    for u in range(6):
        u_base = 20.0 + u * 3.0
        for t_idx, t in enumerate([1.0, 2.0, 3.0, 4.0]):
            is_treated = (u >= 4 and t >= 3.0)
            tau = 4.0 if is_treated else 0.0
            noise = float(np.random.normal(0, 0.1))
            y = round(u_base + 2.0 * t + gamma_u[u] * f_t[t_idx] + tau + noise, 2)
            w = "1" if is_treated else "0"

            started = (now_time - timedelta(minutes=60 - resp_idx)).isoformat()
            submitted = (now_time - timedelta(minutes=58 - resp_idx)).isoformat()
            resp_idx += 1

            resp = client.post(
                f"/api/public/surveys/{slug}/submit",
                json={
                    "answers": {
                        qid_y: y,
                        qid_u: float(u + 1),
                        qid_t: t,
                        qid_w: w
                    },
                    "started_at": started,
                    "submitted_at": submitted
                }
            )
            assert resp.status_code == 201

    # 4. Call IFE endpoint
    ife_res = client.post(f"/api/surveys/{survey_id}/analytics/interactive-fixed-effects", json={
        "outcome_question_id": qid_y,
        "unit_question_id": qid_u,
        "time_question_id": qid_t,
        "treatment_question_id": qid_w,
        "scope": "all"
    })

    assert ife_res.status_code == 200
    data = ife_res.json()
    assert data["status"] == "SUCCESS"
    assert data["model_type"] == "INTERACTIVE_FIXED_EFFECTS_BAI_2009"
    diag = data["diagnostics"]
    assert diag["n_units"] == 6
    assert diag["n_time_periods"] == 4
    assert diag["n_treated_cells"] == 4  # 2 units * 2 periods
    assert "tau_ife" in diag
    assert "se_ife" in diag
    assert "z_statistic" in diag
    assert "p_value" in diag
    assert "ci_lower_95" in diag
    assert "ci_upper_95" in diag
    assert "tau_twfe" in diag
    assert "factor_bias_gap" in diag
    assert "pesaran_cd_statistic" in diag
    assert "<svg" in data["svg_visualization"]
    assert "Interactive Fixed Effects" in data["apa_narrative"]
    assert len(data["latent_factors"]) > 0
    assert len(data["scree_spectrum"]) > 0


def test_interactive_fixed_effects_validation_errors():
    # Non-existent survey
    bad_res = client.post("/api/surveys/non-existent-survey-uuid/analytics/interactive-fixed-effects", json={
        "outcome_question_id": "q1",
        "unit_question_id": "q2",
        "time_question_id": "q3",
        "treatment_question_id": "q4"
    })
    assert bad_res.status_code == 404

    # Create survey but provide invalid QID
    s = client.post("/api/surveys", json={"title": "Test Survey IFE Validation"}).json()
    survey_id = s["id"]

    bad_qid_res = client.post(f"/api/surveys/{survey_id}/analytics/interactive-fixed-effects", json={
        "outcome_question_id": "invalid_q",
        "unit_question_id": "q2",
        "time_question_id": "q3",
        "treatment_question_id": "q4"
    })
    assert bad_qid_res.status_code == 400
    assert "không tồn tại" in bad_qid_res.json()["detail"]
