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


def test_scale_equating_routes_workflow():
    # 1. 404 cho survey không tồn tại
    res_404 = client.post("/api/surveys/non-existent-id/analytics/scale-equating", json={
        "source_question_id": "q1",
        "target_question_id": "q2"
    })
    assert res_404.status_code == 404

    # 2. Tạo khảo sát thử nghiệm liên kết thang đo
    create_res = client.post("/api/surveys", json={
        "title": "Khảo Sát Thực Nghiệm Liên Kết Thang Đo",
        "description": "Chuẩn hóa Likert 5 điểm sang NPS 10 điểm"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 3. Tạo 2 câu hỏi thang đo khác nhau
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Khảo Sát Thực Nghiệm Liên Kết Thang Đo",
        "questions": [
            {
                "order_index": 0,
                "question_type": "rating",
                "title": "Mức độ hài lòng thang 5 sao",
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "order_index": 1,
                "question_type": "nps",
                "title": "Chỉ số trung thành NPS thang 10",
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })

    client.post(f"/api/surveys/{survey_id}/publish")
    surv_data = client.get(f"/api/surveys/{survey_id}").json()
    qs = surv_data["questions"]
    q1_id = qs[0]["id"]
    q2_id = qs[1]["id"]

    # 4. Kiểm tra lỗi 400 nếu truyền trùng source và target
    res_400 = client.post(f"/api/surveys/{survey_id}/analytics/scale-equating", json={
        "source_question_id": q1_id,
        "target_question_id": q1_id
    })
    assert res_400.status_code == 400

    # 5. Gửi 8 phản hồi mẫu
    now = datetime.now(timezone.utc)
    pairs = [
        ("1", "2"),
        ("2", "4"),
        ("3", "6"),
        ("3", "5"),
        ("4", "8"),
        ("4", "7"),
        ("5", "9"),
        ("5", "10"),
    ]

    for idx, (v1, v2) in enumerate(pairs):
        sub_body = {
            "started_at": (now - timedelta(minutes=10 - idx, seconds=30)).isoformat(),
            "submitted_at": (now - timedelta(minutes=10 - idx)).isoformat(),
            "answers": {
                q1_id: v1,
                q2_id: v2
            },
            "client_metadata": {
                "ip_hash": f"ip_equating_{idx}",
                "user_agent": "Mozilla/5.0 EquatingTest"
            }
        }
        resp = client.post(f"/api/public/surveys/{slug}/submit", json=sub_body)
        assert resp.status_code == 201

    # 6. Gọi API scale-equating
    eq_res = client.post(f"/api/surveys/{survey_id}/analytics/scale-equating", json={
        "source_question_id": q1_id,
        "target_question_id": q2_id,
        "scope": "all"
    })
    assert eq_res.status_code == 200
    eq_data = eq_res.json()

    assert eq_data["status"] == "OK"
    assert eq_data["sample_sizes"]["x_count"] == 8
    assert eq_data["sample_sizes"]["y_count"] == 8
    assert "linear_equating" in eq_data
    assert eq_data["linear_equating"]["slope_alpha"] > 0
    assert len(eq_data["concordance_table"]) >= 5
    assert "apa_narrative" in eq_data

    # 7. Kiểm tra vết kiểm toán bất biến
    with get_db() as conn:
        log = conn.execute("""
            SELECT action, details_json FROM audit_logs
            WHERE entity_id = ? AND action = 'SCALE_EQUATING_ANALYSIS_PERFORMED'
        """, (survey_id,)).fetchone()
        assert log is not None
        assert "slope_alpha" in log["details_json"]
