import os
import pytest
from fastapi.testclient import TestClient

# Cấu hình db test riêng
os.environ["DATABASE_PATH"] = "backend/data/test_datatrust.db"

from app.main import app
from app.database import init_db, get_db, verify_audit_chain

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists("backend/data/test_datatrust.db"):
        try:
            os.remove("backend/data/test_datatrust.db")
        except Exception:
            pass
    init_db("backend/data/test_datatrust.db")
    yield

def test_seed_academic_demo_study_api():
    """
    Kiểm thử tự động hóa việc nạp khảo sát nghiên cứu khoa học mẫu và 35 phản hồi thực nghiệm:
    - 28 phản hồi sạch có tương quan nội bộ cao Cronbach's Alpha >= 0.80
    - 7 phản hồi bất thường (Speeders, Straightlining, Gibberish Text)
    - Chuỗi băm kiểm toán SHA-256 bất biến toàn vẹn 100%
    """
    response = client.post("/api/surveys/seed-academic-demo")
    assert response.status_code == 201
    data = response.json()

    assert "survey_id" in data
    assert data["total_responses"] == 35
    assert data["clean_count"] == 28
    assert data["flagged_count"] == 7
    assert data["data_trust_index"] == 80.0
    assert data["cronbach_alpha"] is not None
    assert data["cronbach_alpha"] >= 0.80

    survey_id = data["survey_id"]

    # 1. Kiểm tra chi tiết khảo sát
    s_res = client.get(f"/api/surveys/{survey_id}")
    assert s_res.status_code == 200
    s_data = s_res.json()
    assert s_data["status"] == "published"
    assert len(s_data["questions"]) == 7
    assert s_data["responses_count"] == 35

    # 2. Kiểm tra danh sách phản hồi
    r_res = client.get(f"/api/surveys/{survey_id}/responses?limit=100")
    assert r_res.status_code == 200
    r_list = r_res.json()
    assert len(r_list) == 35

    # 3. Kiểm tra tính toàn vẹn toán học của chuỗi băm bất biến
    trail_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert trail_res.status_code == 200
    trail_data = trail_res.json()
    assert trail_data["is_chain_valid"] is True
    assert trail_data["total_records"] >= 36  # CREATE_SURVEY + 35 responses + SEED_ACADEMIC_STUDY

    # 4. Kiểm tra báo cáo thẩm định độc lập
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-report")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["total_collected"] == 35
    assert audit_data["data_trust_index"] == 80.0
    assert audit_data["is_ledger_valid"] is True
    assert audit_data["cronbach_alpha"] is not None
    assert audit_data["cronbach_alpha"] >= 0.80

def test_seed_demo_responses_for_existing_survey():
    """
    Kiểm thử nạp phản hồi mẫu vào một khảo sát tùy biến đã tồn tại
    """
    # 1. Tạo khảo sát mới
    create_res = client.post("/api/surveys", json={
        "title": "Khảo sát Thử nghiệm Tùy biến",
        "description": "Mô tả thử nghiệm",
        "instructions": "Hướng dẫn thử nghiệm"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]

    # 2. Thêm 3 câu hỏi
    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Vai trò của bạn",
                "is_required": True,
                "options": [
                    {"id": "gv", "label": "Giảng viên"},
                    {"id": "sv", "label": "Sinh viên"}
                ]
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Mức độ hài lòng chung",
                "is_required": True,
                "options": []
            },
            {
                "order_index": 2,
                "question_type": "long_text",
                "title": "Ý kiến đóng góp",
                "is_required": False,
                "options": []
            }
        ]
    })

    # 3. Nạp 10 phản hồi mẫu
    seed_res = client.post(f"/api/surveys/{survey_id}/seed-demo-responses?count=10")
    assert seed_res.status_code == 201
    seed_data = seed_res.json()
    assert seed_data["seeded_count"] == 10

    # 4. Kiểm tra phản hồi đã lưu
    r_res = client.get(f"/api/surveys/{survey_id}/responses")
    assert r_res.status_code == 200
    assert len(r_res.json()) == 10

    # 5. Kiểm tra chuỗi băm bất biến
    trail_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert trail_res.status_code == 200
    assert trail_res.json()["is_chain_valid"] is True
