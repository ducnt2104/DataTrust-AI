import pytest
import uuid
import json
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_analytics_and_export_journey():
    # 1. Tạo và xuất bản khảo sát
    s_res = client.post("/api/surveys", json={
        "title": "Khảo sát ý kiến người tiêu dùng về xe điện",
        "description": "Nghiên cứu thị trường 2026"
    })
    survey_id = s_res.json()["id"]
    slug = s_res.json()["public_slug"]

    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q_brand",
                "question_type": "single_choice",
                "title": "Hãng xe bạn quan tâm?",
                "is_required": True,
                "options": [{"id": "vinfast", "label": "VinFast"}, {"id": "tesla", "label": "Tesla"}, {"id": "byd", "label": "BYD"}]
            },
            {
                "id": "q_budget",
                "question_type": "number",
                "title": "Ngân sách dự kiến (triệu VNĐ)?",
                "is_required": True,
                "options": []
            }
        ]
    })
    client.post(f"/api/surveys/{survey_id}/publish")

    # 2. Kiểm tra Analytics khi N = 0
    an_res0 = client.get(f"/api/surveys/{survey_id}/analytics")
    assert an_res0.status_code == 200
    an_data0 = an_res0.json()
    assert an_data0["total_responses"] == 0
    assert an_data0["is_sample_size_sufficient"] is False
    assert "chưa đạt ngưỡng tối thiểu" in an_data0["sample_size_notice"]

    # 3. Gửi 5 phản hồi thực
    now = datetime.now(timezone.utc)
    resp_ids = []
    brands = ["vinfast", "tesla", "vinfast", "byd", "vinfast"]
    budgets = ["700", "1200", "850", "600", "900"]

    for i in range(5):
        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=40)).isoformat(),
            "submitted_at": now.isoformat(),
            "answers": {
                "q_brand": brands[i],
                "q_budget": budgets[i]
            }
        })
        assert sub_res.status_code == 201
        resp_ids.append(sub_res.json()["response_id"])

    # 4. Kiểm tra Analytics khi N >= 5
    an_res5 = client.get(f"/api/surveys/{survey_id}/analytics")
    assert an_res5.status_code == 200
    an_data5 = an_res5.json()
    assert an_data5["total_responses"] == 5
    assert an_data5["is_sample_size_sufficient"] is True
    assert an_data5["sample_size_notice"] is None
    assert an_data5["overall_completion_rate"] == 100.0
    assert len(an_data5["funnel_analytics"]) == 2
    assert an_data5["funnel_analytics"][0]["completion_rate_pct"] == 100.0
    
    # Kiểm tra phân bố câu hỏi
    brand_stats = next(q for q in an_data5["questions_analytics"] if q["question_id"] == "q_brand")
    assert brand_stats["completion_rate"] == 100.0
    assert brand_stats["option_distribution"]["VinFast"] == 3
    assert brand_stats["option_distribution"]["Tesla"] == 1

    budget_stats = next(q for q in an_data5["questions_analytics"] if q["question_id"] == "q_budget")
    assert budget_stats["stats_summary"]["min"] == 600.0
    assert budget_stats["stats_summary"]["max"] == 1200.0

    # 5. Cập nhật quyết định xác minh (Review decision)
    rev_res = client.patch(f"/api/surveys/{survey_id}/responses/{resp_ids[0]}/review", json={
        "review_status": "verified_valid",
        "review_notes": "Đã gọi điện xác nhận phỏng vấn thành công"
    })
    assert rev_res.status_code == 200

    rev_res_fraud = client.patch(f"/api/surveys/{survey_id}/responses/{resp_ids[1]}/review", json={
        "review_status": "verified_fraud",
        "review_notes": "Số điện thoại không liên lạc được"
    })
    assert rev_res_fraud.status_code == 200

    # 6. Kiểm tra so sánh 2 phản hồi side-by-side
    cmp_res = client.get(f"/api/surveys/{survey_id}/responses/compare/side-by-side?resp1={resp_ids[0]}&resp2={resp_ids[2]}")
    assert cmp_res.status_code == 200
    cmp_data = cmp_res.json()
    assert cmp_data["total_questions_compared"] == 2
    # Cả 2 đều chọn VinFast ở q_brand -> matching_answers_count >= 1
    assert cmp_data["matching_answers_count"] >= 1

    # 7. Xuất dữ liệu CSV
    # Verified Clean scope: Phải bao gồm các bản ghi hợp lệ hoặc chưa bị gắn cờ, nhưng LOẠI BỎ bản ghi verified_fraud
    export_csv = client.get(f"/api/surveys/{survey_id}/export?scope=verified_clean&format=csv")
    assert export_csv.status_code == 200
    assert "text/csv" in export_csv.headers["content-type"]

    # 7.1. Kiểm tra Tải tệp mẫu CSV Import Template
    template_res = client.get(f"/api/surveys/{survey_id}/import/template")
    assert template_res.status_code == 200
    assert "text/csv" in template_res.headers["content-type"]
    template_text = template_res.content.decode("utf-8-sig")
    assert "Enumerator_ID" in template_text
    assert "Duration_Seconds" in template_text
    assert "Hãng xe bạn quan tâm?" in template_text
    assert "Ngân sách dự kiến (triệu VNĐ)?" in template_text

    # 7.2. Kiểm tra Nhập dữ liệu CSV (CSV Import) với siêu dữ liệu Enumerator & Duration
    csv_payload = "Enumerator_ID,Duration_Seconds,Hãng xe bạn quan tâm?,Ngân sách dự kiến (triệu VNĐ)?\nDTV09,150,VinFast,750\nDTV10,95,Tesla,1100\n"
    import_res = client.post(
        f"/api/surveys/{survey_id}/import/csv",
        files={"file": ("import_sample.csv", csv_payload.encode("utf-8"), "text/csv")}
    )
    assert import_res.status_code == 200
    import_data = import_res.json()
    assert import_data["imported_count"] == 2

    # Xác nhận tổng số phản hồi sau import tăng lên 7
    an_res7 = client.get(f"/api/surveys/{survey_id}/analytics")
    assert an_res7.status_code == 200
    assert an_res7.json()["total_responses"] == 7
    csv_text = export_csv.content.decode("utf-8-sig")
    assert "Response_ID" in csv_text
    assert "Hãng xe bạn quan tâm?" in csv_text
    # resp_ids[1] bị đánh dấu verified_fraud -> KHÔNG được có trong verified_clean
    assert resp_ids[1] not in csv_text
    # resp_ids[0] là verified_valid -> BẮT BUỘC có trong verified_clean
    assert resp_ids[0] in csv_text

    # 8. Kiểm tra AI endpoints
    ai_gen = client.post("/api/ai/generate-survey", json={
        "topic": "Khảo sát ứng dụng trí tuệ nhân tạo trong giáo dục",
        "audience": "Sinh viên đại học",
        "expected_time_minutes": 5
    })
    assert ai_gen.status_code == 200
    ai_draft = ai_gen.json()
    assert "title" in ai_draft
    assert len(ai_draft["questions"]) >= 3

    # Kiểm định câu hỏi
    ai_audit = client.post("/api/ai/audit-questions", json={
        "questions": [
            {"id": "test_q", "title": "Sản phẩm của chúng tôi tuyệt vời thế nào?", "question_type": "single_choice", "options": [{"id": "1", "label": "Tốt"}]}
        ]
    })
    assert ai_audit.status_code == 200
    assert ai_audit.json()["total_issues"] >= 1

