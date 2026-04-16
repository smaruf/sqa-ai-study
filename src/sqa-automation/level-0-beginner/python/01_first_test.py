"""
Level 0 - Beginner: First Test in Python
=========================================
This module introduces pytest — Python's most popular test framework.
We use a simple Calculator class as the System Under Test (SUT).

Run:
    pip install pytest
    pytest 01_first_test.py -v
"""


# ─── System Under Test ────────────────────────────────────────────────────────

class Calculator:
    """A simple calculator — our System Under Test (SUT)."""

    def add(self, a: float, b: float) -> float:
        return a + b

    def subtract(self, a: float, b: float) -> float:
        return a - b

    def multiply(self, a: float, b: float) -> float:
        return a * b

    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b


# ─── Tests ────────────────────────────────────────────────────────────────────

# pytest discovers any function whose name starts with "test_"

def test_add_two_positive_numbers():
    calc = Calculator()
    result = calc.add(3, 4)
    assert result == 7


def test_subtract_returns_correct_difference():
    calc = Calculator()
    result = calc.subtract(10, 3)
    assert result == 7


def test_multiply_two_numbers():
    calc = Calculator()
    result = calc.multiply(6, 7)
    assert result == 42


def test_divide_gives_float_result():
    calc = Calculator()
    result = calc.divide(10, 4)
    assert result == 2.5


def test_divide_by_zero_raises_value_error():
    """Verify that dividing by zero raises the expected exception."""
    import pytest
    calc = Calculator()
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calc.divide(5, 0)


def test_add_negative_numbers():
    calc = Calculator()
    assert calc.add(-3, -4) == -7


def test_add_zero_returns_other_number():
    calc = Calculator()
    assert calc.add(0, 42) == 42
