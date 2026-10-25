import csv
import io
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Response, Query
from app.database import get_db, record_audit_log
from app.schemas import (
    PaperTemplateLayout, PaperScanResult, PaperIngestPayload
)
from app.engine.omr_engine import OMREngine
from app.engine.quality_engine import QualityEngine
from app.routes.export_import import sanitize_csv_cell

router = APIRouter(prefix="/api/surveys/{survey_id}/paper", tags=["Paper Survey & OMR"])

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@router.get("/template", response_model=Dict[str, Any])
def get_or_create_paper_template(survey_id: str):
    """
    Lấy hoặc khởi tạo mẫu phiếu khảo sát giấy chuẩn hóa kèm tọa độ các ô tích và mốc căn góc.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        t_row = conn.execute("""
            SELECT * FROM paper_templates WHERE survey_id = ? ORDER BY template_version DESC LIMIT 1
        """, (survey_id,)).fetchone()

        q_rows = conn.execute("""
            SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()

        questions = []
        for q in q_rows:
            questions.append({
                "id": q["id"],
                "question_type": q["question_type"],
                "title": q["title"],
                "order_index": q["order_index"],
                "options": json.loads(q["options_json"] or "[]")
            })

        if t_row:
            layout = json.loads(t_row["layout_config_json"])
            return {
                "template_id": t_row["id"],
                "survey_id": survey_id,
                "version": t_row["template_version"],
                "layout": layout
            }

        # Sinh layout mới
        survey_dict = dict(s_row)
        layout = OMREngine.generate_paper_template(survey_dict, questions)
        t_id = str(uuid.uuid4())
        created_at = now_iso()

        conn.execute("""
            INSERT INTO paper_templates (id, survey_id, template_version, layout_config_json, created_at)
            VALUES (?, ?, 1, ?, ?)
        """, (t_id, survey_id, json.dumps(layout, ensure_ascii=False), created_at))

        return {
            "template_id": t_id,
            "survey_id": survey_id,
            "version": 1,
            "layout": layout
        }

@router.get("/printable-html", response_class=Response)
def get_printable_paper_html(
    survey_id: str,
    form_id: Optional[str] = Query(None, description="Mã phiếu cụ thể (hoặc tự động sinh)"),
    enumerator_id: Optional[str] = Query("DTV-01", description="Mã điều tra viên mặc định")
):
    """
    Xuất trang HTML chuẩn A4 in ấn độ nét cao của phiếu khảo sát thực địa:
    - Chứa 4 mốc căn góc màu đen (Fiducial markers) phục vụ OpenCV Perspective Warp.
    - Chứa mã QR nhúng dạng base64 PNG định danh khảo sát và biểu mẫu.
    - Lưới ô tích tròn (OMR bubbles) và các khối câu hỏi định dạng tối ưu in ấn khổ A4.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute("""
            SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()

        questions = []
        for q in q_rows:
            questions.append({
                "id": q["id"],
                "question_type": q["question_type"],
                "title": q["title"],
                "order_index": q["order_index"],
                "options": json.loads(q["options_json"] or "[]")
            })

    survey_dict = dict(s_row)
    html_content = OMREngine.generate_printable_html(
        survey=survey_dict,
        questions=questions,
        form_id=form_id or "",
        enumerator_id=enumerator_id or "DTV-01"
    )
    return Response(content=html_content, media_type="text/html; charset=utf-8")


