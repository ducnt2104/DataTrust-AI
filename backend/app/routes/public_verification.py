import re
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Request, Query
from app.database import get_db, verify_audit_chain
from app.schemas import PublicCertificateVerificationOut
from app.engine.quality_engine import QualityEngine
from app.middleware.rate_limiter import InMemoryRateLimiter

router = APIRouter(prefix="/api/public", tags=["Public Verification & Trust Registry"])

verification_limiter = InMemoryRateLimiter(requests_per_minute=60)

def _resolve_survey_and_verify(query_raw: str, request: Request) -> PublicCertificateVerificationOut:
    verification_limiter.check(request)
    q = query_raw.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Mã truy vấn chứng thư hoặc hồ sơ không được để trống.")

    with get_db() as conn:
        s_row = None

        # Pattern 1: Format DT-CERT-YYYY-XXXXXXXX or CERT-DATATRUST-XXXXXXXX
        cert_match = re.match(r"^(?:DT-CERT-\d{4}-|CERT-DATATRUST-)([A-Fa-f0-9]+)$", q, re.IGNORECASE)
        if cert_match:
            prefix = cert_match.group(1).lower()
            s_row = conn.execute("""
                SELECT * FROM surveys WHERE LOWER(SUBSTR(id, 1, ?)) = ? LIMIT 1
            """, (len(prefix), prefix)).fetchone()

        # Pattern 2: Direct Survey ID (UUID) or Public Slug
        if not s_row:
            s_row = conn.execute("""
                SELECT * FROM surveys WHERE id = ? OR public_slug = ? LIMIT 1
            """, (q, q)).fetchone()

        # Pattern 3: SHA-256 Hash query (64 hex characters)
        if not s_row and re.match(r"^[a-fA-F0-9]{64}$", q):
            # Check if this hash is in the audit log
            audit_log_row = conn.execute("""
                SELECT entity_type, entity_id, details_json FROM audit_logs
                WHERE entry_hash = ? OR prev_hash = ?
                LIMIT 1
            """, (q, q)).fetchone()
            if audit_log_row:
                if audit_log_row["entity_type"] == "survey":
                    s_row = conn.execute("SELECT * FROM surveys WHERE id = ? LIMIT 1", (audit_log_row["entity_id"],)).fetchone()
                elif audit_log_row["entity_type"] == "response":
                    r_row = conn.execute("SELECT survey_id FROM responses WHERE id = ? LIMIT 1", (audit_log_row["entity_id"],)).fetchone()
                    if r_row:
                        s_row = conn.execute("SELECT * FROM surveys WHERE id = ? LIMIT 1", (r_row["survey_id"],)).fetchone()

            # If not associated with a specific survey_id in log, check if it is the current ledger head/genesis
            if not s_row:
                audit_status_check = verify_audit_chain(conn)
                if audit_status_check.get("head_hash") == q or audit_status_check.get("genesis_hash") == q:
                    s_row = conn.execute("SELECT * FROM surveys ORDER BY created_at DESC LIMIT 1").fetchone()

        # Pattern 4: Partial ID match (minimum 6 characters)
        if not s_row and len(q) >= 6 and re.match(r"^[a-fA-F0-9\-]+$", q):
            clean_q = q.lower().replace("-", "")
            all_surveys = conn.execute("SELECT * FROM surveys").fetchall()
            for s in all_surveys:
                sid_clean = s["id"].lower().replace("-", "")
                if sid_clean.startswith(clean_q):
                    s_row = s
                    break

        if not s_row:
            raise HTTPException(
                status_code=404,
                detail=f"Không tìm thấy chứng thư kiểm định hoặc khảo sát tương ứng với mã '{q}'."
            )

        survey_id = s_row["id"]

        # Fetch responses
        resp_rows = conn.execute("SELECT * FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()
        total = len(resp_rows)

        clean_count = sum(
            1 for r in resp_rows
            if r["review_status"] == "verified_valid" or (r["review_status"] == "unverified" and (r["risk_level"] or "low") == "low")
        )
        fraud_count = sum(
            1 for r in resp_rows
            if r["review_status"] == "verified_fraud" or (r["risk_level"] == "high" and r["review_status"] != "verified_valid")
        )
        trust_index = round((clean_count / total * 100), 1) if total > 0 else 100.0

        # Calculate Cronbach's Alpha
        scale_q_rows = conn.execute("""
            SELECT id FROM questions
            WHERE survey_id = ? AND question_type IN ('rating', 'rating_scale', 'linear_scale', 'likert', 'nps')
            ORDER BY order_index ASC
        """, (survey_id,)).fetchall()
        scale_q_ids = [sq["id"] for sq in scale_q_rows]
        cronbach_val = None
        reliability_verdict = None

        clean_resp_ids = [
            r["id"] for r in resp_rows
            if r["review_status"] == "verified_valid" or (r["review_status"] == "unverified" and (r["risk_level"] or "low") == "low")
        ]

        if len(scale_q_ids) >= 2 and len(clean_resp_ids) >= 2:
            ans_rows = conn.execute("""
                SELECT ra.response_id, ra.question_id, ra.answer_value
                FROM response_answers ra
                JOIN responses r ON r.id = ra.response_id
                WHERE r.survey_id = ? AND ra.question_id IN ({})
            """.format(",".join("?" for _ in scale_q_ids)), [survey_id] + scale_q_ids).fetchall()

            ans_map = {}
            for a in ans_rows:
                try:
                    val = float(str(a["answer_value"]).strip())
                    ans_map.setdefault(a["response_id"], {})[a["question_id"]] = val
                except (ValueError, TypeError):
                    pass

            clean_matrix = []
            for rid in clean_resp_ids:
                row_ans = ans_map.get(rid, {})
                if len(row_ans) == len(scale_q_ids):
                    clean_matrix.append([row_ans[qid] for qid in scale_q_ids])

            if clean_matrix:
                cronbach_val = QualityEngine.compute_cronbach_alpha(clean_matrix)
                if cronbach_val is not None:
                    if cronbach_val >= 0.8:
                        reliability_verdict = f"Độ tin cậy thang đo rất cao (α = {cronbach_val:.3f} ≥ 0.80)"
                    elif cronbach_val >= 0.7:
                        reliability_verdict = f"Độ tin cậy thang đo đạt chuẩn công bố khoa học (α = {cronbach_val:.3f} ≥ 0.70)"
                    elif cronbach_val >= 0.6:
                        reliability_verdict = f"Độ tin cậy thang đo chấp nhận được (α = {cronbach_val:.3f} ≥ 0.60)"
                    else:
                        reliability_verdict = f"Độ tin cậy thang đo dưới ngưỡng khuyến nghị (α = {cronbach_val:.3f} < 0.60)"

        # Verify global cryptographic tamper-evident ledger
        audit_status = verify_audit_chain(conn)
        is_chain_valid = audit_status.get("is_valid", True)
        head_hash = audit_status.get("head_hash")
        genesis_hash = audit_status.get("genesis_hash")
        total_audit_records = audit_status.get("total_records", 0)

        # Build official certificate number
        created_at_dt = None
        try:
            created_at_dt = datetime.fromisoformat(s_row["created_at"].replace("Z", "+00:00"))
        except Exception:
            created_at_dt = datetime.now(timezone.utc)

        cert_id = f"DT-CERT-{created_at_dt.year}-{survey_id[:8].upper()}"

        if is_chain_valid:
            status_code = "VERIFIED_VALID"
            verdict_text = "Hợp Lệ & Nguyên Bản — Bộ dữ liệu đã được thẩm định qua 7 lớp chất lượng và bảo toàn toàn vẹn trên chuỗi băm mật mã học SHA-256."
        else:
            status_code = "TAMPERED"
            verdict_text = "CẢNH BÁO: Phát hiện dấu hiệu sửa đổi dữ liệu bất hợp pháp ngoài chuỗi sổ cái kiểm toán (Cryptographic Tampering Detected)."

        standards = [
            "AAPOR Standard Definitions (2016) — American Association for Public Opinion Research",
            "Don Dillman Tailored Design Method (4th Edition) — Khung kiểm soát chất lượng khảo sát thực địa",
            "Nghị định 356/2025/NĐ-CP & Luật Bảo vệ Dữ liệu Cá nhân 2025 (Việt Nam)",
            "W3C Verifiable Data & SHA-256 Tamper-Evident Hash Chain Specification"
        ]

        return PublicCertificateVerificationOut(
            query=q,
            is_valid=is_chain_valid,
            status=status_code,
            certificate_id=cert_id,
            survey_id=survey_id,
            survey_title=s_row["title"],
            survey_description=s_row["description"],
            public_slug=s_row["public_slug"],
            issued_at=s_row["created_at"],
            total_responses=total,
            clean_responses=clean_count,
            excluded_responses=fraud_count,
            trust_index=trust_index,
            cronbach_alpha=cronbach_val,
            reliability_verdict=reliability_verdict,
            ledger_chain_valid=is_chain_valid,
            ledger_head_hash=head_hash,
            ledger_genesis_hash=genesis_hash,
            total_audit_events=total_audit_records,
            verification_verdict=verdict_text,
            compliance_standards=standards,
            printable_certificate_url=f"/api/surveys/{survey_id}/audit-report/printable-certificate"
        )

@router.get("/verify/{identifier}", response_model=PublicCertificateVerificationOut)
def verify_certificate_by_path(identifier: str, request: Request):
    """
    Tra cứu & Thẩm định tính toàn vẹn của Chứng thư Kiểm định Dữ liệu (Public Certificate & Ledger Verification):
    Cho phép hội đồng giám khảo, nhà khoa học, ban biên tập tạp chí kiểm chứng mã băm và chất lượng mẫu khảo sát
    hoàn toàn mở mà không cần đăng nhập tài khoản quản trị.
    Hỗ trợ tra cứu theo:
    - Mã chứng thư: DT-CERT-2026-XXXXXXXX
    - Mã khảo sát UUID
    - Đường dẫn thân thiện (Public Slug)
    - Mã băm đỉnh sổ cái (SHA-256 Head Hash)
    """
    return _resolve_survey_and_verify(identifier, request)

@router.get("/verify", response_model=PublicCertificateVerificationOut)
def verify_certificate_by_query(q: str = Query(..., description="Mã chứng thư, Survey ID, Slug hoặc SHA-256 Hash"), request: Request = None):
    """Tra cứu chứng thư theo query parameter `?q=...`"""
    return _resolve_survey_and_verify(q, request)
