import pytest
import numpy as np
import scipy.stats
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_gaussian_copula_routes_end_to_end():
    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Copula Endogeneity Test Survey",
        "description": "Testing Park & Gupta 2012 Gaussian Copula"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add questions
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Copula Endogeneity Test Survey",
        "questions": [
            {"order_index": 0, "question_type": "number", "title": "Endogenous Training Hours (P)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 1, "question_type": "number", "title": "Sales Performance (Y)", "is_required": True, "options": [], "logic_rules": []},
            {"order_index": 2, "question_type": "number", "title": "Prior Experience (X1)", "is_required": True, "options": [], "logic_rules": []}
        ]
    })
    assert put_res.status_code == 200
    q_objs = put_res.json()["questions"]
    p_qid = q_objs[0]["id"]
    y_qid = q_objs[1]["id"]
    x_qid = q_objs[2]["id"]

    # 3. Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    # 4. Generate 45 responses via bivariate Gaussian copula
    rng = np.random.RandomState(42)
    N = 45
    rho_true = 0.6
    cov_mat = np.array([[1.0, rho_true], [rho_true, 1.0]])
    z = rng.multivariate_normal([0, 0], cov_mat, size=N)
    u_p = scipy.stats.norm.cdf(z[:, 0])
    P = -2.0 * np.log(1.0 - np.clip(u_p, 1e-6, 1.0 - 1e-6))
    X1 = rng.normal(5.0, 1.0, size=N)
    eps = 1.2 * z[:, 1]
    Y = 10.0 + 2.0 * P + 0.8 * X1 + eps

    now_time = datetime.now(timezone.utc)
    for i in range(N):
        sub_res = client.post(
            f"/api/public/surveys/{slug}/submit",
            json={
                "answers": {
                    p_qid: str(round(float(P[i]), 2)),
                    y_qid: str(round(float(Y[i]), 2)),
                    x_qid: str(round(float(X1[i]), 2))
                },
                "started_at": (now_time - timedelta(minutes=60 + i)).isoformat(),
                "submitted_at": (now_time - timedelta(minutes=i)).isoformat()
            }
        )
        assert sub_res.status_code in [200, 201]

    # 5. Run Gaussian Copula Analysis
    cop_res = client.post(
        f"/api/surveys/{survey_id}/analytics/gaussian-copula",
        json={
            "endogenous_question_id": p_qid,
            "outcome_question_id": y_qid,
            "control_question_ids": [x_qid],
            "n_bootstraps": 100,
            "scope": "all"
        }
    )
    assert cop_res.status_code == 200
    data = cop_res.json()
    assert data["status"] == "success"
    assert data["sample_diagnostics"]["n_observations"] == N
    assert "naive_ols" in data
    assert "copula_corrected" in data
    assert "<svg" in data["svg_chart"]
    assert "Park & Gupta" in data["apa_narrative"]

    # 6. Verify audit trail
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    events = [e["action"] for e in audit_res.json()["events"]]
    assert "GAUSSIAN_COPULA_EVALUATED" in events


def test_gaussian_copula_routes_validation_and_errors():
    # 404
    res_404 = client.post(
        "/api/surveys/non-existent-survey/analytics/gaussian-copula",
        json={"endogenous_question_id": "p", "outcome_question_id": "y"}
    )
    assert res_404.status_code == 404

    # 400 when question IDs don't exist
    create_res = client.post("/api/surveys", json={"title": "Small"})
    sid = create_res.json()["id"]
    res_400 = client.post(
        f"/api/surveys/{sid}/analytics/gaussian-copula",
        json={"endogenous_question_id": "fake_p", "outcome_question_id": "fake_y"}
    )
    assert res_400.status_code == 400
