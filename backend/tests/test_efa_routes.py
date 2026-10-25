import pytest
import random
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_efa_routes_workflow():
    # 1. 404 cho survey không tồn tại
    res_404 = client.get("/api/surveys/non-existent-survey-id/analytics/efa")
    assert res_404.status_code == 404

    # 2. Tạo khảo sát học thuật với 6 câu hỏi thang đo Likert (2 thứ nguyên độc lập)
    create_res = client.post("/api/surveys", json={
        "title": "Nghiên cứu Khám phá Cấu trúc Nhân tố EFA Thang Đo Dịch Vụ Số",
        "description": "Đo lường Hiệu năng Kỹ thuật và Chất lượng Chăm sóc Khách hàng",
        "instructions": "Đánh giá theo thang đo từ 1 (Rất kém) đến 5 (Rất tốt)"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 6 câu hỏi thang đo
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Nghiên cứu Khám phá Cấu trúc Nhân tố EFA Thang Đo Dịch Vụ Số",
        "questions": [
            # Nhóm 1: Hiệu năng Kỹ thuật
            {"order_index": 1, "question_type": "rating", "title": "Tốc độ phản hồi phần mềm", "is_required": True, "options": ["1","2","3","4","5"], "logic_rules": []},
            {"order_index": 2, "question_type": "rating", "title": "Độ mượt mà khi thao tác", "is_required": True, "options": ["1","2","3","4","5"], "logic_rules": []},
            {"order_index": 3, "question_type": "rating", "title": "Sự ổn định của hệ thống", "is_required": True, "options": ["1","2","3","4","5"], "logic_rules": []},
            # Nhóm 2: Chăm sóc Khách hàng
            {"order_index": 4, "question_type": "rating", "title": "Thái độ của nhân viên hỗ trợ", "is_required": True, "options": ["1","2","3","4","5"], "logic_rules": []},
            {"order_index": 5, "question_type": "rating", "title": "Thời gian giải đáp thắc mắc", "is_required": True, "options": ["1","2","3","4","5"], "logic_rules": []},
            {"order_index": 6, "question_type": "rating", "title": "Sự nhiệt tình của tư vấn viên", "is_required": True, "options": ["1","2","3","4","5"], "logic_rules": []}
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")

    # 4. Kiểm tra khi chưa có phản hồi nào
    res_no_resp = client.get(f"/api/surveys/{survey_id}/analytics/efa")
    assert res_no_resp.status_code == 200
    assert res_no_resp.json()["status"] == "INSUFFICIENT_SAMPLE"
    assert res_no_resp.json()["variable_count"] == 6

    # 5. Lấy danh sách ID câu hỏi
    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    q_ids = [q["id"] for q in public_q]

    # 6. Gửi 35 phản hồi theo 2 nhân tố tiềm ẩn
    random.seed(101)
    for idx in range(35):
        # f1: Hiệu năng kỹ thuật
        f1_level = random.choice([2.0, 3.0, 4.0, 5.0])
        # f2: Hỗ trợ khách hàng (độc lập với f1)
        f2_level = random.choice([1.0, 2.0, 4.0, 5.0])

        q1 = max(1, min(5, int(round(f1_level + random.uniform(-0.5, 0.5)))))
        q2 = max(1, min(5, int(round(f1_level + random.uniform(-0.5, 0.5)))))
        q3 = max(1, min(5, int(round(f1_level + random.uniform(-0.5, 0.5)))))

        q4 = max(1, min(5, int(round(f2_level + random.uniform(-0.5, 0.5)))))
        q5 = max(1, min(5, int(round(f2_level + random.uniform(-0.5, 0.5)))))
        q6 = max(1, min(5, int(round(f2_level + random.uniform(-0.5, 0.5)))))

        client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": f"2026-10-24T02:{idx:02d}:00Z",
            "submitted_at": f"2026-10-24T02:{idx:02d}:40Z",
            "answers": {
                q_ids[0]: str(q1),
                q_ids[1]: str(q2),
                q_ids[2]: str(q3),
                q_ids[3]: str(q4),
                q_ids[4]: str(q5),
                q_ids[5]: str(q6)
            }
        })

    # 7. Gọi API EFA với xoay Varimax mặc định
    res_efa = client.get(f"/api/surveys/{survey_id}/analytics/efa")
    assert res_efa.status_code == 200
    data = res_efa.json()

    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 35
    assert data["variables_count"] == 6
    assert data["rotation_method"] == "Varimax"

    # Kiểm tra các chỉ số học thuật cốt lõi
    assert data["kmo_overall"] >= 0.50
    assert data["is_kmo_acceptable"] is True
    assert "kmo_verdict" in data
    assert data["is_bartlett_significant"] is True
    assert data["bartlett_df"] == 15  # 6*5/2 = 15
    assert data["factors_extracted_count"] == 2
    assert len(data["factors"]) == 2
    assert data["cumulative_variance_extracted_pct"] >= 50.0

    # Kiểm tra cấu trúc phân nhóm nhân tố xoay Varimax
    assert len(data["items"]) == 6
    for item in data["items"]:
        assert "question_title" in item
        assert "communality" in item
        assert "factor_loadings" in item
        assert len(item["factor_loadings"]) == 2

    # Scree Plot Data
    assert len(data["scree_plot_data"]) == 6
    assert data["scree_plot_data"][0]["threshold"] == 1.0

    # APA Narrative
    assert "Phân tích nhân tố khám phá (EFA)" in data["apa_interpretation"]

    # 8. Kiểm tra EFA với tham số rotation=none và forced_factors=1
    res_none = client.get(f"/api/surveys/{survey_id}/analytics/efa?rotation=none&forced_factors=1")
    assert res_none.status_code == 200
    data_none = res_none.json()
    assert data_none["status"] == "SUCCESS"
    assert data_none["rotation_method"] == "None"
    assert data_none["factors_extracted_count"] == 1
    assert len(data_none["items"][0]["factor_loadings"]) == 1

    # 9. Kiểm tra với question_ids tùy chọn
    subset_ids = f"{q_ids[0]},{q_ids[1]},{q_ids[2]}"
    res_subset = client.get(f"/api/surveys/{survey_id}/analytics/efa?question_ids={subset_ids}")
    assert res_subset.status_code == 200
    data_subset = res_subset.json()
    assert data_subset["status"] == "SUCCESS"
    assert data_subset["variables_count"] == 3
