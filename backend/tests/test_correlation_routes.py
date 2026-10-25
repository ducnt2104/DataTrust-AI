import pytest
import random
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_correlation_routes_workflow():
    # 1. 404 cho survey không tồn tại
    res_404 = client.get("/api/surveys/non-existent-id/analytics/correlation")
    assert res_404.status_code == 404

    # 2. Tạo khảo sát thực nghiệm 3 biến thang đo
    create_res = client.post("/api/surveys", json={
        "title": "Nghiên cứu Ma trận Tương quan Chất Lượng - Hài Lòng - Trung Thành",
        "description": "Kiểm tra tương quan đôi Pearson và Spearman",
        "instructions": "Vui lòng cho điểm từ 1 đến 5"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 3 câu hỏi thang đo rating
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Nghiên cứu Ma trận Tương quan Chất Lượng - Hài Lòng - Trung Thành",
        "questions": [
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Chất lượng dịch vụ tổng thể",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Mức độ hài lòng của khách hàng",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "rating",
                "title": "Ý định tiếp tục gắn bó",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")

    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    q1_id = public_q[0]["id"]
    q2_id = public_q[1]["id"]
    q3_id = public_q[2]["id"]

    # 4. Gửi 20 phản hồi có tính tương quan thực nghiệm cao
    random.seed(42)
    for i in range(20):
        # Q1 từ 1 đến 5
        base_val = (i % 5) + 1
        # Q2 tương quan cao với Q1 (+- 0.5)
        noise = random.choice([0, 0, 1, -1])
        val_q2 = max(1, min(5, base_val + noise))
        # Q3 ngẫu nhiên
        val_q3 = random.choice([2, 3, 4])

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": f"2026-10-24T02:{i:02d}:00Z",
            "submitted_at": f"2026-10-24T02:{i:02d}:45Z",
            "answers": {
                q1_id: str(base_val),
                q2_id: str(val_q2),
                q3_id: str(val_q3)
            }
        })
        assert sub_res.status_code == 201

    # 5. Gọi API Pearson Correlation
    res_pearson = client.get(f"/api/surveys/{survey_id}/analytics/correlation?method=pearson")
    assert res_pearson.status_code == 200
    data_p = res_pearson.json()

    assert data_p["status"] == "SUCCESS"
    assert data_p["method"] == "pearson"
    assert data_p["variables_count"] == 3
    assert data_p["total_pairs_count"] == 3
    assert len(data_p["matrix"]) == 3

    # Kiểm tra đường chéo và tính đối xứng
    for r_idx in range(3):
        assert data_p["matrix"][r_idx][r_idx]["correlation"] == 1.0

    # q1 và q2 phải có tương quan dương mạnh
    r_q1_q2 = data_p["matrix"][0][1]["correlation"]
    assert r_q1_q2 > 0.60
    assert data_p["matrix"][0][1]["is_significant_05"] is True
    assert data_p["matrix"][1][0]["correlation"] == r_q1_q2

    # APA text có tồn tại
    assert "Pearson" in data_p["apa_interpretation"]

    # 6. Gọi API Spearman Correlation
    res_spearman = client.get(f"/api/surveys/{survey_id}/analytics/correlation?method=spearman")
    assert res_spearman.status_code == 200
    data_s = res_spearman.json()
    assert data_s["status"] == "SUCCESS"
    assert data_s["method"] == "spearman"
    assert "Spearman" in data_s["apa_interpretation"]

    # 7. Lọc theo question_ids cụ thể (chỉ 2 biến q1, q2)
    res_filtered = client.get(f"/api/surveys/{survey_id}/analytics/correlation?question_ids={q1_id},{q2_id}")
    assert res_filtered.status_code == 200
    data_f = res_filtered.json()
    assert data_f["variables_count"] == 2
    assert data_f["total_pairs_count"] == 1
