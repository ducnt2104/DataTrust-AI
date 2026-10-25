import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_conjoint_routes_workflow():
    """Kiểm thử tích hợp đầu-cuối API Phân tích Đánh đổi Lựa chọn Choice-Based Conjoint (CBC / DCE)."""
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey/analytics/conjoint", json={
        "rating_question_id": "none",
        "attribute_question_ids": ["none1", "none2"]
    })
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Đánh Đổi Lựa Chọn Conjoint CBC Điện Thoại Thông Minh",
        "description": "Nghiên cứu đánh đổi tiện ích giữa Thương hiệu và Mức giá"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Cập nhật 3 câu hỏi: Thuộc tính Thương hiệu, Thuộc tính Mức giá, Đánh giá Sở thích (Rating)
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Đánh Đổi Lựa Chọn Conjoint CBC Điện Thoại Thông Minh",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Thương hiệu sản phẩm",
                "is_required": True,
                "options": ["Apple", "Samsung", "Xiaomi"],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Mức giá chào bán",
                "is_required": True,
                "options": ["10 Triệu", "15 Triệu", "20 Triệu"],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Mức độ ưa chuộng tổng thể (1-5 sao)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200

    # Publish survey
    client.post(f"/api/surveys/{survey_id}/publish")

    # Lấy ID câu hỏi từ public API
    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    q_brand_id = public_q[0]["id"]
    q_price_id = public_q[1]["id"]
    q_rating_id = public_q[2]["id"]

    # 4. Khi chưa đủ dữ liệu (< 6 phản hồi)
    insufficient_res = client.post(f"/api/surveys/{survey_id}/analytics/conjoint", json={
        "rating_question_id": q_rating_id,
        "attribute_question_ids": [q_brand_id, q_price_id]
    })
    assert insufficient_res.status_code == 200
    ins_data = insufficient_res.json()
    assert ins_data["status"] == "INSUFFICIENT_SAMPLE"

    # 5. Sinh 9 phản hồi mẫu trực giao
    now = datetime.now(timezone.utc)
    dataset = [
        ("Apple", "10 Triệu", 5),
        ("Apple", "15 Triệu", 4),
        ("Apple", "20 Triệu", 3),
        ("Samsung", "10 Triệu", 4),
        ("Samsung", "15 Triệu", 3),
        ("Samsung", "20 Triệu", 2),
        ("Xiaomi", "10 Triệu", 3),
        ("Xiaomi", "15 Triệu", 2),
        ("Xiaomi", "20 Triệu", 1),
    ]

    for i, (brand_val, price_val, rating_val) in enumerate(dataset):
        dur = 45 + i * 15
        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=dur + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 20)).isoformat(),
            "answers": {
                q_brand_id: brand_val,
                q_price_id: price_val,
                q_rating_id: rating_val
            },
            "client_metadata": {
                "user_agent": f"Conjoint Respondent {brand_val[:3]} {i}"
            }
        })
        assert sub_res.status_code == 201

    # 6. Gọi API phân tích Conjoint
    cj_res = client.post(f"/api/surveys/{survey_id}/analytics/conjoint", json={
        "rating_question_id": q_rating_id,
        "attribute_question_ids": [q_brand_id, q_price_id],
        "price_question_id": q_price_id,
        "scope": "all"
    })
    assert cj_res.status_code == 200
    res_data = cj_res.json()

    assert res_data["status"] == "SUCCESS"
    assert res_data["sample_size"] == 9
    assert res_data["attributes_count"] == 2
    assert res_data["model_fit"]["r_squared"] > 0.8
    assert len(res_data["importance_ranking"]) == 2
    assert "Thương hiệu sản phẩm" in res_data["part_worth_utilities"]
    assert "Mức giá chào bán" in res_data["part_worth_utilities"]
    assert "<svg" in res_data["svg_importance_chart"]
    assert "apa_narrative" in res_data
    assert "Conjoint Analysis" in res_data["apa_narrative"]

    # 7. Gọi API mô phỏng thị phần lựa chọn (Choice Simulator)
    sim_res = client.post(f"/api/surveys/{survey_id}/analytics/conjoint-simulate", json={
        "rating_question_id": q_rating_id,
        "attribute_question_ids": [q_brand_id, q_price_id],
        "candidate_profiles": [
            {
                "id": "Hồ sơ A (Apple Giá Cao)",
                "attributes": {"Thương hiệu sản phẩm": "Apple", "Mức giá chào bán": "20 Triệu"}
            },
            {
                "id": "Hồ sơ B (Xiaomi Giá Thấp)",
                "attributes": {"Thương hiệu sản phẩm": "Xiaomi", "Mức giá chào bán": "10 Triệu"}
            }
        ],
        "scope": "all"
    })
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["status"] == "SUCCESS"
    assert len(sim_data["market_shares"]) == 2
    total_share = sum(p["choice_share_pct"] for p in sim_data["market_shares"])
    assert abs(total_share - 100.0) < 0.2

    # 8. Kiểm tra audit trail
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    actions = [evt["action"] for evt in audit_res.json()["events"]]
    assert "CONJOINT_MODEL_EVALUATED" in actions
    assert "CONJOINT_SIMULATION_EVALUATED" in actions
