import math
import re
from typing import Dict, List, Any, Optional, Tuple

class QualityEngine:
    """
    DataTrust AI Quality Assurance & Fraud Screening Engine.
    Thực hiện đánh giá chất lượng phản hồi đa tầng bằng các thuật toán tất định:
    - Layer A: Validation & Completeness
    - Layer B: Hamming Distance Vectorization (Trùng lặp / Gần trùng lặp)
    - Layer C: Response Pattern Anomalies (Straightlining, Shannon Entropy)
    - Layer D: Cross-Question Logic Consistency
    - Layer E: Timing & Submission Speed (Speeding detection)
    - Layer F: Open-Ended Text Repetition & Gibberish
    - Layer G: Composite Explainable Heuristic Risk Score (0 - 100)
    """

    DEFAULT_WEIGHTS = {
        "dup": 0.35,
        "pat": 0.25,
        "logic": 0.25,
        "speed": 0.15
    }

    @staticmethod
    def normalize_value(val: Any) -> str:
        """Chuẩn hóa giá trị trả lời để so sánh vector"""
        if val is None:
            return ""
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, list):
            # Với multiple choice hoặc ranking, sắp xếp để so sánh tập hợp
            cleaned = sorted([str(x).strip().lower() for x in val if x is not None])
            return "|".join(cleaned)
        if isinstance(val, dict):
            # Với matrix: sắp xếp key và value
            items = sorted([f"{k}:{v}" for k, v in val.items()])
            return ";".join(items)
        return str(val).strip().lower()

    @classmethod
    def analyze_response(
        cls,
        new_answers: Dict[str, Any],
        duration_seconds: float,
        questions: List[Dict[str, Any]],
        prior_responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Phân tích toàn diện một phản hồi mới đối chiếu với schema câu hỏi và tập phản hồi trước đó.
        """
        flags = []
        score_dup = 0.0
        score_pat = 0.0
        score_logic = 0.0
        score_speed = 0.0
        score_text = 0.0
        
        closest_match_id = None
        highest_similarity = 0.0

        # Lọc danh sách câu hỏi đóng để so sánh vector
        closed_q_ids = [
            q["id"] for q in questions
            if q.get("question_type") not in ("long_text", "short_text")
        ]
        
        # 1. LAYER B: So sánh trùng lặp và gần trùng lặp (Hamming distance)
        if closed_q_ids and prior_responses:
            new_vector = [cls.normalize_value(new_answers.get(qid)) for qid in closed_q_ids]
            
            for prior in prior_responses:
                prior_answers = prior.get("answers", {})
                prior_vector = [cls.normalize_value(prior_answers.get(qid)) for qid in closed_q_ids]
                
                # Tính khoảng cách Hamming
                matches = sum(1 for a, b in zip(new_vector, prior_vector) if a == b and a != "")
                valid_comparisons = sum(1 for a, b in zip(new_vector, prior_vector) if a != "" or b != "")
                
                if valid_comparisons > 0:
                    sim = matches / valid_comparisons
                    if sim > highest_similarity:
                        highest_similarity = sim
                        closest_match_id = prior.get("id")

            if highest_similarity >= 0.999:
                score_dup = 100.0
                flags.append({
                    "code": "FLAG_EXACT_DUPLICATE",
                    "severity": "CRITICAL",
                    "message": "Phản hồi có vector đáp án đóng trùng khớp 100% với một phản hồi đã gửi trước đó.",
                    "details": {"closest_response_id": closest_match_id, "similarity": 1.0}
                })
            elif highest_similarity >= 0.85:
                score_dup = highest_similarity * 90.0
                flags.append({
                    "code": "FLAG_NEAR_DUPLICATE",
                    "severity": "HIGH",
                    "message": f"Phản hồi gần trùng lặp ({highest_similarity * 100:.1f}%) với một phản hồi trước đó.",
                    "details": {"closest_response_id": closest_match_id, "similarity": round(highest_similarity, 3)}
                })
            elif highest_similarity >= 0.70:
                score_dup = 35.0
                flags.append({
                    "code": "FLAG_MODERATE_SIMILARITY",
                    "severity": "LOW",
                    "message": f"Độ tương đồng câu trả lời ở mức đáng chú ý ({highest_similarity * 100:.1f}%).",
                    "details": {"closest_response_id": closest_match_id, "similarity": round(highest_similarity, 3)}
                })

        # 2. LAYER C: Mẫu đáp án bất thường (Straightlining & Shannon Entropy)
        scale_q_ids = [
            q["id"] for q in questions
            if q.get("question_type") in ("linear_scale", "likert", "matrix")
        ]
        
        scale_answers = [
            cls.normalize_value(new_answers.get(qid))
            for qid in scale_q_ids
            if new_answers.get(qid) is not None and cls.normalize_value(new_answers.get(qid)) != ""
        ]

        if len(scale_answers) >= 4:
            # Kiểm tra Straightlining (chọn cùng 1 phương án liên tiếp)
            counts = {}
            for ans in scale_answers:
                counts[ans] = counts.get(ans, 0) + 1
            max_freq = max(counts.values()) if counts else 0
            straightline_ratio = max_freq / len(scale_answers)

            if straightline_ratio >= 0.85:
                score_pat = max(score_pat, 85.0)
                flags.append({
                    "code": "FLAG_STRAIGHTLINING",
                    "severity": "HIGH",
                    "message": f"Phát hiện mẫu điền thẳng (Straightlining): {straightline_ratio * 100:.0f}% câu hỏi thang đo chọn cùng một mức đánh giá.",
                    "details": {"straightline_ratio": round(straightline_ratio, 2), "total_scale_questions": len(scale_answers)}
                })
            elif straightline_ratio >= 0.70:
                score_pat = max(score_pat, 40.0)
                flags.append({
                    "code": "FLAG_REPETITIVE_PATTERN",
                    "severity": "MEDIUM",
                    "message": "Độ đa dạng câu trả lời thang đo thấp, có xu hướng chọn lặp lại một phương án.",
                    "details": {"straightline_ratio": round(straightline_ratio, 2)}
                })

            # Tính Shannon Entropy
            entropy = 0.0
            for count in counts.values():
                p = count / len(scale_answers)
                if p > 0:
                    entropy -= p * math.log2(p)
            
            # Nếu entropy quá thấp trên tập nhiều hơn 3 câu hỏi
            if len(scale_answers) >= 5 and entropy < 0.4:
                score_pat = max(score_pat, 75.0)
                flags.append({
                    "code": "FLAG_LOW_SHANNON_ENTROPY",
                    "severity": "MEDIUM",
                    "message": f"Entropy Shannon cực thấp ({entropy:.2f}), cho thấy câu trả lời thiếu tính đa dạng tự nhiên.",
                    "details": {"entropy": round(entropy, 2)}
                })

        # 3. LAYER D: Vi phạm logic câu hỏi chéo (Cross-question Logic Contradiction)
        for q in questions:
            qid = q["id"]
            rules = q.get("logic_rules", [])
            for rule in rules:
                dep_id = rule.get("depends_on_question_id")
                op = rule.get("operator", "equals")
                expected_val = rule.get("value")
                action = rule.get("action", "show")
                
                dep_ans = cls.normalize_value(new_answers.get(dep_id))
                exp_norm = cls.normalize_value(expected_val)
                curr_ans = new_answers.get(qid)
                
                condition_met = (dep_ans == exp_norm) if op == "equals" else (dep_ans != exp_norm)
                
                # Nếu action là 'show', nhưng condition KHÔNG met mà người dùng vẫn trả lời câu qid
                if action == "show" and not condition_met:
                    if curr_ans is not None and str(curr_ans).strip() != "":
                        score_logic = max(score_logic, 80.0)
                        flags.append({
                            "code": "FLAG_LOGIC_CONTRADICTION",
                            "severity": "HIGH",
                            "message": f"Câu hỏi '{q.get('title')}' được trả lời dù điều kiện phụ thuộc vào câu trước không thỏa mãn.",
                            "details": {"question_id": qid, "dependent_on": dep_id}
                        })

        # 4. LAYER E: Thời gian hoàn thành & Tốc độ làm bài (Speeding)
        total_questions = len(questions)
        min_expected_duration = max(5.0, total_questions * 2.2)  # Tối thiểu 2.2 giây/câu
        
        if duration_seconds > 0 and duration_seconds < min_expected_duration:
            ratio = duration_seconds / min_expected_duration
            if ratio < 0.4:
                score_speed = 90.0
                flags.append({
                    "code": "FLAG_EXTREME_SPEEDING",
                    "severity": "HIGH",
                    "message": f"Thời gian làm bài siêu tốc ({duration_seconds:.1f}s cho {total_questions} câu hỏi), người tham gia không đủ thời gian đọc hiểu.",
                    "details": {"duration": duration_seconds, "min_expected": min_expected_duration}
                })
            else:
                score_speed = 50.0
                flags.append({
                    "code": "FLAG_FAST_COMPLETION",
                    "severity": "MEDIUM",
                    "message": f"Thời gian làm bài nhanh bất thường ({duration_seconds:.1f}s so với chuẩn tối thiểu {min_expected_duration:.1f}s).",
                    "details": {"duration": duration_seconds, "min_expected": min_expected_duration}
                })

        # 5. LAYER F: Kiểm tra văn bản mở (Gibberish & Repetition)
        text_q_ids = [
            q["id"] for q in questions
            if q.get("question_type") in ("long_text", "short_text")
        ]
        for qid in text_q_ids:
            txt = str(new_answers.get(qid, "")).strip()
            if txt:
                # Kiểm tra ký tự lặp vô nghĩa (ví dụ: "aaaaaa", "111111", ".....", "asdfasdf")
                if len(txt) >= 4 and len(set(txt)) <= 2:
                    score_text = max(score_text, 75.0)
                    flags.append({
                        "code": "FLAG_GIBBERISH_TEXT",
                        "severity": "MEDIUM",
                        "message": f"Phát hiện văn bản có dấu hiệu vô nghĩa hoặc lặp ký tự đơn điệu: '{txt[:20]}...'",
                        "details": {"question_id": qid, "text_sample": txt[:30]}
                    })
                # Kiểm tra văn bản mở trùng hệt một phản hồi trước đó
                if prior_responses:
                    for prior in prior_responses:
                        prior_txt = str(prior.get("answers", {}).get(qid, "")).strip()
                        if len(txt) >= 15 and txt.lower() == prior_txt.lower():
                            score_text = max(score_text, 80.0)
                            flags.append({
                                "code": "FLAG_DUPLICATE_OPEN_TEXT",
                                "severity": "HIGH",
                                "message": "Câu trả lời mở trùng khớp nguyên văn với câu trả lời của một người tham gia khác.",
                                "details": {"question_id": qid, "matched_response_id": prior.get("id")}
                            })
                            break

        # 6. LAYER G: Tính điểm rủi ro tổng hợp (Composite Risk Score: 0 - 100)
        # Tái chuẩn hóa trọng số nếu một thành phần không áp dụng
        active_weights = {}
        total_w = 0.0

        active_weights["dup"] = cls.DEFAULT_WEIGHTS["dup"]
        total_w += cls.DEFAULT_WEIGHTS["dup"]

        if scale_q_ids:
            active_weights["pat"] = cls.DEFAULT_WEIGHTS["pat"]
            total_w += cls.DEFAULT_WEIGHTS["pat"]

        active_weights["logic"] = cls.DEFAULT_WEIGHTS["logic"]
        total_w += cls.DEFAULT_WEIGHTS["logic"]

        if duration_seconds > 0:
            active_weights["speed"] = cls.DEFAULT_WEIGHTS["speed"]
            total_w += cls.DEFAULT_WEIGHTS["speed"]

        raw_score = 0.0
        if total_w > 0:
            raw_score += (active_weights.get("dup", 0) / total_w) * score_dup
            raw_score += (active_weights.get("pat", 0) / total_w) * score_pat
            raw_score += (active_weights.get("logic", 0) / total_w) * score_logic
            raw_score += (active_weights.get("speed", 0) / total_w) * score_speed

        # Quy tắc ưu tiên cho các cờ cảnh báo đặc biệt nghiêm trọng (Overriding rules)
        if score_dup >= 100.0:
            raw_score = max(raw_score, 85.0)
        elif score_dup >= 85.0:
            raw_score = max(raw_score, 55.0)

        # Bổ sung phụ phí nếu có văn bản vô nghĩa/trùng lặp
        if score_text > 0:
            raw_score = max(raw_score, score_text * 0.7)

        composite_score = round(min(100.0, max(0.0, raw_score)), 1)
        
        if composite_score >= 70.0:
            risk_level = "high"
        elif composite_score >= 40.0:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "score_dup": round(score_dup, 1),
            "score_pattern": round(score_pat, 1),
            "score_logic": round(score_logic, 1),
            "score_speed": round(score_speed, 1),
            "score_text": round(score_text, 1),
            "composite_score": composite_score,
            "risk_level": risk_level,
            "flags": flags,
            "closest_match_response_id": closest_match_id,
            "highest_similarity": round(highest_similarity, 3)
        }
