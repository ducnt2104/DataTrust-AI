import os
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

os.environ["DATABASE_PATH"] = "backend/data/test_datatrust.db"

from app.main import app
from app.database import init_db

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists("backend/data/test_datatrust.db"):
        try:
            os.remove("backend/data/test_datatrust.db")
        except Exception:
            pass
    init_db("backend/data/test_datatrust.db")
    yield

client = TestClient(app)

def test_public_survey_lifecycle():
    # 1. Tạo khảo sát
    create_res = client.post("/api/surveys", json={
        "title": "Nghiên cứu thị trường công nghệ",
        "description": "Mô tả",
        "instructions": "Hướng dẫn"
    })
    s_data = create_res.json()
    survey_id = s_data["id"]
    slug = s_data["public_slug"]

    # 2. Thêm 2 câu hỏi
    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q_device",
                "question_type": "single_choice",
                "title": "Thiết bị chính bạn sử dụng?",
                "is_required": True,
                "options": [{"id": "phone", "label": "Smartphone"}, {"id": "laptop", "label": "Laptop"}]
            },
            {
                "id": "q_feedback",
                "question_type": "short_text",
                "title": "Ý kiến đóng góp:",
                "is_required": False,
                "options": []
            }
        ]
    })

    # 3. Khi khảo sát còn là 'draft', public endpoint phải trả về 403 Forbidden
    draft_res = client.get(f"/api/public/surveys/{slug}")
    assert draft_res.status_code == 403

    # 4. Xuất bản khảo sát
    client.post(f"/api/surveys/{survey_id}/publish")

    # 5. Truy cập lại public endpoint -> Thành công 200
    pub_get = client.get(f"/api/public/surveys/{slug}")
    assert pub_get.status_code == 200
    pub_body = pub_get.json()
    assert len(pub_body["questions"]) == 2

    # 6. Gửi phản hồi thiếu trường bắt buộc -> Lỗi 422
    now = datetime.now(timezone.utc)
    submit_fail = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (now - timedelta(seconds=20)).isoformat(),
        "submitted_at": now.isoformat(),
        "answers": {}  # Thiếu q_device bắt buộc
    })
    assert submit_fail.status_code == 422

    # 7. Gửi phản hồi hợp lệ -> 201 Created
    submit_ok = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (now - timedelta(seconds=35)).isoformat(),
        "submitted_at": now.isoformat(),
        "client_metadata": {"browser": "Chrome"},
        "answers": {
            "q_device": "laptop",
            "q_feedback": "Nền tảng giao diện rất mượt mà"
        }
    })
    assert submit_ok.status_code == 201
    resp_id = submit_ok.json()["response_id"]

    # 8. Kiểm tra phản hồi hiển thị trong danh sách responses
    list_res = client.get(f"/api/surveys/{survey_id}/responses")
    assert list_res.status_code == 200
    responses_list = list_res.json()
    assert len(responses_list) == 1
    assert responses_list[0]["id"] == resp_id

    # 9. Kiểm tra chi tiết phản hồi
    detail_res = client.get(f"/api/surveys/{survey_id}/responses/{resp_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["answers"]["q_device"] == "laptop"
    assert detail["assessment"] is not None

    # 10. Đóng khảo sát và thử gửi phản hồi tiếp -> Bị từ chối
    client.post(f"/api/surveys/{survey_id}/close")
    submit_after_close = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (now - timedelta(seconds=10)).isoformat(),
        "submitted_at": now.isoformat(),
        "answers": {"q_device": "phone"}
    })
    assert submit_after_close.status_code == 400
