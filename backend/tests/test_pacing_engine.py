import pytest
from app.engine.pacing_engine import CognitivePacingEngine

def test_pacing_engine_word_count():
    assert CognitivePacingEngine._count_words("Khảo sát mức độ hài lòng khách hàng") == 8
    assert CognitivePacingEngine._count_words("What is your primary occupation?") == 5
    assert CognitivePacingEngine._count_words("") == 0
    assert CognitivePacingEngine._count_words(None) == 0

def test_pacing_engine_single_question_burden():
    # Câu hỏi ngắn gọn đơn giản
    q_simple = {
        "id": "q1",
        "order_index": 1,
        "title": "Giới tính của bạn",
        "description": "",
        "question_type": "single_choice",
        "options": ["Nam", "Nữ", "Khác"]
    }
    res_simple = CognitivePacingEngine.calculate_question_cognitive_burden(q_simple)
    assert res_simple["title_words"] == 4
    assert res_simple["num_options"] == 3
    assert res_simple["cognitive_burden_score"] < 40.0
    assert res_simple["burden_tier"] in ("Low", "Moderate")
    assert len(res_simple["risk_factors"]) == 0

    # Câu hỏi quá tải (Miller's law > 7 options, prompt dài > 35 từ)
    long_title = "Vui lòng cho biết bạn thường xuyên sử dụng những dịch vụ nào dưới đây trong hoạt động công việc hàng ngày của bạn tại cơ quan hoặc văn phòng nghiên cứu phát triển công nghệ cao của đơn vị?"
    q_overloaded = {
        "id": "q2",
        "order_index": 2,
        "title": long_title,
        "description": "Đọc kỹ từng phương án",
        "question_type": "single_choice",
        "options": [
            "Dịch vụ đám mây AWS", "Dịch vụ Google Cloud", "Dịch vụ Microsoft Azure",
            "Dịch vụ Viettel IDC", "Dịch vụ FPT Cloud", "Dịch vụ VNPT SmartCloud",
            "Máy chủ cục bộ On-Premise", "Hạ tầng lai Hybrid Cloud", "Khác (ghi rõ)"
        ]
    }
    res_over = CognitivePacingEngine.calculate_question_cognitive_burden(q_overloaded)
    assert res_over["title_words"] > 30
    assert res_over["num_options"] == 9
    assert res_over["cognitive_burden_score"] >= 60.0
    assert len(res_over["risk_factors"]) >= 1
    assert any("Miller" in rf for rf in res_over["risk_factors"])

def test_pacing_engine_survey_level_analysis():
    questions = [
        {
            "id": "q1",
            "order_index": 1,
            "title": "Giới tính",
            "question_type": "single_choice",
            "options": ["Nam", "Nữ"]
        },
        {
            "id": "q2",
            "order_index": 2,
            "title": "Mức độ hài lòng chung",
            "question_type": "rating",
            "options": ["1", "2", "3", "4", "5"]
        }
    ]

    # Kịch bản 1: Nhóm trả lời quá nhanh (Severe Speeding)
    fast_durations = [1.2, 1.5, 2.0, 1.8]
    res_fast = CognitivePacingEngine.analyze_survey_pacing(
        survey_title="Khảo sát ngắn",
        questions=questions,
        durations=fast_durations
    )
    sl = res_fast["survey_level"]
    assert sl["actual_sample_size"] == 4
    assert sl["overall_pacing_ratio"] < 0.65
    assert sl["respondent_pacing_distribution"]["severe_speeding"] > 0
    assert "apa_interpretation" in sl

    # Kịch bản 2: Nhóm trả lời nhịp độ chuẩn (Optimal)
    expected_sec = sl["expected_reading_seconds"]
    normal_durations = [expected_sec * 0.9, expected_sec * 1.1, expected_sec * 1.0]
    res_norm = CognitivePacingEngine.analyze_survey_pacing(
        survey_title="Khảo sát ngắn",
        questions=questions,
        durations=normal_durations
    )
    assert res_norm["survey_level"]["engagement_level"] == "Optimal Cognitive Engagement"
    assert res_norm["survey_level"]["overall_pacing_ratio"] >= 0.65
