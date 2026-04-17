// Level 2 - Intermediate: Mocking with Moq in C#
// ================================================
// Moq is the most popular .NET mocking library. It generates
// mock implementations of interfaces at runtime.
//
// NuGet: Moq, NUnit, Microsoft.NET.Test.Sdk
//
// Run:  dotnet test --verbosity normal

using Moq;
using NUnit.Framework;

namespace Sqa.Level2;

// ── Interfaces (dependency boundaries) ───────────────────────────────────────

public interface IEmailSender
{
    void Send(string to, string subject, string body);
}

public interface IUserRepository
{
    User Save(string name, string email);
    User? FindById(int id);
    bool Delete(int id);
}

// ── Domain ────────────────────────────────────────────────────────────────────

public record User(int Id, string Name, string Email);

public class NotificationService
{
    private readonly IEmailSender _sender;
    public NotificationService(IEmailSender sender) => _sender = sender;

    public void Welcome(string to, string name) =>
        _sender.Send(to, "Welcome!", $"Hello {name}, welcome to our platform.");

    public void PasswordReset(string to, string token) =>
        _sender.Send(to, "Password Reset", $"Your reset token: {token}");
}

public class UserService
{
    private readonly IUserRepository     _repo;
    private readonly NotificationService _notifications;

    public UserService(IUserRepository repo, NotificationService notifications)
    {
        _repo          = repo;
        _notifications = notifications;
    }

    public User Register(string name, string email)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new ArgumentException("Name must not be blank", nameof(name));

        var user = _repo.Save(name, email);
        _notifications.Welcome(user.Email, user.Name);
        return user;
    }

    public User GetUser(int id) =>
        _repo.FindById(id) ?? throw new KeyNotFoundException($"User not found: {id}");
}

// ── Tests ─────────────────────────────────────────────────────────────────────

[TestFixture]
public class NotificationServiceTests
{
    private Mock<IEmailSender>  _mockSender  = null!;
    private NotificationService _service     = null!;

    [SetUp]
    public void SetUp()
    {
        _mockSender = new Mock<IEmailSender>();
        _service    = new NotificationService(_mockSender.Object);
    }

    [Test]
    public void Welcome_SendsEmailToCorrectAddress()
    {
        _service.Welcome("alice@example.com", "Alice");

        // Verify the mock was called with specific arguments
        _mockSender.Verify(s => s.Send(
            "alice@example.com",
            "Welcome!",
            It.IsAny<string>()
        ), Times.Once);
    }

    [Test]
    public void Welcome_BodyContainsUserName()
    {
        string? capturedBody = null;
        _mockSender
            .Setup(s => s.Send(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<string>()))
            .Callback<string, string, string>((_, _, body) => capturedBody = body);

        _service.Welcome("alice@example.com", "Alice");

        Assert.That(capturedBody, Does.Contain("Alice"));
    }

    [Test]
    public void PasswordReset_BodyContainsToken()
    {
        string? capturedBody = null;
        _mockSender
            .Setup(s => s.Send(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<string>()))
            .Callback<string, string, string>((_, _, body) => capturedBody = body);

        _service.PasswordReset("alice@example.com", "tok_abc123");

        Assert.That(capturedBody, Does.Contain("tok_abc123"));
    }
}

[TestFixture]
public class UserServiceTests
{
    private Mock<IUserRepository>  _mockRepo     = null!;
    private Mock<IEmailSender>     _mockSender   = null!;
    private UserService            _service      = null!;

    [SetUp]
    public void SetUp()
    {
        _mockRepo   = new Mock<IUserRepository>();
        _mockSender = new Mock<IEmailSender>();
        var notifications = new NotificationService(_mockSender.Object);
        _service    = new UserService(_mockRepo.Object, notifications);
    }

    [Test]
    public void Register_ValidInput_SavesUserAndSendsWelcome()
    {
        // Arrange — configure the stub to return a user
        _mockRepo
            .Setup(r => r.Save("Alice", "alice@example.com"))
            .Returns(new User(1, "Alice", "alice@example.com"));

        // Act
        var user = _service.Register("Alice", "alice@example.com");

        // Assert
        Assert.That(user.Id,    Is.EqualTo(1));
        Assert.That(user.Name,  Is.EqualTo("Alice"));

        // Verify email was sent
        _mockSender.Verify(s => s.Send(
            "alice@example.com",
            "Welcome!",
            It.IsAny<string>()
        ), Times.Once);
    }

    [Test]
    public void Register_BlankName_ThrowsAndDoesNotSave()
    {
        Assert.Throws<ArgumentException>(() => _service.Register("", "alice@example.com"));

        // Verify repository was never called
        _mockRepo.Verify(r => r.Save(It.IsAny<string>(), It.IsAny<string>()), Times.Never);
    }

    [Test]
    public void GetUser_UnknownId_ThrowsKeyNotFoundException()
    {
        _mockRepo.Setup(r => r.FindById(999)).Returns((User?)null);

        Assert.Throws<KeyNotFoundException>(() => _service.GetUser(999));
    }
}