@router.post("/scan", response_model=PaperScanResult)
async def scan_paper_image(
    survey_id: str,
    file: UploadFile = File(...)
):
    """
    Tải lên ảnh phiếu chụp từ điện thoại, thực hiện kiểm tra độ nét, nắn phối cảnh,
    đọc mã QR, nhận diện ô tích OMR và trả về kết quả số hóa kèm ảnh lớp phủ.
    """
    content = await file.read()
    nparr = np.frombuffer(content, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Không thể giải mã tệp ảnh tải lên. Vui lòng thử lại với định dạng JPG hoặc PNG.")

    # 1. Đánh giá chất lượng ảnh
    quality = OMREngine.assess_image_quality(image)

    # 2. Lấy template layout của khảo sát
    with get_db() as conn:
        t_row = conn.execute("""
            SELECT * FROM paper_templates WHERE survey_id = ? ORDER BY template_version DESC LIMIT 1
        """, (survey_id,)).fetchone()

        if not t_row:
            # Tự động tạo template nếu chưa có
            s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
            if not s_row:
                raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")
            q_rows = conn.execute("SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC", (survey_id,)).fetchall()
            questions = [{
                "id": q["id"], "question_type": q["question_type"], "title": q["title"],
                "order_index": q["order_index"], "options": json.loads(q["options_json"] or "[]")
            } for q in q_rows]
            layout = OMREngine.generate_paper_template(dict(s_row), questions)
            t_id = str(uuid.uuid4())
            conn.execute("""
                INSERT INTO paper_templates (id, survey_id, template_version, layout_config_json, created_at)
                VALUES (?, ?, 1, ?, ?)
            """, (t_id, survey_id, json.dumps(layout, ensure_ascii=False), now_iso()))
        else:
            layout = json.loads(t_row["layout_config_json"])

    # 3. Chuẩn hóa phối cảnh (Perspective Warp) & Tự động xoay đúng chiều (Auto-Orient)
    warped = OMREngine.normalize_perspective(image)
    warped, rot_angle = OMREngine.auto_orient_page(warped)

    # 4. Đọc mã QR
    qr_data, qr_status = OMREngine.decode_qr(warped)
    form_id = f"FORM-{uuid.uuid4().hex[:8].upper()}"
    enumerator_id = ""

    if qr_data and isinstance(qr_data, dict):
        form_id = qr_data.get("form_id", form_id)
        enumerator_id = qr_data.get("enumerator_id", "")

    # 5. Đọc các ô tích OMR
    detected_answers, confidences, warnings = OMREngine.read_bubbles(warped, layout)

    # 6. Tính điểm tin cậy trung bình
    avg_conf = float(np.mean(list(confidences.values()))) if confidences else 0.85

    # 7. Sinh ảnh lớp phủ trực quan (Visual Overlay)
    overlay_b64 = OMREngine.generate_visual_overlay(warped, layout, detected_answers, confidences)

    return PaperScanResult(
        success=True,
        survey_id=survey_id,
        form_id=form_id,
        enumerator_id=enumerator_id,
        image_quality=quality,
        confidence_score=round(avg_conf, 2),
        detected_answers=detected_answers,
        question_confidences={k: round(v, 2) for k, v in confidences.items()},
        overlay_image_base64=overlay_b64,
        warnings=warnings,
        orientation_corrected=rot_angle
    )

@router.post("/batch-scan")
async def batch_scan_paper_images(
    survey_id: str,
    files: List[UploadFile] = File(...)
):
    """
    Tiếp nhận và xử lý hàng loạt ảnh phiếu khảo sát thực địa:
    Tự động giải mã QR, nắn phẳng phối cảnh và bóc tách đáp án OMR theo lô.
    """
    if not files:
        raise HTTPException(status_code=400, detail="Không có tệp ảnh nào được gửi lên.")

    with get_db() as conn:
        t_row = conn.execute("""
            SELECT * FROM paper_templates WHERE survey_id = ? ORDER BY template_version DESC LIMIT 1
        """, (survey_id,)).fetchone()

        if not t_row:
            s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
            if not s_row:
                raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")
            q_rows = conn.execute("SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC", (survey_id,)).fetchall()
            questions = [{
                "id": q["id"], "question_type": q["question_type"], "title": q["title"],
                "order_index": q["order_index"], "options": json.loads(q["options_json"] or "[]")
            } for q in q_rows]
            layout = OMREngine.generate_paper_template(dict(s_row), questions)
            t_id = str(uuid.uuid4())
            conn.execute("""
                INSERT INTO paper_templates (id, survey_id, template_version, layout_config_json, created_at)
                VALUES (?, ?, 1, ?, ?)
            """, (t_id, survey_id, json.dumps(layout, ensure_ascii=False), now_iso()))
        else:
            layout = json.loads(t_row["layout_config_json"])

    results = []
    success_count = 0
    failure_count = 0

    for file in files:
        try:
            content = await file.read()
            nparr = np.frombuffer(content, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "Không thể giải mã tệp ảnh (định dạng không hợp lệ)."
                })
                failure_count += 1
                continue

            quality = OMREngine.assess_image_quality(image)
            warped = OMREngine.normalize_perspective(image)
            warped, rot_angle = OMREngine.auto_orient_page(warped)
            qr_data, qr_status = OMREngine.decode_qr(warped)
            form_id = f"FORM-{uuid.uuid4().hex[:8].upper()}"
            enumerator_id = ""
            if qr_data and isinstance(qr_data, dict):
                form_id = qr_data.get("form_id", form_id)
                enumerator_id = qr_data.get("enumerator_id", "")

            detected_answers, confidences, warnings = OMREngine.read_bubbles(warped, layout)
            avg_conf = float(np.mean(list(confidences.values()))) if confidences else 0.85

            results.append({
                "filename": file.filename,
                "success": True,
                "form_id": form_id,
                "enumerator_id": enumerator_id,
                "confidence_score": round(avg_conf, 2),
                "detected_answers": detected_answers,
                "warnings": warnings,
                "image_quality": quality,
                "orientation_corrected": rot_angle
            })
            success_count += 1
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
            failure_count += 1

    return {
        "survey_id": survey_id,
        "total_files": len(files),
        "success_count": success_count,
        "failure_count": failure_count,
        "results": results
    }

