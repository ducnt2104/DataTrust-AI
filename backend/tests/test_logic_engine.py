"""
Unit tests for SurveyLogicEngine (DAG Analysis, Cycle Detection & Flow Simulation)
"""

import pytest
from app.engine.logic_engine import SurveyLogicEngine

def test_linear_survey_optimal():
    questions = [
        {"id": "q1", "order_index": 0, "title": "Tuổi", "logic_rules": []},
        {"id": "q2", "order_index": 1, "title": "Giới tính", "logic_rules": []},
        {"id": "q3", "order_index": 2, "title": "Nghề nghiệp", "logic_rules": []}
    ]
    report = SurveyLogicEngine.analyze_survey_logic(questions)
    assert report["is_valid"] is True
    assert report["health_score"] == 100.0
    assert report["status"] == "OPTIMAL"
    assert len(report["issues"]) == 0
    assert report["topology"]["node_count"] == 3
    assert report["topology"]["edge_count"] == 2
    assert report["topology"]["cyclomatic_complexity"] == 1

def test_dangling_reference_detection():
    questions = [
        {"id": "q1", "order_index": 0, "title": "Câu 1", "logic_rules": []},
        {
            "id": "q2",
            "order_index": 1,
            "title": "Câu 2",
            "logic_rules": [
                {"depends_on_question_id": "nonexistent_q99", "operator": "equals", "value": "A", "action": "show"}
            ]
        }
    ]
    report = SurveyLogicEngine.analyze_survey_logic(questions)
    assert report["is_valid"] is False
    assert report["status"] == "CRITICAL"
    dangling = [i for i in report["issues"] if i["type"] == "DANGLING_REF"]
    assert len(dangling) == 1
    assert dangling[0]["question_id"] == "q2"

def test_order_inversion_detection():
    questions = [
        {
            "id": "q1",
            "order_index": 0,
            "title": "Câu 1",
            "logic_rules": [
                {"depends_on_question_id": "q2", "operator": "equals", "value": "Có", "action": "show"}
            ]
        },
        {"id": "q2", "order_index": 1, "title": "Câu 2", "logic_rules": []}
    ]
    report = SurveyLogicEngine.analyze_survey_logic(questions)
    inversions = [i for i in report["issues"] if i["type"] == "ORDER_INVERSION"]
    assert len(inversions) == 1
    assert inversions[0]["question_id"] == "q1"
    assert report["status"] == "WARNING"

def test_circular_dependency_cycle_detection():
    # q1 depends on q2, q2 depends on q3, q3 depends on q1
    questions = [
        {
            "id": "q1",
            "order_index": 0,
            "title": "Câu 1",
            "logic_rules": [{"depends_on_question_id": "q3", "operator": "equals", "value": "A", "action": "show"}]
        },
        {
            "id": "q2",
            "order_index": 1,
            "title": "Câu 2",
            "logic_rules": [{"depends_on_question_id": "q1", "operator": "equals", "value": "B", "action": "show"}]
        },
        {
            "id": "q3",
            "order_index": 2,
            "title": "Câu 3",
            "logic_rules": [{"depends_on_question_id": "q2", "operator": "equals", "value": "C", "action": "show"}]
        }
    ]
    report = SurveyLogicEngine.analyze_survey_logic(questions)
    assert report["is_valid"] is False
    assert report["status"] == "CRITICAL"
    cycles = [i for i in report["issues"] if i["type"] == "CYCLE"]
    assert len(cycles) >= 1
    assert any("q1" in node["id"] for node in report["nodes"] if node["status"] == "cycle")

def test_contradictory_rules_detection():
    questions = [
        {"id": "q1", "order_index": 0, "title": "Bạn có xe máy không?", "logic_rules": []},
        {
            "id": "q2",
            "order_index": 1,
            "title": "Hãng xe máy",
            "logic_rules": [
                {"depends_on_question_id": "q1", "operator": "equals", "value": "Có", "action": "show"},
                {"depends_on_question_id": "q1", "operator": "equals", "value": "Không", "action": "show"}
            ]
        }
    ]
    report = SurveyLogicEngine.analyze_survey_logic(questions)
    contradictions = [i for i in report["issues"] if i["type"] == "CONTRADICTION"]
    assert len(contradictions) == 1
    assert contradictions[0]["question_id"] == "q2"

def test_simulate_respondent_flow():
    questions = [
        {"id": "q1", "order_index": 0, "title": "Bạn có nuôi thú cưng không?", "logic_rules": []},
        {
            "id": "q2",
            "order_index": 1,
            "title": "Bạn nuôi chó hay mèo?",
            "logic_rules": [
                {"depends_on_question_id": "q1", "operator": "equals", "value": "Có", "action": "show"}
            ]
        },
        {"id": "q3", "order_index": 2, "title": "Cảm ơn bạn", "logic_rules": []}
    ]

    # Scenario 1: Respondent has a pet
    flow1 = SurveyLogicEngine.simulate_respondent_flow(questions, {"q1": "Có"})
    assert "q2" in flow1["visible_questions"]
    assert flow1["visible_count"] == 3
    assert flow1["completion_ratio"] == 100.0

    # Scenario 2: Respondent does NOT have a pet
    flow2 = SurveyLogicEngine.simulate_respondent_flow(questions, {"q1": "Không"})
    assert "q2" in flow2["hidden_questions"]
    assert flow2["visible_count"] == 2
    assert "q2" in flow2["skipped_reasons"]
    assert flow2["completion_ratio"] == 66.7
