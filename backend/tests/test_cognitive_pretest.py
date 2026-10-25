import os
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_PATH"] = "backend/data/test_datatrust.db"

from app.main import app
from app.database import init_db
from app.engine.cognitive_pretest_engine import CognitivePretestEngine

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists("backend/data/test_datatrust.db"):
        try:
            os.remove("backend/data/test_datatrust.db")
        except Exception:
            pass
    init_db("backend/data/test_datatrust.db")
    yield

client = TestClient(app)

def test_readability_computation():
    """Kiểm tra tính toán chỉ số Flesch Reading Ease và độ dài câu"""
    # 1. Văn bản ngắn gọn, phổ thông
    easy_text = "Bạn có thích đọc sách không? Khảo sát này rất ngắn."
    metrics_easy = CognitivePretestEngine.compute_readability_metrics(easy_text)
    assert metrics_easy["word_count"] > 0
    assert metrics_easy["flesch_reading_ease"] >= 50.0

    # 2. Văn bản rỗng
    empty_res = CognitivePretestEngine.compute_readability_metrics("")
    assert empty_res["readability_level"] == "EASY"
    assert empty_res["word_count"] == 0

def test_diagnose_question_ambiguities_all_classes():
    """Kiểm thử phát hiện đầy đủ 7 dạng lỗi thiết kế bảng hỏi học thuật"""
    # 1. Leading question
    q_lead = {
        "id": "q1",
        "title": "Sản phẩm của chúng tôi tuyệt vời thế nào đối với bạn?",
        "question_type": "single_choice",
        "options": [{"id": "1", "label": "Tốt"}, {"id": "2", "label": "Bình thường"}]
    }
    issues_lead = CognitivePretestEngine.diagnose_question_ambiguities(q_lead, 0)
    assert any(i["issue_type"] == "LEADING_QUESTION" for i in issues_lead)
    assert issues_lead[0]["auto_fix_title"] is not None

    # 2. Double-barreled question
    q_double = {
        "id": "q2",
        "title": "Bạn đánh giá chất lượng sản phẩm và thái độ phục vụ của nhân viên như thế nào?",
        "question_type": "rating",
        "options": []
    }
    issues_double = CognitivePretestEngine.diagnose_question_ambiguities(q_double, 1)
    assert any(i["issue_type"] == "DOUBLE_BARRELED" for i in issues_double)

    # 3. Double negative
    q_neg = {
        "id": "q3",
        "title": "Bạn có đồng ý rằng không thể không đổi mới chương trình học?",
        "question_type": "single_choice",
        "options": [{"id": "1", "label": "Đồng ý"}, {"id": "2", "label": "Không"}]
    }
    issues_neg = CognitivePretestEngine.diagnose_question_ambiguities(q_neg, 2)
    assert any(i["issue_type"] == "DOUBLE_NEGATIVE" for i in issues_neg)
    assert issues_neg[0]["severity"] == "CRITICAL"

    # 4. Vague quantifiers
    q_vague = {
        "id": "q4",
        "title": "Bạn sử dụng ứng dụng với tần suất như thế nào?",
        "question_type": "single_choice",
        "options": [
            {"id": "1", "label": "thường xuyên"},
            {"id": "2", "label": "thỉnh thoảng"},
            {"id": "3", "label": "hiếm khi"}
        ]
    }
    issues_vague = CognitivePretestEngine.diagnose_question_ambiguities(q_vague, 3)
    assert any(i["issue_type"] == "VAGUE_QUANTIFIER" for i in issues_vague)
    assert issues_vague[0]["suggested_options"] is not None

    # 5. Cognitive overload (word count > 35)
    long_title = " ".join(["từ_vựng_kiểm_định"] * 40) + "?"
    q_overload = {
        "id": "q5",
        "title": long_title,
        "question_type": "text",
        "options": []
    }
    issues_overload = CognitivePretestEngine.diagnose_question_ambiguities(q_overload, 4)
    assert any(i["issue_type"] == "COGNITIVE_OVERLOAD" for i in issues_overload)

    # 6. Insufficient options
    q_insufficient = {
        "id": "q6",
        "title": "Bạn có dự định tham gia sự kiện không?",
        "question_type": "single_choice",
        "options": [{"id": "1", "label": "Có"}]
    }
    issues_insufficient = CognitivePretestEngine.diagnose_question_ambiguities(q_insufficient, 5)
    assert any(i["issue_type"] == "INSUFFICIENT_OPTIONS" for i in issues_insufficient)

    # 7. Sensitive unprotected
    q_sensitive = {
        "id": "q7",
        "title": "Mức thu nhập hàng tháng của gia đình bạn là bao nhiêu?",
        "question_type": "single_choice",
        "options": [
            {"id": "1", "label": "Dưới 10 triệu"},
            {"id": "2", "label": "Trên 10 triệu"}
        ]
    }
    issues_sensitive = CognitivePretestEngine.diagnose_question_ambiguities(q_sensitive, 6)
    assert any(i["issue_type"] == "SENSITIVE_UNPROTECTED" for i in issues_sensitive)

