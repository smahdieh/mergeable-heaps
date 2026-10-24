# Benchmark results

Machine: Apple M1 Pro (8 cores, 16 GB RAM), macOS, CPython 3.10.16
(`environment.json`). Dataset: seed 42, see `../data/manifest.json`.

| File | Contents |
|---|---|
| `results_binomial.csv`, `results_fibonacci.csv`, `results_pairing.csv` | Run 1: every workload and size, the three heaps as parallel processes |
| `results_10M_sequential.csv` | Run 2: `heapsort` and `decrease` at n = 10^7 again, one heap at a time |
| `log_*.txt` | progress logs of both runs |

**Which numbers to use:** for n = 10^7, the rows in `results_10M_sequential.csv`
replace the run-1 rows of the same heap, workload and phase. Everything else
comes from run 1. `benchmarks/check_results.py` applies this rule.

## Why n = 10^7 was run twice

In run 1 the three processes each held a heap of 10^7 nodes plus the input
lists (several GB each), and together they needed more than the 16 GB of RAM. macOS moved
memory to disk (`vm.swapusage` showed 4.3 GB of swap in use), and the
operations that ran while another process was competing for memory became
2-3 times slower. `check_results.py` caught this: time per extract_min divided
by log2(n) was flat from 10^3 to 3·10^6 and then jumped at 10^7.

Run 2 repeated n = 10^7 with one process at a time. Seconds per phase:

| Heap | Phase | Run 1 (parallel) | Run 2 (sequential) | Run 1 / Run 2 |
|---|---|---|---|---|
| binomial | insert | 21.9 | 22.8 | 0.96 |
| binomial | extract_min | 429.1 | 153.9 | 2.79 |
| binomial | decrease_key | 15.2 | 10.4 | 1.46 |
| binomial | extract_after_decrease | 167.9 | 154.2 | 1.09 |
| fibonacci | insert | 6.8 | 5.8 | 1.17 |
| fibonacci | extract_min | 388.1 | 193.0 | 2.01 |
| fibonacci | decrease_key | 10.1 | 10.2 | 0.98 |
| fibonacci | extract_after_decrease | 216.5 | 191.6 | 1.13 |
| pairing | insert | 5.4 | 5.3 | 1.03 |
| pairing | extract_min | 103.2 | 90.0 | 1.15 |
| pairing | decrease_key | 12.2 | 11.2 | 1.09 |
| pairing | extract_after_decrease | 337.7 | 107.1 | 3.15 |

With run 2, every 10^7 point is back on the trend of the smaller sizes and
all checks in `check_results.py` for these workloads pass. Sizes up to 3·10^6 fit in memory with
all three processes running, so they did not need to be repeated.

## Worst-case decrease_key (`results_decrease_min.csv`)

Run separately, one heap at a time (`--workloads decrease_min`): every item is
decreased once, in random order, to below the current minimum. The binomial
heap must move each key to its root, so its cost grows with log n, while the
Fibonacci and pairing heaps only cut the node.

`check_results.py` flags one point here: the binomial heap at n = 10^7 costs
6.5 us per call against 3.4 us at 3*10^6, more than log n alone predicts. This
is not swapping. The run was repeated (5,968 vs 6,974 ns per call; both rows
are kept and the median is used) and had only 326 page faults. The binomial
heap touches two objects on each of about log n levels per call, so it is hit
hardest when the 3 GB heap no longer fits in fast memory; the Fibonacci and
pairing heaps touch a constant number of nodes and are not affected.

