"""
Level 5 - Master: Mutation-Resistant Tests in Python
=====================================================
Mutation testing introduces small artificial bugs (mutants) into the source
code, then checks whether your tests detect (kill) each mutant.

A test suite that doesn't kill most mutants is not verifying much — it has
high coverage but low confidence.

This file shows patterns that make tests more mutation-resistant:

1. Test boundary conditions (>, >=, ==, !=)
2. Verify exact return values, not just truthiness
3. Test both sides of every branch
4. Assert the *absence* of side effects as well as their presence

Run tests:
    pytest 01_mutation_testing.py -v

Run mutation testing:
    pip install mutmut
    mutmut run --paths-to-mutate 01_mutation_testing.py
    mutmut results
"""

import pytest


# ─── System Under Test ────────────────────────────────────────────────────────

def discount_rate(years_as_customer: int) -> float:
    """
    Return a discount rate based on customer loyalty.
    0–1 years  → 0%
    2–4 years  → 5%
    5–9 years  → 10%
    10+ years  → 15%
    """
    if years_as_customer < 0:
        raise ValueError("years_as_customer must not be negative")
    if years_as_customer < 2:
        return 0.0
    if years_as_customer < 5:
        return 0.05
    if years_as_customer < 10:
        return 0.10
    return 0.15


def apply_discount(price: float, rate: float) -> float:
    """Apply a discount rate to a price."""
    if price < 0:
        raise ValueError("price must not be negative")
    if not 0.0 <= rate <= 1.0:
        raise ValueError("rate must be between 0.0 and 1.0")
    return round(price * (1 - rate), 2)


# ─── Tests — covering every boundary ──────────────────────────────────────────

class TestDiscountRate:
    """Each test targets a specific boundary to resist mutations like > → >=."""

    # Boundary: years < 2
    def test_zero_years_returns_zero_discount(self):
        assert discount_rate(0) == 0.0          # exact value assertion

    def test_one_year_returns_zero_discount(self):
        assert discount_rate(1) == 0.0

    # Boundary: years == 2 (first year that qualifies for 5%)
    def test_two_years_returns_five_percent(self):
        assert discount_rate(2) == 0.05

    def test_four_years_returns_five_percent(self):
        assert discount_rate(4) == 0.05

    # Boundary: years == 5 (first year that qualifies for 10%)
    def test_five_years_returns_ten_percent(self):
        assert discount_rate(5) == 0.10

    def test_nine_years_returns_ten_percent(self):
        assert discount_rate(9) == 0.10

    # Boundary: years == 10 (first year that qualifies for 15%)
    def test_ten_years_returns_fifteen_percent(self):
        assert discount_rate(10) == 0.15

    def test_twenty_years_returns_fifteen_percent(self):
        assert discount_rate(20) == 0.15

    # Guard: negative input raises
    def test_negative_years_raises(self):
        with pytest.raises(ValueError):
            discount_rate(-1)

    # Verify distinct values — kills relational mutations
    def test_discount_increases_with_loyalty(self):
        assert discount_rate(0) < discount_rate(2) < discount_rate(5) < discount_rate(10)


class TestApplyDiscount:

    # Exact value assertions (resist arithmetic mutations like * → /)
    def test_no_discount_returns_full_price(self):
        assert apply_discount(100.0, 0.0) == 100.0

    def test_full_discount_returns_zero(self):
        assert apply_discount(100.0, 1.0) == 0.0

    def test_five_percent_discount(self):
        assert apply_discount(100.0, 0.05) == 95.0

    def test_ten_percent_discount(self):
        assert apply_discount(200.0, 0.10) == 180.0

    def test_result_is_rounded_to_two_decimal_places(self):
        # 100 * (1 - 0.333) = 66.7 — ensure rounding is applied
        result = apply_discount(100.0, 1/3)
        assert result == round(result, 2)

    # Guard: negative price raises
    def test_negative_price_raises(self):
        with pytest.raises(ValueError, match="price must not be negative"):
            apply_discount(-1.0, 0.0)

    # Guard: rate out of range raises
    def test_rate_above_one_raises(self):
        with pytest.raises(ValueError, match="rate must be between"):
            apply_discount(100.0, 1.01)

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError):
            apply_discount(100.0, -0.01)
