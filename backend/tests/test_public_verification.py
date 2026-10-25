import uuid
import pytest
from fastapi.testclient import TestClient

def _create_sample_survey(client: TestClient) -> str:
    res = client.post("/api/surveys", json={
        "title": "Khảo sát Kiểm định Công khai DataTrust",
        "description": "Dùng để kiểm thử tính năng tra cứu chứng thư công khai"
    })
    assert res.status_code == 201
    survey_id = res.json()["id"]

    q1_id = f"q1_{uuid.uuid4().hex[:6]}"
    q2_id = f"q2_{uuid.uuid4().hex[:6]}"

    # Add questions
    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": q1_id,
                "question_type": "rating",
                "title": "Mức độ tin cậy của dữ liệu khảo sát",
                "order_index": 0,
                "is_required": True,
                "options": [],
                "logic_rules": []
            },
            {
                "id": q2_id,
                "question_type": "rating",
                "title": "Mức độ hài lòng với quy trình kiểm định",
                "order_index": 1,
                "is_required": True,
                "options": [],
                "logic_rules": []
            }
        ]
    })

    # Publish survey
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200
    slug = pub_res.json()["public_slug"]

    # Submit sample response
    client.post(f"/api/public/surveys/{slug}/submit", json={
        "started_at": "2026-10-23T08:00:00Z",
        "submitted_at": "2026-10-23T08:00:30Z",
        "duration_seconds": 30.0,
        "client_metadata": {"ip": "127.0.0.1", "user_agent": "Pytest"},
        "answers": {q1_id: 5, q2_id: 5}
    })

    return survey_id

def test_public_certificate_verification_by_cert_id(client: TestClient):
    survey_id = _create_sample_survey(client)

    # 1. First get the printable certificate to verify QR code and verification block
    res_cert = client.get(f"/api/surveys/{survey_id}/audit-report/printable-certificate")
    assert res_cert.status_code == 200
    assert "Chứng Thư Kiểm Định Chất Lượng Dữ Liệu" in res_cert.text
    assert "Tra Cứu &amp; Xác Thực Toàn Vẹn Mật Mã Trực Tuyến" in res_cert.text or "Tra Cứu & Xác Thực Toàn Vẹn Mật Mã Trực Tuyến" in res_cert.text
    assert "<svg" in res_cert.text  # Embedded SVG QR code

    # Expected certificate id
    cert_no = f"DT-CERT-2026-{survey_id[:8].upper()}"

    # 2. Query public verification by certificate ID
    verify_res = client.get(f"/api/public/verify/{cert_no}")
    assert verify_res.status_code == 200
    data = verify_res.json()

    assert data["status"] == "VERIFIED_VALID"
    assert data["survey_id"] == survey_id
    assert data["certificate_id"] == cert_no
    assert data["ledger_chain_valid"] is True
    assert data["ledger_head_hash"] is not None
    assert "AAPOR Standard Definitions" in " ".join(data["compliance_standards"])
    assert f"/api/surveys/{survey_id}/audit-report/printable-certificate" in data["printable_certificate_url"]

def test_public_certificate_verification_by_survey_id(client: TestClient):
    survey_id = _create_sample_survey(client)
    verify_res = client.get(f"/api/public/verify/{survey_id}")
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert data["survey_id"] == survey_id
    assert data["is_valid"] is True

def test_public_certificate_verification_by_query_param(client: TestClient):
    survey_id = _create_sample_survey(client)
    cert_no = f"DT-CERT-2026-{survey_id[:8].upper()}"
    verify_res = client.get(f"/api/public/verify?q={cert_no}")
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert data["survey_id"] == survey_id

def test_public_certificate_verification_by_head_hash(client: TestClient):
    survey_id = _create_sample_survey(client)
    # Get head hash from audit trail
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    head_hash = audit_res.json().get("head_hash")
    assert head_hash is not None

    # Query with head hash
    verify_res = client.get(f"/api/public/verify/{head_hash}")
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert data["is_valid"] is True

def test_public_certificate_verification_not_found(client: TestClient):
    fake_id = f"DT-CERT-2026-{uuid.uuid4().hex[:8].upper()}"
    res = client.get(f"/api/public/verify/{fake_id}")
    assert res.status_code == 404
    assert "Không tìm thấy chứng thư" in res.json()["detail"]
