import pytest
from app.engine.translation_engine import TranslationEngine

def test_translation_engine_phrases():
    # Likert CSAT
    assert TranslationEngine._translate_phrase("Rất hài lòng", "en") == "Very Satisfied"
    assert TranslationEngine._translate_phrase("Không hài lòng", "en") == "Dissatisfied"
    assert TranslationEngine._translate_phrase("Bình thường", "en") == "Neutral"

    # Likert Agreement
    assert TranslationEngine._translate_phrase("Hoàn toàn đồng ý", "en") == "Strongly Agree"
    assert TranslationEngine._translate_phrase("Không đồng ý", "en") == "Disagree"

    # Demographics
    assert TranslationEngine._translate_phrase("Giới tính của bạn", "en") == "What is your gender?"
    assert TranslationEngine._translate_phrase("Nam", "en") == "Male"
    assert TranslationEngine._translate_phrase("Nữ", "en") == "Female"
    assert TranslationEngine._translate_phrase("Miền Bắc", "en") == "Northern Region"

def test_translation_engine_auto_translate_survey():
    questions = [
        {
            "id": "q_gender",
            "title": "Giới tính",
            "question_type": "single_choice",
            "options": ["Nam", "Nữ", "Khác"]
        },
        {
            "id": "q_satisfaction",
            "title": "Mức độ hài lòng với dịch vụ",
            "question_type": "rating",
            "options": ["Rất không hài lòng", "Không hài lòng", "Bình thường", "Hài lòng", "Rất hài lòng"]
        }
    ]

    res = TranslationEngine.auto_translate_survey(
        survey_title="Khảo sát ý kiến khách hàng",
        survey_desc="Mục đích nghiên cứu",
        survey_instructions="Vui lòng trả lời trung thực",
        questions=questions,
        target_lang="en"
    )

    assert res["language_code"] == "en"
    assert "Survey" in res["title"]
    assert "q_gender" in res["questions"]
    assert res["questions"]["q_gender"]["title"] == "Gender"
    assert res["questions"]["q_gender"]["options"] == ["Male", "Female", "Other"]

    assert "q_satisfaction" in res["questions"]
    assert "Very Satisfied" in res["questions"]["q_satisfaction"]["options"]
    assert "Very Dissatisfied" in res["questions"]["q_satisfaction"]["options"]
