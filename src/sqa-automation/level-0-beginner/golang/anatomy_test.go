// Level 0 - Beginner: Anatomy of a Test in Go — Arrange, Act, Assert
// ====================================================================
//
// Run:  go test -v -run TestBankAccount

package level0

import (
	"errors"
	"testing"
)

// ── System Under Test ─────────────────────────────────────────────────────────

// BankAccount is a minimal bank account for demonstrating test anatomy.
type BankAccount struct {
	Owner   string
	balance float64
}

// NewBankAccount creates a BankAccount; returns an error for negative balances.
func NewBankAccount(owner string, initialBalance float64) (*BankAccount, error) {
	if initialBalance < 0 {
		return nil, errors.New("initial balance cannot be negative")
	}
	return &BankAccount{Owner: owner, balance: initialBalance}, nil
}

func (a *BankAccount) Balance() float64 { return a.balance }

func (a *BankAccount) Deposit(amount float64) error {
	if amount <= 0 {
		return errors.New("deposit amount must be positive")
	}
	a.balance += amount
	return nil
}

func (a *BankAccount) Withdraw(amount float64) error {
	if amount <= 0 {
		return errors.New("withdrawal amount must be positive")
	}
	if amount > a.balance {
		return errors.New("insufficient funds")
	}
	a.balance -= amount
	return nil
}

func (a *BankAccount) Transfer(amount float64, target *BankAccount) error {
	if err := a.Withdraw(amount); err != nil {
		return err
	}
	return target.Deposit(amount)
}

// ── Deposit tests ─────────────────────────────────────────────────────────────

func TestBankAccountDeposit_IncreasesBalance(t *testing.T) {
	// Arrange
	account, _ := NewBankAccount("Alice", 100)

	// Act
	err := account.Deposit(50)

	// Assert
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if account.Balance() != 150 {
		t.Errorf("balance = %v; want 150", account.Balance())
	}
}

func TestBankAccountDeposit_ZeroAmountReturnsError(t *testing.T) {
	// Arrange
	account, _ := NewBankAccount("Alice", 0)

	// Act
	err := account.Deposit(0)

	// Assert
	if err == nil {
		t.Error("expected error for zero deposit, got nil")
	}
}

func TestBankAccountDeposit_NegativeAmountReturnsError(t *testing.T) {
	account, _ := NewBankAccount("Alice", 0)
	if err := account.Deposit(-10); err == nil {
		t.Error("expected error for negative deposit, got nil")
	}
}

// ── Withdrawal tests ──────────────────────────────────────────────────────────

func TestBankAccountWithdraw_DecreasesBalance(t *testing.T) {
	// Arrange
	account, _ := NewBankAccount("Bob", 200)

	// Act
	err := account.Withdraw(75)

	// Assert
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if account.Balance() != 125 {
		t.Errorf("balance = %v; want 125", account.Balance())
	}
}

func TestBankAccountWithdraw_InsufficientFundsReturnsError(t *testing.T) {
	// Arrange
	account, _ := NewBankAccount("Bob", 50)

	// Act
	err := account.Withdraw(100)

	// Assert
	if err == nil {
		t.Error("expected insufficient funds error, got nil")
	}
	// Balance must remain unchanged
	if account.Balance() != 50 {
		t.Errorf("balance changed after failed withdrawal: got %v; want 50", account.Balance())
	}
}

// ── Transfer tests ────────────────────────────────────────────────────────────

func TestBankAccountTransfer_MovesFundsBetweenAccounts(t *testing.T) {
	// Arrange
	sender, _   := NewBankAccount("Alice", 500)
	receiver, _ := NewBankAccount("Bob", 100)

	// Act
	err := sender.Transfer(200, receiver)

	// Assert
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if sender.Balance() != 300 {
		t.Errorf("sender balance = %v; want 300", sender.Balance())
	}
	if receiver.Balance() != 300 {
		t.Errorf("receiver balance = %v; want 300", receiver.Balance())
	}
}

func TestBankAccountTransfer_InsufficientFundsLeavesBalancesUnchanged(t *testing.T) {
	// Arrange
	sender, _   := NewBankAccount("Alice", 50)
	receiver, _ := NewBankAccount("Bob", 100)

	// Act
	err := sender.Transfer(200, receiver)

	// Assert
	if err == nil {
		t.Error("expected error for insufficient funds, got nil")
	}
	if sender.Balance() != 50 {
		t.Errorf("sender balance changed: %v; want 50", sender.Balance())
	}
	if receiver.Balance() != 100 {
		t.Errorf("receiver balance changed: %v; want 100", receiver.Balance())
	}
}