def test_batch_review_decisions_endpoint():
    """Kiểm tra API cập nhật quyết định xác minh hàng loạt (Batch Review) và ghi nhật ký chuỗi băm"""
    s_res = client.post("/api/surveys", json={
        "title": "Khảo sát Thẩm định Hàng loạt 2026",
        "description": "Test batch review"
    })
    survey_id = s_res.json()["id"]
    slug = s_res.json()["public_slug"]
    q_batch_id = f"q_batch_{uuid.uuid4().hex[:8]}"

    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": q_batch_id,
                "question_type": "single_choice",
                "title": "Bạn có hài lòng không?",
                "is_required": True,
                "options": [{"id": "yes", "label": "Có"}, {"id": "no", "label": "Không"}]
            }
        ]
    })
    client.post(f"/api/surveys/{survey_id}/publish")

    now = datetime.now(timezone.utc)
    resp_ids = []
    for i in range(4):
        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=60 - i * 10)).isoformat(),
            "submitted_at": (now - timedelta(seconds=30 - i * 5)).isoformat(),
            "client_metadata": {"device_id": f"distinct_device_{i}"},
            "answers": {q_batch_id: "Có" if i % 2 == 0 else "Không"}
        })
        resp_ids.append(sub_res.json()["response_id"])

    # Batch duyệt hợp lệ 3 phản hồi đầu
    batch_res = client.post(f"/api/surveys/{survey_id}/responses/batch-review", json={
        "response_ids": resp_ids[:3],
        "review_status": "verified_valid",
        "review_notes": "Duyệt hàng loạt tự động"
    })
    assert batch_res.status_code == 200
    assert batch_res.json()["updated_count"] == 3
    assert batch_res.json()["review_status"] == "verified_valid"

    # Batch đánh dấu loại bỏ phản hồi thứ 4
    fraud_res = client.post(f"/api/surveys/{survey_id}/responses/batch-review", json={
        "response_ids": [resp_ids[3]],
        "review_status": "verified_fraud",
        "review_notes": "Nghi vấn trùng lặp"
    })
    assert fraud_res.status_code == 200
    assert fraud_res.json()["updated_count"] == 1

    # Kiểm tra danh sách phản hồi để xác nhận trạng thái
    list_res = client.get(f"/api/surveys/{survey_id}/responses?review_status=verified_valid")
    assert list_res.status_code == 200
    valid_list = list_res.json()
    assert len(valid_list) == 3

    # Kiểm tra chuỗi băm kiểm toán audit_chain vẫn hợp lệ 100%
    audit_res = client.get(f"/api/surveys/{survey_id}/audit-trail")
    assert audit_res.status_code == 200
    assert audit_res.json()["is_chain_valid"] is True
    assert audit_res.json()["chain_status"] == "VALID"

