"""Sanity-check benchmark CSVs: are the results complete, consistent and plausible?

Checks:
  1. completeness  every heap has every workload / phase / size
  2. agreement     Dijkstra gives the same total distance with all three heaps
  3. scaling       time per operation, divided by the theoretical cost, stays
                   roughly flat as n grows (a jump means something other than
                   the heap is being measured, e.g. swapping)

Usage:
  python benchmarks/check_results.py                         # all results/results_*.csv
  python benchmarks/check_results.py results/quick.csv
"""

import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEAPS = ["binomial", "fibonacci", "pairing"]

# Expected cost per operation as a function of n (amortized, CLRS / original papers).
THEORY = {
    ("heapsort", "insert"): {"binomial": "1", "fibonacci": "1", "pairing": "1"},
    ("heapsort", "extract_min"): {"binomial": "log n", "fibonacci": "log n", "pairing": "log n"},
    ("decrease", "extract_after_decrease"): {"binomial": "log n", "fibonacci": "log n", "pairing": "log n"},
    # Every item decreased below the minimum: binomial bubbles to the root,
    # Fibonacci cuts (amortized O(1)), pairing cuts and melds (O(1)).
    ("decrease_min", "decrease_key_to_min"): {"binomial": "log n", "fibonacci": "1", "pairing": "1"},
}
COST = {"1": lambda n: 1.0, "log n": lambda n: math.log2(n)}
JUMP_LIMIT = 1.6  # flag if normalized cost grows more than 60% from one size to the next


def load(paths):
    """Read the CSVs; rows from a "*sequential*" file replace the matching
    (heap, workload, phase, n) rows of the parallel run, which swapped at n = 10^7.

    Input: CSV paths. Output: list of row dicts.
    """
    rows, rerun = [], []
    for path in paths:
        with open(path, newline="") as f:
            (rerun if "sequential" in Path(path).name else rows).extend(csv.DictReader(f))
    redone = {(r["heap"], r["workload"], r["phase"], r["n"]) for r in rerun}
    kept = [r for r in rows if (r["heap"], r["workload"], r["phase"], r["n"]) not in redone]
    return kept + rerun


def main() -> None:
    """Run the three checks and print a report. Exit code 1 if any check fails."""
    paths = sys.argv[1:] or sorted(str(p) for p in (ROOT / "results").glob("results_*.csv"))
    rows = load(paths)
    print(f"Read {len(rows)} rows from {len(paths)} file(s)\n")
    failed = False

    # Median seconds per (workload, phase, n, heap); the sequential 10M file overrides.
    timings = defaultdict(list)
    ops = {}
    for r in rows:
        if r["seconds"]:
            key = (r["workload"], r["phase"], int(r["n"]), r["heap"])
            timings[key].append(float(r["seconds"]))
            ops[key] = int(r["ops"])

    # 1. completeness
    cells = defaultdict(set)
    for wl, ph, n, heap in timings:
        cells[(wl, ph, n)].add(heap)
    missing = [(k, set(HEAPS) - v) for k, v in sorted(cells.items()) if v != set(HEAPS)]
    print("1. Completeness:", "OK" if not missing else "MISSING")
    for (wl, ph, n), heaps in missing:
        print(f"   {wl}/{ph} n={n:,}: no result for {', '.join(sorted(heaps))}")
    failed |= bool(missing)

    # 2. Dijkstra agreement
    sums = defaultdict(set)
    for r in rows:
        if r["workload"] == "dijkstra" and r["check"]:
            sums[int(r["n"])].add(r["check"].split(";")[0])
    bad = {n: s for n, s in sums.items() if len(s) != 1}
    print("\n2. Dijkstra distances identical across heaps:", "OK" if not bad else "MISMATCH")
    for n in sorted(sums):
        print(f"   V={n:>9,}: sum of distances = {next(iter(sums[n])) if n not in bad else sums[n]}")
    failed |= bool(bad)

    # 3. scaling vs theory
    print(f"\n3. Scaling: nanoseconds per op / theoretical cost (should stay roughly flat;"
          f" '!' = jump > {JUMP_LIMIT}x)")
    for (wl, ph), by_heap in THEORY.items():
        sizes = sorted({n for (w, p, n, _) in timings if (w, p) == (wl, ph)})
        if not sizes:
            continue
        print(f"   {wl}/{ph}" + "".join(f"{n:>12,}" for n in sizes))
        for heap, cost in by_heap.items():
            line, prev = f"   {heap:<9} O({cost})".ljust(len(wl) + len(ph) + 4), None
            for n in sizes:
                key = (wl, ph, n, heap)
                if key not in timings:
                    line += f"{'-':>12}"
                    continue
                value = statistics.median(timings[key]) / ops[key] / COST[cost](n) * 1e9
                flag = "!" if prev and value > JUMP_LIMIT * prev else " "
                failed |= flag == "!"
                line += f"{value:>11.0f}{flag}"
                prev = value
            print(line)

    print("\nResult:", "all checks passed" if not failed else "some checks FAILED (see above)")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
