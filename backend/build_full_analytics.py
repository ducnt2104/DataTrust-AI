import json, re, subprocess

transcript_path = r'C:\Users\ADMIN\.gemini\antigravity\brain\732a7110-cc70-46c5-aafb-4dc4e675b9e2\.system_generated\logs\transcript_full.jsonl'

step_reps = {}
target_steps = [
    1254, 2234, 5009, 5369, 5600, 5762, 6004, 6253, 6363, 6477, 6571,
    6700, 6801, 7185, 7311, 7438, 7595, 7818, 8062, 8715, 9074, 9280,
    9364, 9446, 9655, 9745, 10052, 10249, 10253, 10301, 10303, 10305, 10307
]

with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        idx = obj.get('step_index')
        if idx in target_steps:
            for tc in obj.get('tool_calls', []):
                args = tc.get('args', {})
                rep = args.get('Replacement', '') or args.get('Content', '')
                tgt = args.get('Target', '')
                p = args.get('Path', '')
                if 'routes/analytics.py' in p.replace('\\\\', '/').replace('\\', '/'):
                    step_reps[idx] = (tgt, rep)

print(f"Loaded {len(step_reps)} step replacements.")

def extract_added(tgt, rep):
    if tgt and rep.startswith(tgt):
        return rep[len(tgt):].strip()
    return rep.strip()

header = '''import json
import statistics
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from app.database import get_db, record_audit_log
from app.schemas import (
    SurveyAnalyticsOut, QuestionStats, QualitativeAnalysisResponse, LongitudinalWaveComparisonOut,
    SamplingQuotaReportOut, SaveQuotasRequest, DemographicRakingRequest, DemographicRakingOut,
    DIFReportOut, DIFItemResult, IndependentTTestRequest, PairedTTestRequest, OneWayANOVARequest,
    LinearRegressionRequest, PowerAnalysisRequest, SplitBallotAnalysisRequest, RaschAnalysisRequest,
    ClusterAnalysisRequest, PairwiseSimilarityRequest, SpatialAnalysisRequest,
    MediationAnalysisRequest, MediationAnalysisOut,
    MannWhitneyURequest, MannWhitneyUOut,
    WilcoxonSignedRankRequest, WilcoxonSignedRankOut,
    KruskalWallisRequest, KruskalWallisOut,
    MissingDataDiagnosticsRequest, MissingDataDiagnosticsOut,
    MissingDataImputationRequest, MissingDataImputationOut,
    ScaleEquatingRequest, ScaleEquatingOut,
    MeasurementInvarianceRequest, MeasurementInvarianceOut,
    CommonMethodBiasRequest, CommonMethodBiasOut,
    ModerationAnalysisRequest, ModerationAnalysisOut,
    ModeratedMediationRequest, ModeratedMediationOut,
    ComplexSamplingRequest, ComplexSamplingOut,
    PSMAnalysisRequest, PSMAnalysisOut,
    TopicModelAnalysisRequest, TopicModelAnalysisOut,
    PsychometricNetworkRequest, PsychometricNetworkOut,
    IRT2PLAnalysisRequest, IRT2PLAnalysisOut,
    SurvivalAnalysisRequest, SurvivalAnalysisOut,
    MultilevelAnalysisRequest, MultilevelAnalysisOut,
    ConjointAnalysisRequest, ConjointAnalysisOut,
    ConjointSimulationRequest, ConjointSimulationOut,
    LCAAnalysisRequest, LCAAnalysisOut,
    DiDAnalysisRequest, DiDAnalysisOut,
    SEMAnalysisRequest, SEMAnalysisOut,
    CompetingRisksAnalysisRequest, CompetingRisksAnalysisOut,
    IRT4PLAnalysisRequest, IRT4PLAnalysisOut,
    IPWAnalysisRequest, IPWAnalysisOut,
    GAMSplineAnalysisRequest, GAMSplineAnalysisOut,
    QuantileRegressionRequest, QuantileRegressionOut,
    GTheoryAnalysisRequest, GTheoryAnalysisOut,
    RDDAnalysisRequest, RDDAnalysisOut
)
from app.engine.quality_engine import QualityEngine
from app.engine.qualitative_engine import QualitativeEngine
from app.engine.quota_engine import QuotaEngine, RakingEngine
from app.engine.dif_engine import DIFEngine
from app.engine.pacing_engine import CognitivePacingEngine
from app.engine.mahalanobis_engine import MahalanobisEngine
from app.engine.efa_engine import EFAEngine
from app.engine.ttest_engine import TTestEngine
from app.engine.anova_engine import ANOVAEngine
from app.engine.correlation_engine import CorrelationEngine
from app.engine.regression_engine import RegressionEngine
from app.engine.power_engine import PowerAnalysisEngine
from app.engine.split_ballot_engine import SplitBallotEngine
from app.engine.rasch_engine import RaschEngine
from app.engine.cluster_engine import ClusterEngine
from app.engine.similarity_engine import SimilarityEngine
from app.engine.spatial_engine import SpatialEngine
from app.engine.mediation_engine import MediationEngine
from app.engine.non_parametric_engine import NonParametricEngine
from app.engine.missing_data_engine import MissingDataEngine
from app.engine.equating_engine import EquatingEngine
from app.engine.invariance_engine import MeasurementInvarianceEngine
from app.engine.cmb_engine import CMBEngine
from app.engine.moderation_engine import ModerationEngine
from app.engine.moderated_mediation_engine import ModeratedMediationEngine
from app.engine.complex_sampling_engine import ComplexSamplingEngine
from app.engine.psm_engine import PSMEngine
from app.engine.topic_model_engine import TopicModelingEngine
from app.engine.network_engine import PsychometricNetworkEngine
from app.engine.irt_2pl_engine import IRT2PLEngine
from app.engine.survival_engine import SurvivalDropOffEngine
from app.engine.multilevel_engine import MultilevelModelingEngine
from app.engine.conjoint_engine import ConjointAnalysisEngine
from app.engine.lca_engine import LatentClassAnalysisEngine
from app.engine.did_engine import DifferenceInDifferencesEngine
from app.engine.sem_engine import SEMEngine
from app.engine.competing_risks_frailty_engine import CompetingRisksFrailtyEngine
from app.engine.irt_4pl_engine import IRT4PLEngine
from app.engine.ipw_doubly_robust_engine import IPWDoublyRobustEngine
from app.engine.gam_spline_engine import GAMSplineEngine
from app.engine.quantile_regression_engine import QuantileRegressionEngine
from app.engine.g_theory_engine import GTheoryEngine
from app.engine.rdd_engine import RDDEngine

router = APIRouter(prefix="/api/surveys/{survey_id}/analytics", tags=["Analytics"])
'''