def test_crosstab_analysis_endpoint():
    """Kiểm tra API phân tích Bảng Ngẫu Nhiên (Cross-Tabulation & Chi-Square Independence Test)"""
    # 1. Tạo khảo sát kiểm định 2 biến
    s_res = client.post("/api/surveys", json={
        "title": "Nghiên cứu liên hệ giới tính và mức độ hài lòng",
        "description": "Cross-tabulation evaluation"
    })
    survey_id = s_res.json()["id"]
    slug = s_res.json()["public_slug"]

    q_gender_id = f"q_gender_{uuid.uuid4().hex[:6]}"
    q_satisfaction_id = f"q_sat_{uuid.uuid4().hex[:6]}"

    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": q_gender_id,
                "question_type": "single_choice",
                "title": "Giới tính của bạn",
                "is_required": True,
                "options": [{"id": "nam", "text": "Nam"}, {"id": "nu", "text": "Nữ"}]
            },
            {
                "id": q_satisfaction_id,
                "question_type": "single_choice",
                "title": "Đánh giá mức độ hài lòng",
                "is_required": True,
                "options": [{"id": "hai_long", "text": "Hài lòng"}, {"id": "khong_hai_long", "text": "Không hài lòng"}]
            }
        ]
    })
    client.post(f"/api/surveys/{survey_id}/publish")

    # 2. Gửi dữ liệu có mối tương quan mạnh giữa giới tính và mức độ hài lòng
    # Nam: 12 Hài lòng, 2 Không hài lòng
    # Nữ: 2 Hài lòng, 14 Không hài lòng
    now = datetime.now(timezone.utc)
    submissions = (
        [("Nam", "Hài lòng")] * 12 +
        [("Nam", "Không hài lòng")] * 2 +
        [("Nữ", "Hài lòng")] * 2 +
        [("Nữ", "Không hài lòng")] * 14
    )

    for idx, (gen, sat) in enumerate(submissions):
        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=120 - idx * 2)).isoformat(),
            "submitted_at": (now - timedelta(seconds=60 - idx)).isoformat(),
            "client_metadata": {"device_id": f"crosstab_device_{idx}"},
            "answers": {
                q_gender_id: gen,
                q_satisfaction_id: sat
            }
        })
        assert sub_res.status_code == 201

    # 3. Gọi API Cross-Tabulation
    ct_res = client.get(
        f"/api/surveys/{survey_id}/analytics/crosstab?row_var={q_gender_id}&col_var={q_satisfaction_id}"
    )
    assert ct_res.status_code == 200
    data = ct_res.json()

    assert data["total_valid_samples"] == 30
    assert data["is_sample_sufficient"] is True
    assert data["degrees_of_freedom"] == 1
    assert data["chi_square_statistic"] > 10.0  # Mối liên hệ rất mạnh
    assert data["p_value"] < 0.01               # Có ý nghĩa thống kê cao
    assert data["cramers_v"] > 0.40             # Cramer's V cao
    assert data["is_statistically_significant"] is True
    assert "Mối liên hệ" in data["association_strength"]
    assert "matrix" in data

    # Kiểm tra ô quan sát
    matrix = data["matrix"]
    assert "nam" in matrix
    assert "nữ" in matrix
    assert matrix["nam"]["hài lòng"]["observed"] == 12
    assert matrix["nam"]["không hài lòng"]["observed"] == 2
    assert matrix["nữ"]["hài lòng"]["observed"] == 2
    assert matrix["nữ"]["không hài lòng"]["observed"] == 14
    assert "pearson_residual" in matrix["nam"]["hài lòng"]
    assert matrix["nam"]["hài lòng"]["pearson_residual"] > 1.5
    assert matrix["nam"]["không hài lòng"]["pearson_residual"] < -1.5

    # 4. Kiểm tra các trường hợp ngoại lệ
    # Trùng biến
    err_res = client.get(f"/api/surveys/{survey_id}/analytics/crosstab?row_var={q_gender_id}&col_var={q_gender_id}")
    assert err_res.status_code == 400

    # ID câu hỏi không tồn tại
    err_res2 = client.get(f"/api/surveys/{survey_id}/analytics/crosstab?row_var={q_gender_id}&col_var=non_existent_q")
    assert err_res2.status_code == 404

