"""
Level 1 - Basic: Rich Assertions in pytest
==========================================
pytest's assert statement rewrites assertions at collection time so that
failure messages show detailed context — no need for a special assertion
library in most cases.

Run:
    pytest 02_assertions.py -v
"""

import math
import pytest


# ─── System Under Test ────────────────────────────────────────────────────────

class Vector:
    """A 2D vector with basic operations."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def magnitude(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def normalise(self) -> "Vector":
        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Cannot normalise the zero vector")
        return Vector(self.x / mag, self.y / mag)

    def dot(self, other: "Vector") -> float:
        return self.x * other.x + self.y * other.y

    def __add__(self, other: "Vector") -> "Vector":
        return Vector(self.x + other.x, self.y + other.y)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented
        return math.isclose(self.x, other.x) and math.isclose(self.y, other.y)

    def __repr__(self):
        return f"Vector({self.x}, {self.y})"


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestVectorMagnitude:

    def test_unit_vector_has_magnitude_one(self):
        v = Vector(1, 0)
        assert v.magnitude() == 1.0

    def test_magnitude_of_3_4_is_5(self):
        v = Vector(3, 4)
        assert v.magnitude() == 5.0

    def test_magnitude_is_always_non_negative(self):
        v = Vector(-3, -4)
        assert v.magnitude() >= 0

    def test_magnitude_with_float_precision(self):
        """Use pytest.approx for floating-point comparisons."""
        v = Vector(1, 1)
        assert v.magnitude() == pytest.approx(math.sqrt(2), rel=1e-6)


class TestVectorNormalise:

    def test_normalised_vector_has_unit_magnitude(self):
        v = Vector(3, 4)
        n = v.normalise()
        assert n.magnitude() == pytest.approx(1.0, abs=1e-9)

    def test_normalise_zero_vector_raises(self):
        v = Vector(0, 0)
        with pytest.raises(ValueError, match="Cannot normalise the zero vector"):
            v.normalise()

    def test_normalised_direction_is_preserved(self):
        v = Vector(6, 8)
        n = v.normalise()
        # After normalisation the direction (ratio x:y) stays the same
        assert n.x == pytest.approx(0.6)
        assert n.y == pytest.approx(0.8)


class TestVectorDot:

    def test_perpendicular_vectors_have_zero_dot_product(self):
        """(1,0) · (0,1) should be 0 — they are perpendicular."""
        v1 = Vector(1, 0)
        v2 = Vector(0, 1)
        assert v1.dot(v2) == pytest.approx(0.0, abs=1e-9)

    def test_parallel_unit_vectors_have_dot_product_of_one(self):
        v1 = Vector(1, 0)
        v2 = Vector(1, 0)
        assert v1.dot(v2) == pytest.approx(1.0)

    def test_dot_product_is_commutative(self):
        v1 = Vector(2, 3)
        v2 = Vector(4, 5)
        assert v1.dot(v2) == pytest.approx(v2.dot(v1))


class TestVectorAddition:

    def test_add_two_vectors(self):
        v1 = Vector(1, 2)
        v2 = Vector(3, 4)
        assert v1 + v2 == Vector(4, 6)

    def test_adding_zero_vector_returns_same_vector(self):
        v = Vector(3, 4)
        zero = Vector(0, 0)
        assert v + zero == v

    def test_addition_is_commutative(self):
        v1 = Vector(1, 2)
        v2 = Vector(3, 4)
        assert v1 + v2 == v2 + v1


class TestAssertionMessages:
    """Show how pytest generates useful failure messages."""

    def test_custom_failure_message(self):
        items = [1, 2, 3]
        assert len(items) == 3, f"Expected 3 items, got {len(items)}"

    def test_multiple_assertions_in_sequence(self):
        user = {"name": "Alice", "age": 30, "email": "alice@example.com"}
        assert "name"  in user
        assert "email" in user
        assert user["age"] >= 18

    def test_assert_raises_captures_exception(self):
        with pytest.raises(ZeroDivisionError) as exc_info:
            _ = 1 / 0
        assert "division by zero" in str(exc_info.value)
