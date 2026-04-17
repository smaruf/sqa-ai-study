"""
Level 5 - Master: Property-Based Testing with Hypothesis
=========================================================
Property-based testing generates hundreds of random inputs automatically,
looking for inputs that break invariants (properties) you specify.

This complements example-based tests: instead of hand-picking inputs,
you describe *properties that must always hold* and let the framework
find edge cases you didn't think of.

Prerequisites:
    pip install pytest hypothesis

Run:
    pytest 02_property_based.py -v --hypothesis-show-statistics
"""

from hypothesis import given, assume, settings, HealthCheck
from hypothesis import strategies as st
import pytest


# ─── System Under Test ────────────────────────────────────────────────────────

def sort_ascending(items: list[int]) -> list[int]:
    """Return a new list sorted in ascending order."""
    return sorted(items)


def encode_base64(data: bytes) -> str:
    import base64
    return base64.b64encode(data).decode()


def decode_base64(encoded: str) -> bytes:
    import base64
    return base64.b64decode(encoded)


class BoundedStack:
    """A stack with a maximum capacity."""

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._capacity = capacity
        self._items: list = []

    def push(self, item) -> None:
        if len(self._items) >= self._capacity:
            raise OverflowError("stack is full")
        self._items.append(item)

    def pop(self):
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self):
        if not self._items:
            raise IndexError("peek from empty stack")
        return self._items[-1]

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def size(self) -> int:
        return len(self._items)


# ─── Properties ───────────────────────────────────────────────────────────────

# Property: sorted list has the same length as the original
@given(st.lists(st.integers()))
def test_sort_preserves_length(items):
    assert len(sort_ascending(items)) == len(items)


# Property: sorted list is actually sorted
@given(st.lists(st.integers()))
def test_sort_output_is_ordered(items):
    result = sort_ascending(items)
    for i in range(len(result) - 1):
        assert result[i] <= result[i + 1]


# Property: sorted list contains the same elements (multiset equality)
@given(st.lists(st.integers()))
def test_sort_preserves_elements(items):
    assert sorted(sort_ascending(items)) == sorted(items)


# Property: sorting is idempotent
@given(st.lists(st.integers()))
def test_sort_is_idempotent(items):
    once  = sort_ascending(items)
    twice = sort_ascending(once)
    assert once == twice


# Property: base64 encode → decode is a round-trip
@given(st.binary())
def test_base64_round_trip(data: bytes):
    assert decode_base64(encode_base64(data)) == data


# Property: base64 output is always valid ASCII
@given(st.binary())
def test_base64_output_is_ascii(data: bytes):
    encoded = encode_base64(data)
    assert encoded.isascii()


# ─── BoundedStack properties ──────────────────────────────────────────────────

@given(
    capacity=st.integers(min_value=1, max_value=100),
    items=st.lists(st.integers(), max_size=100),
)
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_stack_size_never_exceeds_capacity(capacity, items):
    stack = BoundedStack(capacity)
    for item in items:
        if stack.size() < capacity:
            stack.push(item)
    assert stack.size() <= capacity


@given(
    capacity=st.integers(min_value=1, max_value=50),
    items=st.lists(st.integers(), min_size=1, max_size=50),
)
def test_stack_lifo_order(capacity, items):
    """Items are returned in LIFO (last-in, first-out) order."""
    assume(len(items) <= capacity)
    stack = BoundedStack(capacity)
    for item in items:
        stack.push(item)

    popped = []
    while not stack.is_empty():
        popped.append(stack.pop())

    assert popped == list(reversed(items))


@given(st.integers(min_value=1, max_value=20))
def test_empty_stack_raises_on_pop(capacity):
    stack = BoundedStack(capacity)
    with pytest.raises(IndexError):
        stack.pop()


@given(st.integers(min_value=1, max_value=20))
def test_full_stack_raises_on_push(capacity):
    stack = BoundedStack(capacity)
    for i in range(capacity):
        stack.push(i)
    with pytest.raises(OverflowError):
        stack.push(99)
