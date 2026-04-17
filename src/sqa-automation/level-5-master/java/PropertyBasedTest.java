// Level 5 - Master: Property-Based Testing in Java with jqwik
// =============================================================
// jqwik is a property-based testing library for JUnit 5.
//
// Maven dependency:
//   net.jqwik:jqwik:1.8.x
//
// Run:  mvn test

package sqa.level5;

import net.jqwik.api.*;
import net.jqwik.api.constraints.*;
import java.util.*;
import static org.assertj.core.api.Assertions.*;

@Label("Property-Based Tests")
class PropertyBasedTest {

    // ── System Under Test ──────────────────────────────────────────────────────

    /** Sort a list in ascending order. */
    static List<Integer> sortAscending(List<Integer> items) {
        var result = new ArrayList<>(items);
        Collections.sort(result);
        return result;
    }

    /** Reverse a string. */
    static String reverseString(String s) {
        return new StringBuilder(s).reverse().toString();
    }

    // ── Sorting properties ─────────────────────────────────────────────────────

    @Property
    @Label("sorted list has the same size as input")
    void sortPreservesLength(@ForAll List<Integer> items) {
        assertThat(sortAscending(items)).hasSameSizeAs(items);
    }

    @Property
    @Label("sorted list is in non-decreasing order")
    void sortedListIsOrdered(@ForAll List<Integer> items) {
        var result = sortAscending(items);
        for (int i = 0; i < result.size() - 1; i++) {
            assertThat(result.get(i)).isLessThanOrEqualTo(result.get(i + 1));
        }
    }

    @Property
    @Label("sorted list contains the same elements")
    void sortPreservesElements(@ForAll List<Integer> items) {
        var result = sortAscending(items);
        var sortedInput    = new ArrayList<>(items);
        var sortedResult   = new ArrayList<>(result);
        Collections.sort(sortedInput);
        Collections.sort(sortedResult);
        assertThat(sortedResult).isEqualTo(sortedInput);
    }

    @Property
    @Label("sorting is idempotent")
    void sortIsIdempotent(@ForAll List<Integer> items) {
        var once  = sortAscending(items);
        var twice = sortAscending(once);
        assertThat(twice).isEqualTo(once);
    }

    // ── String reversal properties ─────────────────────────────────────────────

    @Property
    @Label("reverse of reverse is the original string")
    void doubleReverseIsIdentity(@ForAll String s) {
        assertThat(reverseString(reverseString(s))).isEqualTo(s);
    }

    @Property
    @Label("reversed string has the same length")
    void reversedStringHasSameLength(@ForAll String s) {
        assertThat(reverseString(s)).hasSameSizeAs(s);
    }

    @Property
    @Label("reversing a single character is a no-op")
    void reverseSingleCharIsNoOp(@ForAll @StringLength(1) String s) {
        assertThat(reverseString(s)).isEqualTo(s);
    }

    // ── Arithmetic properties ──────────────────────────────────────────────────

    @Property
    @Label("addition is commutative")
    void additionIsCommutative(
            @ForAll @IntRange(min = -1000, max = 1000) int a,
            @ForAll @IntRange(min = -1000, max = 1000) int b) {
        assertThat(a + b).isEqualTo(b + a);
    }

    @Property
    @Label("absolute value is always non-negative")
    void absIsNonNegative(@ForAll int n) {
        Assume.that(n != Integer.MIN_VALUE); // avoid overflow edge case
        assertThat(Math.abs(n)).isGreaterThanOrEqualTo(0);
    }
}
