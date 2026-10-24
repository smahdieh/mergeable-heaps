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
# Run the unit tests (164 tests, about 2 s)
pytest
```

| Test file | What it checks |
|---|---|
| `test_heap_interface.py` | Behaviour every heap must share (run once per heap): empty-heap errors, heapsort vs `sorted()`, duplicates, `decrease_key`, `merge`, and 3,000-step random operation sequences checked against a brute-force reference |
| `test_binomial_heap.py` | Distinct increasing root degrees, every B_k has 2^k nodes, one tree per 1-bit of n, entry handles stay valid after swaps |
| `test_fibonacci_heap.py` | Lazy insert, distinct root degrees after consolidate, max degree <= log_phi(n), cut and cascading-cut marking |
| `test_pairing_heap.py` | Heap order and `prev` pointers, two-pass pairing, cutting leftmost and middle children, no recursion-limit crash on 200,000 siblings |
| `test_dataset.py` | Generator is reproducible from its seed, smaller runs are prefixes of larger ones, value ranges, graphs are strongly connected, save/load round trip, checksum catches corrupted or missing files |

More instructions (dataset, demo, benchmarks) will be added as the project grows.
