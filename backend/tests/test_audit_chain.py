import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, record_audit_log, verify_audit_chain

client = TestClient(app)

def test_audit_hash_chain_creation_and_verification():
    """Kiểm tra chuỗi băm kiểm toán được khởi tạo liên tục và hợp lệ toán học"""
    # 1. Tạo một khảo sát mới
    res_create = client.post("/api/surveys", json={
        "title": "Khảo sát Kiểm định Tính Toàn vẹn Dữ liệu",
        "description": "Thử nghiệm chuỗi băm bất biến SHA-256"
    })
    assert res_create.status_code == 201
    survey_id = res_create.json()["id"]

    # 2. Thêm câu hỏi vào khảo sát
    res_update = client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q1",
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Mức độ tin cậy của chuỗi kiểm toán?",
                "is_required": True,
                "options": [{"id": "opt1", "text": "Rất cao"}]
            }
        ]
    })
    assert res_update.status_code == 200

    # 3. Xuất bản khảo sát
    res_pub = client.post(f"/api/surveys/{survey_id}/publish")
    assert res_pub.status_code == 200

    # 4. Gửi một phản hồi công khai
    slug = res_pub.json()["public_slug"]
    now_ts = "2026-10-23T20:00:00Z"
    now_ts_end = "2026-10-23T20:01:00Z"
    res_submit = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": now_ts,
        "submitted_at": now_ts_end,
        "answers": {"q1": "opt1"},
        "client_metadata": {"device": "desktop"},
        "source": "online_form"
    })
    assert res_submit.status_code == 201
    resp_id = res_submit.json()["response_id"]

    # 5. Duyệt phản hồi (Review Decision)
    res_review = client.patch(f"/api/surveys/{survey_id}/responses/{resp_id}/review", json={
        "review_status": "verified_valid",
        "review_notes": "Đã đối chiếu thông tin thực địa hợp lệ."
    })
    assert res_review.status_code == 200

    # 6. Thực thi ẩn danh hóa PII
    res_anon = client.post(f"/api/surveys/{survey_id}/privacy/anonymize", json={
        "anonymize_client_metadata": True,
        "mask_text_answers": False,
        "operator_notes": "Kiểm thử chuỗi băm"
    })
    assert res_anon.status_code == 200

    # 7. Kiểm tra API Audit Trail
    res_trail = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert res_trail.status_code == 200
    trail_data = res_trail.json()

    assert trail_data["is_chain_valid"] is True
    assert trail_data["chain_status"] == "VALID"
    assert trail_data["total_records"] >= 4
    assert trail_data["genesis_hash"] is not None
    assert trail_data["head_hash"] is not None

    events = trail_data["events"]
    assert len(events) >= 3
    for ev in events:
        assert ev["is_valid_hash"] is True
        assert len(ev["entry_hash"]) == 64
        assert len(ev["prev_hash"]) == 64

def test_audit_hash_chain_tamper_detection():
    """Kiểm tra khả năng phát hiện giả mạo dữ liệu tức thì khi có can thiệp trực tiếp vào CSDL"""
    # Tạo khảo sát để sinh dữ liệu kiểm toán
    res = client.post("/api/surveys", json={
        "title": "Khảo sát Kiểm thử Giả mạo",
        "description": "Thử nghiệm phát hiện tampering"
    })
    assert res.status_code == 201
    survey_id = res.json()["id"]

    with get_db() as conn:
        # Lấy bản ghi kiểm toán vừa tạo
        last_row = conn.execute("SELECT id, action, details_json FROM audit_logs ORDER BY rowid DESC LIMIT 1").fetchone()
        assert last_row is not None
        target_id = last_row["id"]
        original_details = last_row["details_json"]

        # Can thiệp sửa đổi trái phép nội dung details_json trong CSDL
        conn.execute(
            "UPDATE audit_logs SET details_json = ? WHERE id = ?",
            ('{"malicious_tamper": true, "original_hacked": true}', target_id)
        )

    # Chạy kiểm chứng toàn vẹn: Hệ thống PHẢI phát hiện gian lận
    with get_db() as conn:
        verify_result = verify_audit_chain(conn)
        assert verify_result["is_valid"] is False
        assert verify_result["error_type"] == "SIGNATURE_PAYLOAD_TAMPERED"
        assert verify_result["tampered_record_id"] == target_id

    # Khôi phục lại dữ liệu ban đầu
    with get_db() as conn:
        conn.execute("UPDATE audit_logs SET details_json = ? WHERE id = ?", (original_details, target_id))
        restored_verify = verify_audit_chain(conn)
        assert restored_verify["is_valid"] is True
