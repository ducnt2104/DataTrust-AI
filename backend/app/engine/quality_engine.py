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
        "enum": 0.15,
        "speed": 0.15
    }

    @staticmethod
    def normalize_value(val: Any, q_type: str = "") -> str:
        """Chuẩn hóa giá trị trả lời để so sánh vector"""
        if val is None:
            return ""
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, list):
            if q_type == "ranking":
                # Đối với câu hỏi xếp hạng, thứ tự là thông tin quyết định
                cleaned = [str(x).strip().lower() for x in val if x is not None]
                return ">".join(cleaned)
            # Với multiple choice, sắp xếp để so sánh tập hợp
            cleaned = sorted([str(x).strip().lower() for x in val if x is not None])
            return "|".join(cleaned)
        if isinstance(val, dict):
            # Với matrix: sắp xếp key và value
            items = sorted([f"{k}:{v}" for k, v in val.items()])
            return ";".join(items)
        return str(val).strip().lower()

    @staticmethod
    def compute_benford_analysis(numbers: List[Any]) -> Dict[str, Any]:
        """
        Kiểm định Luật Benford (Benford's Law First-Digit Test) trên các câu hỏi số học
        để phát hiện số liệu ngụy tạo / bịa đặt bởi con người (Schräpler & Wagner 2012, AAPOR 2003).
        """
        digits = []
        for n in numbers:
            try:
                val = abs(float(n))
                if val > 0:
                    # Lấy chữ số đầu tiên khác 0
                    s = f"{val:.10e}"
                    first_digit = int(s[0])
                    if 1 <= first_digit <= 9:
                        digits.append(first_digit)
            except Exception:
                continue

        n_samples = len(digits)
        is_sample_sufficient = n_samples >= 30

        benford_probs = {d: math.log10(1.0 + 1.0 / d) for d in range(1, 10)}
        counts = {d: digits.count(d) for d in range(1, 10)}
        
        distribution = []
        chi_square = 0.0

        for d in range(1, 10):
            obs_cnt = counts[d]
            obs_pct = round((obs_cnt / n_samples * 100), 2) if n_samples > 0 else 0.0
            exp_pct = round(benford_probs[d] * 100, 2)
            exp_cnt = n_samples * benford_probs[d]
            
            if exp_cnt > 0:
                chi_square += ((obs_cnt - exp_cnt) ** 2) / exp_cnt

            distribution.append({
                "digit": d,
                "observed_count": obs_cnt,
                "observed_percentage": obs_pct,
                "benford_percentage": exp_pct,
                "difference": round(obs_pct - exp_pct, 2)
            })

        chi_square = round(chi_square, 2)
        is_anomalous = False
        significance_level = "Bình thường (Khớp quy luật tự nhiên)"
        if is_sample_sufficient:
            if chi_square >= 20.09:
                is_anomalous = True
                significance_level = "p < 0.01 (Độ lệch nghiêm trọng, nghi ngờ số liệu tự bịa đặt)"
            elif chi_square >= 15.51:
                is_anomalous = True
                significance_level = "p < 0.05 (Độ lệch có ý nghĩa thống kê)"

        return {
            "total_numeric_samples": n_samples,
            "is_sample_sufficient": is_sample_sufficient,
            "notice": None if is_sample_sufficient else f"Cần tối thiểu N >= 30 mẫu số liệu để kiểm định Benford đạt ý nghĩa thống kê (hiện có N = {n_samples}).",
            "chi_square_statistic": chi_square,
            "degrees_of_freedom": 8,
            "is_anomalous": is_anomalous,
            "significance_level": significance_level,
            "distribution": distribution
        }

    @classmethod
    def analyze_response(
        cls,
        new_answers: Dict[str, Any],
        duration_seconds: float,
        questions: List[Dict[str, Any]],
        prior_responses: List[Dict[str, Any]],
        enumerator_id: Optional[str] = None,
        quality_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Phân tích toàn diện một phản hồi mới đối chiếu với schema câu hỏi và tập phản hồi trước đó.
        """
        # Cấu hình độ nhạy kiểm định chất lượng (Sensitivity settings)
        q_settings = quality_settings or {}
        sensitivity_mode = q_settings.get("sensitivity", "standard")
        
        duplicate_threshold = 0.85
        straightline_threshold = 0.85
        speed_threshold_per_question = 2.2
        
        if sensitivity_mode == "strict":
            duplicate_threshold = 0.80
            straightline_threshold = 0.75
            speed_threshold_per_question = 2.8
        elif sensitivity_mode == "lenient":
            duplicate_threshold = 0.90
            straightline_threshold = 0.90
            speed_threshold_per_question = 1.5

        if "duplicate_threshold" in q_settings:
            try:
                duplicate_threshold = float(q_settings["duplicate_threshold"])
            except (ValueError, TypeError):
                pass
        if "straightline_threshold" in q_settings:
            try:
                straightline_threshold = float(q_settings["straightline_threshold"])
            except (ValueError, TypeError):
                pass
        if "speed_threshold_per_question" in q_settings:
            try:
                speed_threshold_per_question = float(q_settings["speed_threshold_per_question"])
            except (ValueError, TypeError):
                pass

        flags = []
        score_dup = 0.0
        score_pat = 0.0
        score_logic = 0.0
        score_speed = 0.0
        score_text = 0.0
        score_enum = 0.0
        
        closest_match_id = None
        highest_similarity = 0.0

        # Lọc danh sách câu hỏi đóng để so sánh vector
        closed_q_items = [
            q for q in questions
            if q.get("question_type") not in ("long_text", "short_text")
        ]
        
        # 1. LAYER B: So sánh trùng lặp và gần trùng lặp (Hamming distance)
        if closed_q_items and prior_responses:
            new_vector = [cls.normalize_value(new_answers.get(q["id"]), q.get("question_type", "")) for q in closed_q_items]
            
            for prior in prior_responses:
                prior_answers = prior.get("answers", {})
                prior_vector = [cls.normalize_value(prior_answers.get(q["id"]), q.get("question_type", "")) for q in closed_q_items]
                
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
            elif highest_similarity >= duplicate_threshold:
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

        # 2. LAYER C: Mẫu đáp án bất thường (Straightlining, Đường chéo, Zíc-zắc & Shannon Entropy)
        scale_answers = []
        for q in questions:
            qid = q["id"]
            qtype = q.get("question_type")
            if qtype in ("linear_scale", "likert"):
                val = new_answers.get(qid)
                if val is not None and str(val).strip() != "":
                    scale_answers.append(str(val).strip())
            elif qtype == "matrix":
                val = new_answers.get(qid)
                if isinstance(val, dict):
                    for row_col in val.values():
                        if row_col is not None and str(row_col).strip() != "":
                            scale_answers.append(str(row_col).strip())

        if len(scale_answers) >= 4:
            # Kiểm tra Straightlining (chọn cùng 1 phương án liên tiếp)
            counts = {}
            for ans in scale_answers:
                counts[ans] = counts.get(ans, 0) + 1
            max_freq = max(counts.values()) if counts else 0
            straightline_ratio = max_freq / len(scale_answers)

            if straightline_ratio >= straightline_threshold:
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

            # Chuyển đổi các câu trả lời thang đo sang dạng số để kiểm tra mẫu hình học (Geometric Pattern Detection)
            numeric_scale_vals = []
            for ans in scale_answers:
                try:
                    numeric_scale_vals.append(float(ans))
                except (ValueError, TypeError):
                    pass

            if len(numeric_scale_vals) >= 4:
                # A. Mẫu đường chéo / bậc thang tăng hoặc giảm liên tiếp (Monotonic Diagonal Pattern)
                # Ví dụ: 1 -> 2 -> 3 -> 4 -> 5 hoặc 5 -> 4 -> 3 -> 2 -> 1
                diffs = [round(numeric_scale_vals[i+1] - numeric_scale_vals[i], 2) for i in range(len(numeric_scale_vals) - 1)]
                is_all_inc = all(d == 1.0 for d in diffs)
                is_all_dec = all(d == -1.0 for d in diffs)

                if is_all_inc or is_all_dec:
                    score_pat = max(score_pat, 80.0)
                    direction_str = "tăng dần đều (1 -> 2 -> 3...)" if is_all_inc else "giảm dần đều (5 -> 4 -> 3...)"
                    flags.append({
                        "code": "FLAG_DIAGONAL_PATTERN",
                        "severity": "HIGH",
                        "message": f"Phát hiện mẫu đường chéo bậc thang ({direction_str}): Thao tác tích lướt qua loa theo đường chéo.",
                        "details": {"pattern_type": "monotonic_diagonal", "total_steps": len(numeric_scale_vals)}
                    })

                # B. Mẫu Zíc-Zắc xen kẽ lặp lại (Alternating Zig-Zag Pattern)
                # Ví dụ: 1 -> 5 -> 1 -> 5 -> 1 hoặc 5 -> 1 -> 5 -> 1
                val_set = set(numeric_scale_vals)
                if len(val_set) == 2:
                    is_alternating = all(
                        numeric_scale_vals[i] != numeric_scale_vals[i+1]
                        for i in range(len(numeric_scale_vals) - 1)
                    )
                    if is_alternating:
                        v_list = sorted(list(val_set))
                        score_pat = max(score_pat, 75.0)
                        flags.append({
                            "code": "FLAG_ZIGZAG_PATTERN",
                            "severity": "HIGH",
                            "message": f"Phát hiện mẫu zíc-zắc xen kẽ hai cực ({v_list[0]} <-> {v_list[1]}): Thể hiện thao tác điền đối xứng cơ học.",
                            "details": {"pattern_type": "alternating_zigzag", "values": v_list, "length": len(numeric_scale_vals)}
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
        min_expected_duration = max(5.0, total_questions * speed_threshold_per_question)
        
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

        # 6. LAYER G: Phân tích bất thường theo điều tra viên (Enumerator & Group Anomalies)
        if enumerator_id and str(enumerator_id).strip() and prior_responses:
            enum_str = str(enumerator_id).strip()
            # Lọc các phản hồi trước của chính điều tra viên này
            enum_prior = [
                p for p in prior_responses
                if str(p.get("enumerator_id", "")).strip() == enum_str
            ]
            
            # Kiểm tra 1: Tỷ lệ phiếu rủi ro cao trong lô của điều tra viên này (nếu đã nộp >= 3 phiếu)
            if len(enum_prior) >= 3:
                high_risk_priors = sum(
                    1 for p in enum_prior
                    if float(p.get("risk_score", 0.0)) >= 60.0
                )
                if high_risk_priors / len(enum_prior) >= 0.5:
                    score_enum = max(score_enum, 75.0)
                    flags.append({
                        "code": "FLAG_ENUMERATOR_HIGH_RISK_CONCENTRATION",
                        "severity": "HIGH",
                        "message": f"Điều tra viên '{enum_str}' có tỷ lệ phiếu bị cảnh báo rủi ro cao bất thường ({high_risk_priors}/{len(enum_prior)} phiếu).",
                        "details": {"enumerator_id": enum_str, "high_risk_ratio": round(high_risk_priors / len(enum_prior), 2)}
                    })

            # Kiểm tra 2: Đo độ tương đồng nội bộ bất thường giữa các phiếu của cùng một điều tra viên
            eval_q_ids = [q["id"] for q in closed_q_items]
            if eval_q_ids and (len(enum_prior) + 1) >= 4:
                all_enum_responses = enum_prior + [{"answers": new_answers}]
                enum_answer_sets = []
                for resp in all_enum_responses:
                    ans_map = resp.get("answers", {})
                    vec = [cls.normalize_value(ans_map.get(qid)) for qid in eval_q_ids]
                    enum_answer_sets.append(vec)
                
                pairwise_sims = []
                for i in range(len(enum_answer_sets)):
                    for j in range(i + 1, len(enum_answer_sets)):
                        matches = sum(1 for a, b in zip(enum_answer_sets[i], enum_answer_sets[j]) if a == b and a != "")
                        valid = sum(1 for a, b in zip(enum_answer_sets[i], enum_answer_sets[j]) if a != "" or b != "")
                        if valid > 0:
                            pairwise_sims.append(matches / valid)
                
                if pairwise_sims:
                    avg_internal_sim = sum(pairwise_sims) / len(pairwise_sims)
                    if avg_internal_sim >= 0.80:
                        score_enum = max(score_enum, 80.0)
                        flags.append({
                            "code": "FLAG_ENUMERATOR_VARIANCE_ANOMALY",
                            "severity": "HIGH",
                            "message": f"Lô phiếu của điều tra viên '{enum_str}' có độ tương đồng nội bộ bất thường ({avg_internal_sim * 100:.1f}%), nghi ngờ tự điền hàng loạt ngoài thực địa.",
                            "details": {"enumerator_id": enum_str, "avg_internal_similarity": round(avg_internal_sim, 3), "batch_size": len(all_enum_responses)}
                        })

        # 7. LAYER H: Tính điểm rủi ro tổng hợp (Composite Risk Score: 0 - 100)
        # Tái chuẩn hóa trọng số nếu một thành phần không áp dụng
        active_weights = {}
        total_w = 0.0

        active_weights["dup"] = cls.DEFAULT_WEIGHTS["dup"]
        total_w += cls.DEFAULT_WEIGHTS["dup"]

        has_scale_questions = any(
            q.get("question_type") in ("linear_scale", "likert", "matrix")
            for q in questions
        )
        if has_scale_questions:
            active_weights["pat"] = cls.DEFAULT_WEIGHTS["pat"]
            total_w += cls.DEFAULT_WEIGHTS["pat"]

        active_weights["logic"] = cls.DEFAULT_WEIGHTS["logic"]
        total_w += cls.DEFAULT_WEIGHTS["logic"]

        if duration_seconds > 0:
            active_weights["speed"] = cls.DEFAULT_WEIGHTS["speed"]
            total_w += cls.DEFAULT_WEIGHTS["speed"]

        if score_enum > 0:
            active_weights["enum"] = cls.DEFAULT_WEIGHTS["enum"]
            total_w += cls.DEFAULT_WEIGHTS["enum"]

        raw_score = 0.0
        if total_w > 0:
            raw_score += (active_weights.get("dup", 0) / total_w) * score_dup
            raw_score += (active_weights.get("pat", 0) / total_w) * score_pat
            raw_score += (active_weights.get("logic", 0) / total_w) * score_logic
            raw_score += (active_weights.get("speed", 0) / total_w) * score_speed
            raw_score += (active_weights.get("enum", 0) / total_w) * score_enum

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
            "score_enum": round(score_enum, 1),
            "composite_score": composite_score,
            "risk_level": risk_level,
            "flags": flags,
            "closest_match_response_id": closest_match_id,
            "highest_similarity": round(highest_similarity, 3)
        }
