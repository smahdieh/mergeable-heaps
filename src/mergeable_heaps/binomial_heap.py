"""Binomial heap (Vuillemin 1978; CLRS 2nd ed. ch. 19).

A forest of binomial trees B_0, B_1, ... with at most one tree of each degree.
B_k has 2^k nodes, so a heap of n items has at most floor(log2 n) + 1 trees
(one per 1-bit of n).

Handle design: decrease_key bubbles a key up by swapping it with its parent.
If the tree nodes themselves were the handles, a swap would leave the user's
handle pointing at the wrong item. So the handle (BinomialEntry) is kept
separate from the tree position (_TreeNode): a swap exchanges the entries of
two tree nodes and fixes their back pointers, and every handle stays valid.
"""

from typing import Any, Optional

from mergeable_heaps.base import EmptyHeapError, HeapNode, MergeableHeap


class BinomialEntry(HeapNode):
    """Handle returned by insert(); `tree` points to its current tree node."""

    __slots__ = ("tree",)

    def __init__(self, key: Any, value: Any = None) -> None:
        """Input: key and optional value."""
        super().__init__(key, value)
        self.tree: Optional["_TreeNode"] = None


class _TreeNode:
    """A position in a binomial tree.

    Children are a singly linked list through `sibling`, ordered by
    decreasing degree (CLRS layout). Roots are also linked through `sibling`,
    ordered by increasing degree.
    """

    __slots__ = ("entry", "parent", "child", "sibling", "degree")

    def __init__(self, entry: BinomialEntry) -> None:
        """Input: the entry stored at this position."""
        self.entry = entry
        self.parent: Optional["_TreeNode"] = None
        self.child: Optional["_TreeNode"] = None
        self.sibling: Optional["_TreeNode"] = None
        self.degree = 0


class BinomialHeap(MergeableHeap):
    """Min-heap as a list of binomial trees, roots sorted by degree.

    insert, extract_min, decrease_key and merge are O(log n) worst case;
    find_min is O(1) because a pointer to the minimum root is kept.
    """

    def __init__(self) -> None:
        """Create an empty heap."""
        self._head: Optional[_TreeNode] = None  # first root (smallest degree)
        self._min: Optional[_TreeNode] = None  # root with the smallest key
        self._size = 0

    def __len__(self) -> int:
        """Number of items in the heap."""
        return self._size

    @staticmethod
    def _link(child: _TreeNode, parent: _TreeNode) -> None:
        """Make `child` the leftmost child of `parent` (both roots of degree k).

        Input: two roots of equal degree, parent.entry.key <= child.entry.key.
        Output: None; parent becomes the root of a tree of degree k + 1. O(1).
        """
        child.parent = parent
        child.sibling = parent.child
        parent.child = child
        parent.degree += 1

    @staticmethod
    def _merge_root_lists(a: Optional[_TreeNode], b: Optional[_TreeNode]) -> Optional[_TreeNode]:
        """Merge two root lists into one list sorted by degree (like merge in merge sort).

        Input: heads of two root lists, each sorted by increasing degree.
        Output: head of the merged list (may contain two trees of the same degree).
        """
        if a is None:
            return b
        if b is None:
            return a
        if a.degree <= b.degree:
            head, a = a, a.sibling
        else:
            head, b = b, b.sibling
        tail = head
        while a is not None and b is not None:
            if a.degree <= b.degree:
                tail.sibling, a = a, a.sibling
            else:
                tail.sibling, b = b, b.sibling
            tail = tail.sibling
        tail.sibling = a if a is not None else b
        return head

    def _union_roots(self, other_head: Optional[_TreeNode]) -> None:
        """Combine another root list into this heap (CLRS BINOMIAL-HEAP-UNION).

        Input: head of a root list. Output: None; self._head is the new list,
        with at most one tree per degree. Works like binary addition with carries.
        """
        head = self._merge_root_lists(self._head, other_head)
        self._head = head
        if head is None:
            self._min = None
            return

        prev = None
        x = head
        nxt = x.sibling
        while nxt is not None:
            if x.degree != nxt.degree or (
                nxt.sibling is not None and nxt.sibling.degree == x.degree
            ):
                # Cases 1 and 2: nothing to link here yet, move forward.
                prev, x = x, nxt
            elif x.entry.key <= nxt.entry.key:
                # Case 3: x stays a root, nxt becomes its child.
                x.sibling = nxt.sibling
                self._link(nxt, x)
            else:
                # Case 4: nxt stays a root, x becomes its child.
                if prev is None:
                    head = nxt
                else:
                    prev.sibling = nxt
                self._link(x, nxt)
                x = nxt
            nxt = x.sibling

        self._head = head
        self._update_min()

    def _update_min(self) -> None:
        """Scan the root list and point self._min at the smallest key.

        Input: none. Output: None. O(log n) since there are <= log2 n + 1 roots.
        """
        best = self._head
        x = best.sibling if best is not None else None
        while x is not None:
            if x.entry.key < best.entry.key:
                best = x
            x = x.sibling
        self._min = best

    def insert(self, key: Any, value: Any = None) -> BinomialEntry:
        """Add an item as a new B_0 tree and union it in.

        Input: key and optional value. Output: the entry handle. O(log n) worst case.
        """
        entry = BinomialEntry(key, value)
        tree = _TreeNode(entry)
        entry.tree = tree
        self._union_roots(tree)
        self._size += 1
        return entry

    def find_min(self) -> BinomialEntry:
        """Input: none. Output: entry with the minimum key. O(1)."""
        if self._min is None:
            raise EmptyHeapError("find_min on an empty heap")
        return self._min.entry

    def extract_min(self) -> BinomialEntry:
        """Remove and return the minimum entry.

        Input: none. Output: entry with the minimum key. O(log n).
        """
        min_root = self._min
        if min_root is None:
            raise EmptyHeapError("extract_min on an empty heap")

        # Unlink min_root from the root list.
        prev = None
        x = self._head
        while x is not min_root:
            prev, x = x, x.sibling
        if prev is None:
            self._head = min_root.sibling
        else:
            prev.sibling = min_root.sibling

        # Its children are in decreasing degree; reversed they form a valid root list.
        reversed_children = None
        child = min_root.child
        while child is not None:
            nxt = child.sibling
            child.sibling = reversed_children
            child.parent = None
            reversed_children = child
            child = nxt

        self._union_roots(reversed_children)
        self._size -= 1

        entry = min_root.entry
        entry.tree = None
        min_root.child = min_root.sibling = None
        return entry

    def decrease_key(self, node: BinomialEntry, new_key: Any) -> None:
        """Lower an entry's key and bubble it up toward the root.

        Input: entry handle from insert(), new_key <= current key.
        Output: None. O(log n) because a tree has height <= log2 n.
        """
        self._check_decrease(node, new_key)
        node.key = new_key
        y = node.tree
        z = y.parent
        while z is not None and y.entry.key < z.entry.key:
            # Swap the entries (not the tree nodes), then fix the back pointers.
            y_entry, z_entry = y.entry, z.entry
            y.entry, z.entry = z_entry, y_entry
            z_entry.tree = y
            y_entry.tree = z
            y = z
            z = y.parent
        if z is None and y.entry.key < self._min.entry.key:
            self._min = y

    def merge(self, other: "BinomialHeap") -> None:
        """Move all items of `other` into this heap.

        Input: another BinomialHeap. Output: None; `other` is emptied. O(log n).
        """
        self._check_same_type(other)
        if other is self:
            return
        self._union_roots(other._head)
        self._size += other._size
        other._head = other._min = None
        other._size = 0
