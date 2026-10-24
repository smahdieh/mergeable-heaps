"""Fibonacci heap (Fredman & Tarjan 1987; CLRS 3rd ed. ch. 19).

A lazy collection of heap-ordered trees. Roots are kept in a circular doubly
linked list, and so are the children of every node. Work is postponed until
extract_min, which consolidates the roots so that no two have the same degree.

Amortized costs (potential = number of roots + 2 * number of marked nodes):
insert, find_min, merge and decrease_key are O(1); extract_min is O(log n).
"""

import math
from typing import Any, Optional

from mergeable_heaps.base import EmptyHeapError, HeapNode, MergeableHeap

# Max degree D(n) <= log_phi(n), with phi the golden ratio (CLRS Cor. 19.5).
_LOG_PHI = math.log((1 + math.sqrt(5)) / 2)


class FibonacciNode(HeapNode):
    """Handle returned by insert(); also the tree node itself.

    left/right link the node into a circular doubly linked list (root list or
    a sibling list); both are set to None when the node is extracted, which is
    how decrease_key recognises a node that is no longer in the heap. `mark` is
    True if the node lost a child since it last became a child of another node.
    """

    __slots__ = ("parent", "child", "left", "right", "degree", "mark")

    def __init__(self, key: Any, value: Any = None) -> None:
        """Input: key and optional value. Starts as a one-node circular list."""
        super().__init__(key, value)
        self.parent: Optional["FibonacciNode"] = None
        self.child: Optional["FibonacciNode"] = None
        self.left: "FibonacciNode" = self
        self.right: "FibonacciNode" = self
        self.degree = 0
        self.mark = False


class FibonacciHeap(MergeableHeap):
    """Min-heap as a lazy forest; `_min` points into the root list."""

    def __init__(self) -> None:
        """Create an empty heap."""
        self._min: Optional[FibonacciNode] = None
        self._size = 0

    def __len__(self) -> int:
        """Number of items in the heap."""
        return self._size

    @staticmethod
    def _splice(a: FibonacciNode, b: FibonacciNode) -> None:
        """Join two circular lists into one: a -> b ... b.left -> a.right ... -> a.

        Input: a node from each list. Output: None. O(1).
        """
        a_right = a.right
        b_left = b.left
        a.right = b
        b.left = a
        b_left.right = a_right
        a_right.left = b_left

    @staticmethod
    def _remove_from_list(x: FibonacciNode) -> None:
        """Unlink x from its circular list and make it a one-node list.

        Input: a node. Output: None. O(1).
        """
        x.left.right = x.right
        x.right.left = x.left
        x.left = x.right = x

    def insert(self, key: Any, value: Any = None) -> FibonacciNode:
        """Add a new one-node tree to the root list (no consolidation).

        Input: key and optional value. Output: the node handle. O(1).
        """
        node = FibonacciNode(key, value)
        if self._min is None:
            self._min = node
        else:
            self._splice(self._min, node)
            if node.key < self._min.key:
                self._min = node
        self._size += 1
        return node

    def find_min(self) -> FibonacciNode:
        """Input: none. Output: node with the minimum key. O(1)."""
        if self._min is None:
            raise EmptyHeapError("find_min on an empty heap")
        return self._min

    def extract_min(self) -> FibonacciNode:
        """Remove and return the minimum node, then consolidate the roots.

        Input: none. Output: node with the minimum key. O(log n) amortized.
        """
        z = self._min
        if z is None:
            raise EmptyHeapError("extract_min on an empty heap")

        # Promote all children of z to the root list.
        first_child = z.child
        if first_child is not None:
            x = first_child
            while True:
                x.parent = None
                x.mark = False
                x = x.right
                if x is first_child:
                    break
            self._splice(z, first_child)
            z.child = None

        if z.right is z:  # z was the only root and had no children
            self._min = None
        else:
            self._min = z.right
            self._remove_from_list(z)
            self._consolidate()

        self._size -= 1
        z.degree = 0
        z.left = z.right = None  # a node in the heap always has list links
        return z

    def _consolidate(self) -> None:
        """Link roots of equal degree until all root degrees are distinct.

        Input: none. Output: None; also recomputes self._min.
        O(D(n) + number of roots) actual time.
        """
        # Size is still counting the extracted node here, so this is an upper bound.
        max_degree = int(math.log(self._size) / _LOG_PHI) + 2 if self._size > 1 else 2
        by_degree: list = [None] * (max_degree + 1)

        # Copy the roots first: linking changes the root list while we iterate.
        roots = []
        start = x = self._min
        while True:
            roots.append(x)
            x = x.right
            if x is start:
                break

        for x in roots:
            d = x.degree
            while by_degree[d] is not None:
                y = by_degree[d]
                if y.key < x.key:
                    x, y = y, x
                self._link(y, x)
                by_degree[d] = None
                d += 1
            by_degree[d] = x

        # The losers were removed by _link, so the root list is exactly the
        # trees left in by_degree; only the min pointer needs recomputing.
        self._min = None
        for x in by_degree:
            if x is not None and (self._min is None or x.key < self._min.key):
                self._min = x

    def _link(self, y: FibonacciNode, x: FibonacciNode) -> None:
        """Make root y a child of root x (CLRS FIB-HEAP-LINK).

        Input: two roots with x.key <= y.key. Output: None. O(1).
        """
        self._remove_from_list(y)
        if x.child is None:
            x.child = y
        else:
            self._splice(x.child, y)
        y.parent = x
        x.degree += 1
        y.mark = False

    def decrease_key(self, node: FibonacciNode, new_key: Any) -> None:
        """Lower a node's key; cut it out if it breaks heap order.

        Input: node handle from insert(), new_key <= current key.
        Output: None. O(1) amortized.
        Raises ValueError if the node was already extracted.
        """
        if node.left is None:
            raise self._not_in_heap(node)
        self._check_decrease(node, new_key)
        node.key = new_key
        parent = node.parent
        if parent is not None and node.key < parent.key:
            self._cut(node, parent)
            self._cascading_cut(parent)
        if node.key < self._min.key:
            self._min = node

    def _cut(self, x: FibonacciNode, y: FibonacciNode) -> None:
        """Move child x of y to the root list.

        Input: x and its parent y. Output: None. O(1).
        """
        if x.right is x:  # x was the only child
            y.child = None
        elif y.child is x:
            y.child = x.right
        self._remove_from_list(x)
        y.degree -= 1
        self._splice(self._min, x)
        x.parent = None
        x.mark = False

    def _cascading_cut(self, y: FibonacciNode) -> None:
        """Walk up from y: cut marked ancestors, mark the first unmarked one.

        Input: a node that just lost a child. Output: None.
        O(1) amortized (each cut pays for itself with the potential of its mark).
        Written as a loop instead of CLRS's recursion to avoid the recursion limit.
        """
        z = y.parent
        while z is not None:
            if not y.mark:
                y.mark = True
                return
            self._cut(y, z)
            y = z
            z = y.parent

    def merge(self, other: "FibonacciHeap") -> None:
        """Move all items of `other` into this heap by splicing root lists.

        Input: another FibonacciHeap. Output: None; `other` is emptied. O(1).
        """
        self._check_same_type(other)
        if other is self or other._min is None:
            return
        if self._min is None:
            self._min = other._min
        else:
            self._splice(self._min, other._min)
            if other._min.key < self._min.key:
                self._min = other._min
        self._size += other._size
        other._min = None
        other._size = 0
