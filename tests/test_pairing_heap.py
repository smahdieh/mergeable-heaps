"""Structural tests for PairingHeap."""

import random

from mergeable_heaps import PairingHeap


def check_tree(node):
    """Check heap order and prev pointers below `node`; return subtree size."""
    size = 1
    prev, c = node, node.child
    while c is not None:
        assert c.prev is prev  # parent for the leftmost child, else left sibling
        assert node.key <= c.key
        size += check_tree(c)
        prev, c = c, c.sibling
    return size


def check_heap(heap):
    """Check every invariant on the whole heap."""
    root = heap._root
    if root is None:
        assert len(heap) == 0
        return
    assert root.prev is None and root.sibling is None
    assert check_tree(root) == len(heap)


def root_children(heap):
    """Number of children of the root."""
    count, c = 0, heap._root.child
    while c is not None:
        count, c = count + 1, c.sibling
    return count


def test_inserts_hang_off_the_root():
    heap = PairingHeap()
    heap.insert(0)
    for key in range(1, 20):
        heap.insert(key)
    check_heap(heap)
    assert root_children(heap) == 19  # each larger insert becomes a child of the root


def test_two_pass_reduces_root_degree():
    heap = PairingHeap()
    for key in range(1025):
        heap.insert(key)
    heap.extract_min()
    check_heap(heap)
    # Pairing halves the 1024 children, and pass 2 links them into one chain
    # under the new root, so the root keeps about half of them as children.
    assert root_children(heap) <= 512


def test_invariants_after_each_extract():
    heap = PairingHeap()
    for key in random.Random(0).sample(range(1000), 300):
        heap.insert(key)
    while len(heap):
        heap.extract_min()
        check_heap(heap)


def test_invariants_after_decrease_keys():
    rng = random.Random(1)
    heap = PairingHeap()
    nodes = [heap.insert(key) for key in rng.sample(range(10_000), 500)]
    heap.extract_min()
    for node in rng.sample(nodes, 200):
        if node.prev is None and node is not heap._root:
            continue  # already extracted
        heap.decrease_key(node, node.key - rng.randint(0, 20_000))
        check_heap(heap)


def test_decrease_key_cuts_leftmost_and_middle_children():
    heap = PairingHeap()
    root = heap.insert(0)
    kids = [heap.insert(key) for key in (10, 20, 30)]  # child list: 30, 20, 10
    assert root.child is kids[2]

    heap.decrease_key(kids[2], 5)  # leftmost child
    check_heap(heap)
    heap.decrease_key(kids[1], 4)  # middle child
    check_heap(heap)
    assert [heap.extract_min().key for _ in range(4)] == [0, 4, 5, 10]


def test_long_sibling_list_does_not_hit_recursion_limit():
    heap = PairingHeap()
    for key in range(200_000):
        heap.insert(key)
    heap.extract_min()  # two-pass over 199,999 siblings
    assert heap.find_min().key == 1
