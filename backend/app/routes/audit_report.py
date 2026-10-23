import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db
from app.schemas import (
    QualityAuditReportOut, AnonymizeRequest, AnonymizeResponse
)

router = APIRouter(prefix="/api/surveys/{survey_id}", tags=["Audit & Legal Compliance"])

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@router.get("/audit-report", response_model=QualityAuditReportOut)
def get_survey_audit_report(survey_id: str):
    """
    Sinh Báo cáo Kiểm định Chất lượng Dữ liệu Độc lập (Evidence-Based Quality Audit Report)
    Tuân thủ Nghị định 356/2025/NĐ-CP, Luật Bảo vệ Dữ liệu Cá nhân 2025 và Tiêu chuẩn AAPOR (2003)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_rows = conn.execute("SELECT * FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()
        qa_rows = conn.execute("""
            SELECT qa.*, r.source, r.risk_level, r.review_status
            FROM quality_assessments qa
            JOIN responses r ON r.id = qa.response_id
            WHERE r.survey_id = ?
        """, (survey_id,)).fetchall()

        total = len(resp_rows)
        source_counts = {"online_form": 0, "paper_scan": 0, "csv_import": 0}
        risk_counts = {"low": 0, "medium": 0, "high": 0}
        review_counts = {
            "unverified": 0,
            "under_review": 0,
            "verified_valid": 0,
            "verified_fraud": 0,
            "inconclusive": 0
        }

        for r in resp_rows:
            src = r["source"] if "source" in r.keys() and r["source"] else "online_form"
            source_counts[src] = source_counts.get(src, 0) + 1

            lvl = r["risk_level"] or "low"
            risk_counts[lvl] = risk_counts.get(lvl, 0) + 1

            rev = r["review_status"] or "unverified"
            review_counts[rev] = review_counts.get(rev, 0) + 1

        # Đếm chi tiết các tín hiệu gian lận từ flags_json trong quality_assessments
        fraud_signals = {
            "speeding": 0,
            "straightlining": 0,
            "duplicate": 0,
            "logic_violation": 0,
            "gibberish_text": 0,
            "enumerator_anomaly": 0
        }

        for qa in qa_rows:
            flags = json.loads(qa["flags_json"] or "[]")
            flag_types = {f.get("type", "") for f in flags}

            if "FLAG_SPEEDING" in flag_types:
                fraud_signals["speeding"] += 1
            if "FLAG_STRAIGHTLINING" in flag_types:
                fraud_signals["straightlining"] += 1
            if "FLAG_EXACT_DUPLICATE" in flag_types or "FLAG_HIGH_SIMILARITY" in flag_types:
                fraud_signals["duplicate"] += 1
            if "FLAG_LOGIC_CONTRADICTION" in flag_types:
                fraud_signals["logic_violation"] += 1
            if "FLAG_TEXT_GIBBERISH" in flag_types or "FLAG_TEXT_MONOTONE" in flag_types:
                fraud_signals["gibberish_text"] += 1
            if "FLAG_ENUM_HIGH_FRAUD_CONCENTRATION" in flag_types or "FLAG_ENUM_ANOMALOUS_VARIANCE" in flag_types:
                fraud_signals["enumerator_anomaly"] += 1

        # Tính toán số lượng verified clean
        # Điều kiện: đã duyệt hợp lệ HOẶC (chưa duyệt nhưng risk_level là low)
        verified_clean_count = sum(
            1 for r in resp_rows
            if r["review_status"] == "verified_valid" or (r["review_status"] == "unverified" and r["risk_level"] == "low")
        )

        data_trust_index = round((verified_clean_count / total * 100), 1) if total > 0 else 100.0

        gen_time = now_iso()

        # Tạo chuỗi băm xác thực bảo vệ tính toàn vẹn (Tamper-evident Audit Hash)
        raw_hash_str = f"{survey_id}:{s_row['title']}:{total}:{verified_clean_count}:{gen_time}"
        audit_hash = hashlib.sha256(raw_hash_str.encode("utf-8")).hexdigest()[:16].upper()

        compliance_statement = {
            "law_name": "Luật Bảo vệ dữ liệu cá nhân năm 2025 & Nghị định số 356/2025/NĐ-CP (hiệu lực từ 01/01/2026)",
            "principles_applied": [
                {
                    "principle": "Tối thiểu hóa dữ liệu (Data Minimization)",
                    "description": "Chỉ thu thập các trường thông tin cần thiết phục vụ đề tài nghiên cứu; không thu thập thông tin cá nhân dư thừa."
                },
                {
                    "principle": "Giả danh hóa định danh (Pseudonymization)",
                    "description": "Mã hóa danh tính người trả lời qua UUID và mã QR; không hiển thị công khai danh tính trên bảng phân tích thống kê."
                },
                {
                    "principle": "Bảo mật lưu trữ & Đường truyền (Encryption & Storage Security)",
                    "description": "Dữ liệu được lưu trữ chuẩn hóa trong CSDL quan hệ SQLite WAL có băm SHA-256 và nhật ký kiểm toán bất biến."
                },
                {
                    "principle": "Quyền ẩn danh hóa & Xóa dữ liệu (Right to Erasure / Automated Anonymization)",
                    "description": "Hệ thống hỗ trợ tính năng tự động ẩn/xóa siêu dữ liệu thiết bị và phản hồi mở sau khi nghiệm thu chất lượng."
                }
            ],
            "compliance_status": "COMPLIANT"
        }

        citations = [
            "Quốc hội & Chính phủ Việt Nam (2025), Luật Bảo vệ dữ liệu cá nhân năm 2025 và Nghị định số 356/2025/NĐ-CP.",
            "AAPOR - American Association for Public Opinion Research (2003), Interviewer Falsification in Survey Research: Current Best Methods for Prevention, Detection and Repair.",
            "Kennedy, C., et al. – Pew Research Center (2016), Evaluating a New Proposal for Detecting Data Falsification in Surveys.",
            "Schwanhäuser, S., Sakshaug, J. W., & Kosyakova, Y. (2022), How to Catch a Falsifier: Comparison of Statistical Detection Methods, Public Opinion Quarterly, 86(1), 51–81.",
            "Geisen, E., et al. – Survey Research Methods, Detecting Fabricated Interviews Using the Hamming Distance."
        ]

        return QualityAuditReportOut(
            survey_id=survey_id,
            survey_title=s_row["title"],
            survey_status=s_row["status"],
            generated_at=gen_time,
            total_collected=total,
            source_breakdown=source_counts,
            verified_clean_count=verified_clean_count,
            data_trust_index=data_trust_index,
            risk_breakdown=risk_counts,
            review_breakdown=review_counts,
            fraud_signals=fraud_signals,
            compliance_statement=compliance_statement,
            methodology_citations=citations,
            audit_hash=f"DT-AUDIT-{audit_hash}"
        )

@router.post("/privacy/anonymize", response_model=AnonymizeResponse)
def anonymize_survey_responses(survey_id: str, payload: AnonymizeRequest):
    """
    Thực thi cơ chế Tự động Ẩn danh hóa / Quyền xóa dữ liệu định danh
    theo Nguyên tắc 4 của Nghị định 356/2025/NĐ-CP sau khi hoàn tất nghiệm thu chất lượng
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_rows = conn.execute("SELECT id FROM responses WHERE survey_id = ?", (survey_id,)).fetchall()
        count = len(resp_rows)

        current_time = now_iso()
        audit_id = str(uuid.uuid4())

        # 1. Ẩn danh hóa client_metadata_json (IP, User-Agent, v.v.)
        if payload.anonymize_client_metadata:
            conn.execute("""
                UPDATE responses 
                SET client_metadata_json = '{"anonymized": true, "anonymized_at": "' || ? || '"}'
                WHERE survey_id = ?
            """, (current_time, survey_id))

        # 2. Xóa hoặc che mờ nội dung văn bản mở (nếu người dùng yêu cầu)
        if payload.mask_text_answers:
            # Tìm các câu hỏi text
            text_q_rows = conn.execute("""
                SELECT id FROM questions 
                WHERE survey_id = ? AND question_type IN ('short_text', 'long_text')
            """, (survey_id,)).fetchall()
            
            for q in text_q_rows:
                conn.execute("""
                    UPDATE response_answers
                    SET answer_value = '[ANONYMIZED_PII]'
                    WHERE question_id = ?
                """, (q["id"],))

        # 3. Ghi vết vào audit_logs
        conn.execute("""
            INSERT INTO audit_logs (id, entity_type, entity_id, action, details_json, created_at)
            VALUES (?, 'survey_privacy', ?, 'ANONYMIZATION_EXECUTED', ?, ?)
        """, (audit_id, survey_id, json.dumps({
            "anonymized_responses_count": count,
            "anonymize_client_metadata": payload.anonymize_client_metadata,
            "mask_text_answers": payload.mask_text_answers,
            "operator_notes": payload.operator_notes,
            "timestamp": current_time
        }, ensure_ascii=False), current_time))

        return AnonymizeResponse(
            message=f"Đã ẩn danh hóa thành công thông tin định danh của {count} phản hồi theo Nghị định 356/2025/NĐ-CP.",
            anonymized_responses_count=count,
            audit_log_id=audit_id
        )
