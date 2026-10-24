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
        # TODO: child.parent = parent
        # TODO: child.sibling = parent.child   (push onto the front of the child list)
        # TODO: parent.child = child
        # TODO: parent.degree += 1
        raise NotImplementedError

    @staticmethod
    def _merge_root_lists(a: Optional[_TreeNode], b: Optional[_TreeNode]) -> Optional[_TreeNode]:
        """Merge two root lists into one list sorted by degree (like merge in merge sort).

        Input: heads of two root lists, each sorted by increasing degree.
        Output: head of the merged list (may contain two trees of the same degree).
        """
        # TODO: walk both lists with two pointers, always taking the root with
        #       the smaller degree, and link them through `sibling`.
        # TODO: append whatever is left of the longer list.
        raise NotImplementedError

    def _union_roots(self, other_head: Optional[_TreeNode]) -> None:
        """Combine another root list into this heap (CLRS BINOMIAL-HEAP-UNION).

        Input: head of a root list. Output: None; self._head is the new list,
        with at most one tree per degree. Works like binary addition with carries.
        """
        # TODO: head = _merge_root_lists(self._head, other_head); if None, set and return.
        # TODO: walk with prev, x = head, nxt = x.sibling:
        #   case 1/2: x.degree != nxt.degree, or three roots in a row have the same
        #             degree (nxt.sibling.degree == x.degree) -> just move forward.
        #   case 3:   x.key <= nxt.key -> x.sibling = nxt.sibling; _link(nxt, x).
        #   case 4:   otherwise -> remove x from the list (fix prev or head);
        #             _link(x, nxt); x = nxt.
        #   then nxt = x.sibling.
        # TODO: self._head = head, then recompute self._min (call _update_min).
        raise NotImplementedError

    def _update_min(self) -> None:
        """Scan the root list and point self._min at the smallest key.

        Input: none. Output: None. O(log n) since there are <= log2 n + 1 roots.
        """
        # TODO: walk self._head through `sibling`, keep the root with the smallest entry.key.
        raise NotImplementedError

    def insert(self, key: Any, value: Any = None) -> BinomialEntry:
        """Add an item as a new B_0 tree and union it in.

        Input: key and optional value. Output: the entry handle. O(log n) worst case.
        """
        # TODO: entry = BinomialEntry(key, value); tree = _TreeNode(entry); entry.tree = tree
        # TODO: self._union_roots(tree); self._size += 1; return entry
        raise NotImplementedError

    def find_min(self) -> BinomialEntry:
        """Input: none. Output: entry with the minimum key. O(1)."""
        # TODO: raise EmptyHeapError if empty; else return self._min.entry
        raise NotImplementedError

    def extract_min(self) -> BinomialEntry:
        """Remove and return the minimum entry.

        Input: none. Output: entry with the minimum key. O(log n).
        """
        # TODO: raise EmptyHeapError if empty.
        # TODO: remove self._min from the root list (need its previous root).
        # TODO: reverse its child list (children are in decreasing degree),
        #       set each child's parent to None -> this is a valid root list.
        # TODO: self._union_roots(reversed_children); self._size -= 1
        # TODO: clear the entry's tree pointer and return the entry.
        raise NotImplementedError

    def decrease_key(self, node: BinomialEntry, new_key: Any) -> None:
        """Lower an entry's key and bubble it up toward the root.

        Input: entry handle from insert(), new_key <= current key.
        Output: None. O(log n) because a tree has height <= log2 n.
        """
        # TODO: self._check_decrease(node, new_key); node.key = new_key
        # TODO: y = node.tree; z = y.parent
        # TODO: while z and y.entry.key < z.entry.key:
        #           swap y.entry and z.entry, then fix both entries' .tree back pointers
        #           y = z; z = y.parent
        # TODO: if y is a root and its key < self._min key, update self._min.
        raise NotImplementedError

    def merge(self, other: "BinomialHeap") -> None:
        """Move all items of `other` into this heap.

        Input: another BinomialHeap. Output: None; `other` is emptied. O(log n).
        """
        # TODO: self._check_same_type(other)
        # TODO: self._union_roots(other._head); self._size += other._size
        # TODO: reset other to empty (_head, _min = None, _size = 0)
        raise NotImplementedError
