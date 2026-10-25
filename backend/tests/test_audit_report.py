import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_survey_audit_report_and_anonymization(client: TestClient):
    # 1. Tạo khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Khảo sát Kiểm định Báo cáo & Tuân thủ Pháp lý",
        "description": "Thử nghiệm báo cáo kiểm định độc lập và Nghị định 356/2025/NĐ-CP"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]

    # Thêm câu hỏi qua update survey
    q_id = "q_pii_name"
    up_res = client.put(f"/api/surveys/{survey_id}", json={
        "questions": [{
            "id": q_id,
            "question_type": "short_text",
            "title": "Họ tên người trả lời (PII)",
            "order_index": 0,
            "is_required": True,
            "options": [],
            "logic_rules": []
        }]
    })
    assert up_res.status_code == 200

    # Xuất bản khảo sát
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200
    slug = pub_res.json()["public_slug"]

    # Nộp phản hồi qua link công khai
    sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": "2026-10-23T08:00:00Z",
        "submitted_at": "2026-10-23T08:00:30Z",
        "duration_seconds": 30.0,
        "client_metadata": {"ip": "192.168.1.100", "user_agent": "Mozilla/5.0"},
        "answers": {q_id: "Nguyễn Văn A"}
    })
    assert sub_res.status_code == 201

    # 2. Lấy Báo cáo Kiểm định Chất lượng Dữ liệu Độc lập
    rep_res = client.get(f"/api/surveys/{survey_id}/audit-report")
    assert rep_res.status_code == 200
    rep_data = rep_res.json()

    assert rep_data["survey_id"] == survey_id
    assert rep_data["total_collected"] == 1
    assert rep_data["source_breakdown"]["online_form"] == 1
    assert rep_data["data_trust_index"] == 100.0
    assert "DT-AUDIT-" in rep_data["audit_hash"]
    assert "is_ledger_valid" in rep_data
    assert rep_data["is_ledger_valid"] is True
    assert "ledger_head_hash" in rep_data
    assert "principles_applied" in rep_data["compliance_statement"]
    assert len(rep_data["compliance_statement"]["principles_applied"]) == 4
    assert len(rep_data["methodology_citations"]) >= 5

    # 3. Kiểm tra tính năng Quyền Ẩn danh hóa / Xóa dữ liệu PII (Decree 356/2025/NĐ-CP)
    anon_res = client.post(f"/api/surveys/{survey_id}/privacy/anonymize", json={
        "anonymize_client_metadata": True,
        "mask_text_answers": True,
        "operator_notes": "Nghiệm thu khảo sát hoàn tất - Thực hiện ẩn danh theo quy định"
    })
    assert anon_res.status_code == 200
    anon_data = anon_res.json()
    assert anon_data["anonymized_responses_count"] == 1
    assert anon_data["audit_log_id"] != ""

    # Kiểm tra lại phản hồi chi tiết đã được ẩn danh
    detail_res = client.get(f"/api/surveys/{survey_id}/responses")
    assert detail_res.status_code == 200
    resp_list = detail_res.json()
    assert len(resp_list) == 1
    resp_id = resp_list[0]["id"]

    full_res = client.get(f"/api/surveys/{survey_id}/responses/{resp_id}")
    assert full_res.status_code == 200
    full_data = full_res.json()
    assert full_data["answers"][q_id] == "[ANONYMIZED_PII]"

    # 4. Kiểm tra trang Chứng Thư Thẩm Định A4 In Ấn / PDF
    cert_res = client.get(f"/api/surveys/{survey_id}/audit-report/printable-certificate")
    assert cert_res.status_code == 200
    assert "text/html" in cert_res.headers["content-type"]
    assert "Chứng Thư Kiểm Định Chất Lượng Dữ Liệu" in cert_res.text
    assert "DT-CERT-" in cert_res.text
    assert "AAPOR (2003)" in cert_res.text
    assert "356/2025/NĐ-CP" in cert_res.text
    assert "Blockchain-Lightweight Ledger" in cert_res.text

def test_simulate_red_team_attack_endpoint(client: TestClient):
    """
    Kiểm tra API Giả lập Tấn công Đối kháng Trực nghiệm (Red-Team Simulation)
    Xác minh cả 6 kịch bản tấn công đều được hệ thống ngăn chặn với điểm số 100%.
    """
    create_res = client.post("/api/surveys", json={
        "title": "Khảo sát Thử Thách An Ninh Red-Team",
        "description": "Thử nghiệm giả lập tấn công đối kháng trực tiếp"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]

    sim_res = client.post(f"/api/surveys/{survey_id}/audit/simulate-attack")
    assert sim_res.status_code == 200
    data = sim_res.json()

    assert data["survey_id"] == survey_id
    assert data["overall_status"] == "SECURE"
    assert data["compliance_score"] == 100.0
    assert data["attacks_tested"] == 6
    assert data["attacks_deflected"] == 6
    assert len(data["attack_results"]) == 6

    # Xác minh từng kịch bản
    attack_ids = [a["id"] for a in data["attack_results"]]
    assert "ATK_SQLI" in attack_ids
    assert "ATK_XSS" in attack_ids
    assert "ATK_CWE1236" in attack_ids
    assert "ATK_LEDGER_TAMPER" in attack_ids
    assert "ATK_SPEEDER" in attack_ids
    assert "ATK_STRAIGHTLINER" in attack_ids

    for atk in data["attack_results"]:
        assert atk["result"] == "DEFENDED"
        assert atk["latency_ms"] >= 0
        assert atk["defense_layer"] != ""

