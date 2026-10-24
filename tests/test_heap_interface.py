"""Behaviour tests that every MergeableHeap must pass (run once per heap class)."""

import random

import pytest

from mergeable_heaps import (
    BinomialHeap,
    EmptyHeapError,
    FibonacciHeap,
    MergeableHeap,
    PairingHeap,
)

ALL_HEAPS = (BinomialHeap, FibonacciHeap, PairingHeap)


def drain(heap):
    """Input: a heap. Output: all keys in extraction order (empties the heap)."""
    return [heap.extract_min().key for _ in range(len(heap))]


# ---- empty heap ----------------------------------------------------------

def test_new_heap_is_empty(heap_cls):
    heap = heap_cls()
    assert isinstance(heap, MergeableHeap)
    assert len(heap) == 0
    assert heap.is_empty()


def test_find_min_on_empty_raises(heap_cls):
    with pytest.raises(EmptyHeapError):
        heap_cls().find_min()


def test_extract_min_on_empty_raises(heap_cls):
    with pytest.raises(EmptyHeapError):
        heap_cls().extract_min()


def test_empty_heap_error_is_index_error():
    assert issubclass(EmptyHeapError, IndexError)


# ---- insert / find_min / extract_min -------------------------------------

def test_single_item(heap_cls):
    heap = heap_cls()
    node = heap.insert(7, "seven")
    assert heap.find_min() is node
    assert len(heap) == 1
    assert heap.extract_min() is node
    assert heap.is_empty()


def test_find_min_does_not_remove(heap_cls):
    heap = heap_cls()
    for key in (5, 3, 8):
        heap.insert(key)
    assert heap.find_min().key == 3
    assert heap.find_min().key == 3
    assert len(heap) == 3


def test_values_travel_with_keys(heap_cls):
    heap = heap_cls()
    for key in (4, 1, 3, 2):
        heap.insert(key, f"v{key}")
    assert [heap.extract_min().value for _ in range(4)] == ["v1", "v2", "v3", "v4"]


@pytest.mark.parametrize("n", [1, 2, 3, 7, 8, 9, 100, 1000])
def test_heapsort_random(heap_cls, n):
    rng = random.Random(n)
    keys = [rng.randint(-10**6, 10**6) for _ in range(n)]
    heap = heap_cls()
    for key in keys:
        heap.insert(key)
    assert drain(heap) == sorted(keys)


@pytest.mark.parametrize("order", ["ascending", "descending"])
def test_heapsort_sorted_inputs(heap_cls, order):
    keys = list(range(2000))
    if order == "descending":
        keys.reverse()
    heap = heap_cls()
    for key in keys:
        heap.insert(key)
    assert drain(heap) == sorted(keys)


def test_duplicate_keys(heap_cls):
    heap = heap_cls()
    keys = [5, 1, 5, 1, 5, 3, 3]
    for key in keys:
        heap.insert(key)
    assert drain(heap) == sorted(keys)


def test_float_and_tuple_keys(heap_cls):
    heap = heap_cls()
    for key in (2.5, -1.0, 0.0):
        heap.insert(key)
    assert drain(heap) == [-1.0, 0.0, 2.5]
    heap = heap_cls()
    for key in ((2, "b"), (1, "z"), (2, "a")):
        heap.insert(key)
    assert drain(heap) == [(1, "z"), (2, "a"), (2, "b")]


def test_interleaved_insert_and_extract(heap_cls):
    heap = heap_cls()
    heap.insert(10)
    heap.insert(4)
    assert heap.extract_min().key == 4
    heap.insert(1)
    heap.insert(12)
    assert heap.extract_min().key == 1
    assert heap.extract_min().key == 10
    assert heap.extract_min().key == 12
    assert heap.is_empty()


# ---- decrease_key --------------------------------------------------------

def test_decrease_key_becomes_new_min(heap_cls):
    heap = heap_cls()
    nodes = [heap.insert(key) for key in range(10, 20)]
    heap.decrease_key(nodes[7], 0)
    assert heap.find_min() is nodes[7]
    assert heap.find_min().key == 0


def test_decrease_key_after_extract_builds_trees(heap_cls):
    # Extracting first forces real trees (Fibonacci consolidates, Pairing pairs),
    # so the decreased node is an inner node and must be cut / bubbled up.
    heap = heap_cls()
    nodes = [heap.insert(key) for key in range(100)]
    heap.extract_min()
    heap.decrease_key(nodes[99], -1)
    heap.decrease_key(nodes[50], -2)
    assert drain(heap) == [-2, -1] + [k for k in range(1, 99) if k != 50]


