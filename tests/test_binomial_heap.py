"""Structural tests for BinomialHeap (checks the invariants from CLRS 19.1)."""

import random

import pytest

from mergeable_heaps import BinomialHeap


def roots(heap):
    """Input: a BinomialHeap. Output: list of root tree nodes, in list order."""
    out, x = [], heap._head
    while x is not None:
        out.append(x)
        x = x.sibling
    return out


def children(node):
    """Input: a tree node. Output: list of its children, in list order."""
    out, c = [], node.child
    while c is not None:
        out.append(c)
        c = c.sibling
    return out


def check_tree(node):
    """Check one binomial tree B_k and return its node count (must be 2^k).

    Checks: heap order, parent pointers, entry back pointers, and that the
    children have degrees k-1, k-2, ..., 0 in that order.
    """
    assert node.entry.tree is node
    kids = children(node)
    assert [c.degree for c in kids] == list(range(node.degree - 1, -1, -1))
    count = 1
    for c in kids:
        assert c.parent is node
        assert node.entry.key <= c.entry.key
        count += check_tree(c)
    assert count == 2 ** node.degree
    return count


def check_heap(heap):
    """Check every binomial-heap invariant on the whole heap."""
    rs = roots(heap)
    degrees = [r.degree for r in rs]
    assert degrees == sorted(set(degrees)), "root degrees must be distinct and increasing"
    assert all(r.parent is None for r in rs)
    assert sum(check_tree(r) for r in rs) == len(heap)
    # One tree per 1-bit of n.
    assert len(rs) == bin(len(heap)).count("1")
    if rs:
        assert heap._min.entry.key == min(r.entry.key for r in rs)


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 15, 16, 17, 100, 1023, 1024])
def test_invariants_after_inserts(n):
    heap = BinomialHeap()
    for key in random.Random(n).sample(range(10 * n), n):
        heap.insert(key)
    check_heap(heap)


def test_invariants_after_each_extract():
    heap = BinomialHeap()
    for key in random.Random(0).sample(range(1000), 300):
        heap.insert(key)
    while len(heap):
        heap.extract_min()
        check_heap(heap)


def test_invariants_after_decrease_keys():
    rng = random.Random(1)
    heap = BinomialHeap()
    nodes = [heap.insert(key) for key in rng.sample(range(10_000), 500)]
    for node in rng.sample(nodes, 200):
        heap.decrease_key(node, node.key - rng.randint(0, 20_000))
        check_heap(heap)


def test_invariants_after_merge():
    a, b = BinomialHeap(), BinomialHeap()
    for key in range(13):
        a.insert(key)
    for key in range(100, 111):
        b.insert(key)
    a.merge(b)
    check_heap(a)
    assert len(a) == 24
