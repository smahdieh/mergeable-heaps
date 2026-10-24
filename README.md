# Mergeable Heaps: Binomial vs Fibonacci vs Pairing

COSC 520 – Assignment 2 (UBC Okanagan, Fall 2026)

Repository: https://github.com/smahdieh/mergeable-heaps

Compares three mergeable priority queues, all implemented from scratch
(no `heapq` or other heap libraries):

| Module | Structure |
|---|---|
| `binomial_heap.py` | Binomial heap |
| `fibonacci_heap.py` | Fibonacci heap |
| `pairing_heap.py` | Pairing heap |

## Project structure

```
mergeable-heaps/
├── src/mergeable_heaps/   # heap implementations
├── data/                  # dataset generator (generated data is not committed)
├── benchmarks/            # timing scripts and plotting
├── results/               # benchmark CSVs and figures
└── tests/                 # unit tests (pytest)
```

## Setup

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Dataset

Download: [mergeable-heaps-dataset.zip](https://ubcca-my.sharepoint.com/:u:/g/personal/mahdieh_sadat_ubc_ca/IQBlhduZTLUxSayS2AOLefOJAQj3RfmTP1xv08hxN26Kbz8?e=qZ7HDQ)
(UBC OneDrive, 194 MB). Unzip it into `data/`, then run
`python data/generate_dataset.py --verify`. You can also regenerate it (see
below): the same seed always gives byte-identical files, checked by `manifest.json`.

```bash
# Generate the full dataset (about 20 s, 242 MB, seed 42)
python data/generate_dataset.py
#    or a small one for a quick try:
python data/generate_dataset.py --n 100000 --graph-nodes 1000 10000

# Check downloaded or generated files against the SHA-256 checksums in manifest.json
python data/generate_dataset.py --verify
```

| File | Contents | Used for |
|---|---|---|
| `keys.bin` | 10,000,000 uniform random keys in [0, 2^31) | insert, heapsort |
| `decrease_targets.bin` | 10,000,000 raw uint32 values; node index = `(raw * n) >> 32` | which node to decrease |
| `decrease_amounts.bin` | 10,000,000 amounts in [1, 2^24] | how much to decrease it |
| `graph_<V>_{src,dst,weight}.bin` | random directed graph, V = 10^3 to 10^6 nodes, 10 V edges, weights in [1, 1000], strongly connected (contains a random Hamiltonian cycle) | Dijkstra |
| `manifest.json` | seed, parameters, count and SHA-256 of every file | verification |

All files are raw little-endian 4-byte integers (Python `array`). Benchmarks
for smaller n read a prefix of the same file, so every size comes from the
same distribution. Sorted and reverse-sorted inputs are `range(n)` and need no file.

## Running

```bash
# Run the unit tests (177 tests, about 2 s)
pytest
```

### Benchmarks

```bash
# Quick check (about 30 s)
python benchmarks/run_benchmarks.py --sizes 1000 10000 100000 --graph-sizes 1000 10000 100000 --repeats 1 --out results/quick.csv

# Full run used in the report. Step 1: all sizes up to 3*10^6 and Dijkstra,
# the three heaps as parallel processes (about 19 min on an M1 Pro, 16 GB RAM):
python benchmarks/run_benchmarks.py --heaps binomial  --out results/results_binomial.csv
python benchmarks/run_benchmarks.py --heaps fibonacci --out results/results_fibonacci.csv
python benchmarks/run_benchmarks.py --heaps pairing   --out results/results_pairing.csv

# Step 2: n = 10^7 again, ONE heap at a time. At 10^7 three parallel
# processes need more than 16 GB, the machine swaps to disk, and the
# timings measure swapping instead of the heaps (see results/README.md).
for h in pairing binomial fibonacci; do
  python benchmarks/run_benchmarks.py --heaps $h --sizes 10000000 \
      --workloads heapsort decrease --out results/results_10M_sequential.csv
done
```

| Workload | What is timed | Sizes |
|---|---|---|
| `heapsort` | n inserts of random keys, then n extract_mins (two phases) | n = 10^3 to 10^7 |
| `decrease` | n random decrease_keys on a heap of n items, then draining it | n = 10^3 to 10^7 |
| `sorted`, `reverse` | heapsort on ascending / descending keys | n = 10^3 to 10^6 |
| `memory` | bytes per item of the heap structure (`tracemalloc`) | n = 10^3 to 10^6 |
| `dijkstra` | shortest paths from node 0 (decrease-key version) | V = 10^3 to 10^6, E = 10 V |

Each measurement is repeated 3 times for n <= 10^6 and once above that
(`--repeats`, `--large-repeats`). The garbage collector is paused inside every
timed phase. Every row of the CSV is one phase:
`heap, workload, phase, n, repeat, ops, seconds, bytes_per_item, check`
(`check` for Dijkstra is `sum of distances;decrease_key count`, and the sum
must be identical for all three heaps). `results/environment.json` records the
Python version and machine.

### Checking and plotting the results

```bash
# Completeness, Dijkstra agreement across heaps, and scaling vs theory
python benchmarks/check_results.py

# Figures + summary table into results/figures/ (add --copy-to ../report/figures for the report)
python benchmarks/plot_results.py
```

| Output | Shows |
|---|---|
| `runtime.pdf` | (a) heapsort time vs n with an n log n guide, (b) extract_min cost / log n, (c) decrease_key cost, (d) extract_min after decrease_keys / log n |
| `dijkstra_memory.pdf` | Dijkstra time vs graph size with a V log V guide, and memory per item |
| `input_order.pdf` | extract_min cost for random, ascending and descending keys (n = 10^6) |
| `summary_table.tex`, `summary.csv` | per-operation times at n = 10^7, Dijkstra at V = 10^6, memory |

Lines are medians over the repeats; shaded bands span min to max. Plots are
drawn with seaborn at the exact text width of the ACM small template and
typeset by LaTeX in the template's fonts (Linux Libertine, 10 pt), so they
match the report when included at `width=\linewidth`. Without a LaTeX
installation, add `--no-latex` (same plots, matplotlib's default font).

Main options of `run_benchmarks.py`:

| Option | Default | Meaning |
|---|---|---|
| `--heaps` | all three | `binomial`, `fibonacci`, `pairing` |
| `--workloads` | all | any of `heapsort decrease sorted reverse memory dijkstra` |
| `--sizes` | 10^3, 3·10^3, ..., 10^7 | values of n |
| `--graph-sizes` | 10^3 ... 10^6 | Dijkstra graph sizes V |
| `--repeats` / `--large-repeats` | 3 / 1 | repeats for n <= 10^6 / n > 10^6 |
| `--out` | `results/results.csv` | output CSV (rows are appended) |

| Test file | What it checks |
|---|---|
| `test_heap_interface.py` | Behaviour every heap must share (run once per heap): empty-heap errors, heapsort vs `sorted()`, duplicates, `decrease_key`, `merge`, and 3,000-step random operation sequences checked against a brute-force reference |
| `test_binomial_heap.py` | Distinct increasing root degrees, every B_k has 2^k nodes, one tree per 1-bit of n, entry handles stay valid after swaps |
| `test_fibonacci_heap.py` | Lazy insert, distinct root degrees after consolidate, max degree <= log_phi(n), cut and cascading-cut marking |
| `test_pairing_heap.py` | Heap order and `prev` pointers, two-pass pairing, cutting leftmost and middle children, no recursion-limit crash on 200,000 siblings |
| `test_dijkstra.py` | CSR graph building, a hand-checked graph, and Dijkstra with each heap equal to Bellman-Ford on random graphs |
| `test_dataset.py` | Generator is reproducible from its seed, smaller runs are prefixes of larger ones, value ranges, graphs are strongly connected, save/load round trip, checksum catches corrupted or missing files |

More instructions (dataset, demo, benchmarks) will be added as the project grows.
