"""
Level 1 - Basic: pytest Parameterised Tests
============================================
@pytest.mark.parametrize lets you run the same test function with
multiple inputs, reducing duplication and increasing coverage.

Run:
    pytest 03_parametrize.py -v
"""

import pytest
import math


# ─── System Under Test ────────────────────────────────────────────────────────

def is_prime(n: int) -> bool:
    """Return True if n is a prime number."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def fizzbuzz(n: int) -> str:
    """Classic FizzBuzz implementation."""
    if n % 15 == 0:
        return "FizzBuzz"
    if n % 3 == 0:
        return "Fizz"
    if n % 5 == 0:
        return "Buzz"
    return str(n)


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp value to the inclusive range [minimum, maximum]."""
    if minimum > maximum:
        raise ValueError("minimum must not exceed maximum")
    return max(minimum, min(value, maximum))


# ─── Parameterised tests ──────────────────────────────────────────────────────

# Single-parameter: pass a list of values
@pytest.mark.parametrize("n", [2, 3, 5, 7, 11, 13, 97])
def test_is_prime_returns_true_for_known_primes(n):
    assert is_prime(n) is True


@pytest.mark.parametrize("n", [0, 1, 4, 6, 8, 9, 100])
def test_is_prime_returns_false_for_non_primes(n):
    assert is_prime(n) is False


# Multiple parameters: each tuple is (input, expected_output)
@pytest.mark.parametrize("n, expected", [
    (1,  "1"),
    (3,  "Fizz"),
    (5,  "Buzz"),
    (9,  "Fizz"),
    (10, "Buzz"),
    (15, "FizzBuzz"),
    (30, "FizzBuzz"),
    (7,  "7"),
])
def test_fizzbuzz(n, expected):
    assert fizzbuzz(n) == expected


# Parameterised with ids for clearer test names
@pytest.mark.parametrize("value, minimum, maximum, expected", [
    pytest.param(5,   1, 10, 5,  id="within_range"),
    pytest.param(0,   1, 10, 1,  id="below_minimum"),
    pytest.param(15,  1, 10, 10, id="above_maximum"),
    pytest.param(1,   1, 10, 1,  id="at_minimum"),
    pytest.param(10,  1, 10, 10, id="at_maximum"),
])
def test_clamp(value, minimum, maximum, expected):
    assert clamp(value, minimum, maximum) == expected


def test_clamp_invalid_range_raises():
    with pytest.raises(ValueError, match="minimum must not exceed maximum"):
        clamp(5, 10, 1)


# Stacking decorators — all combinations are tested
@pytest.mark.parametrize("a", [1, 2])
@pytest.mark.parametrize("b", [10, 20])
def test_clamp_combinations(a, b):
    """Demonstrates cross-product parameterisation."""
    result = clamp(a, 0, b)
    assert 0 <= result <= b
