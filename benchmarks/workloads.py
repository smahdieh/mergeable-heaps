"""Benchmark workloads. Each one runs a heap class on prepared data and returns
the measured phases as a list of (phase, operation count, seconds).

The garbage collector is paused during every timed phase: the heaps create
millions of small objects, and a collection pass in the middle of a phase
would add noise that has nothing to do with the data structure.
"""

import gc
import time
import tracemalloc
from typing import Sequence, Type

from mergeable_heaps.base import MergeableHeap
from mergeable_heaps.dataset import target_index
from mergeable_heaps.dijkstra import dijkstra


class _Timer:
    """Context manager: collect garbage, pause the GC, time the block."""

    def __enter__(self):
        gc.collect()
        gc.disable()
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.seconds = time.perf_counter() - self.start
        gc.enable()


def heapsort(heap_cls: Type[MergeableHeap], keys: Sequence[int]) -> list:
    """Insert all keys, then extract them all.

    Input: heap class, keys. Output: [("insert", n, s), ("extract_min", n, s)].
    """
    n = len(keys)
    heap = heap_cls()
    insert = heap.insert
    with _Timer() as t_insert:
        for key in keys:
            insert(key)
    extract = heap.extract_min
    with _Timer() as t_extract:
        for _ in range(n):
            extract()
    return [("insert", n, t_insert.seconds), ("extract_min", n, t_extract.seconds)]


def decrease_key(
    heap_cls: Type[MergeableHeap],
    keys: Sequence[int],
    targets: Sequence[int],
    amounts: Sequence[int],
) -> list:
    """Build a heap, run one decrease_key per item, then drain the heap.

    One extract_min is done first (untimed) so the Fibonacci and pairing heaps
    have real trees; otherwise every node would still be a root and
    decrease_key would never need to cut anything.

    Input: heap class, n keys, n raw targets and n amounts (dataset streams).
    Output: [("decrease_key", ops, s), ("extract_after_decrease", n - 1, s)].
    """
    n = len(keys)
    heap = heap_cls()
    handles = [heap.insert(key, i) for i, key in enumerate(keys)]
    gone = heap.extract_min().value

    ops = 0
    decrease = heap.decrease_key
    with _Timer() as t_decrease:
        for raw, amount in zip(targets, amounts):
            index = target_index(raw, n)
            if index != gone:
                node = handles[index]
                decrease(node, node.key - amount)
                ops += 1
    del handles
    extract = heap.extract_min
    with _Timer() as t_extract:
        for _ in range(n - 1):
            extract()
    return [("decrease_key", ops, t_decrease.seconds),
            ("extract_after_decrease", n - 1, t_extract.seconds)]


def decrease_to_min(heap_cls: Type[MergeableHeap], keys: Sequence[int],
                    targets: Sequence[int]) -> list:
    """Worst-case decrease_key: every item becomes the new minimum, once.

    Builds a heap, runs one extract_min (untimed) so real trees exist, then
    decreases every remaining item exactly once, in a random order given by
    the dataset's target stream, to a key below the current minimum. This
    forces the expensive path of each heap: the binomial heap must move the
    key up to its root (O(log n)), the Fibonacci heap must cut the node
    (O(1) amortized) and the pairing heap must cut and meld it.

    Input: heap class, n keys, n raw targets (only their order is used).
    Output: [("decrease_key_to_min", ops, s)].
    """
    n = len(keys)
    heap = heap_cls()
    handles = [heap.insert(key, i) for i, key in enumerate(keys)]
    gone = heap.extract_min().value
    new_key = heap.find_min().key
    # Random permutation of the items, decided by the dataset (not timed).
    order = sorted(range(n), key=targets.__getitem__)

    decrease = heap.decrease_key
    ops = 0
    with _Timer() as t:
        for index in order:
            if index != gone:
                new_key -= 1
                decrease(handles[index], new_key)
                ops += 1
    return [("decrease_key_to_min", ops, t.seconds)]


def shortest_paths(heap_cls: Type[MergeableHeap], graph: tuple) -> tuple:
    """Run Dijkstra from node 0.

    Input: heap class, CSR graph. Output: ([("dijkstra", edges, s)], checksum),
    where checksum = sum of all distances, so the three heaps can be checked
    against each other.
    """
    with _Timer() as t:
        dist, counts = dijkstra(heap_cls, graph, source=0)
    return [("dijkstra", len(graph[1]), t.seconds)], sum(dist), counts


def bytes_per_item(heap_cls: Type[MergeableHeap], keys: Sequence[int]) -> float:
    """Memory the heap structure itself uses, per item.

    The key objects already exist before tracing starts, so only the heap's
    own nodes (and its lists) are counted; the same keys are shared by all heaps.
    Input: heap class, keys. Output: traced bytes / len(keys).
    Done separately from timing because tracemalloc slows Python down.
    """
    gc.collect()
    tracemalloc.start()
    heap = heap_cls()
    for key in keys:
        heap.insert(key)
    heap.extract_min()  # let the heap build its trees (consolidate / pair)
    heap.insert(keys[0])
    used = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    return used / len(keys)
