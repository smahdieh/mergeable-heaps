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

## Running

```bash
# Run the unit tests (150 tests, about 2 s)
pytest
```

| Test file | What it checks |
|---|---|
| `test_heap_interface.py` | Behaviour every heap must share (run once per heap): empty-heap errors, heapsort vs `sorted()`, duplicates, `decrease_key`, `merge`, and 3,000-step random operation sequences checked against a brute-force reference |
| `test_binomial_heap.py` | Distinct increasing root degrees, every B_k has 2^k nodes, one tree per 1-bit of n, entry handles stay valid after swaps |
| `test_fibonacci_heap.py` | Lazy insert, distinct root degrees after consolidate, max degree <= log_phi(n), cut and cascading-cut marking |
| `test_pairing_heap.py` | Heap order and `prev` pointers, two-pass pairing, cutting leftmost and middle children, no recursion-limit crash on 200,000 siblings |

More instructions (dataset, demo, benchmarks) will be added as the project grows.
