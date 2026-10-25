"""
Unit tests for Rasch Model & Item Response Theory (IRT) Engine
"""

import pytest
from app.engine.rasch_engine import RaschEngine


def test_binarize_response_matrix():
    raw_responses = [
        {"q1": 5, "q2": "Nam", "q3": True, "q4": "Không đồng ý"},
        {"q1": 2, "q2": "Nữ", "q3": False, "q4": "Rất đồng ý"},
        {"q1": 4, "q2": "Nam", "q3": True, "q4": "Đồng ý"}
    ]
    q_types = {
        "q1": "likert",
        "q2": "single_choice",
        "q3": "boolean",
        "q4": "likert"
    }
    valid_ids, matrix = RaschEngine.binarize_response_matrix(
        raw_responses=raw_responses,
        question_ids=["q1", "q2", "q3", "q4"],
        question_types=q_types
    )
    assert valid_ids == ["q1", "q2", "q3", "q4"]
    assert len(matrix) == 3
    # resp 0: q1 (5) -> 1, q2 ("Nam") -> 1, q3 (True) -> 1, q4 ("Không đồng ý") -> 0
    assert matrix[0] == [1, 1, 1, 0]
    # resp 1: q1 (2) -> 0, q2 ("Nữ") -> 1, q3 (False) -> 0, q4 ("Rất đồng ý") -> 1
    assert matrix[1] == [0, 1, 0, 1]


def test_run_rasch_jmle_calibration():
    # 6 respondents, 4 items with varying difficulty
    # Item 0: easy (mostly 1s)
    # Item 1: medium
    # Item 2: hard (mostly 0s)
    # Item 3: medium
    matrix = [
        [1, 1, 0, 1],
        [1, 1, 1, 1],
        [1, 0, 0, 1],
        [1, 0, 0, 0],
        [0, 0, 0, 0],
        [1, 1, 0, 0]
    ]

    res = RaschEngine.run_rasch_jmle(matrix=matrix, max_iterations=30)
    assert res["person_count"] == 6
    assert res["item_count"] == 4
    assert len(res["item_difficulty"]) == 4

    # Mean difficulty must be zero due to centering constraint
    mean_diff = sum(res["item_difficulty"]) / 4.0
    assert abs(mean_diff) < 0.05

    # Item 0 (easy) should have lower difficulty than Item 2 (hard)
    # Since higher theta / easier item has lower logit difficulty b
    assert res["item_difficulty"][0] < res["item_difficulty"][2]

    # Infit and outfit MNSQ should be positive
    assert all(mnsq > 0 for mnsq in res["item_infit_mnsq"])
    assert all(mnsq > 0 for mnsq in res["item_outfit_mnsq"])

    # Separation reliability in [0, 1]
    assert 0.0 <= res["item_reliability"] <= 1.0


def test_generate_wright_map_buckets():
    person_thetas = [-2.0, -1.0, 0.0, 0.2, 1.5, 2.5]
    items = [
        {"item_code": "Q1", "difficulty_logit": -1.5},
        {"item_code": "Q2", "difficulty_logit": 0.0},
        {"item_code": "Q3", "difficulty_logit": 1.8}
    ]

    buckets = RaschEngine.generate_wright_map_buckets(
        person_thetas=person_thetas,
        item_difficulties=items,
        min_logit=-2.0,
        max_logit=2.0,
        step=1.0
    )
    assert len(buckets) >= 4
    # Check that items appear in respective logit intervals
    q2_found = any("Q2" in b["items"] and b["logit_level"] == 0.0 for b in buckets)
    assert q2_found
