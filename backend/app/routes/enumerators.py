import csv
import io
import json
import math
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from fastapi import APIRouter, HTTPException, Response
from app.database import get_db
from app.schemas import EnumeratorAnalyticsOut, EnumeratorMetrics
from app.engine.quality_engine import QualityEngine

router = APIRouter(prefix="/api/surveys/{survey_id}/enumerators", tags=["Enumerator Analytics"])

def parse_iso_dt(dt_str: str) -> datetime:
    try:
        clean = (dt_str or "").replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except Exception:
        return datetime.now(timezone.utc)

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Tính khoảng cách đường chim bay giữa hai tọa độ GPS theo công thức Haversine (km)"""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(max(0.0, a)), math.sqrt(max(0.0, 1.0 - a)))
    return r * c

def extract_gps_point(meta_raw: Any) -> Optional[Tuple[float, float]]:
    """Trích xuất (latitude, longitude) từ client_metadata nếu có"""
    if not meta_raw:
        return None
    try:
        data = json.loads(meta_raw) if isinstance(meta_raw, str) else meta_raw
        if not isinstance(data, dict):
            return None
        
        lat = None
        lon = None
        if "latitude" in data and "longitude" in data:
            lat = data["latitude"]
            lon = data["longitude"]
        elif "lat" in data and "lng" in data:
            lat = data["lat"]
            lon = data["lng"]
        elif "lat" in data and "lon" in data:
            lat = data["lat"]
            lon = data["lon"]
        elif "location" in data and isinstance(data["location"], dict):
            loc = data["location"]
            lat = loc.get("latitude") or loc.get("lat")
            lon = loc.get("longitude") or loc.get("lng") or loc.get("lon")
        elif "gps" in data and isinstance(data["gps"], dict):
            loc = data["gps"]
            lat = loc.get("latitude") or loc.get("lat")
            lon = loc.get("longitude") or loc.get("lng") or loc.get("lon")

        if lat is not None and lon is not None:
            f_lat = float(lat)
            f_lon = float(lon)
            if -90.0 <= f_lat <= 90.0 and -180.0 <= f_lon <= 180.0:
                return (f_lat, f_lon)
    except Exception:
        pass
    return None

@router.get("", response_model=EnumeratorAnalyticsOut)
def get_enumerator_analytics(survey_id: str):
    """
    Phân tích thống kê và phát hiện bất thường theo từng điều tra viên (Interviewer / Field Group Falsification).
    Đo độ lệch chuẩn Z-score về phương sai câu trả lời, tỷ lệ cảnh báo rủi ro cao,
    và kiểm định tốc độ di chuyển / tọa độ địa lý GPS thực địa (Geofencing & Teleportation Detection).
    """
    with get_db() as conn:
        s_row = conn.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")

        resp_rows = conn.execute("""
            SELECT id, duration_seconds, risk_score, risk_level, source, enumerator_id, client_metadata_json, submitted_at
            FROM responses
            WHERE survey_id = ?
        """, (survey_id,)).fetchall()

        s_settings = json.loads(s_row["settings_json"] or "{}") if "settings_json" in s_row.keys() else {}
        geofence_cfg = s_settings.get("quality_settings", {}).get("geofence")

        if not resp_rows:
            return EnumeratorAnalyticsOut(
                survey_id=survey_id,
                total_enumerators=0,
                total_field_responses=0,
                geofence_setting=geofence_cfg,
                enumerators=[]
            )

        # Lấy danh sách câu hỏi đóng để đo phương sai câu trả lời
        q_rows = conn.execute("""
            SELECT id, question_type, options_json FROM questions
            WHERE survey_id = ? AND question_type NOT IN ('short_text', 'long_text')
        """, (survey_id,)).fetchall()
        eval_q_ids = [q["id"] for q in q_rows]

        # Nhóm responses theo enumerator_id
        grouped: Dict[str, List[Any]] = {}
        for r in resp_rows:
            enum_id = (r["enumerator_id"] or "").strip()
            if not enum_id:
                try:
                    meta = json.loads(r["client_metadata_json"] or "{}")
                    enum_id = meta.get("enumerator_id", "").strip()
                except Exception:
                    pass
            if not enum_id:
                enum_id = "Chưa gán mã ĐTV (Online/Khách vãng lai)"
            
            grouped.setdefault(enum_id, []).append(r)

        # Tối ưu hóa: Tải trước toàn bộ response_answers của khảo sát để tránh N+1 queries theo từng ĐTV
        all_enum_ans = conn.execute("""
            SELECT ra.response_id, ra.question_id, ra.answer_value
            FROM response_answers ra
            JOIN responses r ON r.id = ra.response_id
            WHERE r.survey_id = ?
        """, (survey_id,)).fetchall()
        
        ans_by_resp_id: Dict[str, List[Any]] = {}
        for a in all_enum_ans:
            ans_by_resp_id.setdefault(a["response_id"], []).append(a)

        # Tính phương sai câu trả lời cho từng điều tra viên hoàn toàn trong bộ nhớ
        enum_variances: Dict[str, float] = {}
        for enum_id, r_list in grouped.items():
            r_ids = [r["id"] for r in r_list]
            if len(r_ids) < 2 or not eval_q_ids:
                enum_variances[enum_id] = 1.0
                continue

            numeric_vals = []
            for rid in r_ids:
                for a in ans_by_resp_id.get(rid, []):
                    if a["question_id"] in eval_q_ids:
                        val_str = str(a["answer_value"]).strip().lower()
                        try:
                            numeric_vals.append(float(val_str))
                        except Exception:
                            numeric_vals.append(float(sum(ord(c) for c in val_str) % 10))

            if len(numeric_vals) >= 4:
                mean_val = sum(numeric_vals) / len(numeric_vals)
                var_val = sum((x - mean_val) ** 2 for x in numeric_vals) / (len(numeric_vals) - 1)
                enum_variances[enum_id] = var_val
            else:
                enum_variances[enum_id] = 1.0

        all_vars = list(enum_variances.values())
        mean_global_var = sum(all_vars) / max(1, len(all_vars))
        std_global_var = math.sqrt(sum((v - mean_global_var) ** 2 for v in all_vars) / max(1, len(all_vars)))
        std_global_var = max(0.1, std_global_var)

        metrics_list: List[EnumeratorMetrics] = []
        for enum_id, r_list in grouped.items():
            total = len(r_list)
            online_c = sum(1 for r in r_list if r["source"] == "online_form")
            paper_c = sum(1 for r in r_list if r["source"] == "paper_scan")

            durations = [r["duration_seconds"] for r in r_list if r["duration_seconds"] > 0]
            avg_dur = sum(durations) / len(durations) if durations else 0.0

            risks = [r["risk_score"] for r in r_list]
            avg_risk = sum(risks) / len(risks) if risks else 0.0

            high_risk_c = sum(1 for r in r_list if r["risk_level"] == "high" or r["risk_score"] >= 70.0)
            high_risk_rate = high_risk_c / total if total > 0 else 0.0

            this_var = enum_variances.get(enum_id, 1.0)
            z_score = (this_var - mean_global_var) / std_global_var

            reasons = []
            is_anomaly = False

            # 1. Z-score phương sai thấp (Z < -1.75) khi có từ 4 phiếu trở lên
            if total >= 4 and z_score < -1.75:
                is_anomaly = True
                reasons.append(f"Phương sai câu trả lời thấp bất thường (Z = {z_score:.2f}), dấu hiệu trả lời rập khuôn.")

            # 2. Tỷ lệ rủi ro cao >= 40% trên tổng số phiếu
            if total >= 3 and high_risk_rate >= 0.40:
                is_anomaly = True
                reasons.append(f"Tỷ lệ phiếu bị gắn cờ rủi ro cao vượt mức ({round(high_risk_rate * 100)}%).")

            # 3. Thời gian nộp bài trung bình quá nhanh (< 15s/phiếu)
            if total >= 3 and avg_dur > 0 and avg_dur < 15.0:
                is_anomaly = True
                reasons.append(f"Tốc độ nộp bài trung bình siêu tốc ({round(avg_dur, 1)}s/phiếu).")

            # 4. Phân tích Geofencing & Tọa độ GPS thực địa
            gps_entries: List[Tuple[datetime, Tuple[float, float], str, float]] = []
            for r in r_list:
                pt = extract_gps_point(r["client_metadata_json"])
                if pt is not None:
                    dt = parse_iso_dt(r["submitted_at"])
                    gps_entries.append((dt, pt, r["id"], r["risk_score"] or 0.0))

            gps_coverage = round(len(gps_entries) / total, 3) if total > 0 else 0.0
            impossible_speed = False
            max_speed_kmh: Optional[float] = None
            stationary_cluster = False
            point_dicts: List[Dict[str, Any]] = []

            if len(gps_entries) >= 2:
                # Sắp xếp theo thứ tự thời gian nộp
                gps_entries.sort(key=lambda item: item[0])
                calculated_speeds = []
                for i in range(len(gps_entries)):
                    t1, (lat1, lon1), rid, rscore = gps_entries[i]
                    is_speed_flag = False
                    speed_to_next = None

                    if i < len(gps_entries) - 1:
                        t2, (lat2, lon2), _, _ = gps_entries[i + 1]
                        dt_sec = max(1.0, (t2 - t1).total_seconds())
                        dist_km = haversine_distance_km(lat1, lon1, lat2, lon2)
                        speed = dist_km / (dt_sec / 3600.0)
                        calculated_speeds.append(speed)
                        speed_to_next = round(speed, 1)

                        # Tốc độ phi lý: > 120 km/h trên khoảng cách > 0.3 km
                        if speed > 120.0 and dist_km > 0.3:
                            impossible_speed = True
                            is_speed_flag = True
                            is_anomaly = True
                            reasons.append(
                                f"Tốc độ di chuyển thực địa phi lý ({round(speed, 1)} km/h giữa 2 điểm cách nhau {round(dist_km, 2)} km) - dấu hiệu làm giả tọa độ (GPS spoofing/teleportation)."
                            )

                    point_dicts.append({
                        "response_id": rid,
                        "lat": round(lat1, 6),
                        "lon": round(lon1, 6),
                        "submitted_at": t1.isoformat(),
                        "risk_score": rscore,
                        "speed_to_next_kmh": speed_to_next,
                        "is_speed_anomaly": is_speed_flag
                    })

                if calculated_speeds:
                    max_speed_kmh = round(max(calculated_speeds), 1)
            elif len(gps_entries) == 1:
                t1, (lat1, lon1), rid, rscore = gps_entries[0]
                point_dicts.append({
                    "response_id": rid,
                    "lat": round(lat1, 6),
                    "lon": round(lon1, 6),
                    "submitted_at": t1.isoformat(),
                    "risk_score": rscore,
                    "speed_to_next_kmh": None,
                    "is_speed_anomaly": False
                })

            # Tính toán bán kính chuyển động Radius of Gyration (R_g) và diện tích bao phủ không gian
            rg_km: Optional[float] = None
            cov_sqkm: Optional[float] = None

            if len(gps_entries) >= 2:
                lats = [pt[0] for _, pt, _, _ in gps_entries]
                lons = [pt[1] for _, pt, _, _ in gps_entries]
                mean_lat = sum(lats) / len(lats)
                mean_lon = sum(lons) / len(lons)

                sq_dists = [haversine_distance_km(mean_lat, mean_lon, lat, lon) ** 2 for lat, lon in zip(lats, lons)]
                rg_km = round(math.sqrt(sum(sq_dists) / len(sq_dists)), 3)

                min_lat, max_lat = min(lats), max(lats)
                min_lon, max_lon = min(lons), max(lons)
                d_lat_km = (max_lat - min_lat) * 111.0
                d_lon_km = (max_lon - min_lon) * 111.0 * math.cos(math.radians(mean_lat))
                cov_sqkm = round(max(0.0001, d_lat_km * d_lon_km), 4)

                # Cảnh báo nếu có từ 4 phiếu trở lên nhưng bán kính chuyển động cực tiểu (< 20m)
                if len(gps_entries) >= 4 and rg_km < 0.020:
                    stationary_cluster = True
                    is_anomaly = True
                    reasons.append(
                        f"Cụm tọa độ tĩnh bất thường: Bán kính di chuyển thực địa (Radius of Gyration = {rg_km * 1000:.0f}m) qua {len(gps_entries)} phiếu là cực tiểu - nghi vấn điều tra viên ngồi một chỗ tự điền."
                    )

            # Kiểm tra cụm tọa độ tĩnh (Stationary Cluster)
            if len(gps_entries) >= 4 and not stationary_cluster:
                first_lat, first_lon = gps_entries[0][1]
                max_spread_km = max(
                    haversine_distance_km(first_lat, first_lon, lat, lon)
                    for _, (lat, lon), _, _ in gps_entries
                )
                if max_spread_km < 0.005:  # Tất cả phiếu trong phạm vi dưới 5 mét
                    stationary_cluster = True
                    is_anomaly = True
                    reasons.append(
                        f"Tất cả {len(gps_entries)} phiếu thực địa đều xuất phát từ cùng một tọa độ tĩnh (bán kính < 5m) - nghi vấn điều tra viên ngồi một chỗ tự điền phiếu."
                    )

            # Kiểm tra tuân thủ ranh giới địa lý (Geofencing Compliance)
            enum_geofence_breaches = 0
            if geofence_cfg and isinstance(geofence_cfg, dict) and geofence_cfg.get("enabled"):
                target_lat = geofence_cfg.get("target_lat")
                target_lon = geofence_cfg.get("target_lon")
                max_rad = float(geofence_cfg.get("max_radius_km", 5.0))
                loc_name = geofence_cfg.get("location_name") or "vùng khảo sát"

                for pt in point_dicts:
                    if target_lat is not None and target_lon is not None:
                        dist_center = QualityEngine.haversine_distance_km(target_lat, target_lon, pt["lat"], pt["lon"])
                        pt["distance_from_center_km"] = round(dist_center, 2)
                        if dist_center > max_rad:
                            pt["is_geofence_breach"] = True
                            enum_geofence_breaches += 1
                        else:
                            pt["is_geofence_breach"] = False

                if enum_geofence_breaches > 0:
                    is_anomaly = True
                    reasons.append(
                        f"Vi phạm ranh giới địa lý ({enum_geofence_breaches} điểm phỏng vấn nằm ngoài bán kính {max_rad}km quanh {loc_name})."
                    )

            metrics_list.append(EnumeratorMetrics(
                enumerator_id=enum_id,
                total_responses=total,
                online_count=online_c,
                paper_count=paper_c,
                avg_duration_seconds=round(avg_dur, 1),
                avg_risk_score=round(avg_risk, 1),
                high_risk_count=high_risk_c,
                high_risk_rate=round(high_risk_rate, 3),
                variance_z_score=round(z_score, 2),
                is_anomaly=is_anomaly,
                anomaly_reasons=reasons,
                gps_coverage_rate=gps_coverage,
                impossible_speed_detected=impossible_speed,
                max_speed_kmh=max_speed_kmh,
                stationary_cluster_detected=stationary_cluster,
                radius_of_gyration_km=rg_km,
                spatial_coverage_sqkm=cov_sqkm,
                geofence_breach_count=enum_geofence_breaches,
                gps_points=point_dicts
            ))

        # Sắp xếp theo trạng thái bất thường và điểm rủi ro
        metrics_list.sort(key=lambda m: (m.is_anomaly, m.avg_risk_score), reverse=True)

        return EnumeratorAnalyticsOut(
            survey_id=survey_id,
            total_enumerators=len(metrics_list),
            total_field_responses=len(resp_rows),
            geofence_setting=geofence_cfg,
            enumerators=metrics_list
        )

@router.get("/export")
def export_enumerator_audit_csv(survey_id: str):
    """
    Xuất danh sách giám sát và phân tích bất thường theo từng điều tra viên (CSV định dạng UTF-8 BOM cho Excel).
    Phục vụ công tác hậu kiểm thực địa (Field Back-checks) và biên bản nghiệm thu dữ liệu.
    Bao gồm kiểm định độ phủ GPS, tốc độ di chuyển và cảnh báo gian lận thực địa.
    """
    analytics = get_enumerator_analytics(survey_id)
    with get_db() as conn:
        s_row = conn.execute("SELECT title, public_slug FROM surveys WHERE id = ?", (survey_id,)).fetchone()
        slug = s_row["public_slug"] if s_row else survey_id

    output = io.StringIO()
    fieldnames = [
        "Mã Điều tra viên",
        "Tổng số phiếu",
        "Phiếu giấy (OMR)",
        "Phiếu trực tuyến",
        "Thời gian TB (giây)",
        "Điểm rủi ro TB",
        "Số phiếu rủi ro cao",
        "Tỷ lệ rủi ro cao (%)",
        "Z-score Phương sai",
        "Độ phủ GPS (%)",
        "Bán kính di chuyển Rg (m)",
        "Diện tích bao phủ (km²)",
        "Số điểm vi phạm ranh giới",
        "Cảnh báo Vi phạm vùng",
        "Tốc độ tối đa (km/h)",
        "Cảnh báo Tốc độ phi lý",
        "Cảnh báo Tọa độ tĩnh",
        "Trạng thái Bất thường",
        "Lý do cảnh báo"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for m in analytics.enumerators:
        writer.writerow({
            "Mã Điều tra viên": m.enumerator_id,
            "Tổng số phiếu": m.total_responses,
            "Phiếu giấy (OMR)": m.paper_count,
            "Phiếu trực tuyến": m.online_count,
            "Thời gian TB (giây)": m.avg_duration_seconds,
            "Điểm rủi ro TB": m.avg_risk_score,
            "Số phiếu rủi ro cao": m.high_risk_count,
            "Tỷ lệ rủi ro cao (%)": f"{round(m.high_risk_rate * 100, 1)}%",
            "Z-score Phương sai": m.variance_z_score,
            "Độ phủ GPS (%)": f"{round(m.gps_coverage_rate * 100, 1)}%",
            "Bán kính di chuyển Rg (m)": f"{round(m.radius_of_gyration_km * 1000, 1)}" if m.radius_of_gyration_km is not None else "—",
            "Diện tích bao phủ (km²)": f"{m.spatial_coverage_sqkm:.4f}" if m.spatial_coverage_sqkm is not None else "—",
            "Số điểm vi phạm ranh giới": m.geofence_breach_count,
            "Cảnh báo Vi phạm vùng": "CÓ (BẤT THƯỜNG)" if m.geofence_breach_count > 0 else "Không",
            "Tốc độ tối đa (km/h)": f"{m.max_speed_kmh:.1f}" if m.max_speed_kmh is not None else "—",
            "Cảnh báo Tốc độ phi lý": "CÓ (BẤT THƯỜNG)" if m.impossible_speed_detected else "Không",
            "Cảnh báo Tọa độ tĩnh": "CÓ (BẤT THƯỜNG)" if m.stationary_cluster_detected else "Không",
            "Trạng thái Bất thường": "CẢNH BÁO" if m.is_anomaly else "BÌNH THƯỜNG",
            "Lý do cảnh báo": "; ".join(m.anomaly_reasons) if m.anomaly_reasons else "Đạt chuẩn"
        })

    csv_bytes = "\ufeff" + output.getvalue()
    safe_slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", slug)
    return Response(
        content=csv_bytes.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="datatrust_enumerator_audit_{safe_slug}.csv"'}
    )
