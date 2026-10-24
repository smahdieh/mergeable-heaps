"""Dijkstra's shortest paths on top of any MergeableHeap (the application benchmark).

Uses the decrease-key version (CLRS 24.3): each node is inserted once when it
is first reached and then only has its key lowered. With n nodes and m edges
this does at most n inserts, n extract_mins and m decrease_keys, so the
total cost is O(n log n + m) with a Fibonacci heap and O((n + m) log n) with
a binomial heap.

The graph is stored in CSR form (compressed sparse row): the out-edges of
node u are targets[offsets[u]:offsets[u + 1]] with matching weights.
"""

from typing import Sequence, Type

from mergeable_heaps.base import MergeableHeap

INF = float("inf")


def build_csr(num_nodes: int, src: Sequence[int], dst: Sequence[int], weight: Sequence[int]) -> tuple:
    """Turn an edge list into CSR arrays with a counting sort on the source node.

    Input: node count and three equal-length edge arrays.
    Output: (offsets, targets, weights) lists; offsets has num_nodes + 1 entries.
    """
    offsets = [0] * (num_nodes + 1)
    for u in src:
        offsets[u + 1] += 1
    for u in range(num_nodes):
        offsets[u + 1] += offsets[u]

    next_slot = offsets[:-1]
    targets = [0] * len(src)
    weights = [0] * len(src)
    for u, v, w in zip(src, dst, weight):
        slot = next_slot[u]
        targets[slot] = v
        weights[slot] = w
        next_slot[u] = slot + 1
    return offsets, targets, weights


def dijkstra(heap_cls: Type[MergeableHeap], graph: tuple, source: int = 0) -> tuple:
    """Single-source shortest paths with non-negative weights.

    Input: heap class to use, graph as (offsets, targets, weights) from
    build_csr, and the source node.
    Output: (dist, counts). dist[v] is the shortest distance (INF if
    unreachable); counts is {"insert", "extract_min", "decrease_key"} totals.
    """
    offsets, targets, weights = graph
    num_nodes = len(offsets) - 1
    dist = [INF] * num_nodes
    handles = [None] * num_nodes
    counts = {"insert": 1, "extract_min": 0, "decrease_key": 0}

    heap = heap_cls()
    dist[source] = 0
    handles[source] = heap.insert(0, source)
    while len(heap):
        node = heap.extract_min()
        counts["extract_min"] += 1
        u, du = node.value, node.key
        for i in range(offsets[u], offsets[u + 1]):
            v = targets[i]
            candidate = du + weights[i]
            if candidate < dist[v]:  # never true for finished nodes (weights >= 0)
                dist[v] = candidate
                handle = handles[v]
                if handle is None:
                    handles[v] = heap.insert(candidate, v)
                    counts["insert"] += 1
                else:
                    heap.decrease_key(handle, candidate)
                    counts["decrease_key"] += 1
    return dist, counts
