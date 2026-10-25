import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_irt_4pl_routes_workflow():
    """Kiểm thử tích hợp đầu-cuối API Mô hình IRT 3PL & 4PL (Birnbaum 1968, Lord 1980, Magis 2013)."""
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-survey/analytics/irt-4pl", json={
        "question_ids": ["q1", "q2"]
    })
    assert res_404.status_code == 404

    # 2. Tạo cuộc khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Bài Trắc Nghiệm Đánh Giá Năng Lực Toán & Logic (IRT 4PL)",
        "description": "Kiểm định mô hình 4 tham số logistic với đoán mò và đãng trí"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Thêm 3 câu hỏi đánh giá 1-5 sao
    put_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": "Bài Trắc Nghiệm Đánh Giá Năng Lực Toán & Logic (IRT 4PL)",
        "questions": [
            {
                "order_index": 0,
                "question_type": "rating",
                "title": "Câu hỏi Dễ (Basic Concept)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Câu hỏi Trung bình (Application)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Câu hỏi Khó (Advanced Synthesis)",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert put_res.status_code == 200

    # Publish survey để mở cổng nhận phản hồi
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200

    survey_data = client.get(f"/api/surveys/{survey_id}").json()
    questions = survey_data["questions"]
    assert len(questions) == 3
    q_easy = questions[0]["id"]
    q_med = questions[1]["id"]
    q_hard = questions[2]["id"]

    # 4. Khi chưa có phản hồi (< 8)
    empty_res = client.post(f"/api/surveys/{survey_id}/analytics/irt-4pl", json={
        "question_ids": [q_easy, q_med, q_hard]
    })
    assert empty_res.status_code == 200
    assert empty_res.json()["status"] == "INSUFFICIENT_SAMPLE"

    # 5. Sinh 24 phản hồi có phân hóa năng lực
    now = datetime.now(timezone.utc)
    for i in range(24):
        dur = 50 + (i * 15)
        # Điểm tương quan với năng lực i
        score_easy = min(5, max(1, 2 + (i // 5)))
        score_med = min(5, max(1, 1 + (i // 6)))
        score_hard = min(5, max(1, 1 + (i // 8)))

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=dur + i * 20)).isoformat(),
            "submitted_at": (now - timedelta(seconds=i * 20)).isoformat(),
            "answers": {
                q_easy: score_easy,
                q_med: score_med,
                q_hard: score_hard
            }
        })
        assert sub_res.status_code == 201

    # 6. Gọi API ước lượng mô hình IRT 4PL
    res_4pl = client.post(f"/api/surveys/{survey_id}/analytics/irt-4pl", json={
        "question_ids": [q_easy, q_med, q_hard],
        "model_type": "4pl",
        "scope": "all"
    })
    assert res_4pl.status_code == 200
    data_4pl = res_4pl.json()

    assert data_4pl["status"] == "SUCCESS"
    assert data_4pl["sample_size"] == 24
    assert data_4pl["items_count"] == 3
    assert data_4pl["model_type"] == "4PL"
    assert len(data_4pl["items_parameters"]) == 3
    for it in data_4pl["items_parameters"]:
        assert it["discrimination_a"] > 0
        assert it["guessing_c"] > 0
        assert it["inattention_d"] <= 1.0

    # Kiểm tra TIF, CAT simulation, SVG, APA
    assert "test_information_function" in data_4pl
    assert "cat_simulation" in data_4pl
    assert len(data_4pl["cat_simulation"]) >= 2
    assert "<svg" in data_4pl["svg_curves"]
    assert "4PL" in data_4pl["apa_narrative"]

    # 7. Gọi API ước lượng mô hình IRT 3PL (cố định d=1.0)
    res_3pl = client.post(f"/api/surveys/{survey_id}/analytics/irt-4pl", json={
        "question_ids": [q_easy, q_med, q_hard],
        "model_type": "3pl",
        "scope": "all"
    })
    assert res_3pl.status_code == 200
    data_3pl = res_3pl.json()
    assert data_3pl["model_type"] == "3PL"
    for it in data_3pl["items_parameters"]:
        assert it["inattention_d"] == 1.0

    # 8. Kiểm tra audit trail
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    actions = [evt["action"] for evt in audit_res.json()["events"]]
    assert "IRT_4PL_MODEL_EVALUATED" in actions
