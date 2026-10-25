import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)

def test_cognitive_pacing_endpoint():
    # 1. Tạo khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Nghiên cứu Nhịp độ Nhận thức và Thói quen Tiêu dùng",
        "description": "Đo lường thời gian đọc và phản ứng nhận thức",
        "instructions": "Vui lòng trả lời câu hỏi"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Cập nhật câu hỏi
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Nghiên cứu Nhịp độ Nhận thức và Thói quen Tiêu dùng",
        "questions": [
            {
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Bạn biết đến sản phẩm của chúng tôi qua kênh truyền thông nào?",
                "description": "Chọn một phương án phù hợp nhất",
                "is_required": True,
                "options": ["Mạng xã hội", "Bạn bè giới thiệu", "Báo chí", "Tìm kiếm Google", "Khác"],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Mức độ hài lòng chung",
                "description": "Thang đo 1 đến 5",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            }
        ]
    })

    # 3. Xuất bản khảo sát
    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Kiểm tra endpoint cognitive-pacing khi chưa có phản hồi nào
    res_empty = client.get(f"/api/surveys/{survey_id}/analytics/cognitive-pacing")
    assert res_empty.status_code == 200
    data_empty = res_empty.json()
    assert "survey_level" in data_empty
    assert "question_analyses" in data_empty
    assert len(data_empty["question_analyses"]) == 2
    assert data_empty["survey_level"]["actual_sample_size"] == 0
    assert data_empty["survey_level"]["expected_reading_seconds"] > 0

    # 5. Gửi một phản hồi mẫu
    q_rows = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": "2026-10-24T02:00:00Z",
        "submitted_at": "2026-10-24T02:00:45Z",  # 45 giây
        "answers": {
            q_rows[0]["id"]: "Mạng xã hội",
            q_rows[1]["id"]: "5"
        }
    })

    # 6. Kiểm tra lại cognitive-pacing sau khi đã có phản hồi
    res_filled = client.get(f"/api/surveys/{survey_id}/analytics/cognitive-pacing")
    assert res_filled.status_code == 200
    data_filled = res_filled.json()
    sl = data_filled["survey_level"]
    assert sl["actual_sample_size"] == 1
    assert sl["actual_median_seconds"] == 45.0
    assert sl["overall_pacing_ratio"] > 0
    assert "apa_interpretation" in sl
