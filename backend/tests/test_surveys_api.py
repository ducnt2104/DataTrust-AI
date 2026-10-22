import os
import pytest
from fastapi.testclient import TestClient

# Cấu hình db test riêng
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

def test_create_and_update_survey():
    # 1. Tạo khảo sát mới
    res = client.post("/api/surveys", json={
        "title": "Khảo sát trải nghiệm khách hàng",
        "description": "Thu thập phản hồi quý 4",
        "instructions": "Vui lòng chọn câu trả lời chính xác"
    })
    assert res.status_code == 201
    data = res.json()
    survey_id = data["id"]
    assert data["status"] == "draft"
    assert "public_slug" in data

    # 2. Thêm câu hỏi và cập nhật
    update_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo sát trải nghiệm khách hàng (Đã cập nhật)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Bạn biết đến chúng tôi qua kênh nào?",
                "is_required": True,
                "options": [{"id": "fb", "label": "Facebook"}, {"id": "web", "label": "Website"}],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "likert",
                "title": "Mức độ hài lòng chung:",
                "is_required": True,
                "options": [{"id": "1", "label": "Kém"}, {"id": "5", "label": "Tốt"}],
                "logic_rules": []
            }
        ]
    })
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert len(updated_data["questions"]) == 2
    assert updated_data["version"] == 2

    # 3. Xuất bản khảo sát
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["status"] == "published"
    assert f"/s/{data['public_slug']}" in pub_data["public_url"]

    # 4. Đóng khảo sát
    close_res = client.post(f"/api/surveys/{survey_id}/close")
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "closed"
