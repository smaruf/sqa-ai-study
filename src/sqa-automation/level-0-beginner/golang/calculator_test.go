// Level 0 - Beginner: First Go Test
// ==================================
// Go ships with a built-in testing package — no extra dependencies needed.
//
// Run:
//   go test -v ./...        (from the golang/ directory)
//   go test -v -run TestCalculator

package level0

import (
	"errors"
	"testing"
)

// ── System Under Test ─────────────────────────────────────────────────────────

// Calculator is a simple arithmetic helper used as the SUT.
type Calculator struct{}

func (c Calculator) Add(a, b float64) float64      { return a + b }
func (c Calculator) Subtract(a, b float64) float64 { return a - b }
func (c Calculator) Multiply(a, b float64) float64 { return a * b }

func (c Calculator) Divide(a, b float64) (float64, error) {
	if b == 0 {
		return 0, errors.New("cannot divide by zero")
	}
	return a / b, nil
}

// ── Tests ─────────────────────────────────────────────────────────────────────

// Go test functions must start with "Test" and accept *testing.T.

func TestCalculatorAdd(t *testing.T) {
	calc := Calculator{}
	got := calc.Add(3, 4)
	want := float64(7)
	if got != want {
		t.Errorf("Add(3, 4) = %v; want %v", got, want)
	}
}

func TestCalculatorSubtract(t *testing.T) {
	calc := Calculator{}
	got := calc.Subtract(10, 3)
	if got != 7 {
		t.Errorf("Subtract(10, 3) = %v; want 7", got)
	}
}

func TestCalculatorMultiply(t *testing.T) {
	calc := Calculator{}
	if calc.Multiply(6, 7) != 42 {
		t.Error("Multiply(6, 7) should equal 42")
	}
}

func TestCalculatorDivide(t *testing.T) {
	calc := Calculator{}
	got, err := calc.Divide(10, 4)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != 2.5 {
		t.Errorf("Divide(10, 4) = %v; want 2.5", got)
	}
}

func TestCalculatorDivideByZeroReturnsError(t *testing.T) {
	calc := Calculator{}
	_, err := calc.Divide(5, 0)
	if err == nil {
		t.Error("expected error when dividing by zero, got nil")
	}
}

func TestCalculatorAddNegativeNumbers(t *testing.T) {
	calc := Calculator{}
	if calc.Add(-3, -4) != -7 {
		t.Error("Add(-3, -4) should equal -7")
	}
}

func TestCalculatorAddZero(t *testing.T) {
	calc := Calculator{}
	if calc.Add(0, 42) != 42 {
		t.Error("Add(0, 42) should equal 42")
	}
}

// ── Table-driven tests ────────────────────────────────────────────────────────
// Table-driven tests are idiomatic Go — define a slice of test cases,
// then iterate, calling t.Run() for each one.

func TestCalculatorAddTableDriven(t *testing.T) {
	tests := []struct {
		name string
		a, b float64
		want float64
	}{
		{"positive + positive", 3, 4, 7},
		{"negative + negative", -3, -4, -7},
		{"zero identity", 0, 42, 42},
		{"float values", 1.5, 2.5, 4.0},
	}

	calc := Calculator{}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := calc.Add(tc.a, tc.b)
			if got != tc.want {
				t.Errorf("Add(%v, %v) = %v; want %v", tc.a, tc.b, got, tc.want)
			}
		})
	}
}
