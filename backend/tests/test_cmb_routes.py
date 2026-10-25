"""
API Route integration tests for Common Method Bias / Variance (CMB/CMV).
"""

from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_common_method_bias_route_workflow():
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-id/analytics/common-method-bias", json={})
    assert res_404.status_code == 404

    # 2. Tạo khảo sát thử nghiệm CMB
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Đánh Giá Sai Lệch Phương Pháp Chung (CMB)",
        "description": "Kiểm định Harman's Single Factor, Kỹ thuật Biến Đánh Dấu và ULMCF"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 4 câu hỏi thang đo và 1 câu hỏi biến đánh dấu
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Đánh Giá Sai Lệch Phương Pháp Chung (CMB)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "rating",
                "title": "Mục 1: Nhận thức hữu ích",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Mục 2: Dễ sử dụng",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Mục 3: Sự tin cậy",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "rating",
                "title": "Mục 4: Ý định tiếp tục sử dụng",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 4,
                "question_type": "rating",
                "title": "Biến đánh dấu: Sở thích thời tiết",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")
    surv_data = client.get(f"/api/surveys/{survey_id}").json()
    qs = surv_data["questions"]
    q1_id = qs[0]["id"]
    q2_id = qs[1]["id"]
    q3_id = qs[2]["id"]
    q4_id = qs[3]["id"]
    marker_id = qs[4]["id"]

    # 4. Khi chưa có dữ liệu, trả về INSUFFICIENT_SAMPLE
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/common-method-bias", json={
        "scale_question_ids": [q1_id, q2_id, q3_id, q4_id]
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 5. Gửi 12 phản hồi mô phỏng đa dạng
    now = datetime.now(timezone.utc)
    for idx in range(12):
        val1 = str(1 + (idx % 5))
        val2 = str(1 + ((idx + 1) % 5))
        val3 = str(5 - (idx % 4))
        val4 = str(1 + ((idx * 2) % 5))
        marker_val = str(3 + (idx % 2))

        sub_body = {
            "started_at": (now - timedelta(minutes=20 - idx, seconds=30)).isoformat(),
            "submitted_at": (now - timedelta(minutes=20 - idx)).isoformat(),
            "answers": {
                q1_id: val1,
                q2_id: val2,
                q3_id: val3,
                q4_id: val4,
                marker_id: marker_val
            },
            "client_metadata": {
                "ip_hash": f"ip_cmb_{idx}",
                "user_agent": "Mozilla/5.0 TestBrowser",
                "screen_resolution": "1920x1080"
            }
        }
        resp = client.post(f"/api/public/surveys/{slug}/submit", json=sub_body)
        assert resp.status_code == 201

    # 6. Gọi API chẩn đoán CMB với marker variable
    cmb_res = client.post(f"/api/surveys/{survey_id}/analytics/common-method-bias", json={
        "scale_question_ids": [q1_id, q2_id, q3_id, q4_id],
        "marker_question_id": marker_id,
        "scope": "all"
    })
    assert cmb_res.status_code == 200
    data = cmb_res.json()
    assert data["status"] == "SUCCESS"
    assert data["overall_risk"] in ["LOW", "MODERATE", "HIGH"]
    assert "harman_test" in data
    assert data["harman_test"]["threshold_pct"] == 50.0
    assert "marker_test" in data
    assert data["marker_test"]["marker_variable"] == marker_id
    assert "ulmcf_test" in data
    assert "apa_writeup" in data
    assert len(data["recommended_remedies"]) > 0

    # 7. Gọi API với tự động xác định scale questions (scale_question_ids = None)
    auto_res = client.post(f"/api/surveys/{survey_id}/analytics/common-method-bias", json={
        "scope": "all"
    })
    assert auto_res.status_code == 200
    assert auto_res.json()["status"] == "SUCCESS"
    assert auto_res.json()["harman_test"]["n_items"] >= 4