modern_get_survey_analytics = '''@router.get("", response_model=SurveyAnalyticsOut)
def get_survey_analytics(survey_id: str):
    """Tính toán thống kê thực từ cơ sở dữ liệu cho cuộc khảo sát"""
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_rows = conn.execute("""
            SELECT * FROM responses WHERE survey_id = ?
        """, (survey_id,)).fetchall()

        total_responses = len(resp_rows)
        is_sufficient = total_responses >= 5
        notice = None if is_sufficient else f"Cỡ mẫu hiện tại (N = {total_responses}) chưa đạt ngưỡng tối thiểu N >= 5 để đảm bảo độ tin cậy thống kê tổng thể."

        avg_dur = 0.0
        risk_dist = {"low": 0, "medium": 0, "high": 0}
        review_dist = {"unverified": 0, "under_review": 0, "verified_valid": 0, "verified_fraud": 0, "inconclusive": 0}

        if total_responses > 0:
            durations = [r["duration_seconds"] for r in resp_rows if r["duration_seconds"] > 0]
            avg_dur = round(sum(durations) / len(durations), 1) if durations else 0.0

            for r in resp_rows:
                lvl = r["risk_level"] or "low"
                risk_dist[lvl] = risk_dist.get(lvl, 0) + 1
                
                rev = r["review_status"] or "unverified"
                review_dist[rev] = review_dist.get(rev, 0) + 1

        # Lấy danh sách câu hỏi
        q_rows = conn.execute("""
            SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()

        # Tối ưu hóa: Tải trước toàn bộ câu trả lời của khảo sát vào bộ nhớ trong 1 câu truy vấn (Tránh N+1)
        all_ans_rows = conn.execute("""
            SELECT ra.question_id, ra.answer_value 
            FROM response_answers ra
            JOIN responses r ON r.id = ra.response_id
            WHERE r.survey_id = ?
        """, (survey_id,)).fetchall()
        answers_by_qid = {}
        for a in all_ans_rows:
            answers_by_qid.setdefault(a["question_id"], []).append(a)

        questions_analytics = []
        funnel_analytics = []
        prev_ans_count = total_responses if total_responses > 0 else None

        for idx, q in enumerate(q_rows):
            qid = q["id"]
            q_type = q["question_type"]
            options = json.loads(q["options_json"] or "[]")
            
            # Lấy câu trả lời từ dict trong bộ nhớ (O(1) lookup)
            ans_rows = answers_by_qid.get(qid, [])

            total_ans = len(ans_rows)
            opt_dist = None
            stats_sum = None
            text_samples = None

            # Tính completion rate & drop-off rate
            comp_rate = round((total_ans / total_responses) * 100, 1) if total_responses > 0 else 0.0
            drop_off = round(((prev_ans_count - total_ans) / max(1, prev_ans_count)) * 100, 1) if (prev_ans_count is not None and prev_ans_count > total_ans) else 0.0
            prev_ans_count = total_ans

            funnel_analytics.append({
                "step": idx + 1,
                "question_id": qid,
                "question_title": q["title"],
                "question_type": q_type,
                "total_answers": total_ans,
                "completion_rate_pct": comp_rate,
                "drop_off_pct": drop_off
            })

            if q_type in ("single_choice", "dropdown", "likert"):
                id_to_label = {opt.get("id"): opt.get("label") for opt in options if isinstance(opt, dict)}
                counts = {opt.get("label", opt.get("id")): 0 for opt in options if isinstance(opt, dict)}
                
                for a in ans_rows:
                    raw = a["answer_value"]
                    val = id_to_label.get(raw, raw)
                    counts[val] = counts.get(val, 0) + 1
                opt_dist = counts

            elif q_type == "multiple_choice":
                id_to_label = {opt.get("id"): opt.get("label") for opt in options if isinstance(opt, dict)}
                counts = {opt.get("label", opt.get("id")): 0 for opt in options if isinstance(opt, dict)}
                
                for a in ans_rows:
                    raw = a["answer_value"]
                    try:
                        selected = json.loads(raw)
                        if isinstance(selected, list):
                            for s in selected:
                                label = id_to_label.get(s, s)
                                counts[label] = counts.get(label, 0) + 1
                        else:
                            label = id_to_label.get(raw, raw)
                            counts[label] = counts.get(label, 0) + 1
                    except Exception:
                        label = id_to_label.get(raw, raw)
                        counts[label] = counts.get(label, 0) + 1
                opt_dist = counts

            elif q_type in ("linear_scale", "number"):
                nums = []
                for a in ans_rows:
                    try:
                        nums.append(float(a["answer_value"]))
                    except Exception:
                        pass
                if nums:
                    stats_sum = {
                        "min": min(nums),
                        "max": max(nums),
                        "avg": round(sum(nums) / len(nums), 2),
                        "count": len(nums)
                    }
                    num_counts = {}
                    for n in nums:
                        k = str(int(n) if n.is_integer() else n)
                        num_counts[k] = num_counts.get(k, 0) + 1
                    opt_dist = num_counts

            elif q_type == "matrix":
                matrix_rows = options.get("rows", []) if isinstance(options, dict) else []
                matrix_cols = options.get("columns", []) if isinstance(options, dict) else []
                row_map = {
                    (r.get("id") if isinstance(r, dict) else str(r)): (r.get("label") if isinstance(r, dict) else str(r))
                    for r in matrix_rows
                }
                col_map = {
                    (c.get("id") if isinstance(c, dict) else str(c)): (c.get("label") if isinstance(c, dict) else str(c))
                    for c in matrix_cols
                }
                
                counts = {r_lbl: {c_lbl: 0 for c_lbl in col_map.values()} for r_lbl in row_map.values()}
                
                for a in ans_rows:
                    try:
                        m_ans = json.loads(a["answer_value"])
                        if isinstance(m_ans, dict):
                            for r_k, c_v in m_ans.items():
                                r_lbl = row_map.get(r_k, r_k)
                                c_lbl = col_map.get(c_v, c_v)
                                if r_lbl in counts and c_lbl in counts[r_lbl]:
                                    counts[r_lbl][c_lbl] += 1
                    except Exception:
                        pass
                opt_dist = {r_lbl: sum(counts[r_lbl].values()) for r_lbl in counts}
                stats_sum = {"matrix_distribution": counts}

            elif q_type == "ranking":
                items = options if isinstance(options, list) else []
                item_map = {
                    (it.get("id") if isinstance(it, dict) else str(it)): (it.get("label") if isinstance(it, dict) else str(it))
                    for it in items
                }
                rank_positions = {label: [] for label in item_map.values()}
                
                for a in ans_rows:
                    try:
                        ranked_list = json.loads(a["answer_value"])
                        if isinstance(ranked_list, list):
                            for pos, item_id in enumerate(ranked_list):
                                label = item_map.get(item_id, item_id)
                                if label not in rank_positions:
                                    rank_positions[label] = []
                                rank_positions[label].append(pos + 1)
                    except Exception:
                        pass
                
                avg_ranks = {}
                first_place_counts = {}
                for label, positions in rank_positions.items():
                    if positions:
                        avg_ranks[label] = round(sum(positions) / len(positions), 2)
                        first_place_counts[label] = positions.count(1)
                    else:
                        avg_ranks[label] = 0.0
                        first_place_counts[label] = 0
                
                opt_dist = first_place_counts
                stats_sum = {"ranking_averages": avg_ranks}

            elif q_type in ("long_text", "short_text"):
                samples = []
                for a in ans_rows:
                    txt = (a["answer_value"] or "").strip()
                    if txt and txt not in samples:
                        samples.append(txt)
                    if len(samples) >= 8:
                        break
                text_samples = samples

            questions_analytics.append(QuestionStats(
                question_id=qid,
                question_title=q["title"],
                question_type=q_type,
                total_answers=total_ans,
                completion_rate=comp_rate,
                drop_off_rate=drop_off,
                option_distribution=opt_dist,
                stats_summary=stats_sum,
                recent_text_samples=text_samples
            ))

        # Tính tỷ lệ hoàn thành toàn bộ cuộc khảo sát (Overall Completion Rate)
        overall_completed_count = 0
        if total_responses > 0 and q_rows:
            req_qids = [q["id"] for q in q_rows if q["is_required"]]
            target_qids = req_qids if req_qids else [q["id"] for q in q_rows]
            placeholders = ",".join(["?"] * len(target_qids))
            completed_row = conn.execute(f"""
                SELECT COUNT(*) as completed_count FROM (
                    SELECT ra.response_id
                    FROM response_answers ra
                    JOIN responses r ON r.id = ra.response_id
                    WHERE r.survey_id = ? AND ra.question_id IN ({placeholders})
                    GROUP BY ra.response_id
                    HAVING COUNT(DISTINCT ra.question_id) = ?
                )
            """, [survey_id] + target_qids + [len(target_qids)]).fetchone()
            if completed_row:
                overall_completed_count = completed_row["completed_count"]
            overall_comp_rate = round((overall_completed_count / total_responses) * 100, 1)
        else:
            overall_comp_rate = 100.0 if total_responses > 0 else 0.0

        return SurveyAnalyticsOut(
            survey_id=survey_id,
            survey_title=s_row["title"],
            total_responses=total_responses,
            is_sample_size_sufficient=is_sufficient,
            sample_size_notice=notice,
            avg_duration_seconds=avg_dur,
            overall_completion_rate=overall_comp_rate,
            funnel_analytics=funnel_analytics,
            risk_distribution=risk_dist,
            review_distribution=review_dist,
            questions_analytics=questions_analytics
        )
'''

benford_code = '''@router.get("/benford")
def get_benford_analysis(survey_id: str, question_id: Optional[str] = Query(None)):
    """
    Phân tích định luật Benford (First-Digit Test) trên các câu hỏi kiểu số học
    để phát hiện số liệu ngụy tạo / bịa đặt theo phương pháp Schräpler & Wagner (2012)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        if question_id:
            ans_rows = conn.execute("""
                SELECT ra.answer_value 
                FROM response_answers ra
                JOIN responses r ON r.id = ra.response_id
                WHERE ra.question_id = ? AND r.survey_id = ?
            """, (question_id, survey_id)).fetchall()
        else:
            ans_rows = conn.execute("""
                SELECT ra.answer_value 
                FROM response_answers ra
                JOIN responses r ON r.id = ra.response_id
                JOIN questions q ON q.id = ra.question_id
                WHERE r.survey_id = ? AND q.question_type IN ('number', 'linear_scale')
            """, (survey_id,)).fetchall()

        values = []
        for a in ans_rows:
            try:
                v = float(a["answer_value"])
                values.append(v)
            except Exception:
                pass

        result = QualityEngine.compute_benford_analysis(values)
        return result
'''

qualitative_code = extract_added(*step_reps[1254])
crosstab_code = extract_added(*step_reps[2234])
reliability_code = extract_added(*step_reps[5009]).replace('/analytics/reliability', '/reliability')
longitudinal_code = extract_added(*step_reps[5369])
quotas_raking_code = extract_added(*step_reps[5600]).replace("review_status != 'verified_fraud'", "review_status NOT IN ('verified_fraud', 'quota_screened_out')")
dif_code = extract_added(*step_reps[5762])
pacing_code = extract_added(*step_reps[6004])
outliers_code = extract_added(*step_reps[6253])
efa_code = extract_added(*step_reps[6363])
ttest_code = extract_added(*step_reps[6477])
anova_code = extract_added(*step_reps[6571])
correlation_code = extract_added(*step_reps[6700])
regression_code = extract_added(*step_reps[6801])
power_code = extract_added(*step_reps[7185])
split_ballot_code = extract_added(*step_reps[7311])

# Rasch with both GET and POST
rasch_post = extract_added(*step_reps[7438])
rasch_get = step_reps[10301][1]

# Clusters with both GET and POST
clusters_post = extract_added(*step_reps[7595])
clusters_get = step_reps[10303][1]

# Similarity with both GET and POST
similarity_post = extract_added(*step_reps[7818])
similarity_get = step_reps[10305][1]

# Spatial with both GET and POST
spatial_code = '''@router.post("/spatial")
def run_spatial_analysis(survey_id: str, payload: SpatialAnalysisRequest = SpatialAnalysisRequest()):
    """
    Kiem dinh Khong gian Thuc dia va Gian lan Toa do GPS (Spatial Geo-Fencing va DBSCAN):
    - Phan cum mat do DBSCAN (Ester et al., 1996) phat hien gian lan ngoi mot cho khai khong
    - Phat hien van toc di chuyen bat kha thi / Gia lap vi tri (Teleportation & GPS Spoofing)
    - Kiem dinh ranh gioi da giac Geo-Fencing bang thuat toan Ray-Casting
    - Do do phan tan khong gian chuan (Spatial Standard Distance Deviation - Bachi 1962)
    """
    try:
        polygon = None
        if payload.geofence_polygon:
            polygon = [(p[0], p[1]) for p in payload.geofence_polygon if len(p) >= 2]
        return SpatialEngine.analyze_survey_spatial(
            survey_id=survey_id,
            eps_meters=payload.eps_meters,
            min_samples=payload.min_samples,
            max_speed_kmh=payload.max_speed_kmh,
            geofence_polygon=polygon,
            scope=payload.scope
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/spatial")
def get_spatial_analysis(
    survey_id: str,
    eps_meters: float = Query(75.0, ge=10.0, le=2000.0, description="Ban kinh lang gieng DBSCAN (met)"),
    min_samples: int = Query(3, ge=2, le=20, description="So diem toi thieu de hinh thanh cum"),
    max_speed_kmh: float = Query(120.0, ge=20.0, le=500.0, description="Van toc di chuyen toi da (km/h)"),
    scope: str = Query("all", description="Pham vi phan hoi: all hoac verified_clean")
):
    """
    Endpoint GET cho kiem dinh khong gian thuc dia va phat hien gian lan GPS
    """
    try:
        return SpatialEngine.analyze_survey_spatial(
            survey_id=survey_id,
            eps_meters=eps_meters,
            min_samples=min_samples,
            max_speed_kmh=max_speed_kmh,
            scope=scope
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
'''