def test_complex_csv_import_with_matrix_and_duplicates():
    """Kiểm tra nhập dữ liệu CSV phức hợp: cột mã biến, cột ma trận con, và phát hiện trùng lặp"""
    # 1. Tạo khảo sát có câu hỏi ma trận và câu hỏi đơn
    s_res = client.post("/api/surveys", json={
        "title": "Khảo sát Trải nghiệm Khách hàng Đa Chiều Matrix Test",
        "description": "Thử nghiệm import CSV với ma trận"
    })
    s_id = s_res.json()["id"]

    client.put(f"/api/surveys/{s_id}", json={
        "questions": [
            {
                "id": "q_service",
                "question_type": "single_choice",
                "title": "Loại dịch vụ sử dụng?",
                "is_required": True,
                "options": [{"id": "gold", "label": "Gói Vàng"}, {"id": "silver", "label": "Gói Bạc"}]
            },
            {
                "id": "q_matrix_eval",
                "question_type": "matrix",
                "title": "Đánh giá các khía cạnh dịch vụ",
                "is_required": True,
                "options": {
                    "rows": [
                        {"id": "speed", "label": "Tốc độ phục vụ"},
                        {"id": "attitude", "label": "Thái độ nhân viên"}
                    ],
                    "columns": ["Kém", "Trung bình", "Tốt"]
                }
            }
        ]
    })
    client.post(f"/api/surveys/{s_id}/publish")

    # 2. Tạo nội dung CSV chứa:
    # - Cột mã biến VAR001 thay cho tiêu đề
    # - Cột ma trận sub-columns: "Đánh giá các khía cạnh dịch vụ [Tốc độ phục vụ]" và "Đánh giá các khía cạnh dịch vụ [Thái độ nhân viên]"
    # - 2 dòng đầu có nội dung khác nhau
    # - Dòng thứ 3 là BẢN SAO TRÙNG LẶP HOÀN TOÀN (Exact duplicate) của dòng 2
    csv_content = (
        "Enumerator_ID,Duration_Seconds,VAR001,Đánh giá các khía cạnh dịch vụ [Tốc độ phục vụ],Đánh giá các khía cạnh dịch vụ [Thái độ nhân viên]\n"
        "ENUM01,45,Gói Vàng,Tốt,Tốt\n"
        "ENUM02,50,Gói Bạc,Trung bình,Tốt\n"
        "ENUM02,50,Gói Bạc,Trung bình,Tốt\n"
    )

    import_res = client.post(
        f"/api/surveys/{s_id}/import/csv",
        files={"file": ("matrix_import.csv", csv_content.encode("utf-8"), "text/csv")}
    )
    assert import_res.status_code == 200
    assert import_res.json()["imported_count"] == 3

    # 3. Kiểm tra các phản hồi đã nạp vào CSDL
    resps_res = client.get(f"/api/surveys/{s_id}/responses")
    assert resps_res.status_code == 200
    resps = resps_res.json()
    assert len(resps) == 3

    # Dòng thứ 3 (trùng lặp với dòng 2) phải bị gắn cờ trùng lặp cao (High Risk / FLAG_EXACT_DUPLICATE)
    dup_resp = client.get(f"/api/surveys/{s_id}/responses/{resps[0]['id']}")
    assert dup_resp.status_code == 200
    dup_data = dup_resp.json()
    assert dup_data["assessment"] is not None
    # Phải có cờ FLAG_EXACT_DUPLICATE
    flag_codes = [f["code"] for f in dup_data["assessment"]["flags"]]
    assert "FLAG_EXACT_DUPLICATE" in flag_codes

