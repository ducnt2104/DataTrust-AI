import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)

def test_quota_management_and_submission_overflow():
    # 1. Tạo khảo sát thử nghiệm
    survey_payload = {
        "title": "Khảo sát Nghiên cứu Hạn ngạch Mẫu",
        "description": "Kiểm thử Quota & Raking"
    }
    res = client.post("/api/surveys", json=survey_payload)
    assert res.status_code == 201
    survey = res.json()
    survey_id = survey["id"]

    # 2. Thêm 2 câu hỏi nhân khẩu học: Giới tính & Vùng miền
    q_gender_id = f"q_gender_{uuid.uuid4().hex[:6]}"
    q_region_id = f"q_region_{uuid.uuid4().hex[:6]}"

    with get_db() as conn:
        conn.execute("""
            INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at)
            VALUES (?, ?, 1, 'single_choice', 'Giới tính của bạn', 1, ?, '2026-10-24T00:00:00Z')
        """, (q_gender_id, survey_id, '["Nam", "Nữ"]'))
        conn.execute("""
            INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at)
            VALUES (?, ?, 2, 'single_choice', 'Khu vực sinh sống', 1, ?, '2026-10-24T00:00:00Z')
        """, (q_region_id, survey_id, '["Miền Bắc", "Miền Trung", "Miền Nam"]'))

    # Xuất bản khảo sát
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200
    public_slug = pub_res.json()["public_slug"]

    # 3. Cập nhật quy tắc hạn ngạch mẫu
    quota_payload = {
        "quota_rules": [
            {
                "id": "quota_male",
                "name": "Nam giới tối đa 2",
                "question_id": q_gender_id,
                "target_value": "Nam",
                "max_target": 2,
                "action": "flag_overflow"
            },
            {
                "id": "quota_female_strict",
                "name": "Nữ giới tối đa 1 (Screen out)",
                "question_id": q_gender_id,
                "target_value": "Nữ",
                "max_target": 1,
                "action": "screen_out"
            }
        ]
    }
    put_res = client.put(f"/api/surveys/{survey_id}/analytics/quotas", json=quota_payload)
    assert put_res.status_code == 200
    assert "Đã cập nhật 2 quy tắc" in put_res.json()["message"]

    # 4. Kiểm tra tiến độ hạn ngạch khi chưa có dữ liệu
    get_quotas = client.get(f"/api/surveys/{survey_id}/analytics/quotas")
    assert get_quotas.status_code == 200
    q_data = get_quotas.json()
    assert q_data["total_quota_cells"] == 2
    assert q_data["filled_cells"] == 0
    assert q_data["overall_achieved_sum"] == 0

    # 5. Gửi phản hồi 1 (Nam)
    sub1 = {
        "started_at": "2026-10-24T00:00:00Z",
        "submitted_at": "2026-10-24T00:01:00Z",
        "answers": {q_gender_id: "Nam", q_region_id: "Miền Bắc"},
        "client_metadata": {"device": "desktop_1"}
    }
    r1 = client.post(f"/api/public/surveys/{public_slug}/submit", json=sub1)
    assert r1.status_code == 201
    assert r1.json()["status"] == "recorded"

    # 6. Gửi phản hồi 2 (Nữ) - Đạt mốc 1/1
    sub2 = {
        "started_at": "2026-10-24T00:00:00Z",
        "submitted_at": "2026-10-24T00:01:10Z",
        "answers": {q_gender_id: "Nữ", q_region_id: "Miền Trung"},
        "client_metadata": {"device": "desktop_2"}
    }
    r2 = client.post(f"/api/public/surveys/{public_slug}/submit", json=sub2)
    assert r2.status_code == 201

    # 7. Gửi phản hồi 3 (Nữ) - Phải bị SCREEN OUT vì Nữ đã đủ (1/1) và action là screen_out!
    sub3 = {
        "started_at": "2026-10-24T00:00:00Z",
        "submitted_at": "2026-10-24T00:01:20Z",
        "answers": {q_gender_id: "Nữ", q_region_id: "Miền Nam"},
        "client_metadata": {"device": "desktop_3"}
    }
    r3 = client.post(f"/api/public/surveys/{public_slug}/submit", json=sub3)
    assert r3.status_code == 201
    r3_data = r3.json()
    assert r3_data["status"] == "screen_out"
    assert "Hạn ngạch khảo sát cho nhóm nhân khẩu học này đã đủ" in r3_data["message"]

    # 8. Kiểm tra tiến độ hạn ngạch sau khi thu thập
    get_quotas_after = client.get(f"/api/surveys/{survey_id}/analytics/quotas")
    assert get_quotas_after.status_code == 200
    cells = get_quotas_after.json()["cells"]
    female_cell = next(c for c in cells if c["cell_id"] == "quota_female_strict")
    assert female_cell["achieved_count"] == 1
    assert female_cell["status"] == "filled"

