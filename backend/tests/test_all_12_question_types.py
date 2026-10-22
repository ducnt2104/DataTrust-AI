import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.engine.quality_engine import QualityEngine

client = TestClient(app)

def test_quality_engine_ranking_normalization():
    """Kiểm tra normalize_value cho câu hỏi ranking bảo toàn thứ tự ưu tiên."""
    ranking_order_1 = ["option_A", "option_B", "option_C"]
    ranking_order_2 = ["option_C", "option_B", "option_A"]
    
    norm1 = QualityEngine.normalize_value(ranking_order_1, "ranking")
    norm2 = QualityEngine.normalize_value(ranking_order_2, "ranking")
    
    assert norm1 == "option_a>option_b>option_c"
    assert norm2 == "option_c>option_b>option_a"
    assert norm1 != norm2, "Hai thứ tự xếp hạng đối nghịch không được bằng nhau!"

def test_quality_engine_matrix_straightlining():
    """Kiểm tra QualityEngine phát hiện straightlining trên câu hỏi dạng matrix."""
    questions = [
        {
            "id": "q_matrix",
            "question_type": "matrix",
            "title": "Đánh giá các khía cạnh dịch vụ",
            "options": {
                "rows": ["Tốc độ", "Chất lượng", "Thái độ", "Giá cả"],
                "columns": ["Rất kém", "Kém", "Bình thường", "Tốt", "Rất tốt"]
            }
        }
    ]
    
    # Người trả lời chọn "Rất tốt" cho toàn bộ 4 hàng (100% straightlining)
    answers_straightline = {
        "q_matrix": {
            "Tốc độ": "Rất tốt",
            "Chất lượng": "Rất tốt",
            "Thái độ": "Rất tốt",
            "Giá cả": "Rất tốt"
        }
    }
    
    result = QualityEngine.analyze_response(
        new_answers=answers_straightline,
        questions=questions,
        prior_responses=[],
        duration_seconds=30.0
    )
    
    straightlining_flags = [f for f in result["flags"] if f["code"] == "FLAG_STRAIGHTLINING"]
    assert len(straightlining_flags) > 0, "Phải phát hiện Straightlining khi respondent chọn cùng 1 cột cho tất cả các hàng trong matrix!"
    assert straightlining_flags[0]["details"]["straightline_ratio"] == 1.0