def test_academic_research_dossier_export():
    """Kiểm tra xuất toàn diện gói Hồ Sơ Nghiên Cứu Khoa Học (Academic Dossier ZIP) với đầy đủ 4 gói thống kê"""
    import zipfile
    import io

    # 1. Tạo khảo sát mẫu với câu hỏi thang đo và danh mục
    s_res = client.post("/api/surveys", json={
        "title": "Nghiên cứu Đánh giá Chất lượng Đào tạo Đại học 2026",
        "description": "Thử nghiệm xuất Academic Dossier"
    })
    s_id = s_res.json()["id"]

    client.put(f"/api/surveys/{s_id}", json={
        "questions": [
            {
                "id": "q_faculty",
                "question_type": "single_choice",
                "title": "Khoa đào tạo của bạn?",
                "is_required": True,
                "options": [{"id": "1", "label": "Công nghệ thông tin"}, {"id": "2", "label": "Kinh tế đối ngoại"}]
            },
            {
                "id": "q_rating",
                "question_type": "rating_scale",
                "title": "Mức độ hài lòng với chương trình đào tạo (1-5)?",
                "is_required": True,
                "options": [
                    {"id": "1", "label": "1 - Rất không hài lòng"},
                    {"id": "2", "label": "2 - Không hài lòng"},
                    {"id": "3", "label": "3 - Bình thường"},
                    {"id": "4", "label": "4 - Hài lòng"},
                    {"id": "5", "label": "5 - Rất hài lòng"}
                ]
            }
        ]
    })
    client.post(f"/api/surveys/{s_id}/publish")

    # 2. Tạo 3 phản hồi mẫu
    now = datetime.now(timezone.utc)
    for i in range(3):
        client.post(f"/api/public/surveys/{s_res.json()['public_slug']}/submit", json={
            "started_at": (now - timedelta(seconds=100 - i * 10)).isoformat(),
            "submitted_at": (now - timedelta(seconds=30 - i * 5)).isoformat(),
            "client_metadata": {"device_id": f"dossier_dev_{i}"},
            "answers": {
                "q_faculty": "Công nghệ thông tin" if i % 2 == 0 else "Kinh tế đối ngoại",
                "q_rating": str(4 + (i % 2))
            }
        })

    # 3. Tải Academic Dossier
    res = client.get(f"/api/surveys/{s_id}/export/academic-dossier?scope=all")
    assert res.status_code == 200
    assert "application/zip" in res.headers["content-type"]

    # 4. Giải nén và kiểm tra từng tệp trong ZIP
    zf = zipfile.ZipFile(io.BytesIO(res.content))
    file_list = zf.namelist()
    
    assert "README_RESEARCH_DOSSIER.md" in file_list
    assert "RESEARCH_MANUSCRIPT.md" in file_list
    assert "dataset_clean.csv" in file_list
    assert "dataset_labeled.csv" in file_list
    assert "spss_syntax.sps" in file_list
    assert "stata_syntax.do" in file_list
    assert "run_analysis.R" in file_list
    assert "analyze_data.py" in file_list
    assert "CODEBOOK.md" in file_list
    assert "INTEGRITY_CERTIFICATE_SHA256.json" in file_list

    # Kiểm tra nội dung stata_syntax.do
    stata_do = zf.read("stata_syntax.do").decode("utf-8")
    assert "import delimited" in stata_do
    assert "label variable" in stata_do
    assert "summarize" in stata_do

    # Kiểm tra chứng chỉ SHA-256
    cert = json.loads(zf.read("INTEGRITY_CERTIFICATE_SHA256.json").decode("utf-8"))
    assert cert["survey_id"] == s_id
    assert "dataset_cryptographic_fingerprints" in cert
    assert len(cert["dataset_cryptographic_fingerprints"]["dataset_clean_csv_sha256"]) == 64

