import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_mahalanobis_outliers_workflow():
    # 1. 404 cho survey không tồn tại
    res_404 = client.get("/api/surveys/non-existent-survey-id/analytics/multivariate-outliers")
    assert res_404.status_code == 404

    # 2. Tạo khảo sát học thuật với 3 biến thang đo Likert
    create_res = client.post("/api/surveys", json={
        "title": "Nghiên cứu Hành vi Khách hàng & Dị biệt Đa biến Mahalanobis",
        "description": "Kiểm định đa biến trên các thang đo dịch vụ",
        "instructions": "Vui lòng cho biết mức độ đánh giá của bạn từ 1 đến 5"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Cập nhật câu hỏi: 3 câu thang đo (rating) và 1 câu phân loại
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Nghiên cứu Hành vi Khách hàng & Dị biệt Đa biến Mahalanobis",
        "questions": [
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Chất lượng dịch vụ tư vấn (Likert 1-5)",
                "description": "1 là rất kém, 5 là rất tốt",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Mức độ tin cậy của giải pháp (Likert 1-5)",
                "description": "1 là hoàn toàn không tin, 5 là hoàn toàn tin cậy",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "rating",
                "title": "Sự sẵn lòng giới thiệu cho đồng nghiệp (Likert 1-5)",
                "description": "1 là chắc chắn không, 5 là chắc chắn có",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "order_index": 4,
                "question_type": "single_choice",
                "title": "Khu vực địa lý",
                "description": "Tỉnh/thành phố",
                "is_required": True,
                "options": ["Hà Nội", "Đà Nẵng", "TP. Hồ Chí Minh"],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Kiểm tra khi chưa có phản hồi nào
    res_no_resp = client.get(f"/api/surveys/{survey_id}/analytics/multivariate-outliers")
    assert res_no_resp.status_code == 200
    data_no_resp = res_no_resp.json()
    assert data_no_resp["status"] == "INSUFFICIENT_SAMPLE"
    assert data_no_resp["variable_count"] == 3

    # 5. Lấy ID câu hỏi từ public API
    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    q1_id = public_q[0]["id"]
    q2_id = public_q[1]["id"]
    q3_id = public_q[2]["id"]
    q4_id = public_q[3]["id"]

    # 6. Gửi 16 phản hồi bình thường (các câu trả lời dao động quanh [4, 4, 4] hoặc [3, 4, 4])
    base_samples = [
        ("4", "4", "5"), ("4", "5", "4"), ("5", "4", "4"), ("4", "4", "4"),
        ("3", "4", "4"), ("4", "3", "4"), ("5", "5", "4"), ("4", "5", "5"),
        ("4", "4", "3"), ("3", "3", "4"), ("4", "4", "4"), ("5", "4", "5"),
        ("4", "4", "4"), ("3", "4", "3"), ("4", "5", "4"), ("5", "5", "5")
    ]
    for idx, (v1, v2, v3) in enumerate(base_samples):
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": f"2026-10-24T02:{idx:02d}:00Z",
            "submitted_at": f"2026-10-24T02:{idx:02d}:45Z",
            "answers": {q1_id: v1, q2_id: v2, q3_id: v3, q4_id: "Hà Nội"}
        })

    # 7. Gửi 2 phản hồi dị biệt cực đoan trái ngược (VD: [1, 5, 1] hoặc [1, 1, 5])
    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": "2026-10-24T02:30:00Z",
        "submitted_at": "2026-10-24T02:30:50Z",
        "answers": {q1_id: "1", q2_id: "5", q3_id: "1", q4_id: "TP. Hồ Chí Minh"}
    })
    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": "2026-10-24T02:31:00Z",
        "submitted_at": "2026-10-24T02:31:55Z",
        "answers": {q1_id: "1", q2_id: "1", q3_id: "5", q4_id: "Đà Nẵng"}
    })

    # 8. Gọi endpoint kiểm định dị biệt đa biến Mahalanobis
    res_analysis = client.get(f"/api/surveys/{survey_id}/analytics/multivariate-outliers")
    assert res_analysis.status_code == 200
    data = res_analysis.json()

    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 18
    assert data["degrees_of_freedom"] == 3
    assert data["scale_variables_count"] == 3
    assert len(data["scale_variable_titles"]) == 3
    assert "Chất lượng dịch vụ tư vấn (Likert 1-5)" in data["scale_variable_titles"][0]
    assert data["mean_d2"] > 0
    assert len(data["outliers_summary"]) > 0

    # Phản hồi có D² lớn nhất phải có D² > 0 và có p-value
    top_outlier = data["outliers_summary"][0]
    assert "d2_mahalanobis" in top_outlier
    assert "p_value" in top_outlier
    assert "outlier_tier" in top_outlier
    assert top_outlier["d2_mahalanobis"] >= data["outliers_summary"][-1]["d2_mahalanobis"]
    assert "Kiểm định dị biệt đa biến Mahalanobis" in data["apa_interpretation"]

    # 9. Kiểm tra với question_ids tùy chọn
    res_custom_q = client.get(f"/api/surveys/{survey_id}/analytics/multivariate-outliers?question_ids={q1_id},{q2_id}")
    assert res_custom_q.status_code == 200
    data_custom = res_custom_q.json()
    assert data_custom["status"] == "SUCCESS"
    assert data_custom["degrees_of_freedom"] == 2
    assert len(data_custom["scale_variable_titles"]) == 2

    # 10. Kiểm tra khi chỉ truyền 1 question_id (INSUFFICIENT_VARIABLES)
    res_one_q = client.get(f"/api/surveys/{survey_id}/analytics/multivariate-outliers?question_ids={q1_id}")
    assert res_one_q.status_code == 200
    assert res_one_q.json()["status"] == "INSUFFICIENT_VARIABLES"