@router.post("/ingest", status_code=201)
def ingest_paper_response(
    survey_id: str,
    payload: PaperIngestPayload
):
    """
    Xác nhận nạp kết quả số hóa phiếu giấy vào cơ sở dữ liệu sau khi người dùng đã xem xét
    hoặc chỉnh sửa thủ công. Dữ liệu được chuyển vào DataTrust Quality Engine để sàng lọc gian lận.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        survey_version = s_row["version"]
        response_id = str(uuid.uuid4())
        submitted_at_iso = now_iso()
        # Thời gian làm bài danh nghĩa cho phiếu giấy
        duration = 180.0

        # Lưu bản ghi response với source = 'paper_scan'
        client_meta = {
            "source": "paper_scan",
            "form_id": payload.form_id,
            "omr_confidence": payload.omr_confidence,
            "manual_corrections_count": len(payload.manual_corrections or [])
        }

        conn.execute("""
            INSERT INTO responses (
                id, survey_id, survey_version, started_at, submitted_at,
                duration_seconds, client_metadata_json, risk_score, risk_level,
                analysis_status, review_status, source, enumerator_id, paper_form_id,
                scan_image_url, omr_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0.0, 'low', 'pending', 'unverified', 'paper_scan', ?, ?, ?, ?)
        """, (
            response_id, survey_id, survey_version, submitted_at_iso, submitted_at_iso,
            duration, json.dumps(client_meta), payload.enumerator_id, payload.form_id,
            payload.scan_image_url or "", payload.omr_confidence
        ))

        # Lưu câu trả lời
        for qid, val in payload.answers.items():
            ans_id = str(uuid.uuid4())
            ans_str = json.dumps(val, ensure_ascii=False) if isinstance(val, (list, dict)) else str(val if val is not None else "")
            conn.execute("""
                INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (ans_id, response_id, qid, ans_str, submitted_at_iso))

        # Ghi nhật ký Audit Log nếu có sửa đổi thủ công vào chuỗi băm bất biến
        if payload.manual_corrections:
            record_audit_log(
                conn, 'response', response_id, 'MANUAL_CORRECTION_FIELD_OMR',
                {
                    "form_id": payload.form_id,
                    "corrections": payload.manual_corrections
                },
                submitted_at_iso
            )

        # Lấy danh sách câu hỏi và phản hồi trước để đưa vào Quality Engine
        q_rows = conn.execute("SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC", (survey_id,)).fetchall()
        questions = [dict(q) for q in q_rows]
        for q in questions:
            q["options"] = json.loads(q.get("options_json") or "[]")
            q["logic_rules"] = json.loads(q.get("logic_rules_json") or "[]")

        prior_resp_rows = conn.execute("""
            SELECT id, enumerator_id, risk_score FROM responses WHERE survey_id = ? AND id != ?
        """, (survey_id, response_id)).fetchall()

        prior_responses = []
        for pr in prior_resp_rows:
            pr_id = pr["id"]
            ans_rows = conn.execute("SELECT question_id, answer_value FROM response_answers WHERE response_id = ?", (pr_id,)).fetchall()
            p_answers = {}
            for a in ans_rows:
                raw_val = a["answer_value"]
                try:
                    p_answers[a["question_id"]] = json.loads(raw_val)
                except Exception:
                    p_answers[a["question_id"]] = raw_val
            prior_responses.append({
                "id": pr_id,
                "answers": p_answers,
                "enumerator_id": pr["enumerator_id"],
                "risk_score": pr["risk_score"]
            })

        # Thực thi Quality Engine
        s_settings = json.loads(s_row["settings_json"] or "{}") if "settings_json" in s_row.keys() else {}
        quality_settings = s_settings.get("quality_settings", {})

        analysis = QualityEngine.analyze_response(
            new_answers=payload.answers,
            duration_seconds=duration,
            questions=questions,
            prior_responses=prior_responses,
            enumerator_id=payload.enumerator_id,
            quality_settings=quality_settings
        )

        assessment_id = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO quality_assessments (
                id, response_id, score_dup, score_pattern, score_logic, score_speed, score_text, score_enum,
                composite_score, flags_json, closest_match_response_id, highest_similarity, assessed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assessment_id, response_id,
            analysis["score_dup"], analysis["score_pattern"], analysis["score_logic"],
            analysis["score_speed"], analysis["score_text"], analysis.get("score_enum", 0.0),
            analysis["composite_score"], json.dumps(analysis["flags"], ensure_ascii=False),
            analysis.get("closest_match_response_id"), analysis.get("highest_similarity", 0.0),
            submitted_at_iso
        ))

        conn.execute("""
            UPDATE responses 
            SET risk_score = ?, risk_level = ?, analysis_status = 'analyzed'
            WHERE id = ?
        """, (analysis["composite_score"], analysis["risk_level"], response_id))

        return {
            "response_id": response_id,
            "status": "ingested",
            "source": "paper_scan",
            "form_id": payload.form_id,
            "risk_score": analysis["composite_score"],
            "risk_level": analysis["risk_level"],
            "flags": analysis["flags"]
        }

