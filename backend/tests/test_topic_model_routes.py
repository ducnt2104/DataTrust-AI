import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_topic_modeling_routes_workflow():
    """Kiểm thử tích hợp đầu-cuối API Mô hình hóa Chủ đề Cấu trúc (STM/LDA)."""
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey/analytics/topic-modeling", json={
        "text_question_id": "q_text"
    })
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Đánh Giá Trải Nghiệm Khách Hàng và Góp Ý Mở",
        "description": "Thu thập phản hồi định tính để mô hình hóa chủ đề phân bổ Dirichlet tiềm ẩn (LDA)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo câu hỏi: Text mở (long_text) và Covariate Đánh giá (rating)
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Đánh Giá Trải Nghiệm Khách Hàng và Góp Ý Mở",
        "questions": [
            {
                "order_index": 0,
                "question_type": "long_text",
                "title": "Góp ý chất lượng dịch vụ và nền tảng",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Mức độ hài lòng tổng thể",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")

    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    text_qid = public_q[0]["id"]
    rating_qid = public_q[1]["id"]

    # 4. Kiểm tra lỗi 400 nếu text_question_id không hợp lệ
    res_400 = client.post(f"/api/surveys/{survey_id}/analytics/topic-modeling", json={
        "text_question_id": "invalid_question_id"
    })
    assert res_400.status_code == 400

    # 5. Kiểm tra khi chưa có phản hồi nào
    res_empty = client.post(f"/api/surveys/{survey_id}/analytics/topic-modeling", json={
        "text_question_id": text_qid
    })
    assert res_empty.status_code == 200
    assert res_empty.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 6. Gửi 10 phản hồi thực tế với văn bản tiếng Việt phong phú
    qualitative_texts = [
        ("Giao diện hệ thống rất đẹp, tốc độ tải trang nhanh và mượt mà.", 5),
        ("Hệ thống có giao diện trực quan, tốc độ xử lý rất nhanh và ổn định.", 5),
        ("Tốc độ tải chậm, giao diện cần cải tiến thêm nhiều tính năng mới.", 2),
        ("Giao diện thân thiện người dùng, tính năng tìm kiếm nhanh chóng.", 4),
        ("Dịch vụ khách hàng nhiệt tình, nhân viên hỗ trợ giải đáp rất chu đáo.", 5),
        ("Nhân viên hỗ trợ khách hàng chuyên nghiệp, dịch vụ chăm sóc tốt.", 5),
        ("Dịch vụ hỗ trợ chậm trễ, nhân viên chưa giải quyết thỏa đáng phản hồi.", 2),
        ("Chất lượng dịch vụ và chăm sóc khách hàng cần nâng cấp đào tạo nhân viên.", 3),
        ("Bảo mật hệ thống rất an toàn, dữ liệu khảo sát tin cậy.", 4),
        ("Nền tảng bảo mật thông tin tốt, quy trình khảo sát an toàn bảo mật.", 4)
    ]

    now = datetime.now(timezone.utc)
    for idx, (txt, rating) in enumerate(qualitative_texts):
        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=60 + idx)).isoformat(),
            "submitted_at": (now - timedelta(seconds=idx)).isoformat(),
            "answers": {
                text_qid: txt,
                rating_qid: rating
            },
            "client_metadata": {"user_agent": "Pytest Qualitative Tester"}
        })
        assert sub_res.status_code == 201

    # 7. Gọi API Topic Modeling
    res_analysis = client.post(f"/api/surveys/{survey_id}/analytics/topic-modeling", json={
        "text_question_id": text_qid,
        "covariate_question_id": rating_qid,
        "num_topics": 2,
        "num_iterations": 40,
        "scope": "all"
    })
    assert res_analysis.status_code == 200
    data = res_analysis.json()

    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 10
    assert data["num_topics"] == 2
    assert len(data["topics"]) == 2
    assert "mean_coherence_umass" in data
    assert len(data["covariate_effects"]) == 2
    assert "apa_narrative" in data
    assert "Latent Dirichlet Allocation" in data["apa_narrative"]

    # 8. Xác minh audit trail đã ghi lại nhật ký kiểm toán SHA-256
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    events = audit_res.json()["events"]
    assert any(e["action"] == "STRUCTURAL_TOPIC_MODEL_EVALUATED" for e in events)
