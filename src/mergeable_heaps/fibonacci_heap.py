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
    a sibling list). `mark` is True if the node lost a child since it last
    became a child of another node.
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
        """Join two circular lists into one.

        Input: a node from each list. Output: None. O(1).
        """
        # TODO: connect a <-> b.right ... and b <-> a.right so the two circles
        #       become one (4 pointer updates; save a.right first).
        raise NotImplementedError

    @staticmethod
    def _remove_from_list(x: FibonacciNode) -> None:
        """Unlink x from its circular list and make it a one-node list.

        Input: a node. Output: None. O(1).
        """
        # TODO: x.left.right = x.right; x.right.left = x.left
        # TODO: x.left = x.right = x
        raise NotImplementedError

    def insert(self, key: Any, value: Any = None) -> FibonacciNode:
        """Add a new one-node tree to the root list (no consolidation).

        Input: key and optional value. Output: the node handle. O(1).
        """
        # TODO: node = FibonacciNode(key, value)
        # TODO: if heap empty: self._min = node; else splice node into the root
        #       list and update self._min if node.key < self._min.key
        # TODO: self._size += 1; return node
        raise NotImplementedError

    def find_min(self) -> FibonacciNode:
        """Input: none. Output: node with the minimum key. O(1)."""
        # TODO: raise EmptyHeapError if empty; else return self._min
        raise NotImplementedError

    def extract_min(self) -> FibonacciNode:
        """Remove and return the minimum node, then consolidate the roots.

        Input: none. Output: node with the minimum key. O(log n) amortized.
        """
        # TODO: raise EmptyHeapError if empty; z = self._min
        # TODO: for each child of z: set child.parent = None (the mark can be
        #       cleared too); then splice z's whole child list into the root list.
        # TODO: if z.right is z (z is now the only root): self._min = None
        #       else: self._min = z.right; remove z from the root list;
        #             self._consolidate()
        # TODO: self._size -= 1; detach z (child = None, degree = 0); return z
        raise NotImplementedError

    def _consolidate(self) -> None:
        """Link roots of equal degree until all root degrees are distinct.

        Input: none. Output: None; also recomputes self._min.
        O(D(n) + number of roots) actual time.
        """
        # TODO: degree table A of size floor(log_phi(n)) + 2, all None
        #       (int(math.log(self._size) / _LOG_PHI) + 2 when size > 1).
        # TODO: collect the current roots into a Python list FIRST (the root list
        #       changes while linking, so do not walk it while modifying it).
        # TODO: for each root x:
        #           d = x.degree
        #           while A[d] is not None:
        #               y = A[d]
        #               if y.key < x.key: swap x and y
        #               self._link(y, x)    # y becomes a child of x
        #               A[d] = None; d += 1
        #           A[d] = x
        # TODO: rebuild the root list from the non-None entries of A and set
        #       self._min to the smallest one.
        raise NotImplementedError

    def _link(self, y: FibonacciNode, x: FibonacciNode) -> None:
        """Make root y a child of root x (CLRS FIB-HEAP-LINK).

        Input: two roots with x.key <= y.key. Output: None. O(1).
        """
        # TODO: remove y from the root list
        # TODO: add y to x's child list (or make it x.child if x has none)
        # TODO: y.parent = x; x.degree += 1; y.mark = False
        raise NotImplementedError

    def decrease_key(self, node: FibonacciNode, new_key: Any) -> None:
        """Lower a node's key; cut it out if it breaks heap order.

        Input: node handle from insert(), new_key <= current key.
        Output: None. O(1) amortized.
        """
        # TODO: self._check_decrease(node, new_key); node.key = new_key
        # TODO: y = node.parent
        # TODO: if y and node.key < y.key: self._cut(node, y); self._cascading_cut(y)
        # TODO: if node.key < self._min.key: self._min = node
        raise NotImplementedError

    def _cut(self, x: FibonacciNode, y: FibonacciNode) -> None:
        """Move child x of y to the root list.

        Input: x and its parent y. Output: None. O(1).
        """
        # TODO: if y.child is x: y.child = x.right if x.right is not x else None
        # TODO: remove x from y's child list; y.degree -= 1
        # TODO: splice x into the root list; x.parent = None; x.mark = False
        raise NotImplementedError

    def _cascading_cut(self, y: FibonacciNode) -> None:
        """Walk up from y: cut marked ancestors, mark the first unmarked one.

        Input: a node that just lost a child. Output: None.
        O(1) amortized (each cut pays for itself with the potential of its mark).
        """
        # TODO: write it as a loop, not recursion (deep trees + Python recursion limit):
        #   z = y.parent
        #   while z is not None:
        #       if not y.mark: y.mark = True; break
        #       self._cut(y, z); y = z; z = y.parent
        raise NotImplementedError

    def merge(self, other: "FibonacciHeap") -> None:
        """Move all items of `other` into this heap by splicing root lists.

        Input: another FibonacciHeap. Output: None; `other` is emptied. O(1).
        """
        # TODO: self._check_same_type(other); if other is empty: return
        # TODO: if self is empty: take other's _min; else splice the two root
        #       lists and keep the smaller min
        # TODO: self._size += other._size; reset other (_min = None, _size = 0)
        raise NotImplementedError
