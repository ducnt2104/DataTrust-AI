import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_irt_2pl_routes_workflow():
    """Kiểm thử tích hợp đầu-cuối API Phân tích Mô hình IRT 2PL và Đường cong ICC."""
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey/analytics/irt-2pl", json={})
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Đánh Giá Đo Lường Năng Lực IRT 2PL",
        "description": "Kiểm định mô hình 2-Parameter Logistic IRT và đường cong đặc trưng ICC"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 3 câu hỏi đánh giá
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Đánh Giá Đo Lường Năng Lực IRT 2PL",
        "questions": [
            {
                "order_index": 0,
                "question_type": "rating",
                "title": "Kỹ năng tư duy logic",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Khả năng phân tích định lượng",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Năng lực giải quyết vấn đề",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")

    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    q1_id = public_q[0]["id"]
    q2_id = public_q[1]["id"]
    q3_id = public_q[2]["id"]

    # 4. Kiểm tra khi chưa có phản hồi nào
    res_empty = client.post(f"/api/surveys/{survey_id}/analytics/irt-2pl", json={})
    assert res_empty.status_code == 200
    assert res_empty.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 5. Gửi 10 phản hồi
    responses_data = [
        (5, 4, 3),
        (4, 5, 2),
        (3, 3, 1),
        (5, 5, 4),
        (2, 2, 1),
        (4, 4, 3),
        (5, 4, 2),
        (1, 2, 1),
        (4, 5, 4),
        (3, 4, 2)
    ]

    now = datetime.now(timezone.utc)
    for idx, (v1, v2, v3) in enumerate(responses_data):
        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=60 + idx)).isoformat(),
            "submitted_at": (now - timedelta(seconds=idx)).isoformat(),
            "answers": {
                q1_id: v1,
                q2_id: v2,
                q3_id: v3
            },
            "client_metadata": {"user_agent": "Pytest IRT Tester"}
        })
        assert sub_res.status_code == 201

    # 6. Gọi API IRT 2PL
    res_irt = client.post(f"/api/surveys/{survey_id}/analytics/irt-2pl", json={
        "question_ids": [q1_id, q2_id, q3_id],
        "scope": "all"
    })
    assert res_irt.status_code == 200
    irt_data = res_irt.json()

    assert irt_data["status"] == "SUCCESS"
    assert irt_data["sample_size"] == 10
    assert irt_data["num_items"] == 3
    assert "marginal_reliability" in irt_data
    assert len(irt_data["items"]) == 3
    assert len(irt_data["icc_curves"]) == 3
    assert "test_information_curve" in irt_data
    assert "apa_narrative" in irt_data
    assert "person_trait_summary" in irt_data

    # 7. Kiểm tra audit trail
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    actions = [evt["action"] for evt in audit_res.json()["events"]]
    assert "IRT_2PL_MODEL_EVALUATED" in actions
