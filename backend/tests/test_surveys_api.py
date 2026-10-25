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

    # 5. Mở lại khảo sát (Reopen)
    reopen_res = client.post(f"/api/surveys/{survey_id}/reopen")
    assert reopen_res.status_code == 200
    assert reopen_res.json()["status"] == "published"

    # 6. Nhân bản khảo sát (Duplicate)
    dup_res = client.post(f"/api/surveys/{survey_id}/duplicate")
    assert dup_res.status_code == 201
    dup_data = dup_res.json()
    assert dup_data["status"] == "draft"
    assert "Bản sao của" in dup_data["title"]
    assert len(dup_data["questions"]) == 2

    # 7. Danh sách khảo sát (List Surveys with Filter)
    list_res = client.get("/api/surveys?status=published")
    assert list_res.status_code == 200
    pub_list = list_res.json()
    assert any(s["id"] == survey_id for s in pub_list)

    # 8. Xóa khảo sát (Delete Survey & Verify Audit Log)
    del_res = client.delete(f"/api/surveys/{survey_id}")
    assert del_res.status_code == 204

    # Khảo sát không còn tồn tại
    assert client.get(f"/api/surveys/{survey_id}").status_code == 404

def test_survey_versioning_and_schema_history():
    # 1. Tạo khảo sát
    res = client.post("/api/surveys", json={
        "title": "Nghiên cứu hành vi người tiêu dùng",
        "description": "Phiên bản khởi tạo v1"
    })
    s_id = res.json()["id"]

    # 2. Thêm 1 câu hỏi đầu tiên (v1 -> v2)
    client.put(f"/api/surveys/{s_id}", json={
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Bạn có hay mua sắm online không?",
                "is_required": True,
                "options": [{"id": "yes", "label": "Có"}, {"id": "no", "label": "Không"}]
            }
        ]
    })

    # 3. Cập nhật thêm câu hỏi thứ hai (v2 -> v3)
    client.put(f"/api/surveys/{s_id}", json={
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Bạn có hay mua sắm online không?",
                "is_required": True,
                "options": [{"id": "yes", "label": "Có"}, {"id": "no", "label": "Không"}]
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Đánh giá mức độ hài lòng về sàn thương mại điện tử:",
                "is_required": True,
                "options": []
            }
        ]
    })

    # 4. Kiểm tra danh sách phiên bản lịch sử
    ver_list_res = client.get(f"/api/surveys/{s_id}/versions")
    assert ver_list_res.status_code == 200
    versions = ver_list_res.json()
    assert len(versions) >= 2

    # 5. Kiểm tra chi tiết phiên bản v2 (chỉ có 1 câu hỏi)
    v2_res = client.get(f"/api/surveys/{s_id}/versions/2")
    assert v2_res.status_code == 200
    v2_data = v2_res.json()
    assert v2_data["version"] == 2
    assert v2_data["questions_count"] == 1
    assert v2_data["questions"][0]["title"] == "Bạn có hay mua sắm online không?"

    # 6. Kiểm tra chi tiết phiên bản v3 (có 2 câu hỏi)
    v3_res = client.get(f"/api/surveys/{s_id}/versions/3")
    assert v3_res.status_code == 200
    v3_data = v3_res.json()
    assert v3_data["version"] == 3
    assert v3_data["questions_count"] == 2

