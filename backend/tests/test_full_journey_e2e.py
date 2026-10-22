import json
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_full_12_step_e2e_journey():
    """
    TEST-12 — Toàn bộ hành trình sản phẩm:
    Tạo khảo sát -> Lưu -> Xuất bản -> Lấy link -> Mở trang công khai ->
    Gửi phản hồi -> Đọc dữ liệu đã lưu -> Phân tích chất lượng ->
    Xem cảnh báo -> Xác minh quyết định -> Xuất bộ dữ liệu sạch.
    """
    now = datetime.now(timezone.utc)

    # 1. TEST-01: Tạo khảo sát mới
    res_create = client.post("/api/surveys", json={
        "title": "Khảo sát ứng dụng trí tuệ nhân tạo trong giáo dục Việt Nam",
        "description": "Nghiên cứu cấp độ chấp nhận và hiệu quả thực tế",
        "instructions": "Vui lòng hoàn thành trung thực các câu hỏi bên dưới."
    })
    assert res_create.status_code == 201
    survey_data = res_create.json()
    survey_id = survey_data["id"]
    slug = survey_data["public_slug"]
    assert survey_data["status"] == "draft"

    # 2. TEST-02: Thêm câu hỏi, ràng buộc bắt buộc và logic rẽ nhánh
    questions_payload = [
        {
            "id": "q_role",
            "question_type": "single_choice",
            "title": "Vai trò chính của bạn trong môi trường giáo dục?",
            "is_required": True,
            "options": [
                {"id": "student", "label": "Học sinh / Sinh viên"},
                {"id": "teacher", "label": "Giáo viên / Giảng viên"},
                {"id": "other", "label": "Khác"}
            ]
        },
        {
            "id": "q_ai_use",
            "question_type": "single_choice",
            "title": "Bạn có sử dụng các công cụ AI (ChatGPT, Gemini, Claude, ...) trong học tập/giảng dạy không?",
            "is_required": True,
            "options": [
                {"id": "yes", "label": "Có"},
                {"id": "no", "label": "Không"}
            ]
        },
        {
            "id": "q_ai_freq",
            "question_type": "single_choice",
            "title": "Tần suất sử dụng AI của bạn?",
            "is_required": False,
            "options": [
                {"id": "daily", "label": "Hàng ngày"},
                {"id": "weekly", "label": "Hàng tuần"},
                {"id": "rarely", "label": "Hiếm khi"}
            ],
            "logic_rules": [
                {"depends_on_question_id": "q_ai_use", "operator": "equals", "value": "yes", "action": "show"}
            ]
        },
        {
            "id": "q_sat_efficiency",
            "question_type": "likert",
            "title": "AI giúp tôi tiết kiệm thời gian tìm kiếm tài liệu:",
            "is_required": True,
            "options": [{"id": "1", "label": "1"}, {"id": "5", "label": "5"}]
        },
        {
            "id": "q_sat_quality",
            "question_type": "likert",
            "title": "AI nâng cao chất lượng bài viết/nghiên cứu của tôi:",
            "is_required": True,
            "options": [{"id": "1", "label": "1"}, {"id": "5", "label": "5"}]
        },
        {
            "id": "q_sat_reliability",
            "question_type": "likert",
            "title": "Tôi hoàn toàn tin cậy thông tin do AI cung cấp mà không cần kiểm tra lại:",
            "is_required": True,
            "options": [{"id": "1", "label": "1"}, {"id": "5", "label": "5"}]
        },
        {
            "id": "q_sat_critical",
            "question_type": "likert",
            "title": "AI kích thích tư duy phản biện của tôi:",
            "is_required": True,
            "options": [{"id": "1", "label": "1"}, {"id": "5", "label": "5"}]
        },
        {
            "id": "q_open_feedback",
            "question_type": "long_text",
            "title": "Những rủi ro hoặc thách thức lớn nhất khi áp dụng AI là gì?",
            "is_required": False,
            "options": []
        }
    ]

    res_update = client.put(f"/api/surveys/{survey_id}", json={
        "questions": questions_payload
    })
    assert res_update.status_code == 200
    assert len(res_update.json()["questions"]) == 8

    # 3. TEST-03: Thử truy cập bản draft bằng public link -> 403 Forbidden
    res_draft_access = client.get(f"/api/public/surveys/{slug}")
    assert res_draft_access.status_code == 403

    # Xuất bản khảo sát
    res_pub = client.post(f"/api/surveys/{survey_id}/publish")
    assert res_pub.status_code == 200
    assert res_pub.json()["status"] == "published"

    # Mở link công khai sau khi xuất bản -> 200 OK
    res_pub_get = client.get(f"/api/public/surveys/{slug}")
    assert res_pub_get.status_code == 200
    assert len(res_pub_get.json()["questions"]) == 8

    # 4. TEST-04 & TEST-05: Gửi phản hồi thật
    # Ca A: Phản hồi hợp lệ, tự nhiên
    sub_resp_A = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (now - timedelta(seconds=75)).isoformat(),
        "submitted_at": now.isoformat(),
        "client_metadata": {"device": "Desktop Windows Chrome"},
        "answers": {
            "q_role": "student",
            "q_ai_use": "yes",
            "q_ai_freq": "daily",
            "q_sat_efficiency": "5",
            "q_sat_quality": "4",
            "q_sat_reliability": "2",
            "q_sat_critical": "3",
            "q_open_feedback": "Ảo giác thông tin và thiếu trích dẫn học thuật chuẩn."
        }
    })
    assert sub_resp_A.status_code == 201
    resp_id_A = sub_resp_A.json()["response_id"]
    assert sub_resp_A.json()["risk_level"] == "low"

    # Ca B: Phản hồi gian lận / Trùng lặp 100% với Ca A
    sub_resp_B = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (now - timedelta(seconds=70)).isoformat(),
        "submitted_at": now.isoformat(),
        "client_metadata": {"device": "Mobile Safari"},
        "answers": {
            "q_role": "student",
            "q_ai_use": "yes",
            "q_ai_freq": "daily",
            "q_sat_efficiency": "5",
            "q_sat_quality": "4",
            "q_sat_reliability": "2",
            "q_sat_critical": "3",
            "q_open_feedback": "Ảo giác thông tin và thiếu trích dẫn học thuật chuẩn."
        }
    })
    assert sub_resp_B.status_code == 201
    resp_id_B = sub_resp_B.json()["response_id"]
    # Bị bắt cờ FLAG_EXACT_DUPLICATE -> Rủi ro cao
    assert sub_resp_B.json()["risk_level"] == "high"

    # Ca C: Phản hồi có mẫu điền thẳng (Straightlining) - chọn toàn 5
    sub_resp_C = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (now - timedelta(seconds=60)).isoformat(),
        "submitted_at": now.isoformat(),
        "client_metadata": {"device": "Desktop Firefox"},
        "answers": {
            "q_role": "teacher",
            "q_ai_use": "yes",
            "q_ai_freq": "weekly",
            "q_sat_efficiency": "5",
            "q_sat_quality": "5",
            "q_sat_reliability": "5",
            "q_sat_critical": "5",
            "q_open_feedback": "Tốt"
        }
    })
    assert sub_resp_C.status_code == 201
    resp_id_C = sub_resp_C.json()["response_id"]

    # Ca D: Phản hồi mâu thuẫn logic ("no" ở q_ai_use nhưng lại trả lời q_ai_freq)
    sub_resp_D = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (now - timedelta(seconds=50)).isoformat(),
        "submitted_at": now.isoformat(),
        "client_metadata": {"device": "Mobile Android"},
        "answers": {
            "q_role": "teacher",
            "q_ai_use": "no",
            "q_ai_freq": "daily",  # Mâu thuẫn logic!
            "q_sat_efficiency": "1",
            "q_sat_quality": "2",
            "q_sat_reliability": "1",
            "q_sat_critical": "2",
            "q_open_feedback": "Không dùng vì lo ngại đạo đức học thuật."
        }
    })
    assert sub_resp_D.status_code == 201
    resp_id_D = sub_resp_D.json()["response_id"]

    # Ca E: Phản hồi thứ 5 (để đạt N >= 5)
    sub_resp_E = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": (now - timedelta(seconds=55)).isoformat(),
        "submitted_at": now.isoformat(),
        "client_metadata": {"device": "Desktop Edge"},
        "answers": {
            "q_role": "student",
            "q_ai_use": "yes",
            "q_ai_freq": "weekly",
            "q_sat_efficiency": "4",
            "q_sat_quality": "3",
            "q_sat_reliability": "2",
            "q_sat_critical": "4",
            "q_open_feedback": "Cần có hướng dẫn sử dụng chính thức."
        }
    })
    assert sub_resp_E.status_code == 201
    resp_id_E = sub_resp_E.json()["response_id"]

    # 5. TEST-06: Kiểm tra chi tiết đánh giá chất lượng của từng phản hồi
    # Kiểm tra Ca B (Trùng lặp 100%)
    detail_B = client.get(f"/api/surveys/{survey_id}/responses/{resp_id_B}").json()
    assert detail_B["assessment"]["score_dup"] == 100.0
    assert any(f["code"] == "FLAG_EXACT_DUPLICATE" for f in detail_B["assessment"]["flags"])
    assert detail_B["assessment"]["closest_match_response_id"] == resp_id_A

    # Kiểm tra Ca C (Straightlining)
    detail_C = client.get(f"/api/surveys/{survey_id}/responses/{resp_id_C}").json()
    assert detail_C["assessment"]["score_pattern"] >= 80.0
    assert any(f["code"] == "FLAG_STRAIGHTLINING" for f in detail_C["assessment"]["flags"])

    # Kiểm tra Ca D (Mâu thuẫn logic)
    detail_D = client.get(f"/api/surveys/{survey_id}/responses/{resp_id_D}").json()
    assert detail_D["assessment"]["score_logic"] >= 80.0
    assert any(f["code"] == "FLAG_LOGIC_CONTRADICTION" for f in detail_D["assessment"]["flags"])

    # 6. TEST-07: Review Center & Cập nhật quyết định thẩm định
    # Người thẩm định xác nhận: Ca A là hợp lệ
    client.patch(f"/api/surveys/{survey_id}/responses/{resp_id_A}/review", json={
        "review_status": "verified_valid",
        "review_notes": "Phản hồi chuẩn từ sinh viên khoa CNTT"
    })

    # Người thẩm định xác nhận: Ca B là bản sao chép (bị loại)
    client.patch(f"/api/surveys/{survey_id}/responses/{resp_id_B}/review", json={
        "review_status": "verified_fraud",
        "review_notes": "Trùng khớp 100% với bản ghi trước đó, nghi vấn gửi lặp"
    })

    # 7. TEST-08: Analytics Dashboard tính toán số liệu thực
    analytics = client.get(f"/api/surveys/{survey_id}/analytics").json()
    assert analytics["total_responses"] == 5
    assert analytics["is_sample_size_sufficient"] is True
    assert analytics["risk_distribution"]["high"] >= 1
    assert analytics["review_distribution"]["verified_valid"] == 1
    assert analytics["review_distribution"]["verified_fraud"] == 1

    # 8. TEST-09: Xuất dữ liệu sạch đã kiểm định (Verified Clean Dataset)
    export_clean = client.get(f"/api/surveys/{survey_id}/export?scope=verified_clean&format=csv")
    assert export_clean.status_code == 200
    clean_csv = export_clean.content.decode("utf-8-sig")
    assert resp_id_A in clean_csv
    assert resp_id_B not in clean_csv  # Đã bị loại trừ vì là verified_fraud

    # 9. TEST-11: Thử đóng khảo sát và gửi tiếp
    client.post(f"/api/surveys/{survey_id}/close")
    sub_after_close = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": now.isoformat(),
        "submitted_at": now.isoformat(),
        "answers": {"q_role": "student"}
    })
    assert sub_after_close.status_code == 400
