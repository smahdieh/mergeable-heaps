"""Short demo of the three mergeable heaps (runs in a few seconds, no dataset needed).

Shows, for each heap:
  1. the basic operations on a small example (insert, find_min, decrease_key,
     merge, extract_min),
  2. Dijkstra on a small random graph, with all three heaps giving the same distances,
  3. a quick timing comparison on 100,000 random keys.

Usage:
  python demo.py
"""

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mergeable_heaps import BinomialHeap, FibonacciHeap, PairingHeap  # noqa: E402
from mergeable_heaps.dataset import random_graph  # noqa: E402
from mergeable_heaps.dijkstra import build_csr, dijkstra  # noqa: E402

HEAPS = [BinomialHeap, FibonacciHeap, PairingHeap]


def basic_operations(heap_cls) -> None:
    """Walk through every operation on a small example and print the result."""
    heap = heap_cls()
    tasks = {name: heap.insert(priority, name) for name, priority in
             [("email", 5), ("backup", 9), ("deploy", 3), ("report", 7)]}
    print(f"  inserted 4 tasks, min is {heap.find_min().value!r} (priority {heap.find_min().key})")

    heap.decrease_key(tasks["backup"], 1)
    print(f"  decrease_key(backup, 1) -> min is {heap.find_min().value!r}")

    other = heap_cls()
    other.insert(2, "meeting")
    heap.merge(other)
    print(f"  merged a heap with 'meeting' (priority 2) -> {len(heap)} items, other heap has {len(other)}")

    order = [heap.extract_min().value for _ in range(len(heap))]
    print(f"  extract_min until empty -> {order}")


def shortest_paths() -> None:
    """Run Dijkstra with each heap on the same graph and compare the answers."""
    num_nodes = 2_000
    graph = build_csr(num_nodes, *random_graph(num_nodes, avg_degree=5, seed=1))
    results = {}
    for heap_cls in HEAPS:
        dist, counts = dijkstra(heap_cls, graph, source=0)
        results[heap_cls.__name__] = dist
        print(f"  {heap_cls.__name__:<14} sum of distances = {sum(dist):,}  "
              f"(decrease_key calls: {counts['decrease_key']:,})")
    same = len({tuple(d) for d in results.values()}) == 1
    print(f"  all three heaps agree: {same}")


def timing(n: int = 100_000) -> None:
    """Heapsort n random keys with each heap and check the output is sorted."""
    rng = random.Random(7)
    keys = [rng.randrange(2**31) for _ in range(n)]
    expected = sorted(keys)
    print(f"  {'heap':<14}{'insert':>10}{'extract_min':>14}   sorted?")
    for heap_cls in HEAPS:
        heap = heap_cls()
        start = time.perf_counter()
        for key in keys:
            heap.insert(key)
        middle = time.perf_counter()
        out = [heap.extract_min().key for _ in range(n)]
        end = time.perf_counter()
        print(f"  {heap_cls.__name__:<14}{middle - start:>9.2f}s{end - middle:>13.2f}s   {out == expected}")


def main() -> None:
    """Run the three parts of the demo."""
    for heap_cls in HEAPS:
        print(f"\n== {heap_cls.__name__}: basic operations ==")
        basic_operations(heap_cls)
    print("\n== Dijkstra on a random graph (2,000 nodes, 10,000 edges) ==")
    shortest_paths()
    print("\n== Heapsort timing on 100,000 random keys ==")
    timing()
    print("\nFull benchmarks: see README (benchmarks/run_benchmarks.py).")


if __name__ == "__main__":
    main()
