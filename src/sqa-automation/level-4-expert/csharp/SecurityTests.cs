// Level 4 - Expert: Security Testing in C# with NUnit
// ====================================================
// Demonstrates security anti-patterns and their secure alternatives.
//
// NuGet: NUnit, BCrypt.Net-Next, System.Security.Cryptography
//
// Run:  dotnet test --verbosity normal

using System.Data;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Data.Sqlite;
using NUnit.Framework;

namespace Sqa.Level4;

// ── A02: Cryptographic Failures ───────────────────────────────────────────────

public static class PasswordHasher
{
    /// <summary>
    /// INSECURE: MD5 is broken — do not use for passwords.
    /// </summary>
    public static string HashInsecureMD5(string password)
    {
        var bytes = MD5.HashData(Encoding.UTF8.GetBytes(password));
        return Convert.ToHexString(bytes);
    }

    /// <summary>
    /// SECURE: BCrypt with a random salt and adaptive cost factor.
    /// Requires NuGet: BCrypt.Net-Next
    /// </summary>
    public static string HashSecure(string password) =>
        BCrypt.Net.BCrypt.HashPassword(password, workFactor: 12);

    public static bool VerifySecure(string password, string hash) =>
        BCrypt.Net.BCrypt.Verify(password, hash);
}

[TestFixture]
[Description("Password Hashing — Cryptographic Security")]
public class PasswordHasherTests
{
    [Test]
    public void SecureHash_VerifiesCorrectPassword()
    {
        var hash = PasswordHasher.HashSecure("my_secret_password");
        Assert.That(PasswordHasher.VerifySecure("my_secret_password", hash), Is.True);
    }

    [Test]
    public void SecureHash_RejectsWrongPassword()
    {
        var hash = PasswordHasher.HashSecure("correct_password");
        Assert.That(PasswordHasher.VerifySecure("wrong_password", hash), Is.False);
    }

    [Test]
    public void SecureHash_TwoHashesOfSamePasswordDiffer()
    {
        var h1 = PasswordHasher.HashSecure("password");
        var h2 = PasswordHasher.HashSecure("password");
        Assert.That(h1, Is.Not.EqualTo(h2), "BCrypt includes a random salt — hashes must differ");
    }
}

// ── A03: SQL Injection ────────────────────────────────────────────────────────

public class UserDatabase : IDisposable
{
    private readonly SqliteConnection _conn;

    public UserDatabase()
    {
        _conn = new SqliteConnection("Data Source=:memory:");
        _conn.Open();
        _conn.CreateCommand().ExecuteNonQuery();
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = """
            CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT);
            INSERT INTO users VALUES (1, 'Alice', 'alice@example.com');
            """;
        cmd.ExecuteNonQuery();
    }

    /// <summary>INSECURE: String concatenation → SQL injection</summary>
    public List<string> FindByEmailInsecure(string email)
    {
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = $"SELECT name FROM users WHERE email = '{email}'"; // vulnerable
        using var reader = cmd.ExecuteReader();
        var result = new List<string>();
        while (reader.Read()) result.Add(reader.GetString(0));
        return result;
    }

    /// <summary>SECURE: Parameterised query</summary>
    public List<string> FindByEmailSecure(string email)
    {
        using var cmd = _conn.CreateCommand();
        cmd.CommandText = "SELECT name FROM users WHERE email = @email";
        cmd.Parameters.AddWithValue("@email", email);
        using var reader = cmd.ExecuteReader();
        var result = new List<string>();
        while (reader.Read()) result.Add(reader.GetString(0));
        return result;
    }

    public void Dispose() => _conn.Dispose();
}

[TestFixture]
[Description("SQL Injection Prevention")]
public class SqlInjectionTests
{
    private UserDatabase _db = null!;

    [SetUp]   public void SetUp()    => _db = new UserDatabase();
    [TearDown] public void TearDown() => _db.Dispose();

    [Test]
    public void SecureQuery_FindsCorrectUser()
    {
        var names = _db.FindByEmailSecure("alice@example.com");
        Assert.That(names, Is.EqualTo(new[] { "Alice" }));
    }

    [Test]
    public void SecureQuery_InjectionPayloadReturnsEmpty()
    {
        var names = _db.FindByEmailSecure("' OR '1'='1");
        Assert.That(names, Is.Empty, "Parameterised query must not be injectable");
    }
}

// ── A07: Weak Token Generation ────────────────────────────────────────────────

public static class TokenGenerator
{
    /// <summary>SECURE: Cryptographically strong random token</summary>
    public static string GenerateSecure(int byteLength = 32) =>
        Convert.ToHexString(RandomNumberGenerator.GetBytes(byteLength));

    /// <summary>SECURE: Constant-time comparison to prevent timing attacks</summary>
    public static bool ConstantTimeEqual(string a, string b) =>
        CryptographicOperations.FixedTimeEquals(
            Encoding.UTF8.GetBytes(a),
            Encoding.UTF8.GetBytes(b)
        );
}

[TestFixture]
[Description("Secure Token Generation")]
public class TokenGeneratorTests
{
    [Test]
    public void SecureToken_HasExpectedLength()
    {
        var token = TokenGenerator.GenerateSecure(32);
        Assert.That(token.Length, Is.EqualTo(64)); // hex: 2 chars per byte
    }

    [Test]
    public void SecureTokens_AreUnique()
    {
        var tokens = Enumerable.Range(0, 1000)
                               .Select(_ => TokenGenerator.GenerateSecure())
                               .ToHashSet();
        Assert.That(tokens.Count, Is.EqualTo(1000), "All tokens should be unique");
    }

    [Test]
    public void ConstantTimeEqual_SameStringsReturnTrue()
    {
        Assert.That(TokenGenerator.ConstantTimeEqual("abc", "abc"), Is.True);
    }

    [Test]
    public void ConstantTimeEqual_DifferentStringsReturnFalse()
    {
        Assert.That(TokenGenerator.ConstantTimeEqual("abc", "xyz"), Is.False);
    }
}
