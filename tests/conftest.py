"""Shared pytest fixtures."""

import pytest

from mergeable_heaps import BinomialHeap, FibonacciHeap, PairingHeap

HEAP_CLASSES = [BinomialHeap, FibonacciHeap, PairingHeap]


@pytest.fixture(params=HEAP_CLASSES, ids=lambda cls: cls.__name__)
def heap_cls(request):
    """Runs a test once for each heap class."""
    return request.param
