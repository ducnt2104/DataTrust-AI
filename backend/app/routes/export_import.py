import csv
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Response
from app.database import get_db
from app.engine.quality_engine import QualityEngine

router = APIRouter(prefix="/api/surveys/{survey_id}", tags=["Export & Import"])

@router.get("/export")
def export_survey_data(
    survey_id: str,
    scope: str = Query("verified_clean", description="Phạm vi xuất: raw, reviewed, verified_clean"),
    format: str = Query("csv", description="Định dạng: csv hoặc json")
):
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        # Lọc danh sách phản hồi theo scope
        query = "SELECT * FROM responses WHERE survey_id = ?"
        params = [survey_id]

        if scope == "reviewed":
            query += " AND review_status != 'unverified'"
        elif scope == "verified_clean":
            query += " AND (review_status = 'verified_valid' OR (review_status = 'unverified' AND risk_level = 'low'))"

        query += " ORDER BY submitted_at ASC"
        resp_rows = conn.execute(query, params).fetchall()

        # Lấy danh sách câu hỏi để dựng cột
        q_rows = conn.execute("""
            SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()
        
        q_map = {q["id"]: q["title"] for q in q_rows}

        # Thu thập dữ liệu các dòng
        data = []
        for r in resp_rows:
            rid = r["id"]
            ans_rows = conn.execute("""
                SELECT question_id, answer_value FROM response_answers WHERE response_id = ?
            """, (rid,)).fetchall()
            
            ans_dict = {a["question_id"]: a["answer_value"] for a in ans_rows}
            
            row_data = {
                "Response_ID": rid,
                "Submitted_At": r["submitted_at"],
                "Duration_Seconds": round(r["duration_seconds"], 1),
                "Risk_Score": round(r["risk_score"], 1),
                "Risk_Level": r["risk_level"],
                "Review_Status": r["review_status"],
                "Review_Notes": r["review_notes"] or ""
            }
            
            for qid, qtitle in q_map.items():
                row_data[qtitle] = ans_dict.get(qid, "")
                
            data.append(row_data)

        if format.lower() == "json":
            return {
                "survey_id": survey_id,
                "survey_title": s_row["title"],
                "export_scope": scope,
                "total_records": len(data),
                "records": data
            }

        # Xuất định dạng CSV với UTF-8 BOM
        output = io.StringIO()
        fieldnames = ["Response_ID", "Submitted_At", "Duration_Seconds", "Risk_Score", "Risk_Level", "Review_Status", "Review_Notes"] + list(q_map.values())
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

        csv_content = output.getvalue()
        # Thêm UTF-8 BOM để Excel hiển thị đúng tiếng Việt
        csv_bytes = "\ufeff" + csv_content

        filename = f"{s_row['public_slug']}_{scope}.csv"
        return Response(
            content=csv_bytes.encode("utf-8"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

@router.post("/import/csv")
async def import_csv_responses(survey_id: str, file: UploadFile = File(...)):
    """Nhập dữ liệu phản hồi từ tệp CSV bên ngoài và chạy phân tích chất lượng"""
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except Exception:
        text = content.decode("utf-8", errors="replace")

    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise HTTPException(status_code=400, detail="Tệp CSV không có dữ liệu.")

    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        q_rows = conn.execute("""
            SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()
        
        q_title_to_id = {q["title"].strip().lower(): q["id"] for q in q_rows}
        questions_list = [dict(q) for q in q_rows]
        for q in questions_list:
            q["options"] = json.loads(q.get("options_json") or "[]")
            q["logic_rules"] = json.loads(q.get("logic_rules_json") or "[]")

        imported_count = 0
        current_time = datetime.now(timezone.utc).isoformat()

        for row in rows:
            response_id = str(uuid.uuid4())
            answers = {}
            for col_name, val in row.items():
                if col_name and col_name.strip().lower() in q_title_to_id:
                    qid = q_title_to_id[col_name.strip().lower()]
                    answers[qid] = val.strip()

            if not answers:
                continue

            conn.execute("""
                INSERT INTO responses (
                    id, survey_id, survey_version, started_at, submitted_at,
                    duration_seconds, client_metadata_json, risk_score, risk_level,
                    analysis_status, review_status
                ) VALUES (?, ?, ?, ?, ?, 30.0, '{"source": "csv_import"}', 0.0, 'low', 'pending', 'unverified')
            """, (response_id, survey_id, s_row["version"], current_time, current_time))

            for qid, val in answers.items():
                conn.execute("""
                    INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (str(uuid.uuid4()), response_id, qid, str(val), current_time))

            # Chạy Quality Engine
            analysis = QualityEngine.analyze_response(
                new_answers=answers,
                duration_seconds=30.0,
                questions=questions_list,
                prior_responses=[]
            )

            conn.execute("""
                INSERT INTO quality_assessments (
                    id, response_id, score_dup, score_pattern, score_logic, score_speed, score_text,
                    composite_score, flags_json, closest_match_response_id, highest_similarity, assessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), response_id,
                analysis["score_dup"], analysis["score_pattern"], analysis["score_logic"],
                analysis["score_speed"], analysis["score_text"], analysis["composite_score"],
                json.dumps(analysis["flags"], ensure_ascii=False),
                None, 0.0, current_time
            ))

            conn.execute("""
                UPDATE responses SET risk_score = ?, risk_level = ?, analysis_status = 'analyzed' WHERE id = ?
            """, (analysis["composite_score"], analysis["risk_level"], response_id))

            imported_count += 1

    return {"message": f"Đã nhập thành công {imported_count} phản hồi từ tệp CSV.", "imported_count": imported_count}
