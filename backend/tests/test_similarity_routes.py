"""
Integration tests for DataTrust Pairwise Similarity & Collusion Ring API routes
(POST & GET /api/surveys/{survey_id}/analytics/pairwise-similarity)
"""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
try:
    from app.main import app
except ModuleNotFoundError:
    from backend.app.main import app

client = TestClient(app)


def test_pairwise_similarity_empty_survey():
    """Kiểm thử khi khảo sát chưa có phản hồi nào (N = 0)"""
    res = client.post("/api/surveys", json={
        "title": "Khảo sát chưa có phản hồi",
        "description": "Pairwise similarity on empty dataset"
    })
    survey_id = res.json()["id"]

    # 1. Gọi GET
    get_res = client.get(f"/api/surveys/{survey_id}/analytics/pairwise-similarity")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["total_responses"] == 0
    assert data["high_risk_pairs"] == []
    assert data["collusion_rings"] == []
    assert data["summary"]["status"] == "CHƯA CÓ DỮ LIỆU"

    # 2. Gọi POST
    post_res = client.post(f"/api/surveys/{survey_id}/analytics/pairwise-similarity", json={
        "threshold": 0.85,
        "scope": "all"
    })
    assert post_res.status_code == 200
    assert post_res.json()["total_responses"] == 0


def test_pairwise_similarity_with_collusion_syndicate():
    """
    Kiểm thử phát hiện mạng lưới thông đồng (Collusion Syndicate Ring):
    Gửi 3 phản hồi bot farm cùng device_id, nộp cách nhau vài giây với câu trả lời gần như giống hệt.
    Gửi thêm 2 phản hồi độc lập từ người dùng thực.
    """
    # 1. Tạo và cấu hình khảo sát
    res = client.post("/api/surveys", json={
        "title": "Khảo sát Kiểm định An toàn Giao thông",
        "description": "Collusion Detection Test"
    })
    survey_id = res.json()["id"]
    slug = res.json()["public_slug"]

    q1_id = f"q1_{uuid.uuid4().hex[:6]}"
    q2_id = f"q2_{uuid.uuid4().hex[:6]}"
    q_text_id = f"q_text_{uuid.uuid4().hex[:6]}"

    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": q1_id,
                "question_type": "single_choice",
                "title": "Bạn sử dụng phương tiện gì?",
                "is_required": True,
                "options": [{"id": "car", "label": "Ô tô"}, {"id": "bike", "label": "Xe máy"}]
            },
            {
                "id": q2_id,
                "question_type": "rating",
                "title": "Đánh giá chất lượng mặt đường",
                "is_required": True,
                "options": []
            },
            {
                "id": q_text_id,
                "question_type": "long_text",
                "title": "Ý kiến đóng góp",
                "is_required": False,
                "options": []
            }
        ]
    })
    client.post(f"/api/surveys/{survey_id}/publish")

    base_time = datetime.now(timezone.utc)

    # 2. Gửi 3 phản hồi bot cùng một thiết bị device_bot_farm_01
    for i in range(3):
        submit_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (base_time + timedelta(seconds=i * 20)).isoformat(),
            "submitted_at": (base_time + timedelta(seconds=i * 20 + 15)).isoformat(),
            "client_metadata": {
                "device_id": "device_bot_farm_01",
                "ip_address": "203.113.152.1"
            },
            "answers": {
                q1_id: "car",
                q2_id: 5,
                q_text_id: "Hạ tầng đường xá hiện nay rất tốt và hoàn thiện"
            }
        })
        assert submit_res.status_code == 201

    # 3. Gửi 2 phản hồi độc lập khác biệt hoàn toàn
    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (base_time + timedelta(seconds=300)).isoformat(),
        "submitted_at": (base_time + timedelta(seconds=360)).isoformat(),
        "client_metadata": {"device_id": "device_user_clean_a"},
        "answers": {
            q1_id: "bike",
            q2_id: 1,
            q_text_id: "Nhiều ổ gà và chưa có đèn tín hiệu"
        }
    })

    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (base_time + timedelta(seconds=400)).isoformat(),
        "submitted_at": (base_time + timedelta(seconds=480)).isoformat(),
        "client_metadata": {"device_id": "device_user_clean_b"},
        "answers": {
            q1_id: "car",
            q2_id: 3,
            q_text_id: "Tạm chấp nhận được nhưng hay kẹt xe giờ cao điểm"
        }
    })

    # 4. Gọi API phân tích tương đồng
    api_res = client.get(f"/api/surveys/{survey_id}/analytics/pairwise-similarity?threshold=0.80")
    assert api_res.status_code == 200
    data = api_res.json()

    assert data["total_responses"] == 5
    assert data["matrix_size"] == 5
    assert len(data["matrix_nodes"]) == 5
    assert len(data["similarity_matrix"]) == 5
    for row in data["similarity_matrix"]:
        assert len(row) == 5

    # 5. Xác minh vòng thông đồng được phát hiện
    rings = data["collusion_rings"]
    assert len(rings) >= 1
    bot_ring = rings[0]
    assert bot_ring["member_count"] == 3
    assert bot_ring["threat_level"] == "CRITICAL"
    assert bot_ring["has_shared_device"] is True
    assert "Cách ly khẩn cấp" in bot_ring["recommended_action"]

    # 6. Kiểm tra các cặp nguy cơ cao
    pairs = data["high_risk_pairs"]
    assert len(pairs) >= 3
    # Phải có cặp có cùng device và is_collusion_syndicate = True
    collusion_pairs = [p for p in pairs if p.get("is_collusion_syndicate")]
    assert len(collusion_pairs) >= 3

    # 7. Kiểm tra tóm tắt thống kê & narrative
    summary = data["summary"]
    assert summary["collusion_rings_count"] >= 1
    assert summary["collusion_nodes_count"] == 3
    assert summary["highest_similarity"] >= 0.95
    assert summary["data_integrity_index"] < 100.0
    assert "CẢNH BÁO" in summary["status"]
    assert "AAPOR" in data["academic_narrative"]
