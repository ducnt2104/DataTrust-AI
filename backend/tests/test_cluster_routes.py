"""
Integration tests for Respondent Clustering & Segmentation API routes
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_survey_cluster_analysis_routes():
    # 1. Create a survey
    res = client.post("/api/surveys", json={
        "title": "Khảo Sát Phân Khúc Người Tiêu Dùng K-Means",
        "description": "Nghiên cứu phân cụm hồ sơ nhân vật (Persona Segmentation)",
        "instructions": "Trả lời câu hỏi bên dưới"
    })
    assert res.status_code == 201
    survey_id = res.json()["id"]
    slug = res.json()["public_slug"]

    # 2. Add 3 Likert scale questions
    q_res = client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q_brand_trust",
                "order_index": 0,
                "question_type": "likert",
                "title": "Mức độ tin tưởng thương hiệu",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "id": "q_tech_adoption",
                "order_index": 1,
                "question_type": "likert",
                "title": "Mức độ sẵn sàng ứng dụng công nghệ mới",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "id": "q_price_sensitivity",
                "order_index": 2,
                "question_type": "likert",
                "title": "Mức độ quan tâm đến giá thành sản phẩm",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            }
        ]
    })
    assert q_res.status_code == 200

    # Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    qids = [q["id"] for q in public_q]

    # 3. Submit 12 responses (6 Tech Enthusiasts with high trust & tech, 6 Price Conscious with high price concern)
    for i in range(6):
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                qids[0]: 5,
                qids[1]: 5,
                qids[2]: 1 + (i % 2)
            },
            "started_at": f"2026-10-23T15:00:{i:02d}Z",
            "submitted_at": f"2026-10-23T15:01:{i*10:02d}Z",
            "client_metadata": {"device_id": f"tech_user_{i}"}
        })

    for i in range(6):
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "answers": {
                qids[0]: 2,
                qids[1]: 1 + (i % 2),
                qids[2]: 5
            },
            "started_at": f"2026-10-23T15:05:{i:02d}Z",
            "submitted_at": f"2026-10-23T15:06:{i*10:02d}Z",
            "client_metadata": {"device_id": f"price_user_{i}"}
        })

    # 4. Call POST endpoint with k = 2
    post_res = client.post(f"/api/surveys/{survey_id}/analytics/clusters", json={
        "k": 2,
        "scope": "all"
    })
    assert post_res.status_code == 200
    data = post_res.json()

    assert data["survey_id"] == survey_id
    assert data["sample_size"] == 12
    assert data["chosen_k"] == 2
    assert "silhouette" in data
    assert data["silhouette"]["overall_score"] > 0.30
    assert "personas" in data
    assert len(data["personas"]) == 2
    assert "feature_importance" in data
    assert len(data["feature_importance"]) == 3
    assert data["feature_importance"][0]["f_ratio"] > 0
    assert "apa_narrative" in data
    assert len(data["apa_narrative"]) > 20

    # 5. Call GET endpoint
    get_res = client.get(f"/api/surveys/{survey_id}/analytics/clusters?scope=all")
    assert get_res.status_code == 200
    assert get_res.json()["sample_size"] == 12
