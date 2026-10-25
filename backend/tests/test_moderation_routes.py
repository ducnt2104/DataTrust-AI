"""
API Route integration tests for Statistical Moderation & Interaction Effects (PROCESS Model 1).
"""

from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_moderation_route_workflow():
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-id/analytics/moderation", json={
        "independent_question_id": "q1",
        "moderator_question_id": "q2",
        "dependent_question_id": "q3"
    })
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát thử nghiệm điều tiết
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Thực Nghiệm Tác Động Điều Tiết (PROCESS Model 1)",
        "description": "Kiểm định vai trò điều tiết của Tech Readiness lên Leadership -> Performance"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 3 câu hỏi thang đo
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Thực Nghiệm Tác Động Điều Tiết (PROCESS Model 1)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "rating",
                "title": "X: Phong cách lãnh đạo",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "W: Mức độ sẵn sàng công nghệ",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Y: Hiệu quả công việc",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")
    surv_data = client.get(f"/api/surveys/{survey_id}").json()
    qs = surv_data["questions"]
    x_id = qs[0]["id"]
    w_id = qs[1]["id"]
    y_id = qs[2]["id"]

    # 4. Kiểm tra lỗi 400 nếu truyền trùng biến
    res_400 = client.post(f"/api/surveys/{survey_id}/analytics/moderation", json={
        "independent_question_id": x_id,
        "moderator_question_id": x_id,
        "dependent_question_id": y_id
    })
    assert res_400.status_code == 400

    # 5. Gửi 15 phản hồi thử nghiệm
    now = datetime.now(timezone.utc)
    for idx in range(15):
        xv = str(1 + (idx % 5))
        wv = str(1 + ((idx + 2) % 5))
        # Y thang 1-5:
        base_y = 1 + ((int(xv) + int(wv)) % 5)
        yv = str(base_y)

        sub_body = {
            "started_at": (now - timedelta(minutes=25 - idx, seconds=30)).isoformat(),
            "submitted_at": (now - timedelta(minutes=25 - idx)).isoformat(),
            "answers": {
                x_id: xv,
                w_id: wv,
                y_id: yv
            },
            "client_metadata": {
                "ip_hash": f"ip_mod_{idx}",
                "user_agent": "Mozilla/5.0 TestBrowser",
                "screen_resolution": "1920x1080"
            }
        }
        resp = client.post(f"/api/public/surveys/{slug}/submit", json=sub_body)
        assert resp.status_code == 201

    # 6. Gọi API phân tích điều tiết
    mod_res = client.post(f"/api/surveys/{survey_id}/analytics/moderation", json={
        "independent_question_id": x_id,
        "moderator_question_id": w_id,
        "dependent_question_id": y_id,
        "center_variables": True,
        "scope": "all"
    })
    assert mod_res.status_code == 200
    data = mod_res.json()
    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 15
    assert "moderation_effect" in data
    assert "delta_r_squared" in data["moderation_effect"]
    assert "simple_slopes" in data
    assert len(data["simple_slopes"]) == 3
    assert "johnson_neyman" in data
    assert "interaction_plot" in data
    assert len(data["interaction_plot"]["lines"]) == 3
    assert "apa_narrative" in data
