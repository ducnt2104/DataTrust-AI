import pytest
from app.engine.conjoint_engine import ConjointAnalysisEngine


def test_conjoint_estimation_and_importance():
    """Kiểm thử tính năng ước lượng tiện ích từng phần và xếp hạng độ quan trọng thuộc tính."""
    attributes_config = {
        "Thương hiệu": ["Apple", "Samsung", "Xiaomi"],
        "Dung lượng pin": ["3000mAh", "4000mAh", "5000mAh"],
        "Mức giá": ["10M", "15M", "20M"]
    }

    # Sinh dữ liệu trực giao giả lập phản ánh sở thích:
    # Apple > Samsung > Xiaomi; 5000mAh > 4000mAh > 3000mAh; 10M > 15M > 20M
    data = [
        {"Thương hiệu": "Apple", "Dung lượng pin": "5000mAh", "Mức giá": "10M", "rating": 9.5},
        {"Thương hiệu": "Apple", "Dung lượng pin": "4000mAh", "Mức giá": "15M", "rating": 8.0},
        {"Thương hiệu": "Apple", "Dung lượng pin": "3000mAh", "Mức giá": "20M", "rating": 6.5},
        {"Thương hiệu": "Samsung", "Dung lượng pin": "5000mAh", "Mức giá": "15M", "rating": 7.5},
        {"Thương hiệu": "Samsung", "Dung lượng pin": "4000mAh", "Mức giá": "20M", "rating": 6.0},
        {"Thương hiệu": "Samsung", "Dung lượng pin": "3000mAh", "Mức giá": "10M", "rating": 7.0},
        {"Thương hiệu": "Xiaomi", "Dung lượng pin": "5000mAh", "Mức giá": "20M", "rating": 5.5},
        {"Thương hiệu": "Xiaomi", "Dung lượng pin": "4000mAh", "Mức giá": "10M", "rating": 6.5},
        {"Thương hiệu": "Xiaomi", "Dung lượng pin": "3000mAh", "Mức giá": "15M", "rating": 4.5},
    ]

    res = ConjointAnalysisEngine.compute_conjoint_analysis(
        profiles_data=data,
        attributes_config=attributes_config,
        rating_key="rating",
        price_attribute_name="Mức giá"
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == 9
    assert res["attributes_count"] == 3
    assert res["model_fit"]["r_squared"] > 0.85
    assert res["model_fit"]["fit_quality"] == "Rất tốt (Excellent)"

    # Kiểm tra tổng tiện ích effects coding của từng thuộc tính xấp xỉ 0
    pw = res["part_worth_utilities"]
    for attr, levels in attributes_config.items():
        attr_sum = sum(pw[attr][lvl] for lvl in levels)
        assert abs(attr_sum) < 1e-3, f"Tổng tiện ích thuộc tính {attr} phải bằng 0 (hiện tại: {attr_sum})"

    # Apple phải có tiện ích cao hơn Xiaomi
    assert pw["Thương hiệu"]["Apple"] > pw["Thương hiệu"]["Xiaomi"]
    # 10M phải có tiện ích cao hơn 20M
    assert pw["Mức giá"]["10M"] > pw["Mức giá"]["20M"]

    # Kiểm tra xếp hạng độ quan trọng
    ranking = res["importance_ranking"]
    assert len(ranking) == 3
    total_imp = sum(item["importance_pct"] for item in ranking)
    assert abs(total_imp - 100.0) < 0.2

    # Biểu đồ SVG và thuyết minh APA
    assert "<svg" in res["svg_importance_chart"]
    assert "Conjoint Analysis" in res["apa_narrative"]
    assert "McFadden" in res["apa_narrative"]


def test_conjoint_wtp_and_market_simulator():
    """Kiểm thử tính toán Willingness to Pay và Mô phỏng Thị phần Lựa chọn Logit."""
    attributes_config = {
        "Dịch vụ khách hàng": ["Cơ bản", "Ưu tiên 24/7"],
        "Giá thuê bao": ["100k", "200k"]
    }

    data = [
        {"Dịch vụ khách hàng": "Ưu tiên 24/7", "Giá thuê bao": "100k", "rating": 9.0},
        {"Dịch vụ khách hàng": "Ưu tiên 24/7", "Giá thuê bao": "200k", "rating": 7.0},
        {"Dịch vụ khách hàng": "Cơ bản", "Giá thuê bao": "100k", "rating": 6.0},
        {"Dịch vụ khách hàng": "Cơ bản", "Giá thuê bao": "200k", "rating": 4.0},
        {"Dịch vụ khách hàng": "Ưu tiên 24/7", "Giá thuê bao": "100k", "rating": 8.8},
        {"Dịch vụ khách hàng": "Cơ bản", "Giá thuê bao": "200k", "rating": 4.2},
    ]

    res = ConjointAnalysisEngine.compute_conjoint_analysis(
        profiles_data=data,
        attributes_config=attributes_config,
        rating_key="rating",
        price_attribute_name="Giá thuê bao"
    )

    assert res["status"] == "SUCCESS"
    assert res["willingness_to_pay"] is not None
    assert len(res["willingness_to_pay"]) == 2

    # WTP của gói Ưu tiên 24/7 phải dương (người dùng sẵn sàng trả thêm tiền)
    wtp_vip = next(w for w in res["willingness_to_pay"] if w["level"] == "Ưu tiên 24/7")
    assert wtp_vip["wtp_valuation"] > 0

    # Kiểm thử Simulator
    candidate_profiles = [
        {
            "id": "Gói Cao Cấp",
            "attributes": {"Dịch vụ khách hàng": "Ưu tiên 24/7", "Giá thuê bao": "100k"}
        },
        {
            "id": "Gói Tiết Kiệm",
            "attributes": {"Dịch vụ khách hàng": "Cơ bản", "Giá thuê bao": "200k"}
        }
    ]

    shares = ConjointAnalysisEngine.simulate_choice_shares(
        part_worth_utilities=res["part_worth_utilities"],
        intercept=res["overall_utility_intercept"],
        candidate_profiles=candidate_profiles
    )

    assert len(shares) == 2
    assert shares[0]["profile_id"] == "Gói Cao Cấp"
    assert shares[0]["choice_share_pct"] > shares[1]["choice_share_pct"]
    total_share = sum(s["choice_share_pct"] for s in shares)
    assert abs(total_share - 100.0) < 0.1


def test_conjoint_insufficient_sample_and_levels():
    """Kiểm thử bắt lỗi dữ liệu thiếu mẫu hoặc cấu hình thuộc tính không hợp lệ."""
    # Thiếu mẫu (< 6)
    res_sample = ConjointAnalysisEngine.compute_conjoint_analysis(
        profiles_data=[{"A": "1", "rating": 5}],
        attributes_config={"A": ["1", "2"], "B": ["1", "2"]}
    )
    assert res_sample["status"] == "INSUFFICIENT_SAMPLE"

    # Thiếu thuộc tính (< 2)
    res_attrs = ConjointAnalysisEngine.compute_conjoint_analysis(
        profiles_data=[{"A": "1", "rating": 5}] * 10,
        attributes_config={"A": ["1", "2"]}
    )
    assert res_attrs["status"] == "INSUFFICIENT_ATTRIBUTES"