mediation_code = '''@router.post("/mediation", response_model=MediationAnalysisOut)
def run_mediation_analysis(survey_id: str, payload: MediationAnalysisRequest):
    """
    Phân tích Tác động Trung gian (Statistical Mediation & Path Analysis)
    theo chuẩn Baron & Kenny (1986), Preacher & Hayes (2004, 2008), Sobel (1982),
    Bootstrap 95% CI và VAF (Hair et al., 2017).
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        x_id = payload.x_question_id or payload.independent_var_id
        m_id = payload.m_question_id or payload.mediator_var_id
        y_id = payload.y_question_id or payload.dependent_var_id

        if not x_id or not m_id or not y_id:
            raise HTTPException(status_code=400, detail="Vui lòng cung cấp đầy đủ x_question_id, m_question_id, y_question_id.")

        if len({x_id, m_id, y_id}) < 3:
            raise HTTPException(status_code=400, detail="Biến độc lập (X), trung gian (M) và phụ thuộc (Y) phải hoàn toàn phân biệt.")

        q_rows = conn.execute(
            "SELECT id, title FROM questions WHERE survey_id = ? AND id IN (?, ?, ?)",
            (survey_id, x_id, m_id, y_id)
        ).fetchall()
        q_dict = {q["id"]: q["title"] for q in q_rows}
        if x_id not in q_dict or m_id not in q_dict or y_id not in q_dict:
            raise HTTPException(status_code=400, detail="Không tìm thấy các câu hỏi tương ứng trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses WHERE survey_id = ?
            """, (survey_id,)).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": "Chưa có phản hồi nào trong khảo sát.",
                "sample_size": 0,
                "variables": {"x": q_dict.get(x_id, x_id), "m": q_dict.get(m_id, m_id), "y": q_dict.get(y_id, y_id)}
            }

        placeholders = ",".join("?" for _ in resp_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders}) AND question_id IN (?, ?, ?)
        """, resp_ids + [x_id, m_id, y_id]).fetchall()

        resp_map = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_map:
                resp_map[rid] = {}
            resp_map[rid][a["question_id"]] = a["answer_value"]

        x_data, m_data, y_data = [], [], []
        for rid in resp_ids:
            row_ans = resp_map.get(rid, {})
            if x_id in row_ans and m_id in row_ans and y_id in row_ans:
                try:
                    xv = float(row_ans[x_id])
                    mv = float(row_ans[m_id])
                    yv = float(row_ans[y_id])
                    x_data.append(xv)
                    m_data.append(mv)
                    y_data.append(yv)
                except (ValueError, TypeError):
                    continue

        if len(x_data) < 5:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(x_data)} phản hồi có dữ liệu hợp lệ cho cả 3 biến (yêu cầu tối thiểu 5).",
                "sample_size": len(x_data),
                "variables": {"x": q_dict.get(x_id, x_id), "m": q_dict.get(m_id, m_id), "y": q_dict.get(y_id, y_id)}
            }

        res = MediationEngine.analyze_mediation(
            x_data=x_data,
            m_data=m_data,
            y_data=y_data,
            x_label=q_dict[x_id],
            m_label=q_dict[m_id],
            y_label=q_dict[y_id],
            bootstrap_samples=payload.bootstrap_samples or payload.num_bootstrap or 1000
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MEDIATION_ANALYSIS_PERFORMED",
            details={
                "independent_var": q_dict[x_id],
                "mediator_var": q_dict[m_id],
                "dependent_var": q_dict[y_id],
                "sample_size": len(x_data),
                "mediation_type": res.get("sobel_test", {}).get("mediation_type"),
                "indirect_effect": res.get("paths", {}).get("indirect_effect_ab")
            }
        )

        return res
'''

# Non-parametric routes from scratch/append_non_parametric_routes.py
with open('C:/Users/ADMIN/.gemini/antigravity/brain/732a7110-cc70-46c5-aafb-4dc4e675b9e2/scratch/append_non_parametric_routes.py', 'r', encoding='utf-8') as f:
    np_raw = f.read()
    np_start = np_raw.find('@router.post("/mann-whitney-u"')
    np_end = np_raw.rfind("'''")
    if np_end == -1:
        np_end = len(np_raw)
    non_parametric_code = np_raw[np_start:np_end].strip()

missing_data_code = extract_added(*step_reps[9074]).replace("FROM answers", "FROM response_answers")
scale_equating_code = extract_added(*step_reps[9280])
measurement_invariance_code = extract_added(*step_reps[9364])
cmb_code = extract_added(*step_reps[9446])
moderation_code = extract_added(*step_reps[9655])
moderated_mediation_code = extract_added(*step_reps[9745])
complex_sampling_code = extract_added(*step_reps[10052]).replace(
    "verification_status = 'verified_clean'",
    "(is_verified_clean = 1 OR review_status = 'verified_valid')"
).replace(
    "verification_status != 'rejected'",
    "review_status != 'verified_fraud'"
)

psm_code = '''@router.post("/propensity-matching", response_model=PSMAnalysisOut)
def run_propensity_matching_analysis(survey_id: str, payload: PSMAnalysisRequest):
    """
    Phân tích So khớp Điểm Xu hướng (Propensity Score Matching - PSM)
    và Nghịch đảo Xác suất Trọng số (Inverse Probability Weighting - IPW):
    - Đánh giá tác động can thiệp nhân quả (ATT - Average Treatment Effect on the Treated)
    - Mô hình hóa điểm xu hướng qua Hồi quy Logistic (Newton-Raphson/IRLS)
    - So khớp láng giềng gần nhất 1:1 không thay thế có chặn ngưỡng Caliper (Austin 2011)
    - Chẩn đoán cân bằng đồng biến (SMD < 0.10, Tỷ số phương sai VR, Love Plot)
    - Tự động sinh đoạn trích dẫn chuẩn APA 7th Edition và ghi nhận sổ cái SHA-256.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        treatment_id = payload.treatment_question_id
        outcome_id = payload.outcome_question_id
        cov_ids = payload.covariate_question_ids

        all_qids = [treatment_id, outcome_id] + cov_ids
        placeholders = ",".join("?" for _ in all_qids)
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + all_qids
        ).fetchall()

        q_dict = {q["id"]: {"title": q["title"], "type": q["question_type"]} for q in q_rows}
        if treatment_id not in q_dict or outcome_id not in q_dict:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi can thiệp hoặc kết quả.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses WHERE survey_id = ?
            """, (survey_id,)).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return PSMEngine._build_empty_response(
                treatment_title=q_dict[treatment_id]["title"],
                outcome_title=q_dict[outcome_id]["title"],
                reason="Chưa có phản hồi nào trong khảo sát."
            )

        ans_rows = conn.execute(
            f"SELECT response_id, question_id, answer_value FROM response_answers WHERE question_id IN ({placeholders})",
            all_qids
        ).fetchall()

        resp_map: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_map:
                resp_map[rid] = {}
            resp_map[rid][a["question_id"]] = a["answer_value"]

        records = []
        treat_val_str = str(payload.treatment_value).strip().lower()
        for rid in resp_ids:
            ans = resp_map.get(rid, {})
            if treatment_id not in ans or outcome_id not in ans:
                continue

            raw_treat = str(ans[treatment_id]).strip().lower()
            is_treat = 1 if raw_treat == treat_val_str else 0

            try:
                outcome_val = float(ans[outcome_id])
            except (ValueError, TypeError):
                continue

            cov_vals = []
            has_all_covs = True
            for cid in cov_ids:
                if cid not in ans:
                    has_all_covs = False
                    break
                try:
                    cov_vals.append(float(ans[cid]))
                except (ValueError, TypeError):
                    has_all_covs = False
                    break

            if has_all_covs:
                records.append({
                    "id": rid,
                    "treatment": is_treat,
                    "outcome": outcome_val,
                    "covariates": cov_vals
                })

        cov_titles = [q_dict.get(cid, {}).get("title", cid) for cid in cov_ids]
        res = PSMEngine.analyze_propensity_matching(
            records=records,
            treatment_name=q_dict[treatment_id]["title"],
            outcome_name=q_dict[outcome_id]["title"],
            covariate_names=cov_titles,
            caliper_factor=payload.caliper_factor or 0.20
        )
        res["survey_id"] = survey_id

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="PROPENSITY_SCORE_MATCHING_EVALUATED",
            details={
                "treatment_question": q_dict[treatment_id]["title"],
                "outcome_question": q_dict[outcome_id]["title"],
                "sample_size": res.get("sample_size"),
                "matched_pairs": res.get("matched_pairs_count"),
                "att_matched": res.get("matched_att", {}).get("estimate"),
                "p_value": res.get("matched_att", {}).get("p_value")
            }
        )

        return res
'''

topic_model_code = '''@router.post("/topic-modeling", response_model=TopicModelAnalysisOut)
def run_topic_modeling_analysis(survey_id: str, payload: TopicModelAnalysisRequest):
    """
    Mô hình hóa Chủ đề Cấu trúc (Structural Topic Modeling - STM)
    và Phân bổ Dirichlet Tiềm ẩn (Latent Dirichlet Allocation - LDA) cho câu hỏi mở:
    - Thuật toán lấy mẫu Gibbs có điều kiện (Collapsed Gibbs Sampling; Griffiths & Steyvers 2004)
    - Tiền xử lý văn bản tiếng Việt chuyên sâu với từ ghép và từ dừng khảo sát
    - Đánh giá độ mạch lạc ngữ nghĩa UMass Topic Coherence (Mimno et al. 2011) và Exclusivity
    - Phân tích tương quan giữa biến kiểm soát và tỷ trọng chủ đề (Roberts et al. 2014)
    - Tự động biên soạn thuyết minh chuẩn APA 7th Edition và ghi nhận sổ cái SHA-256.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        text_qid = payload.text_question_id
        cov_qid = payload.covariate_question_id

        all_qids = [text_qid]
        if cov_qid:
            all_qids.append(cov_qid)

        placeholders = ",".join("?" for _ in all_qids)
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders})",
            [survey_id] + all_qids
        ).fetchall()

        q_dict = {q["id"]: {"title": q["title"], "type": q["question_type"]} for q in q_rows}
        if text_qid not in q_dict:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi văn bản trong khảo sát.")
        if cov_qid and cov_qid not in q_dict:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến đồng biến trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if not resp_ids:
            return TopicModelingEngine._build_empty_response(reason="Chưa có phản hồi nào trong khảo sát.")

        ans_rows = conn.execute(
            f"SELECT response_id, question_id, answer_value FROM response_answers WHERE question_id IN ({placeholders})",
            all_qids
        ).fetchall()

        resp_map: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_map:
                resp_map[rid] = {}
            resp_map[rid][a["question_id"]] = a["answer_value"]

        documents = []
        for rid in resp_ids:
            ans = resp_map.get(rid, {})
            raw_text = ans.get(text_qid)
            if not raw_text or not str(raw_text).strip():
                continue

            cov_val = None
            if cov_qid and cov_qid in ans:
                try:
                    cov_val = float(ans[cov_qid])
                except (ValueError, TypeError):
                    cov_val = None

            documents.append({
                "id": rid,
                "text": str(raw_text).strip(),
                "covariate": cov_val
            })

        if len(documents) < 3:
            return TopicModelingEngine._build_empty_response(
                reason=f"Chỉ có {len(documents)} phản hồi chứa văn bản hợp lệ (yêu cầu tối thiểu 3)."
            )

        res = TopicModelingEngine.fit_lda_topic_model(
            documents=documents,
            num_topics=payload.num_topics or 3,
            num_iterations=payload.num_iterations or 60,
            random_seed=42
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="STRUCTURAL_TOPIC_MODEL_EVALUATED",
            details={
                "text_question": q_dict[text_qid]["title"],
                "covariate_question": q_dict.get(cov_qid, {}).get("title") if cov_qid else None,
                "sample_size": res.get("sample_size"),
                "topics_count": res.get("num_topics"),
                "mean_coherence_umass": res.get("mean_coherence_umass")
            }
        )

        return res
'''

