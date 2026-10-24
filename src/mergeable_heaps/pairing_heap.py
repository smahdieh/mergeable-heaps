"""Pairing heap (Fredman, Sedgewick, Sleator & Tarjan 1986).

A single heap-ordered multi-way tree. Uses the left-child / right-sibling
representation: each node points to its leftmost child and its next sibling,
plus `prev` (previous sibling, or the parent for a leftmost child) so a node
can be cut out in O(1).

insert, find_min and merge are O(1); extract_min is O(log n) amortized
(two-pass pairing). decrease_key is o(log n) amortized; its exact bound is
open: Omega(log log n) (Fredman 1999) and O(2^(2 sqrt(log log n))) (Pettie 2005).
"""

from typing import Any, Optional

from mergeable_heaps.base import EmptyHeapError, HeapNode, MergeableHeap


class PairingNode(HeapNode):
    """Handle returned by insert(); also the tree node itself."""

    __slots__ = ("child", "sibling", "prev")

    def __init__(self, key: Any, value: Any = None) -> None:
        """Input: key and optional value."""
        super().__init__(key, value)
        self.child: Optional["PairingNode"] = None  # leftmost child
        self.sibling: Optional["PairingNode"] = None  # next sibling to the right
        self.prev: Optional["PairingNode"] = None  # previous sibling, or parent if leftmost


class PairingHeap(MergeableHeap):
    """Min-heap as one multi-way tree; the root is the minimum."""

    def __init__(self) -> None:
        """Create an empty heap."""
        self._root: Optional[PairingNode] = None
        self._size = 0

    def __len__(self) -> int:
        """Number of items in the heap."""
        return self._size

    @staticmethod
    def _meld(a: Optional[PairingNode], b: Optional[PairingNode]) -> Optional[PairingNode]:
        """Link two trees: the root with the larger key becomes the leftmost
        child of the other.

        Input: two tree roots (either may be None; both have no sibling/prev).
        Output: the root of the combined tree. O(1).
        """
        # TODO: if a is None return b; if b is None return a
        # TODO: if b.key < a.key: swap a and b   (a is now the winner)
        # TODO: make b the leftmost child of a:
        #       b.sibling = a.child; if a.child: a.child.prev = b
        #       b.prev = a; a.child = b
        # TODO: return a
        raise NotImplementedError

    def insert(self, key: Any, value: Any = None) -> PairingNode:
        """Add an item as a one-node tree and meld it with the root.

        Input: key and optional value. Output: the node handle. O(1).
        """
        # TODO: node = PairingNode(key, value); self._root = self._meld(self._root, node)
        # TODO: self._size += 1; return node
        raise NotImplementedError

    def find_min(self) -> PairingNode:
        """Input: none. Output: node with the minimum key (the root). O(1)."""
        # TODO: raise EmptyHeapError if empty; else return self._root
        raise NotImplementedError

    def extract_min(self) -> PairingNode:
        """Remove the root and rebuild one tree from its children by two-pass pairing.

        Input: none. Output: node with the minimum key. O(log n) amortized.
        """
        # TODO: raise EmptyHeapError if empty; old = self._root
        # TODO: self._root = self._two_pass(old.child); if root: root.prev = None
        # TODO: self._size -= 1; detach old (child = None); return old
        raise NotImplementedError

    def _two_pass(self, first: Optional[PairingNode]) -> Optional[PairingNode]:
        """Combine a sibling list into one tree.

        Input: the leftmost node of a sibling list. Output: root of the result.
        Pass 1 (left to right): meld siblings in pairs (1st+2nd, 3rd+4th, ...).
        Pass 2 (right to left): meld each pair result into the accumulated tree.
        """
        # TODO: pass 1 with a loop, collecting pair results in a Python list:
        #       a = first; b = a.sibling; next = b.sibling (if b)
        #       detach a and b (sibling = prev = None) BEFORE melding them
        #       pairs.append(self._meld(a, b)); continue from next
        # TODO: pass 2: result = pairs[-1]; for p in reversed(pairs[:-1]):
        #       result = self._meld(p, result)
        # TODO: return result (None if first is None)
        raise NotImplementedError

    def decrease_key(self, node: PairingNode, new_key: Any) -> None:
        """Lower a node's key; if it is not the root, cut its subtree and meld it back.

        Input: node handle from insert(), new_key <= current key.
        Output: None. o(log n) amortized.
        """
        # TODO: self._check_decrease(node, new_key); node.key = new_key
        # TODO: if node is self._root: return
        # TODO: cut node (with its subtree) out of its sibling list:
        #       if node.prev.child is node: node.prev.child = node.sibling   (leftmost child)
        #       else: node.prev.sibling = node.sibling
        #       if node.sibling: node.sibling.prev = node.prev
        #       node.sibling = node.prev = None
        # TODO: self._root = self._meld(self._root, node)
        raise NotImplementedError

    def merge(self, other: "PairingHeap") -> None:
        """Move all items of `other` into this heap by melding the two roots.

        Input: another PairingHeap. Output: None; `other` is emptied. O(1).
        """
        # TODO: self._check_same_type(other)
        # TODO: self._root = self._meld(self._root, other._root); self._size += other._size
        # TODO: reset other (_root = None, _size = 0)
        raise NotImplementedError