def test_demographic_raking_api_and_csv_export():
    # 1. Tạo khảo sát và nạp mẫu dữ liệu
    res = client.post("/api/surveys", json={"title": "Raking Test Survey"})
    survey_id = res.json()["id"]

    q_gen = f"q_g_{uuid.uuid4().hex[:6]}"
    q_reg = f"q_r_{uuid.uuid4().hex[:6]}"

    with get_db() as conn:
        conn.execute("INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at) VALUES (?, ?, 1, 'single_choice', 'Giới tính', 1, '[]', '2026-10-24T00:00:00Z')", (q_gen, survey_id))
        conn.execute("INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at) VALUES (?, ?, 2, 'single_choice', 'Khu vực', 1, '[]', '2026-10-24T00:00:00Z')", (q_reg, survey_id))

        # Thêm 10 phản hồi (7 Nam, 3 Nữ)
        for i in range(7):
            rid = str(uuid.uuid4())
            conn.execute("INSERT INTO responses (id, survey_id, started_at, submitted_at, duration_seconds, risk_score, risk_level, review_status) VALUES (?, ?, '2026-10-24T00:00:00Z', '2026-10-24T00:01:00Z', 60.0, 0.0, 'low', 'verified_valid')", (rid, survey_id))
            conn.execute("INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at) VALUES (?, ?, ?, '\"Nam\"', '2026-10-24T00:00:00Z')", (str(uuid.uuid4()), rid, q_gen))
            conn.execute("INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at) VALUES (?, ?, ?, '\"Bắc\"', '2026-10-24T00:00:00Z')", (str(uuid.uuid4()), rid, q_reg))

        for i in range(3):
            rid = str(uuid.uuid4())
            conn.execute("INSERT INTO responses (id, survey_id, started_at, submitted_at, duration_seconds, risk_score, risk_level, review_status) VALUES (?, ?, '2026-10-24T00:00:00Z', '2026-10-24T00:01:05Z', 65.0, 0.0, 'low', 'verified_valid')", (rid, survey_id))
            conn.execute("INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at) VALUES (?, ?, ?, '\"Nữ\"', '2026-10-24T00:00:00Z')", (str(uuid.uuid4()), rid, q_gen))
            conn.execute("INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at) VALUES (?, ?, ?, '\"Bắc\"', '2026-10-24T00:00:00Z')", (str(uuid.uuid4()), rid, q_reg))

    # 2. Gọi API POST /api/surveys/{survey_id}/analytics/raking
    raking_payload = {
        "target_margins": {
            q_gen: {"Nam": 0.50, "Nữ": 0.50}
        },
        "scope": "verified_clean"
    }

    rake_res = client.post(f"/api/surveys/{survey_id}/analytics/raking", json=raking_payload)
    assert rake_res.status_code == 200
    rake_data = rake_res.json()
    assert rake_data["converged"] is True
    assert rake_data["sample_size"] == 10
    assert rake_data["design_effect_deff"] >= 1.0
    assert len(rake_data["marginal_comparisons"]) == 1

    comp = rake_data["marginal_comparisons"][0]
    male_cat = next(c for c in comp["categories"] if c["category"] == "Nam")
    assert male_cat["unweighted_pct"] == 70.0
    assert abs(male_cat["weighted_pct"] - 50.0) < 1.0

    # 3. Xuất tệp CSV có trọng số
    csv_res = client.post(f"/api/surveys/{survey_id}/analytics/raking/export-csv", json=raking_payload)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    csv_text = csv_res.text
    assert "statistical_weight_wi" in csv_text
    assert "Nam" in csv_text
    assert "Nữ" in csv_text