def test_decrease_key_to_equal_key_is_allowed(heap_cls):
    heap = heap_cls()
    node = heap.insert(5)
    heap.insert(6)
    heap.decrease_key(node, 5)
    assert heap.find_min() is node


def test_decrease_key_of_root(heap_cls):
    heap = heap_cls()
    node = heap.insert(1)
    heap.insert(2)
    heap.decrease_key(node, -5)
    assert heap.extract_min() is node
    assert heap.extract_min().key == 2


def test_decrease_key_rejects_larger_key(heap_cls):
    heap = heap_cls()
    node = heap.insert(5)
    with pytest.raises(ValueError):
        heap.decrease_key(node, 6)
    assert node.key == 5  # unchanged


def test_handles_stay_valid_after_many_decreases(heap_cls):
    # Binomial swaps entries while bubbling up; handles must still point at their own item.
    heap = heap_cls()
    nodes = [heap.insert(key, key) for key in range(500)]
    heap.extract_min()
    for node in nodes[1:]:
        heap.decrease_key(node, node.key - 1000)
    for node in nodes[1:]:
        assert node.key == node.value - 1000
    extracted = [heap.extract_min() for _ in range(len(heap))]
    assert [n.value for n in extracted] == list(range(1, 500))


# ---- merge ---------------------------------------------------------------

def test_merge_two_heaps(heap_cls):
    a, b = heap_cls(), heap_cls()
    for key in (5, 1, 9):
        a.insert(key)
    for key in (4, 0, 7, 2):
        b.insert(key)
    a.merge(b)
    assert len(a) == 7
    assert b.is_empty()
    assert drain(a) == [0, 1, 2, 4, 5, 7, 9]


def test_merge_with_empty(heap_cls):
    a, b = heap_cls(), heap_cls()
    a.insert(3)
    a.merge(b)
    assert drain(a) == [3]

    a, b = heap_cls(), heap_cls()
    b.insert(3)
    a.merge(b)
    assert drain(a) == [3]
    assert b.is_empty()


def test_merged_heap_supports_decrease_key(heap_cls):
    a, b = heap_cls(), heap_cls()
    for key in range(10):
        a.insert(key)
    nodes = [b.insert(key) for key in range(10, 20)]
    a.merge(b)
    a.extract_min()
    a.decrease_key(nodes[5], -1)
    assert a.find_min() is nodes[5]


def test_emptied_heap_is_reusable(heap_cls):
    a, b = heap_cls(), heap_cls()
    b.insert(1)
    a.merge(b)
    b.insert(42)
    assert drain(b) == [42]


def test_merge_with_itself_is_noop(heap_cls):
    heap = heap_cls()
    heap.insert(1)
    heap.insert(2)
    heap.merge(heap)
    assert drain(heap) == [1, 2]


def test_merge_different_types_raises(heap_cls):
    other_cls = next(cls for cls in ALL_HEAPS if cls is not heap_cls)
    with pytest.raises(TypeError):
        heap_cls().merge(other_cls())


# ---- randomized check against a brute-force reference --------------------

@pytest.mark.parametrize("seed", range(10))
def test_random_operations_match_reference(heap_cls, seed):
    """Random inserts / extracts / decrease-keys / merges, checked after every step."""
    rng = random.Random(seed)
    heaps = [heap_cls(), heap_cls()]
    contents = [[], []]  # reference: list of live handles per heap
    for _ in range(3000):
        i = rng.randrange(2)
        heap, live = heaps[i], contents[i]
        op = rng.random()
        if op < 0.45:
            live.append(heap.insert(rng.randint(-1000, 1000)))
        elif op < 0.70 and live:
            expected = min(node.key for node in live)
            got = heap.extract_min()
            assert got.key == expected
            live.remove(got)
        elif op < 0.95 and live:
            node = rng.choice(live)
            heap.decrease_key(node, node.key - rng.randint(0, 500))
        elif op >= 0.95:
            heap.merge(heaps[1 - i])
            live.extend(contents[1 - i])
            contents[1 - i].clear()
        assert len(heap) == len(live)
        if live:
            assert heap.find_min().key == min(node.key for node in live)
    for heap, live in zip(heaps, contents):
        assert drain(heap) == sorted(node.key for node in live)
