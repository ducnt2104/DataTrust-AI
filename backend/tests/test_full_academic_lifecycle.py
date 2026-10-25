import pytest
from fastapi.testclient import TestClient

def test_full_academic_research_lifecycle_e2e(client: TestClient):
    """
    KIỂM THỬ ĐẦU-CUỐI TRỌN VẸN VÒNG ĐỜI NGHIÊN CỨU KHOA HỌC (E2E Academic Lifecycle):
    1. Thiết kế khảo sát đa thang đo (Likert, Text, Number, Choice).
    2. Xuất bản và lưu vết lịch sử phiên bản (Schema Evolution).
    3. Thu thập dữ liệu thực địa đa nguồn (Mẫu chuẩn + Kẻ gian lận speeder/straightliner + CSV injection).
    4. Thẩm định qua 7-Layer Quality Engine.
    5. Thực thi Làm sạch dữ liệu tự động (AAPOR / Don Dillman automated cleansing).
    6. Sinh Từ điển dữ liệu & Cú pháp 4-trong-1 (SPSS, Stata, R, JSON).
    7. Cấp Chứng thư Kiểm định Chất lượng A4 (Printable Academic Certificate).
    8. Xác thực toán học Chuỗi băm kiểm toán bất biến (Tamper-Evident SHA-256 Ledger).
    """
    # BƯỚC 1: Khởi tạo khảo sát
    create_res = client.post("/api/surveys", json={
        "title": "Nghiên cứu Thực nghiệm Đánh giá Chất lượng Đào tạo Đại học",
        "description": "Đề tài nghiên cứu khoa học cấp cơ sở năm 2026",
        "instructions": "Vui lòng trả lời trung thực các câu hỏi dưới đây."
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]

    q_name = "q_respondent_name"
    q_faculty = "q_faculty_choice"
    q_res = "q_likert_resources"
    q_mentor = "q_likert_mentorship"
    q_hours = "q_study_hours"

    up_res = client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": q_name,
                "question_type": "short_text",
                "title": "Mã sinh viên hoặc tên viết tắt",
                "order_index": 0,
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "id": q_faculty,
                "question_type": "single_choice",
                "title": "Khoa đào tạo chính",
                "order_index": 1,
                "is_required": True,
                "options": [
                    {"id": "fac_it", "label": "Công nghệ thông tin"},
                    {"id": "fac_econ", "label": "Kinh tế & Quản trị"},
                    {"id": "fac_eng", "label": "Kỹ thuật Công nghệ"}
                ],
                "logic_rules": []
            },
            {
                "id": q_res,
                "question_type": "likert",
                "title": "Mức độ hài lòng với nguồn học liệu và phòng thí nghiệm (1-5)",
                "order_index": 2,
                "is_required": True,
                "options": [
                    {"id": "1", "label": "1 - Hoàn toàn không đồng ý"},
                    {"id": "2", "label": "2 - Không đồng ý"},
                    {"id": "3", "label": "3 - Trung lập"},
                    {"id": "4", "label": "4 - Đồng ý"},
                    {"id": "5", "label": "5 - Hoàn toàn đồng ý"}
                ],
                "logic_rules": []
            },
            {
                "id": q_mentor,
                "question_type": "likert",
                "title": "Mức độ hỗ trợ và hướng dẫn của giảng viên hướng dẫn (1-5)",
                "order_index": 3,
                "is_required": True,
                "options": [
                    {"id": "1", "label": "1 - Hoàn toàn không đồng ý"},
                    {"id": "2", "label": "2 - Không đồng ý"},
                    {"id": "3", "label": "3 - Trung lập"},
                    {"id": "4", "label": "4 - Đồng ý"},
                    {"id": "5", "label": "5 - Hoàn toàn đồng ý"}
                ],
                "logic_rules": []
            },
            {
                "id": q_hours,
                "question_type": "number",
                "title": "Số giờ tự học và nghiên cứu trung bình mỗi tuần",
                "order_index": 4,
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert up_res.status_code == 200

    # BƯỚC 2: Xuất bản và xác nhận lịch sử phiên bản
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200
    slug = pub_res.json()["public_slug"]

    ver_res = client.get(f"/api/surveys/{survey_id}/versions")
    assert ver_res.status_code == 200
    ver_data = ver_res.json()
    assert len(ver_data) >= 1

    # BƯỚC 3: Thu thập dữ liệu thực địa
    # 3.1. Nộp 20 mẫu hợp lệ (duration 25s - 50s, Likert tương quan cao)
    for i in range(20):
        res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": "2026-10-23T08:00:00Z",
            "submitted_at": "2026-10-23T08:00:35Z",
            "duration_seconds": 35.0 + (i % 10),
            "client_metadata": {"ip": f"192.168.1.{10 + i}", "user_agent": "Mozilla/5.0 Chrome"},
            "answers": {
                q_name: f"SV_{i+1:03d}",
                q_faculty: "fac_it" if i % 2 == 0 else "fac_econ",
                q_res: str(4 if i % 3 != 0 else 5),
                q_mentor: str(4 if i % 3 != 0 else 5),
                q_hours: str(15 + (i * 2))
            }
        })
        assert res.status_code == 201

    # 3.2. Nộp 2 mẫu speeders gian lận thời gian (< 5 giây)
    for i in range(2):
        s_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": "2026-10-23T08:10:00Z",
            "submitted_at": "2026-10-23T08:10:03Z",
            "duration_seconds": 3.0,
            "answers": {
                q_name: f"SPEEDER_{i}",
                q_faculty: "fac_it",
                q_res: "1",
                q_mentor: "1",
                q_hours: "2"
            }
        })
        assert s_res.status_code == 201

    # 3.3. Nộp 1 mẫu chứa payload độc hại CSV Formula Injection (CWE-1236)
    cwe_res = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": "2026-10-23T08:15:00Z",
        "submitted_at": "2026-10-23T08:15:25Z",
        "duration_seconds": 25.0,
        "answers": {
            q_name: "=cmd|' /C calc'!A0",
            q_faculty: "fac_eng",
            q_res: "3",
            q_mentor: "3",
            q_hours: "10"
        }
    })
    assert cwe_res.status_code == 201

    # BƯỚC 4: Kiểm tra đánh giá Quality Engine
    resp_list_res = client.get(f"/api/surveys/{survey_id}/responses")
    assert resp_list_res.status_code == 200
    all_responses = resp_list_res.json()
    assert len(all_responses) == 23

    # BƯỚC 5: Kiểm tra và áp dụng Quy trình Làm sạch Dữ liệu Tự động (Cleansing)
    preview_res = client.post(f"/api/surveys/{survey_id}/responses/cleansing/preview", json={
        "exclude_speeders": True,
        "speeder_min_seconds": 10.0,
        "exclude_straightlining": True,
        "straightlining_threshold": 0.85,
        "exclude_logic_contradictions": True
    })
    assert preview_res.status_code == 200
    p_data = preview_res.json()
    assert p_data["total_responses"] == 23
    assert p_data["flagged_speeders"] >= 2  # Phải phát hiện 2 speeders

    # Áp dụng làm sạch
    apply_res = client.post(f"/api/surveys/{survey_id}/responses/cleansing/apply", json={
        "exclude_speeders": True,
        "speeder_min_seconds": 10.0,
        "exclude_straightlining": True,
        "straightlining_threshold": 0.85,
        "exclude_logic_contradictions": True
    })
    assert apply_res.status_code == 200
    apply_data = apply_res.json()
    assert apply_data["success"] is True
    assert apply_data["rejected_count"] >= 2
    assert apply_data["verified_clean_count"] >= 20
    assert apply_data["audit_log_id"] != ""

    # BƯỚC 6: Kiểm tra Từ điển Dữ liệu & Cú pháp 4-trong-1
    # 6.1. JSON Codebook
    cb_res = client.get(f"/api/surveys/{survey_id}/codebook?format=json")
    assert cb_res.status_code == 200
    cb_data = cb_res.json()
    assert cb_data["total_variables"] == 5
    assert "spss_syntax" in cb_data
    assert "r_script" in cb_data
    assert "stata_syntax" in cb_data

    # 6.2. SPSS
    spss_res = client.get(f"/api/surveys/{survey_id}/codebook?format=spss")
    assert spss_res.status_code == 200
    assert "VARIABLE LABELS" in spss_res.text
    assert "MISSING VALUES ALL (999)." in spss_res.text

    # 6.3. Stata
    stata_res = client.get(f"/api/surveys/{survey_id}/codebook?format=stata")
    assert stata_res.status_code == 200
    assert "capture label variable" in stata_res.text
    assert "capture label define" in stata_res.text

    # 6.4. R
    r_res = client.get(f"/api/surveys/{survey_id}/codebook?format=r")
    assert r_res.status_code == 200
    assert "var_labels <- c" in r_res.text

    # BƯỚC 7: Kiểm tra Chứng thư Kiểm định Chất lượng A4 (Printable Certificate)
    cert_res = client.get(f"/api/surveys/{survey_id}/audit-report/printable-certificate")
    assert cert_res.status_code == 200
    assert "text/html" in cert_res.headers["content-type"]
    assert "DT-CERT-" in cert_res.text
    assert "Chứng Thư Kiểm Định Chất Lượng Dữ Liệu" in cert_res.text
    assert "AAPOR (2003)" in cert_res.text
    assert "356/2025/NĐ-CP" in cert_res.text
    assert "Blockchain-Lightweight Ledger" in cert_res.text

    # BƯỚC 8: Xác thực Chuỗi Băm Kiểm toán Bất biến (Tamper-Evident SHA-256)
    trail_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert trail_res.status_code == 200
    trail_data = trail_res.json()
    assert trail_data["is_chain_valid"] is True
    assert trail_data["chain_status"] == "VALID"
    assert trail_data["tampered_at_index"] is None
    assert trail_data["head_hash"] is not None
    assert len(trail_data["events"]) >= 1
