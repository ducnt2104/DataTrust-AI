"""
Integration tests for Extreme Value Theory (EVT) API routes.
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient
from app.main import app


def test_extreme_value_routes_lifecycle():
    client = TestClient(app)

    # 1. Create survey
    create_res = client.post("/api/surveys", json={
        "title": "Survey Operational Latency & Outlier Risk",
        "description": "EVT analysis on server response times and customer claim amounts"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Add question via PUT: Metric Question (e.g. claim loss amount / response latency)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Survey Operational Latency & Outlier Risk",
        "questions": [
            {
                "order_index": 0,
                "question_type": "number",
                "title": "Giá trị yêu cầu bồi thường (Triệu VNĐ)",
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

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    q_metric = survey_data["questions"][0]["id"]

    # 3. Empty survey check -> INSUFFICIENT_SAMPLE
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/extreme-value", json={
        "metric_question_id": q_metric,
        "threshold_percentile": 0.85
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 4. Ingest 60 responses with heavy-tailed Pareto values
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    np.random.seed(42)
    pareto_vals = (np.random.pareto(a=2.0, size=60) * 15.0 + 5.0).tolist()

    for idx, val in enumerate(pareto_vals):
        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=3000 + idx * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=idx * 20)).isoformat(),
            "answers": {
                q_metric: str(round(float(val), 2))
            }
        })
        assert submit_res.status_code in [200, 201]

    # 5. Run EVT analysis
    evt_res = client.post(f"/api/surveys/{survey_id}/analytics/extreme-value", json={
        "metric_question_id": q_metric,
        "threshold_percentile": 0.75,
        "alpha_levels": [0.95, 0.99]
    })
    assert evt_res.status_code == 200
    evt_data = evt_res.json()

    assert evt_data["status"] == "success"
    assert evt_data["sample_size"] == 60
    assert evt_data["threshold"] > 0
    assert evt_data["exceedances_count"] >= 5
    assert evt_data["scale_sigma"] > 0
    assert "tail_classification" in evt_data
    assert len(evt_data["risk_measures"]) == 2
    assert "<svg" in evt_data["svg_chart"]
    assert "Pickands" in evt_data["apa_narrative"]
