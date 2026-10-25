"""
Integration tests for Causal Mediation Sensitivity Analysis API routes.
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_causal_mediation_sensitivity_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Employee Training, Self-Efficacy & Job Performance Mediation Study",
        "description": "Evaluating causal mechanism of job training on performance via self-efficacy with unmeasured confounding sensitivity"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Employee Training, Self-Efficacy & Job Performance Mediation Study",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Tham gia khóa đào tạo chuyên sâu (Training Treatment T)",
                "is_required": True,
                "options": [
                    {"label": "Đã tham gia (Treatment)", "value": "1"},
                    {"label": "Chưa tham gia (Control)", "value": "0"}
                ],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Mức độ tự tin năng lực chuyên môn (Self-Efficacy Mediator M)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Hiệu suất công việc đánh giá KPI (Performance Outcome Y)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Số năm kinh nghiệm làm việc (Experience Covariate X)",
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
    t_qid = questions[0]["id"]
    m_qid = questions[1]["id"]
    y_qid = questions[2]["id"]
    x_qid = questions[3]["id"]

    # 3. Check empty survey
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/causal-mediation-sensitivity", json={
        "treatment_question_id": t_qid,
        "mediator_question_id": m_qid,
        "outcome_question_id": y_qid,
        "covariate_question_ids": [x_qid]
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_RESPONSES", "INSUFFICIENT_SAMPLE"]

    # 4. Ingest 32 respondents
    np.random.seed(99)
    now_time = datetime.now(timezone.utc)

    for i in range(32):
        t_val = "1" if (i % 2 == 0) else "0"
        t_num = 1.0 if t_val == "1" else 0.0
        exp = float(np.random.uniform(1.0, 10.0))

        # Mediator: M = 2.0 + 1.2 * T + 0.15 * Exp + e_M
        m_val = 2.0 + 1.2 * t_num + 0.15 * exp + float(np.random.normal(0, 0.3))
        # Outcome: Y = 1.5 + 0.5 * T + 0.8 * M + 0.2 * Exp + e_Y
        y_val = 1.5 + 0.5 * t_num + 0.8 * m_val + 0.2 * exp + float(np.random.normal(0, 0.3))

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                t_qid: t_val,
                m_qid: str(round(m_val, 2)),
                y_qid: str(round(y_val, 2)),
                x_qid: str(round(exp, 1))
            },
            "started_at": (now_time - timedelta(minutes=45 + i)).isoformat(),
            "submitted_at": (now_time - timedelta(minutes=i)).isoformat()
        })
        assert sub_res.status_code in [200, 201]

    # 5. Execute Causal Mediation Sensitivity Analysis
    ana_res = client.post(f"/api/surveys/{survey_id}/analytics/causal-mediation-sensitivity", json={
        "treatment_question_id": t_qid,
        "mediator_question_id": m_qid,
        "outcome_question_id": y_qid,
        "covariate_question_ids": [x_qid],
        "scope": "all"
    })
    assert ana_res.status_code == 200
    data = ana_res.json()

    assert data["status"] == "success"
    assert data["sample_diagnostics"]["n_total"] == 32
    assert data["sample_diagnostics"]["n_treated"] == 16
    assert data["sample_diagnostics"]["n_control"] == 16

    # Verify path estimates
    paths = data["path_estimates"]
    assert paths["path_a"]["coefficient"] > 0
    assert paths["path_b"]["coefficient"] > 0
    assert "p_value" in paths["path_a"]

    # Verify baseline effects (ACME)
    effects = data["baseline_effects"]
    assert effects["acme"] > 0.4
    assert effects["total_effect"] > effects["acme"]
    assert effects["proportion_mediated"] > 0.3

    # Verify sensitivity analysis
    sens = data["sensitivity_analysis"]
    assert "critical_rho_threshold" in sens
    assert "robustness_level" in sens
    assert len(sens["sensitivity_curve"]) > 5

    # Verify SVG and APA narrative
    assert "<svg" in data["svg_chart"]
    assert "APA" in data["apa_narrative"] or "Imai" in data["apa_narrative"]

    # 6. Verify audit trail was logged
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    events = audit_res.json()["events"]
    cms_events = [e for e in events if e["action"] == "CAUSAL_MEDIATION_SENSITIVITY_EVALUATED"]
    assert len(cms_events) >= 1
