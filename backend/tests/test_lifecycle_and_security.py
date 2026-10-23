import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_survey_reopen_and_duplicate(client: TestClient):
    """
    Kiểm thử vòng đời khảo sát: Đóng, Mở lại và Nhân bản khảo sát
    """
    # 1. Tạo khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Khảo sát Nghiên cứu Thị trường Ban đầu",
        "description": "Thử nghiệm vòng đời đóng mở và nhân bản"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]

    # Thêm câu hỏi
    up_res = client.put(f"/api/surveys/{survey_id}", json={
        "questions": [{
            "id": "q_brand_test",
            "question_type": "single_choice",
            "title": "Thương hiệu yêu thích",
            "order_index": 0,
            "is_required": True,
            "options": [{"id": "opt1", "label": "A"}, {"id": "opt2", "label": "B"}],
            "logic_rules": []
        }]
    })
    assert up_res.status_code == 200

    # Xuất bản
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200
    slug = pub_res.json()["public_slug"]

    # Đóng khảo sát
    close_res = client.post(f"/api/surveys/{survey_id}/close")
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "closed"

    # Kiểm tra link công khai từ chối với HTTP 410 Gone khi đã đóng
    pub_get = client.get(f"/api/public/surveys/{slug}")
    assert pub_get.status_code == 410

    # Mở lại khảo sát (Reopen)
    reopen_res = client.post(f"/api/surveys/{survey_id}/reopen")
    assert reopen_res.status_code == 200
    assert reopen_res.json()["status"] == "published"
    assert reopen_res.json()["closed_at"] is None

    # Link công khai lại hoạt động bình thường
    pub_get_again = client.get(f"/api/public/surveys/{slug}")
    assert pub_get_again.status_code == 200

    # 2. Nhân bản khảo sát (Duplicate)
    dup_res = client.post(f"/api/surveys/{survey_id}/duplicate")
    assert dup_res.status_code == 201
    dup_data = dup_res.json()
    assert dup_data["id"] != survey_id
    assert "Bản sao của" in dup_data["title"]
    assert dup_data["status"] == "draft" # Bản sao bắt đầu ở dạng nháp
    assert len(dup_data["questions"]) == 1
    assert dup_data["questions"][0]["title"] == "Thương hiệu yêu thích"
    assert dup_data["responses_count"] == 0

def test_public_security_double_click_and_rate_limit(client: TestClient):
    """
    Kiểm thử bảo mật: Bảo vệ chống nộp trùng lặp do double click và Giới hạn tốc độ (Rate Limiting)
    """
    # 1. Tạo và xuất bản khảo sát
    create_res = client.post("/api/surveys", json={
        "title": "Khảo sát Kiểm thử Bảo mật",
        "description": "Thử nghiệm Rate limit và Double click"
    })
    survey_id = create_res.json()["id"]

    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [{
            "id": "q_sec_1",
            "question_type": "short_text",
            "title": "Nội dung phản hồi",
            "order_index": 0,
            "is_required": True,
            "options": [],
            "logic_rules": []
        }]
    })

    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    slug = pub_res.json()["public_slug"]

    # 2. Kiểm thử bảo vệ chống nộp trùng do double click (2 lần liên tiếp cùng payload trong 1 giây)
    sub1 = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": "2026-10-23T08:00:00Z",
        "submitted_at": "2026-10-23T08:00:15Z",
        "duration_seconds": 15.0,
        "answers": {"q_sec_1": "Test an toàn"}
    }, headers={"X-Test-Bypass": "1"})
    assert sub1.status_code == 201
    resp1_id = sub1.json()["response_id"]

    # Gửi lại ngay lập tức (mô phỏng click đúp)
    sub2 = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": "2026-10-23T08:00:00Z",
        "submitted_at": "2026-10-23T08:00:15Z",
        "duration_seconds": 15.0,
        "answers": {"q_sec_1": "Test an toàn"}
    }, headers={"X-Test-Bypass": "1"})
    assert sub2.status_code == 201
    # Hệ thống phải trả về response_id cũ mà không tạo bản ghi mới trùng lặp
    assert sub2.json()["response_id"] == resp1_id

    # 3. Kiểm thử Rate Limiting (gửi liên tiếp vượt ngưỡng 40 req/phút không có header bypass)
    # Reset limiter history cho test client nếu cần
    from app.middleware.rate_limiter import public_submission_limiter
    public_submission_limiter.history.clear()

    hit_rate_limit = False
    for _ in range(45):
        r = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": "2026-10-23T08:00:00Z",
            "submitted_at": "2026-10-23T08:00:15Z",
            "duration_seconds": 15.0,
            "answers": {"q_sec_1": f"Flood test {_}"}
        }, headers={"X-Test-Rate-Limit": "1"})
        if r.status_code == 429:
            hit_rate_limit = True
            assert "Retry-After" in r.headers
            break

    assert hit_rate_limit is True
