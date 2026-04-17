// Level 5 - Master: Property-Based Testing in Go with rapid
// ===========================================================
// rapid is a Go property-based testing library inspired by Hypothesis.
//
// Install:  go get pgregory.net/rapid
// Run:      go test -v ./...

package level5

import (
	"fmt"
	"sort"
	"strings"
	"testing"

	"pgregory.net/rapid"
)

// ── System Under Test ─────────────────────────────────────────────────────────

// SortAscending returns a new sorted slice.
func SortAscending(items []int) []int {
	result := make([]int, len(items))
	copy(result, items)
	sort.Ints(result)
	return result
}

// ReverseString reverses the rune sequence of a string.
func ReverseString(s string) string {
	runes := []rune(s)
	for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
		runes[i], runes[j] = runes[j], runes[i]
	}
	return string(runes)
}

// Clamp constrains value to [lo, hi].
func Clamp(value, lo, hi int) (int, error) {
	if lo > hi {
		return 0, fmt.Errorf("lo must not exceed hi")
	}
	if value < lo {
		return lo, nil
	}
	if value > hi {
		return hi, nil
	}
	return value, nil
}

// ── Sorting properties ────────────────────────────────────────────────────────

func TestSortPreservesLength(t *testing.T) {
	rapid.Check(t, func(rt *rapid.T) {
		items := rapid.SliceOf(rapid.Int()).Draw(rt, "items")
		result := SortAscending(items)
		if len(result) != len(items) {
			rt.Fatalf("length changed: got %d; want %d", len(result), len(items))
		}
	})
}

func TestSortedListIsOrdered(t *testing.T) {
	rapid.Check(t, func(rt *rapid.T) {
		items := rapid.SliceOf(rapid.Int()).Draw(rt, "items")
		result := SortAscending(items)
		for i := 0; i < len(result)-1; i++ {
			if result[i] > result[i+1] {
				rt.Fatalf("not sorted at index %d: %d > %d", i, result[i], result[i+1])
			}
		}
	})
}

func TestSortIsIdempotent(t *testing.T) {
	rapid.Check(t, func(rt *rapid.T) {
		items := rapid.SliceOf(rapid.Int()).Draw(rt, "items")
		once  := SortAscending(items)
		twice := SortAscending(once)
		for i := range once {
			if once[i] != twice[i] {
				rt.Fatalf("sort not idempotent at index %d", i)
			}
		}
	})
}

// ── String reversal properties ────────────────────────────────────────────────

func TestDoubleReverseIsIdentity(t *testing.T) {
	rapid.Check(t, func(rt *rapid.T) {
		s := rapid.String().Draw(rt, "s")
		if ReverseString(ReverseString(s)) != s {
			rt.Fatalf("double reverse of %q did not return original", s)
		}
	})
}

func TestReversedStringHasSameRuneLength(t *testing.T) {
	rapid.Check(t, func(rt *rapid.T) {
		s := rapid.String().Draw(rt, "s")
		if len([]rune(ReverseString(s))) != len([]rune(s)) {
			rt.Fatal("reversed string has different rune length")
		}
	})
}

func TestReverseSingleCharIsNoOp(t *testing.T) {
	rapid.Check(t, func(rt *rapid.T) {
		// Generate a string with exactly one rune
		r := rapid.Rune().Draw(rt, "r")
		s := string(r)
		if ReverseString(s) != s {
			rt.Fatalf("reversing single char %q changed it to %q", s, ReverseString(s))
		}
	})
}

// ── Arithmetic properties ─────────────────────────────────────────────────────

func TestAdditionIsCommutative(t *testing.T) {
	rapid.Check(t, func(rt *rapid.T) {
		a := rapid.Int().Draw(rt, "a")
		b := rapid.Int().Draw(rt, "b")
		if a+b != b+a {
			rt.Fatalf("a+b (%d) != b+a (%d) for a=%d, b=%d", a+b, b+a, a, b)
		}
	})
}

// ── Placeholder to avoid unused import warning ────────────────────────────────

var _ = strings.TrimSpace