network_code = '''@router.post("/psychometric-network", response_model=PsychometricNetworkOut)
def run_psychometric_network_analysis(survey_id: str, payload: PsychometricNetworkRequest):
    """
    Phân tích Mạng Lưới Tâm lý học Đo lường (Psychometric Network Analysis)
    và Mô hình Đồ thị Gaussian (Gaussian Graphical Model - GGM; Epskamp et al. 2012, 2018):
    - Đảo ma trận hiệp phương sai mẫu thành ma trận chính xác Precision Matrix với điều chuẩn Ridge
    - Ước lượng ma trận tương quan riêng phần (Partial Correlation Matrix) và ngưỡng regularization
    - Tính toán các chỉ số trung tâm mạng lưới: Cường độ bậc (Strength), Tầm ảnh hưởng kỳ vọng (Expected Influence), Độ gần gũi (Closeness), Độ trung gian (Betweenness)
    - Thuật toán bố trí lực lò xo Fruchterman-Reingold (1991) tính toán tọa độ vector 2D phục vụ hiển thị SVG
    - Tự động sinh thuyết minh học thuật chuẩn APA 7th Edition và ghi nhận nhật ký kiểm toán SHA-256.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        if payload.question_ids and len(payload.question_ids) > 0:
            placeholders = ",".join("?" for _ in payload.question_ids)
            q_rows = conn.execute(
                f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders}) ORDER BY order_index ASC",
                [survey_id] + payload.question_ids
            ).fetchall()
        else:
            q_rows = conn.execute("""
                SELECT id, title, question_type FROM questions
                WHERE survey_id = ? AND question_type IN ('number', 'rating', 'nps', 'likert', 'linear_scale')
                ORDER BY order_index ASC
            """, (survey_id,)).fetchall()

        if len(q_rows) < 3:
            raise HTTPException(status_code=400, detail="Cần tối thiểu 3 câu hỏi định lượng để phân tích mạng lưới đồ thị.")

        q_ids = [q["id"] for q in q_rows]
        node_names = [q["title"] for q in q_rows]

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if len(resp_ids) < 4:
            return PsychometricNetworkEngine._build_empty_response(
                reason=f"Cần tối thiểu 4 phản hồi để phân tích mạng lưới đồ thị (hiện có {len(resp_ids)})."
            )

        placeholders_resp = ",".join("?" for _ in resp_ids)
        placeholders_q = ",".join("?" for _ in q_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + q_ids).fetchall()

        resp_map: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_map:
                resp_map[rid] = {}
            resp_map[rid][a["question_id"]] = a["answer_value"]

        data_matrix = []
        for rid in resp_ids:
            row_dict = resp_map.get(rid, {})
            row_vals = []
            valid_row = True
            for qid in q_ids:
                if qid not in row_dict:
                    valid_row = False
                    break
                try:
                    row_vals.append(float(row_dict[qid]))
                except (ValueError, TypeError):
                    valid_row = False
                    break
            if valid_row:
                data_matrix.append(row_vals)

        if len(data_matrix) < 4:
            return PsychometricNetworkEngine._build_empty_response(
                reason=f"Chỉ có {len(data_matrix)} phản hồi hoàn chỉnh cho cả {len(q_ids)} biến (yêu cầu tối thiểu 4)."
            )

        res = PsychometricNetworkEngine.analyze_network(
            data_matrix=data_matrix,
            node_names=node_names,
            regularization_threshold=payload.regularization_threshold or 0.05
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="PSYCHOMETRIC_NETWORK_ANALYSIS_EVALUATED",
            details={
                "nodes_count": res.get("num_nodes"),
                "edges_count": res.get("num_edges"),
                "density": res.get("density"),
                "sample_size": res.get("sample_size"),
                "most_central_node": res.get("most_central_node")
            }
        )

        return res
'''

irt_2pl_code = '''@router.post("/irt-2pl", response_model=IRT2PLAnalysisOut)
def run_irt_2pl_analysis(survey_id: str, payload: IRT2PLAnalysisRequest):
    """
    Lý thuyết Ứng đáp Câu hỏi 2 Tham số Logistic (Item Response Theory - IRT 2PL)
    và Đường cong Đặc trưng Câu hỏi (Item Characteristic Curve - ICC; Birnbaum 1968, Reckase 2009):
    - Ước lượng độ phân biệt câu hỏi (a_i) và độ khó/ngưỡng ủng hộ (b_i) bằng thuật toán MML-EM
    - Đường cong ICC và Hàm thông tin câu hỏi (IIF) / Hàm thông tin bài test (TIF)
    - Đánh giá độ tin cậy biên thang đo (Marginal Reliability rho_IRT)
    - Ước lượng năng lực người làm bài (EAP Latent Trait Person Scoring)
    - Tự động sinh tọa độ vector SVG cho ICC và TIF, kèm thuyết minh học thuật APA 7th Edition.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        if payload.question_ids and len(payload.question_ids) > 0:
            placeholders = ",".join("?" for _ in payload.question_ids)
            q_rows = conn.execute(
                f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders}) ORDER BY order_index ASC",
                [survey_id] + payload.question_ids
            ).fetchall()
        else:
            q_rows = conn.execute("""
                SELECT id, title, question_type FROM questions
                WHERE survey_id = ? AND question_type IN ('number', 'rating', 'nps', 'likert', 'linear_scale', 'single_choice', 'boolean')
                ORDER BY order_index ASC
            """, (survey_id,)).fetchall()

        if len(q_rows) < 2:
            raise HTTPException(status_code=400, detail="Cần tối thiểu 2 câu hỏi để ước lượng mô hình IRT 2PL.")

        q_ids = [q["id"] for q in q_rows]
        item_names = [q["title"] for q in q_rows]

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        resp_ids = [r["id"] for r in resp_rows]
        if len(resp_ids) < 6:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 6 phản hồi để ước lượng mô hình IRT 2PL (hiện có {len(resp_ids)})."
            }

        placeholders_resp = ",".join("?" for _ in resp_ids)
        placeholders_q = ",".join("?" for _ in q_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + q_ids).fetchall()

        resp_map: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_map:
                resp_map[rid] = {}
            resp_map[rid][a["question_id"]] = a["answer_value"]

        raw_matrix = []
        for rid in resp_ids:
            row_dict = resp_map.get(rid, {})
            row_vals = []
            valid_row = True
            for qid in q_ids:
                if qid not in row_dict:
                    valid_row = False
                    break
                val_str = str(row_dict[qid]).strip().lower()
                if val_str in ("true", "yes", "1", "đúng", "dong_y"):
                    row_vals.append(1.0)
                elif val_str in ("false", "no", "0", "sai", "khong"):
                    row_vals.append(0.0)
                else:
                    try:
                        row_vals.append(float(val_str))
                    except (ValueError, TypeError):
                        valid_row = False
                        break
            if valid_row:
                raw_matrix.append(row_vals)

        if len(raw_matrix) < 6:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(raw_matrix)} phản hồi hoàn chỉnh cho cả {len(q_ids)} câu hỏi (yêu cầu tối thiểu 6)."
            }

        res = IRT2PLEngine.analyze_irt_2pl(
            raw_matrix=raw_matrix,
            item_names=item_names,
            binarization_threshold=payload.binarization_threshold,
            max_em_iter=payload.max_em_iter or 35
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="IRT_2PL_MODEL_EVALUATED",
            details={
                "items_count": res.get("num_items"),
                "sample_size": res.get("sample_size"),
                "marginal_reliability": res.get("marginal_reliability"),
                "average_discrimination": res.get("average_discrimination"),
                "average_difficulty": res.get("average_difficulty")
            }
        )

        return res
'''

survival_dropoff_code = '''@router.post("/survival-dropoff", response_model=SurvivalAnalysisOut)
def run_survival_dropoff_analysis(survey_id: str, payload: SurvivalAnalysisRequest):
    """
    Phân tích Sống sót & Thời gian Bỏ dở Khảo sát (Survival Analysis & Time-to-Drop-off Engine;
    Kaplan & Meier 1958, Cox 1972, Mantel 1966, Couper 2001):
    - Ước lượng hàm sống sót phi tham số Kaplan-Meier S(t) với sai số chuẩn Greenwood
    - Đánh giá tỷ lệ duy trì (retention) và tỷ lệ bỏ dở (drop-off) tại các mốc 1p, 3p, 5p, 10p
    - Kiểm định Log-Rank Mantel-Cox so sánh đường cong sống sót giữa 2 nhóm (Thiết bị, Nhân khẩu học)
    - Ước lượng Tỷ số nguy cơ Cox Hazard Ratio (HR) và khoảng tin cậy 95% CI
    - Tự động sinh tọa độ đồ thị hàm bậc thang vector SVG và đoạn thuyết minh chuẩn APA 7th Edition.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        all_q_rows = conn.execute(
            "SELECT id, is_required FROM questions WHERE survey_id = ?",
            (survey_id,)
        ).fetchall()
        total_questions = len(all_q_rows)
        if total_questions == 0:
            raise HTTPException(status_code=400, detail="Khảo sát chưa có câu hỏi nào.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id, duration_seconds, client_metadata_json, review_status, experimental_arm
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id, duration_seconds, client_metadata_json, review_status, experimental_arm
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 5:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 5 phản hồi để phân tích đường cong sống sót (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders = ",".join("?" for _ in resp_ids)

        ans_counts_rows = conn.execute(f"""
            SELECT response_id, COUNT(*) as cnt
            FROM response_answers
            WHERE response_id IN ({placeholders}) AND answer_value IS NOT NULL AND TRIM(answer_value) != ''
            GROUP BY response_id
        """, resp_ids).fetchall()
        ans_count_map = {row["response_id"]: row["cnt"] for row in ans_counts_rows}

        group_map = {}
        grouping_qid = payload.grouping_question_id
        if grouping_qid:
            grp_ans_rows = conn.execute(f"""
                SELECT response_id, answer_value
                FROM response_answers
                WHERE response_id IN ({placeholders}) AND question_id = ?
            """, resp_ids + [grouping_qid]).fetchall()
            for row in grp_ans_rows:
                group_map[row["response_id"]] = str(row["answer_value"]).strip()

        durations = []
        events = []
        group_labels = []

        for r in resp_rows:
            rid = r["id"]
            dur = max(5.0, float(r["duration_seconds"] or 0.0))
            ans_count = ans_count_map.get(rid, 0)
            is_screened_out = (r["review_status"] == "quota_screened_out")

            event = 1 if (ans_count < total_questions or is_screened_out) else 0

            durations.append(dur)
            events.append(event)

            if grouping_qid and rid in group_map and group_map[rid]:
                group_labels.append(group_map[rid])
            elif r["experimental_arm"]:
                group_labels.append(r["experimental_arm"])
            else:
                meta_str = (r["client_metadata_json"] or "").lower()
                if "mobile" in meta_str or "android" in meta_str or "iphone" in meta_str:
                    group_labels.append("Mobile")
                else:
                    group_labels.append("Desktop")

        res = SurvivalDropOffEngine.analyze_survival(
            durations=durations,
            events=events,
            group_labels=group_labels if len(set(group_labels)) >= 2 else None,
            time_milestones=payload.time_milestones
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SURVIVAL_ANALYSIS_EVALUATED",
            details={
                "total_participants": res.get("total_participants"),
                "drop_off_count": res.get("drop_off_count"),
                "completion_rate": res.get("overall_completion_rate"),
                "log_rank_p_value": res.get("log_rank_test", {}).get("p_value") if res.get("log_rank_test") else None
            }
        )

        return res
'''

