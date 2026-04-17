// Level 5 - Master: Mutation-Resistant Tests in C#
// ==================================================
// Stryker.NET kills mutants that survive a weak test suite.
// This file shows patterns that maximise the mutation kill rate.
//
// Run tests:      dotnet test --verbosity normal
// Run mutations:  dotnet stryker

using NUnit.Framework;

namespace Sqa.Level5;

// ── System Under Test ─────────────────────────────────────────────────────────

public static class DiscountCalculator
{
    /// <summary>
    /// Returns a discount rate based on years as a customer.
    /// 0–1 → 0%, 2–4 → 5%, 5–9 → 10%, 10+ → 15%
    /// </summary>
    public static double DiscountRate(int yearsAsCustomer)
    {
        if (yearsAsCustomer < 0)
            throw new ArgumentOutOfRangeException(nameof(yearsAsCustomer), "Must not be negative");
        if (yearsAsCustomer < 2)  return 0.00;
        if (yearsAsCustomer < 5)  return 0.05;
        if (yearsAsCustomer < 10) return 0.10;
        return 0.15;
    }

    public static double ApplyDiscount(double price, double rate)
    {
        if (price < 0)
            throw new ArgumentException("price must not be negative", nameof(price));
        if (rate is < 0.0 or > 1.0)
            throw new ArgumentException("rate must be between 0 and 1", nameof(rate));
        return Math.Round(price * (1 - rate), 2);
    }
}

// ── Tests — targeting every boundary condition ────────────────────────────────

[TestFixture]
public class DiscountRateTests
{
    // Boundary: years < 2
    [TestCase(0,  0.00, TestName = "0 years → 0%")]
    [TestCase(1,  0.00, TestName = "1 year  → 0%")]
    // Boundary: years == 2 (first year for 5%)
    [TestCase(2,  0.05, TestName = "2 years → 5%")]
    [TestCase(4,  0.05, TestName = "4 years → 5%")]
    // Boundary: years == 5 (first year for 10%)
    [TestCase(5,  0.10, TestName = "5 years → 10%")]
    [TestCase(9,  0.10, TestName = "9 years → 10%")]
    // Boundary: years == 10 (first year for 15%)
    [TestCase(10, 0.15, TestName = "10 years → 15%")]
    [TestCase(20, 0.15, TestName = "20 years → 15%")]
    public void DiscountRate_ReturnsExpectedValue(int years, double expected)
    {
        Assert.That(DiscountCalculator.DiscountRate(years), Is.EqualTo(expected).Within(0.001));
    }

    [Test]
    public void DiscountRate_IncreasesWithLoyalty()
    {
        // Verify ordering — kills relational-operator mutations
        Assert.That(DiscountCalculator.DiscountRate(0),  Is.LessThan(DiscountCalculator.DiscountRate(2)));
        Assert.That(DiscountCalculator.DiscountRate(2),  Is.LessThan(DiscountCalculator.DiscountRate(5)));
        Assert.That(DiscountCalculator.DiscountRate(5),  Is.LessThan(DiscountCalculator.DiscountRate(10)));
    }

    [Test]
    public void DiscountRate_NegativeYears_Throws()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => DiscountCalculator.DiscountRate(-1));
    }
}

[TestFixture]
public class ApplyDiscountTests
{
    [TestCase(100.0, 0.00, 100.0, TestName = "no discount returns full price")]
    [TestCase(100.0, 1.00,   0.0, TestName = "full discount returns zero")]
    [TestCase(100.0, 0.05,  95.0, TestName = "5% discount")]
    [TestCase(200.0, 0.10, 180.0, TestName = "10% discount on 200")]
    [TestCase(99.99, 0.15,  84.99, TestName = "15% discount on 99.99")]
    public void ApplyDiscount_ReturnsExpectedPrice(double price, double rate, double expected)
    {
        Assert.That(DiscountCalculator.ApplyDiscount(price, rate), Is.EqualTo(expected).Within(0.01));
    }

    [Test]
    public void ApplyDiscount_NegativePrice_Throws()
    {
        Assert.Throws<ArgumentException>(() => DiscountCalculator.ApplyDiscount(-1.0, 0.0));
    }

    [TestCase(1.01)]
    [TestCase(-0.01)]
    public void ApplyDiscount_RateOutOfRange_Throws(double badRate)
    {
        Assert.Throws<ArgumentException>(() => DiscountCalculator.ApplyDiscount(100.0, badRate));
    }
}
