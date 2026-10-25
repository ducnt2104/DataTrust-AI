import pytest
from app.engine.network_engine import PsychometricNetworkEngine


def test_network_engine_fitting():
    """Kiểm tra phân tích mạng lưới tâm lý học đo lường GGM, tính toán partial correlation và centrality."""
    # Tạo 15 quan sát mô phỏng cho 4 biến khảo sát:
    # Q1 (Chất lượng), Q2 (Trải nghiệm), Q3 (Hài lòng), Q4 (Giới thiệu)
    # Q1 và Q2 có quan hệ tương quan mạnh, Q3 và Q4 có quan hệ tương quan mạnh
    data = [
        [5.0, 5.0, 4.0, 4.0],
        [4.5, 5.0, 4.0, 4.5],
        [4.0, 4.5, 3.5, 3.5],
        [5.0, 4.5, 5.0, 5.0],
        [3.0, 3.0, 2.5, 2.0],
        [2.5, 3.0, 2.0, 2.5],
        [4.0, 4.0, 4.5, 4.0],
        [3.5, 4.0, 3.0, 3.5],
        [5.0, 5.0, 5.0, 4.5],
        [2.0, 2.5, 2.0, 2.0],
        [4.5, 4.0, 4.0, 4.0],
        [3.0, 3.5, 3.5, 3.0],
        [4.0, 4.5, 4.0, 4.5],
        [5.0, 4.5, 4.5, 5.0],
        [2.5, 2.0, 2.5, 2.0]
    ]
    node_names = [
        "Chất lượng dịch vụ",
        "Trải nghiệm khách hàng",
        "Mức độ hài lòng",
        "Khả năng giới thiệu"
    ]

    res = PsychometricNetworkEngine.analyze_network(
        data_matrix=data,
        node_names=node_names,
        regularization_threshold=0.05
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == 15
    assert res["num_nodes"] == 4
    assert res["possible_edges"] == 6
    assert res["num_edges"] > 0
    assert 0.0 <= res["density"] <= 1.0

    # Kiểm tra danh sách nút
    assert len(res["nodes"]) == 4
    for node in res["nodes"]:
        assert "name" in node
        assert "strength" in node
        assert "expected_influence" in node
        assert "closeness" in node
        assert "betweenness" in node
        # Tọa độ bố trí SVG phải nằm trong khung
        assert 40.0 <= node["x"] <= 460.0
        assert 40.0 <= node["y"] <= 320.0

    # Kiểm tra danh sách cạnh
    assert len(res["edges"]) == res["num_edges"]
    for edge in res["edges"]:
        assert edge["source"] != edge["target"]
        assert abs(edge["weight"]) > 0.0
        assert edge["edge_type"] in ["positive", "negative"]

    # Kiểm tra APA narrative
    assert "apa_narrative" in res
    assert "Psychometric Network Analysis" in res["apa_narrative"]
    assert "Gaussian Graphical Model" in res["apa_narrative"]


def test_network_engine_insufficient_samples():
    """Kiểm tra xử lý biên khi quá ít phản hồi hoặc quá ít câu hỏi."""
    # N < 4
    res_few_samples = PsychometricNetworkEngine.analyze_network(
        data_matrix=[[1.0, 2.0, 3.0], [2.0, 3.0, 4.0]],
        node_names=["A", "B", "C"]
    )
    assert res_few_samples["status"] == "INSUFFICIENT_SAMPLE"

    # P < 3
    res_few_vars = PsychometricNetworkEngine.analyze_network(
        data_matrix=[[1.0, 2.0], [2.0, 3.0], [3.0, 4.0], [4.0, 5.0]],
        node_names=["A", "B"]
    )
    assert res_few_vars["status"] == "INSUFFICIENT_VARIABLES"
