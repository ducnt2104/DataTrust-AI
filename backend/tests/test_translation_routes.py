import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)

def test_survey_multilingual_workflow():
    # 1. Tạo một cuộc khảo sát tiếng Việt
    create_payload = {
        "title": "Khảo sát ý kiến người tiêu dùng",
        "description": "Nghiên cứu thị trường và mức độ hài lòng khách hàng",
        "instructions": "Vui lòng trả lời trung thực các câu hỏi bên dưới."
    }
    res = client.post("/api/surveys", json=create_payload)
    assert res.status_code == 201
    survey = res.json()
    survey_id = survey["id"]
    slug = survey["public_slug"]

    # 2. Cập nhật danh sách câu hỏi đo lường
    update_payload = {
        "title": survey["title"],
        "description": survey["description"],
        "instructions": survey["instructions"],
        "questions": [
            {
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Giới tính",
                "description": "Thông tin nhân khẩu học",
                "is_required": True,
                "options": ["Nam", "Nữ", "Khác"],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "single_choice",
                "title": "Đánh giá chất lượng dịch vụ",
                "description": "Thang đo mức độ hài lòng",
                "is_required": True,
                "options": ["Rất không hài lòng", "Không hài lòng", "Bình thường", "Hài lòng", "Rất hài lòng"],
                "logic_rules": []
            }
        ]
    }
    res = client.put(f"/api/surveys/{survey_id}", json=update_payload)
    assert res.status_code == 200
    updated_survey = res.json()
    questions = updated_survey["questions"]
    assert len(questions) == 2
    q_gender_id = questions[0]["id"]
    q_csat_id = questions[1]["id"]

    # 3. Xuất bản khảo sát
    res = client.post(f"/api/surveys/{survey_id}/publish")
    assert res.status_code == 200

    # 4. Kiểm tra khảo sát công khai mặc định (tiếng Việt)
    res = client.get(f"/api/public/surveys/{slug}")
    assert res.status_code == 200
    pub_data = res.json()
    assert pub_data["title"] == "Khảo sát ý kiến người tiêu dùng"
    assert pub_data["current_language"] == "vi"
    assert pub_data["available_languages"] == ["vi"]
    assert pub_data["questions"][0]["title"] == "Giới tính"
    assert pub_data["questions"][0]["options"] == ["Nam", "Nữ", "Khác"]

    # 5. Kích hoạt Auto-Translate sang tiếng Anh (EN)
    res = client.post(f"/api/surveys/{survey_id}/translations/auto-translate?target_lang=en")
    assert res.status_code == 200
    trans_data = res.json()
    assert trans_data["language_code"] == "en"
    assert "questions" in trans_data
    assert q_gender_id in trans_data["questions"]
    assert trans_data["questions"][q_gender_id]["title"] == "Gender"
    assert trans_data["questions"][q_gender_id]["options"] == ["Male", "Female", "Other"]

    # 6. Lấy danh sách translations của khảo sát
    res = client.get(f"/api/surveys/{survey_id}/translations")
    assert res.status_code == 200
    t_list = res.json()
    assert t_list["survey_id"] == survey_id
    assert "en" in t_list["available_languages"]
    assert "en" in t_list["translations"]

    # 7. Truy vấn khảo sát công khai phiên bản tiếng Anh
    res = client.get(f"/api/public/surveys/{slug}?lang=en")
    assert res.status_code == 200
    en_pub = res.json()
    assert en_pub["current_language"] == "en"
    assert "en" in en_pub["available_languages"]
    assert "vi" in en_pub["available_languages"]
    assert en_pub["questions"][0]["title"] == "Gender"
    assert en_pub["questions"][0]["options"] == ["Male", "Female", "Other"]
    assert "Very Satisfied" in en_pub["questions"][1]["options"]

    # 8. Cập nhật thủ công bản dịch (PUT translation)
    custom_trans = trans_data
    custom_trans["title"] = "Official Consumer Sentiment Survey 2026"
    res = client.put(f"/api/surveys/{survey_id}/translations/en", json=custom_trans)
    assert res.status_code == 200

    # Kiểm tra lại công khai xem bản dịch tùy chỉnh đã áp dụng chưa
    res = client.get(f"/api/public/surveys/{slug}?lang=en")
    assert res.status_code == 200
    assert res.json()["title"] == "Official Consumer Sentiment Survey 2026"

    # 9. Gửi phản hồi tiếng Anh hợp lệ
    submit_payload = {
        "started_at": "2026-10-24T02:00:00Z",
        "submitted_at": "2026-10-24T02:02:30Z",
        "client_metadata": {
            "browser": "Chrome",
            "platform": "Desktop",
            "lang": "en"
        },
        "answers": {
            q_gender_id: "Male",
            q_csat_id: "Very Satisfied"
        }
    }
    res = client.post(f"/api/public/surveys/{slug}/submit", json=submit_payload)
    assert res.status_code == 201
    resp_result = res.json()
    assert "response_id" in resp_result
    assert "thành công" in resp_result["message"].lower()
