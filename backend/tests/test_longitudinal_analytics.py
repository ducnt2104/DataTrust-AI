import uuid
import pytest
from fastapi.testclient import TestClient

def test_longitudinal_wave_comparison_endpoint(client: TestClient):
    # 1. Tạo Khảo sát Đợt 1 (Wave 1 / Pre-test)
    res_w1 = client.post("/api/surveys", json={
        "title": "Đánh giá Năng lực Số Sinh viên — Đợt 1 (Pre-intervention)",
        "description": "Đo lường đầu vào trước khóa tập huấn"
    })
    assert res_w1.status_code == 201
    w1_id = res_w1.json()["id"]

    q1_scale_id = f"q_scale_{uuid.uuid4().hex[:6]}"
    q1_cat_id = f"q_cat_{uuid.uuid4().hex[:6]}"

    client.put(f"/api/surveys/{w1_id}", json={
        "questions": [
            {
                "id": q1_scale_id,
                "question_type": "rating",
                "title": "Mức độ tự tin ứng dụng AI trong nghiên cứu",
                "order_index": 0,
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "id": q1_cat_id,
                "question_type": "single_choice",
                "title": "Tần suất sử dụng công cụ số",
                "order_index": 1,
                "is_required": True,
                "options": ["Hàng ngày", "Hàng tuần", "Hiếm khi"],
                "logic_rules": []
            }
        ]
    })
    pub_w1 = client.post(f"/api/surveys/{w1_id}/publish")
    assert pub_w1.status_code == 200
    slug_w1 = pub_w1.json()["public_slug"]

    # Nộp 6 phản hồi phân biệt cho Wave 1: điểm thấp (trung bình ~2.3)
    w1_scores = [1, 2, 3, 2, 3, 1]
    w1_cats = ["Hiếm khi", "Hàng tuần", "Hiếm khi", "Hàng ngày", "Hàng tuần", "Hiếm khi"]
    for i in range(6):
        client.post(f"/api/public/surveys/{slug_w1}/submit", json={
            "started_at": f"2026-10-23T08:0{i}:00Z",
            "submitted_at": f"2026-10-23T08:0{i}:30Z",
            "duration_seconds": 25.0 + i,
            "client_metadata": {"ip": f"10.0.0.{i+1}", "user_agent": f"Tester-{i}"},
            "answers": {q1_scale_id: w1_scores[i], q1_cat_id: w1_cats[i]}
        })

    # 2. Tạo Khảo sát Đợt 2 (Wave 2 / Post-test)
    res_w2 = client.post("/api/surveys", json={
        "title": "Đánh giá Năng lực Số Sinh viên — Đợt 2 (Post-intervention)",
        "description": "Đo lường kết quả sau khóa tập huấn"
    })
    assert res_w2.status_code == 201
    w2_id = res_w2.json()["id"]

    q2_scale_id = f"q_scale_{uuid.uuid4().hex[:6]}"
    q2_cat_id = f"q_cat_{uuid.uuid4().hex[:6]}"

    client.put(f"/api/surveys/{w2_id}", json={
        "questions": [
            {
                "id": q2_scale_id,
                "question_type": "rating",
                # Khớp tiêu đề giống hệt Wave 1
                "title": "Mức độ tự tin ứng dụng AI trong nghiên cứu",
                "order_index": 0,
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "id": q2_cat_id,
                "question_type": "single_choice",
                "title": "Tần suất sử dụng công cụ số",
                "order_index": 1,
                "is_required": True,
                "options": ["Hàng ngày", "Hàng tuần", "Hiếm khi"],
                "logic_rules": []
            }
        ]
    })
    pub_w2 = client.post(f"/api/surveys/{w2_id}/publish")
    assert pub_w2.status_code == 200
    slug_w2 = pub_w2.json()["public_slug"]

    # Nộp 6 phản hồi phân biệt cho Wave 2: điểm cao (trung bình ~4.5)
    w2_scores = [4, 5, 5, 4, 5, 4]
    w2_cats = ["Hàng ngày", "Hàng ngày", "Hàng tuần", "Hàng ngày", "Hàng tuần", "Hàng ngày"]
    for i in range(6):
        client.post(f"/api/public/surveys/{slug_w2}/submit", json={
            "started_at": f"2026-10-23T09:0{i}:00Z",
            "submitted_at": f"2026-10-23T09:0{i}:30Z",
            "duration_seconds": 28.0 + i,
            "client_metadata": {"ip": f"10.0.1.{i+1}", "user_agent": f"Tester-W2-{i}"},
            "answers": {q2_scale_id: w2_scores[i], q2_cat_id: w2_cats[i]}
        })

    # 3. Gọi API phân tích dọc (Longitudinal Comparison) với scope=all
    res_comp = client.get(f"/api/surveys/{w2_id}/analytics/longitudinal?compare_survey_id={w1_id}&scope=all")
    assert res_comp.status_code == 200
    data = res_comp.json()

    assert data["matched_questions_count"] == 2
    assert data["wave1_survey"]["survey_id"] == w1_id
    assert data["wave2_survey"]["survey_id"] == w2_id
    assert data["wave1_survey"]["total_responses"] == 6
    assert data["wave2_survey"]["total_responses"] == 6

    # Kiểm tra chỉ tiêu thang đo
    scale_item = next(it for it in data["items"] if it["is_scale"] is True)
    assert scale_item["mean_wave1"] < 3.0
    assert scale_item["mean_wave2"] > 4.0
    assert scale_item["mean_shift"] > 1.5
    assert scale_item["cohens_d"] > 0.8  # Hiệu ứng lớn (Large Effect)
    assert "Large Effect" in scale_item["effect_size"]
    assert scale_item["is_statistically_significant"] is True
    assert scale_item["trend_direction"] == "INCREASED"
    assert "t(" in scale_item["apa_summary"]
    assert "d =" in scale_item["apa_summary"]

    # Kiểm tra biến định danh (Categorical Shift)
    cat_item = next(it for it in data["items"] if it["is_scale"] is False)
    assert cat_item["trend_direction"] == "SHIFTED"
    assert "Dịch chuyển lớn nhất" in cat_item["apa_summary"]
    assert len(cat_item["category_shifts"]) == 3


    # Kết luận tổng thể
    assert data["items_increased_count"] >= 1
    assert "Xu hướng tích cực rõ rệt" in data["comparative_summary"]

def test_longitudinal_wave_comparison_validation_errors(client: TestClient):
    # Khảo sát không tồn tại
    fake_id = str(uuid.uuid4())
    res_fake = client.get(f"/api/surveys/{fake_id}/analytics/longitudinal?compare_survey_id={fake_id}")
    # Phải bắt lỗi khi 2 ID trùng nhau
    assert res_fake.status_code == 400
    assert "phải khác" in res_fake.json()["detail"]