@router.get("/export-audit")
def export_paper_omr_audit_csv(survey_id: str):
    """
    Xuất báo cáo kiểm định và hậu kiểm toàn bộ phiếu giấy OMR đã số hóa vào hệ thống (CSV UTF-8 BOM).
    Bao gồm mã phiếu, mã ĐTV, độ tin cậy OMR, số lượng câu chỉnh sửa thủ công, điểm rủi ro, cờ vi phạm chất lượng.
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT title, public_slug FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")
        slug = s_row["public_slug"] or survey_id

        rows = conn.execute("""
            SELECT 
                r.id, r.paper_form_id, r.enumerator_id, r.submitted_at, r.duration_seconds,
                r.omr_confidence, r.risk_score, r.risk_level, r.review_status, r.review_notes,
                r.client_metadata_json,
                qa.flags_json, qa.composite_score
            FROM responses r
            LEFT JOIN quality_assessments qa ON qa.response_id = r.id
            WHERE r.survey_id = ? AND r.source = 'paper_scan'
            ORDER BY r.submitted_at DESC
        """, (survey_id,)).fetchall()

    output = io.StringIO()
    fieldnames = [
        "Mã Phiếu Giấy (Form ID)",
        "Mã Điều tra viên",
        "Thời gian số hóa",
        "Độ tin cậy OMR (%)",
        "Số câu sửa thủ công",
        "Điểm rủi ro",
        "Phân loại rủi ro",
        "Trạng thái hậu kiểm",
        "Ghi chú hậu kiểm",
        "Cờ cảnh báo chất lượng"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for r in rows:
        meta = {}
        try:
            meta = json.loads(r["client_metadata_json"] or "{}")
        except Exception:
            pass
        
        flags = []
        try:
            flags = json.loads(r["flags_json"] or "[]")
        except Exception:
            pass

        flags_text = "; ".join([f"{f.get('code', '')}: {f.get('message', '')}" for f in flags]) if flags else "Đạt chuẩn"
        conf_pct = round((r["omr_confidence"] or 1.0) * 100, 1)

        writer.writerow({
            "Mã Phiếu Giấy (Form ID)": sanitize_csv_cell(r["paper_form_id"] or r["id"]),
            "Mã Điều tra viên": sanitize_csv_cell(r["enumerator_id"] or "—"),
            "Thời gian số hóa": sanitize_csv_cell(r["submitted_at"]),
            "Độ tin cậy OMR (%)": f"{conf_pct}%",
            "Số câu sửa thủ công": meta.get("manual_corrections_count", 0),
            "Điểm rủi ro": r["risk_score"] or 0.0,
            "Phân loại rủi ro": (r["risk_level"] or "low").upper(),
            "Trạng thái hậu kiểm": sanitize_csv_cell(r["review_status"] or "unverified"),
            "Ghi chú hậu kiểm": sanitize_csv_cell(r["review_notes"] or ""),
            "Cờ cảnh báo chất lượng": sanitize_csv_cell(flags_text)
        })

    csv_bytes = "\ufeff" + output.getvalue()
    safe_slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", slug)
    return Response(
        content=csv_bytes.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="datatrust_paper_omr_audit_{safe_slug}.csv"'}
    )
