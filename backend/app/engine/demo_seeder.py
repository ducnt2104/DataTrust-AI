import json
import uuid
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import sqlite3

from app.engine.quality_engine import QualityEngine
from app.database import record_audit_log

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class DemoAcademicSeeder:
    """
    Trình khởi tạo khảo sát nghiên cứu khoa học và tập dữ liệu thực nghiệm mẫu.
    Được thiết kế phục vụ hội đồng thẩm định, ban giám khảo (KHKT, ISEF, ViSEF)
    và các nhà nghiên cứu trải nghiệm ngay lập tức toàn bộ chu trình kiểm định dữ liệu:
    - 7 tầng kiểm định chất lượng (Quality Engine).
    - Phân tích tương quan độ tin cậy thang đo Cronbach's Alpha (Alpha >= 0.80).
    - Phân tích bảng ngẫu nhiên 2 chiều & Chi-square (Cross-Tabulation).
    - Phân tích định tính ngữ nghĩa tiếng Việt (Qualitative NLP Engine).
    - Tự động làm sạch dữ liệu loại trừ Speeders / Straightliners (Don Dillman Rules).
    - Xuất hồ sơ học thuật 4-trong-1 (SPSS, Stata, R, Python) và Chứng thư A4.
    """

    CLEAN_COMMENTS = [
        "Hệ thống số hóa giúp sinh viên tra cứu và nộp bài tập thuận tiện, cần bổ sung xác thực hai lớp.",
        "Ứng dụng AI hỗ trợ tổng hợp tài liệu nghiên cứu nhanh chóng nhưng cần quy định liêm chính học thuật rõ ràng.",
        "Độ tin cậy của dữ liệu khảo sát là yếu tố sống còn cho các công bố khoa học quốc tế uy tín.",
        "Nhà trường nên tổ chức thêm các buổi tập huấn hướng dẫn sinh viên sử dụng công cụ AI có trách nhiệm.",
        "Hạ tầng mạng wifi tại các giảng đường lớn cần được nâng cấp băng thông vào giờ cao điểm học tập.",
        "Rất ủng hộ việc áp dụng chữ ký số và công nghệ chuỗi băm để kiểm định tính trung thực của phiếu điều tra.",
        "Cần có cơ chế phát hiện các tài khoản trả lời bừa hoặc làm bài quá nhanh để loại trừ dữ liệu rác.",
        "Dữ liệu khảo sát số hóa cần được công khai minh bạch để các nhóm nghiên cứu có thể đối chiếu chéo khi cần.",
        "Việc tích hợp trí tuệ nhân tạo vào xử lý dữ liệu định tính giúp tiết kiệm rất nhiều thời gian phân loại.",
        "Cần quy định chuẩn hóa biến số và từ điển dữ liệu ngay từ khâu thiết kế câu hỏi khảo sát.",
        "Các phần mềm thống kê như SPSS và R cần được nhà trường cấp bản quyền rộng rãi hơn cho sinh viên.",
        "Hạ tầng máy chủ phục vụ khảo sát hoạt động rất mượt mà, giao diện trực quan và dễ thao tác.",
        "Đề xuất bổ sung thêm các tính năng phân tích trực quan hóa dữ liệu theo thời gian thực.",
        "Bảo vệ quyền riêng tư và ẩn danh người trả lời là tiêu chí quan trọng nhất để thu thập số liệu trung thực.",
        "Chất lượng đường truyền tại ký túc xá cần được cải thiện để sinh viên truy cập tài nguyên số thuận lợi.",
        "Nên khuyến khích giảng viên ứng dụng AI trong việc gợi ý tài liệu học tập theo năng lực từng học viên.",
        "Công tác kiểm tra tính toàn vẹn của dữ liệu nghiên cứu nên được đưa vào quy trình thẩm định đề tài.",
        "Nền tảng khảo sát cần hỗ trợ giao diện thân thiện trên điện thoại thông minh để tăng tỷ lệ phản hồi.",
        "Các báo cáo phân tích tự động giúp sinh viên nắm bắt nhanh xu hướng dữ liệu trước khi viết báo cáo.",
        "Cần có hướng dẫn cụ thể về việc trích dẫn nguồn khi sử dụng nội dung do AI tạo ra trong luận văn.",
        "Dữ liệu khảo sát cần được lưu trữ bảo mật lâu dài phục vụ các nghiên cứu dọc theo thời gian.",
        "Hệ thống cảnh báo câu trả lời bất thường hoạt động rất chuẩn xác, giúp lọc mẫu sạch hiệu quả.",
        "Nên tích hợp thêm tính năng xuất biểu đồ chất lượng cao dạng SVG để đưa vào kỷ yếu hội thảo.",
        "Giao diện khảo sát rất chuyên nghiệp, các thang đo được thiết kế rõ ràng và dễ hiểu.",
        "Đề xuất mở rộng các buổi tọa đàm về đạo đức trí tuệ nhân tạo trong nghiên cứu khoa học.",
        "Quy trình làm sạch dữ liệu tự động giúp giảm thiểu tối đa sai sót chủ quan của người nhập liệu.",
        "Nền tảng này rất hữu ích cho các dự án nghiên cứu khoa học sinh viên và hội đồng nghiệm thu.",
        "Tính năng chuỗi băm bất biến giúp tăng độ tin cậy tuyệt đối cho kết quả khảo sát thực địa."
    ]

    @classmethod
    def seed_academic_study(cls, conn: sqlite3.Connection) -> Dict[str, Any]:
        """
        Khởi tạo khảo sát hoàn chỉnh kèm 35 phản hồi thực nghiệm chuẩn khoa học
        """
        survey_id = str(uuid.uuid4())
        created_dt = datetime.now(timezone.utc) - timedelta(hours=3)
        created_at_iso = created_dt.isoformat()
        public_slug = f"chuyen-doi-so-ai-edu-{uuid.uuid4().hex[:6]}"

        title = "Khảo sát Đánh giá Chuyển đổi Số và Ứng dụng AI trong Giáo dục Đại học"
        description = (
            "Nghiên cứu thực nghiệm về mức độ sẵn sàng ứng dụng trí tuệ nhân tạo, chất lượng hạ tầng số "
            "và tính toàn vẹn dữ liệu trong môi trường học thuật theo chuẩn Don Dillman & AAPOR 2003."
        )
        instructions = (
            "Kính gửi Quý Thầy/Cô và các bạn Sinh viên, khảo sát gồm 6 câu hỏi đo lường. "
            "Toàn bộ dữ liệu được bảo vệ và kiểm định bởi chuỗi băm bất biến DataTrust Ledger."
        )

        settings = {
            "quality_settings": {
                "speed_threshold_factor": 1.0,
                "duplicate_threshold": 0.85,
                "straightlining_tolerance": 0.0
            }
        }

        # 1. Tạo bản ghi khảo sát trong surveys
        conn.execute("""
            INSERT INTO surveys (
                id, title, description, instructions, status, public_slug, version,
                created_at, updated_at, settings_json
            ) VALUES (?, ?, ?, ?, 'published', ?, 1, ?, ?, ?)
        """, (
            survey_id, title, description, instructions, public_slug,
            created_at_iso, created_at_iso, json.dumps(settings, ensure_ascii=False)
        ))

        # 2. Tạo 6 câu hỏi chuẩn học thuật
        questions_spec = [
            {
                "id": str(uuid.uuid4()),
                "order_index": 0,
                "question_type": "single_choice",
                "title": "Giới tính của bạn",
                "description": "Thông tin nhân khẩu học phục vụ phân tầng mẫu",
                "is_required": 1,
                "options": [
                    {"id": "nam", "label": "Nam"},
                    {"id": "nu", "label": "Nữ"},
                    {"id": "khac", "label": "Khác"}
                ],
                "logic_rules": []
            },
            {
                "id": str(uuid.uuid4()),
                "order_index": 1,
                "question_type": "single_choice",
                "title": "Khối ngành đào tạo hiện tại",
                "description": "Lĩnh vực chuyên môn theo chuẩn phân loại giáo dục",
                "is_required": 1,
                "options": [
                    {"id": "cntt_kt", "label": "Khoa học Kỹ thuật & Công nghệ"},
                    {"id": "kinh_te", "label": "Kinh tế & Quản lý"},
                    {"id": "xh_nv", "label": "Khoa học Xã hội & Nhân văn"},
                    {"id": "y_duoc", "label": "Khoa học Y Dược"}
                ],
                "logic_rules": []
            },
            {
                "id": str(uuid.uuid4()),
                "order_index": 2,
                "question_type": "rating",
                "title": "Hạ tầng CNTT và phần mềm tại cơ sở đào tạo đáp ứng tốt nhu cầu học tập và nghiên cứu",
                "description": "Thang đo Likert 1 (Rất không đồng ý) đến 5 (Rất đồng ý)",
                "is_required": 1,
                "options": [],
                "logic_rules": []
            },
            {
                "id": str(uuid.uuid4()),
                "order_index": 3,
                "question_type": "rating",
                "title": "Mức độ sẵn sàng và tần suất ứng dụng các công cụ AI trong học thuật",
                "description": "Thang đo Likert 1 (Rất thấp) đến 5 (Rất cao)",
                "is_required": 1,
                "options": [],
                "logic_rules": []
            },
            {
                "id": str(uuid.uuid4()),
                "order_index": 4,
                "question_type": "rating",
                "title": "Mức độ tin cậy và minh bạch của dữ liệu số hóa trong quản lý học thuật",
                "description": "Thang đo Likert 1 (Hoàn toàn không tin cậy) đến 5 (Rất tin cậy)",
                "is_required": 1,
                "options": [],
                "logic_rules": []
            },
            {
                "id": str(uuid.uuid4()),
                "order_index": 5,
                "question_type": "rating",
                "title": "Mức độ hiệu quả của chính sách bảo vệ dữ liệu và liêm chính học thuật",
                "description": "Thang đo Likert 1 (Rất kém hiệu quả) đến 5 (Rất hiệu quả)",
                "is_required": 1,
                "options": [],
                "logic_rules": []
            },
            {
                "id": str(uuid.uuid4()),
                "order_index": 6,
                "question_type": "long_text",
                "title": "Đóng góp ý kiến hoặc đề xuất giải pháp nhằm nâng cao độ tin cậy của dữ liệu khảo sát số",
                "description": "Ý kiến mở phục vụ phân tích định tính chủ đề và cảm xúc (NLP)",
                "is_required": 0,
                "options": [],
                "logic_rules": []
            }
        ]

        for q in questions_spec:
            conn.execute("""
                INSERT INTO questions (
                    id, survey_id, order_index, question_type, title, description,
                    is_required, options_json, logic_rules_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                q["id"], survey_id, q["order_index"], q["question_type"], q["title"],
                q["description"], q["is_required"], json.dumps(q["options"], ensure_ascii=False),
                json.dumps(q["logic_rules"], ensure_ascii=False), created_at_iso
            ))

        # Lưu snapshot phiên bản 1
        conn.execute("""
            INSERT INTO survey_versions (id, survey_id, version, title, description, questions_json, created_at)
            VALUES (?, ?, 1, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), survey_id, title, description,
            json.dumps(questions_spec, ensure_ascii=False), created_at_iso
        ))

        # Ghi audit log tạo khảo sát
        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="CREATE_SURVEY",
            details={"title": title, "version": 1, "status": "published"},
            created_at=created_at_iso
        )

        q_gender, q_faculty, q_infra, q_ai, q_trust, q_policy, q_text = questions_spec

        # 3. Danh sách cấu hình phản hồi mẫu (35 phản hồi)
        # 28 Mẫu sạch được tối ưu hóa: Pairwise similarity <= 0.60, Cronbach's Alpha = 0.8989
        clean_profiles = [
            ("khac", "cntt_kt", 3, 4, 3, 3, 115.0),
            ("khac", "xh_nv", 4, 3, 3, 4, 140.0),
            ("khac", "xh_nv", 3, 3, 2, 3, 98.0),
            ("nu", "kinh_te", 4, 3, 4, 4, 160.0),
            ("nu", "y_duoc", 4, 4, 4, 5, 85.0),
            ("khac", "kinh_te", 2, 2, 2, 3, 125.0),
            ("khac", "cntt_kt", 5, 4, 4, 5, 170.0),
            ("nam", "kinh_te", 4, 5, 4, 4, 110.0),
            ("nam", "xh_nv", 3, 4, 4, 3, 95.0),
            ("nam", "cntt_kt", 4, 5, 5, 4, 130.0),
            ("khac", "y_duoc", 2, 3, 3, 2, 105.0),
            ("nu", "y_duoc", 3, 2, 3, 3, 145.0),
            ("khac", "cntt_kt", 4, 4, 5, 4, 118.0),
            ("khac", "y_duoc", 3, 3, 4, 3, 155.0),
            ("nam", "kinh_te", 2, 3, 3, 3, 122.0),
            ("khac", "xh_nv", 4, 5, 5, 5, 102.0),
            ("nu", "kinh_te", 4, 4, 5, 4, 90.0),
            ("nam", "kinh_te", 4, 3, 3, 4, 135.0),
            ("nam", "y_duoc", 3, 2, 2, 3, 165.0),
            ("nam", "y_duoc", 4, 4, 3, 4, 142.0),
            ("nam", "y_duoc", 2, 3, 4, 2, 128.0),
            ("khac", "xh_nv", 5, 5, 4, 5, 112.0),
            ("nu", "kinh_te", 2, 3, 2, 2, 108.0),
            ("nam", "kinh_te", 3, 3, 4, 3, 150.0),
            ("khac", "kinh_te", 4, 4, 4, 3, 119.0),
            ("nu", "kinh_te", 3, 4, 4, 4, 134.0),
            ("nu", "kinh_te", 3, 2, 2, 3, 126.0),
            ("nam", "cntt_kt", 2, 2, 3, 2, 99.0)
        ]

        # Vị trí thực địa mẫu quanh các trường đại học lớn (Hà Nội & TP.HCM)
        university_hubs = [
            (21.0045, 105.8432, "ĐHBK Hà Nội"),
            (21.0378, 105.7812, "ĐHQG Hà Nội"),
            (10.7725, 106.6575, "ĐHBK TP.HCM"),
            (10.8700, 106.8030, "ĐHQG TP.HCM"),
            (21.0285, 105.8542, "Khu vực Hoàn Kiếm, HN")
        ]

        enumerators = ["NV_HA_NOI_01", "NV_HA_NOI_02", "NV_HCM_01", ""]

        generated_responses: List[Dict[str, Any]] = []

        # 3.1. Thêm 28 phản hồi hợp lệ (Clean Responses)
        for i, (gender, faculty, r_infra, r_ai, r_trust, r_policy, duration) in enumerate(clean_profiles):
            resp_id = str(uuid.uuid4())
            sub_dt = created_dt + timedelta(minutes=i * 4 + 5)
            start_dt = sub_dt - timedelta(seconds=duration)
            
            hub_lat, hub_lon, hub_name = university_hubs[i % len(university_hubs)]
            lat_jitter = hub_lat + (random.random() - 0.5) * 0.006
            lon_jitter = hub_lon + (random.random() - 0.5) * 0.006

            answers = {
                q_gender["id"]: gender,
                q_faculty["id"]: faculty,
                q_infra["id"]: r_infra,
                q_ai["id"]: r_ai,
                q_trust["id"]: r_trust,
                q_policy["id"]: r_policy,
                q_text["id"]: cls.CLEAN_COMMENTS[i]
            }

            metadata = {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
                "screen_width": 1920,
                "screen_height": 1080,
                "device_type": "desktop" if i % 3 != 0 else "mobile",
                "location": {
                    "latitude": round(lat_jitter, 6),
                    "longitude": round(lon_jitter, 6),
                    "accuracy": 15.0,
                    "hub": hub_name
                }
            }

            enum_id = enumerators[i % len(enumerators)]

            generated_responses.append({
                "id": resp_id,
                "answers": answers,
                "duration_seconds": duration,
                "started_at": start_dt.isoformat(),
                "submitted_at": sub_dt.isoformat(),
                "client_metadata": metadata,
                "enumerator_id": enum_id,
                "resp_type": "clean"
            })

        # 3.2. Thêm 3 phản hồi Speeders (Làm bài siêu tốc < 5 giây)
        speeders_data = [
            ("nam", "cntt_kt", 3, 3, 3, 3, 2.5),
            ("nu", "kinh_te", 4, 4, 4, 4, 3.2),
            ("nam", "xh_nv", 5, 5, 5, 5, 4.1)
        ]
        for j, (gender, faculty, r1, r2, r3, r4, dur) in enumerate(speeders_data):
            resp_id = str(uuid.uuid4())
            sub_dt = created_dt + timedelta(minutes=120 + j * 5)
            start_dt = sub_dt - timedelta(seconds=dur)
            answers = {
                q_gender["id"]: gender,
                q_faculty["id"]: faculty,
                q_infra["id"]: r1,
                q_ai["id"]: r2,
                q_trust["id"]: r3,
                q_policy["id"]: r4,
                q_text["id"]: "ok"
            }
            generated_responses.append({
                "id": resp_id,
                "answers": answers,
                "duration_seconds": dur,
                "started_at": start_dt.isoformat(),
                "submitted_at": sub_dt.isoformat(),
                "client_metadata": {"device_type": "mobile", "user_agent": "SpeedBot/1.0"},
                "enumerator_id": "",
                "resp_type": "speeder"
            })

        # 3.3. Thêm 2 phản hồi Straightliners (Chọn 1 cột duy nhất across ratings)
        straightliners_data = [
            ("nam", "cntt_kt", 5, 5, 5, 5, 80.0, "tất cả đều 5 sao tuyệt vời"),
            ("nu", "xh_nv", 1, 1, 1, 1, 75.0, "tất cả đều kém hoàn toàn")
        ]
        for k, (gender, faculty, r1, r2, r3, r4, dur, comment) in enumerate(straightliners_data):
            resp_id = str(uuid.uuid4())
            sub_dt = created_dt + timedelta(minutes=140 + k * 6)
            start_dt = sub_dt - timedelta(seconds=dur)
            answers = {
                q_gender["id"]: gender,
                q_faculty["id"]: faculty,
                q_infra["id"]: r1,
                q_ai["id"]: r2,
                q_trust["id"]: r3,
                q_policy["id"]: r4,
                q_text["id"]: comment
            }
            generated_responses.append({
                "id": resp_id,
                "answers": answers,
                "duration_seconds": dur,
                "started_at": start_dt.isoformat(),
                "submitted_at": sub_dt.isoformat(),
                "client_metadata": {"device_type": "desktop"},
                "enumerator_id": "NV_HA_NOI_01",
                "resp_type": "straightliner"
            })

        # 3.4. Thêm 1 phản hồi văn bản vô nghĩa (Gibberish Text)
        resp_id = str(uuid.uuid4())
        sub_dt = created_dt + timedelta(minutes=160)
        start_dt = sub_dt - timedelta(seconds=68.0)
        answers = {
            q_gender["id"]: "nam",
            q_faculty["id"]: "cntt_kt",
            q_infra["id"]: 4,
            q_ai["id"]: 4,
            q_trust["id"]: 3,
            q_policy["id"]: 4,
            q_text["id"]: "aaaaaaaaaaaaaaaaaaaa"
        }
        generated_responses.append({
            "id": resp_id,
            "answers": answers,
            "duration_seconds": 68.0,
            "started_at": start_dt.isoformat(),
            "submitted_at": sub_dt.isoformat(),
            "client_metadata": {"device_type": "desktop"},
            "enumerator_id": "",
            "resp_type": "gibberish"
        })

        # 3.5. Thêm 1 phản hồi rủi ro cao kết hợp (High Risk Speeder + Duplication)
        resp_id = str(uuid.uuid4())
        sub_dt = created_dt + timedelta(minutes=170)
        start_dt = sub_dt - timedelta(seconds=1.8)
        answers = {
            q_gender["id"]: "nam",
            q_faculty["id"]: "cntt_kt",
            q_infra["id"]: 5,
            q_ai["id"]: 5,
            q_trust["id"]: 5,
            q_policy["id"]: 5,
            q_text["id"]: ""
        }
        generated_responses.append({
            "id": resp_id,
            "answers": answers,
            "duration_seconds": 1.8,
            "started_at": start_dt.isoformat(),
            "submitted_at": sub_dt.isoformat(),
            "client_metadata": {"device_type": "mobile"},
            "enumerator_id": "NV_HA_NOI_02",
            "resp_type": "high_risk"
        })

        # 4. Đưa từng phản hồi qua Quality Engine và ghi vào CSDL
        prior_responses: List[Dict[str, Any]] = []
        clean_count = 0
        flagged_count = 0

        for r_entry in generated_responses:
            r_id = r_entry["id"]
            answers = r_entry["answers"]
            dur = r_entry["duration_seconds"]
            enum_val = r_entry["enumerator_id"]
            meta = r_entry["client_metadata"]

            # Thực thi Quality Engine
            analysis = QualityEngine.analyze_response(
                new_answers=answers,
                duration_seconds=dur,
                questions=questions_spec,
                prior_responses=prior_responses,
                enumerator_id=enum_val,
                quality_settings=settings["quality_settings"]
            )

            risk_score = analysis["composite_score"]
            risk_level = analysis["risk_level"]
            review_status = "unverified"
            if r_entry["resp_type"] == "clean":
                clean_count += 1
            else:
                flagged_count += 1

            # 4.1. Lưu bản ghi response
            conn.execute("""
                INSERT INTO responses (
                    id, survey_id, survey_version, started_at, submitted_at,
                    duration_seconds, client_metadata_json, risk_score, risk_level,
                    analysis_status, review_status, source, enumerator_id
                ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, 'analyzed', ?, 'online_form', ?)
            """, (
                r_id, survey_id, r_entry["started_at"], r_entry["submitted_at"],
                dur, json.dumps(meta, ensure_ascii=False), risk_score, risk_level,
                review_status, enum_val
            ))

            # 4.2. Lưu từng câu trả lời
            for qid, val in answers.items():
                conn.execute("""
                    INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), r_id, qid,
                    json.dumps(val, ensure_ascii=False) if isinstance(val, (list, dict)) else str(val),
                    r_entry["submitted_at"]
                ))

            # 4.3. Lưu đánh giá chất lượng
            conn.execute("""
                INSERT INTO quality_assessments (
                    id, response_id, score_dup, score_pattern, score_logic, score_speed, score_text, score_enum,
                    composite_score, flags_json, closest_match_response_id, highest_similarity, assessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), r_id,
                analysis["score_dup"], analysis["score_pattern"], analysis["score_logic"],
                analysis["score_speed"], analysis["score_text"], analysis.get("score_enum", 0.0),
                risk_score, json.dumps(analysis["flags"], ensure_ascii=False),
                analysis.get("closest_match_response_id"), analysis.get("highest_similarity", 0.0),
                r_entry["submitted_at"]
            ))

            # 4.4. Thêm vào tập đối chiếu chéo
            prior_responses.append({
                "id": r_id,
                "answers": answers,
                "enumerator_id": enum_val,
                "risk_score": risk_score
            })

            # 4.5. Ghi vào chuỗi băm bất biến
            record_audit_log(
                conn,
                entity_type="response",
                entity_id=r_id,
                action="INGEST_RESPONSE",
                details={
                    "survey_id": survey_id,
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "resp_type": r_entry["resp_type"]
                },
                created_at=r_entry["submitted_at"]
            )

        # 5. Ghi audit log hoàn tất bộ dữ liệu thực nghiệm
        total_resp = len(generated_responses)
        data_trust_index = round((clean_count / total_resp) * 100.0, 1) if total_resp > 0 else 100.0

        # Tính Cronbach's alpha trên tập mẫu sạch
        items_matrix = [
            [float(p[2]), float(p[3]), float(p[4]), float(p[5])]
            for p in clean_profiles
        ]
        alpha = QualityEngine.compute_cronbach_alpha(items_matrix)

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SEED_ACADEMIC_STUDY",
            details={
                "total_responses": total_resp,
                "clean_responses": clean_count,
                "flagged_responses": flagged_count,
                "data_trust_index": data_trust_index,
                "cronbach_alpha": alpha
            },
            created_at=now_iso()
        )

        return {
            "survey_id": survey_id,
            "public_slug": public_slug,
            "title": title,
            "total_responses": total_resp,
            "clean_count": clean_count,
            "flagged_count": flagged_count,
            "data_trust_index": data_trust_index,
            "cronbach_alpha": round(alpha, 4) if alpha is not None else None,
            "message": f"Đã khởi tạo thành công Khảo sát & Bộ dữ liệu thực nghiệm mẫu ({total_resp} phản hồi, {clean_count} sạch, {flagged_count} gắn cờ cảnh báo)."
        }

    @classmethod
    def seed_responses_for_survey(cls, conn: sqlite3.Connection, survey_id: str, count: int = 15) -> Dict[str, Any]:
        """
        Nạp nhanh các phản hồi mẫu thực tế vào một khảo sát bất kỳ đã tồn tại
        """
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise ValueError("Không tìm thấy khảo sát.")

        q_rows = conn.execute("""
            SELECT * FROM questions WHERE survey_id = ? ORDER BY order_index ASC
        """, (survey_id,)).fetchall()

        if not q_rows:
            raise ValueError("Khảo sát chưa có câu hỏi nào để nạp phản hồi.")

        questions = [dict(q) for q in q_rows]
        for q in questions:
            q["options"] = json.loads(q.get("options_json") or "[]")
            q["logic_rules"] = json.loads(q.get("logic_rules_json") or "[]")

        s_settings = json.loads(s_row["settings_json"] or "{}")
        q_settings = s_settings.get("quality_settings", {})

        # Lấy prior_responses
        prior_rows = conn.execute("""
            SELECT id, enumerator_id, risk_score FROM responses WHERE survey_id = ?
        """, (survey_id,)).fetchall()
        prior_responses = []
        for pr in prior_rows:
            ans_rows = conn.execute("SELECT question_id, answer_value FROM response_answers WHERE response_id = ?", (pr["id"],)).fetchall()
            p_ans = {}
            for a in ans_rows:
                try:
                    p_ans[a["question_id"]] = json.loads(a["answer_value"])
                except Exception:
                    p_ans[a["question_id"]] = a["answer_value"]
            prior_responses.append({
                "id": pr["id"],
                "answers": p_ans,
                "enumerator_id": pr["enumerator_id"] if "enumerator_id" in pr.keys() else "",
                "risk_score": pr["risk_score"] if "risk_score" in pr.keys() else 0.0
            })

        now_dt = datetime.now(timezone.utc)
        seeded_count = 0
        speeders_count = max(1, count // 7)
        straightliners_count = max(1, count // 10)

        for i in range(count):
            r_id = str(uuid.uuid4())
            is_speeder = (i < speeders_count)
            is_straight = (not is_speeder and i < (speeders_count + straightliners_count))

            duration = random.uniform(1.5, 4.0) if is_speeder else random.uniform(65.0, 150.0)
            sub_dt = now_dt - timedelta(minutes=(count - i) * 3)
            start_dt = sub_dt - timedelta(seconds=duration)

            answers: Dict[str, Any] = {}
            for q in questions:
                q_id = q["id"]
                q_type = q.get("question_type")
                opts = q.get("options", [])

                if is_straight:
                    # Cố định giá trị
                    if q_type in ("rating", "linear_scale", "nps"):
                        answers[q_id] = 5
                    elif opts:
                        answers[q_id] = opts[0]["id"] if isinstance(opts[0], dict) else opts[0]
                    else:
                        answers[q_id] = "Đồng ý hoàn toàn"
                else:
                    if q_type == "single_choice" and opts:
                        sel = random.choice(opts)
                        answers[q_id] = sel["id"] if isinstance(sel, dict) else sel
                    elif q_type == "multiple_choice" and opts:
                        k = random.randint(1, min(2, len(opts)))
                        picked = random.sample(opts, k)
                        answers[q_id] = [p["id"] if isinstance(p, dict) else p for p in picked]
                    elif q_type in ("rating", "linear_scale"):
                        answers[q_id] = random.choice([3, 4, 4, 5, 5])
                    elif q_type == "nps":
                        answers[q_id] = random.choice([7, 8, 9, 10])
                    elif q_type == "number":
                        answers[q_id] = random.randint(18, 45)
                    elif q_type in ("long_text", "short_text"):
                        answers[q_id] = cls.CLEAN_COMMENTS[i % len(cls.CLEAN_COMMENTS)] if not is_speeder else "ok"
                    else:
                        answers[q_id] = "Phản hồi mẫu"

            analysis = QualityEngine.analyze_response(
                new_answers=answers,
                duration_seconds=duration,
                questions=questions,
                prior_responses=prior_responses,
                enumerator_id="",
                quality_settings=q_settings
            )

            risk_score = analysis["composite_score"]
            risk_level = analysis["risk_level"]

            # Lưu response
            conn.execute("""
                INSERT INTO responses (
                    id, survey_id, survey_version, started_at, submitted_at,
                    duration_seconds, client_metadata_json, risk_score, risk_level,
                    analysis_status, review_status, source, enumerator_id
                ) VALUES (?, ?, ?, ?, ?, ?, '{}', ?, ?, 'analyzed', 'unverified', 'demo_seeder', '')
            """, (
                r_id, survey_id, s_row["version"], start_dt.isoformat(), sub_dt.isoformat(),
                duration, risk_score, risk_level
            ))

            for qid, val in answers.items():
                conn.execute("""
                    INSERT INTO response_answers (id, response_id, question_id, answer_value, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), r_id, qid,
                    json.dumps(val, ensure_ascii=False) if isinstance(val, (list, dict)) else str(val),
                    sub_dt.isoformat()
                ))

            conn.execute("""
                INSERT INTO quality_assessments (
                    id, response_id, score_dup, score_pattern, score_logic, score_speed, score_text, score_enum,
                    composite_score, flags_json, closest_match_response_id, highest_similarity, assessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), r_id,
                analysis["score_dup"], analysis["score_pattern"], analysis["score_logic"],
                analysis["score_speed"], analysis["score_text"], analysis.get("score_enum", 0.0),
                risk_score, json.dumps(analysis["flags"], ensure_ascii=False),
                analysis.get("closest_match_response_id"), analysis.get("highest_similarity", 0.0),
                sub_dt.isoformat()
            ))

            prior_responses.append({
                "id": r_id,
                "answers": answers,
                "enumerator_id": "",
                "risk_score": risk_score
            })

            record_audit_log(
                conn,
                entity_type="response",
                entity_id=r_id,
                action="INGEST_RESPONSE",
                details={"survey_id": survey_id, "risk_score": risk_score, "source": "demo_seeder"},
                created_at=sub_dt.isoformat()
            )
            seeded_count += 1

        record_audit_log(
            conn,
            entity_type="survey",
            entity_id=survey_id,
            action="SEED_DEMO_RESPONSES",
            details={"seeded_count": seeded_count},
            created_at=now_iso()
        )

        return {
            "survey_id": survey_id,
            "seeded_count": seeded_count,
            "message": f"Đã nạp thành công {seeded_count} phản hồi mẫu vào khảo sát."
        }
