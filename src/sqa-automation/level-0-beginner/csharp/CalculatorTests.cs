// Level 0 - Beginner: First NUnit Test in C#
// ============================================
// This file demonstrates a minimal NUnit test for a Calculator class.
//
// Prerequisites:
//   .NET 8 SDK
//   NuGet: NUnit, NUnit3TestAdapter, Microsoft.NET.Test.Sdk
//
// Run:
//   dotnet test --verbosity normal

using NUnit.Framework;

namespace Sqa.Level0;

/// <summary>
/// A simple calculator — our System Under Test (SUT).
/// In a real project this would live in the production assembly.
/// </summary>
public class Calculator
{
    public double Add(double a, double b)      => a + b;
    public double Subtract(double a, double b) => a - b;
    public double Multiply(double a, double b) => a * b;

    public double Divide(double a, double b)
    {
        if (b == 0) throw new DivideByZeroException("Cannot divide by zero");
        return a / b;
    }
}

/// <summary>
/// Unit tests for <see cref="Calculator"/>.
///
/// NUnit discovers classes with [TestFixture] and methods with [Test].
/// [TestFixture] is optional in NUnit 3+ when the class contains [Test] methods.
/// </summary>
[TestFixture]
public class CalculatorTests
{
    private Calculator _calc = null!;

    // SetUp runs before each test method — used for common Arrange steps.
    [SetUp]
    public void SetUp() => _calc = new Calculator();

    [Test]
    [Description("Adds two positive numbers")]
    public void Add_TwoPositiveNumbers_ReturnsCorrectSum()
    {
        double result = _calc.Add(3, 4);
        Assert.That(result, Is.EqualTo(7));
    }

    [Test]
    public void Subtract_ReturnsCorrectDifference()
    {
        double result = _calc.Subtract(10, 3);
        Assert.That(result, Is.EqualTo(7));
    }

    [Test]
    public void Multiply_TwoNumbers_ReturnsProduct()
    {
        Assert.That(_calc.Multiply(6, 7), Is.EqualTo(42));
    }

    [Test]
    public void Divide_GivesFloatResult()
    {
        Assert.That(_calc.Divide(10, 4), Is.EqualTo(2.5));
    }

    [Test]
    public void Divide_ByZero_ThrowsDivideByZeroException()
    {
        Assert.Throws<DivideByZeroException>(() => _calc.Divide(5, 0));
    }

    [Test]
    public void Add_NegativeNumbers_ReturnsNegativeSum()
    {
        Assert.That(_calc.Add(-3, -4), Is.EqualTo(-7));
    }

    [Test]
    public void Add_Zero_ReturnsOtherNumber()
    {
        Assert.That(_calc.Add(0, 42), Is.EqualTo(42));
    }
}