multilevel_code = '''@router.post("/multilevel", response_model=MultilevelAnalysisOut)
def run_multilevel_analysis(survey_id: str, payload: MultilevelAnalysisRequest):
    """
    Phân tích Mô hình Tuyến tính Thứ bậc Đa cấp (Multilevel Modeling - MLM / HLM;
    Raudenbush & Bryk 2002, Snijders & Bosker 2012, Hox et al. 2017):
    - Khớp mô hình rỗng Unconditional Null Model phân rã phương sai và tính ICC
    - Ước lượng mô hình 2 tầng đầy đủ với hệ số chặn ngẫu nhiên (Random Intercepts) và độ dốc ngẫu nhiên (Random Slopes)
    - Co rút tham số Empirical Bayes (EB Shrinkage Estimates) hiệu chỉnh cỡ mẫu nhỏ của từng cụm/điều tra viên
    - Đánh giá tỷ lệ phương sai giải thích R^2 tầng 1 và tầng 2 theo Snijders & Bosker
    - Kiểm định tỷ số hợp lý LRT so sánh với hồi quy OLS gộp (-2LL Deviance Chi-Square)
    - Tự động sinh tọa độ đường quỹ đạo từng cụm vector SVG và đoạn thuyết minh chuẩn APA 7th Edition.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        y_qid = payload.outcome_question_id
        x_qid = payload.predictor_question_id
        c_qid = payload.cluster_question_id

        all_qids = [y_qid]
        if x_qid:
            all_qids.append(x_qid)
        if c_qid:
            all_qids.append(c_qid)

        placeholders_q = ",".join("?" for _ in all_qids)
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            [survey_id] + all_qids
        ).fetchall()
        q_dict = {q["id"]: q["title"] for q in q_rows}

        if y_qid not in q_dict:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến phụ thuộc (Y) trong khảo sát.")
        if x_qid and x_qid not in q_dict:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến dự báo (X) trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id, enumerator_id, experimental_arm
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id, enumerator_id, experimental_arm
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 8 phản hồi để ước lượng mô hình đa cấp (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        resp_meta_map = {r["id"]: r for r in resp_rows}

        placeholders_resp = ",".join("?" for _ in resp_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + all_qids).fetchall()

        resp_ans: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_ans:
                resp_ans[rid] = {}
            resp_ans[rid][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            ans = resp_ans.get(rid, {})
            if y_qid not in ans:
                continue
            try:
                y_val = float(ans[y_qid])
            except (ValueError, TypeError):
                continue

            x_val = 0.0
            if x_qid:
                if x_qid not in ans:
                    continue
                try:
                    x_val = float(ans[x_qid])
                except (ValueError, TypeError):
                    continue

            # Xác định cluster ID
            cluster_id = None
            if c_qid and c_qid in ans and ans[c_qid]:
                cluster_id = str(ans[c_qid]).strip()
            elif resp_meta_map[rid]["enumerator_id"]:
                cluster_id = f"Enum_{resp_meta_map[rid]['enumerator_id']}"
            elif resp_meta_map[rid]["experimental_arm"]:
                cluster_id = f"Arm_{resp_meta_map[rid]['experimental_arm']}"
            else:
                cluster_id = f"Group_{len(data_rows) % 3 + 1}"

            row_dict = {
                "y": y_val,
                "cluster": cluster_id
            }
            if x_qid:
                row_dict["x"] = x_val
            data_rows.append(row_dict)

        if len(data_rows) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} phản hồi hợp lệ đầy đủ các biến (yêu cầu tối thiểu 8)."
            }

        res = MultilevelModelingEngine.fit_multilevel_model(
            data_rows=data_rows,
            y_var="y",
            x_var="x" if x_qid else None,
            cluster_var="cluster",
            centering=payload.centering or "grand_mean"
        )

        res["dependent_variable"] = q_dict[y_qid]
        res["predictor_variable"] = q_dict.get(x_qid) if x_qid else None
        res["cluster_variable"] = q_dict.get(c_qid, "Điều tra viên / Nhóm thực địa")

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="MULTILEVEL_MODEL_EVALUATED",
            details={
                "outcome_question": q_dict[y_qid],
                "predictor_question": q_dict.get(x_qid),
                "num_clusters": res.get("num_clusters"),
                "sample_size": res.get("total_sample_size"),
                "icc": res.get("null_model", {}).get("icc"),
                "r2_level_1": res.get("random_effects", {}).get("r2_level_1")
            }
        )

        return res
'''


conjoint_code = '''@router.post("/conjoint", response_model=ConjointAnalysisOut)
def run_conjoint_analysis(survey_id: str, payload: ConjointAnalysisRequest):
    """
    Phân tích Đánh đổi Lựa chọn Choice-Based Conjoint (CBC / DCE; McFadden 1974, Green & Srinivasan 1990):
    - Ước lượng Tiện ích Từng phần (Part-Worth Utilities) theo chuẩn Effects Coding
    - Đánh giá Độ quan trọng Tương đối của các Thuộc tính (Attribute Relative Importance %)
    - Sẵn sàng Chi trả (Willingness to Pay - WTP; Hensher et al., 2005)
    - Trực quan hóa tỷ trọng thuộc tính và hồ sơ tiện ích vector SVG
    - Tự động sinh đoạn thuyết minh học thuật chuẩn APA 7th Edition
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        rating_qid = payload.rating_question_id
        attr_qids = payload.attribute_question_ids
        price_qid = payload.price_question_id

        if len(attr_qids) < 2:
            raise HTTPException(status_code=400, detail="Cần tối thiểu 2 câu hỏi thuộc tính để phân tích Conjoint.")

        all_qids = [rating_qid] + attr_qids
        if price_qid and price_qid not in all_qids:
            all_qids.append(price_qid)

        placeholders_q = ",".join("?" for _ in all_qids)
        q_rows = conn.execute(
            f"SELECT id, title, question_type, options_json FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            [survey_id] + all_qids
        ).fetchall()
        q_map = {q["id"]: q for q in q_rows}

        if rating_qid not in q_map:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi đánh giá mức độ ưa thích (Rating).")

        for aq in attr_qids:
            if aq not in q_map:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi thuộc tính {aq} trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 6:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 6 phản hồi để phân tích Conjoint (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + all_qids).fetchall()

        resp_ans: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_ans:
                resp_ans[rid] = {}
            resp_ans[rid][a["question_id"]] = a["answer_value"]

        # Xây dựng cấu hình attributes_config từ options_json của câu hỏi hoặc các giá trị xuất hiện
        attr_config: Dict[str, List[str]] = {}
        price_attr_title = None

        for aq_id in attr_qids:
            q_info = q_map[aq_id]
            title = q_info["title"]
            if aq_id == price_qid:
                price_attr_title = title

            # Trích xuất options_json nếu có
            levels: List[str] = []
            if q_info["options_json"]:
                try:
                    raw_opts = json.loads(q_info["options_json"]) if isinstance(q_info["options_json"], str) else q_info["options_json"]
                    levels = [str(opt).strip() for opt in raw_opts if str(opt).strip()]
                except Exception:
                    pass

            if not levels:
                # Tìm các giá trị trả lời duy nhất
                observed = set()
                for rid in resp_ids:
                    val = resp_ans.get(rid, {}).get(aq_id)
                    if val is not None and str(val).strip():
                        observed.add(str(val).strip())
                levels = sorted(list(observed))

            if len(levels) >= 2:
                attr_config[title] = levels

        if len(attr_config) < 2:
            return {
                "status": "INSUFFICIENT_ATTRIBUTES",
                "message": f"Cần tối thiểu 2 thuộc tính có từ 2 mức độ trở lên (hiện có {len(attr_config)})."
            }

        # Chuyển đổi dữ liệu từng phản hồi thành profiles_data
        profiles_data: List[Dict[str, Any]] = []
        for rid in resp_ids:
            ans = resp_ans.get(rid, {})
            if rating_qid not in ans:
                continue
            try:
                r_val = float(ans[rating_qid])
            except (ValueError, TypeError):
                continue

            profile_entry = {"rating": r_val}
            complete = True
            for aq_id in attr_qids:
                q_title = q_map[aq_id]["title"]
                if aq_id not in ans or not str(ans[aq_id]).strip():
                    complete = False
                    break
                profile_entry[q_title] = str(ans[aq_id]).strip()

            if complete:
                profiles_data.append(profile_entry)

        res = ConjointAnalysisEngine.compute_conjoint_analysis(
            profiles_data=profiles_data,
            attributes_config=attr_config,
            rating_key="rating",
            price_attribute_name=price_attr_title
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CONJOINT_MODEL_EVALUATED",
            details={
                "rating_question_id": rating_qid,
                "attributes_count": len(attr_config),
                "sample_size": res.get("sample_size", 0),
                "r2": res.get("model_fit", {}).get("r_squared")
            }
        )

        return res


@router.post("/conjoint-simulate", response_model=ConjointSimulationOut)
def run_conjoint_simulation(survey_id: str, payload: ConjointSimulationRequest):
    """
    Mô phỏng Thị phần Lựa chọn (Choice Share Market Simulator) theo mô hình Logit (McFadden 1974)
    cho danh sách các hồ sơ sản phẩm đối đầu.
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        ana_req = ConjointAnalysisRequest(
            rating_question_id=payload.rating_question_id,
            attribute_question_ids=payload.attribute_question_ids,
            scope=payload.scope
        )
        ana_res = run_conjoint_analysis(survey_id, ana_req)
        if ana_res.get("status") != "SUCCESS":
            return {
                "status": "ERROR",
                "message": ana_res.get("message", "Không thể ước lượng tiện ích để mô phỏng thị phần.")
            }

        pw = ana_res.get("part_worth_utilities", {})
        intercept = ana_res.get("overall_utility_intercept", 0.0)

        shares = ConjointAnalysisEngine.simulate_choice_shares(
            part_worth_utilities=pw,
            intercept=intercept,
            candidate_profiles=payload.candidate_profiles
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CONJOINT_SIMULATION_EVALUATED",
            details={
                "profiles_count": len(payload.candidate_profiles),
                "scope": payload.scope
            }
        )

        return {
            "status": "SUCCESS",
            "market_shares": shares
        }
'''


