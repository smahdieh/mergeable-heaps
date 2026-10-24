"""Time the three heaps on the dataset and write one CSV row per measured phase.

Workloads (see benchmarks/workloads.py):
  heapsort   insert n random keys, then extract_min n times
  decrease   n random decrease_keys on a heap of n items, then drain it
  decrease_min  every item decreased once to below the minimum (worst case)
  sorted     heapsort on keys 0..n-1 (ascending insert order)
  reverse    heapsort on keys n-1..0 (descending insert order)
  memory     bytes per item of the heap structure
  dijkstra   shortest paths on the graph_<V> files

Usage:
  python benchmarks/run_benchmarks.py                       # everything, all heaps (slow)
  python benchmarks/run_benchmarks.py --heaps pairing --out results/results_pairing.csv
  python benchmarks/run_benchmarks.py --sizes 1000 10000 --graph-sizes 1000 --repeats 1
"""

import argparse
import csv
import json
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "benchmarks"))

from mergeable_heaps import BinomialHeap, FibonacciHeap, PairingHeap  # noqa: E402
from mergeable_heaps.dataset import load_array  # noqa: E402
from mergeable_heaps.dijkstra import build_csr  # noqa: E402
import workloads  # noqa: E402

HEAPS = {"binomial": BinomialHeap, "fibonacci": FibonacciHeap, "pairing": PairingHeap}
WORKLOADS = ["heapsort", "decrease", "decrease_min", "sorted", "reverse", "memory", "dijkstra"]
DEFAULT_SIZES = [1_000, 3_000, 10_000, 30_000, 100_000, 300_000,
                 1_000_000, 3_000_000, 10_000_000]
FIELDS = ["heap", "workload", "phase", "n", "repeat", "ops", "seconds", "bytes_per_item", "check"]


def parse_args() -> argparse.Namespace:
    """Read the command-line options."""
    parser = argparse.ArgumentParser(description="Benchmark the mergeable heaps.")
    parser.add_argument("--heaps", nargs="+", choices=HEAPS, default=list(HEAPS))
    parser.add_argument("--workloads", nargs="+", choices=WORKLOADS, default=WORKLOADS)
    parser.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES, help="values of n")
    parser.add_argument("--graph-sizes", type=int, nargs="+",
                        default=[1_000, 10_000, 100_000, 1_000_000], help="graph node counts V")
    parser.add_argument("--repeats", type=int, default=3, help="repeats for n <= 1,000,000")
    parser.add_argument("--large-repeats", type=int, default=1, help="repeats for n > 1,000,000")
    parser.add_argument("--adversarial-max", type=int, default=1_000_000,
                        help="largest n for the sorted / reverse workloads")
    parser.add_argument("--memory-max", type=int, default=1_000_000,
                        help="largest n for the memory workload (tracemalloc is slow)")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "results.csv")
    return parser.parse_args()


def repeats_for(n: int, args: argparse.Namespace) -> int:
    """Input: problem size, options. Output: how many times to repeat it."""
    return args.repeats if n <= 1_000_000 else args.large_repeats


class ResultWriter:
    """Appends rows to the CSV and flushes each one, so a long run that is
    stopped early still keeps everything measured so far."""

    def __init__(self, path: Path) -> None:
        """Input: CSV path (created with a header if it does not exist)."""
        path.parent.mkdir(parents=True, exist_ok=True)
        is_new = not path.exists()
        self._file = path.open("a", newline="")
        self._writer = csv.DictWriter(self._file, fieldnames=FIELDS)
        if is_new:
            self._writer.writeheader()

    def write(self, **row) -> None:
        """Input: one row as keyword arguments (missing fields left blank). Output: None."""
        self._writer.writerow(row)
        self._file.flush()

    def close(self) -> None:
        """Close the file."""
        self._file.close()


def log(message: str, start: float) -> None:
    """Print a progress line with the elapsed time."""
    print(f"[{time.perf_counter() - start:7.1f}s] {message}", flush=True)


def save_environment(out_dir: Path) -> None:
    """Record the machine and Python version next to the results (for the report)."""
    info = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }
    (out_dir / "environment.json").write_text(json.dumps(info, indent=2) + "\n")


