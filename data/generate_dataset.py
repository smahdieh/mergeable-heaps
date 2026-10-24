"""Generate the benchmark dataset (see src/mergeable_heaps/dataset.py for the format).

Creates in data/:
  keys.bin                    n random keys                (insert, heapsort)
  decrease_targets.bin        n raw decrease-key targets   (decrease-key)
  decrease_amounts.bin        n decrease amounts           (decrease-key)
  graph_<V>_{src,dst,weight}.bin  one graph per V          (Dijkstra)
  manifest.json               counts and SHA-256 checksums

Usage:
  python data/generate_dataset.py                        # full: 10M keys, graphs up to 1M nodes / 10M edges
  python data/generate_dataset.py --n 100000 --graph-nodes 1000 10000   # quick test run
  python data/generate_dataset.py --verify               # re-check existing files against the manifest
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mergeable_heaps.dataset import (  # noqa: E402
    decrease_ops,
    random_graph,
    random_keys,
    save_array,
    verify_dataset,
    write_manifest,
)

DATA_DIR = Path(__file__).resolve().parent


def main() -> None:
    """Parse arguments, generate every stream, write the files and the manifest."""
    parser = argparse.ArgumentParser(description="Generate the mergeable-heap benchmark dataset.")
    parser.add_argument("--n", type=int, default=10_000_000, help="number of keys and decrease ops")
    parser.add_argument("--graph-nodes", type=int, nargs="+",
                        default=[1_000, 10_000, 100_000, 1_000_000], help="graph sizes V")
    parser.add_argument("--avg-degree", type=int, default=10, help="edges per node in each graph")
    parser.add_argument("--seed", type=int, default=42, help="random seed")
    parser.add_argument("--out-dir", type=Path, default=DATA_DIR, help="output folder")
    parser.add_argument("--verify", action="store_true", help="only verify existing files")
    args = parser.parse_args()

    if args.verify:
        problems = verify_dataset(args.out_dir)
        print("\n".join(problems) if problems else "All files match manifest.json")
        sys.exit(1 if problems else 0)

    start = time.perf_counter()
    files = {}

    keys = random_keys(args.n, args.seed)
    save_array(keys, args.out_dir / "keys.bin")
    files["keys.bin"] = ("i", "uniform random keys in [0, 2^31)")
    del keys
    print(f"keys: {args.n:,} ({time.perf_counter() - start:.1f}s)")

    targets, amounts = decrease_ops(args.n, args.seed)
    save_array(targets, args.out_dir / "decrease_targets.bin")
    save_array(amounts, args.out_dir / "decrease_amounts.bin")
    files["decrease_targets.bin"] = ("I", "raw uint32; node index = (raw * n) >> 32")
    files["decrease_amounts.bin"] = ("i", "decrease-key amount in [1, 2^24]")
    del targets, amounts
    print(f"decrease ops: {args.n:,} ({time.perf_counter() - start:.1f}s)")

    for num_nodes in args.graph_nodes:
        src, dst, weight = random_graph(num_nodes, args.avg_degree, args.seed)
        for part, arr in (("src", src), ("dst", dst), ("weight", weight)):
            name = f"graph_{num_nodes}_{part}.bin"
            save_array(arr, args.out_dir / name)
            files[name] = ("i", f"graph V={num_nodes}, E={len(src)}: edge {part}")
        print(f"graph V={num_nodes:,} E={len(src):,} ({time.perf_counter() - start:.1f}s)")
        del src, dst, weight

    params = {
        "seed": args.seed,
        "n": args.n,
        "graph_nodes": args.graph_nodes,
        "avg_degree": args.avg_degree,
    }
    write_manifest(args.out_dir, params, files)
    print(f"Wrote {len(files)} files + manifest.json to {args.out_dir} "
          f"in {time.perf_counter() - start:.1f}s")


if __name__ == "__main__":
    main()