lca_code = '''@router.post("/lca", response_model=LCAAnalysisOut)
def run_lca_analysis(survey_id: str, payload: LCAAnalysisRequest):
    """
    Phân tích Lớp Ẩn (Latent Class Analysis - LCA; Goodman 1974, McLachlan & Peel 2000):
    - Thuật toán Expectation-Maximization (EM) phân đoạn người trả lời vào các lớp ẩn xác suất
    - Ước lượng tỷ lệ phân bố lớp ẩn (Class Prevalences) và xác suất phản hồi điều kiện (Item Probabilities)
    - So sánh tiêu chuẩn thông tin AIC, BIC, Sample-Adjusted BIC (SABIC) và Entropy để chọn K tối ưu
    - Trực quan hóa tọa độ song song Vector SVG Profile Plot
    - Tự động sinh đoạn thuyết minh học thuật chuẩn APA 7th Edition
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        item_qids = payload.item_question_ids
        if len(item_qids) < 3:
            raise HTTPException(status_code=400, detail="Cần tối thiểu 3 câu hỏi để phân tích Lớp Ẩn LCA.")

        placeholders_q = ",".join("?" for _ in item_qids)
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            [survey_id] + item_qids
        ).fetchall()
        q_map = {q["id"]: q["title"] for q in q_rows}

        for qid in item_qids:
            if qid not in q_map:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi {qid} trong khảo sát.")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 10 phản hồi để phân tích Lớp Ẩn LCA (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + item_qids).fetchall()

        resp_ans: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_ans:
                resp_ans[rid] = {}
            resp_ans[rid][a["question_id"]] = str(a["answer_value"]).strip()

        # Dữ liệu dạng List[Dict[item_title, answer_value]]
        responses_data: List[Dict[str, str]] = []
        for rid in resp_ids:
            ans = resp_ans.get(rid, {})
            row_dict = {}
            complete = True
            for qid in item_qids:
                if qid not in ans or not ans[qid]:
                    complete = False
                    break
                row_dict[q_map[qid]] = ans[qid]
            if complete:
                responses_data.append(row_dict)

        res = LatentClassAnalysisEngine.compute_lca(
            responses_data=responses_data,
            item_keys=[q_map[qid] for qid in item_qids],
            num_classes=payload.num_classes
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="LCA_MODEL_EVALUATED",
            details={
                "items_count": len(item_qids),
                "optimal_classes": res.get("optimal_classes_count"),
                "sample_size": res.get("sample_size"),
                "entropy": res.get("entropy")
            }
        )

        return res
'''


did_code = '''@router.post("/did", response_model=DiDAnalysisOut)
def run_did_analysis(survey_id: str, payload: DiDAnalysisRequest):
    """
    Phân tích Khác biệt trong Khác biệt (Difference-in-Differences - DiD / TWFE;
    Card & Krueger 1994, Angrist & Pischke 2009):
    - Đánh giá tác động nhân quả thuần túy (ATT) của can thiệp chính sách / khảo sát thử nghiệm
    - Bảng phân rã 2x2 Cell Means (Treatment vs Control qua 2 kỳ Pre vs Post)
    - Hồi quy OLS Hai chiều Cố định (TWFE) kiểm soát xu thế thời gian tự nhiên
    - Ước tính đường quỹ đạo phản thực tế (Counterfactual) theo giả định Xu hướng Song song
    - Trực quan hóa tọa độ Vector SVG và đoạn thuyết minh chuẩn APA 7th Edition
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        y_qid = payload.outcome_question_id
        d_qid = payload.treatment_question_id
        t_qid = payload.time_question_id

        all_qids = [y_qid, d_qid, t_qid]
        placeholders_q = ",".join("?" for _ in all_qids)
        q_rows = conn.execute(
            f"SELECT id, title, question_type FROM questions WHERE survey_id = ? AND id IN ({placeholders_q})",
            [survey_id] + all_qids
        ).fetchall()
        q_map = {q["id"]: q["title"] for q in q_rows}

        if y_qid not in q_map:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến kết quả (Y).")
        if d_qid not in q_map:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi phân loại nhóm can thiệp (Treatment/Control).")
        if t_qid not in q_map:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi phân loại thời điểm (Pre/Post).")

        if payload.scope == "verified_clean":
            resp_rows = conn.execute("""
                SELECT id
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud', 'quota_screened_out')
                  AND (risk_level != 'high' OR review_status = 'verified_valid')
            """, (survey_id,)).fetchall()
        else:
            resp_rows = conn.execute("""
                SELECT id
                FROM responses
                WHERE survey_id = ?
                  AND review_status NOT IN ('verified_fraud')
            """, (survey_id,)).fetchall()

        if len(resp_rows) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 8 phản hồi để ước lượng mô hình DiD (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + all_qids).fetchall()

        resp_ans: Dict[str, Dict[str, str]] = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in resp_ans:
                resp_ans[rid] = {}
            resp_ans[rid][a["question_id"]] = str(a["answer_value"]).strip()

        data_rows: List[Dict[str, Any]] = []
        for rid in resp_ids:
            ans = resp_ans.get(rid, {})
            if y_qid not in ans or d_qid not in ans or t_qid not in ans:
                continue
            try:
                y_val = float(ans[y_qid])
            except (ValueError, TypeError):
                continue

            data_rows.append({
                "y": y_val,
                "treatment": ans[d_qid],
                "time": ans[t_qid]
            })

        res = DifferenceInDifferencesEngine.compute_did_analysis(
            data_rows=data_rows,
            outcome_key="y",
            treatment_key="treatment",
            time_key="time",
            treatment_value=payload.treatment_value,
            post_value=payload.post_value
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="DID_MODEL_EVALUATED",
            details={
                "outcome_question": q_map[y_qid],
                "treatment_question": q_map[d_qid],
                "time_question": q_map[t_qid],
                "att_estimate": res.get("did_treatment_effect", {}).get("att_estimate"),
                "sample_size": res.get("sample_size")
            }
        )

        return res
'''


sem_code = '''@router.post("/sem", response_model=SEMAnalysisOut)
def run_sem_analysis(survey_id: str, payload: SEMAnalysisRequest):
    """
    Mô hình Phương trình Cấu trúc & Phân tích Đường dẫn (Structural Equation Modeling - SEM / Path Analysis;
    Wright 1934, Jöreskog 1970, Hu & Bentler 1999, Kline 2015):
    - Ước lượng đồng thời các phương trình hồi quy cấu trúc nội sinh (Structural Regressions)
    - Hệ số đường dẫn chưa chuẩn hóa B, chuẩn hóa beta, sai số chuẩn SE, z-value, p-value, 95% CI
    - Phân rã tác động: Trực tiếp (Direct), Gián tiếp (Indirect/Mediation qua Sobel/Delta method), Tổng thể (Total)
    - Đánh giá độ phù hợp tổng thể (Global Fit): Chi-square, df, p, CFI, TLI, RMSEA (90% CI), SRMR
    - Trực quan hóa sơ đồ đường dẫn SVG đa tầng và báo cáo học thuật chuẩn APA 7th Edition
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        if not payload.paths:
            return {
                "status": "EMPTY_SPECIFICATION",
                "message": "Vui lòng chọn ít nhất một đường dẫn quan hệ giữa các biến."
            }

        q_rows = conn.execute("SELECT id, title FROM questions WHERE survey_id = ?", (survey_id,)).fetchall()
        q_map = {r["id"]: r["title"] for r in q_rows}

        resp_filter = "AND r.quality_status = 'verified_clean'" if payload.scope == "verified_clean" else ""
        resp_rows = conn.execute(f"""
            SELECT r.id
            FROM responses r
            WHERE r.survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if len(resp_rows) < 10:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 10 phản hồi để ước lượng mô hình SEM (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)
        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp})
        """, resp_ids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            val = a["answer_value"]
            if val is not None:
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    val = None
            by_resp[rid][a["question_id"]] = val

        data_rows = list(by_resp.values())
        paths_dict = [{"source": p.source, "target": p.target} for p in payload.paths]

        res = SEMEngine.fit_path_analysis(
            data_rows=data_rows,
            paths=paths_dict,
            labels=q_map
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SEM_MODEL_EVALUATED",
            details={
                "paths_count": len(payload.paths),
                "sample_size": res.get("sample_size"),
                "status": res.get("status"),
                "scope": payload.scope
            }
        )

        return res
'''


