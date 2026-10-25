import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_survival_dropoff_routes_workflow():
    """Kiểm thử tích hợp đầu-cuối API Phân tích Sống sót & Thời gian Bỏ dở Khảo sát (Kaplan-Meier)."""
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey/analytics/survival-dropoff", json={})
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Đánh Giá Thời Gian Duy Trì & Tỷ Lệ Sống Sót",
        "description": "Kiểm định mô hình Kaplan-Meier và phân tích thời gian bỏ dở"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 2 câu hỏi
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Đánh Giá Thời Gian Duy Trì & Tỷ Lệ Sống Sót",
        "questions": [
            {
                "order_index": 0,
                "question_type": "rating",
                "title": "Mức độ hài lòng chung",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "text",
                "title": "Góp ý chi tiết",
                "is_required": False,
                "options": [],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")

    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    q1_id = public_q[0]["id"]
    q2_id = public_q[1]["id"]

    # 4. Kiểm tra khi chưa có phản hồi nào
    res_empty = client.post(f"/api/surveys/{survey_id}/analytics/survival-dropoff", json={})
    assert res_empty.status_code == 200
    assert res_empty.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 5. Gửi 8 phản hồi (5 hoàn thành cả 2 câu, 3 chỉ trả lời 1 câu -> drop-off)
    now = datetime.now(timezone.utc)
    for idx in range(8):
        dur = 45 + idx * 25  # 45s to 220s
        is_drop = idx in (1, 3, 5)  # 3 drop-offs
        answers = {q1_id: (idx % 5) + 1}
        if not is_drop:
            answers[q2_id] = f"Ý kiến đóng góp nghiên cứu số {idx} với nội dung khác biệt chi tiết"

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=dur + idx * 5)).isoformat(),
            "submitted_at": (now - timedelta(seconds=idx * 5)).isoformat(),
            "answers": answers,
            "client_metadata": {
                "user_agent": f"Tester Agent Device {idx}"
            }
        })
        assert sub_res.status_code == 201

    # 6. Gọi API Phân tích Sống sót
    res_surv = client.post(f"/api/surveys/{survey_id}/analytics/survival-dropoff", json={
        "scope": "all"
    })
    assert res_surv.status_code == 200
    surv_data = res_surv.json()

    assert surv_data["status"] == "SUCCESS"
    assert surv_data["total_participants"] == 8
    assert surv_data["drop_off_count"] == 3
    assert surv_data["completed_count"] == 5
    assert "overall_km" in surv_data
    assert len(surv_data["overall_km"]["steps"]) > 0
    assert "milestones" in surv_data
    assert len(surv_data["milestones"]) == 4
    assert "apa_narrative" in surv_data

    # 7. Kiểm tra audit trail
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    actions = [evt["action"] for evt in audit_res.json()["events"]]
    assert "SURVIVAL_ANALYSIS_EVALUATED" in actions
