# Mergeable Heaps: Binomial vs Fibonacci vs Pairing

COSC 520 – Assignment 2 (UBC Okanagan, Fall 2026)

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
# Run the unit tests
pytest
```

More instructions (dataset, demo, benchmarks) will be added as the project grows.
