import pytest
import numpy as np
from app.engine.bayesian_network_engine import BayesianNetworkEngine


def test_bayesian_network_engine_success():
    np.random.seed(42)
    N = 80

    # Chain: X1 -> X2 -> X3 -> X4
    x1 = np.random.normal(0, 1, N)
    x2 = 0.8 * x1 + np.random.normal(0, 0.4, N)
    x3 = 0.7 * x2 + np.random.normal(0, 0.4, N)
    x4 = 0.6 * x3 + np.random.normal(0, 0.4, N)

    data = np.column_stack([x1, x2, x3, x4]).tolist()
    labels = ["Privacy Concern", "Trust in Platform", "Ease of Use", "Satisfaction"]

    res = BayesianNetworkEngine.learn_bayesian_network(
        data_matrix=data,
        node_labels=labels,
        max_parents=3
    )

    assert res["status"] == "SUCCESS"
    assert res["model_type"] == "GAUSSIAN_BAYESIAN_NETWORK_DAG"
    diag = res["diagnostics"]
    assert diag["sample_size"] == 80
    assert diag["n_nodes"] == 4
    assert diag["is_acyclic"] is True
    assert diag["total_edges"] >= 3
    assert diag["bic_gain"] > 0

    # Check nodes and Markov Blankets
    nodes = res["nodes"]
    assert len(nodes) == 4
    for node in nodes:
        assert "markov_blanket" in node
        assert "topological_role" in node

    # Check edges
    edges = res["edges"]
    assert len(edges) >= 3
    assert "<svg" in res["svg_visualization"]
    assert "APA 7th Edition" in res["apa_narrative"]
    assert "Heckerman" in res["apa_narrative"]


def test_bayesian_network_insufficient_sample():
    res = BayesianNetworkEngine.learn_bayesian_network(
        data_matrix=[[1.0, 2.0, 3.0], [2.0, 3.0, 4.0]],
        node_labels=["A", "B", "C"]
    )
    assert res["status"] == "INSUFFICIENT_SAMPLE"


def test_bayesian_network_insufficient_nodes():
    res = BayesianNetworkEngine.learn_bayesian_network(
        data_matrix=[[float(i), float(i*2)] for i in range(25)],
        node_labels=["A", "B"]
    )
    assert res["status"] == "INSUFFICIENT_NODES"
