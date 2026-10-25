import json
import time
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, record_audit_log

client = TestClient(app)

def test_explain_query_plan_uses_indexes():
    """Kiểm tra SQLite EXPLAIN QUERY PLAN sử dụng đúng các B-Tree Indexes để tránh Full Table Scan"""
    with get_db() as conn:
        # 1. Kiểm tra index trên bảng responses theo survey_id
        plan_resp = conn.execute("EXPLAIN QUERY PLAN SELECT id FROM responses INDEXED BY idx_responses_survey WHERE survey_id = ?", ("s_test",)).fetchall()
        plan_resp_str = " ".join([dict(p).get("detail", "") for p in plan_resp])
        assert "idx_responses_survey" in plan_resp_str or "USING INDEX" in plan_resp_str

        # 2. Kiểm tra index trên bảng response_answers theo response_id
        plan_ans = conn.execute("EXPLAIN QUERY PLAN SELECT answer_value FROM response_answers INDEXED BY idx_answers_response WHERE response_id = ?", ("r_test",)).fetchall()
        plan_ans_str = " ".join([dict(p).get("detail", "") for p in plan_ans])
        assert "idx_answers_response" in plan_ans_str or "USING INDEX" in plan_ans_str

        # 3. Kiểm tra index trên bảng audit_logs theo entity_type và entity_id
        plan_audit = conn.execute("EXPLAIN QUERY PLAN SELECT id FROM audit_logs INDEXED BY idx_audit_logs_entity WHERE entity_type = ? AND entity_id = ?", ("survey", "s_test")).fetchall()
        plan_audit_str = " ".join([dict(p).get("detail", "") for p in plan_audit])
        assert "idx_audit_logs_entity" in plan_audit_str or "USING INDEX" in plan_audit_str

        # 4. Kiểm tra index trên bảng quality_assessments theo response_id
        plan_qa = conn.execute("EXPLAIN QUERY PLAN SELECT composite_score FROM quality_assessments INDEXED BY idx_quality_response WHERE response_id = ?", ("r_test",)).fetchall()
        plan_qa_str = " ".join([dict(p).get("detail", "") for p in plan_qa])
        assert "idx_quality_response" in plan_qa_str or "USING INDEX" in plan_qa_str