def test_psychometric_scale_reliability_analytics():
    """Kiểm tra phân tích độ tin cậy thang đo (Cronbach's Alpha, Item-Total Statistics & Alpha if Deleted)"""
    from app.engine.quality_engine import QualityEngine

    # 1. Kiểm thử trực tiếp hàm tính toán tất định
    test_matrix = [
        [4.0, 5.0, 4.0, 5.0],
        [3.0, 4.0, 4.0, 4.0],
        [5.0, 5.0, 5.0, 5.0],
        [2.0, 3.0, 2.0, 3.0],
        [4.0, 4.0, 5.0, 4.0],
        [3.0, 3.0, 3.0, 4.0],
        [5.0, 4.0, 5.0, 5.0],
        [4.0, 5.0, 4.0, 4.0],
    ]
    meta = [
        {"id": "q1", "title": "Hài lòng 1"},
        {"id": "q2", "title": "Hài lòng 2"},
        {"id": "q3", "title": "Hài lòng 3"},
        {"id": "q4", "title": "Hài lòng 4"},
    ]
    rel = QualityEngine.compute_detailed_reliability(test_matrix, meta)
    assert rel["is_sufficient"] is True
    assert rel["cronbach_alpha"] is not None
    assert rel["cronbach_alpha"] > 0.80
    assert rel["standardized_alpha"] is not None
    assert rel["k_items"] == 4
    assert rel["n_samples"] == 8
    assert len(rel["item_statistics"]) == 4
    for item in rel["item_statistics"]:
        assert "corrected_item_total_correlation" in item
        assert "alpha_if_item_deleted" in item
        assert item["corrected_item_total_correlation"] > 0.40
        assert item["status"] in ("GOOD", "ACCEPTABLE")

    # 2. Kiểm thử API qua endpoint
    # Tạo khảo sát có 3 câu hỏi rating
    s_res = client.post("/api/surveys", json={
        "title": "Khảo sát Thang Đo Likert Tâm Trắc Học",
        "description": "Kiểm tra tính nhất quán nội tại của thang đo"
    })
    assert s_res.status_code == 201
    survey_id = s_res.json()["id"]

    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "order_index": 0,
                "question_type": "rating",
                "title": "Chất lượng sản phẩm",
                "is_required": True,
                "options": []
            },
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Chất lượng dịch vụ",
                "is_required": True,
                "options": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Giá trị nhận được",
                "is_required": True,
                "options": []
            }
        ]
    })
    client.post(f"/api/surveys/{survey_id}/publish")
    s_data = client.get(f"/api/surveys/{survey_id}").json()
    q_ids = [q["id"] for q in s_data["questions"]]
    slug = s_data["public_slug"]

    # Nạp 10 phản hồi có tính nhất quán cao
    from datetime import datetime, timezone, timedelta
    now_ts = datetime.now(timezone.utc)
    for idx in range(10):
        base_score = 3 + (idx % 3)
        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now_ts - timedelta(seconds=120 - idx * 2)).isoformat(),
            "submitted_at": (now_ts - timedelta(seconds=60 - idx)).isoformat(),
            "client_metadata": {"device_id": f"rel_device_{idx}"},
            "answers": {
                q_ids[0]: base_score,
                q_ids[1]: base_score,
                q_ids[2]: base_score
            }
        })
        assert sub_res.status_code == 201

    # Gọi API phân tích độ tin cậy thang đo
    api_res = client.get(f"/api/surveys/{survey_id}/analytics/reliability")
    assert api_res.status_code == 200
    res_data = api_res.json()

    assert res_data["is_sufficient"] is True
    assert res_data["k_items"] == 3
    assert res_data["n_samples"] == 10
    assert res_data["cronbach_alpha"] is not None
    assert res_data["cronbach_alpha"] >= 0.70
    assert len(res_data["item_statistics"]) == 3
    assert "interpretation" in res_data
    assert "academic_rating" in res_data