competing_risks_code = '''@router.post("/competing-risks", response_model=CompetingRisksAnalysisOut)
def run_competing_risks_analysis(survey_id: str, payload: CompetingRisksAnalysisRequest):
    """
    Phân tích Nguy cơ Cạnh tranh & Mô hình Suy yếu Chung (Competing Risks & Shared Frailty Survival Engine;
    Fine & Gray 1999, Hougaard 2000, Wienke 2010, Putter et al. 2007):
    - Ước lượng phi tham số Hàm Tích lũy Biến cố (Cumulative Incidence Function - CIF Aalen-Johansen)
    - Phân định các nguyên nhân kết thúc cạnh tranh loại trừ lẫn nhau (Bỏ cuộc, Quota screen-out, Loại trừ gian lận)
    - Lượng hóa độ lệch thổi phồng rủi ro của ước lượng Kaplan-Meier cổ điển (Naive KM Overestimation Bias)
    - Mô hình Suy yếu Chung Gamma (Shared Gamma Frailty) đánh giá tính không đồng nhất giữa các cụm điều tra viên / thiết bị
    - Kiểm định Tỉ số Hợp lý LRT (Self & Liang 1987) và ước lượng Bayes Thực nghiệm (Empirical Bayes)
    - Đồ họa Vector SVG đa đường cong CIF và đoạn thuyết minh chuẩn APA 7th Edition
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        all_q_rows = conn.execute(
            "SELECT id, title, is_required FROM questions WHERE survey_id = ?",
            (survey_id,)
        ).fetchall()
        total_questions = len(all_q_rows)

        resp_filter = ""
        if payload.scope == "verified_clean":
            resp_filter = "AND review_status NOT IN ('verified_fraud', 'quota_screened_out') AND (risk_level != 'high' OR review_status = 'verified_valid')"

        resp_rows = conn.execute(f"""
            SELECT id, duration_seconds, review_status
            FROM responses
            WHERE survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if len(resp_rows) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 8 phản hồi để phân tích nguy cơ cạnh tranh và mô hình suy yếu (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders = ",".join("?" for _ in resp_ids)

        ans_counts_rows = conn.execute(f"""
            SELECT response_id, COUNT(*) as cnt
            FROM response_answers
            WHERE response_id IN ({placeholders}) AND answer_value IS NOT NULL AND TRIM(answer_value) != ''
            GROUP BY response_id
        """, resp_ids).fetchall()
        ans_count_map = {row["response_id"]: row["cnt"] for row in ans_counts_rows}

        event_map = {}
        if payload.event_question_id:
            ev_ans_rows = conn.execute(f"""
                SELECT response_id, answer_value
                FROM response_answers
                WHERE response_id IN ({placeholders}) AND question_id = ?
            """, resp_ids + [payload.event_question_id]).fetchall()
            event_map = {row["response_id"]: str(row["answer_value"]).strip() for row in ev_ans_rows}

        cluster_map = {}
        if payload.cluster_question_id:
            c_ans_rows = conn.execute(f"""
                SELECT response_id, answer_value
                FROM response_answers
                WHERE response_id IN ({placeholders}) AND question_id = ?
            """, resp_ids + [payload.cluster_question_id]).fetchall()
            cluster_map = {row["response_id"]: str(row["answer_value"]).strip() for row in c_ans_rows}

        durations = []
        event_types = []
        cluster_ids = []

        for r in resp_rows:
            rid = r["id"]
            dur = max(5.0, float(r["duration_seconds"] or 60.0))
            durations.append(dur)

            if payload.event_question_id and rid in event_map:
                event_types.append(event_map[rid])
            else:
                st = r["review_status"]
                c_cnt = ans_count_map.get(rid, 0)
                if st == "quota_screened_out":
                    event_types.append("quota_screenout")
                elif st == "verified_fraud":
                    event_types.append("fraud_rejected")
                elif c_cnt < total_questions:
                    event_types.append("voluntary_dropoff")
                else:
                    event_types.append("completed")

            if payload.cluster_question_id and rid in cluster_map:
                cluster_ids.append(cluster_map[rid])
            else:
                cluster_ids.append("Default_Cluster")

        res = CompetingRisksFrailtyEngine.analyze_competing_risks_and_frailty(
            durations=durations,
            event_types=event_types,
            cluster_ids=cluster_ids if payload.cluster_question_id else None,
            time_milestones=payload.time_milestones
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="COMPETING_RISKS_EVALUATED",
            details={
                "sample_size": res.get("sample_size"),
                "competing_causes": res.get("competing_causes"),
                "clusters_count": res.get("shared_frailty_model", {}).get("clusters_count"),
                "scope": payload.scope
            }
        )

        return res
'''


irt_4pl_code = '''@router.post("/irt-4pl", response_model=IRT4PLAnalysisOut)
def run_irt_4pl_analysis(survey_id: str, payload: IRT4PLAnalysisRequest):
    """
    Lý thuyết Ứng đáp Câu hỏi 3 & 4 Tham số Logistic (3PL & 4PL IRT Engine;
    Birnbaum 1968, Lord 1980, Barton & Lord 1981, Magis 2013):
    - Ước lượng độ phân biệt a_i, độ khó b_i, đoán mò c_i và đãng trí/bất cẩn d_i
    - Hàm Thông tin Câu hỏi (IIF) và Hàm Thông tin Bài trắc nghiệm (TIF)
    - Sai số đo lường chuẩn SE(theta) và độ tin cậy có điều kiện
    - Mô phỏng quy trình kiểm tra thích ứng máy tính (CAT Adaptive Testing)
    - Đồ họa Vector SVG đường cong ICC & TIF và đoạn thuyết minh chuẩn APA 7th Edition
    """
    with get_db() as conn:
        survey = conn.execute("SELECT id, title FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not survey:
            raise HTTPException(status_code=404, detail="Khảo sát không tồn tại.")

        if len(payload.question_ids) < 2:
            return {
                "status": "INSUFFICIENT_ITEMS",
                "message": "Cần chọn tối thiểu 2 câu hỏi để phân tích mô hình IRT 3PL/4PL."
            }

        placeholders_q = ",".join("?" for _ in payload.question_ids)
        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q}) AND survey_id = ?
        """, payload.question_ids + [survey_id]).fetchall()
        q_map = {r["id"]: r["title"] for r in q_rows}

        if len(q_map) < 2:
            return {
                "status": "INSUFFICIENT_ITEMS",
                "message": "Không tìm thấy đủ câu hỏi hợp lệ thuộc khảo sát này."
            }

        ordered_qids = [qid for qid in payload.question_ids if qid in q_map]
        item_names = [q_map[qid] for qid in ordered_qids]

        resp_filter = ""
        if payload.scope == "verified_clean":
            resp_filter = "AND review_status NOT IN ('verified_fraud', 'quota_screened_out') AND (risk_level != 'high' OR review_status = 'verified_valid')"

        resp_rows = conn.execute(f"""
            SELECT id
            FROM responses
            WHERE survey_id = ? {resp_filter}
        """, (survey_id,)).fetchall()

        if len(resp_rows) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 8 phản hồi để ước lượng mô hình IRT 3PL/4PL (hiện có {len(resp_rows)})."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + ordered_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            val = a["answer_value"]
            if val is not None:
                try:
                    num_val = float(val)
                except (ValueError, TypeError):
                    num_val = None
            else:
                num_val = None
            by_resp[rid][a["question_id"]] = num_val

        matrix = []
        for rid in resp_ids:
            row_dict = by_resp.get(rid, {})
            row_vals = []
            valid_row = True
            for qid in ordered_qids:
                v = row_dict.get(qid)
                if v is None:
                    valid_row = False
                    break
                row_vals.append(v)
            if valid_row:
                matrix.append(row_vals)

        if len(matrix) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(matrix)} người trả lời đầy đủ các câu hỏi được chọn (cần tối thiểu 8)."
            }

        res = IRT4PLEngine.fit_irt_4pl(
            raw_matrix=matrix,
            item_names=item_names,
            model_type=payload.model_type,
            binarization_threshold=payload.binarization_threshold
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="IRT_4PL_MODEL_EVALUATED",
            details={
                "items_count": len(ordered_qids),
                "model_type": payload.model_type.upper(),
                "sample_size": res.get("sample_size"),
                "scope": payload.scope
            }
        )

        return res
'''


ipw_code = '''@router.post("/ipw", response_model=IPWAnalysisOut)
def run_ipw_analysis(survey_id: str, payload: IPWAnalysisRequest):
    """
    Ước lượng tác động nhân quả qua Trọng số Xác suất Nghịch đảo (IPW) & Ước lượng Vững Kép (Doubly Robust / AIPW).
    (Rosenbaum & Rubin 1983; Robins et al. 1994; Lunceford & Davidian 2004; Austin & Stuart 2015)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        all_qids = [payload.treatment_question_id, payload.outcome_question_id] + payload.covariate_question_ids
        unique_qids = list(dict.fromkeys(all_qids))
        placeholders_q = ",".join("?" for _ in unique_qids)

        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, unique_qids).fetchall()

        labels = {q["id"]: q["title"] for q in q_rows}

        if payload.treatment_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi can thiệp (treatment).")
        if payload.outcome_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi kết quả (outcome).")
        for cq in payload.covariate_question_ids:
            if cq not in labels:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy biến đồng biến: {cq}")

        query_resp = "SELECT id FROM responses WHERE survey_id = ?"
        params_resp = [survey_id]
        if payload.scope == "verified_clean":
            query_resp += " AND status = 'completed' AND quality_score >= 0.7"

        resp_rows = conn.execute(query_resp, params_resp).fetchall()
        if not resp_rows:
            return {
                "status": "NO_DATA",
                "message": "Không có phản hồi nào phù hợp với phạm vi phân tích."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + unique_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            row_dict = {}
            t_val = ans_dict.get(payload.treatment_question_id)
            y_val = ans_dict.get(payload.outcome_question_id)
            if t_val is not None and y_val is not None:
                row_dict[payload.treatment_question_id] = t_val
                row_dict[payload.outcome_question_id] = y_val
                all_covs = True
                for cq in payload.covariate_question_ids:
                    cv = ans_dict.get(cq)
                    if cv is None:
                        all_covs = False
                        break
                    row_dict[cq] = cv
                if all_covs:
                    data_rows.append(row_dict)

        if len(data_rows) < 16:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} người trả lời đầy đủ biến can thiệp, kết quả và đồng biến (cần tối thiểu 16)."
            }

        res = IPWDoublyRobustEngine.estimate_causal_effects(
            data_rows=data_rows,
            treatment_key=payload.treatment_question_id,
            outcome_key=payload.outcome_question_id,
            covariate_keys=payload.covariate_question_ids,
            treatment_value=payload.treatment_value,
            weight_scheme=payload.weight_scheme,
            trim_weights=payload.trim_weights,
            labels=labels
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="IPW_DOUBLY_ROBUST_EVALUATED",
            details={
                "weight_scheme": payload.weight_scheme.upper(),
                "sample_size": res.get("sample_size"),
                "covariates_count": len(payload.covariate_question_ids),
                "scope": payload.scope
            }
        )

        return res
'''


gam_code = '''@router.post("/gam", response_model=GAMSplineAnalysisOut)
def run_gam_spline_analysis(survey_id: str, payload: GAMSplineAnalysisRequest):
    """
    Ước lượng Mô hình GAM & Hồi quy Spline Trơn (Generalized Additive Models & Natural Splines).
    (Hastie & Tibshirani 1990; Wood 2017; Green & Silverman 1994)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        target_qids = [payload.predictor_question_id, payload.outcome_question_id]
        placeholders_q = ",".join("?" for _ in target_qids)

        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, target_qids).fetchall()

        labels = {q["id"]: q["title"] for q in q_rows}

        if payload.predictor_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến dự báo (predictor).")
        if payload.outcome_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến kết quả (outcome).")

        query_resp = "SELECT id FROM responses WHERE survey_id = ?"
        params_resp = [survey_id]
        if payload.scope == "verified_clean":
            query_resp += " AND status = 'completed' AND quality_score >= 0.7"

        resp_rows = conn.execute(query_resp, params_resp).fetchall()
        if not resp_rows:
            return {
                "status": "NO_DATA",
                "message": "Không có phản hồi nào phù hợp với phạm vi phân tích."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + target_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            xv = ans_dict.get(payload.predictor_question_id)
            yv = ans_dict.get(payload.outcome_question_id)
            if xv is not None and yv is not None:
                data_rows.append({
                    payload.predictor_question_id: xv,
                    payload.outcome_question_id: yv
                })

        if len(data_rows) < 16:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} người trả lời đầy đủ biến dự báo và kết quả (cần tối thiểu 16)."
            }

        res = GAMSplineEngine.fit_gam_spline(
            data_rows=data_rows,
            predictor_key=payload.predictor_question_id,
            outcome_key=payload.outcome_question_id,
            n_knots=payload.n_knots,
            smoothing_penalty=payload.smoothing_penalty,
            labels=labels
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="GAM_SPLINE_MODEL_EVALUATED",
            details={
                "n_knots": payload.n_knots,
                "smoothing_penalty": payload.smoothing_penalty,
                "sample_size": res.get("sample_size"),
                "scope": payload.scope
            }
        )

        return res
'''