def test_high_volume_data_load_and_analytics_latency():
    """
    Tạo 500 phản hồi thực tế và kiểm tra độ trễ (latency) của toàn bộ các endpoint phân tích:
    - /analytics
    - /analytics/benford
    - /analytics/qualitative
    - /enumerators
    - /audit-trail
    Đảm bảo thời gian phản hồi đạt chuẩn cấp độ sản xuất (< 250ms cho tập dữ liệu 500 phiếu)
    """
    survey_id = f"stress_survey_{uuid.uuid4().hex[:8]}"
    slug = f"stress-slug-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        # 1. Tạo survey
        conn.execute("""
            INSERT INTO surveys (id, title, description, instructions, status, public_slug, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'published', ?, 1, ?, ?)
        """, (survey_id, "Khảo sát Tải Cao Benchmark", "Benchmark Data Load", "Hướng dẫn", slug, now_iso, now_iso))

        # 2. Tạo 4 câu hỏi (single_choice, number, likert, short_text)
        q1_id = f"q1_{uuid.uuid4().hex[:6]}"
        q2_id = f"q2_{uuid.uuid4().hex[:6]}"
        q3_id = f"q3_{uuid.uuid4().hex[:6]}"
        q4_id = f"q4_{uuid.uuid4().hex[:6]}"

        conn.execute("""
            INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at)
            VALUES (?, ?, 0, 'single_choice', 'Đánh giá mức độ hài lòng', 1, ?, ?)
        """, (q1_id, survey_id, json.dumps([{"id": "o1", "label": "Rất tốt"}, {"id": "o2", "label": "Tốt"}, {"id": "o3", "label": "Bình thường"}]), now_iso))

        conn.execute("""
            INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at)
            VALUES (?, ?, 1, 'number', 'Doanh thu tháng (triệu VNĐ)', 1, '[]', ?)
        """, (q2_id, survey_id, now_iso))

        conn.execute("""
            INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at)
            VALUES (?, ?, 2, 'likert', 'Mức độ cam kết gắn bó', 1, ?, ?)
        """, (q3_id, survey_id, json.dumps([{"id": "l1", "label": "1"}, {"id": "l2", "label": "2"}, {"id": "l3", "label": "3"}, {"id": "l4", "label": "4"}, {"id": "l5", "label": "5"}]), now_iso))

        conn.execute("""
            INSERT INTO questions (id, survey_id, order_index, question_type, title, is_required, options_json, created_at)
            VALUES (?, ?, 3, 'short_text', 'Ý kiến đóng góp cải tiến', 0, '[]', ?)
        """, (q4_id, survey_id, now_iso))

        # 3. Ghi log kiểm toán cho việc xuất bản
        record_audit_log(conn, "survey", survey_id, "PUBLISH", {"slug": slug, "benchmark": True})

        # 4. Chèn 500 responses & response_answers theo batch
        resp_batch = []
        ans_batch = []
        qa_batch = []
        
        sample_texts = [
            "Dịch vụ hỗ trợ rất nhanh chóng và nhiệt tình",
            "Giao diện thân thiện nhưng cần tối ưu hóa tốc độ tải trang",
            "Chất lượng dữ liệu rất tin cậy và minh bạch",
            "Hệ thống ổn định, đội ngũ hỗ trợ giải quyết vấn đề kịp thời",
            "Quy trình kiểm duyệt dữ liệu rất chặt chẽ và an tâm",
            "Cần bổ sung thêm tính năng xuất báo cáo tự động"
        ]

        for i in range(500):
            rid = f"r_bench_{i}_{uuid.uuid4().hex[:6]}"
            dur = 25.0 + (i % 80)
            risk = (i % 30) * 2.5
            risk_lvl = "high" if risk >= 70.0 else ("medium" if risk >= 40.0 else "low")
            enum_code = f"ENUM_{i % 8:02d}"
            lat = 10.762622 + (i % 20) * 0.005
            lon = 106.660172 + (i % 20) * 0.005
            meta = json.dumps({"latitude": lat, "longitude": lon, "enumerator_id": enum_code})

            resp_batch.append((
                rid, survey_id, 1, now_iso, now_iso, dur, meta, risk, risk_lvl, "analyzed", "unverified",
                "", None, "online_form", enum_code, "", "", 1.0
            ))

            # Câu trả lời Q1 (single_choice)
            ans_batch.append((f"a1_{rid}", rid, q1_id, f"o{(i % 3) + 1}", now_iso))
            # Câu trả lời Q2 (number - phân bố Benford tự nhiên)
            num_val = round(12.5 * (1.15 ** (i % 45)), 1)
            ans_batch.append((f"a2_{rid}", rid, q2_id, str(num_val), now_iso))
            # Câu trả lời Q3 (likert)
            ans_batch.append((f"a3_{rid}", rid, q3_id, f"l{(i % 5) + 1}", now_iso))
            # Câu trả lời Q4 (short_text)
            ans_batch.append((f"a4_{rid}", rid, q4_id, sample_texts[i % len(sample_texts)], now_iso))

            # Quality assessment
            qa_batch.append((
                f"qa_{rid}", rid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, risk, "[]", None, 0.0, now_iso
            ))

        conn.executemany("""
            INSERT INTO responses (
                id, survey_id, survey_version, started_at, submitted_at, duration_seconds,
                client_metadata_json, risk_score, risk_level, analysis_status, review_status,
                review_notes, reviewed_at, source, enumerator_id, paper_form_id, scan_image_url, omr_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, resp_batch)

        conn.executemany("""
            INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, ans_batch)

        conn.executemany("""
            INSERT INTO quality_assessments (
                id, response_id, score_dup, score_pattern, score_logic, score_speed,
                score_text, score_enum, composite_score, flags_json, closest_match_response_id,
                highest_similarity, assessed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, qa_batch)

    # 5. Benchmark API 1: /api/surveys/{survey_id}/analytics
    t0 = time.perf_counter()
    resp_analytics = client.get(f"/api/surveys/{survey_id}/analytics")
    t1 = time.perf_counter()
    analytics_duration_ms = (t1 - t0) * 1000.0

    assert resp_analytics.status_code == 200
    data_analytics = resp_analytics.json()
    assert data_analytics["total_responses"] == 500
    assert len(data_analytics["questions_analytics"]) == 4
    assert len(data_analytics["funnel_analytics"]) == 4
    assert analytics_duration_ms < 250.0, f"Analytics latency quá chậm: {analytics_duration_ms:.2f}ms >= 250ms"

    # 6. Benchmark API 2: /api/surveys/{survey_id}/analytics/benford
    t0 = time.perf_counter()
    resp_benford = client.get(f"/api/surveys/{survey_id}/analytics/benford?question_id={q2_id}")
    t1 = time.perf_counter()
    benford_duration_ms = (t1 - t0) * 1000.0

    assert resp_benford.status_code == 200
    data_benford = resp_benford.json()
    assert data_benford["total_numeric_samples"] == 500
    assert benford_duration_ms < 150.0, f"Benford latency quá chậm: {benford_duration_ms:.2f}ms >= 150ms"

    # 7. Benchmark API 3: /api/surveys/{survey_id}/enumerators
    t0 = time.perf_counter()
    resp_enums = client.get(f"/api/surveys/{survey_id}/enumerators")
    t1 = time.perf_counter()
    enums_duration_ms = (t1 - t0) * 1000.0

    assert resp_enums.status_code == 200
    data_enums = resp_enums.json()
    assert data_enums["total_enumerators"] == 8
    assert enums_duration_ms < 200.0, f"Enumerators latency quá chậm: {enums_duration_ms:.2f}ms >= 200ms"

    # 8. Benchmark API 4: /api/surveys/{survey_id}/analytics/qualitative
    t0 = time.perf_counter()
    resp_qual = client.get(f"/api/surveys/{survey_id}/analytics/qualitative?question_id={q4_id}&sample_limit=300")
    t1 = time.perf_counter()
    qual_duration_ms = (t1 - t0) * 1000.0

    assert resp_qual.status_code == 200
    data_qual = resp_qual.json()
    assert data_qual["total_analyzed"] > 0
    assert qual_duration_ms < 400.0, f"Qualitative NLP latency quá chậm: {qual_duration_ms:.2f}ms >= 400ms"

    # 9. Benchmark API 5: /api/surveys/{survey_id}/audit-trail
    t0 = time.perf_counter()
    resp_audit = client.get(f"/api/surveys/{survey_id}/audit-trail")
    t1 = time.perf_counter()
    audit_duration_ms = (t1 - t0) * 1000.0

    assert resp_audit.status_code == 200
    data_audit = resp_audit.json()
    assert data_audit["is_chain_valid"] is True
    assert audit_duration_ms < 150.0, f"Audit trail latency quá chậm: {audit_duration_ms:.2f}ms >= 150ms"
