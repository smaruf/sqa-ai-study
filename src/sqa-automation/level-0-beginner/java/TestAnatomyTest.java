// Level 0 - Beginner: Anatomy of a Test in Java — Arrange, Act, Assert
// ======================================================================
// This file demonstrates the AAA pattern using a BankAccount class.
//
// Run:  mvn test

package sqa.level0;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Demonstrates the Arrange-Act-Assert (AAA) pattern in JUnit 5.
 *
 * Nested test classes (@Nested) let you group related tests together
 * under a descriptive heading, improving readability in test reports.
 */
@DisplayName("BankAccount")
class TestAnatomyTest {

    // ── System Under Test ─────────────────────────────────────────────────────

    static class BankAccount {
        private final String owner;
        private double balance;

        BankAccount(String owner, double initialBalance) {
            if (initialBalance < 0) throw new IllegalArgumentException("Initial balance cannot be negative");
            this.owner = owner;
            this.balance = initialBalance;
        }

        double getBalance()  { return balance; }
        String getOwner()    { return owner; }

        void deposit(double amount) {
            if (amount <= 0) throw new IllegalArgumentException("Deposit amount must be positive");
            balance += amount;
        }

        void withdraw(double amount) {
            if (amount <= 0) throw new IllegalArgumentException("Withdrawal amount must be positive");
            if (amount > balance) throw new IllegalStateException("Insufficient funds");
            balance -= amount;
        }

        void transfer(double amount, BankAccount target) {
            withdraw(amount);
            target.deposit(amount);
        }
    }

    // ── Deposit tests ─────────────────────────────────────────────────────────

    @Nested
    @DisplayName("deposit()")
    class DepositTests {

        @Test
        @DisplayName("increases the balance by the deposited amount")
        void depositIncreasesBalance() {
            // Arrange
            BankAccount account = new BankAccount("Alice", 100.0);

            // Act
            account.deposit(50.0);

            // Assert
            assertEquals(150.0, account.getBalance());
        }

        @Test
        @DisplayName("throws when amount is zero")
        void depositZeroThrows() {
            // Arrange
            BankAccount account = new BankAccount("Alice", 0);

            // Act & Assert
            assertThrows(IllegalArgumentException.class, () -> account.deposit(0));
        }

        @Test
        @DisplayName("throws when amount is negative")
        void depositNegativeThrows() {
            BankAccount account = new BankAccount("Alice", 0);
            assertThrows(IllegalArgumentException.class, () -> account.deposit(-10));
        }
    }

    // ── Withdrawal tests ──────────────────────────────────────────────────────

    @Nested
    @DisplayName("withdraw()")
    class WithdrawalTests {

        @Test
        @DisplayName("decreases the balance by the withdrawn amount")
        void withdrawDecreasesBalance() {
            // Arrange
            BankAccount account = new BankAccount("Bob", 200.0);

            // Act
            account.withdraw(75.0);

            // Assert
            assertEquals(125.0, account.getBalance());
        }

        @Test
        @DisplayName("withdrawing the full balance leaves zero")
        void withdrawEntireBalanceLeavesZero() {
            BankAccount account = new BankAccount("Bob", 100.0);
            account.withdraw(100.0);
            assertEquals(0.0, account.getBalance());
        }

        @Test
        @DisplayName("throws InsufficientFunds when amount exceeds balance")
        void withdrawMoreThanBalanceThrows() {
            // Arrange
            BankAccount account = new BankAccount("Bob", 50.0);

            // Act & Assert
            IllegalStateException ex = assertThrows(
                    IllegalStateException.class,
                    () -> account.withdraw(100.0)
            );
            assertEquals("Insufficient funds", ex.getMessage());
        }
    }

    // ── Transfer tests ────────────────────────────────────────────────────────

    @Nested
    @DisplayName("transfer()")
    class TransferTests {

        @Test
        @DisplayName("moves funds from sender to receiver")
        void transferMovesFunds() {
            // Arrange
            BankAccount sender   = new BankAccount("Alice", 500.0);
            BankAccount receiver = new BankAccount("Bob",   100.0);

            // Act
            sender.transfer(200.0, receiver);

            // Assert
            assertEquals(300.0, sender.getBalance());
            assertEquals(300.0, receiver.getBalance());
        }

        @Test
        @DisplayName("leaves balances unchanged when sender has insufficient funds")
        void transferInsufficientFundsLeavesBalancesUnchanged() {
            // Arrange
            BankAccount sender   = new BankAccount("Alice",  50.0);
            BankAccount receiver = new BankAccount("Bob",   100.0);

            // Act & Assert
            assertThrows(IllegalStateException.class, () -> sender.transfer(200.0, receiver));

            assertEquals(50.0,  sender.getBalance());
            assertEquals(100.0, receiver.getBalance());
        }
    }
}
