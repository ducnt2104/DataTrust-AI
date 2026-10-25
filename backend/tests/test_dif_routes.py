import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)

def test_dif_route_mantel_haenszel_endpoint():
    # 1. Tạo khảo sát
    res = client.post("/api/surveys", json={"title": "Khảo sát Kiểm định Bất biến Đo lường DIF"})
    assert res.status_code == 201
    survey_id = res.json()["id"]

    q_grp = f"q_gender_{uuid.uuid4().hex[:6]}"
    q_scale1 = f"q_s1_{uuid.uuid4().hex[:6]}"
    q_scale2 = f"q_s2_{uuid.uuid4().hex[:6]}"
    q_scale3 = f"q_s3_{uuid.uuid4().hex[:6]}"

    with get_db() as conn:
        conn.execute("INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at) VALUES (?, ?, 1, 'single_choice', 'Giới tính', 1, '[\"Nam\", \"Nữ\"]', '2026-10-24T00:00:00Z')", (q_grp, survey_id))
        conn.execute("INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at) VALUES (?, ?, 2, 'rating', 'Mức độ hài lòng dịch vụ', 1, '[]', '2026-10-24T00:00:00Z')", (q_scale1, survey_id))
        conn.execute("INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at) VALUES (?, ?, 3, 'rating', 'Mức độ tin cậy nền tảng', 1, '[]', '2026-10-24T00:00:00Z')", (q_scale2, survey_id))
        conn.execute("INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at) VALUES (?, ?, 4, 'rating', 'Ý định tiếp tục sử dụng', 1, '[]', '2026-10-24T00:00:00Z')", (q_scale3, survey_id))

        # Thêm 20 phản hồi (10 Nam, 10 Nữ)
        for i in range(10):
            rid = str(uuid.uuid4())
            conn.execute("INSERT INTO responses (id, survey_id, started_at, submitted_at, duration_seconds, risk_score, risk_level, review_status) VALUES (?, ?, '2026-10-24T00:00:00Z', '2026-10-24T00:01:00Z', 60.0, 0.0, 'low', 'verified_valid')", (rid, survey_id))
            conn.execute("INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at) VALUES (?, ?, ?, '\"Nam\"', '2026-10-24T00:00:00Z')", (str(uuid.uuid4()), rid, q_grp))
            conn.execute("INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at) VALUES (?, ?, ?, '4', '2026-10-24T00:00:00Z')", (str(uuid.uuid4()), rid, q_scale1))
            conn.execute("INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at) VALUES (?, ?, ?, '5', '2026-10-24T00:00:00Z')", (str(uuid.uuid4()), rid, q_scale2))
            conn.execute("INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at) VALUES (?, ?, ?, '4', '2026-10-24T00:00:00Z')", (str(uuid.uuid4()), rid, q_scale3))

        for i in range(10):
            rid = str(uuid.uuid4())
            conn.execute("INSERT INTO responses (id, survey_id, started_at, submitted_at, duration_seconds, risk_score, risk_level, review_status) VALUES (?, ?, '2026-10-24T00:00:00Z', '2026-10-24T00:01:00Z', 60.0, 0.0, 'low', 'verified_valid')", (rid, survey_id))
            conn.execute("INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at) VALUES (?, ?, ?, '\"Nữ\"', '2026-10-24T00:00:00Z')", (str(uuid.uuid4()), rid, q_grp))
            conn.execute("INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at) VALUES (?, ?, ?, '4', '2026-10-24T00:00:00Z')", (str(uuid.uuid4()), rid, q_scale1))
            conn.execute("INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at) VALUES (?, ?, ?, '5', '2026-10-24T00:00:00Z')", (str(uuid.uuid4()), rid, q_scale2))
            conn.execute("INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at) VALUES (?, ?, ?, '4', '2026-10-24T00:00:00Z')", (str(uuid.uuid4()), rid, q_scale3))

    # 2. Gọi endpoint GET /api/surveys/{survey_id}/analytics/dif
    params = {
        "grouping_question_id": q_grp,
        "reference_group": "Nam",
        "focal_group": "Nữ",
        "scope": "verified_clean"
    }
    dif_res = client.get(f"/api/surveys/{survey_id}/analytics/dif", params=params)
    assert dif_res.status_code == 200
    data = dif_res.json()

    assert data["survey_id"] == survey_id
    assert data["reference_group"] == "Nam"
    assert data["focal_group"] == "Nữ"
    assert data["sample_reference"] == 10
    assert data["sample_focal"] == 10
    assert data["total_eval_sample"] == 20
    assert data["overall_verdict"] == "ĐẠT_CHUẨN_BẤT_BIẾN_ĐO_LƯỜNG"
    assert len(data["items"]) == 3
    for it in data["items"]:
        assert it["ets_class"] == "A"
