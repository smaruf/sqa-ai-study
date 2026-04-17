// Level 0 - Beginner: Anatomy of a Test in C# — Arrange, Act, Assert
// ====================================================================
//
// Run:  dotnet test --verbosity normal

using NUnit.Framework;

namespace Sqa.Level0;

/// <summary>
/// A minimal bank account used to demonstrate the AAA pattern.
/// </summary>
public class BankAccount
{
    public string Owner { get; }
    public double Balance { get; private set; }

    public BankAccount(string owner, double initialBalance = 0)
    {
        if (initialBalance < 0)
            throw new ArgumentException("Initial balance cannot be negative", nameof(initialBalance));
        Owner = owner;
        Balance = initialBalance;
    }

    public void Deposit(double amount)
    {
        if (amount <= 0)
            throw new ArgumentException("Deposit amount must be positive", nameof(amount));
        Balance += amount;
    }

    public void Withdraw(double amount)
    {
        if (amount <= 0)
            throw new ArgumentException("Withdrawal amount must be positive", nameof(amount));
        if (amount > Balance)
            throw new InvalidOperationException("Insufficient funds");
        Balance -= amount;
    }

    public void Transfer(double amount, BankAccount target)
    {
        Withdraw(amount);
        target.Deposit(amount);
    }
}

[TestFixture]
[Description("BankAccount — deposit behaviour")]
public class BankAccountDepositTests
{
    [Test]
    public void Deposit_ValidAmount_IncreasesBalance()
    {
        // Arrange
        var account = new BankAccount("Alice", initialBalance: 100);

        // Act
        account.Deposit(50);

        // Assert
        Assert.That(account.Balance, Is.EqualTo(150));
    }

    [Test]
    public void Deposit_ZeroAmount_ThrowsArgumentException()
    {
        // Arrange
        var account = new BankAccount("Alice");

        // Act & Assert
        Assert.Throws<ArgumentException>(() => account.Deposit(0));
    }

    [Test]
    public void Deposit_NegativeAmount_ThrowsArgumentException()
    {
        var account = new BankAccount("Alice");
        Assert.Throws<ArgumentException>(() => account.Deposit(-10));
    }
}

[TestFixture]
[Description("BankAccount — withdrawal behaviour")]
public class BankAccountWithdrawalTests
{
    [Test]
    public void Withdraw_ValidAmount_DecreasesBalance()
    {
        // Arrange
        var account = new BankAccount("Bob", initialBalance: 200);

        // Act
        account.Withdraw(75);

        // Assert
        Assert.That(account.Balance, Is.EqualTo(125));
    }

    [Test]
    public void Withdraw_EntireBalance_LeavesZeroBalance()
    {
        var account = new BankAccount("Bob", initialBalance: 100);
        account.Withdraw(100);
        Assert.That(account.Balance, Is.EqualTo(0));
    }

    [Test]
    public void Withdraw_MoreThanBalance_ThrowsInvalidOperationException()
    {
        // Arrange
        var account = new BankAccount("Bob", initialBalance: 50);

        // Act & Assert
        var ex = Assert.Throws<InvalidOperationException>(() => account.Withdraw(100));
        Assert.That(ex!.Message, Is.EqualTo("Insufficient funds"));
    }
}

[TestFixture]
[Description("BankAccount — transfer behaviour")]
public class BankAccountTransferTests
{
    [Test]
    public void Transfer_ValidAmount_MovesFundsBetweenAccounts()
    {
        // Arrange
        var sender   = new BankAccount("Alice", initialBalance: 500);
        var receiver = new BankAccount("Bob",   initialBalance: 100);

        // Act
        sender.Transfer(200, receiver);

        // Assert
        Assert.That(sender.Balance,   Is.EqualTo(300));
        Assert.That(receiver.Balance, Is.EqualTo(300));
    }

    [Test]
    public void Transfer_InsufficientFunds_LeavesBalancesUnchanged()
    {
        // Arrange
        var sender   = new BankAccount("Alice", initialBalance:  50);
        var receiver = new BankAccount("Bob",   initialBalance: 100);

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => sender.Transfer(200, receiver));

        Assert.That(sender.Balance,   Is.EqualTo(50));
        Assert.That(receiver.Balance, Is.EqualTo(100));
    }
}
