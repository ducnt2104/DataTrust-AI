"""
Integration tests for Multilevel Structural Equation Modeling (MSEM) API routes.
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_msem_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Organizational Leadership & Team Innovation Multilevel Survey",
        "description": "Testing 1-1-1 multilevel mediation across departments without conflation bias"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Organizational Leadership & Team Innovation Multilevel Survey",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Phòng ban / Đơn vị (Department Cluster ID)",
                "is_required": True,
                "options": [
                    {"label": f"Phòng {i}", "value": f"Dept_{i}"} for i in range(1, 7)
                ],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Hỗ trợ từ lãnh đạo (Leadership Support X)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "An toàn tâm lý đội ngũ (Psychological Safety M)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Đổi mới sáng tạo cá nhân (Individual Innovation Y)",
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
    c_qid = questions[0]["id"]
    x_qid = questions[1]["id"]
    m_qid = questions[2]["id"]
    y_qid = questions[3]["id"]

    # 3. Check empty survey
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/msem", json={
        "cluster_question_id": c_qid,
        "x_question_id": x_qid,
        "m_question_id": m_qid,
        "y_question_id": y_qid
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_RESPONSES", "INSUFFICIENT_SAMPLE"]

    # 4. Ingest 28 responses across 6 departments
    np.random.seed(88)
    now_time = datetime.now(timezone.utc)
    resp_count = 0

    for d in range(1, 7):
        dept_name = f"Dept_{d}"
        dept_x = float(np.random.normal(3.5, 0.8))
        dept_m = float(0.7 * dept_x + np.random.normal(0.0, 0.4))
        dept_y = float(0.9 * dept_m + 0.3 * dept_x + np.random.normal(0.0, 0.4))

        for k in range(5 if d <= 4 else 4):
            resp_count += 1
            ind_x = float(np.random.normal(0.0, 0.6))
            ind_m = float(0.4 * ind_x + np.random.normal(0.0, 0.3))
            ind_y = float(0.5 * ind_m + 0.2 * ind_x + np.random.normal(0.0, 0.3))

            x_val = min(5.0, max(1.0, dept_x + ind_x))
            m_val = min(5.0, max(1.0, dept_m + ind_m))
            y_val = min(5.0, max(1.0, dept_y + ind_y))

            sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
                "answers": {
                    c_qid: dept_name,
                    x_qid: str(round(x_val, 2)),
                    m_qid: str(round(m_val, 2)),
                    y_qid: str(round(y_val, 2))
                },
                "started_at": (now_time - timedelta(minutes=60 + resp_count)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=resp_count)).isoformat()
            })
            assert sub_res.status_code in [200, 201]

    # 5. Run MSEM Analysis
    msem_res = client.post(f"/api/surveys/{survey_id}/analytics/msem", json={
        "cluster_question_id": c_qid,
        "x_question_id": x_qid,
        "m_question_id": m_qid,
        "y_question_id": y_qid,
        "n_mc_sims": 1000,
        "scope": "all"
    })
    assert msem_res.status_code == 200
    data = msem_res.json()

    assert data["status"] == "success"
    assert data["sample_diagnostics"]["n_total"] == 28
    assert data["sample_diagnostics"]["n_clusters"] == 6
    assert data["intraclass_correlations"]["icc_x"] > 0
    assert "a_path" in data["level1_within_submodel"]
    assert "indirect_effect" in data["level1_within_submodel"]
    assert "a_path" in data["level2_between_submodel"]
    assert "indirect_effect" in data["level2_between_submodel"]
    assert "<svg" in data["svg_chart"]
    assert "APA 7th" in data["apa_narrative"]