def test_persona_simulation_and_fatigue_curve():
    """Kiểm thử mô phỏng 3 Persona nhân khẩu học và đường cong mệt mỏi nhận thức"""
    sample_questions = [
        {"id": f"q_{i}", "title": f"Câu hỏi đánh giá tiêu chí số {i}?", "question_type": "rating", "options": []}
        for i in range(1, 11)
    ]
    report = CognitivePretestEngine.run_pretest_audit(
        survey_id="test_sim",
        title="Khảo sát trải nghiệm học tập",
        questions=sample_questions
    )

    assert report["total_questions"] == 10
    assert report["design_quality_score"] > 80.0
    assert report["academic_grade"] in ("A+", "A")
    assert len(report["personas"]) == 3
    
    # Kiểm tra đặc tính của 3 persona
    p_ids = [p["persona_id"] for p in report["personas"]]
    assert "PERSONA_FAST_PACED" in p_ids
    assert "PERSONA_ELDERLY_PLAIN" in p_ids
    assert "PERSONA_ANALYTICAL_REVIEWER" in p_ids

    # Kiểm tra đường cong mệt mỏi
    curve = report["fatigue_curve"]
    assert len(curve) == 10
    assert curve[0]["cumulative_time_seconds"] < curve[-1]["cumulative_time_seconds"]
    assert curve[0]["fatigue_percentage"] <= curve[-1]["fatigue_percentage"]

def test_cognitive_pretest_api_endpoints():
    """Kiểm thử các endpoints API POST /api/surveys/{id}/cognitive-pretest và /api/ai/cognitive-pretest"""
    # 1. Tạo khảo sát mẫu
    create_res = client.post("/api/surveys", json={
        "title": "Khảo sát Khảo nghiệm Nhận thức Trực tuyến",
        "description": "Nghiên cứu thử nghiệm tiền xuất bản"
    })
    survey_id = create_res.json()["id"]

    client.put(f"/api/surveys/{survey_id}", json={
        "questions": [
            {
                "id": "q_lead",
                "question_type": "single_choice",
                "title": "Dịch vụ của chúng tôi tuyệt vời thế nào đối với bạn?",
                "is_required": True,
                "options": [{"id": "1", "label": "Tốt"}, {"id": "2", "label": "Bình thường"}]
            },
            {
                "id": "q_double",
                "question_type": "rating",
                "title": "Bạn đánh giá cơ sở vật chất và chương trình đào tạo ra sao?",
                "is_required": True,
                "options": []
            }
        ]
    })

    # 2. Gọi endpoint trên khảo sát đã lưu
    res_survey = client.post(f"/api/surveys/{survey_id}/cognitive-pretest")
    assert res_survey.status_code == 200
    report_survey = res_survey.json()
    assert report_survey["survey_id"] == survey_id
    assert report_survey["total_questions"] == 2
    assert report_survey["total_issues_count"] >= 2
    assert len(report_survey["personas"]) == 3

    # 3. Gọi endpoint trên bản thảo AI (chưa lưu CSDL)
    res_draft = client.post("/api/ai/cognitive-pretest", json={
        "survey_id": None,
        "title": "Bản thảo nghiên cứu",
        "questions": [
            {
                "id": "draft_q",
                "title": "Bạn có đồng ý rằng không thể không cải thiện hệ thống?",
                "question_type": "single_choice",
                "options": [{"id": "1", "label": "Đồng ý"}, {"id": "2", "label": "Không"}]
            }
        ]
    })
    assert res_draft.status_code == 200
    report_draft = res_draft.json()
    assert report_draft["total_questions"] == 1
    assert any(i["issue_type"] == "DOUBLE_NEGATIVE" for i in report_draft["issues"])
