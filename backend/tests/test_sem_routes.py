import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_sem_routes_workflow():
    """Kiểm thử tích hợp đầu-cuối API Mô hình Phương trình Cấu trúc (SEM / Path Analysis)."""
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey/analytics/sem", json={
        "paths": [{"source": "q1", "target": "q2"}]
    })
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Mô Hình Đường Dẫn Hiệu Quả Công Nghệ (SEM)",
        "description": "Nghiên cứu chuỗi tác động: Chất lượng hệ thống -> Sự hài lòng -> Hiệu quả công việc"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Cập nhật 3 câu hỏi đánh giá 1-5 sao: X (Chất lượng), M (Hài lòng), Y (Hiệu quả)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Mô Hình Đường Dẫn Hiệu Quả Công Nghệ (SEM)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "rating",
                "title": "Chất lượng hệ thống công nghệ (X)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Sự hài lòng của nhân viên (M)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Hiệu quả công việc tổng thể (Y)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200

    # Publish survey để mở cổng nhận phản hồi công khai
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    assert len(questions) == 3
    q_x = questions[0]["id"]
    q_m = questions[1]["id"]
    q_y = questions[2]["id"]

    # 4. Kiểm thử khi chưa có phản hồi (INSUFFICIENT_SAMPLE)
    sem_payload = {
        "paths": [
            {"source": q_x, "target": q_m},
            {"source": q_m, "target": q_y},
            {"source": q_x, "target": q_y}
        ],
        "scope": "all"
    }
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/sem", json=sem_payload)
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 5. Nạp 24 phản hồi khảo sát có tương quan trung gian thực tế
    now = datetime.now(timezone.utc)
    for i in range(24):
        x_val = 1 + (i % 5)
        # M phụ thuộc dương vào X
        m_val = min(5, max(1, int(round(0.6 * x_val + 1.2 + (0.5 if i % 2 == 0 else -0.5)))))
        # Y phụ thuộc vào M và X
        y_val = min(5, max(1, int(round(0.5 * m_val + 0.3 * x_val + 0.8 + (0.4 if i % 3 == 0 else -0.4)))))

        dur = 45 + (i * 2)
        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=dur + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 20)).isoformat(),
            "answers": {
                q_x: x_val,
                q_m: m_val,
                q_y: y_val
            }
        })
        assert sub_res.status_code == 201

    # 6. Kiểm tra trường hợp paths rỗng
    res_empty_paths = client.post(f"/api/surveys/{survey_id}/analytics/sem", json={
        "paths": [],
        "scope": "all"
    })
    assert res_empty_paths.status_code == 200
    assert res_empty_paths.json()["status"] == "EMPTY_SPECIFICATION"

    # 7. Gọi API ước lượng SEM
    sem_res = client.post(f"/api/surveys/{survey_id}/analytics/sem", json=sem_payload)
    assert sem_res.status_code == 200
    data = sem_res.json()

    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 24
    assert len(data["paths"]) == 3
    assert len(data["equations"]) == 2
    assert len(data["indirect_effects"]) == 1
    assert data["fit_indices"]["is_good_fit"] is True
    assert "<svg" in data["svg_path_diagram"]
    assert "Mô hình phương trình cấu trúc" in data["apa_narrative"]

    # 8. Xác nhận audit log ghi nhận SEM_MODEL_EVALUATED
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    actions = [evt["action"] for evt in audit_res.json()["events"]]
    assert "SEM_MODEL_EVALUATED" in actions
