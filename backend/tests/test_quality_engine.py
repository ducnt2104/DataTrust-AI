import pytest
from app.engine.quality_engine import QualityEngine

@pytest.fixture
def sample_questions():
    return [
        {
            "id": "q1",
            "question_type": "single_choice",
            "title": "Giới tính của bạn?",
            "options": [{"id": "male", "label": "Nam"}, {"id": "female", "label": "Nữ"}]
        },
        {
            "id": "q2",
            "question_type": "single_choice",
            "title": "Bạn có đang đi làm không?",
            "options": [{"id": "yes", "label": "Có"}, {"id": "no", "label": "Không"}]
        },
        {
            "id": "q3",
            "question_type": "likert",
            "title": "Mức độ hài lòng về lương thưởng:",
            "options": [{"id": "1", "label": "1"}, {"id": "5", "label": "5"}]
        },
        {
            "id": "q4",
            "question_type": "likert",
            "title": "Mức độ hài lòng về môi trường:",
            "options": [{"id": "1", "label": "1"}, {"id": "5", "label": "5"}]
        },
        {
            "id": "q5",
            "question_type": "likert",
            "title": "Mức độ hài lòng về đồng nghiệp:",
            "options": [{"id": "1", "label": "1"}, {"id": "5", "label": "5"}]
        },
        {
            "id": "q6",
            "question_type": "likert",
            "title": "Mức độ hài lòng về sếp:",
            "options": [{"id": "1", "label": "1"}, {"id": "5", "label": "5"}]
        },
        {
            "id": "q7",
            "question_type": "long_text",
            "title": "Góp ý thêm:",
            "options": []
        }
    ]

def test_exact_duplicate_detection(sample_questions):
    prior_responses = [
        {
            "id": "prior_1",
            "answers": {"q1": "male", "q2": "yes", "q3": "4", "q4": "4", "q5": "4", "q6": "4"}
        }
    ]
    new_answers = {"q1": "male", "q2": "yes", "q3": "4", "q4": "4", "q5": "4", "q6": "4"}
    
    result = QualityEngine.analyze_response(
        new_answers=new_answers,
        duration_seconds=60.0,
        questions=sample_questions,
        prior_responses=prior_responses
    )
    
    assert result["score_dup"] == 100.0
    assert result["risk_level"] == "high"
    assert any(f["code"] == "FLAG_EXACT_DUPLICATE" for f in result["flags"])
    assert result["closest_match_response_id"] == "prior_1"

def test_straightlining_detection(sample_questions):
    # Người trả lời chọn cùng mức "5" cho toàn bộ 4 câu Likert
    new_answers = {"q1": "female", "q2": "yes", "q3": "5", "q4": "5", "q5": "5", "q6": "5"}
    
    result = QualityEngine.analyze_response(
        new_answers=new_answers,
        duration_seconds=45.0,
        questions=sample_questions,
        prior_responses=[]
    )
    
    assert result["score_pattern"] >= 80.0
    assert any(f["code"] == "FLAG_STRAIGHTLINING" for f in result["flags"])

def test_speeding_detection(sample_questions):
    # 7 câu hỏi nhưng chỉ làm trong 2 giây
    new_answers = {"q1": "male", "q2": "no", "q3": "3", "q4": "4", "q5": "2", "q6": "5"}
    
    result = QualityEngine.analyze_response(
        new_answers=new_answers,
        duration_seconds=2.0,
        questions=sample_questions,
        prior_responses=[]
    )
    
    assert result["score_speed"] >= 80.0
    assert any(f["code"] == "FLAG_EXTREME_SPEEDING" for f in result["flags"])

def test_logic_contradiction_detection():
    questions = [
        {
            "id": "has_kids",
            "question_type": "single_choice",
            "title": "Bạn đã có con chưa?",
            "options": [{"id": "yes", "label": "Có"}, {"id": "no", "label": "Chưa"}]
        },
        {
            "id": "kid_count",
            "question_type": "number",
            "title": "Số lượng con của bạn?",
            "logic_rules": [{"depends_on_question_id": "has_kids", "operator": "equals", "value": "yes", "action": "show"}]
        }
    ]
    
    # Trả lời "no" (chưa có con), nhưng vẫn điền số lượng con = 3
    new_answers = {"has_kids": "no", "kid_count": "3"}
    
    result = QualityEngine.analyze_response(
        new_answers=new_answers,
        duration_seconds=30.0,
        questions=questions,
        prior_responses=[]
    )
    
    assert result["score_logic"] >= 80.0
    assert any(f["code"] == "FLAG_LOGIC_CONTRADICTION" for f in result["flags"])

def test_clean_response_low_risk(sample_questions):
    # Phản hồi đa dạng, thời gian hợp lý (40 giây), không trùng lặp
    new_answers = {"q1": "male", "q2": "yes", "q3": "2", "q4": "4", "q5": "3", "q6": "5", "q7": "Môi trường công ty rất thân thiện"}
    
    result = QualityEngine.analyze_response(
        new_answers=new_answers,
        duration_seconds=40.0,
        questions=sample_questions,
        prior_responses=[]
    )
    
    assert result["composite_score"] < 40.0
    assert result["risk_level"] == "low"
    assert len(result["flags"]) == 0