def run_key_workloads(args, heaps, out: ResultWriter, start: float) -> None:
    """Run every key-based workload for every size and heap."""
    sizes = sorted(args.sizes)
    max_n = sizes[-1]
    all_keys = list(load_array(args.data_dir / "keys.bin", "i", limit=max_n))
    all_targets = list(load_array(args.data_dir / "decrease_targets.bin", "I", limit=max_n))
    all_amounts = list(load_array(args.data_dir / "decrease_amounts.bin", "i", limit=max_n))
    if len(all_keys) < max_n:
        sys.exit(f"keys.bin has only {len(all_keys):,} keys; regenerate with --n {max_n}")

    for n in sizes:
        keys = all_keys[:n]
        for name, heap_cls in heaps.items():
            for rep in range(repeats_for(n, args)):
                if "heapsort" in args.workloads:
                    for phase, ops, sec in workloads.heapsort(heap_cls, keys):
                        out.write(heap=name, workload="heapsort", phase=phase, n=n,
                                  repeat=rep, ops=ops, seconds=f"{sec:.6f}")
                if "decrease" in args.workloads:
                    phases = workloads.decrease_key(heap_cls, keys, all_targets[:n], all_amounts[:n])
                    for phase, ops, sec in phases:
                        out.write(heap=name, workload="decrease", phase=phase, n=n,
                                  repeat=rep, ops=ops, seconds=f"{sec:.6f}")
                if "decrease_min" in args.workloads:
                    for phase, ops, sec in workloads.decrease_to_min(heap_cls, keys, all_targets[:n]):
                        out.write(heap=name, workload="decrease_min", phase=phase, n=n,
                                  repeat=rep, ops=ops, seconds=f"{sec:.6f}")
                for order in ("sorted", "reverse"):
                    if order in args.workloads and n <= args.adversarial_max:
                        ordered = range(n) if order == "sorted" else range(n - 1, -1, -1)
                        for phase, ops, sec in workloads.heapsort(heap_cls, ordered):
                            out.write(heap=name, workload=order, phase=phase, n=n,
                                      repeat=rep, ops=ops, seconds=f"{sec:.6f}")
            if "memory" in args.workloads and n <= args.memory_max:
                per_item = workloads.bytes_per_item(heap_cls, keys)
                out.write(heap=name, workload="memory", phase="memory", n=n,
                          bytes_per_item=f"{per_item:.1f}")
            log(f"n={n:,} {name} done", start)


def run_dijkstra(args, heaps, out: ResultWriter, start: float) -> None:
    """Run Dijkstra on every graph size for every heap."""
    for num_nodes in sorted(args.graph_sizes):
        parts = [load_array(args.data_dir / f"graph_{num_nodes}_{p}.bin", "i")
                 for p in ("src", "dst", "weight")]
        graph = build_csr(num_nodes, *parts)
        del parts
        for name, heap_cls in heaps.items():
            for rep in range(repeats_for(num_nodes, args)):
                phases, checksum, counts = workloads.shortest_paths(heap_cls, graph)
                for phase, ops, sec in phases:
                    out.write(heap=name, workload="dijkstra", phase=phase, n=num_nodes,
                              repeat=rep, ops=ops, seconds=f"{sec:.6f}",
                              check=f"{checksum};{counts['decrease_key']}")
            log(f"dijkstra V={num_nodes:,} {name} done "
                f"(decrease_keys={counts['decrease_key']:,})", start)


def main() -> None:
    """Run the selected workloads and write results to --out."""
    args = parse_args()
    heaps = {name: HEAPS[name] for name in args.heaps}
    start = time.perf_counter()
    out = ResultWriter(args.out)
    save_environment(args.out.parent)
    try:
        if set(args.workloads) - {"dijkstra"}:
            run_key_workloads(args, heaps, out, start)
        if "dijkstra" in args.workloads:
            run_dijkstra(args, heaps, out, start)
    finally:
        out.close()
    log(f"finished; results in {args.out}", start)


if __name__ == "__main__":
    main()
