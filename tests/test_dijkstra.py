"""Tests for the Dijkstra application, checked against Bellman-Ford."""

import pytest

from mergeable_heaps.dataset import random_graph
from mergeable_heaps.dijkstra import INF, build_csr, dijkstra


def bellman_ford(num_nodes, src, dst, weight, source=0):
    """Slow but simple reference: relax every edge V - 1 times."""
    dist = [INF] * num_nodes
    dist[source] = 0
    for _ in range(num_nodes - 1):
        changed = False
        for u, v, w in zip(src, dst, weight):
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                changed = True
        if not changed:
            break
    return dist


def test_build_csr_groups_edges_by_source():
    offsets, targets, weights = build_csr(3, [2, 0, 2, 1], [0, 1, 1, 2], [5, 6, 7, 8])
    assert offsets == [0, 1, 2, 4]
    assert targets[0:1] == [1] and weights[0:1] == [6]
    assert targets[1:2] == [2] and weights[1:2] == [8]
    assert sorted(zip(targets[2:4], weights[2:4])) == [(0, 5), (1, 7)]


def test_small_hand_checked_graph(heap_cls):
    # 0 -> 1 (4), 0 -> 2 (1), 2 -> 1 (2), 1 -> 3 (1), 2 -> 3 (5)
    graph = build_csr(5, [0, 0, 2, 1, 2], [1, 2, 1, 3, 3], [4, 1, 2, 1, 5])
    dist, counts = dijkstra(heap_cls, graph, source=0)
    assert dist == [0, 3, 1, 4, INF]  # node 4 is unreachable
    assert counts["decrease_key"] >= 1  # 0->1 (4) is improved by 0->2->1 (3)


@pytest.mark.parametrize("seed", range(3))
def test_matches_bellman_ford_on_random_graphs(heap_cls, seed):
    num_nodes = 300
    src, dst, weight = random_graph(num_nodes, avg_degree=4, seed=seed, max_weight=50)
    dist, counts = dijkstra(heap_cls, build_csr(num_nodes, src, dst, weight))
    assert dist == bellman_ford(num_nodes, src, dst, weight)
    # Strongly connected graph: every node is inserted and extracted exactly once.
    assert counts["insert"] == counts["extract_min"] == num_nodes
