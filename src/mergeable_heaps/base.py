"""Base class for all mergeable min-heaps."""

from abc import ABC, abstractmethod
from typing import Any


class EmptyHeapError(IndexError):
    """Raised by find_min / extract_min on an empty heap."""


class HeapNode:
    """Handle returned by insert(); pass it back to decrease_key().

    Each heap subclasses this and adds its own link fields (parent, child, ...).
    Only `key` and `value` are part of the public interface.
    """

    __slots__ = ("key", "value")

    def __init__(self, key: Any, value: Any = None) -> None:
        """Input: key (priority, any comparable) and an optional payload value."""
        self.key = key
        self.value = value

    def __repr__(self) -> str:
        return f"{type(self).__name__}(key={self.key!r}, value={self.value!r})"


class MergeableHeap(ABC):
    """Common min-heap interface so every heap can be tested and benchmarked the same way.

    Operations follow CLRS ch. 19 (mergeable heaps): insert, find-min,
    extract-min, union (merge) and decrease-key.
    """

    @abstractmethod
    def insert(self, key: Any, value: Any = None) -> HeapNode:
        """Add an item.

        Input: key (comparable) and optional value. Output: the node handle,
        which is needed later for decrease_key.
        """

    @abstractmethod
    def find_min(self) -> HeapNode:
        """Look at the smallest item without removing it.

        Input: none. Output: node with the minimum key.
        Raises EmptyHeapError if the heap is empty.
        """

    @abstractmethod
    def extract_min(self) -> HeapNode:
        """Remove and return the smallest item.

        Input: none. Output: node with the minimum key.
        Raises EmptyHeapError if the heap is empty.
        """

    @abstractmethod
    def decrease_key(self, node: HeapNode, new_key: Any) -> None:
        """Lower the key of a node already in this heap.

        Input: a handle returned by insert() on this heap, and new_key <= node.key.
        Output: None. Raises ValueError if new_key is larger than the current key.
        """

    @abstractmethod
    def merge(self, other: "MergeableHeap") -> None:
        """Move every item of `other` into this heap (CLRS "union").

        Input: another heap of the same type. Output: None; `other` is left empty.
        Raises TypeError if `other` is a different heap type.
        """

    @abstractmethod
    def __len__(self) -> int:
        """Number of items in the heap."""

    def is_empty(self) -> bool:
        """Input: none. Output: True if the heap has no items."""
        return len(self) == 0

    def _check_decrease(self, node: HeapNode, new_key: Any) -> None:
        """Shared validation for decrease_key.

        Input: node and the requested key. Output: None.
        Raises ValueError if new_key > node.key.
        """
        if new_key > node.key:
            raise ValueError(f"new key {new_key!r} is greater than current key {node.key!r}")

    def _check_same_type(self, other: "MergeableHeap") -> None:
        """Shared validation for merge.

        Input: the heap to merge in. Output: None.
        Raises TypeError if it is not the same heap type as self.
        """
        if type(other) is not type(self):
            raise TypeError(f"cannot merge {type(other).__name__} into {type(self).__name__}")
