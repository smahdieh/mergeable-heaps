"""Unit tests for the dataset generator and loader."""

from collections import deque

import pytest

from mergeable_heaps.dataset import (
    KEY_BITS,
    MAX_DECREASE,
    decrease_ops,
    load_array,
    random_graph,
    random_keys,
    save_array,
    target_index,
    verify_dataset,
    write_manifest,
)


def test_keys_count_and_range():
    keys = random_keys(5_000, seed=1)
    assert len(keys) == 5_000
    assert all(0 <= k < 2 ** KEY_BITS for k in keys)


def test_same_seed_same_output():
    """The dataset is reproducible from its seed."""
    assert random_keys(1_000, seed=1) == random_keys(1_000, seed=1)
    assert random_keys(1_000, seed=1) != random_keys(1_000, seed=2)
    assert decrease_ops(500, seed=3) == decrease_ops(500, seed=3)


def test_smaller_run_is_prefix_of_larger_run():
    """Benchmarks use prefixes, so a short run must equal the start of a long one."""
    assert random_keys(100, seed=7) == random_keys(1_000, seed=7)[:100]


def test_decrease_amounts_in_range():
    targets, amounts = decrease_ops(5_000, seed=1)
    assert len(targets) == len(amounts) == 5_000
    assert all(1 <= a <= MAX_DECREASE for a in amounts)


@pytest.mark.parametrize("n", [1, 2, 7, 1000, 10_000_000])
def test_target_index_stays_in_range(n):
    for raw in (0, 1, 2 ** 31, 2 ** 32 - 1):
        assert 0 <= target_index(raw, n) < n


def test_graph_shape_and_weights():
    src, dst, weight = random_graph(200, avg_degree=5, seed=1, max_weight=50)
    assert len(src) == len(dst) == len(weight) == 1000
    assert all(0 <= v < 200 for v in src) and all(0 <= v < 200 for v in dst)
    assert all(1 <= w <= 50 for w in weight)


def test_graph_is_strongly_connected():
    """The built-in cycle means every node reaches every other node."""
    num_nodes = 300
    src, dst, _ = random_graph(num_nodes, avg_degree=3, seed=2)
    out_edges = [[] for _ in range(num_nodes)]
    in_edges = [[] for _ in range(num_nodes)]
    for u, v in zip(src, dst):
        out_edges[u].append(v)
        in_edges[v].append(u)

    def reachable(adjacency):
        seen, queue = {0}, deque([0])
        while queue:
            for v in adjacency[queue.popleft()]:
                if v not in seen:
                    seen.add(v)
                    queue.append(v)
        return len(seen)

    assert reachable(out_edges) == num_nodes
    assert reachable(in_edges) == num_nodes


def test_graph_rejects_bad_sizes():
    with pytest.raises(ValueError):
        random_graph(1, avg_degree=3, seed=0)


def test_save_and_load_round_trip(tmp_path):
    """Saving then loading gives back the same array; limit reads a prefix."""
    keys = random_keys(1_000, seed=5)
    targets, _ = decrease_ops(1_000, seed=5)
    save_array(keys, tmp_path / "keys.bin")
    save_array(targets, tmp_path / "targets.bin")
    assert load_array(tmp_path / "keys.bin", "i") == keys
    assert load_array(tmp_path / "keys.bin", "i", limit=10) == keys[:10]
    assert load_array(tmp_path / "targets.bin", "I") == targets


def test_manifest_detects_corruption(tmp_path):
    save_array(random_keys(100, seed=1), tmp_path / "keys.bin")
    write_manifest(tmp_path, {"seed": 1}, {"keys.bin": ("i", "test keys")})
    assert verify_dataset(tmp_path) == []

    with (tmp_path / "keys.bin").open("r+b") as f:
        f.write(b"\xff")
    assert verify_dataset(tmp_path) == ["keys.bin: checksum mismatch"]

    (tmp_path / "keys.bin").unlink()
    assert verify_dataset(tmp_path) == ["keys.bin: missing"]
