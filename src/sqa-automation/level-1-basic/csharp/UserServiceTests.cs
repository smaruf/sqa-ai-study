// Level 1 - Basic: NUnit SetUp/TearDown, Parameterised Tests in C#
// =================================================================
//
// Run:  dotnet test --verbosity normal

using NUnit.Framework;

namespace Sqa.Level1;

// ── System Under Test ─────────────────────────────────────────────────────────

public record User(int Id, string Name, string Email);

public class UserService
{
    private readonly Dictionary<int, User> _store = new();
    private int _nextId = 1;

    public User Create(string name, string email)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new ArgumentException("Name must not be blank", nameof(name));
        if (!email.Contains('@'))
            throw new ArgumentException("Invalid email address", nameof(email));

        var user = new User(_nextId++, name.Trim(), email.Trim());
        _store[user.Id] = user;
        return user;
    }

    public User FindById(int id) =>
        _store.TryGetValue(id, out var user)
            ? user
            : throw new KeyNotFoundException($"User not found: {id}");

    public bool Delete(int id) => _store.Remove(id);
    public int Count()         => _store.Count;
}

// ── Tests ─────────────────────────────────────────────────────────────────────

[TestFixture]
[Description("UserService")]
public class UserServiceTests
{
    private UserService _service = null!;

    [SetUp]
    public void SetUp() => _service = new UserService();

    [TearDown]
    public void TearDown() { /* Clean up resources if needed */ }

    [Test]
    public void Create_ValidInput_AssignsSequentialId()
    {
        var alice = _service.Create("Alice", "alice@example.com");
        var bob   = _service.Create("Bob",   "bob@example.com");

        Assert.That(alice.Id, Is.EqualTo(1));
        Assert.That(bob.Id,   Is.EqualTo(2));
    }

    [Test]
    public void FindById_ReturnsCorrectUser()
    {
        var created = _service.Create("Alice", "alice@example.com");
        var found   = _service.FindById(created.Id);

        Assert.That(found.Name,  Is.EqualTo("Alice"));
        Assert.That(found.Email, Is.EqualTo("alice@example.com"));
    }

    [Test]
    public void FindById_UnknownId_ThrowsKeyNotFoundException()
    {
        Assert.Throws<KeyNotFoundException>(() => _service.FindById(999));
    }

    [Test]
    public void Delete_ExistingUser_ReturnsTrueAndRemovesUser()
    {
        var user = _service.Create("Alice", "alice@example.com");
        bool removed = _service.Delete(user.Id);

        Assert.That(removed,          Is.True);
        Assert.That(_service.Count(), Is.EqualTo(0));
    }

    [Test]
    public void Delete_NonExistentUser_ReturnsFalse()
    {
        Assert.That(_service.Delete(999), Is.False);
    }

    // ── [TestCase] — inline parameterised tests ──────────────────────────────

    [TestCase("",   "user@example.com", TestName = "empty name throws")]
    [TestCase("  ", "user@example.com", TestName = "whitespace name throws")]
    public void Create_BlankName_ThrowsArgumentException(string blankName, string email)
    {
        Assert.Throws<ArgumentException>(() => _service.Create(blankName, email));
    }

    [TestCase("Alice", "not-an-email",        TestName = "no @ symbol")]
    [TestCase("Alice", "missing-at-sign.com", TestName = "no @ in domain")]
    [TestCase("Alice", "",                    TestName = "empty email")]
    public void Create_InvalidEmail_ThrowsArgumentException(string name, string badEmail)
    {
        Assert.Throws<ArgumentException>(() => _service.Create(name, badEmail));
    }

    // ── [TestCaseSource] — external test data ────────────────────────────────

    private static readonly object[] ValidUsers =
    {
        new object[] { "Alice", "alice@example.com" },
        new object[] { "Bob",   "bob@example.com"   },
        new object[] { "Carol", "carol@corp.org"     },
    };

    [TestCaseSource(nameof(ValidUsers))]
    public void Create_ValidUsers_StoredWithCorrectNameAndEmail(string name, string email)
    {
        var user = _service.Create(name, email);

        Assert.That(user.Name,  Is.EqualTo(name));
        Assert.That(user.Email, Is.EqualTo(email));
    }
}
