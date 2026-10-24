"""Structural tests for FibonacciHeap (CLRS 19.2-19.4)."""

import math
import random

from mergeable_heaps import FibonacciHeap

PHI = (1 + math.sqrt(5)) / 2


def circular(start):
    """Input: a node in a circular list. Output: all nodes in the list.

    Also checks that left/right pointers agree.
    """
    out, x = [], start
    while True:
        assert x.right.left is x and x.left.right is x
        out.append(x)
        x = x.right
        if x is start:
            return out


def check_tree(node):
    """Check heap order, parent pointers and degree counts; return subtree size."""
    if node.child is None:
        assert node.degree == 0
        return 1
    kids = circular(node.child)
    assert node.degree == len(kids)
    size = 1
    for c in kids:
        assert c.parent is node
        assert node.key <= c.key
        size += check_tree(c)
    return size


def check_heap(heap):
    """Check every invariant on the whole heap; return the root list."""
    if heap._min is None:
        assert len(heap) == 0
        return []
    rs = circular(heap._min)
    assert all(r.parent is None for r in rs)
    assert heap._min.key == min(r.key for r in rs)
    assert sum(check_tree(r) for r in rs) == len(heap)
    return rs


def max_degree(heap):
    """Largest degree of any node in the heap."""
    best, stack = 0, list(circular(heap._min)) if heap._min else []
    while stack:
        x = stack.pop()
        best = max(best, x.degree)
        if x.child is not None:
            stack.extend(circular(x.child))
    return best


def test_insert_is_lazy():
    heap = FibonacciHeap()
    for key in range(50):
        heap.insert(key)
    rs = check_heap(heap)
    assert len(rs) == 50  # no consolidation until extract_min
    assert all(r.degree == 0 for r in rs)


def test_consolidate_gives_distinct_root_degrees():
    heap = FibonacciHeap()
    for key in random.Random(0).sample(range(1000), 200):
        heap.insert(key)
    heap.extract_min()
    rs = check_heap(heap)
    degrees = [r.degree for r in rs]
    assert len(degrees) == len(set(degrees))
    # 199 nodes -> roots are the binomial trees of the 1-bits of 199.
    assert sorted(2 ** d for d in degrees) == [1, 2, 4, 64, 128]


def test_invariants_after_each_extract():
    heap = FibonacciHeap()
    for key in random.Random(1).sample(range(1000), 300):
        heap.insert(key)
    while len(heap):
        heap.extract_min()
        check_heap(heap)


def test_degree_bound_holds_under_decrease_keys():
    """Max degree must stay <= log_phi(n) (CLRS Cor. 19.5), even with many cuts."""
    rng = random.Random(2)
    heap = FibonacciHeap()
    nodes = [heap.insert(key) for key in range(5000)]
    alive = set(nodes)
    for step in range(3000):
        if step % 3 == 0:
            alive.discard(heap.extract_min())
        else:
            node = rng.choice(nodes)
            if node in alive:
                heap.decrease_key(node, node.key - rng.randint(1, 100))
        if step % 250 == 0:
            check_heap(heap)
            assert max_degree(heap) <= math.log(len(heap), PHI)


def test_cut_and_cascading_cut():
    """Build one tree, then check that decrease_key cuts nodes and marks parents."""
    heap = FibonacciHeap()
    nodes = [heap.insert(key) for key in range(17)]
    heap.extract_min()  # 16 nodes -> a single tree of degree 4 rooted at key 1
    root = heap._min
    assert root.key == 1 and root.degree == 4

    # Pick a grandchild g (parent p, grandparent root) and a sibling s of g.
    p = next(c for c in circular(root.child) if c.degree >= 2)
    g, s = circular(p.child)[:2]

    heap.decrease_key(g, -10)
    assert g.parent is None  # cut to the root list
    assert p.mark  # p lost its first child -> marked
    assert not root.mark

    heap.decrease_key(s, -20)  # p loses a second child -> cascading cut of p
    assert p.parent is None and not p.mark
    assert heap._min is s
    check_heap(heap)


def test_decrease_key_without_violation_does_not_cut():
    heap = FibonacciHeap()
    nodes = [heap.insert(key) for key in range(0, 80, 10)]
    heap.extract_min()
    child = next(n for n in nodes[1:] if n.parent is not None)
    parent = child.parent
    heap.decrease_key(child, parent.key + 1)  # still >= parent key
    assert child.parent is parent
    assert not parent.mark
