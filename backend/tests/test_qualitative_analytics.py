import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.engine.qualitative_engine import QualitativeEngine

client = TestClient(app)

def test_qualitative_engine_sentiment_evaluation():
    """Kiểm tra độ chính xác của phân tích cảm xúc tiếng Việt (Sentiment Analysis)"""
    # 1. Câu tích cực
    assert QualitativeEngine.evaluate_sentiment("Dịch vụ rất tuyệt vời, nhân viên nhiệt tình chu đáo") == "positive"
    assert QualitativeEngine.evaluate_sentiment("Giao diện đẹp mắt, dễ sử dụng và tốc độ rất nhanh") == "positive"
    
    # 2. Câu tiêu cực
    assert QualitativeEngine.evaluate_sentiment("Hệ thống quá chậm, thường xuyên bị lag và lỗi kết nối") == "negative"
    assert QualitativeEngine.evaluate_sentiment("Rất thất vọng vì thủ tục phức tạp và rườm rà") == "negative"

    # 3. Phủ định đảo nghĩa (Negation handling)
    assert QualitativeEngine.evaluate_sentiment("Dịch vụ không tốt và chẳng hài lòng tí nào") == "negative"
    assert QualitativeEngine.evaluate_sentiment("Tôi không thích giao diện này") == "negative"

    # 4. Trung tính
    assert QualitativeEngine.evaluate_sentiment("Tôi đã tham gia khảo sát vào lúc 8 giờ sáng") == "neutral"

def test_qualitative_thematic_clustering_and_api():
    """Kiểm tra phân cụm chủ đề định tính và endpoint API /analytics/qualitative"""
    # 1. Tạo khảo sát mới với câu hỏi văn bản mở
    res_create = client.post("/api/surveys", json={
        "title": "Khảo sát Đánh giá Trải nghiệm Người dùng Toàn diện",
        "description": "Thu thập ý kiến mở để phân tích chủ đề định tính"
    })
    assert res_create.status_code == 201
    survey_id = res_create.json()["id"]

    res_update = client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q_open",
                "order_index": 0,
                "question_type": "long_text",
                "title": "Xin hãy chia sẻ cảm nhận và đề xuất cải tiến của bạn về nền tảng?",
                "is_required": True,
                "options": []
            }
        ]
    })
    assert res_update.status_code == 200

    # Xuất bản khảo sát
    res_pub = client.post(f"/api/surveys/{survey_id}/publish")
    assert res_pub.status_code == 200
    slug = res_pub.json()["public_slug"]

    # 2. Gửi 5 phản hồi mở thuộc nhiều chủ đề và sắc thái khác nhau
    feedbacks = [
        "Giao diện trực quan, thiết kế đẹp và trải nghiệm người dùng rất tuyệt vời.",
        "Tốc độ tải trang rất nhanh, thời gian xử lý thủ tục ngắn không phải chờ đợi.",
        "Nhân viên tư vấn nhiệt tình, hỗ trợ tận tâm và giải đáp thắc mắc chi tiết.",
        "Hệ thống đôi lúc bị lỗi và chậm, tôi đề xuất nên bổ sung thêm tính năng lưu nháp.",
        "Chi phí dịch vụ khá hợp lý và minh bạch, tôi rất hài lòng."
    ]

    for idx, fb in enumerate(feedbacks):
        t1 = f"2026-10-23T20:1{idx}:00Z"
        t2 = f"2026-10-23T20:1{idx}:30Z"
        res_sub = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": t1,
            "submitted_at": t2,
            "answers": {"q_open": fb},
            "client_metadata": {"browser": "chrome"},
            "source": "online_form"
        })
        assert res_sub.status_code == 201

    # 3. Gọi API phân tích định tính
    res_qual = client.get(f"/api/surveys/{survey_id}/analytics/qualitative")
    assert res_qual.status_code == 200
    data = res_qual.json()

    assert data["survey_id"] == survey_id
    assert data["total_analyzed"] == 5
    assert data["sentiment_distribution"]["positive"] >= 3
    assert len(data["key_themes"]) >= 2
    assert "methodology_summary" in data

    # Kiểm tra cấu trúc từng chủ đề
    for theme in data["key_themes"]:
        assert "theme_name" in theme
        assert "sentiment" in theme
        assert theme["sentiment"] in ("positive", "neutral", "negative")
        assert theme["prevalence_percent"] > 0
        assert len(theme["sample_quotes"]) > 0
