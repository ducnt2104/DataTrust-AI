import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_psychometric_network_routes_workflow():
    """Kiểm thử tích hợp đầu-cuối API Phân tích Mạng Lưới Tâm lý học Đo lường (GGM)."""
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey/analytics/psychometric-network", json={})
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Đánh Giá Cấu Trúc Hệ Thống Mạng Lưới Tâm Lý Học",
        "description": "Kiểm định mô hình đồ thị Gaussian GGM và các chỉ số trung tâm mạng lưới"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 4 câu hỏi định lượng
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Đánh Giá Cấu Trúc Hệ Thống Mạng Lưới Tâm Lý Học",
        "questions": [
            {
                "order_index": 0,
                "question_type": "rating",
                "title": "Chất lượng dịch vụ",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Trải nghiệm người dùng",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Mức độ hài lòng",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "rating",
                "title": "Khả năng giới thiệu",
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
    q4_id = public_q[3]["id"]

    # 4. Kiểm tra khi chưa có phản hồi nào
    res_empty = client.post(f"/api/surveys/{survey_id}/analytics/psychometric-network", json={})
    assert res_empty.status_code == 200
    assert res_empty.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 5. Gửi 8 phản hồi mô phỏng
    responses_data = [
        (5, 5, 4, 4),
        (4, 5, 4, 5),
        (3, 3, 2, 2),
        (5, 4, 5, 5),
        (2, 2, 2, 2),
        (4, 4, 4, 4),
        (3, 4, 3, 3),
        (5, 5, 5, 4)
    ]

    now = datetime.now(timezone.utc)
    for idx, (v1, v2, v3, v4) in enumerate(responses_data):
        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=60 + idx)).isoformat(),
            "submitted_at": (now - timedelta(seconds=idx)).isoformat(),
            "answers": {
                q1_id: v1,
                q2_id: v2,
                q3_id: v3,
                q4_id: v4
            },
            "client_metadata": {"user_agent": "Pytest Network Tester"}
        })
        assert sub_res.status_code == 201

    # 6. Gọi API Network Analysis
    res_analysis = client.post(f"/api/surveys/{survey_id}/analytics/psychometric-network", json={
        "regularization_threshold": 0.05,
        "scope": "all"
    })
    assert res_analysis.status_code == 200
    data = res_analysis.json()

    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 8
    assert data["num_nodes"] == 4
    assert data["possible_edges"] == 6
    assert len(data["nodes"]) == 4
    assert "density" in data
    assert "apa_narrative" in data
    assert "Psychometric Network Analysis" in data["apa_narrative"]

    # 7. Xác minh audit trail ghi nhận SHA-256
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    events = audit_res.json()["events"]
    assert any(e["action"] == "PSYCHOMETRIC_NETWORK_ANALYSIS_EVALUATED" for e in events)
