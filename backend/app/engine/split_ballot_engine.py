"""
DataTrust — Split-Ballot & Question Wording Experimentation Engine (A/B & Factorial Arms)
Evaluates experimental survey framing effects, wording plasticity, response distribution shifts,
and deterministic block randomization across experimental arms.
Complies with Schuman & Presser (1981), Mutz (2011), and APA 7th Edition.
"""

import math
import hashlib
from typing import Dict, Any, List, Optional, Tuple
import sqlite3

from app.database import get_db

class SplitBallotEngine:
    """
    Động cơ Thử nghiệm Tách Phiếu & Khảo nghiệm Từ ngữ Khảo sát (Split-Ballot Engine).
    Phục vụ các nghiên cứu thực nghiệm xã hội học, tâm lý học và đo lường hành vi:
    - Phân bổ ngẫu nhiên có kiểm soát (Deterministic Hash Block Randomization)
    - So sánh tỷ lệ hoàn thành & rơi rụng giữa các nhóm đối chứng / thử nghiệm
    - Kiểm định Welch's T-Test và Cohen's d cho câu hỏi thang đo Likert / Điểm số
    - Kiểm định Chi-Square độc lập và Cramér's V cho câu hỏi trắc nghiệm
    - Chỉ số Biến dạng Từ ngữ (Manipulated Wording Distortion Index - MWDI)
    """

    @classmethod
    def assign_arm(
        cls,
        survey_id: str,
        respondent_seed: str,
        arms: List[Dict[str, Any]]
    ) -> str:
        """
        Phân bổ người tham gia vào một nhánh thử nghiệm bằng hàm băm xác định SHA-256.
        Bảo đảm phân bổ đồng đều theo tỷ lệ trọng số mà không xảy ra tranh chấp ghi server.
        """
        if not arms:
            return "arm_a"
        if len(arms) == 1:
            return arms[0].get("id", "arm_a")

        total_weight = sum(a.get("weight", 50) for a in arms)
        if total_weight <= 0:
            total_weight = len(arms) * 50

        seed_str = f"{survey_id}:{respondent_seed}"
        h_val = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:8], 16)
        pick = h_val % total_weight

        cum = 0
        for arm in arms:
            w = arm.get("weight", 50)
            cum += w
            if pick < cum:
                return arm.get("id", "arm_a")

        return arms[-1].get("id", "arm_a")

    @classmethod
    def incomplete_beta(cls, a: float, b: float, x: float) -> float:
        """Tính liên phân số Lentz cho hàm Beta không đầy đủ chính quy hóa I_x(a, b)"""
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0

        ln_beta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
        front = math.exp(a * math.log(x) + b * math.log(1.0 - x) - ln_beta) / a

        # Tiếp phân số Lentz
        f = 1.0
        c = 1.0
        d = 1.0e-30
        tiny = 1.0e-30

        for m in range(1, 140):
            # Hệ số d_(2m)
            num2m = -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))
            d = 1.0 + num2m * d
            if abs(d) < tiny:
                d = tiny
            c = 1.0 + num2m / c
            if abs(c) < tiny:
                c = tiny
            d = 1.0 / d
            f *= c * d

            # Hệ số d_(2m+1)
            num2m1 = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m))
            d = 1.0 + num2m1 * d
            if abs(d) < tiny:
                d = tiny
            c = 1.0 + num2m1 / c
            if abs(c) < tiny:
                c = tiny
            d = 1.0 / d
            f *= c * d

            if abs(c * d - 1.0) < 1.0e-8:
                break

        return front * (f - 1.0)

    @classmethod
    def student_t_pvalue(cls, t_stat: float, df: float) -> float:
        """Tính p-value 2 phía cho thống kê Student t với bậc tự do df"""
        if df <= 0.0:
            return 1.0
        t2 = t_stat * t_stat
        x = df / (df + t2)
        p = cls.incomplete_beta(0.5 * df, 0.5, x)
        return min(1.0, max(0.0, float(p)))

    @classmethod
    def chi_square_cdf(cls, x: float, k: float) -> float:
        """Hàm tích lũy Chi-Square qua hàm Gamma không đầy đủ"""
        if x <= 0.0 or k <= 0.0:
            return 0.0
        # P(k/2, x/2)
        a = 0.5 * k
        z = 0.5 * x
        if z < a + 1.0:
            # Chuỗi lũy thừa Taylor
            sum_val = 1.0 / a
            term = 1.0 / a
            for n in range(1, 120):
                term *= z / (a + n)
                sum_val += term
                if abs(term) < abs(sum_val) * 1.0e-10:
                    break
            return sum_val * math.exp(-z + a * math.log(z) - math.lgamma(a))
        else:
            # Phân số liên tục Legendre
            b0 = z + 1.0 - a
            c = 1.0 / 1.0e-30
            d = 1.0 / b0
            f = d
            for i in range(1, 120):
                an = -i * (i - a)
                b0 += 2.0
                d = an * d + b0
                if abs(d) < 1.0e-30:
                    d = 1.0e-30
                c = b0 + an / c
                if abs(c) < 1.0e-30:
                    c = 1.0e-30
                d = 1.0 / d
                delta = d * c
                f *= delta
                if abs(delta - 1.0) < 1.0e-10:
                    break
            gamma_upper = math.exp(-z + a * math.log(z) - math.lgamma(a)) * f
            return 1.0 - gamma_upper

    @classmethod
    def compare_numeric_arms(
        cls,
        arm_a_vals: List[float],
        arm_b_vals: List[float],
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        So sánh câu hỏi thang đo / điểm số giữa 2 nhánh bằng Welch's T-Test và Cohen's d
        """
        na = len(arm_a_vals)
        nb = len(arm_b_vals)
        if na < 2 or nb < 2:
            return {
                "is_sufficient": False,
                "message": "Cần ít nhất 2 phản hồi hợp lệ cho mỗi nhóm thử nghiệm."
            }

        ma = sum(arm_a_vals) / na
        mb = sum(arm_b_vals) / nb

        va = sum((x - ma) ** 2 for x in arm_a_vals) / (na - 1)
        vb = sum((x - mb) ** 2 for x in arm_b_vals) / (nb - 1)

        sda = math.sqrt(va) if va > 0 else 0.0
        sdb = math.sqrt(vb) if vb > 0 else 0.0

        # Welch's t-statistic
        se_diff = math.sqrt((va / na) + (vb / nb))
        if se_diff <= 1e-12:
            t_stat = 0.0
            df_welch = float(na + nb - 2)
            p_val = 1.0
        else:
            t_stat = (mb - ma) / se_diff
            # Bậc tự do Welch-Satterthwaite
            num = ((va / na) + (vb / nb)) ** 2
            den = (((va / na) ** 2) / (na - 1)) + (((vb / nb) ** 2) / (nb - 1))
            df_welch = num / den if den > 0 else float(na + nb - 2)
            p_val = cls.student_t_pvalue(t_stat, df_welch)

        # Cohen's d (Pooled SD)
        s_pooled_sq = ((na - 1) * va + (nb - 1) * vb) / max(1, na + nb - 2)
        s_pooled = math.sqrt(s_pooled_sq) if s_pooled_sq > 0 else 1.0
        cohen_d = (mb - ma) / s_pooled if s_pooled > 0 else 0.0

        # 95% Confidence Interval for mean difference
        t_crit = 1.960
        ci_lower = (mb - ma) - t_crit * se_diff
        ci_upper = (mb - ma) + t_crit * se_diff

        return {
            "is_sufficient": True,
            "arm_a": {"n": na, "mean": round(ma, 3), "std_dev": round(sda, 3)},
            "arm_b": {"n": nb, "mean": round(mb, 3), "std_dev": round(sdb, 3)},
            "mean_difference": round(mb - ma, 3),
            "se_difference": round(se_diff, 3),
            "t_statistic": round(t_stat, 3),
            "degrees_of_freedom": round(df_welch, 1),
            "p_value": round(p_val, 4),
            "is_significant": p_val < alpha,
            "cohens_d": round(cohen_d, 3),
            "cohens_d_magnitude": (
                "Lớn (Large)" if abs(cohen_d) >= 0.8 else
                "Trung bình (Medium)" if abs(cohen_d) >= 0.5 else
                "Nhỏ (Small)" if abs(cohen_d) >= 0.2 else
                "Không đáng kể (Negligible)"
            ),
            "ci_95": [round(ci_lower, 3), round(ci_upper, 3)]
        }

    @classmethod
    def compare_categorical_arms(
        cls,
        arm_a_opts: List[str],
        arm_b_opts: List[str],
        all_options: List[str]
    ) -> Dict[str, Any]:
        """
        So sánh phân phối phương án trắc nghiệm giữa 2 nhánh bằng Chi-Square và Total Variation Distance
        """
        na = len(arm_a_opts)
        nb = len(arm_b_opts)
        if na < 2 or nb < 2:
            return {
                "is_sufficient": False,
                "message": "Cần ít nhất 2 câu trả lời trong mỗi nhóm."
            }

        # Thu thập toàn bộ các phương án thực tế
        unique_opts = list(dict.fromkeys(all_options + arm_a_opts + arm_b_opts))
        k = len(unique_opts)
        if k < 2:
            return {"is_sufficient": False, "message": "Cần ít nhất 2 phương án lựa chọn."}

        counts_a = {opt: arm_a_opts.count(opt) for opt in unique_opts}
        counts_b = {opt: arm_b_opts.count(opt) for opt in unique_opts}

        # Bảng phân phối tỷ lệ %
        props_a = {opt: round(counts_a[opt] / na, 4) for opt in unique_opts}
        props_b = {opt: round(counts_b[opt] / nb, 4) for opt in unique_opts}

        # Khoảng cách biến thiên toàn phần (Total Variation Distance - TVD): 0.5 * sum(|p_a - p_b|)
        tvd = 0.5 * sum(abs(props_a[opt] - props_b[opt]) for opt in unique_opts)

        # Kiểm định Chi-Square độc lập (2 x K)
        total_n = na + nb
        chi2 = 0.0
        for opt in unique_opts:
            total_opt = counts_a[opt] + counts_b[opt]
            exp_a = (na * total_opt) / total_n
            exp_b = (nb * total_opt) / total_n

            if exp_a > 0:
                chi2 += ((counts_a[opt] - exp_a) ** 2) / exp_a
            if exp_b > 0:
                chi2 += ((counts_b[opt] - exp_b) ** 2) / exp_b

        df = k - 1
        p_val = 1.0 - cls.chi_square_cdf(chi2, df)
        # Cramér's V = sqrt(chi2 / (N * min(R-1, C-1))) = sqrt(chi2 / N)
        cramer_v = math.sqrt(chi2 / total_n) if total_n > 0 else 0.0

        option_comparison = []
        for opt in unique_opts:
            diff_pct = round((props_b[opt] - props_a[opt]) * 100.0, 1)
            option_comparison.append({
                "option": opt,
                "count_a": counts_a[opt],
                "prop_a": round(props_a[opt] * 100.0, 1),
                "count_b": counts_b[opt],
                "prop_b": round(props_b[opt] * 100.0, 1),
                "difference_pct": diff_pct
            })

        return {
            "is_sufficient": True,
            "arm_a_total": na,
            "arm_b_total": nb,
            "chi_square": round(chi2, 3),
            "degrees_of_freedom": df,
            "p_value": round(p_val, 4),
            "is_significant": p_val < 0.05,
            "cramer_v": round(cramer_v, 3),
            "total_variation_distance": round(tvd, 3),
            "option_comparison": option_comparison
        }

    @classmethod
    def calculate_mwdi(
        cls,
        cohens_d: Optional[float] = None,
        tvd: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Tính toán Chỉ Số Biến Dạng Từ Ngữ (Manipulated Wording Distortion Index - MWDI) trong đoạn [0, 1].
        Đánh giá mức độ nhạy cảm của người trả lời trước các cách diễn đạt câu hỏi khác nhau.
        """
        if tvd is not None:
            mwdi = min(1.0, max(0.0, tvd))
        elif cohens_d is not None:
            # Chuẩn hóa Cohen d sang [0, 1] qua d / sqrt(2 + d^2)
            d = abs(cohens_d)
            mwdi = min(1.0, max(0.0, d / math.sqrt(2.0 + d * d)))
        else:
            mwdi = 0.0

        if mwdi < 0.12:
            level = "FRAME_ROBUST"
            badge = "emerald"
            title = "Kháng Đóng Khung (Frame-Robust)"
            desc = "Ý kiến của người trả lời rất kiên định, không bị dao động đáng kể bởi cách dùng từ hoặc thứ tự phương án."
        elif mwdi < 0.28:
            level = "MODERATELY_SENSITIVE"
            badge = "amber"
            title = "Nhạy Cảm Vừa Phải (Moderately Sensitive)"
            desc = "Cách diễn đạt tạo ra sự xê dịch tỷ lệ từ 6% - 15%. Cần chuẩn hóa ngữ cảnh câu hỏi khi báo cáo."
        else:
            level = "HIGHLY_PLASTIC"
            badge = "red"
            title = "Cực Kỳ Nhạy Cảm (Highly Plastic / Frame-Vulnerable)"
            desc = "Hiệu ứng đóng khung từ ngữ nghiêm trọng! Người trả lời bị dẫn dắt mạnh bởi cách hành văn của câu hỏi."

        return {
            "mwdi": round(mwdi, 3),
            "level": level,
            "badge_color": badge,
            "classification_title": title,
            "interpretation": desc
        }

    @classmethod
    def analyze_split_ballot_survey(
        cls,
        survey_id: str,
        question_id: str,
        scope: str = "verified_clean"
    ) -> Dict[str, Any]:
        """
        Phân tích toàn diện thử nghiệm tách phiếu cho một câu hỏi mục tiêu trong khảo sát
        """
        with get_db() as conn:
            s_row = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
            if not s_row:
                raise ValueError("Không tìm thấy khảo sát.")

            q_row = conn.execute("SELECT * FROM questions WHERE id = ? AND survey_id = ?", (question_id, survey_id)).fetchone()
            if not q_row:
                raise ValueError("Không tìm thấy câu hỏi mục tiêu trong khảo sát.")

            q_title = q_row["title"]
            q_type = q_row["question_type"]
            options = []
            try:
                import json
                options = json.loads(q_row["options_json"] or "[]")
                if options and isinstance(options[0], dict):
                    options = [o.get("label", o.get("id", "")) for o in options]
            except Exception:
                options = []

            # Lấy tất cả phản hồi kèm experimental_arm
            base_query = """
                SELECT r.id, r.experimental_arm, r.client_metadata_json, ra.answer_value
                FROM responses r
                LEFT JOIN response_answers ra ON ra.response_id = r.id AND ra.question_id = ?
                WHERE r.survey_id = ?
            """
            params = [question_id, survey_id]
            if scope == "verified_clean":
                base_query += " AND (r.review_status = 'verified_valid' OR (r.review_status = 'unverified' AND r.risk_level = 'low'))"

            rows = conn.execute(base_query, params).fetchall()

        # Phân chia phản hồi theo nhánh experimental_arm
        arms_data: Dict[str, List[Any]] = {}
        for r in rows:
            arm = r["experimental_arm"] or ""
            # Fallback nếu arm chưa được gắn cột trực tiếp: đọc từ client_metadata_json
            if not arm and r["client_metadata_json"]:
                try:
                    import json
                    meta = json.loads(r["client_metadata_json"])
                    arm = meta.get("experimental_arm", "")
                except Exception:
                    pass

            if not arm:
                # Nếu chưa gán nhánh, phân loại giả định theo chẵn lẻ hash ID để phân tích
                arm = "arm_a" if (int(hashlib.md5(r["id"].encode()).hexdigest(), 16) % 2 == 0) else "arm_b"

            ans = r["answer_value"]
            if ans is not None:
                try:
                    import json
                    ans = json.loads(ans)
                except Exception:
                    pass
            arms_data.setdefault(arm, []).append(ans)

        # Sắp xếp các arm theo tên
        sorted_arm_keys = sorted(arms_data.keys())
        arms_summary = []
        for k in sorted_arm_keys:
            ans_list = [a for a in arms_data[k] if a is not None and str(a).strip() != ""]
            arms_summary.append({
                "arm_id": k,
                "label": f"Nhánh Thử Nghiệm {k.upper().replace('ARM_', '')}",
                "total_responses": len(arms_data[k]),
                "answered_count": len(ans_list),
                "response_rate_pct": round((len(ans_list) / len(arms_data[k])) * 100.0, 1) if arms_data[k] else 0.0
            })

        arm_a_key = sorted_arm_keys[0] if len(sorted_arm_keys) > 0 else "arm_a"
        arm_b_key = sorted_arm_keys[1] if len(sorted_arm_keys) > 1 else arm_a_key

        arm_a_answers = [a for a in arms_data.get(arm_a_key, []) if a is not None and str(a).strip() != ""]
        arm_b_answers = [a for a in arms_data.get(arm_b_key, []) if a is not None and str(a).strip() != ""]

        # So sánh dựa trên loại câu hỏi
        is_numeric_type = q_type in ("likert", "rating", "rating_scale", "linear_scale", "number", "nps")
        comparison_res = None
        distortion = None

        if is_numeric_type:
            num_a = []
            for a in arm_a_answers:
                try:
                    num_a.append(float(a))
                except (ValueError, TypeError):
                    pass
            num_b = []
            for a in arm_b_answers:
                try:
                    num_b.append(float(a))
                except (ValueError, TypeError):
                    pass

            num_comp = cls.compare_numeric_arms(num_a, num_b)
            comparison_res = {
                "comparison_type": "numeric",
                "details": num_comp
            }
            cohen_d = num_comp.get("cohens_d") if num_comp.get("is_sufficient") else None
            distortion = cls.calculate_mwdi(cohens_d=cohen_d)
        else:
            str_a = [str(a) for a in arm_a_answers]
            str_b = [str(a) for a in arm_b_answers]
            cat_comp = cls.compare_categorical_arms(str_a, str_b, options)
            comparison_res = {
                "comparison_type": "categorical",
                "details": cat_comp
            }
            tvd = cat_comp.get("total_variation_distance") if cat_comp.get("is_sufficient") else None
            distortion = cls.calculate_mwdi(tvd=tvd)

        # Đoạn trích dẫn học thuật APA 7th Edition
        apa_narrative = (
            f"A split-ballot survey experiment was embedded within the instrument for the target item '{q_title}'. "
            f"Respondents were randomized between {len(arms_data)} experimental arms using deterministic block assignment. "
        )
        if comparison_res.get("comparison_type") == "numeric" and comparison_res["details"].get("is_sufficient"):
            d = comparison_res["details"]
            apa_narrative += (
                f"A Welch's independent samples t-test indicated that the framing difference between Arm A "
                f"(M = {d['arm_a']['mean']}, SD = {d['arm_a']['std_dev']}) and Arm B (M = {d['arm_b']['mean']}, SD = {d['arm_b']['std_dev']}) "
                f"was {'statistically significant' if d['is_significant'] else 'not statistically significant'}, "
                f"t({d['degrees_of_freedom']}) = {d['t_statistic']}, p = {d['p_value']}, Cohen's d = {d['cohens_d']}. "
                f"The Manipulated Wording Distortion Index was calculated at MWDI = {distortion['mwdi']}, classifying the item as {distortion['classification_title']}."
            )
        elif comparison_res.get("comparison_type") == "categorical" and comparison_res["details"].get("is_sufficient"):
            c = comparison_res["details"]
            apa_narrative += (
                f"A Pearson Chi-Square test of independence revealed {'a significant' if c['is_significant'] else 'no significant'} "
                f"shift in option selection across arms, chi-square({c['degrees_of_freedom']}) = {c['chi_square']}, p = {c['p_value']}, "
                f"Cramér's V = {c['cramer_v']}. The Total Variation Distance (TVD) was {c['total_variation_distance']}, "
                f"yielding an overall wording distortion index of MWDI = {distortion['mwdi']} ({distortion['classification_title']})."
            )
        else:
            apa_narrative += "Additional sample collection across arms is required to achieve full inferential power."

        return {
            "survey_id": survey_id,
            "survey_title": s_row["title"],
            "question_id": question_id,
            "question_title": q_title,
            "question_type": q_type,
            "scope": scope,
            "total_responses": len(rows),
            "arms_count": len(arms_data),
            "arms_summary": arms_summary,
            "comparison": comparison_res,
            "distortion_index": distortion,
            "apa_narrative": apa_narrative
        }
