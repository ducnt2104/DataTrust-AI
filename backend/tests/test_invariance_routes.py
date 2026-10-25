import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

try:
    from app.main import app
    from app.database import get_db
except ModuleNotFoundError:
    from backend.app.main import app
    from backend.app.database import get_db

client = TestClient(app)


def test_measurement_invariance_routes_workflow():
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-id/analytics/measurement-invariance", json={
        "grouping_question_id": "g1",
        "scale_question_ids": ["q1", "q2"]
    })
    assert res_404.status_code == 404

    # 2. Tạo khảo sát thực nghiệm bất biến đo lường
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Đánh Giá Bất Biến Đo Lường Đa Nhóm",
        "description": "Kiểm định Configural, Metric, Scalar và Strict Invariance"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 1 câu hỏi phân nhóm và 3 câu hỏi chỉ báo thang đo
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Đánh Giá Bất Biến Đo Lường Đa Nhóm",
        "questions": [
            {
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Giới tính",
                "is_required": True,
                "options": [
                    {"id": "male", "label": "Nam"},
                    {"id": "female", "label": "Nữ"}
                ],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Mục 1: Mức độ tương tác",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Mục 2: Trải nghiệm sử dụng",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "rating",
                "title": "Mục 3: Đánh giá tổng thể",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")
    surv_data = client.get(f"/api/surveys/{survey_id}").json()
    qs = surv_data["questions"]
    g_id = qs[0]["id"]
    i1_id = qs[1]["id"]
    i2_id = qs[2]["id"]
    i3_id = qs[3]["id"]

    # 4. Kiểm tra lỗi 400 nếu ít hơn 2 chỉ báo hoặc trùng biến nhóm
    res_400_few = client.post(f"/api/surveys/{survey_id}/analytics/measurement-invariance", json={
        "grouping_question_id": g_id,
        "scale_question_ids": [i1_id]
    })
    assert res_400_few.status_code == 400

    res_400_dup = client.post(f"/api/surveys/{survey_id}/analytics/measurement-invariance", json={
        "grouping_question_id": g_id,
        "scale_question_ids": [g_id, i1_id]
    })
    assert res_400_dup.status_code == 400

    # 5. Gửi 12 phản hồi mẫu (6 Nam, 6 Nữ)
    now = datetime.now(timezone.utc)
    cases = [
        # 6 Nam
        ("Nam", "4", "4", "5"),
        ("Nam", "5", "5", "5"),
        ("Nam", "3", "4", "4"),
        ("Nam", "4", "3", "4"),
        ("Nam", "5", "4", "5"),
        ("Nam", "3", "3", "4"),
        # 6 Nữ
        ("Nữ", "4", "4", "5"),
        ("Nữ", "5", "5", "5"),
        ("Nữ", "3", "4", "4"),
        ("Nữ", "4", "4", "4"),
        ("Nữ", "5", "5", "4"),
        ("Nữ", "4", "3", "3"),
    ]

    for idx, (grp, s1, s2, s3) in enumerate(cases):
        sub_body = {
            "started_at": (now - timedelta(minutes=20 - idx, seconds=30)).isoformat(),
            "submitted_at": (now - timedelta(minutes=20 - idx)).isoformat(),
            "answers": {
                g_id: grp,
                i1_id: s1,
                i2_id: s2,
                i3_id: s3
            },
            "client_metadata": {
                "ip_hash": f"ip_invariance_{idx}",
                "user_agent": "Mozilla/5.0 InvarianceTest"
            }
        }
        resp = client.post(f"/api/public/surveys/{slug}/submit", json=sub_body)
        assert resp.status_code == 201

    # 6. Gọi API kiểm định bất biến đo lường
    inv_res = client.post(f"/api/surveys/{survey_id}/analytics/measurement-invariance", json={
        "grouping_question_id": g_id,
        "scale_question_ids": [i1_id, i2_id, i3_id],
        "scope": "all"
    })
    assert inv_res.status_code == 200
    inv_data = inv_res.json()

    assert inv_data["status"] == "OK"
    assert inv_data["k_groups"] == 2
    assert inv_data["total_sample_size"] == 12
    assert inv_data["items_count"] == 3
    assert len(inv_data["models_summary"]) == 4
    assert len(inv_data["item_details"]) == 3
    assert "highest_level_achieved" in inv_data
    assert "verdict_badge" in inv_data
    assert "apa_narrative" in inv_data

    # 7. Kiểm tra vết kiểm toán bất biến
    with get_db() as conn:
        log = conn.execute("""
            SELECT action, details_json FROM audit_logs
            WHERE entity_id = ? AND action = 'MEASUREMENT_INVARIANCE_EVALUATED'
        """, (survey_id,)).fetchone()
        assert log is not None
        assert "k_groups" in log["details_json"]