quantile_code = '''@router.post("/quantile-regression", response_model=QuantileRegressionOut)
def run_quantile_regression_analysis(survey_id: str, payload: QuantileRegressionRequest):
    """
    Ước lượng Hồi quy Phân vị & Hiệu ứng Phân phối Có điều kiện (Quantile Regression & Distributional Effects).
    (Koenker & Bassett 1978; Koenker 2005; Angrist & Pischke 2009)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        cov_ids = payload.covariate_question_ids or []
        all_qids = [payload.predictor_question_id, payload.outcome_question_id] + cov_ids
        unique_qids = list(dict.fromkeys(all_qids))
        placeholders_q = ",".join("?" for _ in unique_qids)

        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, unique_qids).fetchall()

        labels = {q["id"]: q["title"] for q in q_rows}

        if payload.predictor_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến dự báo (predictor).")
        if payload.outcome_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến kết quả (outcome).")
        for cq in cov_ids:
            if cq not in labels:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy biến đồng biến: {cq}")

        query_resp = "SELECT id FROM responses WHERE survey_id = ?"
        params_resp = [survey_id]
        if payload.scope == "verified_clean":
            query_resp += " AND status = 'completed' AND quality_score >= 0.7"

        resp_rows = conn.execute(query_resp, params_resp).fetchall()
        if not resp_rows:
            return {
                "status": "NO_DATA",
                "message": "Không có phản hồi nào phù hợp với phạm vi phân tích."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + unique_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            xv = ans_dict.get(payload.predictor_question_id)
            yv = ans_dict.get(payload.outcome_question_id)
            if xv is not None and yv is not None:
                row_dict = {
                    payload.predictor_question_id: xv,
                    payload.outcome_question_id: yv
                }
                all_covs = True
                for cq in cov_ids:
                    cv = ans_dict.get(cq)
                    if cv is None:
                        all_covs = False
                        break
                    row_dict[cq] = cv
                if all_covs:
                    data_rows.append(row_dict)

        if len(data_rows) < 16:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} người trả lời đầy đủ biến dự báo, kết quả và đồng biến (cần tối thiểu 16)."
            }

        res = QuantileRegressionEngine.fit_quantile_regression(
            data_rows=data_rows,
            predictor_key=payload.predictor_question_id,
            outcome_key=payload.outcome_question_id,
            covariate_keys=cov_ids,
            quantiles=payload.quantiles,
            labels=labels
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="QUANTILE_REGRESSION_EVALUATED",
            details={
                "quantiles": payload.quantiles or [0.10, 0.25, 0.50, 0.75, 0.90],
                "sample_size": res.get("sample_size"),
                "covariates_count": len(cov_ids),
                "scope": payload.scope
            }
        )

        return res
'''


g_theory_code = '''@router.post("/g-theory", response_model=GTheoryAnalysisOut)
def run_g_theory_analysis(survey_id: str, payload: GTheoryAnalysisRequest):
    """
    Ước lượng Lý thuyết Khái quát hóa Đo lường (Generalizability Theory: G-Study & D-Study).
    (Cronbach et al. 1972; Brennan 2001; Shavelson & Webb 1991)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        target_qids = list(dict.fromkeys(payload.item_question_ids))
        if payload.rater_question_id:
            target_qids.append(payload.rater_question_id)
            target_qids = list(dict.fromkeys(target_qids))

        placeholders_q = ",".join("?" for _ in target_qids)

        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, target_qids).fetchall()

        labels = {q["id"]: q["title"] for q in q_rows}

        for iq in payload.item_question_ids:
            if iq not in labels:
                raise HTTPException(status_code=400, detail=f"Không tìm thấy câu hỏi đo lường: {iq}")

        query_resp = "SELECT id FROM responses WHERE survey_id = ?"
        params_resp = [survey_id]
        if payload.scope == "verified_clean":
            query_resp += " AND status = 'completed' AND quality_score >= 0.7"

        resp_rows = conn.execute(query_resp, params_resp).fetchall()
        if not resp_rows:
            return {
                "status": "NO_DATA",
                "message": "Không có phản hồi nào phù hợp với phạm vi phân tích."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + target_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            row_dict = {"respondent_id": rid}
            all_valid = True
            for iq in payload.item_question_ids:
                v = ans_dict.get(iq)
                if v is None:
                    all_valid = False
                    break
                row_dict[iq] = v
            if payload.rater_question_id:
                rv = ans_dict.get(payload.rater_question_id)
                row_dict[payload.rater_question_id] = rv
            if all_valid:
                data_rows.append(row_dict)

        if len(data_rows) < 8:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} người trả lời đầy đủ các câu hỏi được chọn (cần tối thiểu 8)."
            }

        res = GTheoryEngine.run_g_study_two_facet(
            data_rows=data_rows,
            person_key="respondent_id",
            item_keys=payload.item_question_ids,
            rater_key=payload.rater_question_id,
            labels=labels
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="G_THEORY_MODEL_EVALUATED",
            details={
                "items_count": len(payload.item_question_ids),
                "has_rater": bool(payload.rater_question_id),
                "sample_size": res.get("sample_size"),
                "scope": payload.scope
            }
        )

        return res
'''


rdd_code = '''@router.post("/rdd", response_model=RDDAnalysisOut)
def run_rdd_analysis(survey_id: str, payload: RDDAnalysisRequest):
    """
    Ước lượng Thiết kế Gián đoạn Hồi quy Sắc nét (Sharp Regression Discontinuity Design / Sharp RDD).
    (Thistlethwaite & Campbell 1960; Hahn et al. 2001; Imbens & Kalyanaraman 2012; Calonico et al. 2014)
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        target_qids = [payload.running_question_id, payload.outcome_question_id]
        placeholders_q = ",".join("?" for _ in target_qids)

        q_rows = conn.execute(f"""
            SELECT id, title FROM questions WHERE id IN ({placeholders_q})
        """, target_qids).fetchall()

        labels = {q["id"]: q["title"] for q in q_rows}

        if payload.running_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến chỉ định (running variable).")
        if payload.outcome_question_id not in labels:
            raise HTTPException(status_code=400, detail="Không tìm thấy câu hỏi biến kết quả (outcome).")

        query_resp = "SELECT id FROM responses WHERE survey_id = ?"
        params_resp = [survey_id]
        if payload.scope == "verified_clean":
            query_resp += " AND status = 'completed' AND quality_score >= 0.7"

        resp_rows = conn.execute(query_resp, params_resp).fetchall()
        if not resp_rows:
            return {
                "status": "NO_DATA",
                "message": "Không có phản hồi nào phù hợp với phạm vi phân tích."
            }

        resp_ids = [r["id"] for r in resp_rows]
        placeholders_resp = ",".join("?" for _ in resp_ids)

        ans_rows = conn.execute(f"""
            SELECT response_id, question_id, answer_value
            FROM response_answers
            WHERE response_id IN ({placeholders_resp}) AND question_id IN ({placeholders_q})
        """, resp_ids + target_qids).fetchall()

        by_resp = {}
        for a in ans_rows:
            rid = a["response_id"]
            if rid not in by_resp:
                by_resp[rid] = {}
            by_resp[rid][a["question_id"]] = a["answer_value"]

        data_rows = []
        for rid in resp_ids:
            ans_dict = by_resp.get(rid, {})
            xv = ans_dict.get(payload.running_question_id)
            yv = ans_dict.get(payload.outcome_question_id)
            if xv is not None and yv is not None:
                data_rows.append({
                    payload.running_question_id: xv,
                    payload.outcome_question_id: yv
                })

        if len(data_rows) < 20:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Chỉ có {len(data_rows)} người trả lời đầy đủ biến chỉ định và kết quả (cần tối thiểu 20)."
            }

        res = RDDEngine.fit_sharp_rdd(
            data_rows=data_rows,
            running_key=payload.running_question_id,
            outcome_key=payload.outcome_question_id,
            cutoff=payload.cutoff,
            bandwidth=payload.bandwidth,
            polynomial_order=payload.polynomial_order,
            labels=labels
        )

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="RDD_MODEL_EVALUATED",
            details={
                "cutoff": payload.cutoff,
                "bandwidth": res.get("bandwidth"),
                "sample_size": res.get("sample_size"),
                "effective_sample_size": res.get("effective_sample_size"),
                "scope": payload.scope
            }
        )

        return res
'''


def clean_route_block(block):
    idx = block.find('@router.')
    if idx != -1:
        return block[idx:].strip()
    return block.strip()

sections = [
    header.strip(),
    modern_get_survey_analytics.strip(),
    benford_code.strip(),
    clean_route_block(qualitative_code),
    clean_route_block(crosstab_code),
    clean_route_block(reliability_code),
    clean_route_block(longitudinal_code),
    clean_route_block(quotas_raking_code),
    clean_route_block(dif_code),
    clean_route_block(pacing_code),
    clean_route_block(outliers_code),
    clean_route_block(efa_code),
    clean_route_block(ttest_code),
    clean_route_block(anova_code),
    clean_route_block(correlation_code),
    clean_route_block(regression_code),
    clean_route_block(power_code),
    clean_route_block(split_ballot_code),
    rasch_get.strip(),
    clean_route_block(rasch_post),
    clusters_get.strip(),
    clean_route_block(clusters_post),
    similarity_get.strip(),
    clean_route_block(similarity_post),
    spatial_code.strip(),
    mediation_code.strip(),
    clean_route_block(non_parametric_code),
    clean_route_block(missing_data_code),
    clean_route_block(scale_equating_code),
    clean_route_block(measurement_invariance_code),
    clean_route_block(cmb_code),
    clean_route_block(moderation_code),
    clean_route_block(moderated_mediation_code),
    clean_route_block(complex_sampling_code),
    psm_code.strip(),
    topic_model_code.strip(),
    network_code.strip(),
    irt_2pl_code.strip(),
    survival_dropoff_code.strip(),
    multilevel_code.strip(),
    conjoint_code.strip(),
    lca_code.strip(),
    did_code.strip(),
    clean_route_block(sem_code),
    clean_route_block(competing_risks_code),
    clean_route_block(irt_4pl_code),
    clean_route_block(ipw_code),
    clean_route_block(gam_code),
    clean_route_block(quantile_code),
    clean_route_block(g_theory_code),
    clean_route_block(rdd_code)
]

full_analytics_code = '\n\n\n'.join(s for s in sections if s) + '\n'

with open('backend/app/routes/analytics.py', 'w', encoding='utf-8') as f:
    f.write(full_analytics_code)

print(f"Successfully generated analytics.py with {len(full_analytics_code.splitlines())} lines.")
