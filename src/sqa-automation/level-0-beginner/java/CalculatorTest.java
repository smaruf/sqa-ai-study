// Level 0 - Beginner: First JUnit 5 Test in Java
// ================================================
// This file demonstrates a minimal JUnit 5 test for a Calculator class.
//
// Prerequisites:
//   JDK 17+, Maven or Gradle
//   Maven dependency: org.junit.jupiter:junit-jupiter:5.10.x
//
// Run:
//   mvn test   (from the java/ directory containing pom.xml)

package sqa.level0;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for the Calculator class.
 *
 * JUnit 5 discovers methods annotated with @Test automatically.
 * @DisplayName provides a human-readable description in test reports.
 */
@DisplayName("Calculator")
class CalculatorTest {

    // ── System Under Test ────────────────────────────────────────────────────

    /**
     * A simple calculator — our System Under Test (SUT).
     * In real projects this would live in src/main/java.
     */
    static class Calculator {
        double add(double a, double b)      { return a + b; }
        double subtract(double a, double b) { return a - b; }
        double multiply(double a, double b) { return a * b; }

        double divide(double a, double b) {
            if (b == 0) throw new ArithmeticException("Cannot divide by zero");
            return a / b;
        }
    }

    private final Calculator calc = new Calculator();

    // ── Tests ─────────────────────────────────────────────────────────────────

    @Test
    @DisplayName("adds two positive numbers")
    void addTwoPositiveNumbers() {
        double result = calc.add(3, 4);
        assertEquals(7, result);
    }

    @Test
    @DisplayName("subtracts to give correct difference")
    void subtractReturnsCorrectDifference() {
        double result = calc.subtract(10, 3);
        assertEquals(7, result);
    }

    @Test
    @DisplayName("multiplies two numbers")
    void multiplyTwoNumbers() {
        assertEquals(42, calc.multiply(6, 7));
    }

    @Test
    @DisplayName("divides to give a float result")
    void divideGivesFloatResult() {
        assertEquals(2.5, calc.divide(10, 4));
    }

    @Test
    @DisplayName("throws ArithmeticException when dividing by zero")
    void divideByZeroThrowsException() {
        ArithmeticException ex = assertThrows(
                ArithmeticException.class,
                () -> calc.divide(5, 0)
        );
        assertEquals("Cannot divide by zero", ex.getMessage());
    }

    @Test
    @DisplayName("adding negative numbers returns negative sum")
    void addNegativeNumbers() {
        assertEquals(-7, calc.add(-3, -4));
    }

    @Test
    @DisplayName("adding zero returns the other number")
    void addZeroReturnsOtherNumber() {
        assertEquals(42, calc.add(0, 42));
    }
}
