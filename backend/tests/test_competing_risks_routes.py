import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_competing_risks_routes_workflow():
    """Kiểm thử tích hợp đầu-cuối API Phân tích Nguy cơ Cạnh tranh & Mô hình Suy yếu (Competing Risks & Shared Frailty)."""
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey/analytics/competing-risks", json={})
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Khách Hàng Doanh Nghiệp (Competing Risks Fieldwork)",
        "description": "Nghiên cứu nguyên nhân bỏ cuộc giữa chừng và đánh giá tính không đồng nhất giữa các điều tra viên"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Cập nhật 2 câu hỏi: 1 cho nội dung đánh giá, 1 cho điều tra viên / cụm
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Khách Hàng Doanh Nghiệp (Competing Risks Fieldwork)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "rating",
                "title": "Mức độ hài lòng với dịch vụ",
                "is_required": False,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Điều tra viên phỏng vấn",
                "is_required": True,
                "options": ["ĐTV Nguyễn Văn A", "ĐTV Trần Thị B"],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200

    # Publish survey để mở cổng nhận phản hồi
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    assert len(questions) == 2
    q_rating = questions[0]["id"]
    q_cluster = questions[1]["id"]

    # 4. Khi chưa có phản hồi (< 8)
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/competing-risks", json={})
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 5. Sinh 16 phản hồi với các nguyên nhân kết thúc và thời lượng khác nhau
    now = datetime.now(timezone.utc)
    for i in range(16):
        dur = 30 + (i * 25)
        dtv = "ĐTV Nguyễn Văn A" if i % 2 == 0 else "ĐTV Trần Thị B"
        # Nửa số phản hồi trả lời đầy đủ cả 2 câu, nửa còn lại chỉ trả lời 1 câu (voluntary dropoff)
        if i % 3 == 0:
            answers_dict = {q_cluster: dtv}  # Bỏ dở câu rating
        else:
            answers_dict = {q_rating: 4, q_cluster: dtv}

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=dur + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 20)).isoformat(),
            "answers": answers_dict
        })
        assert sub_res.status_code == 201

    # 6. Gọi API phân tích nguy cơ cạnh tranh tự động từ telemetry
    res_auto = client.post(f"/api/surveys/{survey_id}/analytics/competing-risks", json={
        "cluster_question_id": q_cluster,
        "scope": "all"
    })
    assert res_auto.status_code == 200
    data = res_auto.json()

    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 16
    assert "competing_causes" in data
    assert len(data["competing_causes"]) >= 1
    assert "final_cumulative_incidence" in data
    assert "milestone_evaluations" in data

    # Kiểm tra mô hình suy yếu chung
    frailty = data["shared_frailty_model"]
    assert frailty["clusters_count"] == 2
    assert frailty["frailty_variance_theta"] > 0
    assert len(frailty["cluster_frailty_estimates"]) == 2

    # Kiểm tra đồ họa SVG và APA narrative
    assert "<svg" in data["svg_cif_chart"]
    assert "Nguy cơ Cạnh tranh" in data["apa_narrative"]
    assert "Aalen-Johansen" in data["apa_narrative"]

    # 7. Kiểm tra audit log
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    actions = [evt["action"] for evt in audit_res.json()["events"]]
    assert "COMPETING_RISKS_EVALUATED" in actions
