import math
from typing import Dict, Any, List, Optional, Tuple


class ConjointAnalysisEngine:
    """
    Choice-Based Conjoint Analysis & Discrete Choice Modeling (CBC / DCE) Engine:
    - McFadden (1974) Random Utility Theory (Nobel Prize 2000)
    - Luce (1959) Choice Axiom & Multinomial Logit
    - Green & Srinivasan (1990) Conjoint Analysis in Consumer & Policy Research
    - Hensher, Rose & Greene (2005) Applied Choice Analysis & Willingness to Pay (WTP)

    Tính năng cốt lõi:
    1. Ước lượng Tiện ích Từng phần (Part-Worth Utilities) theo chuẩn Effects Coding (Zero-Sum)
    2. Độ Quan trọng Tương đối của các Thuộc tính (Attribute Relative Importance %)
    3. Mô phỏng Thị phần Lựa chọn (Choice Share Market Simulator) theo quy tắc Logit
    4. Sẵn sàng Chi trả (Willingness to Pay - WTP) dựa trên hệ số giá
    5. Đồ họa Vector SVG trực quan hóa tỷ trọng thuộc tính và hồ sơ tiện ích
    6. Tự động sinh đoạn thuyết minh học thuật chuẩn APA 7th Edition
    """

    @staticmethod
    def compute_conjoint_analysis(
        profiles_data: List[Dict[str, Any]],
        attributes_config: Dict[str, List[str]],
        rating_key: str = "rating",
        price_attribute_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        profiles_data: Danh sách các đánh giá hồ sơ sản phẩm/chính sách.
          Mỗi phần tử chứa:
            - Các thuộc tính và mức độ tương ứng: e.g. {"Thương hiệu": "Brand A", "Giá": "100k", ...}
            - Điểm đánh giá mức độ ưa thích / xác suất chọn: e.g. {"rating": 4.5}
        attributes_config: Dict ánh xạ tên thuộc tính -> danh sách các mức độ (levels)
          e.g. {"Thương hiệu": ["Brand A", "Brand B"], "Giá": ["100k", "200k", "300k"]}
        rating_key: Tên trường chứa điểm đánh giá (1-5, 1-10, hoặc 0-1 choice)
        price_attribute_name: Tên thuộc tính giá (nếu có) để tính WTP
        """
        n_obs = len(profiles_data)
        if n_obs < 6:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "message": f"Cần tối thiểu 6 quan sát/hồ sơ đánh giá để thực hiện phân tích Conjoint (hiện có {n_obs})."
            }

        if len(attributes_config) < 2:
            return {
                "status": "INSUFFICIENT_ATTRIBUTES",
                "message": f"Cần tối thiểu 2 thuộc tính để phân tích đánh đổi Conjoint (hiện có {len(attributes_config)})."
            }

        # 1. Trích xuất danh sách biến và mức độ
        # Xây dựng danh sách dummy coding (với mức cuối cùng là reference level theo effects coding: sum = 0)
        attr_levels: Dict[str, List[str]] = {}
        for attr, levels in attributes_config.items():
            if len(levels) < 2:
                continue
            attr_levels[attr] = list(levels)

        if len(attr_levels) < 2:
            return {
                "status": "INVALID_LEVELS",
                "message": "Mỗi thuộc tính cần tối thiểu 2 mức độ (levels) để ước lượng tiện ích."
            }

        # 2. Xây dựng ma trận thiết kế X và vector Y
        y_vals: List[float] = []
        x_rows: List[List[float]] = []
        feature_names: List[Tuple[str, str]] = []  # (attr, level)

        for attr, levels in attr_levels.items():
            # Mức cuối cùng là reference level
            for lvl in levels[:-1]:
                feature_names.append((attr, lvl))

        k_features = len(feature_names)
        if k_features == 0:
            return {
                "status": "ERROR",
                "message": "Không có đủ tham số tự do để ước lượng mô hình."
            }

        for row in profiles_data:
            try:
                y = float(row.get(rating_key, 0.0))
            except (ValueError, TypeError):
                continue

            y_vals.append(y)
            # Effects coding: +1 nếu bằng level, -1 nếu bằng reference level, 0 nếu khác
            x_vec = [1.0]  # Intercept
            for attr, lvl in feature_names:
                ref_lvl = attr_levels[attr][-1]
                row_val = str(row.get(attr, "")).strip()
                if row_val == lvl:
                    x_vec.append(1.0)
                elif row_val == ref_lvl:
                    x_vec.append(-1.0)
                else:
                    x_vec.append(0.0)
            x_rows.append(x_vec)

        n_valid = len(y_vals)
        if n_valid < k_features + 2:
            return {
                "status": "INSUFFICIENT_DATA_DEGREES_OF_FREEDOM",
                "message": f"Cần tối thiểu {k_features + 2} hồ sơ hợp lệ để ước lượng {k_features} tham số (hiện có {n_valid})."
            }

        # 3. Ước lượng OLS có điều chuẩn Ridge nhỏ để tránh singular matrix
        p_cols = k_features + 1
        xtx = [[0.0] * p_cols for _ in range(p_cols)]
        xty = [0.0] * p_cols

        for i in range(n_valid):
            x_i = x_rows[i]
            y_i = y_vals[i]
            for r in range(p_cols):
                xty[r] += x_i[r] * y_i
                for c in range(p_cols):
                    xtx[r][c] += x_i[r] * x_i[c]

        # Ridge penalty (L2 lambda = 1e-4) để ổn định số
        for r in range(1, p_cols):
            xtx[r][r] += 1e-4

        # Giải hệ phương trình X^T X beta = X^T y bằng khử Gauss-Jordan
        beta = ConjointAnalysisEngine._solve_linear_system(xtx, xty)
        if not beta:
            return {
                "status": "NUMERICAL_INSTABILITY",
                "message": "Không thể hội tụ ma trận đặc trưng trong ước lượng tiện ích Conjoint."
            }

        intercept = beta[0]
        coefs = beta[1:]

        # 4. Tính toán Part-Worth Utilities cho từng thuộc tính và từng mức độ
        # Với effects coding, tổng các tiện ích của 1 thuộc tính = 0
        part_worths: Dict[str, Dict[str, float]] = {}
        idx_feature = 0

        for attr, levels in attr_levels.items():
            part_worths[attr] = {}
            sum_non_ref = 0.0
            for lvl in levels[:-1]:
                pw = coefs[idx_feature]
                part_worths[attr][lvl] = round(pw, 4)
                sum_non_ref += pw
                idx_feature += 1
            # Mức tham chiếu = - tổng các mức khác
            ref_lvl = levels[-1]
            part_worths[attr][ref_lvl] = round(-sum_non_ref, 4)

        # 5. Đánh giá Độ Quan Trọng Tương Đối (Attribute Relative Importance %)
        # Range = max(part_worth) - min(part_worth)
        # Importance = Range_i / sum(Ranges) * 100%
        attribute_ranges: Dict[str, float] = {}
        for attr, pw_dict in part_worths.items():
            vals = list(pw_dict.values())
            rng = max(vals) - min(vals)
            attribute_ranges[attr] = max(rng, 1e-6)

        total_range = sum(attribute_ranges.values())
        relative_importance: Dict[str, float] = {}
        importance_ranking: List[Dict[str, Any]] = []

        for attr, rng in attribute_ranges.items():
            imp_pct = (rng / total_range) * 100.0
            relative_importance[attr] = round(imp_pct, 2)
            importance_ranking.append({
                "attribute": attr,
                "importance_pct": round(imp_pct, 2),
                "range": round(rng, 4),
                "levels_count": len(attr_levels[attr]),
                "best_level": max(part_worths[attr].items(), key=lambda x: x[1])[0],
                "worst_level": min(part_worths[attr].items(), key=lambda x: x[1])[0]
            })

        importance_ranking.sort(key=lambda x: x["importance_pct"], reverse=True)

        # 6. Đánh giá chất lượng mô hình (R^2, Adjusted R^2, RMSE, McFadden Pseudo-R^2)
        y_mean = sum(y_vals) / n_valid
        ss_tot = sum((y - y_mean) ** 2 for y in y_vals)
        residuals = []
        for i in range(n_valid):
            y_pred = sum(x_rows[i][j] * beta[j] for j in range(p_cols))
            residuals.append(y_vals[i] - y_pred)

        ss_res = sum(e ** 2 for e in residuals)
        r2 = max(0.0, 1.0 - (ss_res / ss_tot)) if ss_tot > 1e-9 else 0.0
        df_res = max(1, n_valid - p_cols)
        adj_r2 = max(0.0, 1.0 - ((ss_res / df_res) / (ss_tot / (n_valid - 1)))) if ss_tot > 1e-9 else 0.0
        rmse = math.sqrt(ss_res / n_valid)

        # McFadden Pseudo-R^2
        # Giả định phân phối chuẩn phần dư: -2LL = n * (ln(2*pi) + ln(ss_res/n) + 1)
        ll_null = -0.5 * n_valid * (math.log(2 * math.pi) + math.log(max(ss_tot / n_valid, 1e-9)) + 1)
        ll_full = -0.5 * n_valid * (math.log(2 * math.pi) + math.log(max(ss_res / n_valid, 1e-9)) + 1)
        mcfadden_r2 = max(0.0, 1.0 - (ll_full / ll_null)) if abs(ll_null) > 1e-9 else 0.0

        # 7. Tính Sẵn sàng Chi trả (Willingness to Pay - WTP) nếu có biến giá
        wtp_results: Optional[List[Dict[str, Any]]] = None
        if price_attribute_name and price_attribute_name in part_worths:
            wtp_results = ConjointAnalysisEngine._compute_wtp(
                part_worths, price_attribute_name, attr_levels[price_attribute_name]
            )

        # 8. Sinh đồ họa Vector SVG:
        # Biểu đồ thanh ngang Độ quan trọng tương đối (Importance Bar Chart)
        # và Biểu đồ Tiện ích từng phần (Part-Worth Utilities Chart)
        svg_importance_chart = ConjointAnalysisEngine._generate_importance_svg(importance_ranking)

        # 9. Biên soạn Thuyết minh Học thuật Chuẩn APA 7th Edition
        apa_narrative = ConjointAnalysisEngine._generate_apa_narrative(
            n_valid=n_valid,
            num_attrs=len(attr_levels),
            r2=r2,
            adj_r2=adj_r2,
            importance_ranking=importance_ranking,
            part_worths=part_worths,
            price_attr=price_attribute_name,
            wtp_results=wtp_results
        )

        return {
            "status": "SUCCESS",
            "sample_size": n_valid,
            "attributes_count": len(attr_levels),
            "parameters_estimated": p_cols,
            "overall_utility_intercept": round(intercept, 4),
            "model_fit": {
                "r_squared": round(r2, 4),
                "adjusted_r_squared": round(adj_r2, 4),
                "mcfadden_pseudo_r2": round(mcfadden_r2, 4),
                "rmse": round(rmse, 4),
                "fit_quality": "Rất tốt (Excellent)" if r2 >= 0.70 else "Tốt (Good)" if r2 >= 0.50 else "Chấp nhận được (Acceptable)"
            },
            "importance_ranking": importance_ranking,
            "part_worth_utilities": part_worths,
            "willingness_to_pay": wtp_results,
            "svg_importance_chart": svg_importance_chart,
            "apa_narrative": apa_narrative
        }

    @staticmethod
    def simulate_choice_shares(
        part_worth_utilities: Dict[str, Dict[str, float]],
        intercept: float,
        candidate_profiles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Mô phỏng thị phần lựa chọn (Choice Share Market Simulator) theo mô hình Logit:
        P(i) = exp(U_i) / sum(exp(U_j))
        candidate_profiles: Danh sách hồ sơ các phương án đối đầu.
        Mỗi hồ sơ gồm: {"id": "Phương án 1", "attributes": {"Thương hiệu": "Brand A", ...}}
        """
        if not candidate_profiles:
            return []

        utilities: List[float] = []
        for prof in candidate_profiles:
            u = intercept
            attrs = prof.get("attributes", {})
            for attr, lvl in attrs.items():
                if attr in part_worth_utilities and lvl in part_worth_utilities[attr]:
                    u += part_worth_utilities[attr][lvl]
            utilities.append(u)

        # Tính xác suất Logit (softmax với scale để chống tràn số)
        max_u = max(utilities) if utilities else 0.0
        exp_u = [math.exp(u - max_u) for u in utilities]
        sum_exp = sum(exp_u) if sum(exp_u) > 1e-9 else 1.0

        shares: List[Dict[str, Any]] = []
        for i, prof in enumerate(candidate_profiles):
            prob = exp_u[i] / sum_exp
            shares.append({
                "profile_id": prof.get("id", f"Profile_{i+1}"),
                "total_utility": round(utilities[i], 4),
                "choice_share_pct": round(prob * 100.0, 2)
            })

        return shares

    @staticmethod
    def _compute_wtp(
        part_worths: Dict[str, Dict[str, float]],
        price_attr: str,
        price_levels: List[str]
    ) -> List[Dict[str, Any]]:
        """Tính Willingness to Pay (WTP) tương đối theo hệ số tiện ích giá."""
        # Cố gắng trích xuất giá trị số từ các mức giá
        numeric_prices: List[Tuple[str, float]] = []
        for lvl in price_levels:
            # Lọc các ký tự số
            cleaned = "".join(ch for ch in lvl if ch.isdigit() or ch == ".")
            try:
                numeric_prices.append((lvl, float(cleaned)))
            except (ValueError, TypeError):
                continue

        wtp_list: List[Dict[str, Any]] = []
        if len(numeric_prices) < 2:
            return wtp_list

        # Sắp xếp theo giá trị số tăng dần
        numeric_prices.sort(key=lambda x: x[1])
        min_lvl, min_p = numeric_prices[0]
        max_lvl, max_p = numeric_prices[-1]

        u_min = part_worths[price_attr].get(min_lvl, 0.0)
        u_max = part_worths[price_attr].get(max_lvl, 0.0)

        price_diff = max_p - min_p
        u_diff = u_max - u_min
        if abs(price_diff) < 1e-9 or abs(u_diff) < 1e-9:
            return wtp_list

        # Hệ số tiện ích trên mỗi đơn vị giá (marginal utility of price)
        # Thường âm vì giá cao tiện ích giảm
        beta_price = u_diff / price_diff

        for attr, pw_dict in part_worths.items():
            if attr == price_attr:
                continue
            for lvl, pw in pw_dict.items():
                wtp_val = - (pw / beta_price) if abs(beta_price) > 1e-9 else 0.0
                wtp_list.append({
                    "attribute": attr,
                    "level": lvl,
                    "part_worth": pw,
                    "wtp_valuation": round(wtp_val, 2)
                })

        return wtp_list

    @staticmethod
    def _generate_importance_svg(importance_ranking: List[Dict[str, Any]]) -> str:
        """Tạo biểu đồ thanh ngang SVG trực quan hóa tỷ trọng độ quan trọng tương đối."""
        width = 600
        bar_height = 24
        gap = 14
        top_offset = 30
        left_label_w = 160
        chart_w = 360

        total_height = top_offset + len(importance_ranking) * (bar_height + gap) + 40
        colors = ["#4f46e5", "#0ea5e9", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#64748b"]

        svg_parts = [
            f'<svg viewBox="0 0 {width} {total_height}" width="100%" height="{total_height}" xmlns="http://www.w3.org/2000/svg">'
        ]

        # Background grid lines
        for pct in [0, 25, 50, 75, 100]:
            x = left_label_w + (pct / 100.0) * chart_w
            svg_parts.append(
                f'<line x1="{x}" y1="{top_offset - 10}" x2="{x}" y2="{total_height - 25}" stroke="#e2e8f0" stroke-dasharray="3 3"/>'
            )
            svg_parts.append(
                f'<text x="{x}" y="{total_height - 10}" font-size="10" fill="#94a3b8" text-anchor="middle">{pct}%</text>'
            )

        # Horizontal bars
        for idx, item in enumerate(importance_ranking):
            y = top_offset + idx * (bar_height + gap)
            pct = item["importance_pct"]
            bw = max(2.0, (pct / 100.0) * chart_w)
            color = colors[idx % len(colors)]
            attr_name = item["attribute"]
            if len(attr_name) > 20:
                attr_name = attr_name[:18] + "..."

            # Label
            svg_parts.append(
                f'<text x="{left_label_w - 10}" y="{y + 16}" font-size="11" font-weight="600" fill="#334155" text-anchor="end">{attr_name}</text>'
            )
            # Bar background
            svg_parts.append(
                f'<rect x="{left_label_w}" y="{y}" width="{chart_w}" height="{bar_height}" rx="6" fill="#f1f5f9"/>'
            )
            # Bar fill
            svg_parts.append(
                f'<rect x="{left_label_w}" y="{y}" width="{bw}" height="{bar_height}" rx="6" fill="{color}"/>'
            )
            # Value text
            svg_parts.append(
                f'<text x="{left_label_w + bw + 8}" y="{y + 16}" font-size="11" font-weight="700" fill="{color}">{pct:.1f}%</text>'
            )

        svg_parts.append('</svg>')
        return "".join(svg_parts)

    @staticmethod
    def _generate_apa_narrative(
        n_valid: int,
        num_attrs: int,
        r2: float,
        adj_r2: float,
        importance_ranking: List[Dict[str, Any]],
        part_worths: Dict[str, Dict[str, float]],
        price_attr: Optional[str],
        wtp_results: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Biên soạn báo cáo học thuật chuẩn APA 7th Edition."""
        top_attr = importance_ranking[0] if importance_ranking else {"attribute": "N/A", "importance_pct": 0.0, "best_level": "N/A"}
        second_attr = importance_ranking[1] if len(importance_ranking) > 1 else None

        text = (
            f"Phân tích đánh đổi lựa chọn Conjoint Analysis (McFadden, 1974; Green & Srinivasan, 1990) "
            f"được tiến hành trên tập dữ liệu gồm N = {n_valid} hồ sơ đánh giá, bao quát {num_attrs} thuộc tính chính. "
            f"Mô hình đạt độ giải thích tốt với R² = {r2:.3f} (R² hiệu chỉnh = {adj_r2:.3f}). "
            f"Kết quả phân rã tiện ích từng phần (Part-Worth Utilities theo Effects Coding) chỉ ra rằng "
            f"thuộc tính có tác động chi phối mạnh nhất đến quyết định lựa chọn là '{top_attr['attribute']}', "
            f"chiếm {top_attr['importance_pct']:.1f}% tổng độ quan trọng tương đối (mức tối ưu nhất là '{top_attr['best_level']}'). "
        )

        if second_attr:
            text += (
                f"Đứng thứ hai là thuộc tính '{second_attr['attribute']}' với trọng số {second_attr['importance_pct']:.1f}% "
                f"(mức được ưa chuộng nhất là '{second_attr['best_level']}'). "
            )

        if price_attr and wtp_results:
            top_wtp = max(wtp_results, key=lambda x: x["wtp_valuation"])
            text += (
                f"Phân tích định giá sẵn sàng chi trả (Willingness-to-Pay; Hensher et al., 2005) dựa trên độ nhạy giá "
                f"xác nhận rằng cải tiến lên mức '{top_wtp['level']}' của thuộc tính '{top_wtp['attribute']}' "
                f"tương đương với mức gia tăng thặng dư giá trị ước tính đạt +{top_wtp['wtp_valuation']} đơn vị tiền tệ."
            )

        return text

    @staticmethod
    def _solve_linear_system(A: List[List[float]], b: List[float]) -> Optional[List[float]]:
        """Giải hệ phương trình tuyến tính A x = b bằng phương pháp khử Gauss-Jordan với chọn phần tử trụ."""
        n = len(b)
        M = [A[i][:] + [b[i]] for i in range(n)]

        for i in range(n):
            max_row = i
            max_val = abs(M[i][i])
            for r in range(i + 1, n):
                if abs(M[r][i]) > max_val:
                    max_val = abs(M[r][i])
                    max_row = r

            if max_val < 1e-12:
                return None

            M[i], M[max_row] = M[max_row], M[i]

            pivot = M[i][i]
            for c in range(i, n + 1):
                M[i][c] /= pivot

            for r in range(n):
                if r != i:
                    factor = M[r][i]
                    for c in range(i, n + 1):
                        M[r][c] -= factor * M[i][c]

        return [M[i][n] for i in range(n)]
