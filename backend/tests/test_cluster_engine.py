"""
Unit tests for Respondent Clustering & Typology Segmentation Engine
"""

import pytest
from app.engine.cluster_engine import ClusterEngine


def test_standardize_matrix():
    raw_data = [
        [10.0, 100.0],
        [20.0, 200.0],
        [30.0, 300.0]
    ]
    z, means, stds = ClusterEngine.standardize_matrix(raw_data)
    assert len(z) == 3
    assert len(z[0]) == 2
    assert abs(means[0] - 20.0) < 1.0e-5
    assert abs(means[1] - 200.0) < 1.0e-5
    # The mean of z across rows should be 0.0
    col0_mean = sum(z[i][0] for i in range(3)) / 3.0
    assert abs(col0_mean) < 1.0e-5


def test_euclidean_distance():
    p1 = [0.0, 0.0]
    p2 = [3.0, 4.0]
    dist = ClusterEngine.euclidean_distance(p1, p2)
    assert abs(dist - 5.0) < 1.0e-5


def test_run_kmeans_and_silhouette():
    # 2 clearly separated synthetic clusters:
    # Cluster A: around (1.0, 1.0)
    # Cluster B: around (10.0, 10.0)
    data = [
        [1.0, 1.1],
        [1.2, 0.9],
        [0.8, 1.0],
        [1.1, 1.3],
        [10.0, 10.1],
        [9.8, 10.2],
        [10.2, 9.9],
        [10.1, 10.3]
    ]

    res = ClusterEngine.run_kmeans(data, k=2, seed=42)
    assert res["converged"] is True
    assert res["k"] == 2
    assert sum(res["cluster_sizes"]) == 8

    # The two groups should be segmented accurately (4 in each)
    assert sorted(res["cluster_sizes"]) == [4, 4]

    # Silhouette score should be high (> 0.70) because the clusters are very far apart
    sil = ClusterEngine.calculate_silhouette_score(data, res["assignments"], k=2)
    assert sil["overall_score"] > 0.70
    assert len(sil["cluster_scores"]) == 2


def test_feature_importance_and_personas():
    data = [
        [5.0, 1.0],
        [5.0, 1.2],
        [5.0, 1.1],
        [1.0, 5.0],
        [1.2, 5.0],
        [1.1, 5.0]
    ]
    assignments = [0, 0, 0, 1, 1, 1]
    feature_names = ["Hài Lòng Dịch Vụ", "Ý Kiến Phàn Nàn"]

    importance = ClusterEngine.calculate_feature_importance(
        raw_data=data,
        assignments=assignments,
        k=2,
        feature_names=feature_names
    )
    assert len(importance) == 2
    assert importance[0]["f_ratio"] > 10.0  # high separation
    assert importance[0]["eta_squared"] > 0.80

    personas = ClusterEngine.generate_persona_profiles(
        feature_importance=importance,
        cluster_sizes=[3, 3],
        total_n=6,
        k=2
    )
    assert len(personas) == 2
    assert personas[0]["percentage"] == 50.0
    assert personas[1]["percentage"] == 50.0
