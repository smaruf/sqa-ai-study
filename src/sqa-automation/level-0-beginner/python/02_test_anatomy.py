"""
Level 0 - Beginner: Anatomy of a Test — Arrange, Act, Assert
=============================================================
Every well-written test follows three clear phases:

  Arrange  — prepare the System Under Test (SUT) and any inputs
  Act      — call the code you want to exercise
  Assert   — verify the outcome matches expectations

Run:
    pytest 02_test_anatomy.py -v
"""

import pytest


# ─── System Under Test ────────────────────────────────────────────────────────

class BankAccount:
    """A minimal bank account used to demonstrate test structure."""

    def __init__(self, owner: str, initial_balance: float = 0.0):
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")
        self.owner = owner
        self._balance = initial_balance

    @property
    def balance(self) -> float:
        return self._balance

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount

    def transfer(self, amount: float, target: "BankAccount") -> None:
        self.withdraw(amount)
        target.deposit(amount)


# ─── Tests demonstrating the AAA pattern ─────────────────────────────────────

class TestBankAccountDeposit:
    """Group related tests in a class for better organisation."""

    def test_deposit_increases_balance(self):
        # Arrange
        account = BankAccount(owner="Alice", initial_balance=100.0)

        # Act
        account.deposit(50.0)

        # Assert
        assert account.balance == 150.0

    def test_deposit_zero_raises_value_error(self):
        # Arrange
        account = BankAccount(owner="Alice")

        # Act & Assert  (combined when testing exceptions)
        with pytest.raises(ValueError, match="Deposit amount must be positive"):
            account.deposit(0)

    def test_deposit_negative_raises_value_error(self):
        # Arrange
        account = BankAccount(owner="Alice")

        # Act & Assert
        with pytest.raises(ValueError):
            account.deposit(-10)


class TestBankAccountWithdrawal:

    def test_withdraw_decreases_balance(self):
        # Arrange
        account = BankAccount(owner="Bob", initial_balance=200.0)

        # Act
        account.withdraw(75.0)

        # Assert
        assert account.balance == 125.0

    def test_withdraw_entire_balance_leaves_zero(self):
        # Arrange
        account = BankAccount(owner="Bob", initial_balance=100.0)

        # Act
        account.withdraw(100.0)

        # Assert
        assert account.balance == 0.0

    def test_withdraw_more_than_balance_raises_error(self):
        # Arrange
        account = BankAccount(owner="Bob", initial_balance=50.0)

        # Act & Assert
        with pytest.raises(ValueError, match="Insufficient funds"):
            account.withdraw(100.0)


class TestBankAccountTransfer:

    def test_transfer_moves_funds_between_accounts(self):
        # Arrange
        sender = BankAccount(owner="Alice", initial_balance=500.0)
        receiver = BankAccount(owner="Bob", initial_balance=100.0)

        # Act
        sender.transfer(200.0, receiver)

        # Assert
        assert sender.balance == 300.0
        assert receiver.balance == 300.0

    def test_transfer_insufficient_funds_leaves_balances_unchanged(self):
        # Arrange
        sender = BankAccount(owner="Alice", initial_balance=50.0)
        receiver = BankAccount(owner="Bob", initial_balance=100.0)

        # Act & Assert
        with pytest.raises(ValueError, match="Insufficient funds"):
            sender.transfer(200.0, receiver)

        # Balances must not have changed
        assert sender.balance == 50.0
        assert receiver.balance == 100.0
