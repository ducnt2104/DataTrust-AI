import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_bsem_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "BSEM Survey Test",
        "description": "Testing Bayesian SEM with MCMC"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions via PUT
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "BSEM Survey Test",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Job Autonomy 1", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Job Autonomy 2", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Job Autonomy 3", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 3, "question_type": "number", "title": "Work Performance 1", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 4, "question_type": "number", "title": "Work Performance 2", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 5, "question_type": "number", "title": "Work Performance 3", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    q1_id = q_objs[0]["id"]
    q2_id = q_objs[1]["id"]
    q3_id = q_objs[2]["id"]
    q4_id = q_objs[3]["id"]
    q5_id = q_objs[4]["id"]
    q6_id = q_objs[5]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Submit 25 responses
    now_time = datetime.now(timezone.utc)
    for i in range(25):
        val_f1 = 3.0 + (i % 3) * 0.5
        val_f2 = 2.5 + 0.6 * val_f1 + (i % 2) * 0.3
        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    q1_id: str(round(val_f1 + 0.1, 2)),
                    q2_id: str(round(val_f1 - 0.1, 2)),
                    q3_id: str(round(val_f1 + 0.2, 2)),
                    q4_id: str(round(val_f2 + 0.1, 2)),
                    q5_id: str(round(val_f2 - 0.2, 2)),
                    q6_id: str(round(val_f2 + 0.1, 2))
                },
                "started_at": (now_time - timedelta(minutes=30 + i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=i)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Request BSEM Analysis
    bsem_payload = {
        "measurement_spec": {
            "Autonomy": [q1_id, q2_id, q3_id],
            "Performance": [q4_id, q5_id, q6_id]
        },
        "structural_regressions": [
            {"source": "Autonomy", "target": "Performance"}
        ],
        "prior_cross_loading_sd": 0.01,
        "n_iterations": 300,
        "n_burnin": 100,
        "n_chains": 2,
        "scope": "all"
    }

    res = client.post(f"/api/surveys/{survey_id}/analytics/bsem", json=bsem_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["sample_diagnostics"]["n_observations"] == 25
    assert len(data["structural_paths"]) == 1
    assert data["structural_paths"][0]["source_factor"] == "Autonomy"
    assert data["structural_paths"][0]["target_factor"] == "Performance"
    assert len(data["loadings"]) == 12
    assert len(data["prior_sensitivity"]) == 4
    assert "<svg" in data["svg_chart"]
    assert "Muthén & Asparouhov" in data["apa_narrative"]

    # 6. Verify audit trail
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    events = [e["action"] for e in audit_res.json()["events"]]
    assert "BSEM_EVALUATED" in events


def test_bsem_routes_validation_and_errors():
    # Non-existent survey
    res_404 = client.post(
        "/api/surveys/non-existent-survey-id/analytics/bsem",
        json={"measurement_spec": {"F1": ["q1", "q2"], "F2": ["q3", "q4"]}}
    )
    assert res_404.status_code == 404

    # Insufficient questions (< 4)
    survey_payload = {
        "title": "BSEM Small Test",
        "description": "Testing validation"
    }
    c_res = client.post("/api/surveys", json=survey_payload)
    sid = c_res.json()["id"]

    res_400 = client.post(
        f"/api/surveys/{sid}/analytics/bsem",
        json={"measurement_spec": {"F1": ["qa"], "F2": ["qb"]}}
    )
    assert res_400.status_code == 400
    assert "tối thiểu 4" in res_400.json()["detail"]
