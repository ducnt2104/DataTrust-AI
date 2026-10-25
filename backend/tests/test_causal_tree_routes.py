"""
Integration tests for Causal Interaction Trees & Honest Subgroup Identification API routes.
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app


def test_causal_tree_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Educational Intervention & Student Learning Gains Subgroup Study",
        "description": "Evaluating heterogeneous impacts of AI-assisted learning tool across student performance tiers"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Educational Intervention & Student Learning Gains Subgroup Study",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Nhóm sử dụng công cụ AI (Treatment T)",
                "is_required": True,
                "options": [
                    {"label": "Can thiệp AI (T=1)", "value": "1"},
                    {"label": "Đối chứng chuẩn (T=0)", "value": "0"}
                ],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "number",
                "title": "Điểm thi chuẩn hóa cuối kỳ (Exam Score Outcome Y)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "number",
                "title": "Điểm kiểm tra đầu vào (Baseline GPA X1)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "number",
                "title": "Số giờ tự học hàng tuần (Weekly Study Hours X2)",
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
    y_qid = questions[1]["id"]
    x1_qid = questions[2]["id"]
    x2_qid = questions[3]["id"]

    # 3. Check empty survey
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/causal-tree", json={
        "treatment_question_id": t_qid,
        "outcome_question_id": y_qid,
        "feature_question_ids": [x1_qid, x2_qid]
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] in ["NO_RESPONSES", "INSUFFICIENT_SAMPLE"]

    # 4. Ingest 40 respondents with heterogeneous effects
    np.random.seed(77)
    now_time = datetime.now(timezone.utc)

    for i in range(40):
        t_val = "1" if (i % 2 == 0) else "0"
        t_num = 1.0 if t_val == "1" else 0.0
        gpa = float(np.random.uniform(2.0, 4.0))
        hours = float(np.random.uniform(5.0, 30.0))

        # Heterogeneous effect: Students with low baseline GPA gain much more from AI intervention
        tau = 8.0 if gpa < 3.0 else 1.5
        score = 50.0 + 10.0 * gpa + 0.5 * hours + tau * t_num + float(np.random.normal(0, 1.0))

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                t_qid: t_val,
                y_qid: str(round(score, 2)),
                x1_qid: str(round(gpa, 2)),
                x2_qid: str(round(hours, 1))
            },
            "started_at": (now_time - timedelta(minutes=45 + i)).isoformat(),
            "submitted_at": (now_time - timedelta(minutes=i)).isoformat()
        })
        assert sub_res.status_code in [200, 201]

    # 5. Run Causal Tree Analysis
    tree_res = client.post(f"/api/surveys/{survey_id}/analytics/causal-tree", json={
        "treatment_question_id": t_qid,
        "outcome_question_id": y_qid,
        "feature_question_ids": [x1_qid, x2_qid],
        "max_depth": 3,
        "min_leaf_size": 4,
        "scope": "all"
    })
    assert tree_res.status_code == 200
    data = tree_res.json()

    assert data["status"] == "success"
    assert data["sample_diagnostics"]["n_total"] == 40
    assert data["sample_diagnostics"]["n_subgroups"] >= 1
    assert "ate_overall" in data["sample_diagnostics"]

    # Verify subgroups
    subgroups = data["subgroups"]
    assert len(subgroups) >= 1
    for s in subgroups:
        assert "tau_subgroup" in s
        assert "category" in s
        assert "is_significant" in s

    # Verify SVG and narrative
    assert "<svg" in data["svg_chart"]
    assert "Honest Causal Interaction Trees" in data["apa_narrative"] or "Athey & Imbens" in data["apa_narrative"]

    # 6. Verify audit trail was logged
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    events = audit_res.json()["events"]
    tree_events = [e for e in events if e["action"] == "CAUSAL_TREE_SUBGROUPS_EVALUATED"]
    assert len(tree_events) >= 1
