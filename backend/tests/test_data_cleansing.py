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

def test_data_cleansing_pipeline_preview_and_apply():
    # 1. Tạo khảo sát với thang đo Likert
    create_res = client.post("/api/surveys", json={
        "title": "Đánh giá chất lượng dịch vụ giáo dục đại học",
        "description": "Nghiên cứu thang đo mức độ hài lòng",
        "instructions": "Vui lòng cho điểm từ 1 đến 5"
    })
    s_data = create_res.json()
    survey_id = s_data["id"]
    slug = s_data["public_slug"]

    # 2. Thêm 3 câu hỏi thang đo rating (1-5) để đo Cronbach's Alpha
    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q_teacher",
                "question_type": "rating",
                "title": "Nhiệt huyết của giảng viên:",
                "is_required": True,
                "options": []
            },
            {
                "id": "q_facility",
                "question_type": "rating",
                "title": "Cơ sở vật chất giảng đường:",
                "is_required": True,
                "options": []
            },
            {
                "id": "q_curriculum",
                "question_type": "rating",
                "title": "Chương trình đào tạo thực tiễn:",
                "is_required": True,
                "options": []
            }
        ]
    })
    client.post(f"/api/surveys/{survey_id}/publish")

    now = datetime.now(timezone.utc)

    # 3. Nạp 3 phản hồi sạch có sự tương quan nội bộ cao
    clean_scores = [
        {"q_teacher": 4, "q_facility": 4, "q_curriculum": 4},
        {"q_teacher": 5, "q_facility": 4, "q_curriculum": 5},
        {"q_teacher": 3, "q_facility": 3, "q_curriculum": 4},
        {"q_teacher": 5, "q_facility": 5, "q_curriculum": 5}
    ]
    for idx, scores in enumerate(clean_scores):
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=60 + idx * 5)).isoformat(),
            "submitted_at": (now - timedelta(seconds=10 + idx * 5)).isoformat(),
            "client_metadata": {"browser": "Firefox", "idx": idx},
            "answers": scores
        })

    # 4. Nạp 1 phản hồi "Speeder" (thời gian làm bài 2 giây < 10 giây)
    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (now - timedelta(seconds=2)).isoformat(),
        "submitted_at": now.isoformat(),
        "client_metadata": {"browser": "Bot/1.0"},
        "answers": {"q_teacher": 1, "q_facility": 5, "q_curriculum": 1}
    })

    # 5. Gọi API Preview quy trình làm sạch dữ liệu
    preview_res = client.post(f"/api/surveys/{survey_id}/responses/cleansing/preview", json={
        "exclude_speeders": True,
        "speeder_min_seconds": 10.0,
        "exclude_straightlining": True,
        "straightlining_threshold": 0.85,
        "exclude_logic_contradictions": True,
        "exclude_high_risk": False,
        "min_omr_confidence": 0.70,
        "exclude_unverified_enumerator": False
    })
    assert preview_res.status_code == 200
    report = preview_res.json()
    assert report["total_responses"] == 5
    assert report["flagged_speeders"] == 1
    assert report["clean_responses_count"] == 4
    assert report["clean_percentage"] == 80.0
    # Sau khi loại bỏ speeder, thời gian trung bình mẫu sạch phải cao hơn
    assert report["post_avg_duration"] >= report["pre_avg_duration"]

    # 6. Gọi API Apply quy trình làm sạch dữ liệu
    apply_res = client.post(f"/api/surveys/{survey_id}/responses/cleansing/apply", json={
        "exclude_speeders": True,
        "speeder_min_seconds": 10.0,
        "exclude_straightlining": True,
        "straightlining_threshold": 0.85,
        "exclude_logic_contradictions": True,
        "exclude_high_risk": False,
        "min_omr_confidence": 0.70,
        "exclude_unverified_enumerator": False
    })
    assert apply_res.status_code == 200
    apply_data = apply_res.json()
    assert apply_data["success"] is True
    assert apply_data["rejected_count"] == 1
    assert apply_data["verified_clean_count"] == 4
    assert apply_data["audit_log_id"] != ""

    # 7. Kiểm tra trạng thái trong danh sách phản hồi
    resp_list_res = client.get(f"/api/surveys/{survey_id}/responses")
    all_responses = resp_list_res.json()
    fraud_responses = [r for r in all_responses if r["review_status"] == "verified_fraud"]
    valid_responses = [r for r in all_responses if r["review_status"] == "verified_valid"]
    assert len(fraud_responses) == 1
    assert len(valid_responses) == 4