def test_all_12_question_types_survey_lifecycle():
    """Tạo khảo sát chứa đầy đủ 12 loại câu hỏi, xuất bản, gửi phản hồi và phân tích analytics."""
    # 1. Tạo khảo sát mới
    res = client.post("/api/surveys", json={
        "title": "Khảo sát Tổng hợp 12 Dạng Câu Hỏi DataTrust AI",
        "description": "Kiểm thử toàn diện 12 question types trong hệ thống"
    })
    assert res.status_code == 201
    survey_id = res.json()["id"]
    slug = res.json()["public_slug"]

    # 2. Cập nhật câu hỏi với đầy đủ 12 loại
    questions = [
        {
            "id": "q1_single",
            "question_type": "single_choice",
            "title": "Bạn biết đến DataTrust qua kênh nào?",
            "is_required": True,
            "options": [{"id": "fb", "label": "Facebook"}, {"id": "web", "label": "Website"}]
        },
        {
            "id": "q2_multi",
            "question_type": "multiple_choice",
            "title": "Các công cụ bạn thường sử dụng?",
            "is_required": False,
            "options": [{"id": "sheets", "label": "Google Sheets"}, {"id": "excel", "label": "Excel"}]
        },
        {
            "id": "q3_short",
            "question_type": "short_text",
            "title": "Họ và tên của bạn?",
            "is_required": True,
            "options": []
        },
        {
            "id": "q4_long",
            "question_type": "long_text",
            "title": "Góp ý cải tiến chất lượng khảo sát?",
            "is_required": False,
            "options": []
        },
        {
            "id": "q5_number",
            "question_type": "number",
            "title": "Số lượng khảo sát bạn thực hiện mỗi tháng?",
            "is_required": False,
            "options": []
        },
        {
            "id": "q6_rating",
            "question_type": "rating",
            "title": "Đánh giá mức độ hài lòng về giao diện?",
            "is_required": True,
            "options": []
        },
        {
            "id": "q7_scale",
            "question_type": "linear_scale",
            "title": "Thang đo độ tin cậy từ 1 đến 10",
            "is_required": False,
            "options": []
        },
        {
            "id": "q8_dropdown",
            "question_type": "dropdown",
            "title": "Khu vực sinh sống?",
            "is_required": True,
            "options": [{"id": "hn", "label": "Hà Nội"}, {"id": "hcm", "label": "TP. Hồ Chí Minh"}]
        },
        {
            "id": "q9_date",
            "question_type": "date",
            "title": "Ngày bắt đầu sử dụng sản phẩm?",
            "is_required": False,
            "options": []
        },
        {
            "id": "q10_likert",
            "question_type": "likert",
            "title": "DataTrust AI trực quan và dễ sử dụng",
            "is_required": True,
            "options": [
                {"id": "1", "label": "1 - Hoàn toàn không đồng ý"},
                {"id": "2", "label": "2 - Không đồng ý"},
                {"id": "3", "label": "3 - Trung lập"},
                {"id": "4", "label": "4 - Đồng ý"},
                {"id": "5", "label": "5 - Hoàn toàn đồng ý"}
            ]
        },
        {
            "id": "q11_matrix",
            "question_type": "matrix",
            "title": "Đánh giá các khía cạnh dịch vụ",
            "is_required": True,
            "options": {
                "rows": ["Tốc độ tải", "Bảo mật", "Hỗ trợ khách hàng"],
                "columns": ["Kém", "Trung bình", "Tốt", "Xuất sắc"]
            }
        },
        {
            "id": "q12_ranking",
            "question_type": "ranking",
            "title": "Sắp xếp độ ưu tiên của các tính năng bạn muốn có:",
            "is_required": True,
            "options": [
                {"id": "feat_ai", "label": "AI Quality Audit"},
                {"id": "feat_export", "label": "Export CSV/Excel"},
                {"id": "feat_branch", "label": "Branching Logic"}
            ]
        }
    ]

    put_res = client.put(f"/api/surveys/{survey_id}", json={"questions": questions})
    assert put_res.status_code == 200

    # 3. Xuất bản khảo sát
    pub_res = client.post(f"/api/surveys/{survey_id}/publish")
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "published"

    # 4. Gửi 5 phản hồi thực qua Public Endpoint
    now = datetime.now(timezone.utc)
    for i in range(5):
        ans = {
            "q1_single": "fb" if i % 2 == 0 else "web",
            "q2_multi": ["sheets"] if i % 2 == 0 else ["sheets", "excel"],
            "q3_short": f"Nguyen Van {chr(65 + i)}",
            "q4_long": f"Góp ý chi tiết và xây dựng số {i+1} từ người dùng thực tế.",
            "q5_number": 10 + i * 2,
            "q6_rating": (i % 5) + 1,
            "q7_scale": (i * 2) % 10 + 1,
            "q8_dropdown": "hn" if i % 2 == 0 else "hcm",
            "q9_date": "2026-10-22",
            "q10_likert": str((i % 5) + 1),
            "q11_matrix": {
                "Tốc độ tải": ["Tốt", "Xuất sắc", "Tốt", "Trung bình", "Xuất sắc"][i],
                "Bảo mật": ["Xuất sắc", "Xuất sắc", "Tốt", "Xuất sắc", "Tốt"][i],
                "Hỗ trợ khách hàng": ["Trung bình", "Tốt", "Xuất sắc", "Tốt", "Xuất sắc"][i]
            },
            "q12_ranking": [
                "feat_ai",
                "feat_export",
                "feat_branch"
            ] if i % 2 == 0 else [
                "feat_branch",
                "feat_ai",
                "feat_export"
            ]
        }

        sub_res = client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": (now - timedelta(seconds=60)).isoformat(),
            "submitted_at": now.isoformat(),
            "answers": ans
        })
        assert sub_res.status_code == 201, f"Failed to submit: {sub_res.text}"

    # 5. Kiểm tra Analytics
    an_res = client.get(f"/api/surveys/{survey_id}/analytics")
    assert an_res.status_code == 200
    data = an_res.json()
    assert data["total_responses"] == 5
    assert data["is_sample_size_sufficient"] is True

    # 6. Kiểm tra Matrix và Ranking trong câu hỏi thống kê
    q_stats_map = {qs["question_id"]: qs for qs in data["questions_analytics"]}
    
    # Kiểm tra Matrix
    matrix_stat = q_stats_map.get("q11_matrix")
    assert matrix_stat is not None
    assert matrix_stat["stats_summary"] is not None
    matrix_dist = matrix_stat["stats_summary"]["matrix_distribution"]
    assert "Tốc độ tải" in matrix_dist
    assert "Bảo mật" in matrix_dist

    # Kiểm tra Ranking
    ranking_stat = q_stats_map.get("q12_ranking")
    assert ranking_stat is not None
    assert ranking_stat["stats_summary"] is not None
    ranking_avgs = ranking_stat["stats_summary"]["ranking_averages"]
    assert len(ranking_avgs) == 3
    # Mỗi item ranking phải có avg_rank > 0
    for item_label, avg_rank in ranking_avgs.items():
        assert avg_rank > 0
